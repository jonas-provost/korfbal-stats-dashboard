from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .config import ACTION_GROUPS, SEASON_START_MONTH, SHOT_BIN_SIZE
from .load import read_match_info, read_workbook


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def season_label(d: pd.Timestamp) -> str:
    start = d.year if d.month >= SEASON_START_MONTH else d.year - 1
    return f"{start}-{start + 1}"


def _flag(series: pd.Series, true_value: str) -> pd.Series:
    return (series.astype(str).str.strip().str.lower() == true_value.lower()).astype(int)


def build_match(info: dict, source_file: str) -> tuple[str, pd.DataFrame]:
    datum = pd.to_datetime(info["Datum"], dayfirst=True)
    tegenstander = str(info["Tegenstander"]).strip()
    match_id = f"{datum:%Y-%m-%d}_{_slug(tegenstander)}"
    # Aanname: "Eindstand thuis" = onze score, "Eindstand uit" = score tegenstander.
    voor, tegen = int(info["Eindstand thuis"]), int(info["Eindstand uit"])
    row = {
        "match_id": match_id,
        "datum": datum.date().isoformat(),
        "seizoen": season_label(datum),
        "tegenstander": tegenstander,
        "doelpunten_voor": voor,
        "doelpunten_tegen": tegen,
        "doelsaldo": voor - tegen,
        "resultaat": "W" if voor > tegen else "V" if voor < tegen else "G",
        "kansen_tegenstander": int(info.get("Kansen tegenstander", 0) or 0),
        "bron_bestand": source_file,
    }
    return match_id, pd.DataFrame([row])


def build_player_match(df: pd.DataFrame, match_id: str) -> pd.DataFrame:
    df = df[df["Naam"].astype(str).str.strip().str.lower() != "totaal"].copy()
    df = df.rename(columns={
        "Naam": "speler", "Nummer": "nummer", "Shots": "schoten", "Goals": "goals",
        "Vrijworp_Gescoord": "vrijworp_gescoord", "Vrijworp_Totaal": "vrijworp_totaal",
        "Penalty_Gescoord": "penalty_gescoord", "Penalty_Totaal": "penalty_totaal",
        "Doorloper_Gescoord": "doorloper_gescoord", "Doorloper_Totaal": "doorloper_totaal",
        "Rebounds": "rebounds", "Assists": "assists", "Steals": "steals",
        "Tegengoals": "tegengoals",
    }).drop(columns=["Kansen_Percentage"], errors="ignore")
    # Veldschoten = alle schoten min vrijworpen/penalty's/doorloopballen.
    df["veld_schoten"] = df["schoten"] - df["vrijworp_totaal"] - df["penalty_totaal"] - df["doorloper_totaal"]
    df["veld_goals"] = df["goals"] - df["vrijworp_gescoord"] - df["penalty_gescoord"] - df["doorloper_gescoord"]
    df["nummer"] = df["nummer"].astype("Int64")
    df.insert(0, "match_id", match_id)
    return df.reset_index(drop=True)


def build_shots(df: pd.DataFrame, match_id: str) -> pd.DataFrame:
    out = pd.DataFrame({
        "match_id": match_id,
        "speler": df["Speler"],
        "x": df["X"].round(1),
        "y": df["Y"].round(1),
        "doelpunt": _flag(df["Doelpunt"], "Ja"),
    })
    out["x_bin"] = (out["x"] // SHOT_BIN_SIZE * SHOT_BIN_SIZE).astype(int)
    out["y_bin"] = (out["y"] // SHOT_BIN_SIZE * SHOT_BIN_SIZE).astype(int)
    return out


def build_possession(df: pd.DataFrame, match_id: str) -> pd.DataFrame:
    return pd.DataFrame({
        "match_id": match_id,
        "aanval_nr": df["Aanval_Nummer"],
        "team": df["Team"],
        "eigen_aanval": _flag(df["Team"], "Ons team"),
        "aantal_kansen": df["Aantal_Kansen"],
        "doelpunt": _flag(df["Doelpunt"], "Ja"),
    })


def build_actions(df: pd.DataFrame, match_id: str) -> pd.DataFrame:
    types = df["Type"].astype(str).str.strip()
    base = types.str.replace(r"\s+no$", "", regex=True)
    groups = base.map(lambda t: ACTION_GROUPS.get(t, (t, False)))
    return pd.DataFrame({
        "match_id": match_id,
        "volgnummer": df["Volgnummer"],
        "type": types,
        "actie_groep": [g for g, _ in groups],
        "is_poging": [int(p) for _, p in groups],
        "speler": df["Speler"].fillna(""),
        "gescoord": _flag(df["Details"].fillna(""), "Doelpunt"),
    })


def build_substitutions(df: pd.DataFrame, match_id: str) -> pd.DataFrame:
    out = df.rename(columns={"Wissel_Nummer": "wissel_nr", "Nummer_Uit": "nummer_uit",
                             "Nummer_In": "nummer_in"})
    out.insert(0, "match_id", match_id)
    return out


def process_workbook(path: Path) -> dict[str, pd.DataFrame]:
    sheets = read_workbook(path)
    match_id, match = build_match(read_match_info(sheets["MatchInfo"]), path.name)
    return {
        "dim_match": match,
        "fact_player_match": build_player_match(sheets["PlayerStats"], match_id),
        "fact_shots": build_shots(sheets["ShotLocations"], match_id),
        "fact_possession": build_possession(sheets["PossessionLog"], match_id),
        "fact_actions": build_actions(sheets["ActionLog"], match_id),
        "fact_substitutions": build_substitutions(sheets["SubstitutionLog"], match_id),
    }


def build_all(raw_dir: Path) -> dict[str, pd.DataFrame]:
    files = sorted(p for p in raw_dir.glob("*.xlsx") if not p.name.startswith("~$"))
    if not files:
        raise FileNotFoundError(f"Geen .xlsx bestanden in {raw_dir}")
    parts: dict[str, list[pd.DataFrame]] = {}
    seen: dict[str, str] = {}
    for f in files:
        tables = process_workbook(f)
        mid = tables["dim_match"].loc[0, "match_id"]
        if mid in seen:
            print(f"WAARSCHUWING: {f.name} lijkt dubbel met {seen[mid]} ({mid}); overgeslagen")
            continue
        seen[mid] = f.name
        for name, df in tables.items():
            parts.setdefault(name, []).append(df)
    model = {n: pd.concat(dfs, ignore_index=True) for n, dfs in parts.items()}

    # Spelersdimensie: één rij per speler, laatst gebruikte rugnummer.
    pm = model["fact_player_match"].merge(model["dim_match"][["match_id", "datum"]], on="match_id")
    pm = pm.sort_values("datum")
    model["dim_player"] = (
        pm.groupby("speler", as_index=False)
        .agg(laatste_nummer=("nummer", "last"), wedstrijden=("match_id", "nunique"))
    )
    return model

"""Genereert fictieve wedstrijd-exports (zelfde formaat als de korfbal-stats-live app).

Bedoeld voor de publieke demo: alle spelers en tegenstanders zijn verzonnen.
Gebruik:  python scripts/make_demo_data.py
"""
from __future__ import annotations

from datetime import date, timedelta
from math import hypot
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "sample_data"
SEED = 2026
FIRST_MATCH = date(2026, 8, 15)  # daarna wekelijks

# naam: (rugnummer, schotgewicht, nauwkeurigheid)
PLAYERS = {
    "Speler A": (1, 1.6, 1.10), "Speler B": (2, 1.4, 1.05), "Speler C": (3, 1.2, 1.00),
    "Speler D": (4, 1.0, 0.95), "Speler E": (5, 0.9, 1.00), "Speler F": (6, 0.8, 0.90),
    "Speler G": (7, 0.6, 0.85), "Speler H": (8, 0.5, 0.90), "Speler I": (9, 0.3, 0.85),
}
OPPONENTS = ["Demo Noord", "Demo Oost", "Demo Zuid", "Demo West",
             "Demo Centrum", "Demo Haven", "Demo Dorp", "Demo Stad"]
BASKET = (275.0, 225.0)
POST = (277.0, 246.0)  # paal op de veldafbeelding (559 x 486 px)
SX, SY = 628 / 559, 547 / 486  # de app werkt met een canvas van ca. 628 x 547 punten
KINDS = ["veld", "vrijworp", "penalty", "doorloper"]
KIND_P = [0.68, 0.10, 0.04, 0.18]
BASE_P = {"vrijworp": 0.42, "penalty": 0.55, "doorloper": 0.50}
LABEL = {"veld": "Schot (veld)", "vrijworp": "Vrijworp", "penalty": "Penalty", "doorloper": "Doorloper"}
PREFIX = {"vrijworp": "vrijworp", "penalty": "penalty", "doorloper": "doorloper"}


def write_workbook(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name, index=False)


def keep_outside_post(x: float, y: float, radius: float = 72.0) -> tuple[float, float]:
    """Schuif schoten die in de gele cirkel rond de paal vallen naar buiten (geen extra random-getallen)."""
    dx, dy = x - POST[0], y - POST[1]
    dist = hypot(dx, dy) or 1.0
    if dist < radius:
        return POST[0] + dx / dist * radius, POST[1] + dy / dist * radius
    return x, y


def simulate(rng: np.random.Generator, opponent: str, day: date) -> dict[str, pd.DataFrame]:
    dropped = rng.choice(list(PLAYERS))
    roster = [p for p in PLAYERS if p != dropped]
    weights = np.array([PLAYERS[p][1] for p in roster])
    weights = weights / weights.sum()
    st = {p: dict(shots=0, goals=0, vw_g=0, vw_t=0, pen_g=0, pen_t=0, dl_g=0, dl_t=0,
                  reb=0, ast=0, stl=0, tg=0) for p in roster}
    own_strength, opp_strength = rng.uniform(0.7, 0.95), rng.uniform(0.85, 1.6)

    actions, shots, possession = [], [], []

    def act(kind, speler=None, details=None):
        actions.append({"Volgnummer": len(actions) + 1, "Type": kind, "Speler": speler, "Details": details})

    order = list(rng.permutation(["own"] * int(rng.integers(38, 50)) + ["opp"] * int(rng.integers(32, 44))))
    opp_goals = opp_kansen = 0
    for nr, team in enumerate(order, 1):
        if team == "own":
            k = int(rng.choice(5, p=[0.12, 0.45, 0.25, 0.12, 0.06]))
            taken, scored = 0, False
            if k == 0:
                act("0 Kans (ons)")
            for i in range(k):
                if i > 0:
                    rebounder = str(rng.choice(roster))
                    st[rebounder]["reb"] += 1
                    act("Rebound", rebounder)
                shooter = str(rng.choice(roster, p=weights))
                kind = str(rng.choice(KINDS, p=KIND_P))
                skill = PLAYERS[shooter][2] * own_strength
                if kind == "veld":
                    x, y = float(rng.uniform(60, 490)), float(rng.uniform(110, 340))
                    x, y = keep_outside_post(x, y)
                    p = float(np.clip((0.55 - hypot(x - BASKET[0], y - BASKET[1]) / 600) * skill, 0.05, 0.75))
                    hit = bool(rng.random() < p)
                    shots.append({"Speler": shooter, "Nummer": PLAYERS[shooter][0],
                                  "X": round(x * SX, 6), "Y": round(y * SY, 6), "Doelpunt": "Ja" if hit else "Nee"})
                else:
                    hit = bool(rng.random() < min(BASE_P[kind] * skill, 0.85))
                    st[shooter][{"vrijworp": "vw", "penalty": "pen", "doorloper": "dl"}[kind] + "_t"] += 1
                    if hit:
                        st[shooter][{"vrijworp": "vw", "penalty": "pen", "doorloper": "dl"}[kind] + "_g"] += 1
                st[shooter]["shots"] += 1
                taken += 1
                label = LABEL[kind] if (hit or kind == "veld") else f"{LABEL[kind]} no"
                act(label, shooter, "Doelpunt" if hit else "Gemist")
                if hit:
                    st[shooter]["goals"] += 1
                    scored = True
                    if kind in ("veld", "doorloper") and rng.random() < 0.55:
                        assister = str(rng.choice([p for p in roster if p != shooter]))
                        st[assister]["ast"] += 1
                        act("Assist", assister)
                    break
            possession.append({"Aanval_Nummer": nr, "Team": "Ons team", "Aantal_Kansen": taken,
                               "Doelpunt": "Ja" if scored else "Nee"})
        else:
            k = int(rng.choice(4, p=[0.2, 0.5, 0.22, 0.08]))
            taken, scored = 0, False
            if k == 0:
                act("0 Kans (tegenstander)")
                if rng.random() < 0.4:
                    stealer = str(rng.choice(roster))
                    st[stealer]["stl"] += 1
                    act("Steal", stealer)
            for _ in range(k):
                act("Kans tegenstander")
                taken += 1
                if rng.random() < 0.30 * opp_strength:
                    scored = True
                    defender = str(rng.choice(roster))
                    st[defender]["tg"] += 1
                    act("Tegengoal", defender)
                    break
                if rng.random() < 0.6:
                    rebounder = str(rng.choice(roster))
                    st[rebounder]["reb"] += 1
                    act("Rebound", rebounder)
            opp_kansen += taken
            opp_goals += int(scored)
            possession.append({"Aanval_Nummer": nr, "Team": "Tegenstander", "Aantal_Kansen": taken,
                               "Doelpunt": "Ja" if scored else "Nee"})

    rows = []
    for p in roster:
        s = st[p]
        rows.append({"Naam": p, "Nummer": PLAYERS[p][0], "Shots": s["shots"], "Goals": s["goals"],
                     "Kansen_Percentage": round(100 * s["goals"] / s["shots"]) if s["shots"] else 0,
                     "Vrijworp_Gescoord": s["vw_g"], "Vrijworp_Totaal": s["vw_t"],
                     "Penalty_Gescoord": s["pen_g"], "Penalty_Totaal": s["pen_t"],
                     "Doorloper_Gescoord": s["dl_g"], "Doorloper_Totaal": s["dl_t"],
                     "Rebounds": s["reb"], "Assists": s["ast"], "Steals": s["stl"], "Tegengoals": s["tg"]})
    players = pd.DataFrame(rows)
    total = players.drop(columns=["Naam", "Nummer", "Kansen_Percentage"]).sum()
    players.loc[len(players)] = {"Naam": "Totaal", "Nummer": np.nan, **total.to_dict(),
                                 "Kansen_Percentage": round(100 * total["Goals"] / total["Shots"])}
    own_goals = int(total["Goals"])

    info = pd.DataFrame([
        ("Tegenstander", opponent), ("Datum", f"{day:%d/%m/%Y}"),
        ("Eindstand thuis", own_goals), ("Eindstand uit", opp_goals),
        ("Kansen tegenstander", opp_kansen), ("Doelpunten tegenstander", opp_goals),
    ], columns=["Veld", "Waarde"])

    subs = []
    for n in range(int(rng.integers(0, 4))):
        uit, inn = rng.choice([PLAYERS[p][0] for p in roster], size=2, replace=False)
        subs.append({"Wissel_Nummer": n + 1, "Nummer_Uit": int(uit), "Nummer_In": int(inn)})
    return {
        "MatchInfo": info,
        "PlayerStats": players,
        "ShotLocations": pd.DataFrame(shots, columns=["Speler", "Nummer", "X", "Y", "Doelpunt"]),
        "PossessionLog": pd.DataFrame(possession),
        "SubstitutionLog": pd.DataFrame(subs, columns=["Wissel_Nummer", "Nummer_Uit", "Nummer_In"]),
        "ActionLog": pd.DataFrame(actions),
    }


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.xlsx"):
        old.unlink()
    rng = np.random.default_rng(SEED)
    for i, opponent in enumerate(OPPONENTS):
        day = FIRST_MATCH + timedelta(days=7 * i)
        sheets = simulate(rng, opponent, day)
        path = OUT / f"wedstrijd-data-{day:%Y-%m-%d}.xlsx"
        write_workbook(path, sheets)
        info = dict(zip(sheets["MatchInfo"]["Veld"], sheets["MatchInfo"]["Waarde"]))
        print(f"{path.name}: {opponent} {info['Eindstand thuis']}-{info['Eindstand uit']}")


if __name__ == "__main__":
    main()

"""Afgeleide cijfers voor het dashboard (per wedstrijd en per speler)."""
from __future__ import annotations

import pandas as pd

SUM_COLS = [
    "schoten", "goals", "veld_schoten", "veld_goals",
    "vrijworp_gescoord", "vrijworp_totaal", "penalty_gescoord", "penalty_totaal",
    "doorloper_gescoord", "doorloper_totaal", "rebounds", "assists", "steals", "tegengoals",
]


def ratio(num: pd.Series, den: pd.Series) -> pd.Series:
    """Deling die NaN geeft i.p.v. een fout als de noemer 0 is."""
    return num / den.where(den != 0)


def add_shooting_pcts(df: pd.DataFrame) -> pd.DataFrame:
    df["schotpercentage"] = ratio(df["goals"], df["schoten"])
    df["veldschot_pct"] = ratio(df["veld_goals"], df["veld_schoten"])
    df["vrijworp_pct"] = ratio(df["vrijworp_gescoord"], df["vrijworp_totaal"])
    df["penalty_pct"] = ratio(df["penalty_gescoord"], df["penalty_totaal"])
    df["doorloper_pct"] = ratio(df["doorloper_gescoord"], df["doorloper_totaal"])
    return df


def _attack_stats(pos: pd.DataFrame, own: int, suffix: str) -> pd.DataFrame:
    sub = pos[pos["eigen_aanval"] == own]
    g = sub.groupby("match_id").agg(
        **{
            f"aanvallen_{suffix}": ("aanval_nr", "count"),
            f"kansen_{suffix}": ("aantal_kansen", "sum"),
            f"goals_aanvallen_{suffix}": ("doelpunt", "sum"),
            f"nulaanvallen_{suffix}": ("aantal_kansen", lambda s: int((s == 0).sum())),
        }
    )
    g[f"kansen_per_aanval_{suffix}"] = ratio(g[f"kansen_{suffix}"], g[f"aanvallen_{suffix}"])
    g[f"goals_per_aanval_{suffix}"] = ratio(g[f"goals_aanvallen_{suffix}"], g[f"aanvallen_{suffix}"])
    g[f"nulaanvallen_pct_{suffix}"] = ratio(g[f"nulaanvallen_{suffix}"], g[f"aanvallen_{suffix}"])
    return g


def match_features(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Eén rij per wedstrijd met score, schotcijfers en aanvalscijfers."""
    dm = model["dim_match"].set_index("match_id")
    pm = model["fact_player_match"].groupby("match_id")[SUM_COLS].sum()
    pos = model["fact_possession"]
    df = dm.join(pm).join(_attack_stats(pos, 1, "eigen")).join(_attack_stats(pos, 0, "tegen"))
    df = add_shooting_pcts(df)
    return df.reset_index().sort_values("datum").reset_index(drop=True)


def player_totals(pm: pd.DataFrame) -> pd.DataFrame:
    """Totalen en gemiddelden per speler over de meegegeven wedstrijden."""
    g = pm.groupby("speler")[SUM_COLS].sum()
    g["wedstrijden"] = pm.groupby("speler")["match_id"].nunique()
    g = add_shooting_pcts(g)
    for col in ["goals", "schoten", "rebounds", "assists", "steals", "tegengoals"]:
        g[f"{col}_per_wedstrijd"] = g[col] / g["wedstrijden"]
    total_goals = g["goals"].sum()
    g["aandeel_teamgoals"] = g["goals"] / total_goals if total_goals else float("nan")
    return g.reset_index().sort_values("goals", ascending=False).reset_index(drop=True)

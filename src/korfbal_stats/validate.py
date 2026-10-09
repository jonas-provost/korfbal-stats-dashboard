"""Consistentiechecks: vangen fouten in de export op voor ze in het dashboard belanden."""
from __future__ import annotations

import pandas as pd


def validate(model: dict[str, pd.DataFrame]) -> list[str]:
    issues: list[str] = []
    for _, m in model["dim_match"].iterrows():
        mid = m["match_id"]
        pm = model["fact_player_match"].query("match_id == @mid")
        pos = model["fact_possession"].query("match_id == @mid")
        shots = model["fact_shots"].query("match_id == @mid")

        if pm["goals"].sum() != m["doelpunten_voor"]:
            issues.append(f"{mid}: spelersgoals ({pm['goals'].sum()}) != eindstand ({m['doelpunten_voor']})")
        own = pos[pos["eigen_aanval"] == 1]
        opp = pos[pos["eigen_aanval"] == 0]
        if own["doelpunt"].sum() != m["doelpunten_voor"]:
            issues.append(f"{mid}: eigen aanvalsgoals ({own['doelpunt'].sum()}) != eindstand")
        if opp["doelpunt"].sum() != m["doelpunten_tegen"]:
            issues.append(f"{mid}: tegengoals in aanvallen ({opp['doelpunt'].sum()}) != eindstand")
        if opp["aantal_kansen"].sum() != m["kansen_tegenstander"]:
            issues.append(f"{mid}: kansen tegenstander komen niet overeen met aanvallenlog")
        if len(shots) != pm["veld_schoten"].sum():
            issues.append(f"{mid}: schotlocaties ({len(shots)}) != veldschoten ({pm['veld_schoten'].sum()})")
        if (pm[["veld_schoten", "veld_goals"]] < 0).any().any():
            issues.append(f"{mid}: negatieve veldschoten/-goals (vrijworp/penalty/doorloper > totaal)")
    return issues

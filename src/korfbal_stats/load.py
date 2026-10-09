from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import REQUIRED_SHEETS


def read_workbook(path: Path) -> dict[str, pd.DataFrame]:
    """Lees alle sheets van één wedstrijd-export."""
    sheets = pd.read_excel(path, sheet_name=None)
    missing = [s for s in REQUIRED_SHEETS if s not in sheets]
    if missing:
        raise ValueError(f"{path.name}: ontbrekende sheets {missing}")
    return sheets


def read_match_info(df: pd.DataFrame) -> dict:
    """MatchInfo is een Veld/Waarde-tabel -> dict."""
    return dict(zip(df["Veld"].astype(str).str.strip(), df["Waarde"]))

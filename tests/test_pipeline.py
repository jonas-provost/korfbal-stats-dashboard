from pathlib import Path

from korfbal_stats.analytics import match_features, player_totals
from korfbal_stats.transform import build_all
from korfbal_stats.validate import validate

SAMPLE = Path(__file__).resolve().parents[1] / "sample_data"


def test_demo_data_loads():
    model = build_all(SAMPLE)
    dm = model["dim_match"]
    assert len(dm) == 8
    assert set(dm["seizoen"]) == {"2026-2027"}
    assert set(dm["resultaat"]) <= {"W", "G", "V"}
    assert "Totaal" not in set(model["fact_player_match"]["speler"])


def test_demo_data_is_consistent():
    # spelersgoals, aanvallenlog, kansen en schotlocaties moeten allemaal kloppen met de eindstand
    assert validate(build_all(SAMPLE)) == []


def test_analytics_totals_match():
    model = build_all(SAMPLE)
    mf = match_features(model)
    assert mf["goals"].sum() == mf["doelpunten_voor"].sum()
    assert ((mf["schotpercentage"] >= 0) & (mf["schotpercentage"] <= 1)).all()

    pt = player_totals(model["fact_player_match"])
    assert abs(pt["aandeel_teamgoals"].sum() - 1) < 1e-9

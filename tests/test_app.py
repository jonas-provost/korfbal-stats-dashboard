from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"


def test_app_runs_without_errors():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception

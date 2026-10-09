# Korfbal stats dashboard

Interactief dashboard (Streamlit) op de Excel-exports van de korfbal-stats-live app. Bekijk statistieken per wedstrijd of over een heel seizoen: score en doelsaldo, schotpercentages, aanvallen, spelerstotalen en een schotkaart.

De repo bevat enkel **fictieve demo-data** (`sample_data/`, gegenereerd door `scripts/make_demo_data.py`). Echte wedstrijddata blijft privé en staat nooit in deze repo.

## Starten
```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```
Zonder eigen data zie je de demo. Met eigen data kies je één van twee opties:

**A. Aparte map of private repo (aanbevolen)** — zet je `wedstrijd-data-*.xlsx` bestanden in een map buiten deze repo en geef die door:
```powershell
# Windows PowerShell, eenmalig (geldt voor nieuwe terminals)
setx KORFBAL_DATA_DIR "C:\pad\naar\jouw\data"
```
```bash
# macOS / Linux
export KORFBAL_DATA_DIR=/pad/naar/jouw/data
```

**B. `data/raw/`** — zet de bestanden in `data/raw/` van deze repo. Excel-bestanden worden door `.gitignore` altijd genegeerd, dus ze belanden niet per ongeluk op GitHub.

De zijbalk toont of je demo-data of eigen data bekijkt.

## Werking
- Elk Excel-bestand = één wedstrijd. Een wedstrijd wordt herkend aan datum + tegenstander uit het tabblad `MatchInfo`; dubbele bestanden worden overgeslagen.
- Het seizoen loopt van augustus tot en met juli (`src/korfbal_stats/config.py`).
- "Eindstand thuis" wordt gelezen als de score van ons team, "Eindstand uit" als die van de tegenstander.
- Bij het inlezen worden controles gedraaid (spelersgoals = eindstand, aanvallenlog = eindstand, schotlocaties = veldschoten). Afwijkingen verschijnen in de zijbalk.

## Structuur
```
app/streamlit_app.py            het dashboard
src/korfbal_stats/              inlezen, omzetten, berekeningen en controles
sample_data/                    fictieve demo-exports
scripts/make_demo_data.py       genereert de demo-data
tests/                          automatische tests
```

## Tests
```bash
pytest
```

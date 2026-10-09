# Korfbal stats dashboard

Interactief dashboard (Streamlit) op de Excel-exports van de korfbal-stats-live app. Bekijk statistieken per wedstrijd of over een heel seizoen: score en doelsaldo, schotpercentages, aanvallen, spelerstotalen en een schotkaart.

De repo bevat enkel **fictieve demo-data** (`sample_data/`, gegenereerd door `scripts/make_demo_data.py`). Echte wedstrijddata blijft privé en staat nooit in deze repo.

## Starten
```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```
Zonder eigen data zie je de demo. Met eigen data:

**Zet je `wedstrijd-data-*.xlsx` bestanden in `data/raw/`.** Excel-bestanden worden door `.gitignore` altijd genegeerd, dus ze belanden nooit per ongeluk op GitHub. Elke week een nieuwe wedstrijd = één bestand in `data/raw/` plaatsen en de pagina verversen.

*Optioneel:* wil je de data elders bewaren (bijvoorbeeld een back-upmap of een aparte private repo), geef dan die map door:
```powershell
# Windows PowerShell, eenmalig (geldt voor nieuwe terminals)
setx KORFBAL_DATA_DIR "C:\pad\naar\jouw\data"
```
```bash
# macOS / Linux
export KORFBAL_DATA_DIR=/pad/naar/jouw/data
```

De zijbalk toont of je demo-data of eigen data bekijkt.

## Uitleg van de cijfers
| Cijfer | Betekenis |
|---|---|
| **Schotpercentage** | doelpunten ÷ **alle** schoten: veldschoten, vrijworpen, penalty's en doorloopballen samen |
| **Veldschot %** | doelpunten uit het spel ÷ schoten uit het spel. Vrijworpen, penalty's en doorloopballen tellen hier **niet** mee |
| Vrijworp % / Penalty % / Doorloper % | doelpunten ÷ pogingen van dat type |
| Kansen per aanval | gemiddeld aantal schoten per aanval (0 = aanval zonder kans) |
| Aanvallen met doelpunt % | aandeel aanvallen dat in een doelpunt eindigde |
| Aanvallen zonder kans % | aandeel aanvallen waarin geen schot kwam |
| Aandeel teamgoals % | doelpunten van de speler ÷ alle doelpunten van het team (in de selectie) |
| Doelsaldo / Winstpercentage | doelpunten voor min tegen / winsten ÷ wedstrijden |

Voorbeeld van het verschil tussen schotpercentage en veldschot %: een speler schiet 10 keer, 6 keer uit het spel (2 raak) en 4 keer uit een vrijworp of penalty (3 raak). Schotpercentage = 5/10 = **50%**, veldschot % = 2/6 = **33%**. Vrijworpen en penalty's zijn vaak makkelijker, dus veldschot % zegt meer over hoe goed iemand uit het spel scoort.

## Schotkaart
De schoten staan op de afbeelding `app/assets/korfbal-veld.png`. De afmetingen van het veld in de coördinaten van de app (ca. 628 x 547) staan in `SHOT_COORD_SIZE` in `src/korfbal_stats/config.py`.

## Werking
- Elk Excel-bestand = één wedstrijd. Een wedstrijd wordt herkend aan datum + tegenstander uit het tabblad `MatchInfo`; dubbele bestanden worden overgeslagen.
- Het seizoen loopt van augustus tot en met juli (`src/korfbal_stats/config.py`).
- "Eindstand thuis" wordt gelezen als de score van ons team, "Eindstand uit" als die van de tegenstander.
- Bij het inlezen worden controles gedraaid (spelersgoals = eindstand, aanvallenlog = eindstand, schotlocaties = veldschoten). Afwijkingen verschijnen in de zijbalk.

## Structuur
```
app/streamlit_app.py            het dashboard
app/assets/korfbal-veld.png     achtergrond voor de schotkaart
src/korfbal_stats/              inlezen, omzetten, berekeningen en controles
sample_data/                    fictieve demo-exports
scripts/make_demo_data.py       genereert de demo-data
tests/                          automatische tests
```

## Tests
```bash
pytest
```

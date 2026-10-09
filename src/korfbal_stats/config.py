"""Instellingen die je makkelijk kan aanpassen."""

# Seizoen loopt van augustus tot en met juli (seizoen 2026-2027 start 1 aug 2026).
SEASON_START_MONTH = 8

# Breedte van de vakjes voor de schotkaart-heatmap (in app-coördinaten).
SHOT_BIN_SIZE = 50

# Verwachte sheets in elke export.
REQUIRED_SHEETS = [
    "MatchInfo",
    "PlayerStats",
    "ShotLocations",
    "PossessionLog",
    "SubstitutionLog",
    "ActionLog",
]

# Actietypes uit de ActionLog -> (groep, is_poging)
# "no"-varianten (bv. "Vrijworp no") worden automatisch naar hun basistype gemapt.
ACTION_GROUPS = {
    "Schot (veld)": ("Veldschot", True),
    "Vrijworp": ("Vrijworp", True),
    "Penalty": ("Penalty", True),
    "Doorloper": ("Doorloper", True),
    "Assist": ("Assist", False),
    "Rebound": ("Rebound", False),
    "Steal": ("Steal", False),
    "Tegengoal": ("Tegengoal", False),
    "Kans tegenstander": ("Kans tegenstander", False),
}

# Afmetingen (breedte, hoogte) van het veld in de coördinaten van de app, voor de schotkaart.
# None = gebruik de afmetingen van de afbeelding app/assets/korfbal-veld.png (559 x 486).
# Staan de schoten verschoven op de afbeelding, pas dit dan aan naar het canvasformaat van de app.
SHOT_COORD_SIZE = None

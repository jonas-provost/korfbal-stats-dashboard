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
# Gemeten met taps in de 4 hoeken van de app: x loopt van ca. 1 tot 627, y van ca. 1 tot 546.
# De veldafbeelding (559 x 486 px) wordt over dit hele vlak uitgerekt.
# None = gebruik de pixelafmetingen van de afbeelding zelf.
SHOT_COORD_SIZE = (628, 547)

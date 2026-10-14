"""Textes affichés (français / anglais)."""

from __future__ import annotations

STRINGS = {
    "fr": {
        "menu": "Dans les menus",
        "title_screen": "🏠 Écran titre",
        "loading": "⏳ Chargement de la partie…",
        "last_game": "Dernière partie : {summary}",
        "in_game": "En partie",
        "day": "Jour {day}",
        "saved_at": "💾 Sauvegarde de {time}",
        "no_mod": "mod temps réel absent",
        "solo": "Solo",
        "coop_host": "Coop (hôte)",
        "coop_client": "Coop",
        "coop_players": "{n} joueurs",
        "strength": "Force niv. {n}",
        "held": "En main : {item}",
        "position": "Position {x}, {y}, {z}",
        # activité
        "dead": "💀 Mort…",
        "sleeping": "😴 Dort",
        "paused": "⏸️ En pause",
        "intro": "🚁 Crash de l'hélicoptère",
        "waking": "🥱 Se réveille",
        "endgame": "🏁 Fin de l'histoire",
        "gliding": "🪂 En deltaplane",
        "golf_cart": "🛺 En voiturette de golf",
        "raft": "🛶 Sur un radeau",
        "underwater": "🤿 Plonge",
        "swimming": "🏊 Nage",
        "constructing": "🔨 Construit",
        "inventory": "🎒 Fouille son inventaire",
        "in_cave": "🕳️ Dans une grotte",
        "in_cave_named": "🕳️ {name}",
        "in_bunker": "🚪 Dans un bunker",
        "in_bunker_named": "🚪 {name}",
        "near": "📍 Près de : {place}",
        "region": "🧭 {region}",
        "exploring": "🌲 Explore l'île",
        "mountain": "⛰️ En montagne",
        # régions
        "center": "Centre de l'île",
        "n": "Nord de l'île", "ne": "Nord-est de l'île", "e": "Est de l'île", "se": "Sud-est de l'île",
        "s": "Sud de l'île", "sw": "Sud-ouest de l'île", "w": "Ouest de l'île", "nw": "Nord-ouest de l'île",
        "held_line": "✋ {item}",
        "empty_hands": "✋ Mains vides",
        # vitals
        "cold": "🥶", "sick": "🤢",
        "downed": "🆘 À terre, attend de l'aide",
        "cutscene": "🎬 Cinématique",
        "burning": "🔥 En feu !",
        "boss": "☠️ Combat contre un boss",
        "knight_v": "🛹 Sur le Knight V",
        "threat": "⚔️ Face à {who}",
        "threat_mutants_only": "👹 Face à {who}",
        "cannibal_1": "un cannibale", "cannibal_n": "{n} cannibales",
        "mutant_1": "un mutant", "mutant_n": "{n} mutants",
        "and": " et ",
        "trees": "🪓 {n} arbres coupés",
        "killed": "⚔️ Tués : {list}",
        "killed_cannibals": "{n} cannibales", "killed_mutants": "{n} mutants", "killed_animals": "{n} animaux",
        "deaths": "💀 {n} morts",
        "companion_with": "{name} t'accompagne",
        "companion_dist": "{name} à {d} m",
        "companion_dead": "{name} ✝️",
        "companion_alive": "{name} ✅",
        "already_running": "le compagnon tourne déjà",
    },
    "en": {
        "menu": "In the menus",
        "title_screen": "🏠 Title screen",
        "loading": "⏳ Loading the game…",
        "last_game": "Last game: {summary}",
        "in_game": "In game",
        "day": "Day {day}",
        "saved_at": "💾 Saved at {time}",
        "no_mod": "live mod missing",
        "solo": "Solo",
        "coop_host": "Co-op (host)",
        "coop_client": "Co-op",
        "coop_players": "{n} players",
        "strength": "Strength lvl {n}",
        "held": "Holding: {item}",
        "position": "Position {x}, {y}, {z}",
        "dead": "💀 Dead…",
        "sleeping": "😴 Sleeping",
        "paused": "⏸️ Paused",
        "intro": "🚁 Helicopter crash",
        "waking": "🥱 Waking up",
        "endgame": "🏁 Story ending",
        "gliding": "🪂 Hang gliding",
        "golf_cart": "🛺 Driving a golf cart",
        "raft": "🛶 On a raft",
        "underwater": "🤿 Diving",
        "swimming": "🏊 Swimming",
        "constructing": "🔨 Building",
        "inventory": "🎒 Rummaging in the inventory",
        "in_cave": "🕳️ In a cave",
        "in_cave_named": "🕳️ {name}",
        "in_bunker": "🚪 In a bunker",
        "in_bunker_named": "🚪 {name}",
        "near": "📍 Near: {place}",
        "region": "🧭 {region}",
        "exploring": "🌲 Exploring the island",
        "mountain": "⛰️ In the mountains",
        "center": "Center of the island",
        "n": "North of the island", "ne": "North-east of the island", "e": "East of the island", "se": "South-east of the island",
        "s": "South of the island", "sw": "South-west of the island", "w": "West of the island", "nw": "North-west of the island",
        "held_line": "✋ {item}",
        "empty_hands": "✋ Empty hands",
        "cold": "🥶", "sick": "🤢",
        "downed": "🆘 Downed, waiting for help",
        "cutscene": "🎬 Cutscene",
        "burning": "🔥 On fire!",
        "boss": "☠️ Boss fight",
        "knight_v": "🛹 Riding the Knight V",
        "threat": "⚔️ Facing {who}",
        "threat_mutants_only": "👹 Facing {who}",
        "cannibal_1": "a cannibal", "cannibal_n": "{n} cannibals",
        "mutant_1": "a mutant", "mutant_n": "{n} mutants",
        "and": " and ",
        "trees": "🪓 {n} trees cut",
        "killed": "⚔️ Killed: {list}",
        "killed_cannibals": "{n} cannibals", "killed_mutants": "{n} mutants", "killed_animals": "{n} animals",
        "deaths": "💀 {n} deaths",
        "companion_with": "{name} is with you",
        "companion_dist": "{name} {d} m away",
        "companion_dead": "{name} ✝️",
        "companion_alive": "{name} ✅",
        "already_running": "the companion is already running",
    },
}

MODES = {
    "fr": {"Normal": "Normal", "Hard": "Difficile", "HardSurvival": "Survie difficile", "Peaceful": "Paisible",
           "Creative": "Créatif", "Custom": "Personnalisé"},
    "en": {"Normal": "Normal", "Hard": "Hard", "HardSurvival": "Hard Survival", "Peaceful": "Peaceful",
           "Creative": "Creative", "Custom": "Custom"},
}

SEASONS = {
    "fr": {"Spring": "🌸 Printemps", "Summer": "🌻 Été", "Fall": "🍂 Automne", "Winter": "❄️ Hiver"},
    "en": {"Spring": "🌸 Spring", "Summer": "🌻 Summer", "Fall": "🍂 Fall", "Winter": "❄️ Winter"},
}

WEATHER = {
    "fr": {"Light": "🌦️ Pluie fine", "Medium": "🌧️ Pluie", "Heavy": "⛈️ Pluie battante", "snow": "🌨️ Neige",
           "clear_day": "☀️ Jour", "clear_night": "🌙 Nuit"},
    "en": {"Light": "🌦️ Light rain", "Medium": "🌧️ Rain", "Heavy": "⛈️ Heavy rain", "snow": "🌨️ Snow",
           "clear_day": "☀️ Day", "clear_night": "🌙 Night"},
}

PERIODS = {
    "fr": ((5, "🌅 Aube"), (8, "☀️ Matin"), (12, "☀️ Après-midi"), (18, "🌇 Soir"), (21, "🌙 Nuit")),
    "en": ((5, "🌅 Dawn"), (8, "☀️ Morning"), (12, "☀️ Afternoon"), (18, "🌇 Evening"), (21, "🌙 Night")),
}


def resolve_lang(wanted: str, game_lang: str = "") -> str:
    wanted = (wanted or "auto").lower()
    if wanted == "auto":
        wanted = (game_lang or "fr").lower()
    wanted = wanted.split("-")[0]
    return wanted if wanted in STRINGS else "en"


def t(lang: str, key: str, **kwargs) -> str:
    text = STRINGS.get(lang, STRINGS["en"]).get(key) or STRINGS["en"].get(key) or key
    return text.format(**kwargs) if kwargs else text


def mode_name(lang: str, mode: str) -> str:
    return MODES.get(lang, MODES["en"]).get(mode, mode)


def season_name(lang: str, season: str) -> str:
    return SEASONS.get(lang, SEASONS["en"]).get(season, season)


def weather_name(lang: str, key: str) -> str:
    return WEATHER.get(lang, WEATHER["en"]).get(key, "")


def period_name(lang: str, hour: int) -> str:
    periods = PERIODS.get(lang, PERIODS["en"])
    name = periods[-1][1]   # avant 5 h : nuit
    for start, label in periods:
        if hour >= start:
            name = label
    return name

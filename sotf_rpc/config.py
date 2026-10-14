"""Chargement de config.json (avec valeurs par défaut)."""

from __future__ import annotations

import json
import os
from typing import Optional

STEAM_ART = "https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/1326470"
TWEMOJI = "https://cdn.jsdelivr.net/gh/jdecked/twemoji@15.1.0/assets/72x72"

DEFAULTS: dict = {
    # Application Discord. Par défaut : l'application officielle « Sons of the Forest » que Discord utilise
    # pour détecter le jeu → une seule activité « Joue à Sons of the Forest », enrichie.
    # Tu peux mettre l'Application ID de ta propre application (https://discord.com/developers/applications).
    "client_id": "1080279445153263686",
    # "auto" = langue du jeu (transmise par le mod), sinon "fr" ou "en".
    "language": "auto",
    # Fréquence de vérification (processus + live.json), en secondes.
    "poll_interval_seconds": 3,
    # Fichier écrit par le mod RedLoader (dossier mod/).
    "live_path": "%LOCALAPPDATA%/SotFRPC/live.json",
    # Au-delà de cet âge (secondes), live.json est ignoré → repli sur les sauvegardes.
    "live_stale_seconds": 30,
    # Exécutable surveillé.
    "process_names": ["SonsOfTheForest.exe"],
    # Dossier des sauvegardes (repli sans mod).
    "saves_dir": "%USERPROFILE%/AppData/LocalLow/Endnight/SonsOfTheForest/Saves",
    # Chrono « écoulées » : "game" (depuis le lancement du jeu), "world" (depuis l'entrée dans la partie), "none".
    "timer": "game",
    # Horloge en jeu : "exact" (22:14), "period" (Nuit), "both", "none".
    "clock_mode": "exact",
    # Le jour affiché (« Jour 6 ») = compteur du jeu + ce décalage.
    "day_offset": 0,
    # Lignes alternées sur la 2e ligne (toutes les rotate_seconds) :
    # "activity" (ce que tu fais / où tu es), "vitals" (santé, faim, soif, repos), "stats" (arbres coupés,
    # ennemis tués, morts), "companions" (Kelvin / Virginia), "held" (objet en main).
    # Une seule entrée = pas d'alternance. Mort, combat, sommeil, pause… restent affichés en continu.
    "state_rotation": ["activity", "vitals", "activity", "stats", "activity", "companions"],
    "rotate_seconds": 20,
    # Vitals : "percent" (❤️ 85%) ou "value" (❤️ 106/124).
    "vitals_format": "percent",
    # « Près de … » si un lieu nommé est à moins de cette distance (mètres).
    "place_radius_m": 150,
    # Sinon, secteur de l'île (« nord-est de l'île ») d'après la position.
    "show_region": True,
    # Afficher l'objet tenu en main dans l'info-bulle de la petite icône.
    "show_held_item": True,
    # Ce que Discord montre dans la liste des membres à côté de ton nom : "name" (« Sons of the Forest »),
    # "details" (1re ligne : jour, saison, heure) ou "state" (2e ligne).
    "status_display": "name",
    # Coordonnées dans l'info-bulle du logo (debug).
    "show_position": False,
    # Noms personnalisés des grottes / bunkers (clés : CaveA…CaveH, BunkerA…BunkerG) et des lieux (id de places.json).
    "area_names": {},
    "place_names": {},
    # Images : clés d'assets de ton application Discord ou URLs https.
    "images": {
        "logo": f"{STEAM_ART}/library_600x900.jpg",
        "menu": f"{STEAM_ART}/library_600x900.jpg",
        "spring": f"{TWEMOJI}/1f338.png",
        "summer": f"{TWEMOJI}/1f33b.png",
        "fall": f"{TWEMOJI}/1f342.png",
        "winter": f"{TWEMOJI}/2744.png",
        "day": f"{TWEMOJI}/2600.png",
        "night": f"{TWEMOJI}/1f319.png",
        "rain_light": f"{TWEMOJI}/1f326.png",
        "rain": f"{TWEMOJI}/1f327.png",
        "storm": f"{TWEMOJI}/26c8.png",
        "snow": f"{TWEMOJI}/1f328.png",
        "cave": f"{TWEMOJI}/1f573.png",
        "bunker": f"{TWEMOJI}/1f6aa.png",
        "dead": f"{TWEMOJI}/1f480.png",
        "sleep": f"{TWEMOJI}/1f634.png",
        "pause": f"{TWEMOJI}/23f8.png",
        "glider": f"{TWEMOJI}/1fa82.png",
        "cart": f"{TWEMOJI}/1f6fa.png",
        "raft": f"{TWEMOJI}/1f6f6.png",
        "swim": f"{TWEMOJI}/1f3ca.png",
        "dive": f"{TWEMOJI}/1f93f.png",
        "loading": f"{TWEMOJI}/23f3.png",
        "menu_small": f"{TWEMOJI}/1f3e0.png",
        "save": f"{TWEMOJI}/1f4be.png",
        "sos": f"{TWEMOJI}/1f198.png",
        "cutscene": f"{TWEMOJI}/1f3ac.png",
        "fire": f"{TWEMOJI}/1f525.png",
        "boss": f"{TWEMOJI}/2620.png",
        "fight": f"{TWEMOJI}/2694.png",
        "mutant": f"{TWEMOJI}/1f479.png",
        "knight": f"{TWEMOJI}/1f6f9.png",
        "heli": f"{TWEMOJI}/1f681.png",
    },
    # Jusqu'à 2 boutons {"label": "…", "url": "https://…"} (visibles par les autres, pas par toi). [] pour aucun.
    "buttons": [{"label": "Sons of the Forest sur Steam", "url": "https://store.steampowered.com/app/1326470/"}],
}


def default_config_path() -> str:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(here, "config.json")


def load_config(path: Optional[str] = None) -> dict:
    path = path or default_config_path()
    config = json.loads(json.dumps(DEFAULTS))  # copie profonde
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8-sig") as fh:
            user = json.load(fh)
        for key, value in user.items():
            if key.startswith("_"):
                continue
            if isinstance(value, dict) and isinstance(config.get(key), dict):
                config[key].update(value)
            else:
                config[key] = value
    config["_path"] = path
    return config

"""Lecture des sauvegardes (repli quand le mod n'est pas là).

Emplacement : ``%USERPROFILE%\\AppData\\LocalLow\\Endnight\\SonsOfTheForest\\Saves\\<SteamID>\\<Type>\\<SaveId>\\``
avec ``SaveData.zip`` (versions récentes) ou les ``*SaveData.json`` à plat (anciennes versions).
Chaque fichier ``XxxSaveData.json`` contient ``{"Data": {"Xxx": "<JSON encodé en chaîne>"}}``.
"""

from __future__ import annotations

import glob
import json
import logging
import os
import zipfile
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

log = logging.getLogger(__name__)

SAVE_TYPES = ("SinglePlayer", "Multiplayer", "MultiplayerClient")
SEASONS = ("Spring", "Summer", "Fall", "Winter")


@dataclass
class SaveInfo:
    path: str
    save_type: str
    save_id: str
    mtime: float
    game_name: str = ""
    mode: str = ""
    day: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    season: str = ""
    kelvin_dead: bool = False
    virginia_dead: bool = False
    health: Optional[float] = None
    health_max: Optional[float] = None
    fullness: Optional[float] = None
    hydration: Optional[float] = None
    rest: Optional[float] = None
    strength_level: Optional[int] = None
    pos: Optional[Tuple[float, float, float]] = None


def _inner(raw: bytes, key: str) -> dict:
    """Décode ``{"Data": {key: "<json>"}}``."""
    outer = json.loads(raw.decode("utf-8-sig"))
    value = (outer.get("Data") or {}).get(key)
    if isinstance(value, str):
        value = json.loads(value)
    return value if isinstance(value, dict) else {}


def _read_members(path: str, names) -> Dict[str, bytes]:
    result: Dict[str, bytes] = {}
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path) as zf:
            available = set(zf.namelist())
            for name in names:
                if name in available:
                    result[name] = zf.read(name)
    else:
        for name in names:
            try:
                with open(os.path.join(path, name), "rb") as fh:
                    result[name] = fh.read()
            except OSError:
                pass
    return result


def parse_save(path: str, save_type: str, save_id: str, mtime: float) -> SaveInfo:
    info = SaveInfo(path=path, save_type=save_type, save_id=save_id, mtime=mtime)
    files = _read_members(path, ("GameStateSaveData.json", "GameSetupSaveData.json",
                                 "WeatherSystemSaveData.json", "PlayerStateSaveData.json"))

    if "GameStateSaveData.json" in files:
        gs = _inner(files["GameStateSaveData.json"], "GameState")
        info.game_name = str(gs.get("GameName") or "")
        info.mode = str(gs.get("GameType") or "")
        for attr, key in (("day", "GameDays"), ("hour", "GameHours"), ("minute", "GameMinutes")):
            value = gs.get(key)
            setattr(info, attr, int(value) if isinstance(value, (int, float)) else (0 if attr != "day" else None))
        info.kelvin_dead = bool(gs.get("IsRobbyDead"))
        info.virginia_dead = bool(gs.get("IsVirginiaDead"))

    if "GameSetupSaveData.json" in files:
        setup = _inner(files["GameSetupSaveData.json"], "GameSetup")
        for setting in setup.get("_settings") or []:
            if setting.get("Name") == "Mode" and setting.get("StringValue"):
                info.mode = str(setting["StringValue"])

    if "WeatherSystemSaveData.json" in files:
        weather = _inner(files["WeatherSystemSaveData.json"], "WeatherSystem")
        season = weather.get("_currentSeason", 0)
        if isinstance(season, int) and 0 <= season < len(SEASONS):
            info.season = SEASONS[season]

    if "PlayerStateSaveData.json" in files:
        player = _inner(files["PlayerStateSaveData.json"], "PlayerState")
        entries = {e.get("Name"): e for e in player.get("_entries") or [] if isinstance(e, dict)}

        def f(name: str) -> Optional[float]:
            entry = entries.get(name)
            return None if entry is None else float(entry.get("FloatValue") or 0.0)

        info.health, info.health_max = f("CurrentHealth"), f("MaxHealth")
        info.fullness, info.hydration, info.rest = f("Fullness"), f("Hydration"), f("Rest")
        if "StrengthLevel" in entries:
            info.strength_level = int(entries["StrengthLevel"].get("IntValue") or 0)
        pos = (entries.get("player.position") or {}).get("FloatArrayValue")
        if isinstance(pos, list) and len(pos) == 3:
            info.pos = (float(pos[0]), float(pos[1]), float(pos[2]))
    return info


class SaveWatcher:
    def __init__(self, saves_dir: str):
        self.saves_dir = os.path.expandvars(saves_dir)
        self._cache: Dict[Tuple[str, float], SaveInfo] = {}

    def _candidates(self):
        for save_type in SAVE_TYPES:
            pattern = os.path.join(self.saves_dir, "*", save_type, "*")
            for folder in glob.glob(pattern):
                if not os.path.isdir(folder):
                    continue
                zip_path = os.path.join(folder, "SaveData.zip")
                if os.path.isfile(zip_path):
                    yield zip_path, save_type, os.path.basename(folder), os.path.getmtime(zip_path)
                elif os.path.isfile(os.path.join(folder, "GameStateSaveData.json")):
                    yield folder, save_type, os.path.basename(folder), os.path.getmtime(os.path.join(folder, "GameStateSaveData.json"))

    def latest(self) -> Optional[SaveInfo]:
        try:
            candidates = sorted(self._candidates(), key=lambda c: c[3], reverse=True)
        except OSError:
            return None
        for path, save_type, save_id, mtime in candidates[:3]:
            key = (path, mtime)
            if key in self._cache:
                return self._cache[key]
            try:
                info = parse_save(path, save_type, save_id, mtime)
            except (OSError, ValueError, zipfile.BadZipFile) as exc:
                log.debug("sauvegarde illisible %s (%s)", path, exc)   # en cours d'écriture ?
                continue
            self._cache = {key: info}
            return info
        return None

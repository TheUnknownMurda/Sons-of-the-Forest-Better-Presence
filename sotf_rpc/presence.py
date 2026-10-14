"""Construit l'activité Discord à partir du mod temps réel (live.json) ou, à défaut, de la dernière sauvegarde."""

from __future__ import annotations

import math
import re
import time
from datetime import datetime
from typing import List, Optional, Tuple

from .game import GameProcess
from .i18n import mode_name, period_name, season_name, t, weather_name
from .live import LiveState
from .saves import SaveInfo

# Une sauvegarde peut être horodatée un peu avant l'heure de lancement mesurée.
CLOCK_SLACK = 90
MAX_PLAYERS = 8
CENTER_RADIUS = 450        # m : en deçà, « centre de l'île » (la montagne)
MOUNTAIN_ALTITUDE = 400    # m
BUNKER_POI_RADIUS = 300    # m : distance max entre le joueur (dans un bunker) et l'entrée de ce bunker
COMPANION_NEAR = 40        # m : en deçà, « Kelvin t'accompagne »
REGION_KEYS = ("n", "ne", "e", "se", "s", "sw", "w", "nw")
STATUS_DISPLAY_TYPES = {"name": 0, "state": 1, "details": 2}

# États prioritaires (affichés en continu, sans rotation), du plus important au moins important.
URGENT_STATES = ("dead", "downed", "cutscene", "sleeping", "paused", "intro", "waking", "endgame", "burning", "boss")

# Petite icône associée à l'état / à l'activité (sinon : météo).
STATE_ICONS = {
    "dead": "dead", "downed": "sos", "cutscene": "cutscene", "sleeping": "sleep", "paused": "pause", "intro": "heli",
    "burning": "fire", "boss": "boss", "threat": "fight", "threat_mutants": "mutant", "knight_v": "knight",
    "gliding": "glider", "golf_cart": "cart", "raft": "raft", "underwater": "dive", "swimming": "swim",
    "bunker": "bunker", "cave": "cave",
}


def _truncate(text: str, limit: int = 128) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _join(*parts: str, sep: str = " · ") -> str:
    return sep.join(p for p in parts if p)


def _image(config: dict, key: str) -> Optional[str]:
    return (config.get("images") or {}).get(key) or None


def prettify_id(identifier: str) -> str:
    """``CannibalVillage_02`` → ``Cannibal Village``."""
    text = re.sub(r"[_\-.]+", " ", identifier or "")
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    text = re.sub(r"\s+\d+$", "", text.strip())
    return text or identifier


def region_key(x: float, z: float) -> str:
    """Secteur de l'île (+z = nord, +x = est), « center » près de l'origine."""
    if math.hypot(x, z) < CENTER_RADIUS:
        return "center"
    angle = math.degrees(math.atan2(x, z)) % 360
    return REGION_KEYS[int((angle + 22.5) // 45) % 8]


# ----------------------------------------------------------------- morceaux de texte

def _clock_text(config: dict, lang: str, hour: Optional[int], minute: Optional[int], night: Optional[bool]) -> str:
    mode = config.get("clock_mode", "exact")
    if hour is None or mode == "none":
        return ""
    if night is None:
        night = hour < 6 or hour >= 20
    exact = f"{hour:02d}:{(minute or 0):02d}"
    if mode == "period":
        return period_name(lang, hour)
    if mode == "both":
        return f"{period_name(lang, hour)} {exact}"
    return f"{'🌙' if night else '☀️'} {exact}"


def _day_text(config: dict, lang: str, day: Optional[int]) -> str:
    if day is None:
        return ""
    return t(lang, "day", day=day + int(config.get("day_offset", 0)))


def _percent(value: Optional[float], maximum: Optional[float]) -> Optional[int]:
    if value is None:
        return None
    maximum = maximum or 100.0
    return max(0, min(100, round(100.0 * value / maximum)))


def _vitals_text(config: dict, lang: str, live: LiveState) -> str:
    as_value = config.get("vitals_format") == "value"
    parts = []
    for icon, key in (("❤️", "health"), ("🍖", "fullness"), ("💧", "hydration"), ("💤", "rest")):
        value, maximum = live.vital(key), live.vital(f"{key}_max")
        if value is None:
            continue
        if as_value:
            parts.append(f"{icon} {round(value)}/{round(maximum or 100)}")
        else:
            parts.append(f"{icon} {_percent(value, maximum)}%")
    if live.vital_flag("cold") or live.flag("freezing"):
        parts.append(t(lang, "cold"))
    if live.vital_flag("sick"):
        parts.append(t(lang, "sick"))
    return _join(*parts)


def _item_title(item) -> str:
    if not isinstance(item, dict):
        return ""
    return str(item.get("title") or "").strip() or prettify_id(str(item.get("name") or ""))


def _location_text(config: dict, lang: str, live: LiveState) -> Tuple[str, str]:
    """(texte, catégorie) : catégorie ∈ cave, bunker, place, region, none."""
    area = str(live.get("area", "None"))
    first = area.split(",")[0].strip()
    names = config.get("area_names") or {}
    place = live.get("place")
    if first.startswith("Bunker"):
        named = names.get(first)
        # le point d'intérêt d'un bunker est à son entrée : le plus proche est celui où l'on se trouve
        if not named and isinstance(place, dict) and str(place.get("id", "")).startswith("Bunker") \
                and isinstance(place.get("dist"), (int, float)) and place["dist"] <= BUNKER_POI_RADIUS:
            named = (config.get("place_names") or {}).get(place["id"]) or place.get("name") or prettify_id(place["id"])
        return (t(lang, "in_bunker_named", name=named) if named else t(lang, "in_bunker")), "bunker"
    if first.startswith("Cave") or live.flag("in_caves"):
        named = names.get(first)
        return (t(lang, "in_cave_named", name=named) if named else t(lang, "in_cave")), "cave"

    radius = float(config.get("place_radius_m", 150))
    if isinstance(place, dict) and isinstance(place.get("dist"), (int, float)) and place["dist"] <= radius:
        pid = str(place.get("id") or "")
        name = (config.get("place_names") or {}).get(pid) or place.get("name") or prettify_id(pid)
        if name:
            return t(lang, "near", place=name), "place"

    pos = live.get("pos")
    if config.get("show_region", True) and isinstance(pos, list) and len(pos) == 3:
        x, y, z = pos
        if y >= MOUNTAIN_ALTITUDE:
            return t(lang, "mountain"), "region"
        return t(lang, "region", region=t(lang, region_key(x, z))), "region"
    return "", "none"


def _bare(text: str) -> str:
    """Texte de lieu sans son emoji de tête (pour l'accoler à une action)."""
    return text.split(" ", 1)[1] if " " in text else text


def _count_text(lang: str, kind: str, n: int) -> str:
    return t(lang, f"{kind}_1") if n == 1 else t(lang, f"{kind}_n", n=n)


def _threat_text(lang: str, live: LiveState) -> Tuple[str, str]:
    """(texte, clé) des ennemis proches, ou ("", "")."""
    threats = live.get("threats")
    if not isinstance(threats, dict):
        return "", ""
    cannibals, mutants = int(threats.get("cannibals") or 0), int(threats.get("mutants") or 0)
    if not cannibals and not mutants:
        return "", ""
    if not cannibals:
        return t(lang, "threat_mutants_only", who=_count_text(lang, "mutant", mutants)), "threat_mutants"
    who = _count_text(lang, "cannibal", cannibals)
    if mutants:
        who += t(lang, "and") + _count_text(lang, "mutant", mutants)
    return t(lang, "threat", who=who), "threat"


def _stats_text(lang: str, live: LiveState) -> str:
    stats = live.get("stats")
    if not isinstance(stats, dict):
        return ""
    kills = [t(lang, f"killed_{key}", n=int(stats[key])) for key in ("cannibals", "mutants", "animals")
             if isinstance(stats.get(key), (int, float)) and stats[key] > 0]
    trees = stats.get("trees")
    deaths = stats.get("deaths")
    return _join(t(lang, "trees", n=int(trees)) if isinstance(trees, (int, float)) and trees > 0 else "",
                 t(lang, "killed", list=", ".join(kills)) if kills else "",
                 t(lang, "deaths", n=int(deaths)) if isinstance(deaths, (int, float)) and deaths > 0 else "")


def _companions_text(lang: str, live: LiveState) -> str:
    parts = []
    for key, name in (("kelvin", "Kelvin"), ("virginia", "Virginia")):
        info = live.get(key)
        if not isinstance(info, dict):
            info = {"alive": not live.flag(f"{key}_dead")}
        dist = info.get("dist")
        if not info.get("alive", True):
            parts.append(t(lang, "companion_dead", name=name))
        elif isinstance(dist, (int, float)) and dist <= COMPANION_NEAR:
            parts.append(t(lang, "companion_with", name=name))
        elif isinstance(dist, (int, float)):
            parts.append(t(lang, "companion_dist", name=name, d=int(dist)))
        else:
            parts.append(t(lang, "companion_alive", name=name))
    return "👥 " + _join(*parts)


def _activity_text(config: dict, lang: str, live: LiveState) -> Tuple[str, bool, str]:
    """(texte, prioritaire, clé). Prioritaire = affiché en continu ; la clé change quand l'activité change
    de nature (pour envoyer ces changements à Discord sans attendre)."""
    view = str(live.get("view", ""))
    conditions = {
        "dead": live.flag("dead"),
        "downed": live.flag("downed"),
        "cutscene": live.flag("cutscene"),
        "sleeping": view == "Sleep",
        "paused": live.flag("paused") and not live.flag("multiplayer"),
        "intro": view == "PlaneCrash",
        "waking": view == "WakingUp",
        "endgame": live.flag("endgame"),
        "burning": live.flag("burning"),
        "boss": live.flag("boss"),
    }
    for key in URGENT_STATES:
        if conditions[key]:
            return t(lang, key), True, key
    threat, threat_key = _threat_text(lang, live)
    if threat:
        return threat, True, threat_key

    location, kind = _location_text(config, lang, live)
    for flag in ("knight_v", "gliding", "golf_cart", "raft", "underwater", "in_water", "constructing"):
        if live.flag(flag):
            key = "swimming" if flag == "in_water" else flag
            suffix = _bare(location) if kind in ("place", "region") else ""
            return _join(t(lang, key), suffix), False, key
    if view in ("Inventory", "Loot", "GrabBag"):
        return t(lang, "inventory"), False, "inventory"
    return location or t(lang, "exploring"), False, f"{kind}:{location}"


def _small_icon(lang: str, live: LiveState, activity_key: str) -> Tuple[str, str]:
    """(clé d'image, texte météo)."""
    rain = str(live.get("rain", "None"))
    if live.flag("snowing"):
        weather_key, weather = "snow", weather_name(lang, "snow")
    elif rain in ("Light", "Medium", "Heavy"):
        weather_key = {"Light": "rain_light", "Medium": "rain", "Heavy": "storm"}[rain]
        weather = weather_name(lang, rain)
    elif live.flag("night"):
        weather_key, weather = "night", weather_name(lang, "clear_night")
    else:
        weather_key, weather = "day", weather_name(lang, "clear_day")

    icon = STATE_ICONS.get(activity_key.split(":", 1)[0])
    return icon or weather_key, weather


def _party_text(lang: str, live: LiveState) -> str:
    if not live.flag("multiplayer"):
        return t(lang, "solo")
    return t(lang, "coop_host") if live.flag("host") else t(lang, "coop_client")


# ----------------------------------------------------------------- activité

def _base_activity(config: dict, process: GameProcess, world_since: Optional[float]) -> dict:
    activity: dict = {"assets": {}}
    timer = config.get("timer", "game")
    if timer == "world" and world_since:
        activity["timestamps"] = {"start": int(world_since)}
    elif timer != "none":
        activity["timestamps"] = {"start": int(process.start_time)}
    buttons = [b for b in (config.get("buttons") or []) if b.get("label") and b.get("url")][:2]
    if buttons:
        activity["buttons"] = [{"label": _truncate(b["label"], 32), "url": b["url"]} for b in buttons]
    return activity


def _save_summary(lang: str, save: Optional[SaveInfo]) -> str:
    if save is None:
        return ""
    day = t(lang, "day", day=save.day) if save.day is not None else ""
    return _join(day, mode_name(lang, save.mode) if save.mode else "")


def _finish(config: dict, activity: dict) -> dict:
    display = STATUS_DISPLAY_TYPES.get(str(config.get("status_display", "name")))
    if display:  # 0 (nom du jeu) = comportement par défaut de Discord : rien à envoyer
        activity["status_display_type"] = display
    for key in ("details", "state"):
        if key in activity:
            activity[key] = _truncate(activity[key])
            if len(activity[key]) < 2:
                del activity[key]
    assets = activity.get("assets") or {}
    for key in ("large_text", "small_text"):
        if key in assets:
            assets[key] = _truncate(assets[key])
            if len(assets[key]) < 2:
                del assets[key]
    assets = {k: v for k, v in assets.items() if v}
    if assets:
        activity["assets"] = assets
    else:
        activity.pop("assets", None)
    return activity


def build_activity(config: dict, lang: str, process: Optional[GameProcess], live: Optional[LiveState],
                   save: Optional[SaveInfo], now: Optional[float] = None,
                   world_since: Optional[float] = None) -> Tuple[str, Optional[dict], str]:
    """Retourne (statut, activité, clé). Statuts : not_running, menu, loading, live, save.
    La clé change quand la situation change de nature (mort, combat, grotte…) : ces changements
    méritent d'être envoyés tout de suite, les autres (horloge, vitals) peuvent attendre."""
    now = now or time.time()
    if process is None:
        return "not_running", None, "not_running"
    activity = _base_activity(config, process, world_since)
    assets = activity["assets"]

    if live is not None and live.in_world:
        activity, key = _live_activity(config, lang, live, activity, now)
        return "live", _finish(config, activity), f"live:{key}"

    in_world_save = save is not None and save.mtime >= process.start_time - CLOCK_SLACK
    if live is None and in_world_save:
        return "save", _finish(config, _save_activity(config, lang, save, activity)), "save"

    # menus / chargement
    loading = live is not None and live.scene == "Loading"
    activity["details"] = t(lang, "loading") if loading else t(lang, "menu")
    summary = _save_summary(lang, save)
    if summary:
        activity["state"] = t(lang, "last_game", summary=summary)
    elif not loading:
        activity["state"] = t(lang, "title_screen")
    assets["large_image"] = _image(config, "menu")
    assets["large_text"] = "Sons of the Forest"
    assets["small_image"] = _image(config, "loading" if loading else "menu_small")
    if live is None:   # sans le mod, « dans les menus » n'est qu'une supposition
        assets["small_text"] = t(lang, "no_mod")
    else:
        assets["small_text"] = t(lang, "loading") if loading else t(lang, "title_screen")
    status = "loading" if loading else "menu"
    return status, _finish(config, activity), status


def _live_activity(config: dict, lang: str, live: LiveState, activity: dict, now: float) -> Tuple[dict, str]:
    assets = activity["assets"]
    day = live.num("day")
    hour, minute = live.num("hour"), live.num("minute")
    activity["details"] = _join(
        _day_text(config, lang, int(day) if day is not None else None),
        season_name(lang, str(live.get("season", ""))) if live.get("season") else "",
        _clock_text(config, lang, int(hour) if hour is not None else None,
                    int(minute) if minute is not None else None, live.flag("night") if "night" in live.raw else None),
    ) or t(lang, "in_game")

    # 2e ligne : action prioritaire, sinon rotation activité / vitals / stats / compagnons / objet
    action, urgent, key = _activity_text(config, lang, live)
    lines: List[str] = []
    for entry in config.get("state_rotation") or ["activity"]:
        if entry == "activity":
            lines.append(action)
        elif entry == "vitals":
            lines.append(_vitals_text(config, lang, live))
        elif entry == "held":
            title = _item_title(live.get("held"))
            lines.append(t(lang, "held_line", item=title) if title else t(lang, "empty_hands"))
        elif entry == "companions":
            lines.append(_companions_text(lang, live))
        elif entry == "stats":
            lines.append(_stats_text(lang, live))
    lines = [line or action for line in lines] or [action]   # ligne indisponible → activité (cycle stable)
    if urgent:
        activity["state"] = action
    else:
        period = max(5.0, float(config.get("rotate_seconds", 20)))
        activity["state"] = lines[int(now // period) % len(lines)]

    # logo : mode, coop, force
    strength = live.vital("strength_level")
    pos = live.get("pos")
    assets["large_image"] = _image(config, "logo")
    assets["large_text"] = _join(
        mode_name(lang, str(live.get("mode", ""))) if live.get("mode") else "",
        _party_text(lang, live),
        t(lang, "strength", n=int(strength)) if strength else "",
        t(lang, "position", x=round(pos[0]), y=round(pos[1]), z=round(pos[2]))
        if config.get("show_position") and isinstance(pos, list) and len(pos) == 3 else "",
    )

    # petite icône : état / météo + objet en main
    icon, weather = _small_icon(lang, live, key)
    held = _item_title(live.get("held")) if config.get("show_held_item", True) else ""
    assets["small_image"] = _image(config, icon)
    assets["small_text"] = _join(weather, t(lang, "held", item=held) if held else "")

    if live.flag("multiplayer"):
        players = int(live.num("players") or 1)
        maximum = int(live.num("max_players") or MAX_PLAYERS)
        activity["party"] = {"id": f"sotf-{live.get('save_id', 0)}", "size": [max(1, players), max(players, maximum)]}
    return activity, key


def _save_activity(config: dict, lang: str, save: SaveInfo, activity: dict) -> dict:
    assets = activity["assets"]
    activity["details"] = _join(
        _day_text(config, lang, save.day),
        season_name(lang, save.season) if save.season else "",
        _clock_text(config, lang, save.hour, save.minute, None),
    ) or t(lang, "in_game")
    saved_at = datetime.fromtimestamp(save.mtime).strftime("%H:%M")
    activity["state"] = _join(t(lang, "saved_at", time=saved_at),
                              mode_name(lang, save.mode) if save.mode else "")
    multiplayer = save.save_type != "SinglePlayer"
    assets["large_image"] = _image(config, "logo")
    assets["large_text"] = _join(
        t(lang, "coop_client") if multiplayer else t(lang, "solo"),
        t(lang, "strength", n=save.strength_level) if save.strength_level else "",
        t(lang, "no_mod"),
    )
    assets["small_image"] = _image(config, "save")
    health = _percent(save.health, save.health_max)
    assets["small_text"] = _join(f"❤️ {health}%" if health is not None else "",
                                 f"🍖 {_percent(save.fullness, 100)}%" if save.fullness is not None else "",
                                 f"💧 {_percent(save.hydration, 100)}%" if save.hydration is not None else "")
    return activity

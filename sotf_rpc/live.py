"""Source « temps réel » : ``live.json`` écrit par le mod RedLoader (dossier ``mod/``).

Le mod réécrit le fichier toutes les 2 s quand quelque chose change (au moins toutes les 10 s).
S'il est absent, illisible ou plus vieux que ``stale_seconds``, on retombe sur les sauvegardes.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)

# Un fichier en cours de remplacement peut manquer quelques ms : on garde la dernière valeur valide.
REWRITE_GRACE = 5


class LiveError(ValueError):
    """Le fichier ne contient pas un état valide."""


@dataclass
class LiveState:
    ts: float
    raw: dict = field(default_factory=dict)

    @property
    def mod_version(self) -> str:
        return str(self.raw.get("mod") or "")

    @property
    def scene(self) -> str:
        return str(self.raw.get("scene") or "")

    @property
    def in_world(self) -> bool:
        return bool(self.raw.get("in_world"))

    @property
    def lang(self) -> str:
        return str(self.raw.get("lang") or "")

    def get(self, key: str, default=None):
        value = self.raw.get(key, default)
        return default if value is None else value

    def num(self, key: str) -> Optional[float]:
        value = self.raw.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return value

    def flag(self, key: str) -> bool:
        return self.raw.get(key) is True

    def vital(self, key: str) -> Optional[float]:
        vitals = self.raw.get("vitals")
        if not isinstance(vitals, dict):
            return None
        value = vitals.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return value

    def vital_flag(self, key: str) -> bool:
        vitals = self.raw.get("vitals")
        return isinstance(vitals, dict) and vitals.get(key) is True

    def age(self, now: Optional[float] = None) -> float:
        return (now or time.time()) - self.ts


def parse_live(text: str) -> LiveState:
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise LiveError(f"JSON invalide : {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("ts"), (int, float)):
        raise LiveError("champ ts manquant")
    return LiveState(ts=float(data["ts"]), raw=data)


class LiveReader:
    def __init__(self, path: str, stale_seconds: float = 30):
        self.path = os.path.expandvars(path)
        self.stale_seconds = float(stale_seconds)
        self._last: Optional[LiveState] = None
        self._last_read_at = 0.0
        self._last_error = ""

    def _read_file(self) -> Optional[LiveState]:
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            return None
        try:
            return parse_live(text)
        except LiveError as exc:
            if str(exc) != self._last_error:
                self._last_error = str(exc)
                log.debug("live.json illisible (%s), nouvel essai plus tard", exc)
            return None

    def read(self, now: Optional[float] = None) -> Optional[LiveState]:
        """État courant du mod, ou None si absent / périmé."""
        now = now or time.time()
        state = self._read_file()
        if state is not None:
            self._last, self._last_read_at = state, now
        elif self._last is not None and now - self._last_read_at > REWRITE_GRACE:
            self._last = None
        state = self._last
        if state is None or state.age(now) > self.stale_seconds:
            return None
        return state

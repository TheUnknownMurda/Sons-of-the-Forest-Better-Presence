"""Tests de construction de la presence : ``python -m unittest discover -s tests``."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sotf_rpc.config import DEFAULTS  # noqa: E402
from sotf_rpc.game import GameProcess  # noqa: E402
from sotf_rpc.live import LiveReader, parse_live  # noqa: E402
from sotf_rpc.presence import build_activity, prettify_id, region_key  # noqa: E402
from sotf_rpc.saves import SaveWatcher  # noqa: E402

NOW = 1_800_000_000.0
PROCESS = GameProcess(pid=1234, exe_name="SonsOfTheForest.exe", start_time=NOW - 3600)


def config(**overrides) -> dict:
    cfg = json.loads(json.dumps(DEFAULTS))
    cfg.update(overrides)
    return cfg


def live(**fields):
    raw = {
        "ts": NOW, "mod": "1.0.0", "scene": "Game", "lang": "fr", "in_world": True,
        "mode": "HardSurvival", "save_type": "SinglePlayer", "save_id": 42, "multiplayer": False,
        "day": 12, "hour": 22, "minute": 5, "night": True, "season": "Fall", "rain": "None", "snowing": False,
        "vitals": {"health": 62, "health_max": 124, "stamina": 80, "stamina_max": 100, "fullness": 55, "fullness_max": 100,
                   "hydration": 40.4, "hydration_max": 100, "rest": 90, "rest_max": 100, "strength_level": 13,
                   "cold": False, "sick": False, "hungry": False, "thirsty": False, "tired": False},
        "view": "World", "dead": False, "paused": False, "in_water": False, "underwater": False, "gliding": False,
        "golf_cart": False, "raft": False, "constructing": False, "endgame": False,
        "held": {"id": 379, "name": "TacticalAxe", "title": "Hache tactique"}, "left": None,
        "area": "None", "in_caves": False, "deep_caves": False, "pos": [900.0, 40.0, 900.0],
        "kelvin_dead": False, "virginia_dead": True, "crash_site": "snow",
    }
    raw.update(fields)
    return parse_live(json.dumps(raw))


class LiveActivityTests(unittest.TestCase):
    def build(self, state, cfg=None, now=NOW):
        status, activity, _key = build_activity(cfg or config(), "fr", PROCESS, state, None, now)
        return status, activity

    def key(self, state):
        return build_activity(config(), "fr", PROCESS, state, None, NOW)[2]

    def test_world_lines(self):
        status, act = self.build(live())
        self.assertEqual(status, "live")
        self.assertEqual(act["details"], "Jour 12 · 🍂 Automne · 🌙 22:05")
        self.assertEqual(act["assets"]["large_text"], "Survie difficile · Solo · Force niv. 13")
        self.assertEqual(act["assets"]["small_text"], "🌙 Nuit · En main : Hache tactique")
        self.assertTrue(act["assets"]["small_image"].endswith("1f319.png"))
        self.assertEqual(act["timestamps"]["start"], int(PROCESS.start_time))
        self.assertNotIn("party", act)

    def test_rotation_activity_then_vitals(self):
        cfg = config(state_rotation=["activity", "vitals"])
        first = self.build(live(), cfg, now=NOW)[1]["state"]           # 1.8e9 / 20 → index pair → activité
        second = self.build(live(), cfg, now=NOW + 20)[1]["state"]
        self.assertEqual(first, "🧭 Nord-est de l'île")
        self.assertEqual(second, "❤️ 50% · 🍖 55% · 💧 40% · 💤 90%")

    def test_default_rotation_cycle(self):
        state = live(stats={"cannibals": 12, "mutants": 0, "animals": 3, "trees": 245, "deaths": 2},
                     kelvin={"alive": True, "dist": 12}, virginia={"alive": False})
        lines = [self.build(state, now=NOW + 20 * i)[1]["state"] for i in range(6)]
        self.assertEqual(lines[0], "🧭 Nord-est de l'île")
        self.assertEqual(lines[2], lines[0])
        self.assertEqual(lines[3], "🪓 245 arbres coupés · ⚔️ Tués : 12 cannibales, 3 animaux · 💀 2 morts")
        self.assertEqual(lines[5], "👥 Kelvin t'accompagne · Virginia ✝️")
        far = self.build(live(kelvin={"alive": True, "dist": 230.4}, virginia={"alive": True}), now=NOW + 100)[1]
        self.assertEqual(far["state"], "👥 Kelvin à 230 m · Virginia ✅")

    def test_urgent_state_does_not_rotate(self):
        for now in (NOW, NOW + 20):
            self.assertEqual(self.build(live(view="Sleep"), now=now)[1]["state"], "😴 Dort")

    def test_urgent_priorities(self):
        self.assertEqual(self.build(live(cutscene=True, view="Sleep"))[1]["state"], "🎬 Cinématique")
        self.assertEqual(self.build(live(dead=True, downed=True))[1]["state"], "💀 Mort…")
        act = self.build(live(downed=True, multiplayer=True))[1]
        self.assertEqual(act["state"], "🆘 À terre, attend de l'aide")
        self.assertTrue(act["assets"]["small_image"].endswith("1f198.png"))
        self.assertEqual(self.build(live(boss=True))[1]["state"], "☠️ Combat contre un boss")

    def test_threats(self):
        for now in (NOW, NOW + 20, NOW + 40):
            act = self.build(live(threats={"cannibals": 3, "mutants": 1, "nearest": 12}), now=now)[1]
            self.assertEqual(act["state"], "⚔️ Face à 3 cannibales et un mutant")
        act = self.build(live(threats={"cannibals": 0, "mutants": 2}))[1]
        self.assertEqual(act["state"], "👹 Face à 2 mutants")
        self.assertTrue(act["assets"]["small_image"].endswith("1f479.png"))
        self.assertEqual(self.build(live(threats={"cannibals": 1, "mutants": 0}))[1]["state"], "⚔️ Face à un cannibale")

    def test_activity_key_changes_with_situation(self):
        calm = self.key(live())
        self.assertEqual(calm, self.key(live(hour=23, vitals={"health": 10})))   # horloge / vitals : même clé
        self.assertNotEqual(calm, self.key(live(threats={"cannibals": 2, "mutants": 0})))
        self.assertNotEqual(calm, self.key(live(area="CaveA", in_caves=True)))
        self.assertEqual(self.key(live(threats={"cannibals": 2, "mutants": 0})),
                         self.key(live(threats={"cannibals": 3, "mutants": 0})))

    def test_knight_v_and_status_display(self):
        act = self.build(live(knight_v=True), cfg=config(status_display="details"))[1]
        self.assertEqual(act["state"], "🛹 Sur le Knight V · Nord-est de l'île")
        self.assertEqual(act["status_display_type"], 2)
        self.assertNotIn("status_display_type", self.build(live())[1])

    def test_near_place_and_cave(self):
        act = self.build(live(place={"id": "CannibalVillage_02", "name": None, "dist": 80}))[1]
        self.assertEqual(act["state"], "📍 Près de : Cannibal Village")
        act = self.build(live(area="CaveB", in_caves=True))[1]
        self.assertEqual(act["state"], "🕳️ Dans une grotte")
        self.assertTrue(act["assets"]["small_image"].endswith("1f573.png"))
        named = self.build(live(area="BunkerA"), cfg=config(area_names={"BunkerA": "Bunker de maintenance A"}))[1]
        self.assertEqual(named["state"], "🚪 Bunker de maintenance A")
        from_poi = self.build(live(area="BunkerF", place={"id": "Bunker Food", "name": "Bunker à nourriture", "dist": 120}))[1]
        self.assertEqual(from_poi["state"], "🚪 Bunker à nourriture")
        far = self.build(live(area="BunkerF", place={"id": "Bunker Food", "name": "Bunker à nourriture", "dist": 900}))[1]
        self.assertEqual(far["state"], "🚪 Dans un bunker")

    def test_vehicle_keeps_location(self):
        act = self.build(live(gliding=True))[1]
        self.assertEqual(act["state"], "🪂 En deltaplane · Nord-est de l'île")

    def test_multiplayer_party(self):
        act = self.build(live(multiplayer=True, host=True, players=3, max_players=8))[1]
        self.assertEqual(act["party"], {"id": "sotf-42", "size": [3, 8]})
        self.assertIn("Coop (hôte)", act["assets"]["large_text"])

    def test_weather_icon(self):
        act = self.build(live(rain="Heavy"))[1]
        self.assertTrue(act["assets"]["small_image"].endswith("26c8.png"))
        self.assertTrue(act["assets"]["small_text"].startswith("⛈️ Pluie battante"))

    def test_menu_and_loading(self):
        status, act, _ = build_activity(config(), "fr", PROCESS, live(in_world=False, scene="Title"), None, NOW)
        self.assertEqual((status, act["details"], act["state"]), ("menu", "Dans les menus", "🏠 Écran titre"))
        status, act, _ = build_activity(config(), "en", PROCESS, live(in_world=False, scene="Loading"), None, NOW)
        self.assertEqual((status, act["details"]), ("loading", "⏳ Loading the game…"))

    def test_not_running(self):
        self.assertEqual(build_activity(config(), "fr", None, live(), None, NOW)[:2], ("not_running", None))

    def test_limits(self):
        act = self.build(live(place={"id": "x", "name": "N" * 300, "dist": 1}))[1]
        self.assertLessEqual(len(act["state"]), 128)
        self.assertTrue(all(len(b["label"]) <= 32 for b in act.get("buttons", [])))


class HelperTests(unittest.TestCase):
    def test_region(self):
        self.assertEqual(region_key(0, 100), "center")
        self.assertEqual(region_key(0, 1500), "n")
        self.assertEqual(region_key(1500, 0), "e")
        self.assertEqual(region_key(-1000, -1000), "sw")

    def test_prettify(self):
        self.assertEqual(prettify_id("Bunker_Entertainment"), "Bunker Entertainment")
        self.assertEqual(prettify_id("LakeHouse-3"), "Lake House")


class ExitWithGameTests(unittest.TestCase):
    def test_should_exit(self):
        from sotf_rpc.__main__ import App, EXIT_GRACE, EXIT_WAIT_FOR_GAME
        app = App(config(), dry_run=True, simulate=False, exit_with_game=True)
        self.assertFalse(app.should_exit())
        app.started_at -= EXIT_WAIT_FOR_GAME + 1
        self.assertTrue(app.should_exit())                     # le jeu n'est jamais apparu
        app.game_seen_at = time.time()
        self.assertFalse(app.should_exit())                    # jeu lancé
        app.game_seen_at -= EXIT_GRACE + 1
        self.assertTrue(app.should_exit())                     # jeu fermé
        app.exit_with_game = False
        self.assertFalse(app.should_exit())


class StorageTests(unittest.TestCase):
    def test_live_reader_staleness(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "live.json")
            reader = LiveReader(path, stale_seconds=30)
            self.assertIsNone(reader.read())
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"ts": time.time(), "in_world": False, "scene": "Title"}, fh)
            self.assertIsNotNone(reader.read())
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"ts": time.time() - 120, "in_world": False}, fh)
            self.assertIsNone(reader.read())

    def test_save_zip(self):
        def wrap(key, inner):
            return json.dumps({"Version": "0.0.0", "Data": {key: json.dumps(inner)}})

        with tempfile.TemporaryDirectory() as tmp:
            folder = os.path.join(tmp, "7656", "SinglePlayer", "123")
            os.makedirs(folder)
            with zipfile.ZipFile(os.path.join(folder, "SaveData.zip"), "w") as zf:
                zf.writestr("GameStateSaveData.json", wrap("GameState", {"GameType": "Normal", "GameDays": 6, "GameHours": 16,
                                                                         "GameMinutes": 14, "IsVirginiaDead": True}))
                zf.writestr("GameSetupSaveData.json", wrap("GameSetup", {"_settings": [{"Name": "Mode", "StringValue": "Hard"}]}))
                zf.writestr("WeatherSystemSaveData.json", wrap("WeatherSystem", {"_currentSeason": 2}))
                zf.writestr("PlayerStateSaveData.json", wrap("PlayerState", {"_entries": [
                    {"Name": "CurrentHealth", "FloatValue": 62.0}, {"Name": "MaxHealth", "FloatValue": 124.0},
                    {"Name": "StrengthLevel", "IntValue": 13}, {"Name": "player.position", "FloatArrayValue": [1, 2, 3]}]}))
            save = SaveWatcher(tmp).latest()
            self.assertEqual((save.mode, save.day, save.hour, save.minute, save.season), ("Hard", 6, 16, 14, "Fall"))
            self.assertTrue(save.virginia_dead)
            self.assertEqual((save.health, save.strength_level, save.pos), (62.0, 13, (1.0, 2.0, 3.0)))

            process = GameProcess(1, "x", save.mtime - 10)
            status, act, _ = build_activity(config(), "fr", process, None, save, save.mtime + 5)
            self.assertEqual(status, "save")
            self.assertEqual(act["details"], "Jour 6 · 🍂 Automne · ☀️ 16:14")
            self.assertTrue(act["state"].startswith("💾 Sauvegarde de "))


if __name__ == "__main__":
    unittest.main()

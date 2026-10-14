"""Point d'entrée : ``python -m sotf_rpc [options]``."""

from __future__ import annotations

import argparse
import json
import logging
import logging.handlers
import os
import sys
import time
from typing import Optional

from . import __version__
from .config import load_config
from .discord_ipc import DiscordIPC, DiscordNotRunning
from .game import GameProcess, find_game
from .i18n import resolve_lang
from .live import LiveReader
from .presence import build_activity
from .saves import SaveWatcher

log = logging.getLogger("sotf_rpc")

# Discord accepte 5 SET_ACTIVITY par 20 s. Un changement de situation (mort, combat, grotte…) part
# après 5 s au plus ; l'horloge, les vitals et la rotation des lignes, toutes les 15 s.
FAST_UPDATE_INTERVAL = 5
MIN_UPDATE_INTERVAL = 15
RECONNECT_INTERVAL = 20
SAVE_REFRESH_INTERVAL = 15
MUTEX_NAME = r"Local\SotFRPC.Companion"   # même nom que dans le mod (CompanionLauncher.cs)
EXIT_GRACE = 15               # --exit-with-game : délai après la fermeture du jeu
EXIT_WAIT_FOR_GAME = 300      # --exit-with-game : abandon si le jeu n'apparaît pas


def acquire_single_instance():
    """Mutex nommé : None si une autre instance du compagnon tourne déjà."""
    if os.name != "nt":
        return True
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle or kernel32.GetLastError() == 183:   # ERROR_ALREADY_EXISTS
        return None
    return handle    # gardé ouvert jusqu'à la fin du processus


def setup_logging(verbose: bool) -> None:
    # La console Windows est souvent en cp1252 : on force l'UTF-8 pour les emojis/accents.
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s", "%H:%M:%S")
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    if sys.stdout is not None:      # absent avec pythonw
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(fmt)
        root.addHandler(console)
    log_dir = os.path.join(os.environ.get("LOCALAPPDATA", "."), "SotFRPC")
    try:
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(os.path.join(log_dir, "sotf_rpc.log"), maxBytes=512_000,
                                                       backupCount=2, encoding="utf-8")
        handler.setFormatter(fmt)
        root.addHandler(handler)
    except OSError:
        pass


class App:
    def __init__(self, config: dict, dry_run: bool, simulate: bool, exit_with_game: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.simulate = simulate
        self.exit_with_game = exit_with_game
        self.started_at = time.time()
        self.game_seen_at: Optional[float] = None
        self.last_sent_key = ""
        self.live = LiveReader(config["live_path"], float(config.get("live_stale_seconds", 30)))
        self.saves = SaveWatcher(config["saves_dir"])
        self.ipc: Optional[DiscordIPC] = None if dry_run else DiscordIPC(config["client_id"])
        self.last_sent: Optional[dict] = None
        self.last_sent_at = 0.0
        self.next_connect = 0.0
        self.pending_key = ""
        self.live_active: Optional[bool] = None
        self.world_since: Optional[float] = None
        self.save = None
        self.save_checked_at = 0.0
        self.pid: Optional[int] = None
        self._simulated: Optional[GameProcess] = None
        log.info("Sons of the Forest Rich Presence %s · temps réel : %s", __version__, self.live.path)

    # ------------------------------------------------------------- Discord
    def _ensure_connected(self) -> bool:
        if self.ipc is None or self.ipc.connected:
            return True
        if time.time() < self.next_connect:
            return False
        self.next_connect = time.time() + RECONNECT_INTERVAL
        try:
            self.ipc.connect()
            self.last_sent = None
            return True
        except DiscordNotRunning as exc:
            log.warning("Discord n'est pas joignable (%s) ; nouvel essai dans %ds", exc, RECONNECT_INTERVAL)
        except Exception as exc:  # handshake refusé, etc.
            log.error("connexion Discord impossible : %s", exc)
        return False

    def _send(self, activity: Optional[dict]) -> None:
        if self.ipc is None:
            log.info("[dry-run] activité → %s", json.dumps(activity, ensure_ascii=False) if activity else "effacée")
            self.last_sent, self.last_sent_at, self.last_sent_key = activity, time.time(), self.pending_key
            return
        if not self._ensure_connected():
            return
        try:
            if activity is None:
                self.ipc.clear_activity(self.pid)
            else:
                self.ipc.set_activity(activity, self.pid)
            self.last_sent, self.last_sent_at, self.last_sent_key = activity, time.time(), self.pending_key
            log.info("presence %s", "effacée" if activity is None
                     else f"mise à jour : {activity.get('details')} | {activity.get('state')}")
        except Exception as exc:
            log.warning("envoi à Discord échoué (%s) ; reconnexion", exc)
            self.ipc.close()
            self.last_sent = None      # force un nouvel envoi après reconnexion
            self.next_connect = time.time() + 5

    # ---------------------------------------------------------------- boucle
    def _current_process(self) -> Optional[GameProcess]:
        if self.simulate:
            if self._simulated is None:
                self._simulated = GameProcess(pid=os.getpid(), exe_name="simulation", start_time=time.time() - 3600)
            return self._simulated
        return find_game(self.config.get("process_names") or ["SonsOfTheForest.exe"])

    def tick(self) -> None:
        now = time.time()
        process = self._current_process()
        if process is not None:
            self.game_seen_at = now
        if process is None:
            self.world_since = None
            if self.last_sent is not None:
                self._send(None)
            self.pid = None
            return
        if self.pid != process.pid and self.last_sent is not None and self.ipc is not None and self.ipc.connected:
            try:
                self.ipc.clear_activity(self.pid)   # ancienne instance du jeu
            except Exception:
                pass
        self.pid = process.pid

        live = self.live.read(now)
        active = live is not None
        if active != self.live_active:
            self.live_active = active
            if active:
                log.info("mod temps réel détecté (v%s)", live.mod_version or "?")
            else:
                log.info("mod temps réel absent ou muet : repli sur les sauvegardes")
        if live is not None and live.in_world:
            self.world_since = self.world_since or now
        else:
            self.world_since = None

        # les sauvegardes ne servent qu'hors partie (résumé « dernière partie ») ou sans le mod
        if not (live is not None and live.in_world) and now - self.save_checked_at >= SAVE_REFRESH_INTERVAL:
            self.save_checked_at = now
            self.save = self.saves.latest()

        lang = resolve_lang(self.config.get("language", "auto"), live.lang if live else "")
        status, activity, key = build_activity(self.config, lang, process, live, self.save, now, self.world_since)
        if activity == self.last_sent:
            return
        wait = FAST_UPDATE_INTERVAL if key != self.last_sent_key else MIN_UPDATE_INTERVAL
        if self.last_sent is not None and now - self.last_sent_at < wait:
            return  # on réessaiera au prochain tick
        log.debug("état %s (%s)", status, key)
        self.pending_key = key
        self._send(activity)

    def should_exit(self) -> bool:
        """--exit-with-game : le jeu est fermé (ou n'a jamais été lancé)."""
        if not self.exit_with_game:
            return False
        now = time.time()
        if self.game_seen_at is None:
            return now - self.started_at > EXIT_WAIT_FOR_GAME
        return now - self.game_seen_at > EXIT_GRACE

    def run_forever(self) -> None:
        interval = max(1.0, float(self.config.get("poll_interval_seconds", 3)))
        try:
            while True:
                try:
                    self.tick()
                except Exception:
                    log.exception("erreur pendant la mise à jour")
                if self.should_exit():
                    log.info("jeu fermé : arrêt du compagnon")
                    break
                time.sleep(interval)
        except KeyboardInterrupt:
            log.info("arrêt demandé")
        finally:
            if self.ipc is not None and self.ipc.connected:
                try:
                    self.ipc.clear_activity(self.pid)
                except Exception:
                    pass
                self.ipc.close()


def dump(config: dict) -> None:
    reader = LiveReader(config["live_path"], float(config.get("live_stale_seconds", 30)))
    live = reader.read()
    if live is None:
        print(f"live.json : absent ou périmé ({reader.path})")
    else:
        print(f"live.json (il y a {live.age():.0f} s) :")
        print(json.dumps(live.raw, ensure_ascii=False, indent=2))
    save = SaveWatcher(config["saves_dir"]).latest()
    print("dernière sauvegarde :", save if save else "aucune")


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(prog="sotf_rpc", description="Discord Rich Presence détaillée pour Sons of the Forest.")
    parser.add_argument("--config", help="chemin de config.json (défaut : à côté du dossier sotf_rpc)")
    parser.add_argument("--dry-run", action="store_true", help="n'envoie rien à Discord, affiche l'activité calculée")
    parser.add_argument("--once", action="store_true", help="une seule itération puis quitte")
    parser.add_argument("--simulate", action="store_true", help="fait comme si le jeu tournait (test sans lancer le jeu)")
    parser.add_argument("--dump", action="store_true", help="affiche live.json et la dernière sauvegarde puis quitte")
    parser.add_argument("--exit-with-game", action="store_true",
                        help="quitte quand le jeu se ferme (utilisé quand le mod lance le compagnon)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    setup_logging(args.verbose)
    config = load_config(args.config)
    if args.dump:
        dump(config)
        return 0

    client_id = str(config.get("client_id") or "").strip()
    if not args.dry_run and not client_id.isdigit():
        log.error("client_id invalide dans %s (Application ID Discord attendu). Utilise --dry-run pour tester sans Discord.",
                  config["_path"])
        return 2

    if not (args.dry_run or args.once):
        mutex = acquire_single_instance()
        if mutex is None:
            log.info("le compagnon tourne déjà (lancé par le mod ou au démarrage de Windows) : rien à faire")
            return 3   # code ≠ 0 : SotFRPC.bat garde la fenêtre ouverte pour afficher ce message

    app = App(config, dry_run=args.dry_run, simulate=args.simulate, exit_with_game=args.exit_with_game)
    if args.once:
        app.tick()
        if app.ipc is not None and app.ipc.connected:
            time.sleep(1)
            app.ipc.close()
        return 0
    app.run_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())

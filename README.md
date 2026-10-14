# Sons of the Forest · Discord Rich Presence détaillée

Affiche sur ton profil Discord ce que tu fais dans **Sons of the Forest**, mis à jour en temps réel : jour, saison,
heure, météo, bunker ou grotte où tu te trouves, ennemis autour de toi, santé, faim, soif, statistiques de ta
partie, Kelvin et Virginia…

```
Joue à Sons of the Forest                         [affiche du jeu]  [icône météo / état]
Jour 12 · 🍂 Automne · 🌙 22:05
🚪 Bunker à nourriture                    ← toutes les 20 s, en alternance :
❤️ 50% · 🍖 55% · 💧 40% · 💤 90%            ← vitals
🪓 245 arbres coupés · ⚔️ Tués : 12 cannibales, 3 mutants · 💀 2 morts
👥 Kelvin t'accompagne · Virginia à 320 m
1:23:45 écoulées                          (3 sur 8 en coop)
```

## Installation (5 minutes)

### Ce qu'il te faut

- **Windows 10 ou 11** et **Sons of the Forest** sur Steam.
- **Discord**, l'application de bureau (Stable, PTB ou Canary), ouverte sur le même PC.
- **Python 3.9 ou plus récent** : <https://www.python.org/downloads/> → *Download Python* → lance l'installeur
  (cocher *Add python.exe to PATH* est conseillé). Déjà installé ? Rien à faire.

Le reste est géré par l'installeur : le chargeur de mods [RedLoader](https://github.com/ToniMacaroni/RedLoader)
(téléchargé depuis sa page officielle s'il n'est pas déjà là) et le mod compilé.
Aucun compte, aucune application Discord à créer.

### Étapes

1. **Télécharge ce projet** : bouton vert **Code → Download ZIP** en haut de la page GitHub, puis
   *clic droit → Extraire tout*. Range le dossier extrait à un endroit où il restera
   (par exemple `Documents\Sons of the Forest Better Presence`) : le jeu va chercher la Rich Presence à cet endroit.
2. **Double-clique sur `Installer-le-mod.bat`**. Il trouve le jeu dans Steam, installe RedLoader si besoin
   (il te demande d'abord ; appuie sur Entrée pour accepter), copie le mod et repère Python.
   Il doit finir par **« Terminé ! »**.
   - Si Windows affiche *« Windows a protégé votre ordinateur »* : *Informations complémentaires* → *Exécuter quand même*.
   - Si le jeu n'est pas trouvé : voir [Ça ne marche pas ?](#ça-ne-marche-pas-).
3. **Lance Sons of the Forest depuis Steam**, comme d'habitude. La Rich Presence démarre et s'arrête toute seule
   avec le jeu. Si RedLoader vient d'être installé, le premier lancement prend 1 à 2 minutes de plus.
4. Dans Discord, vérifie **Paramètres → Confidentialité de l'activité → « Partager mon activité »** (activé).

C'est tout : ton profil affiche « Joue à Sons of the Forest » avec le détail de ta partie. Pour mettre à jour le
projet plus tard, remplace le dossier par la nouvelle version (au même endroit) et relance `Installer-le-mod.bat`.

### Ça ne marche pas ?

| Problème | Solution |
|----------|----------|
| Rien n'apparaît sur Discord | Vérifie « Partager mon activité » (étape 4) et que Discord est ouvert. Le journal `%LOCALAPPDATA%\SotFRPC\sotf_rpc.log` dit ce qui est envoyé. |
| « Dans les menus » alors que tu es en partie, ou rien ne bouge | Le mod n'est pas chargé. Sur l'écran titre, bouton **Mods** de RedLoader : `SotFRPC` ne doit pas être en jaune. Relance `Installer-le-mod.bat`, puis le jeu. Le journal du mod est `…\Sons Of The Forest\_Redloader\Latest.log` (lignes `SotFRPC`). |
| `SotFRPC` en jaune « Missing manifest.json » | Le dossier `Mods\SotFRPC\` manque : relance `Installer-le-mod.bat`. |
| L'installeur ne trouve pas le jeu | Steam → clic droit sur Sons of the Forest → *Gérer* → *Parcourir les fichiers locaux* pour copier le chemin, puis dans une invite de commandes ouverte dans ce dossier : `Installer-le-mod.bat -GamePath "D:\SteamLibrary\steamapps\common\Sons Of The Forest"` |
| Le téléchargement de RedLoader échoue | Installe-le à la main : [RedManager](https://github.com/ToniMacaroni/RedManager), ou le zip de la [release](https://github.com/ToniMacaroni/RedLoader/releases/latest) décompressé dans le dossier du jeu (le dossier `_Redloader` doit être à côté de `SonsOfTheForest.exe`). Puis relance `Installer-le-mod.bat`. |
| Le jeu ne démarre plus après l'installation de RedLoader | Installe le [Visual C++ Redistributable x64](https://aka.ms/vs/16/release/vc_redist.x64.exe) (prérequis de RedLoader). |
| L'installeur dit « Python introuvable » | Installe Python (voir *Ce qu'il te faut*), puis relance `Installer-le-mod.bat`. |
| J'ai déplacé le dossier du projet | Relance `Installer-le-mod.bat` depuis le nouvel emplacement. |
| Le mod ne se charge plus après une mise à jour du jeu | RedLoader régénère ses fichiers au lancement suivant ; si ça ne suffit pas, attends une nouvelle version de ce projet. |
| La presence est en anglais | Elle suit la langue du jeu. Pour l'imposer, voir `language` dans [Configuration](#configuration-configjson-optionnel). |

### Désinstaller

Double-clique sur **`Desinstaller-le-mod.bat`** : il retire le mod et, si aucun autre mod n'est installé, RedLoader
lui-même (le jeu redevient tel quel ; un RedLoader installé par Vortex est laissé à Vortex). Tu peux ensuite
supprimer le dossier du projet.

## Ce qui est affiché

- **Ligne 1** : jour en jeu (le même compteur que les sauvegardes), saison, heure (ou moment de la journée).
- **Ligne 2** : ce que tu fais ou où tu es (une ligne sur deux), en alternance avec tes vitals, tes
  statistiques de partie et tes compagnons.
  - Affichés en continu tant qu'ils durent : 💀 mort, 🆘 à terre (coop), 🎬 cinématique, 😴 sommeil,
    ⏸️ pause (solo), 🔥 en feu, ☠️ combat de boss, ⚔️ « Face à 3 cannibales et un mutant » (ennemis à moins de 35 m).
  - Activités : 🛹 Knight V, 🪂 deltaplane, 🛺 voiturette de golf, 🛶 radeau, 🤿 plongée, 🏊 nage, 🔨 construction,
    🎒 inventaire.
  - Lieux : bunkers **avec leur nom** (« Bunker de luxe », « Bunker à nourriture »…, traduit par le jeu), grotte,
    lieu nommé proche, secteur de l'île, ⛰️ montagne.
  - Vitals : santé / faim / soif / repos (🥶 froid, 🤢 malade).
  - Statistiques : arbres coupés, cannibales / mutants / animaux tués, nombre de morts.
  - Compagnons : Kelvin et Virginia (avec toi, à N m, ✝️).
- **Info-bulle du logo** : mode de jeu (Normal, Difficile, Survie difficile, Paisible, Créatif, Personnalisé),
  solo / coop (hôte), niveau de force.
- **Petite icône** : météo (pluie fine, pluie, pluie battante, neige, jour / nuit) ou état (grotte, bunker,
  combat, deltaplane, mort…) ; son info-bulle indique aussi l'**objet en main** (nom traduit par le jeu).
- **Coop** : « n sur 8 » à côté de la 2e ligne.
- Dans les menus : « Dans les menus · Dernière partie : Jour 9 · Normal » ; pendant le chargement : « Chargement… ».
- La presence disparaît quand tu quittes le jeu.
- Mises à jour : un changement de situation (combat, grotte, mort…) part en 5 s au plus ; l'horloge et les
  vitals toutes les 15 s (Discord limite le nombre de mises à jour).

## Comment ça marche

1. **Le mod `SotFRPC`** (mod RedLoader, C#) lit l'état du jeu et l'écrit toutes les 2 s dans
   `%LOCALAPPDATA%\SotFRPC\live.json`. Il ne modifie rien dans la partie et ne se connecte à rien.
   Au démarrage du jeu, il lance le compagnon (`pythonw.exe`, sans fenêtre) d'après
   `…\Sons Of The Forest\Mods\SotFRPC\companion.json`, écrit par l'installeur.
2. **Le compagnon Python** (`sotf_rpc`, bibliothèque standard uniquement) lit ce fichier et met à jour Discord par
   son canal local (IPC). Il s'arrête 15 s après la fermeture du jeu et ne tourne jamais en double.
   Sans le mod, il retombe sur la **dernière sauvegarde** (jour, heure, saison, mode, santé, sans temps réel).

Par défaut il utilise l'application « Sons of the Forest » que Discord connaît déjà pour détecter le jeu : une seule
activité « Joue à Sons of the Forest », enrichie. Les images sont des URLs (affiche Steam, emojis Twemoji) : rien à
téléverser.

Pour voir ce qui est envoyé en direct : `Installer-le-mod.bat -NoAutoStart`, puis **`SotFRPC.bat`**
(une console affiche chaque mise à jour). Journaux : `%LOCALAPPDATA%\SotFRPC\sotf_rpc.log` (compagnon) et
`…\Sons Of The Forest\_Redloader\Latest.log` (mod).

## Configuration (`config.json`, optionnel)

Copie `config.example.json` en `config.json` et ne garde que ce que tu veux changer.

| Clé                   | Défaut                     | Description |
|-----------------------|----------------------------|-------------|
| `client_id`           | app officielle du jeu      | Application ID Discord. Mets le tien pour utiliser tes propres images (clés d'assets). |
| `language`            | `"auto"`                   | `auto` = langue du jeu (donnée par le mod : français si le jeu est en français, sinon anglais), ou `fr` / `en` pour l'imposer. |
| `timer`               | `"game"`                   | Chrono « écoulées » : `game` (lancement du jeu), `world` (entrée dans la partie), `none`. |
| `clock_mode`          | `"exact"`                  | `exact` (🌙 22:05), `period` (🌙 Nuit), `both`, `none`. |
| `day_offset`          | `0`                        | Ajouté au compteur de jours du jeu. |
| `state_rotation`      | activité une ligne sur deux, puis `vitals`, `stats`, `companions` | Lignes alternées en 2e ligne : `activity`, `vitals`, `stats` (arbres, ennemis tués, morts), `companions` (Kelvin / Virginia), `held` (objet en main). Une seule = pas d'alternance. Mort, combat, sommeil, pause… restent affichés en continu. |
| `rotate_seconds`      | `20`                       | Durée de chaque ligne (les mises à jour « normales » partent toutes les 15 s). |
| `status_display`      | `"name"`                   | Ce que Discord montre à côté de ton nom dans la liste des membres : `name` (« Sons of the Forest »), `details` (jour · saison · heure) ou `state` (2e ligne). |
| `vitals_format`       | `"percent"`                | `percent` (❤️ 85%) ou `value` (❤️ 106/124). |
| `place_radius_m`      | `150`                      | « Près de … » si un lieu nommé est à moins de cette distance. |
| `show_region`         | `true`                     | Sinon, secteur de l'île (« Nord-est de l'île », « En montagne »). Suppose que le nord est l'axe +Z du monde ; `show_position: true` aide à vérifier. |
| `show_held_item`      | `true`                     | Objet en main dans l'info-bulle de la petite icône. |
| `show_position`       | `false`                    | Coordonnées dans l'info-bulle du logo. |
| `area_names`          | `{}`                       | Noms des grottes / bunkers : clés `CaveA`…`CaveH`, `BunkerA`…`BunkerG`. Sans nom : nom du bunker le plus proche, sinon « Dans une grotte » / « Dans un bunker ». |
| `place_names`         | `{}`                       | Renomme un lieu par son `id` (voir `places.json` ci-dessous). |
| `images`              | URLs Steam / Twemoji       | Clés : `logo`, `menu`, `spring`… `winter`, `day`, `night`, `rain_light`, `rain`, `storm`, `snow`, `cave`, `bunker`, `dead`, `sos`, `cutscene`, `sleep`, `pause`, `heli`, `fire`, `boss`, `fight`, `mutant`, `knight`, `glider`, `cart`, `raft`, `swim`, `dive`, `loading`, `menu_small`, `save`. |
| `buttons`             | lien Steam                 | Jusqu'à 2 boutons `{"label": "…", "url": "https://…"}` (visibles par les autres, pas par toi). `[]` pour aucun. |
| `live_stale_seconds`  | `30`                       | Au-delà, `live.json` est considéré périmé (jeu planté / mod absent). |

## Lieux nommés

Le mod relève les déclencheurs « point d'intérêt » du jeu (ceux qui révèlent une icône sur le GPS) avec leur nom
traduit, en début de partie puis toutes les 10 min ; la liste est écrite dans `%LOCALAPPDATA%\SotFRPC\places.json`.
En pratique le jeu n'en nomme que les 7 bunkers :

| `id`                 | Nom (FR)                  |
|----------------------|---------------------------|
| Bunker A / B / C     | Bunker de maintenance A / B / C |
| Bunker Entertainment | Bunker de divertissement  |
| Bunker Food          | Bunker à nourriture       |
| Bunker Luxury        | Bunker de luxe            |
| Bunker Residential   | Bunker Résidentiel        |

Pour renommer un lieu, ajoute son `id` dans `place_names`.

## Outils

```
python -m sotf_rpc --dump           # contenu de live.json + dernière sauvegarde décodée
python -m sotf_rpc --dry-run -v     # calcule la presence sans l'envoyer
python -m sotf_rpc --simulate       # fait comme si le jeu tournait
python -m sotf_rpc --exit-with-game # s'arrête quand le jeu se ferme (mode utilisé par le mod)
python -m unittest discover -s tests
```

### Recompiler le mod

SDK .NET 6 ou plus récent, et RedLoader lancé au moins une fois (il génère les assemblies d'interop du jeu dans
`_Redloader\Game`, contre lesquelles le mod compile) :

```
powershell -ExecutionPolicy Bypass -File mod\install.ps1 -Build
```

## Contenu de `live.json`

```json
{"ts": 1791964154.2, "mod": "1.1.0", "scene": "Game", "lang": "fr", "in_world": true,
 "mode": "Normal", "save_type": "SinglePlayer", "save_id": 2142240785, "multiplayer": false,
 "day": 12, "hour": 22, "minute": 5, "night": true, "season": "Fall", "rain": "None", "snowing": false,
 "vitals": {"health": 62, "health_max": 124, "stamina": 80, "fullness": 55, "hydration": 40.4, "rest": 90,
            "strength_level": 13, "cold": false, "sick": false, "...": "..."},
 "view": "World", "dead": false, "paused": false, "in_water": false, "underwater": false, "gliding": false,
 "golf_cart": false, "raft": false, "constructing": false, "endgame": false,
 "cutscene": false, "knight_v": false, "boss": false, "downed": false, "burning": false, "freezing": false,
 "held": {"id": 367, "name": "Katana", "title": "Katana"}, "left": null,
 "area": "None", "in_caves": false, "pos": [213.3, 735.3, 170.9],
 "place": {"id": "Bunker Food", "name": "Bunker à nourriture", "dist": 832},
 "kelvin_dead": false, "virginia_dead": true, "crash_site": "snow",
 "stats": {"cannibals": 12, "mutants": 3, "animals": 20, "trees": 245, "deaths": 2},
 "kelvin": {"alive": true, "dist": 12}, "virginia": {"alive": false},
 "threats": {"cannibals": 0, "mutants": 0}}
```

## Licences

Code de ce projet : licence MIT (voir [LICENSE](LICENSE)). RedLoader n'est pas inclus : l'installeur le télécharge
depuis sa [release officielle](https://github.com/ToniMacaroni/RedLoader/releases) (empreinte SHA256 vérifiée).
Projet de fan, non affilié à Endnight Games.

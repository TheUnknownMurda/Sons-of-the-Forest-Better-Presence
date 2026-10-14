using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Json;
using Sons.Ai.Vail;
using Sons.Areas;
using Sons.Atmosphere;
using Sons.Cutscenes;
using Sons.Environment;
using Sons.Gameplay;
using Sons.Gameplay.GameSetup;
using Sons.Gui;
using Sons.Inventory;
using Sons.Multiplayer;
using Sons.Save;
using SonsSdk;
using TheForest.Utils;
using TheForest.World;
using UnityEngine;
using UnityEngine.Localization.Settings;
using GameState = Sons.Save.GameState;
using ActorList = Il2CppSystem.Collections.Generic.List<Sons.Ai.Vail.WorldSimActor>;

namespace SotFRPC;

/// <summary>Lit l'état du jeu (sur le thread principal) et le sérialise en JSON.</summary>
internal sealed class Collector
{
    // Relevés des lieux : les objets du monde se chargent progressivement, d'où un 2e passage,
    // puis un passage de contrôle espacé (FindObjectsOfTypeAll parcourt toute la scène).
    private static readonly float[] PlaceScanDelays = { 8f, 60f };
    private const float PlaceRescanInterval = 600f;
    private const float ThreatRadius = 35f;      // ennemis comptés autour du joueur (m)

    private readonly Places _places = new();
    private readonly Dictionary<int, string> _itemTitles = new();
    private float _worldStart;
    private int _placeScans;
    private float _nextPlaceScan = float.MaxValue;
    private string _lang;

    public void ResetWorld()
    {
        _places.Clear();
        _placeScans = 0;
        _nextPlaceScan = float.MaxValue;
    }

    public void OnGameStart()
    {
        _worldStart = Time.realtimeSinceStartup;
        _placeScans = 0;
        _nextPlaceScan = _worldStart + PlaceScanDelays[0];
    }

    public string Collect(ESonsScene scene)
    {
        var lang = Try(() => LocalizationSettings.SelectedLocale?.Identifier.Code);
        if (lang != _lang)
        {
            _lang = lang;
            _itemTitles.Clear(); // noms localisés à recalculer
        }

        var inWorld = scene == ESonsScene.Game && Try(() => LocalPlayer.Transform != null && LocalPlayer.Vitals != null);

        using var ms = new MemoryStream();
        using (var w = new Utf8JsonWriter(ms))
        {
            w.WriteStartObject();
            w.WriteString("scene", scene.ToString());
            w.WriteString("lang", lang);
            w.WriteBoolean("in_world", inWorld);
            if (inWorld)
                WriteWorld(w);
            w.WriteEndObject();
        }
        return Encoding.UTF8.GetString(ms.ToArray());
    }

    private void WriteWorld(Utf8JsonWriter w)
    {
        var now = Time.realtimeSinceStartup;
        if (now >= _nextPlaceScan)
        {
            _placeScans++;
            _nextPlaceScan = _placeScans < PlaceScanDelays.Length
                ? _worldStart + PlaceScanDelays[_placeScans]
                : now + PlaceRescanInterval;
            _places.Scan();
        }

        // ---- partie
        var saveType = Try(() => GameSetupManager.GetSaveGameType(), SaveGameType.SinglePlayer);
        var boltRunning = Try(() => BoltNetwork.isRunning);
        var multiplayer = saveType != SaveGameType.SinglePlayer || (boltRunning && !Try(() => BoltNetwork.IsSinglePlayer, true));
        var saveId = Try(() => GameSetupManager.GetSelectedSaveId());
        if (saveId == 0)
            saveId = SonsSdk.GameState.LastLoadedSaveId;
        w.WriteString("mode", Try(() => GameState.GetGameMode().ToString()));
        w.WriteString("save_type", saveType.ToString());
        w.WriteNumber("save_id", saveId);
        w.WriteBoolean("multiplayer", multiplayer);
        if (multiplayer)
        {
            w.WriteBoolean("host", Try(() => BoltNetwork.isServer));
            var players = Try(() => PlayerTracker.GetPlayerCount());
            if (players <= 0)
                players = Try(() => CoopLobbyManager.IsInLobby() ? CoopLobbyManager.ActiveMemberCount() : 0);
            w.WriteNumber("players", players);
            var max = Try(() => CoopLobbyManager.IsInLobby() ? CoopLobbyManager.ActiveMemberLimit() : 0);
            if (max > 0)
                w.WriteNumber("max_players", max);
        }

        // ---- temps, saison, météo
        var time = Try(() => (TimeOfDay?)TimeOfDayHolder.GetTimeOfDay());
        if (time.HasValue)
        {
            w.WriteNumber("day", time.Value.Days);
            w.WriteNumber("hour", time.Value.Hours);
            w.WriteNumber("minute", time.Value.Minutes);
        }
        w.WriteBoolean("night", Try(() => TimeOfDayHolder.IsNight()));
        w.WriteString("season", Try(() => SeasonsManager.ActiveSeason.ToString()));
        var weather = Try(() => WeatherSystem.Instance);
        if (weather != null)
        {
            w.WriteString("rain", Try(() => weather.IsRaining ? weather.CurrentRainType.ToString() : "None", "None"));
            w.WriteBoolean("snowing", Try(() => weather.IsSnowing));
        }

        // ---- vitals
        var v = LocalPlayer.Vitals;
        w.WriteStartObject("vitals");
        Num(w, "health", () => v.GetHealth());
        Num(w, "health_max", () => v.GetMaxHealth());
        Num(w, "stamina", () => v.GetStamina());
        Num(w, "stamina_max", () => v.Stamina.GetMax());
        Num(w, "fullness", () => v.GetFullness());
        Num(w, "fullness_max", () => v.Fullness.GetMax());
        Num(w, "hydration", () => v.GetHydration());
        Num(w, "hydration_max", () => v.Hydration.GetMax());
        Num(w, "rest", () => v.GetRest());
        Num(w, "rest_max", () => v.Rested.GetMax());
        w.WriteNumber("strength_level", Try(() => v.CurrentStrengthLevel));
        w.WriteBoolean("cold", Try(() => v.IsCold));
        w.WriteBoolean("sick", Try(() => v.IsSick));
        w.WriteBoolean("hungry", Try(() => v.IsHungry));
        w.WriteBoolean("thirsty", Try(() => v.IsThirsty));
        w.WriteBoolean("tired", Try(() => v.IsTired));
        w.WriteEndObject();

        // ---- ce que fait le joueur
        var view = Try(() => LocalPlayer.CurrentView.ToString());
        w.WriteString("view", view);
        w.WriteBoolean("dead", Try(() => v.HasDied()) || view == "Death");
        w.WriteBoolean("paused", Try(() => PauseMenu.IsActive));
        w.WriteBoolean("in_water", Try(() => LocalPlayer.InWater));
        w.WriteBoolean("underwater", Try(() => LocalPlayer.IsUnderwater));
        w.WriteBoolean("gliding", Try(() => LocalPlayer.IsGliding));
        w.WriteBoolean("golf_cart", Try(() => LocalPlayer.IsInGolfCart));
        w.WriteBoolean("raft", Try(() => LocalPlayer.AttachedRaft != null));
        w.WriteBoolean("constructing", Try(() => LocalPlayer.IsConstructing));
        w.WriteBoolean("endgame", Try(() => LocalPlayer.IsInEndgame));
        w.WriteBoolean("cutscene", Try(() => CutsceneManager.IsCutscenePlaying()));
        w.WriteBoolean("knight_v", Try(() => LocalPlayer._cachedItemController?.TryCast<KnightVItemController>()?.IsRiding() ?? false));
        var stats = Try(() => LocalPlayer.Stats);
        if (stats != null)
        {
            w.WriteBoolean("boss", Try(() => stats.IsFightingBoss));
            w.WriteBoolean("downed", Try(() => stats.PlayerIsDowned));
            w.WriteBoolean("burning", Try(() => stats.IsBurning));
            w.WriteBoolean("freezing", Try(() => stats.IsFreezing));
        }

        var inv = Try(() => LocalPlayer.Inventory);
        WriteItem(w, "held", inv == null ? null : Try(() => inv.RightHandItem));
        WriteItem(w, "left", inv == null ? null : Try(() => inv.LeftHandItem));

        // ---- où
        w.WriteString("area", Try(() => CaveEntranceManager.CurrentAreaMask.ToString(), "None"));
        w.WriteBoolean("in_caves", Try(() => LocalPlayer.IsInCaves || CaveEntranceManager.IsInCaves));
        w.WriteBoolean("deep_caves", Try(() => CaveEntranceManager.IsInDeepCaves));
        var pos = Try(() => (Vector3?)LocalPlayer.Transform.position);
        if (pos.HasValue)
        {
            var p = pos.Value;
            w.WriteStartArray("pos");
            w.WriteNumberValue(Math.Round(p.x, 1));
            w.WriteNumberValue(Math.Round(p.y, 1));
            w.WriteNumberValue(Math.Round(p.z, 1));
            w.WriteEndArray();
            var place = _places.Nearest(p);
            if (place != null)
            {
                w.WriteStartObject("place");
                w.WriteString("id", place.Value.Id);
                w.WriteString("name", place.Value.Name);
                w.WriteNumber("dist", Math.Round(place.Value.Distance));
                w.WriteEndObject();
            }
        }

        // ---- histoire
        var kelvinDead = Try(() => GameState.IsRobbyDead());
        var virginiaDead = Try(() => GameState.IsVirginiaDead());
        w.WriteBoolean("kelvin_dead", kelvinDead);
        w.WriteBoolean("virginia_dead", virginiaDead);
        w.WriteString("crash_site", Try(() => GameState.CrashSite()));

        // ---- simulation du monde : compteurs, compagnons, ennemis proches
        var sim = Try(() => VailWorldSimulation._instance);
        if (sim == null)
            return;
        w.WriteStartObject("stats");
        w.WriteNumber("cannibals", Try(() => (int)sim.GetKilledByPlayerCount(VailActorClassId.Cannibal)));
        w.WriteNumber("mutants", Try(() => (int)sim.GetKilledByPlayerCount(VailActorClassId.Creepy)));
        w.WriteNumber("animals", Try(() => (int)sim.GetKilledByPlayerCount(VailActorClassId.Animal)));
        w.WriteNumber("trees", Try(() => sim._playerWorldStats?.CutTrees ?? 0));
        if (stats != null)
            w.WriteNumber("deaths", Try(() => stats._playerDeathCount));
        w.WriteEndObject();

        if (!pos.HasValue)
            return;
        WriteCompanion(w, "kelvin", Try(() => sim._robbyActors), kelvinDead, pos.Value);
        WriteCompanion(w, "virginia", Try(() => sim._virginiaActors), virginiaDead, pos.Value);
        WriteThreats(w, sim, pos.Value);
    }

    private static void WriteCompanion(Utf8JsonWriter w, string name, ActorList actors, bool dead, Vector3 playerPos)
    {
        float? nearest = null;
        try
        {
            for (var i = 0; !dead && actors != null && i < actors.Count; i++)
            {
                var actor = actors[i];
                if (actor == null || actor.IsDead())
                    continue;
                var d = Vector3.Distance(actor.Position(), playerPos);
                if (nearest == null || d < nearest)
                    nearest = d;
            }
        }
        catch
        {
            // liste modifiée pendant le parcours : distance inconnue ce tour-ci
        }
        w.WriteStartObject(name);
        w.WriteBoolean("alive", !dead);
        if (nearest.HasValue)
            w.WriteNumber("dist", Math.Round(nearest.Value));
        w.WriteEndObject();
    }

    private static void WriteThreats(Utf8JsonWriter w, VailWorldSimulation sim, Vector3 playerPos)
    {
        int cannibals = 0, mutants = 0;
        var nearest = float.MaxValue;
        try
        {
            var actors = sim._nearbyActors;
            if (actors == null || actors.Count == 0)
                actors = sim._actors;
            for (var i = 0; actors != null && i < actors.Count; i++)
            {
                var actor = actors[i];
                if (actor == null)
                    continue;
                var cls = actor.ClassId;
                if (cls != VailActorClassId.Cannibal && cls != VailActorClassId.Creepy)
                    continue;
                var d = Vector3.Distance(actor.Position(), playerPos);
                if (d > ThreatRadius || actor.IsDead())
                    continue;
                if (cls == VailActorClassId.Cannibal) cannibals++; else mutants++;
                nearest = Math.Min(nearest, d);
            }
        }
        catch
        {
            // comptage partiel
        }
        w.WriteStartObject("threats");
        w.WriteNumber("cannibals", cannibals);
        w.WriteNumber("mutants", mutants);
        if (nearest < float.MaxValue)
            w.WriteNumber("nearest", Math.Round(nearest));
        w.WriteEndObject();
    }

    private void WriteItem(Utf8JsonWriter w, string name, ItemInstance item)
    {
        var data = item == null ? null : Try(() => item.Data);
        if (data == null)
        {
            w.WriteNull(name);
            return;
        }
        var id = Try(() => data.Id, -1);
        if (!_itemTitles.TryGetValue(id, out var title))
        {
            title = Try(() => data.UiData?.GetTitleLocalized());
            _itemTitles[id] = title;
        }
        w.WriteStartObject(name);
        w.WriteNumber("id", id);
        w.WriteString("name", Try(() => data.Name));
        w.WriteString("title", title);
        w.WriteEndObject();
    }

    private static void Num(Utf8JsonWriter w, string name, Func<float> getter)
    {
        try
        {
            var value = getter();
            if (float.IsFinite(value))
            {
                w.WriteNumber(name, Math.Round(value, 1));
                return;
            }
        }
        catch
        {
            // champ indisponible : omis
        }
    }

    internal static T Try<T>(Func<T> getter, T fallback = default)
    {
        try
        {
            return getter();
        }
        catch
        {
            return fallback;
        }
    }
}

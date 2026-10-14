using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using RedLoader;
using Sons.Gameplay;
using Sons.Gameplay.GPS;
using UnityEngine;

namespace SotFRPC;

/// <summary>
/// Lieux nommés du monde : déclencheurs « point d'intérêt » (ceux qui révèlent une icône sur le GPS)
/// et balises GPS fixes. Leur position sert à afficher « près de … ».
/// La liste trouvée est écrite dans %LOCALAPPDATA%\SotFRPC\places.json (pour vérification / traduction).
/// </summary>
internal sealed class Places
{
    public readonly struct Place
    {
        public Place(string id, string name, Vector3 position, string source)
        {
            Id = id;
            Name = name;
            Position = position;
            Source = source;
            Distance = 0f;
        }

        public Place(Place place, float distance)
        {
            this = place;
            Distance = distance;
        }

        public string Id { get; }
        public string Name { get; }
        public Vector3 Position { get; }
        public string Source { get; }
        public float Distance { get; }
    }

    private readonly List<Place> _places = new();
    private bool _loggedError;

    public void Clear() => _places.Clear();

    public Place? Nearest(Vector3 position)
    {
        Place? best = null;
        var bestSqr = float.MaxValue;
        foreach (var place in _places)
        {
            // distance à plat : une grotte sous un lieu reste « près » de lui
            var dx = place.Position.x - position.x;
            var dz = place.Position.z - position.z;
            var sqr = dx * dx + dz * dz;
            if (sqr < bestSqr)
            {
                bestSqr = sqr;
                best = place;
            }
        }
        return best.HasValue ? new Place(best.Value, MathF.Sqrt(bestSqr)) : null;
    }

    public void Scan()
    {
        var watch = System.Diagnostics.Stopwatch.StartNew();
        var found = new List<Place>();
        var seen = new HashSet<string>();
        try
        {
            foreach (var trigger in Resources.FindObjectsOfTypeAll<PointOfInterestRevealTrigger>())
            {
                if (trigger == null || !trigger.gameObject.scene.IsValid())
                    continue;
                var link = trigger._pointOfInterestName;
                if (string.IsNullOrWhiteSpace(link))
                    continue;
                var pos = trigger.transform.position;
                if (!seen.Add(Key(link, pos)))
                    continue;
                found.Add(new Place(link, ResolveName(trigger._pointsOfInterest, link), pos, "poi"));
            }
        }
        catch (Exception ex)
        {
            LogOnce("points d'intérêt", ex);
        }

        try
        {
            var locators = GPSLocator._activeLocators;
            for (var i = 0; locators != null && i < locators.Count; i++)
            {
                var locator = locators[i];
                if (locator == null || locator._worldActorId != 0)
                    continue; // balise attachée à un personnage (Kelvin, Virginia…) : elle bouge
                var link = locator._pointOfInterestName;
                if (string.IsNullOrWhiteSpace(link))
                    continue;
                var pos = locator.Position();
                if (!seen.Add(Key(link, pos)))
                    continue;
                found.Add(new Place(link, null, pos, "gps"));
            }
        }
        catch (Exception ex)
        {
            LogOnce("balises GPS", ex);
        }

        // un nom localisé trouvé via un déclencheur sert aussi aux balises du même lieu
        var names = new Dictionary<string, string>();
        foreach (var place in found)
            if (place.Name != null)
                names[place.Id] = place.Name;
        _places.Clear();
        foreach (var place in found)
            _places.Add(place.Name == null && names.TryGetValue(place.Id, out var name)
                ? new Place(place.Id, name, place.Position, place.Source)
                : place);

        RLog.Msg($"SotFRPC : {_places.Count} lieux nommés trouvés en {watch.ElapsedMilliseconds} ms");
        Dump();
    }

    private static string ResolveName(PointsOfInterestData data, string link)
    {
        try
        {
            var all = data?.All;
            for (var i = 0; all != null && i < all.Count; i++)
            {
                var poi = all[i];
                if (poi == null || poi.LinkName != link)
                    continue;
                var text = poi.DisplayName?.GetLocalizedString();
                return string.IsNullOrWhiteSpace(text) ? null : text.Trim();
            }
        }
        catch
        {
            // nom localisé indisponible : le compagnon utilisera l'identifiant
        }
        return null;
    }

    private static string Key(string id, Vector3 pos) => $"{id}@{Mathf.RoundToInt(pos.x / 10)},{Mathf.RoundToInt(pos.z / 10)}";

    private void LogOnce(string what, Exception ex)
    {
        if (_loggedError)
            return;
        _loggedError = true;
        RLog.Warning($"SotFRPC : lecture des {what} impossible : {ex.Message}");
    }

    private void Dump()
    {
        if (SotFRPCMod.DataDir == null)
            return;
        try
        {
            using var stream = File.Create(Path.Combine(SotFRPCMod.DataDir, "places.json"));
            using var w = new Utf8JsonWriter(stream, new JsonWriterOptions { Indented = true });
            w.WriteStartArray();
            foreach (var place in _places)
            {
                w.WriteStartObject();
                w.WriteString("id", place.Id);
                w.WriteString("name", place.Name);
                w.WriteString("source", place.Source);
                w.WriteStartArray("pos");
                w.WriteNumberValue(Math.Round(place.Position.x));
                w.WriteNumberValue(Math.Round(place.Position.y));
                w.WriteNumberValue(Math.Round(place.Position.z));
                w.WriteEndArray();
                w.WriteEndObject();
            }
            w.WriteEndArray();
        }
        catch
        {
            // fichier de diagnostic seulement
        }
    }
}

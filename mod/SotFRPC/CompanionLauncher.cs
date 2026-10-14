using System;
using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Threading;
using RedLoader;

namespace SotFRPC;

/// <summary>
/// Lance le compagnon Python au démarrage du jeu, d'après mods\SotFRPC\companion.json
/// (écrit par mod\install.ps1). Le compagnon tient un mutex nommé : s'il tourne déjà
/// (raccourci de démarrage Windows, SotFRPC.bat…), on ne le relance pas.
/// </summary>
internal static class CompanionLauncher
{
    private const string MutexName = @"Local\SotFRPC.Companion";

    public static void TryStart(string modDir)
    {
        var configPath = Path.Combine(modDir, "companion.json");
        if (!File.Exists(configPath))
            return;
        try
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(configPath));
            var root = doc.RootElement;
            if (root.TryGetProperty("enabled", out var enabled) && enabled.ValueKind == JsonValueKind.False)
                return;
            if (Mutex.TryOpenExisting(MutexName, out var existing))
            {
                existing.Dispose();
                RLog.Msg("SotFRPC : compagnon déjà lancé");
                return;
            }
            var info = new ProcessStartInfo
            {
                FileName = root.GetProperty("python").GetString(),
                WorkingDirectory = root.GetProperty("workdir").GetString(),
                UseShellExecute = false,
                CreateNoWindow = true,
            };
            foreach (var arg in root.GetProperty("args").EnumerateArray())
                info.ArgumentList.Add(arg.GetString());
            Process.Start(info)?.Dispose();
            RLog.Msg($"SotFRPC : compagnon lancé ({info.FileName} dans {info.WorkingDirectory})");
        }
        catch (Exception ex)
        {
            RLog.Warning($"SotFRPC : lancement du compagnon impossible ({configPath}) : {ex.Message}");
        }
    }
}

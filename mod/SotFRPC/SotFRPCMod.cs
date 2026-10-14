using System;
using System.IO;
using RedLoader;
using SonsSdk;
using UnityEngine;

namespace SotFRPC;

/// <summary>
/// Écrit toutes les 2 s l'état de la partie dans %LOCALAPPDATA%\SotFRPC\live.json
/// (réécrit seulement si quelque chose a changé, sinon toutes les 10 s pour garder « ts » frais).
/// Le compagnon Python (sotf_rpc) lit ce fichier et met à jour la Rich Presence Discord.
/// </summary>
public class SotFRPCMod : SonsMod
{
    public const string ModVersion = "1.1.0";

    private const float WriteInterval = 2f;
    private const float KeepAliveInterval = 10f;

    private string _livePath;
    private string _tmpPath;
    private string _lastBody;
    private float _nextWrite;
    private float _lastWriteAt = -999f;
    private int _consecutiveErrors;
    private ESonsScene _scene = ESonsScene.Title;
    private readonly Collector _collector = new();

    public SotFRPCMod()
    {
        OnUpdateCallback = Tick;
    }

    public static string DataDir { get; private set; }

    protected override void OnInitializeMod()
    {
        DataDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SotFRPC");
        Directory.CreateDirectory(DataDir);
        _livePath = Path.Combine(DataDir, "live.json");
        _tmpPath = _livePath + ".tmp";
        RLog.Msg($"SotFRPC {ModVersion} : état exporté vers {_livePath}");

        // mods\SotFRPC.dll → mods\SotFRPC\companion.json
        var modsDir = Path.GetDirectoryName(typeof(SotFRPCMod).Assembly.Location);
        if (!string.IsNullOrEmpty(modsDir))
            CompanionLauncher.TryStart(Path.Combine(modsDir, "SotFRPC"));
    }

    protected override void OnSonsSceneInitialized(ESonsScene sonsScene)
    {
        _scene = sonsScene;
        _nextWrite = 0f;
        if (sonsScene != ESonsScene.Game)
            _collector.ResetWorld();
    }

    protected override void OnGameStart()
    {
        _collector.OnGameStart();
        _nextWrite = 0f;
    }

    protected override void OnApplicationQuit()
    {
        try { File.Delete(_livePath); } catch { /* le compagnon verra un fichier périmé */ }
    }

    private void Tick()
    {
        var now = Time.realtimeSinceStartup;
        if (now < _nextWrite || _livePath == null)
            return;
        _nextWrite = now + WriteInterval;

        string body;
        try
        {
            body = _collector.Collect(_scene);
            _consecutiveErrors = 0;
        }
        catch (Exception ex)
        {
            if (_consecutiveErrors++ == 0)
                RLog.Error($"SotFRPC : lecture de l'état impossible : {ex}");
            return;
        }

        if (body == _lastBody && now - _lastWriteAt < KeepAliveInterval)
            return;

        var ts = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0;
        var json = "{\"ts\":" + ts.ToString("0.000", System.Globalization.CultureInfo.InvariantCulture)
                   + ",\"mod\":\"" + ModVersion + "\"," + body.Substring(1);
        try
        {
            File.WriteAllText(_tmpPath, json);
            File.Move(_tmpPath, _livePath, true);
            _lastBody = body;
            _lastWriteAt = now;
        }
        catch (IOException)
        {
            // fichier en cours de lecture par le compagnon : nouvel essai au prochain tick
            _nextWrite = now + 0.25f;
        }
        catch (Exception ex)
        {
            RLog.Error($"SotFRPC : écriture de {_livePath} impossible : {ex.Message}");
        }
    }
}

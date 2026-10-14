# Installe (ou met à jour) la Rich Presence Sons of the Forest : RedLoader si besoin, le mod SotFRPC,
# et le lancement automatique du compagnon Python avec le jeu.
#   powershell -ExecutionPolicy Bypass -File mod\install.ps1 [-GamePath "D:\...\Sons Of The Forest"] [-Build] [-NoAutoStart] [-Yes]
#   powershell -ExecutionPolicy Bypass -File mod\install.ps1 -Uninstall [-RemoveRedLoader]
# -Build recompile d'abord le mod (SDK .NET 6+ requis) ; sinon la DLL fournie dans mod\build est utilisée.
# -NoAutoStart : le jeu ne lance pas le compagnon (tu lances alors SotFRPC.bat toi-même).
# -Yes : installe RedLoader sans poser la question s'il manque.
# -Uninstall retire le mod ; avec -RemoveRedLoader, retire aussi RedLoader si aucun autre mod ne l'utilise
# (c'est ce que fait Desinstaller-le-mod.bat).
# Seul téléchargement possible : RedLoader, depuis sa release officielle GitHub, empreinte SHA256 vérifiée.
# Aucun droit administrateur n'est demandé.
param(
    [string]$GamePath = "",
    [switch]$Build,
    [switch]$NoAutoStart,
    [switch]$Yes,
    [switch]$Uninstall,
    [switch]$RemoveRedLoader
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # Invoke-WebRequest est très lent avec la barre de progression
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $here

$RedLoaderVersion = "0.8.6"
$RedLoaderUrl = "https://github.com/ToniMacaroni/RedLoader/releases/download/$RedLoaderVersion/Redloader.zip"
$RedLoaderSha256 = "1429BEE2FE6A5B1B82BB06A447762B09E9FAF077138966FBFE65C687123FD4EB"

function Write-Step([string]$text) { Write-Host ""; Write-Host "== $text" -ForegroundColor Cyan }
function Write-Ok([string]$text) { Write-Host "   OK  $text" -ForegroundColor Green }
function Write-Warn([string]$text) { Write-Host "   !!  $text" -ForegroundColor Yellow }
function Stop-Install([string]$text) {
    Write-Host ""
    Write-Host "ÉCHEC : $text" -ForegroundColor Red
    exit 1
}

function Find-GamePath {
    $steam = (Get-ItemProperty "HKCU:\Software\Valve\Steam" -ErrorAction SilentlyContinue).SteamPath
    if (-not $steam) { return $null }
    $libraries = @($steam -replace "/", "\")
    $vdf = Join-Path $steam "steamapps\libraryfolders.vdf"
    if (Test-Path $vdf) {
        foreach ($m in (Select-String -Path $vdf -Pattern '"path"\s+"([^"]+)"')) {
            $libraries += $m.Matches[0].Groups[1].Value -replace "\\\\", "\"
        }
    }
    foreach ($lib in $libraries | Select-Object -Unique) {
        $candidate = Join-Path $lib "steamapps\common\Sons Of The Forest"
        if (Test-Path (Join-Path $candidate "SonsOfTheForest.exe")) { return $candidate }
    }
    return $null
}

# pythonw.exe (Python sans console) : PATH, lanceur « py », puis dossiers d'installation habituels.
function Find-Pythonw {
    $candidates = @()
    foreach ($cmd in @(Get-Command pythonw, python -All -ErrorAction SilentlyContinue)) {
        if ($cmd.Source -and $cmd.Source -notmatch "WindowsApps") {
            $candidates += (Join-Path (Split-Path $cmd.Source) "pythonw.exe")
        }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $exe = (& py -3 -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1)
        if ($exe) { $candidates += (Join-Path (Split-Path $exe.Trim()) "pythonw.exe") }
    }
    foreach ($base in @("$env:LOCALAPPDATA\Programs\Python", "$env:ProgramFiles", "${env:ProgramFiles(x86)}")) {
        if (Test-Path $base) {
            $candidates += Get-ChildItem $base -Directory -Filter "Python3*" -ErrorAction SilentlyContinue |
                Sort-Object Name -Descending | ForEach-Object { Join-Path $_.FullName "pythonw.exe" }
        }
    }
    foreach ($pythonw in $candidates | Select-Object -Unique) {
        if (-not (Test-Path $pythonw)) { continue }
        $python = Join-Path (Split-Path $pythonw) "python.exe"
        $version = (& $python -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null | Select-Object -First 1)
        if ($version -and [version]$version -ge [version]"3.9") {
            return [pscustomobject]@{ Pythonw = $pythonw; Version = $version }
        }
    }
    return $null
}

function Test-RedLoader([string]$game) {
    (Test-Path (Join-Path $game "_Redloader\net6\RedLoader.dll")) -and (Test-Path (Join-Path $game "version.dll"))
}

function Install-RedLoader([string]$game) {
    $zip = Join-Path $env:TEMP "Redloader-$RedLoaderVersion.zip"
    Write-Host "   Téléchargement de RedLoader $RedLoaderVersion (37 Mo) depuis github.com/ToniMacaroni/RedLoader..."
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $RedLoaderUrl -OutFile $zip -UseBasicParsing
    } catch {
        Stop-Install ("téléchargement de RedLoader impossible ($($_.Exception.Message)).`n" +
                      "Installe-le à la main : $RedLoaderUrl`n" +
                      "puis décompresse le zip dans le dossier du jeu et relance Installer-le-mod.bat.")
    }
    $hash = (Get-FileHash $zip -Algorithm SHA256).Hash
    if ($hash -ne $RedLoaderSha256) {
        Remove-Item $zip -Force -ErrorAction SilentlyContinue
        Stop-Install "le fichier téléchargé ne correspond pas à RedLoader $RedLoaderVersion (empreinte $hash) : installation annulée."
    }
    try {
        Expand-Archive -Path $zip -DestinationPath $game -Force
    } catch {
        Stop-Install "décompression dans le dossier du jeu impossible ($($_.Exception.Message)). Ferme le jeu et vérifie ton antivirus."
    } finally {
        Remove-Item $zip -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Rich Presence Discord pour Sons of the Forest - $(if ($Uninstall) { 'désinstallation' } else { 'installation' })" -ForegroundColor White

# Fichiers téléchargés (zip GitHub) : retire la marque « provenant d'Internet » qui peut bloquer les scripts.
Get-ChildItem $root -Recurse -File -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue

Write-Step "Dossier du jeu"
if (-not $GamePath) { $GamePath = Find-GamePath }
if (-not $GamePath -or -not (Test-Path (Join-Path $GamePath "SonsOfTheForest.exe"))) {
    Stop-Install ("Sons of the Forest introuvable dans tes bibliothèques Steam.`n" +
                  "Relance avec le dossier du jeu, par exemple :`n" +
                  "  Installer-le-mod.bat -GamePath `"D:\SteamLibrary\steamapps\common\Sons Of The Forest`"`n" +
                  "(Steam > clic droit sur Sons of the Forest > Gérer > Parcourir les fichiers locaux)")
}
Write-Ok $GamePath
$mods = Join-Path $GamePath "Mods"
$modDll = Join-Path $mods "SotFRPC.dll"
$modDir = Join-Path $mods "SotFRPC"     # RedLoader lit le manifeste dans Mods\<nom de la DLL>\manifest.json

if ($Uninstall) {
    Write-Step "Désinstallation"
    if (Get-Process SonsOfTheForest -ErrorAction SilentlyContinue) { Stop-Install "ferme Sons of the Forest avant de désinstaller." }
    foreach ($path in @($modDll, $modDir)) {
        if (Test-Path $path) { Remove-Item -Recurse -Force $path }
    }
    Write-Ok "Mod retiré."
    if (-not $RemoveRedLoader) { exit 0 }
    # RedLoader n'est retiré que si aucun autre mod ne s'en sert.
    $others = @(Get-ChildItem $mods -Recurse -File -ErrorAction SilentlyContinue)
    if ($others.Count -gt 0) {
        Write-Warn "RedLoader gardé : d'autres mods l'utilisent ($($others.Count) fichier(s) dans $mods)."
        exit 0
    }
    if (Test-Path (Join-Path $GamePath "_Redloader\__folder_managed_by_vortex")) {
        Write-Warn "RedLoader gardé : il est géré par Vortex (retire-le depuis Vortex)."
        exit 0
    }
    foreach ($name in @("_Redloader", "version.dll", "doorstop_config.ini", "Mods")) {
        $path = Join-Path $GamePath $name
        if (Test-Path $path) { Remove-Item -Recurse -Force $path }
    }
    $userData = Join-Path $GamePath "UserData"     # créé par RedLoader ; gardé s'il contient des réglages
    if ((Test-Path $userData) -and -not (Get-ChildItem $userData -Recurse -File -ErrorAction SilentlyContinue)) {
        Remove-Item -Recurse -Force $userData
    }
    Write-Ok "RedLoader retiré : le jeu est revenu à son état d'origine."
    exit 0
}

if (Get-Process SonsOfTheForest -ErrorAction SilentlyContinue) {
    Write-Warn "Sons of the Forest est lancé : ferme-le, l'installation sera prise en compte au prochain lancement."
}

Write-Step "RedLoader (chargeur de mods)"
if (Test-RedLoader $GamePath) {
    Write-Ok "déjà installé."
} else {
    Write-Host "   RedLoader n'est pas installé. C'est le chargeur de mods de Sons of the Forest (open source,"
    Write-Host "   https://github.com/ToniMacaroni/RedLoader) : il est nécessaire pour lire ta partie en temps réel."
    $answer = if ($Yes) { "o" } else { Read-Host "   Le télécharger et l'installer maintenant ? [O/n]" }
    if ($answer -and $answer.Trim().ToLower() -notin @("o", "oui", "y", "yes")) {
        Stop-Install ("RedLoader est nécessaire. Installe-le (RedManager ou zip : https://github.com/ToniMacaroni/RedLoader)`n" +
                      "puis relance Installer-le-mod.bat.")
    }
    Install-RedLoader $GamePath
    if (-not (Test-RedLoader $GamePath)) { Stop-Install "RedLoader ne semble pas installé correctement dans $GamePath." }
    Write-Ok "RedLoader $RedLoaderVersion installé (_Redloader, version.dll, doorstop_config.ini)."
    Write-Warn "le premier lancement du jeu sera plus long (1 à 2 min) : RedLoader prépare ses fichiers."
}

if ($Build) {
    Write-Step "Compilation du mod"
    if (-not (Test-Path (Join-Path $GamePath "_Redloader\Game\Sons.dll"))) {
        Stop-Install "lance le jeu une fois avec RedLoader avant de compiler (il génère _Redloader\Game)."
    }
    dotnet build (Join-Path $here "SotFRPC\SotFRPC.csproj") -c Release -o (Join-Path $here "build") "-p:GamePath=$GamePath"
    if ($LASTEXITCODE -ne 0) { Stop-Install "la compilation a échoué." }
}

Write-Step "Mod SotFRPC"
$dll = Join-Path $here "build\SotFRPC.dll"
if (-not (Test-Path $dll)) { Stop-Install "$dll introuvable (télécharge à nouveau le projet, ou lance le script avec -Build)." }
try {
    New-Item -ItemType Directory -Force $modDir | Out-Null
    Copy-Item $dll $modDll -Force
    Copy-Item (Join-Path $here "SotFRPC\manifest.json") (Join-Path $modDir "manifest.json") -Force
} catch {
    Stop-Install "copie dans $mods impossible ($($_.Exception.Message)). Ferme le jeu et réessaie."
}
Write-Ok $modDll

Write-Step "Python (compagnon qui parle à Discord)"
$python = Find-Pythonw
if ($python) {
    Write-Ok "Python $($python.Version) : $($python.Pythonw)"
} else {
    Write-Warn "Python 3.9+ introuvable. Installe-le depuis https://www.python.org/downloads/ puis relance ce script."
}
$enabled = [bool]($python -and -not $NoAutoStart)
$companion = [ordered]@{
    enabled = $enabled
    python  = if ($python) { $python.Pythonw } else { "pythonw" }
    workdir = $root
    args    = @("-m", "sotf_rpc", "--exit-with-game")
}
[IO.File]::WriteAllText((Join-Path $modDir "companion.json"), ($companion | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
if ($enabled) {
    Write-Ok "le jeu lancera la Rich Presence tout seul (et l'arrêtera en quittant)."
} elseif ($NoAutoStart) {
    Write-Ok "lancement automatique désactivé : lance SotFRPC.bat toi-même."
}

Write-Host ""
if ($python) {
    Write-Host "Terminé ! Lance Sons of the Forest depuis Steam : ton statut Discord affichera ta partie." -ForegroundColor Green
    Write-Host "Ne déplace pas ce dossier (sinon relance Installer-le-mod.bat)."
    Write-Host "Discord : Paramètres > Confidentialité de l'activité > « Partager mon activité » doit être activé."
} else {
    Write-Host "Mod installé, mais il manque Python : installe-le puis relance Installer-le-mod.bat." -ForegroundColor Yellow
}

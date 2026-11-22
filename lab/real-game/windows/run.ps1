# Runs the real game (the public demo named in lab/real-game/games.json) with a tool's plugins on a throwaway Windows
# machine (a GitHub-hosted runner), the way lab/real-game/run.sh does under Wine, and writes the evidence.
#
#   pwsh run.ps1 -Plan plan.json -Installer <the demo's installer> -Out <evidence folder>
#
# The plan is the one lab/plugin-test-host/windows/run.ps1 reads (game, release files by URL and SHA-256), with its real-game
# runs under "realgame": [{"name": ..., "ride": <seconds>, "keys": [[<second>, "<key>"], ...]}]. The bare demo runs first,
# as "baseline", ridden as long as the longest run, so the others can be read against it. Each run gets a fresh game
# folder, an outbound firewall block on every program in it, and Process Monitor; the screen is clicked through to a track
# as games.json says, the throttle is held for "ride" seconds and each key is pressed at its second. Its evidence goes to
# <Out>/<name>/ in the layout of the Windows test host.
param([Parameter(Mandatory)][string]$Plan, [Parameter(Mandatory)][string]$Installer, [Parameter(Mandatory)][string]$Out)
$ErrorActionPreference = 'Stop'
$cfg = Get-Content $Plan -Raw | ConvertFrom-Json
$games = Get-Content (Join-Path $PSScriptRoot '..\games.json') -Raw | ConvertFrom-Json
$g = $games.($cfg.game ?? 'mxbikes')
$work = Join-Path $env:RUNNER_TEMP 'realgame'
New-Item -ItemType Directory -Force $work, $Out | Out-Null
$Out = (Resolve-Path $Out).Path

function Get-Pinned($url, $sha, $file) {
  if (-not (Test-Path $file)) { Invoke-WebRequest $url -OutFile $file }
  $h = (Get-FileHash $file -Algorithm SHA256).Hash.ToLower()
  if ($sha -and $h -ne $sha) { throw "$url has SHA-256 $h, expected $sha" }
  $h
}

# The demo: the installer (cached by the workflow) checked against games.json, unpacked once (a self-extracting zip).
if ((Get-FileHash $Installer -Algorithm SHA256).Hash.ToLower() -ne $g.sha256) { throw "$Installer doesn't match its SHA-256 in games.json" }
$demo = "$work\demo"
7z x -y "-o$demo" $Installer | Out-Null
if (-not (Test-Path "$demo\$($g.exe)")) { throw "unpacking $Installer gave no $($g.exe)" }

# Process Monitor and Mesa's software OpenGL (llvmpipe, the renderer of the Wine runs), as the Windows test host gets them.
$pmSha = Get-Pinned 'https://download.sysinternals.com/files/ProcessMonitor.zip' $null "$work\pm.zip"
Expand-Archive "$work\pm.zip" "$work\pm" -Force
Get-Pinned 'https://github.com/pal1000/mesa-dist-win/releases/download/26.3.0/mesa3d-26.3.0-release-msvc.7z' `
  'c505fcc77e8f63a09d7ddac086591d2f542c0698d37fc9e3094685a34d0d9991' "$work\mesa.7z" | Out-Null
7z x -y "-o$work\mesa" "$work\mesa.7z" | Out-Null
$env:GALLIUM_DRIVER = 'llvmpipe'
$pm = "$work\pm\Procmon64.exe"

# The release files, checked against the plan's SHA-256 and unpacked into rel\<file name>\.
$rel = New-Item -ItemType Directory -Force "$work\rel"
$fileLines = foreach ($f in $cfg.files) {
  $name = [IO.Path]::GetFileName(([uri]$f.url).LocalPath)
  $h = Get-Pinned $f.url $f.sha256.ToLower() "$work\$name"
  $dest = New-Item -ItemType Directory -Force (Join-Path $rel $name)
  if ($name -match '\.(zip|7z|rar)$') { 7z x -y "-o$dest" "$work\$name" | Out-Null } else { Copy-Item "$work\$name" $dest }
  "$h  $name"
}
function Get-PluginsFolder {
  $p = Get-ChildItem $rel -Recurse -Directory | Where-Object Name -eq 'plugins' | Select-Object -First 1
  if ($p) { return $p.FullName }
  $d = Get-ChildItem $rel -Recurse -File -Filter *.dlo | Sort-Object { $_.FullName.Length } | Select-Object -First 1
  if ($d) { return $d.DirectoryName }
}

# The screen and the input: SendInput with scan codes (games read the keyboard by scan code), and screen captures.
Add-Type -AssemblyName System.Drawing
# Only the Windows calls are compiled here; the screen is read with System.Drawing from PowerShell, which needs no references.
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class Input {
  [StructLayout(LayoutKind.Sequential)] struct MOUSEINPUT { public int dx, dy; public uint data, flags, time; public IntPtr extra; }
  [StructLayout(LayoutKind.Sequential)] struct KEYBDINPUT { public ushort vk, scan; public uint flags, time; public IntPtr extra; public uint pad1, pad2; }
  [StructLayout(LayoutKind.Explicit)] struct INPUT { [FieldOffset(0)] public uint type; [FieldOffset(8)] public MOUSEINPUT mi; [FieldOffset(8)] public KEYBDINPUT ki; }
  [DllImport("user32.dll")] static extern uint SendInput(uint n, INPUT[] inputs, int size);
  [DllImport("user32.dll")] static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern int GetSystemMetrics(int i);
  [DllImport("user32.dll")] static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] static extern int ChangeDisplaySettings(ref DEVMODE dm, int flags);
  [DllImport("user32.dll")] static extern bool EnumDisplaySettings(string dev, int mode, ref DEVMODE dm);
  [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)] struct DEVMODE {
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string name; public short specVer, drvVer, size, drvExtra; public int fields;
    public int x, y, orient, fixedOut; public short color, duplex, yRes, tt, collate;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string form; public short logPixels; public int bits, width, height, dispFlags, freq;
    public int icm1, icm2, icm3, icm4, icm5, icm6, pan1, pan2; }
  public static int W { get { return GetSystemMetrics(0); } } public static int H { get { return GetSystemMetrics(1); } }
  public static int SetResolution(int w, int h) {
    SetProcessDPIAware(); var dm = new DEVMODE(); dm.size = (short)Marshal.SizeOf(typeof(DEVMODE));
    EnumDisplaySettings(null, -1, ref dm); dm.width = w; dm.height = h; dm.fields = 0x80000 | 0x100000; return ChangeDisplaySettings(ref dm, 1); }
  static void Mouse(uint flags) { var i = new INPUT[1]; i[0].type = 0; i[0].mi.flags = flags; SendInput(1, i, Marshal.SizeOf(typeof(INPUT))); }
  public static void Move(int x, int y) { SetCursorPos(x, y); Mouse(1); }
  public static void Down() { Mouse(2); } public static void Up() { Mouse(4); }
  [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr h, int cmd);
  [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
  // Bring a window to the front and give it the keyboard, so the game's input (read only while it is in front) gets the clicks.
  // Windows lets a process take the foreground only right after input, so an Alt press goes first.
  public static bool Focus(IntPtr h) { Key(0x38, false, false); Key(0x38, false, true); ShowWindow(h, 9); SetForegroundWindow(h); return GetForegroundWindow() == h; }
  public static void Key(ushort scan, bool ext, bool up) { var i = new INPUT[1]; i[0].type = 1; i[0].ki.scan = scan;
    i[0].ki.flags = 8u | (ext ? 1u : 0u) | (up ? 2u : 0u); SendInput(1, i, Marshal.SizeOf(typeof(INPUT))); }
}
'@
function Get-Screen { $b = [Drawing.Bitmap]::new([Input]::W, [Input]::H); $gr = [Drawing.Graphics]::FromImage($b); $gr.CopyFromScreen(0, 0, 0, 0, $b.Size); $gr.Dispose(); $b }
# The screen, small and coarse (64 by 36, 16 grey levels), so a still screen gives the same string; and whether it shows anything.
function Look {
  $b = Get-Screen; $s = [Drawing.Bitmap]::new($b, 64, 36); $b.Dispose(); $sb = [Text.StringBuilder]::new(2304); $sum = 0
  for ($y = 0; $y -lt 36; $y++) { for ($x = 0; $x -lt 64; $x++) { $p = $s.GetPixel($x, $y); $v = [int](($p.R * 3 + $p.G * 6 + $p.B) / 10); $sum += $v; [void]$sb.Append([char](97 + [int][math]::Floor($v / 16))) } }
  $s.Dispose(); @{ hash = $sb.ToString(); lit = ($sum / (2304 * 255)) -gt 0.03 }
}
# The average colour of a 24 by 10 patch centred on x, y (screen pixels).
function Get-Patch($x, $y) {
  $b = Get-Screen; $r = 0; $gg = 0; $bl = 0
  for ($j = -5; $j -lt 5; $j++) { for ($i = -12; $i -lt 12; $i++) { $p = $b.GetPixel([math]::Max(0, [math]::Min($b.Width - 1, $x + $i)), [math]::Max(0, [math]::Min($b.Height - 1, $y + $j))); $r += $p.R; $gg += $p.G; $bl += $p.B } }
  $b.Dispose(); @([int]($r / 240), [int]($gg / 240), [int]($bl / 240))
}
# Keys by name, as xdotool names them in games.json and the plan: scan code and whether it is an extended key.
$scan = @{ Up = 0x48, 1; Down = 0x50, 1; Left = 0x4B, 1; Right = 0x4D, 1; Escape = 0x01, 0; Return = 0x1C, 0; space = 0x39, 0
  F1 = 0x3B, 0; F2 = 0x3C, 0; F3 = 0x3D, 0; F4 = 0x3E, 0; F5 = 0x3F, 0; F6 = 0x40, 0; F7 = 0x41, 0; F8 = 0x42, 0; F9 = 0x43, 0; F10 = 0x44, 0
  F11 = 0x57, 0; F12 = 0x58, 0; ctrl = 0x1D, 0; shift = 0x2A, 0; alt = 0x38, 0 }
$letters = 'qwertyuiop', 'asdfghjkl', 'zxcvbnm'; $row = 0x10, 0x1E, 0x2C
for ($i = 0; $i -lt 3; $i++) { for ($j = 0; $j -lt $letters[$i].Length; $j++) { $scan["$($letters[$i][$j])"] = ($row[$i] + $j), 0 } }
function Send-Key($name, $up) { $k = $scan[$name]; if (-not $k) { throw "unknown key $name" }; [Input]::Key($k[0], [bool]$k[1], $up) }
function Press-Key($combo) { $parts = $combo -split '\+'; foreach ($p in $parts) { Send-Key $p $false; Start-Sleep -Milliseconds 50 }
  Start-Sleep -Milliseconds 150; [array]::Reverse($parts); foreach ($p in $parts) { Send-Key $p $true } }

# games.json places are on a 1280x720 screen; the game runs full screen at the desktop's size, so they are scaled to it.
$rc = [Input]::SetResolution(1280, 720)
$W = [Input]::W; $H = [Input]::H
function SX($x) { [int]($x * $script:W / 1280) }; function SY($y) { [int]($y * $script:H / 720) }
function Save-Shot($o, $name) { $b = Get-Screen; $b.Save("$o\shot_$name.png", [Drawing.Imaging.ImageFormat]::Png); $b.Dispose(); Write-Step $o $name }
function Write-Step($o, $text) { $l = "$([DateTimeOffset]::Now.ToUnixTimeSeconds()) $text"; $l | Add-Content "$o\steps.log"; Write-Host "$(Split-Path $o -Leaf): $l" }
function Wait-Settle($o, $secs, $before) {
  $end = (Get-Date).AddSeconds($secs); $prev = $null; $t0 = $null
  while ((Get-Date) -lt $end) {
    $l = Look
    if ($l.lit -and $l.hash -ne $before) { $t0 = $t0 ?? (Get-Date); if ($l.hash -eq $prev -or ((Get-Date) - $t0).TotalSeconds -ge 10) { return $true } }
    $prev = $l.hash; Start-Sleep 3
  }
  $false
}
function Invoke-Press($o, $x, $y, $secs) {
  if ($script:win) { [void][Input]::Focus($script:win) }
  # The screen before the click is taken once the hover has drawn and the screen holds still: the software-rendered game can
  # take seconds to draw a hover, which must not count as the click's next screen.
  [Input]::Move((SX $x), (SY $y)); Start-Sleep 2; $before = (Look).hash
  for ($k = 0; $k -lt 5; $k++) { Start-Sleep 3; $now = (Look).hash; if ($now -eq $before) { break }; $before = $now }
  foreach ($i in 1..3) {
    [Input]::Move((SX $x), (SY $y)); Start-Sleep -Milliseconds 500; [Input]::Down(); Start-Sleep -Milliseconds 200; [Input]::Up()
    if (Wait-Settle $o $secs $before) { return }
    Write-Step $o "no change after clicking $x,$y (try $i)"
  }
}
function Wait-Colour($o, $secs, $x, $y, $r, $gg, $b) {
  $end = (Get-Date).AddSeconds($secs)
  while ((Get-Date) -lt $end) { $c = Get-Patch (SX $x) (SY $y); if ((($c[0]-$r)*($c[0]-$r) + ($c[1]-$gg)*($c[1]-$gg) + ($c[2]-$b)*($c[2]-$b)) -lt 1600) { return }; Start-Sleep 3 }
  Write-Step $o "timed out waiting for the colour at $x,$y"
}

. (Join-Path $PSScriptRoot '..\..\plugin-test-host\windows\evidence.ps1')  # Write-Evidence, shared with the test host

function Invoke-RealGame($run) {
  $name = $run.name
  $dir = Join-Path $work "run-$name"; Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
  Copy-Item $demo $dir -Recurse
  Copy-Item "$work\mesa\x64\*.dll" $dir
  if ($name -ne 'baseline') { $pf = Get-PluginsFolder; if ($pf) { Copy-Item "$pf\*" "$dir\plugins" -Recurse -Force } }
  $o = New-Item -ItemType Directory -Force (Join-Path $Out $name)
  $docs = [Environment]::GetFolderPath('MyDocuments'); Remove-Item -Recurse -Force "$docs\PiBoSo" -ErrorAction SilentlyContinue
  Get-ChildItem $dir -Recurse -File -Filter *.exe | ForEach-Object { New-NetFirewallRule -DisplayName "realgame $name $($_.Name)" -Direction Outbound -Program $_.FullName -Action Block | Out-Null }
  Get-ChildItem $dir -Recurse -File | ForEach-Object { $_.FullName.Substring($dir.Length + 1) } | Sort-Object | Set-Content "$o\before.lst"
  Start-Process $pm -ArgumentList '/AcceptEula', '/Quiet', '/Minimized', '/BackingFile', "$work\$name.pml"
  Start-Sleep 8
  $rc = [Input]::SetResolution(1280, 720); $script:W = [Input]::W; $script:H = [Input]::H
  $p = Start-Process -FilePath "$dir\$($g.exe)" -WorkingDirectory $dir -PassThru
  # Wait for the game's window, then bring it to the front: until then the screen shows the desktop.
  $script:win = [IntPtr]::Zero; $end = (Get-Date).AddSeconds(120)
  while ($script:win -eq [IntPtr]::Zero -and (Get-Date) -lt $end) { Start-Sleep 2; $p.Refresh(); $script:win = $p.MainWindowHandle }
  Write-Step $o "started $($g.exe), screen ${W}x$H, window $(if ($script:win -ne [IntPtr]::Zero) { 'found, in front: ' + [Input]::Focus($script:win) } else { 'not found' })"
  foreach ($s in $g.steps) {
    if ($s.until) { $u = $s.until; Wait-Colour $o $s.wait $u[0] $u[1] $u[2] $u[3] $u[4] }
    if ($s.click) { Invoke-Press $o $s.click[0] $s.click[1] $s.wait } elseif (-not (Wait-Settle $o $s.wait 'none')) { Write-Step $o 'timed out' }
    Save-Shot $o $s.name
  }
  Send-Key 'Up' $false; $t = 0
  foreach ($k in @($run.keys) | Where-Object { $_ } | Sort-Object { [int]$_[0] }) {
    if ([int]$k[0] -gt $t) { Start-Sleep ([int]$k[0] - $t); $t = [int]$k[0] }
    Press-Key $k[1]; Start-Sleep 2; Save-Shot $o "key-$($k[1])"; $t += 2
  }
  $ride = [int]($run.ride ?? 30); if ($ride -gt $t) { Start-Sleep ($ride - $t) }
  Send-Key 'Up' $true; Save-Shot $o 'ride'
  & taskkill /T /F /PID $p.Id | Out-Null; Start-Sleep 5
  & $pm /Terminate; Start-Sleep 5
  Get-ChildItem $dir -Recurse -File | ForEach-Object { $_.FullName.Substring($dir.Length + 1) } | Sort-Object | Set-Content "$o\after.lst"
  Write-Host "${name}: saving the Process Monitor log"
  & $pm /AcceptEula /Quiet /OpenLog "$work\$name.pml" /SaveAs "$work\$name.csv"
  Get-Process Procmon* -ErrorAction SilentlyContinue | Wait-Process -Timeout 300 -ErrorAction SilentlyContinue
  @("game: $($g.name), $($g.exe), installer SHA-256 $($g.sha256)", 'steps (unix time, step):') + (Get-Content "$o\steps.log") | Set-Content "$o\host.log"
  Remove-Item "$o\steps.log"
  Write-Evidence $name $dir $o $p.Id "$work\$name.csv"
}

$vc = (Get-CimInstance Win32_VideoController | Select-Object -First 1).Name
$os = (Get-CimInstance Win32_OperatingSystem).Caption
@("Machine: $os, video: $vc (no GPU). Screen: ${W}x$H (setting 1280x720 returned $rc). OpenGL: Mesa 26.3.0 llvmpipe (software). Process Monitor SHA-256: $pmSha.",
  "Game: $($g.name), installer SHA-256 $($g.sha256).", 'Release files (SHA-256):') + $fileLines | Set-Content (Join-Path $Out 'machine.txt')
Set-NetFirewallProfile -All -LogBlocked True -LogMaxSizeKilobytes 32767
$runs = @($cfg.realgame) | Where-Object { $_ }
$longest = ($runs | ForEach-Object { [int]($_.ride ?? 30) } | Measure-Object -Maximum).Maximum
foreach ($r in @([pscustomobject]@{ name = 'baseline'; ride = $longest }) + $runs) { Invoke-RealGame $r }
exit 0

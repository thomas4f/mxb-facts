# Runs a tool's release files on a throwaway Windows machine (a GitHub-hosted runner) and writes the evidence.
#
#   pwsh run.ps1 -Plan plan.json -Release <release folder> -HostDir <folder with mxbikes.exe, gpbikes.exe, victim.dlo> -Out <evidence folder>
#
# The plan (lab/plugin-test-host/windows/README.md) names the release files by URL and SHA-256, the game, and the runs:
# plugin cases (the host's arguments) and apps (an .exe started with no account, then stopped). Each run is recorded by
# Process Monitor, with an outbound firewall block on every program in the run folder, and its evidence goes to
# <Out>/<name>/ in the same layout as src/collect.sh, plus what only Windows shows (procmon.txt, registry.txt, outside.txt).
# The machine holds no keys and no repository credentials; only the evidence folder leaves it.
param([Parameter(Mandatory)][string]$Plan, [Parameter(Mandatory)][string]$Release, [Parameter(Mandatory)][string]$HostDir, [Parameter(Mandatory)][string]$Out)
$ErrorActionPreference = 'Stop'
$cfg = Get-Content $Plan -Raw | ConvertFrom-Json  # $cfg, not $plan: variables ignore case, and $Plan is a [string]
$game = if ($cfg.game -eq 'gpbikes') { 'gpbikes.exe' } else { 'mxbikes.exe' }
$work = Join-Path $env:RUNNER_TEMP 'mxbfacts'
New-Item -ItemType Directory -Force $work, $Out | Out-Null
$Out = (Resolve-Path $Out).Path

# Process Monitor and Mesa's software OpenGL (llvmpipe, the same renderer as the Wine lab), pinned by SHA-256.
function Get-Pinned($url, $sha, $file) {
  Invoke-WebRequest $url -OutFile $file
  $h = (Get-FileHash $file -Algorithm SHA256).Hash.ToLower()
  if ($sha -and $h -ne $sha) { throw "$url has SHA-256 $h, expected $sha" }
  $h
}
# Sysinternals publishes Process Monitor at one moving URL, so its hash is recorded rather than pinned.
$pmSha = Get-Pinned 'https://download.sysinternals.com/files/ProcessMonitor.zip' $null "$work\pm.zip"
Expand-Archive "$work\pm.zip" "$work\pm" -Force
Get-Pinned 'https://github.com/pal1000/mesa-dist-win/releases/download/26.3.0/mesa3d-26.3.0-release-msvc.7z' `
  'c505fcc77e8f63a09d7ddac086591d2f542c0698d37fc9e3094685a34d0d9991' "$work\mesa.7z" | Out-Null
7z x -y "-o$work\mesa" "$work\mesa.7z" | Out-Null
$env:GALLIUM_DRIVER = 'llvmpipe'
$pm = "$work\pm\Procmon64.exe"

# The runner has .NET 8, 10 and 11, and .NET starts an app only on the major version it was built for. So for apps,
# Microsoft's .NET Desktop Runtimes 6, 7 and 9 (each with its base runtime) are installed too, pinned by SHA-256, so
# each app runs on the runtime its players have rather than rolled forward to a newer one.
$dotnet = if ($cfg.apps) {
  foreach ($r in @(@('6.0.36', '0d20debb26fc8b2bc84f25fbd9d4596a6364af8517ebf012e8b871127b798941'),
                   @('7.0.20', '57e7c16e7226c9a29dbc3faedd9e5876cec494c7660528052f52160521e7b714'),
                   @('9.0.23', 'eefb60bd0f3fb33c0787074cebc0467ffba32bcb01088613121649fc3bdb4a27'))) {
    $exe = "$work\windowsdesktop-runtime-$($r[0]).exe"
    Get-Pinned "https://builds.dotnet.microsoft.com/dotnet/WindowsDesktop/$($r[0])/windowsdesktop-runtime-$($r[0])-win-x64.exe" $r[1] $exe | Out-Null
    $inst = Start-Process $exe '/install', '/quiet', '/norestart' -Wait -PassThru
    if ($inst.ExitCode -notin 0, 3010) { throw ".NET Desktop Runtime $($r[0]) didn't install (exit code $($inst.ExitCode))" }
  }
  " .NET runtimes: $((& dotnet --list-runtimes) -join '; ')."
}

# The release files, downloaded by the workflow's fetch job (tools/fetch_release.py, which also reads MEGA links) and
# listed in release.json, checked again against their SHA-256 and unpacked (zip, 7z, rar) into rel\<file name>\.
$rel = New-Item -ItemType Directory -Force "$work\rel"
$fileLines = foreach ($f in @(Get-Content (Join-Path $Release 'release.json') -Raw | ConvertFrom-Json)) {
  $name = $f.name; $file = Join-Path $Release $name
  $h = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLower()
  if ($h -ne $f.sha256) { throw "$name has SHA-256 $h, expected $($f.sha256)" }
  $dest = New-Item -ItemType Directory -Force (Join-Path $rel $name)
  if ($name -match '\.(zip|7z|rar)$') { 7z x -y "-o$dest" $file | Out-Null } else { Copy-Item -LiteralPath $file $dest }
  "$h  $name"
}

# The game's plugins folder: a folder named "plugins" in a release file, else the folder that holds its .dlo files.
function Get-PluginsFolder {
  $p = Get-ChildItem $rel -Recurse -Directory | Where-Object Name -eq 'plugins' | Select-Object -First 1
  if ($p) { return $p.FullName }
  $d = Get-ChildItem $rel -Recurse -File -Filter *.dlo | Sort-Object { $_.FullName.Length } | Select-Object -First 1
  if ($d) { return $d.DirectoryName }
}

# One run: a fresh folder, a block rule per program in it, Process Monitor around it, then the evidence.
function Invoke-Run($name, $exe, [string[]]$exeArgs, $seconds) {
  $run = Join-Path $work "run-$name"
  Remove-Item -Recurse -Force $run -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Force $run | Out-Null
  Copy-Item "$HostDir\$game", "$HostDir\victim.dlo", "$work\mesa\x64\*.dll" $run
  $pf = Get-PluginsFolder
  if ($pf) { New-Item -ItemType Directory -Force "$run\plugins" | Out-Null; Copy-Item "$pf\*" "$run\plugins" -Recurse }
  Copy-Item "$rel\*" (New-Item -ItemType Directory -Force "$run\release") -Recurse
  $o = New-Item -ItemType Directory -Force (Join-Path $Out $name)
  Get-ChildItem $run -Recurse -File -Filter *.exe | ForEach-Object { New-NetFirewallRule -DisplayName "mxbfacts $name $($_.Name)" -Direction Outbound -Program $_.FullName -Action Block | Out-Null }
  Get-ChildItem $run -Recurse -File | ForEach-Object { $_.FullName.Substring($run.Length + 1) } | Sort-Object | Set-Content "$o\before.lst"
  Start-Process $pm -ArgumentList '/AcceptEula', '/Quiet', '/Minimized', '/BackingFile', "$work\$name.pml"
  Start-Sleep 8
  $sp = @{ FilePath = (Join-Path $run $exe); WorkingDirectory = $run; PassThru = $true
          RedirectStandardOutput = "$o\host.log"; RedirectStandardError = "$work\$name-stderr.log" }
  # Start-Process joins the arguments with spaces, so one with a space (a --click text) is quoted to stay one argument.
  if ($exeArgs) { $sp.ArgumentList = $exeArgs | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } } }
  $p = Start-Process @sp
  if (-not $p.WaitForExit($seconds * 1000)) {
    & taskkill /T /F /PID $p.Id | Out-Null
    "stopped after $seconds seconds" | Add-Content "$o\host.log"
  } else { "exit=$($p.ExitCode)" | Add-Content "$o\host.log" }
  Start-Sleep 5
  & $pm /Terminate; Start-Sleep 5
  Get-ChildItem $run -Recurse -File | ForEach-Object { $_.FullName.Substring($run.Length + 1) } | Sort-Object | Set-Content "$o\after.lst"
  & $pm /AcceptEula /Quiet /OpenLog "$work\$name.pml" /SaveAs "$work\$name.csv"
  Get-Process Procmon* -ErrorAction SilentlyContinue | Wait-Process -Timeout 180 -ErrorAction SilentlyContinue
  Write-Evidence $name $run $o $p.Id "$work\$name.csv"
}

. (Join-Path $PSScriptRoot 'evidence.ps1')  # Write-Evidence, shared with the real-game run

$vc = (Get-CimInstance Win32_VideoController | Select-Object -First 1).Name
$os = (Get-CimInstance Win32_OperatingSystem).Caption
@("Machine: $os, video: $vc (no GPU). OpenGL: Mesa 26.3.0 llvmpipe (software). Process Monitor SHA-256: $pmSha.$dotnet",
  'Release files (SHA-256):') + $fileLines | Set-Content (Join-Path $Out 'machine.txt')
Set-NetFirewallProfile -All -LogBlocked True -LogMaxSizeKilobytes 32767

foreach ($c in $cfg.cases) { Invoke-Run $c.name $game ([string[]]$c.args) 600 }
foreach ($a in $cfg.apps) { Invoke-Run $a.name "release\$($a.exe)" ([string[]]$a.args) ([int]($a.seconds ?? 60)) }
exit 0

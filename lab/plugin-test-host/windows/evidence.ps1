# The evidence of one Windows run, from its file lists and Process Monitor's log, in the layout of src/collect.sh plus what
# only Windows shows (procmon.txt, registry.txt, outside.txt) and raw\ (the originals those are read from, compressed). Dot-sourced by run.ps1 here and by lab/real-game/windows/run.ps1;
# it reads $Out (the evidence root) from the script that sources it.

# A CreateFile that can change a file: write, delete or append access, or a disposition that creates or overwrites it.
# (Process Monitor's Detail also lists ShareMode, which says nothing about this open, so only these two fields are read.)
function Test-Writes($detail) {
  if ($detail -notmatch 'Desired Access: (.*?), Disposition: (\w+)') { return $false }
  $Matches[1] -match 'Write|Delete|Append' -or $Matches[2] -match '^(Create|Overwrite|OverwriteIf|Supersede)$'
}

# One file of raw\, gzip-compressed.
function Save-Raw($o, $name, [string[]]$lines) {
  $raw = New-Item -ItemType Directory -Force "$o\raw"
  $gz = [IO.Compression.GZipStream]::new([IO.File]::Create("$raw\$name.gz"), [IO.Compression.CompressionLevel]::Optimal)
  $w = [IO.StreamWriter]::new($gz, [Text.UTF8Encoding]::new($false))
  foreach ($l in $lines) { $w.WriteLine($l) }
  $w.Dispose()
}

function Write-Evidence($name, $run, $o, $rootPid, $csv) {
  $diff = Compare-Object (Get-Content "$o\before.lst") (Get-Content "$o\after.lst")
  ($diff | ForEach-Object { "$(if ($_.SideIndicator -eq '=>') { '>' } else { '<' }) .\$($_.InputObject)" }) -join "`n" | Set-Content "$o\files.diff"
  Remove-Item "$o\before.lst", "$o\after.lst"
  # The run's processes: the one started and every process it started, by PID, from Process Monitor's Process Create events.
  $rows = @(Import-Csv $csv)
  $pids = [Collections.Generic.HashSet[string]]::new(); [void]$pids.Add([string]$rootPid)
  do {
    $n = $pids.Count
    foreach ($r in $rows) { if ($r.Operation -eq 'Process Create' -and $pids.Contains($r.PID) -and $r.Detail -match 'PID: (\d+)') { [void]$pids.Add($Matches[1]) } }
  } while ($pids.Count -ne $n)
  # The console window Windows attaches (conhost.exe) is left out: it is Windows', not the tool's.
  $mine = $rows | Where-Object { $pids.Contains($_.PID) -and $_.'Process Name' -ne 'conhost.exe' }
  # The originals: every Process Monitor event of the run's processes, unfiltered (other processes on the machine are left
  # out: they are Windows' and the runner's), and the firewall's whole log.
  Save-Raw $o 'procmon.csv' @($mine | ConvertTo-Csv -NoTypeInformation)
  $noise = '^(FASTIO_|IRP_MJ_|Query|CloseFile|ReadFile|LockFile|UnlockFile|CreateFileMapping|Thread |RegOpenKey|RegQuery|RegCloseKey|RegEnum|RegSetInfoKey|Load Image|Process Profiling)'
  # What the run did, each distinct operation once with its count: reads, queries, closes and loaded DLLs (loaded.txt) left out.
  $mine | Where-Object { $_.Operation -notmatch $noise -and -not ($_.Operation -eq 'CreateFile' -and -not (Test-Writes $_.Detail)) } | Group-Object 'Process Name', Operation, Path, Result |
    ForEach-Object { $r = $_.Group[0]; '{0,5}  {1}  {2}  {3}  {4}' -f $_.Count, $r.'Process Name', $r.Operation, $r.Path, $r.Result } |
    Set-Content "$o\procmon.txt"
  $net = $mine | Where-Object Operation -match '^(TCP|UDP) ' | ForEach-Object { "$($_.'Time of Day')  $($_.'Process Name') ($($_.PID))  $($_.Operation)  $($_.Path)  $($_.Result)" }
  $fw = "$env:SystemRoot\System32\LogFiles\Firewall\pfirewall.log"
  $fwlog = if (Test-Path $fw) { @(Get-Content $fw) } else { @() }
  Save-Raw $o 'firewall.log' $fwlog
  $drops = $fwlog | Where-Object { $_ -match ' DROP .* SEND (\d+)$' -and $pids.Contains($Matches[1]) }
  if ($net -or $drops) {
    @('Internet connections the run''s processes tried (Process Monitor), then the firewall''s drops for them. Every program in the run folder was blocked by the firewall, so this shows attempts, not traffic.') + $net + $drops | Set-Content "$o\network.txt"
  } else {
    'No internet connections (TCP or UDP) by the run''s processes in Process Monitor, and none dropped by the firewall. Every program in the run folder was blocked, so this shows attempts, not traffic.' | Set-Content "$o\network.txt"
  }
  $mine | Where-Object Operation -eq 'Load Image' | ForEach-Object Path | Sort-Object -Unique | Set-Content "$o\loaded.txt"
  $w = $mine | Where-Object { $_.Operation -in 'WriteFile', 'SetRenameInformationFile', 'SetDispositionInformationFile', 'SetEndOfFileInformationFile' -or
      ($_.Operation -eq 'CreateFile' -and (Test-Writes $_.Detail)) }
  $outside = $w | Where-Object { $_.Path -notlike "$run\*" -and $_.Path -notlike "$Out\*" -and $_.Path -notmatch '^[A-Z]:\\\$' } |
    ForEach-Object { "$($_.'Process Name')  $($_.Operation)  $($_.Path)  $($_.Result)" } | Sort-Object -Unique
  if (-not $outside) { $outside = 'No files written outside the run folder.' }
  $outside | Set-Content "$o\outside.txt"
  $reg = $mine | Where-Object Operation -in 'RegSetValue', 'RegCreateKey', 'RegDeleteValue', 'RegDeleteKey', 'RegRenameKey' |
    ForEach-Object { "$($_.'Process Name')  $($_.Operation)  $($_.Path)  $($_.Result)" } | Sort-Object -Unique
  if (-not $reg) { $reg = 'No registry writes.' }
  $reg | Set-Content "$o\registry.txt"
  Get-ChildItem $run -Recurse -File -Include *.dlo, *.exe, *.dll | Where-Object { $_.DirectoryName -ne $run -or $_.Extension -ne '.dll' } |
    ForEach-Object { '{0}  {1}' -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(), $_.FullName.Substring($run.Length + 1) } | Set-Content "$o\plugins.sha256"
  Add-Type -AssemblyName System.Drawing
  Get-ChildItem $run -Filter 'shot_*.bmp' | ForEach-Object {
    $img = [Drawing.Image]::FromFile($_.FullName); $img.Save("$o\$($_.BaseName).png", [Drawing.Imaging.ImageFormat]::Png); $img.Dispose()
  }
  # Logs the plugins write in their own folders, so a card can quote them.
  Get-ChildItem "$run\plugins" -Recurse -File -Include *.log, *.txt -ErrorAction SilentlyContinue | Where-Object FullName -match '\\(logs?|update)\\|\.log$' |
    ForEach-Object { Copy-Item $_.FullName (Join-Path $o (($_.FullName.Substring("$run\plugins\".Length)) -replace '[\\/]', '-')) }
}

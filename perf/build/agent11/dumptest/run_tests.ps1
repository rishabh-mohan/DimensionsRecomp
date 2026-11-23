# Scratch test for bench/agent11/testg_dump.ps1 (task #23). Starts two harmless hidden processes
# (ping, powershell Start-Sleep), dumps them with TestGWin.MiniDump, kills them, analyzes the dumps,
# and checks the legodimensions.map symbol lookup. Never starts the game.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
Set-Location $root
Add-Type -TypeDefinition ([IO.File]::ReadAllText("$root\bench\agent11\testg_win.cs")) -Language CSharp
Add-Type -TypeDefinition ([IO.File]::ReadAllText("$root\bench\agent11\testg_dump.cs")) -Language CSharp
$out = Join-Path $PSScriptRoot 'fresh'
New-Item -ItemType Directory -Force $out | Out-Null

$p1 = Start-Process -FilePath "$env:SystemRoot\System32\PING.EXE" -ArgumentList '-n 60 127.0.0.1' -WindowStyle Hidden -PassThru
$p2 = Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList '-NoProfile -Command Start-Sleep 60' -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 4
"ping pid $($p1.Id): " + [TestGWin]::MiniDump($p1.Id, "$out\ping.dmp")
"powershell pid $($p2.Id): " + [TestGWin]::MiniDump($p2.Id, "$out\pwsh.dmp")
foreach ($p in $p1, $p2) {
    try { if (-not $p.HasExited) { $p.Kill() }; [void]$p.WaitForExit(5000); "pid $($p.Id) exited: $($p.HasExited)" }
    catch { "kill $($p.Id): $($_.Exception.Message)" }
}

$map = "$root\build\baseline-bin\legodimensions.map"
$sw = [Diagnostics.Stopwatch]::StartNew()
$ms = [TestGDump+MapSymbols]::Load($map)
"map: {0} symbols, preferred 0x{1:X}, timestamp {2:x8}, load {3} ms" -f $ms.Count, $ms.Preferred, $ms.TimeStamp, $ms.LoadMs
$r = New-Object IO.StreamReader $map
$entry = $null; $pubs = @()
while ($null -ne ($l = $r.ReadLine())) {
    if ($l -match '^\s*entry point at\s+([0-9a-f]{4}):([0-9a-f]{8})') { $entry = $Matches[2]; break }
    if ($pubs.Count -lt 3 -and $l -match '^\s*0001:[0-9a-f]{8}\s+(\S+)\s+([0-9a-f]{16})\s+f\s' -and ($l.GetHashCode() % 7000) -eq 0) { $pubs += , @($Matches[1], [Convert]::ToUInt64($Matches[2], 16) - 0x140000000) }
}
$r.Close()
foreach ($pp in $pubs) {
    $d = 0
    $n = $ms.Lookup([uint32]($pp[1] + 0x10), [ref]$d)
    "lookup {0}+0x10 -> {1}+0x{2:X}  match={3}" -f $pp[0], $n, $d, ($n -eq $pp[0])
}
if ($entry) {
    $rva = [uint32](0x1000 + [Convert]::ToUInt32($entry, 16))
    $d = 0; $n = $ms.Lookup($rva, [ref]$d)
    "entry point 0001:{0} (rva 0x{1:X}) -> {2}+0x{3:X}" -f $entry, $rva, $n, $d
}
"map test total {0} ms" -f $sw.ElapsedMilliseconds

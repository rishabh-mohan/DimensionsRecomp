# day-update.ps1: Agent 5, task #26, second part: Agent 10's day-draft condition 1 and N1-N3, staged in
# build\agent5\day-draft\ only (nothing goes to bench\agent5\day\). Run it after install-scrnsave.ps1.
# It checks that the draft files are still the ones the fix was made from, copies new\make-run-day.ps1,
# new\README-DAY.md and new\RUN-DAY.cmd into the draft folder, runs make-run-day.ps1 there (source: the installed
# bench\agent5\launch\run-night.ps1, which must be 565D30D4...), checks that run-day.ps1 equals new\day\run-day.ps1
# and that run-day.diff names repo-relative paths, and prints the draft folder's hashes. -Check: checks only.
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent5\scrnsave-fix\day-update.ps1 [-Check]
param([switch]$Check)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$Here = $PSScriptRoot
$Repo = (Resolve-Path (Join-Path $Here '..\..\..')).Path
$Dd = Join-Path $Repo 'build\agent5\day-draft'
$LogFile = Join-Path $Here 'install-log.txt'
function Sha([string]$P) { return (Get-FileHash -LiteralPath $P -Algorithm SHA256).Hash }
function Say([string]$M) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  day-update: $M"
    Write-Host $line
    [IO.File]::AppendAllText($LogFile, $line + "`n", (New-Object Text.UTF8Encoding $false))
}
$Night = Join-Path $Repo 'bench\agent5\launch\run-night.ps1'
$NightWant = '565D30D40DC5025AD63FD9B9F606724BABC167BC81FCB6FBEB6362B603977112'
$Before = [ordered]@{
    'make-run-day.ps1' = '17413F8A566E79BF0721BF77DA64BACEA629DBAB7D70887A6AA75CBAA2827780'
    'run-day.ps1'      = 'D86F6DE04B3EDA47A4811CD7139B9BEE21B43E0E368AAB4287143F45B8C59E98'
    'run-day.diff'     = '54E35C180DBF4B164DB86CC5B61D71952F132C7149E69D909634DAE0B60EC12F'
    'README-DAY.md'    = '9D131EB14B89DBBBB642D0C40AA0103FB7742BD95B1BA143E7F8E6A8CE308FCB'
    'RUN-DAY.cmd'      = '4B5489B4C1021038C44D2C97A18B19E675AB278CCC43D5CD1B11B21F5039CAD9'
}
$Copy = [ordered]@{   # file -> staged sha
    'make-run-day.ps1' = '4A96B0B947D0796B7C65539C35648C50DB4F61E43B7191B58C8816B69E968D4C'
    'README-DAY.md'    = 'A36574ED620880809AC504C387B8AF923E1B490120A378B1A19E742B594DF517'
    'RUN-DAY.cmd'      = 'B08645E9D4296AC1623E65EBBB3ECCB532EC5C49837569D3AD8F7A7F671DD736'
}
$DayWant = 'B67EBD6C2C9A378C8897558DD71AD383DCC85015952601F3EDF2FAED415ADC65'
$bad = New-Object System.Collections.Generic.List[string]
$hn = Sha $Night
if ($hn -ne $NightWant) { $bad.Add("bench\agent5\launch\run-night.ps1 has sha256 $($hn.Substring(0, 8)), not $($NightWant.Substring(0, 8)): run install-scrnsave.ps1 first") }
if ((Sha (Join-Path $Here 'new\day\run-day.ps1')) -ne $DayWant) { $bad.Add('new\day\run-day.ps1 is not the staged one') }
foreach ($f in $Before.Keys) {
    $h = Sha (Join-Path $Dd $f)
    if ($h -eq $Before[$f]) { continue }
    if ($Copy.Contains($f) -and $h -eq $Copy[$f]) { continue }   # copied by an earlier run
    if ($f -eq 'run-day.ps1' -and $h -eq $DayWant) { continue }    # made by an earlier run
    if ($f -eq 'run-day.diff') { continue }                        # made by an earlier run (its sha depends on the paths)
    $bad.Add("build\agent5\day-draft\$f has sha256 $($h.Substring(0, 8)): neither the one the fix was made from nor the staged one")
}
foreach ($f in $Copy.Keys) { if ((Sha (Join-Path $Here "new\$f")) -ne $Copy[$f]) { $bad.Add("new\$f is not the staged one") } }
if ($bad.Count) { foreach ($b in $bad) { Say "REFUSED: $b" }; exit 2 }
if ($Check) { Say 'checks OK (-Check: nothing changed)'; exit 0 }

foreach ($f in $Copy.Keys) { Copy-Item -LiteralPath (Join-Path $Here "new\$f") -Destination (Join-Path $Dd $f) -Force; Say "copied new\$f to build\agent5\day-draft\" }
$out = @(& (Join-Path $PSHOME 'powershell.exe') -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Dd 'make-run-day.ps1') 2>&1 | ForEach-Object { "$_" })
$rc = $LASTEXITCODE
foreach ($l in $out) { Say "  make-run-day: $l" }
if ($rc -ne 0) { Say "ERROR: make-run-day.ps1 exit $rc"; exit 3 }
$hd = Sha (Join-Path $Dd 'run-day.ps1')
if ($hd -ne $DayWant) { Say "ERROR: run-day.ps1 is $hd, not the staged $DayWant"; exit 3 }
$hdrs = @([IO.File]::ReadAllLines((Join-Path $Dd 'run-day.diff')) | Where-Object { $_ -match '^(diff --git |--- |\+\+\+ )' })
$want = @('diff --git a/bench/agent5/launch/run-night.ps1 b/build/agent5/day-draft/run-day.ps1', '--- a/bench/agent5/launch/run-night.ps1', '+++ b/build/agent5/day-draft/run-day.ps1')
if (($hdrs -join '|') -cne ($want -join '|')) { Say "ERROR: run-day.diff header lines: $($hdrs -join ' / ')"; exit 3 }
Say "run-day.ps1 = the staged $($DayWant.Substring(0, 8)); run-day.diff paths are repo-relative: $($hdrs[0])"
foreach ($f in @(Get-ChildItem -LiteralPath $Dd -File | Sort-Object Name)) { Say "  $(Sha $f.FullName)  build/agent5/day-draft/$($f.Name)" }
exit 0

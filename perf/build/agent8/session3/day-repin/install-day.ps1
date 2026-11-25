# install-day.ps1: S3T-5, condition 2 of the day launcher (RESUME section 6 item 6): copy the rated day draft from
# build\agent5\day-draft\ into bench\agent5\day\ and compare the hashes. Plan only unless -Install is given.
# Run -Install ONLY after the Overseer relays M11's rating (condition 3) and says go.
# It refuses (exit 2, nothing written) if: a draft file is not at its rated hash; a night/day launcher runs (mutex
# Local\Agent5RunNight-real, or a powershell whose command line runs run-night.ps1/run-day.ps1 with -File);
# perf-notes\WINDOW-HOLD.txt exists; the target folder exists and is not empty; a night-launcher file has changed.
# It never starts a launcher, never touches the registry, perf-notes\ or bench\agent5\launch\.
# Exit: 0 plan OK / installed and all hashes equal; 1 copied but a hash differs (target left for inspection); 2 refused.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File install-day.ps1 [-Install] [-NoOptional] [-Target DIR]
#   -Target is for tests only (default bench\agent5\day). A test target must be under build\agent5\session3\.
param([switch]$Install, [switch]$NoOptional, [string]$Target = '')
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$Src = Join-Path $Repo 'build\agent5\day-draft'
$Real = Join-Path $Repo 'bench\agent5\day'
if (-not $Target) { $Target = $Real }
$Target = [IO.Path]::GetFullPath($Target)
$IsTest = ($Target -ine $Real)
if ($IsTest -and -not $Target.StartsWith((Join-Path $Repo 'build\agent5\session3\'), [StringComparison]::OrdinalIgnoreCase)) {
    Write-Host "refused: a test -Target must be under build\agent5\session3\ ($Target)" -ForegroundColor Red; exit 2
}
$Log = Join-Path $PSScriptRoot $(if ($IsTest) { 'install-day-test-log.txt' } else { 'install-day-log.txt' })

# The rated day draft (Agent 10 checked these at 07:56 on 23 Nov; README-DAY 9739BCF8 L138-141).
$Need = [ordered]@{
    'RUN-DAY.cmd'       = 'B08645E9D4296AC1623E65EBBB3ECCB532EC5C49837569D3AD8F7A7F671DD736'
    'STOP-LAUNCHER.cmd' = 'CE27332F354B1DBB253678189A7070D8AB3C79010D1584C9DE204BB160C8E1B3'
    'launcher-ctl.ps1'  = '6DDE3150B72D6B0D849B17788098F9C10C1E96CBF5CF3BBC395C95C935C34895'
    'run-day.ps1'       = 'B67EBD6C2C9A378C8897558DD71AD383DCC85015952601F3EDF2FAED415ADC65'
    'README-DAY.md'     = '9739BCF8952146D9258E7A843A4CC0F07451FBE81AE0A3FC795C35F05356EECB'
}
$Opt = [ordered]@{
    'make-run-day.ps1'  = '4A96B0B947D0796B7C65539C35648C50DB4F61E43B7191B58C8816B69E968D4C'
    'run-day.diff'      = '3D0E8753683A17AAAC3FD5B85377DC930FDF1CE6E9F338F8C2891E74C23082D2'
    'test-day.ps1'      = '410FB2ECBA7B72B9530B6DD50B7AB8F0FEDEE0A5650D0A1F705F201EA137118E'
}
# The installed night launcher set (post-SCRNSAVE install, RESUME section 8; run-matrix.ps1 re-pinned after M8's runner install 25 Nov 07:30,
# build\agent8\session3\day-repin\README.md). Must be equal before and after.
$Night = [ordered]@{
    'bench\agent5\launch\run-night.ps1' = '565D30D40DC5025AD63FD9B9F606724BABC167BC81FCB6FBEB6362B603977112'
    'bench\agent5\launch\README.md'     = 'B7CEBD635D847D4CB89D900B9E002B87526D487C971A03A4563EC6807B2A7965'
    'bench\agent5\launch\RUN-NIGHT.cmd' = 'D7A0362BE90C12B4F027116B9A5146D1F4C8D109110F885EE8CF62E6769DE6D5'
    'bench\agent8\run\run-matrix.ps1'   = '72370A1E737A3A34399E78D6D8C670F8B5789F0B49212A53F4846D89EF790C04'
}
$Files = [ordered]@{}; foreach ($k in $Need.Keys) { $Files[$k] = $Need[$k] }
if (-not $NoOptional) { foreach ($k in $Opt.Keys) { $Files[$k] = $Opt[$k] } }

$lines = New-Object System.Collections.Generic.List[string]
function Say([string]$T, [string]$C = 'Gray') { $lines.Add($T); Write-Host $T -ForegroundColor $C }
function Sha([string]$P) { if (Test-Path -LiteralPath $P) { return (Get-FileHash -LiteralPath $P -Algorithm SHA256).Hash } return '<missing>' }
function Done([int]$Code) {
    Say "exit $Code"
    if ($Install) { Add-Content -LiteralPath $Log -Value (($lines -join "`r`n") + "`r`n") -Encoding ASCII }
    exit $Code
}

Say "install-day $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') mode $(if ($Install) { 'INSTALL' } else { 'plan only' })$(if ($IsTest) { ' (TEST target)' }) -> $Target"
$why = New-Object System.Collections.Generic.List[string]
foreach ($k in $Files.Keys) {
    $h = Sha (Join-Path $Src $k); $ok = ($h -eq $Files[$k])
    Say "  source $(if ($ok) { 'OK  ' } else { 'BAD ' }) $($h.Substring(0, [Math]::Min(8, $h.Length)))  $k"
    if (-not $ok) { $why.Add("draft $k is $h, not the rated $($Files[$k].Substring(0, 8))") }
}
foreach ($k in $Night.Keys) {
    $h = Sha (Join-Path $Repo $k)
    if ($h -ne $Night[$k]) { $why.Add("night file $k is $h, not $($Night[$k].Substring(0, 8))") }
}
$m = $null
if ([System.Threading.Mutex]::TryOpenExisting('Local\Agent5RunNight-real', [ref]$m)) { $m.Dispose(); $why.Add('a launcher holds Local\Agent5RunNight-real') }
$procs = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe' or Name='pwsh.exe'" | Where-Object {
    $_.ProcessId -ne $PID -and $_.CommandLine -and $_.CommandLine -match '-File\s+"?[^"]*\\(run-night|run-day)\.ps1' })
foreach ($p in $procs) { $why.Add("a launcher process runs: pid $($p.ProcessId)") }
if (Test-Path -LiteralPath (Join-Path $Repo 'perf-notes\WINDOW-HOLD.txt')) { $why.Add('perf-notes\WINDOW-HOLD.txt exists (a window is on)') }
if ((Test-Path -LiteralPath $Target) -and @(Get-ChildItem -LiteralPath $Target -Force).Count) { $why.Add("$Target exists and is not empty (never overwrite an install)") }
if ($why.Count) { foreach ($w in $why) { Say "REFUSED: $w" 'Red' }; Say 'Nothing was written.'; Done 2 }
Say "checks OK: draft at rated hashes, night set unchanged, no launcher, no HOLD, target free" 'Green'
if (-not $Install) { Say "plan: copy $($Files.Count) files to $Target, then compare. Re-run with -Install after the go."; Done 0 }

New-Item -ItemType Directory -Force -Path $Target | Out-Null
foreach ($k in $Files.Keys) { Copy-Item -LiteralPath (Join-Path $Src $k) -Destination (Join-Path $Target $k) }
$bad = 0
foreach ($k in $Files.Keys) {
    $h = Sha (Join-Path $Target $k); $ok = ($h -eq $Files[$k]); if (-not $ok) { $bad++ }
    Say "  target $(if ($ok) { 'OK  ' } else { 'BAD ' }) $h  $k" $(if ($ok) { 'Gray' } else { 'Red' })
}
$extra = @(Get-ChildItem -LiteralPath $Target -Force | Where-Object { -not $Files.Contains($_.Name) })
foreach ($x in $extra) { $bad++; Say "  target EXTRA $($x.Name)" 'Red' }
foreach ($k in $Night.Keys) { $h = Sha (Join-Path $Repo $k); if ($h -ne $Night[$k]) { $bad++; Say "  night file changed during install: $k $h" 'Red' } }
if ($bad) { Say "$bad mismatch(es): the target is left as it is for inspection. Do not start RUN-DAY." 'Red'; Done 1 }
Say "installed: $($Files.Count) files, all hashes equal; night set unchanged." 'Green'
Done 0

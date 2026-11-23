# Agent 5, task #4: finalize W6 once the S4b bin exists.
# Usage (from the repo root):
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent5\w6-draft\finalize-w6.ps1 -Bin build/agent2/<name>-bin
#   ... -Bin build/agent2/devoff4-bin -Check    # pipeline check with a stand-in bin: writes only to w6-draft\check\
# It writes matrix-window6.json (matrix-w6.json with the placeholder bin replaced by -Bin in every arm), RUN-WINDOW6.cmd
# (from RUN-WINDOW6.cmd.template) and FINAL.txt (sha256s, the bin's MANIFEST head, the -PlanOnly output and the GO line)
# in build\agent5\w6-draft\ (check\ with -Check). It checks the matrix against the rules of Agent 5's launcher
# (bench\agent5\launch\run-night.ps1, Test-Matrix) and runs bench\agent8\run\run-matrix.ps1 -PlanOnly at Below Normal
# priority, which reads the matrix and starts nothing. It writes nothing outside build\agent5\w6-draft\.
# Agent 8 copies matrix-window6.json to bench\agent8\run\ and RUN-WINDOW6.cmd to bench\agent8\ byte for byte, so the
# sha256 in the GO line stays valid.
param(
    [Parameter(Mandatory = $true)][string]$Bin,
    [string]$Only = 's0,p2,p2f,p2fc',
    [ValidateRange(1, 20)][int]$Repeats = 3,
    [switch]$Check,
    [switch]$NoPlan
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$Here = $PSScriptRoot
$Repo = (Resolve-Path (Join-Path $Here '..\..\..')).Path
if (Test-Path -LiteralPath (Join-Path $Repo 'perf-notes\WINDOW-HOLD.txt')) { Write-Host 'perf-notes\WINDOW-HOLD.txt exists: a timed window is running. Nothing done.' -ForegroundColor Red; exit 4 }
$Placeholder = 'build/agent2/S4b-bin-TBD'
$Out = if ($Check) { Join-Path $Here 'check' } else { $Here }
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$fail = New-Object System.Collections.Generic.List[string]
$utf8 = New-Object Text.UTF8Encoding $false
function Sha([string]$P) { return (Get-FileHash -LiteralPath $P -Algorithm SHA256).Hash }
function P($O, [string]$N) { if ($null -ne $O -and $O -is [System.Management.Automation.PSCustomObject]) { $pp = $O.PSObject.Properties[$N]; if ($null -ne $pp) { return $pp.Value } }; return $null }

# 1. the bin
$b = ($Bin -replace '\\', '/').TrimEnd('/')
if ($b -notmatch '^build/agent2/[A-Za-z0-9][A-Za-z0-9_.-]*-bin$' -or $b -match '\.\.') { throw "-Bin must be build/agent2/<name>-bin, not '$Bin'" }
$leaf = $b.Substring('build/agent2/'.Length)
$binDir = Join-Path $Repo ($b -replace '/', '\')
foreach ($f in @('MANIFEST.txt', 'legodimensions.exe')) { if (-not (Test-Path -LiteralPath (Join-Path $binDir $f) -PathType Leaf)) { throw "$b has no $f" } }
$exeSha = Sha (Join-Path $binDir 'legodimensions.exe')
$manHead = @(Get-Content -LiteralPath (Join-Path $binDir 'MANIFEST.txt') -TotalCount 40)

# 2. the matrix, by text replacement so the draft's layout stays
$when = Get-Date -Format 'yyyy-MM-dd HH:mm'
$txt = [IO.File]::ReadAllText((Join-Path $Here 'matrix-w6.json'))
$tag = if ($Check) { "PIPELINE CHECK ONLY with the stand-in bin $b, $when; do not promote" } else { "finalized $when for $b" }
$rxTitle = '"Window 6 DRAFT v2 \(Agent 5, task #4 run 2; Agent 8 promotes it as matrix-window6\.json\)'
$rxNote = '"DRAFT v2, not runnable yet:[^"]*"'
if ($txt -notmatch $rxTitle -or $txt -notmatch $rxNote) { throw 'matrix-w6.json: the draft title or first note is not the expected text' }
$txt = [regex]::Replace($txt, $rxTitle, "`"Window 6 (Agent 5's draft v2, $tag)", 1)
$note1 = "W6 $tag by build/agent5/w6-draft/finalize-w6.ps1 from Agent 5's draft v2 (matrix-w6.json): bin $b in every arm (legodimensions.exe sha256 $exeSha). The gates before any timed run are G1-G12 in build/agent12/w6-gates/W6-GATES.md (v2, 20:20); build/agent5/w6-draft/README.md has the summary."
$txt = [regex]::Replace($txt, $rxNote, ('"' + $note1 + '"'), 1)
$n = ([regex]::Matches($txt, [regex]::Escape($Placeholder))).Count
if ($n -lt 1) { throw "matrix-w6.json has no placeholder bin $Placeholder" }
$txt = $txt.Replace($Placeholder, $b)
$m = $txt | ConvertFrom-Json

# 3. the launcher's rules (run-night.ps1 Test-Matrix), for every arm
$allowedEnv = @('REX_TIMER_WAIT_BLOCKING', 'LEGO_GPU_WAIT_STATS')
$ids = @()
$arms = @(P $m 'arms')
foreach ($a in $arms) {
    $id = [string](P $a 'id'); $ids += $id
    $ab = ([string](P $a 'bin') -replace '\\', '/').TrimEnd('/')
    if ($ab -ne $b) { $fail.Add("arm '$id': bin '$ab' is not $b") }
    $ev = P $a 'env'
    if ($null -ne $ev) { foreach ($pp in $ev.PSObject.Properties) { if ($allowedEnv -cnotcontains $pp.Name) { $fail.Add("arm '$id': env key '$($pp.Name)' is not allowed") } } }
    if ([string](P $a 'menu')) { $fail.Add("arm '$id': menu") }
    if ((P $a 'profile') -eq $true) { $fail.Add("arm '$id': profile") }
    if (@(P $a 'triggers' | Where-Object { $_ }).Count) { $fail.Add("arm '$id': triggers") }
    $tm = P $a 'toml'; if ($null -ne $tm -and @($tm.PSObject.Properties).Count) { $fail.Add("arm '$id': toml") }
    if ([string](P $a 'seed_cache')) { $fail.Add("arm '$id': seed_cache") }
    $dr = [string](P $a 'driver')
    if ($dr -and -not (Test-Path -LiteralPath (Join-Path $Repo ('bench\agent8\run\' + ($dr -replace '/', '\'))) -PathType Leaf)) { $fail.Add("arm '$id': driver $dr is not in bench\agent8\run") }
}
$onlyList = @($Only -split '[,;\s]+' | Where-Object { $_ })
foreach ($o in $onlyList) { if ($ids -cnotcontains $o) { $fail.Add("only=: no arm '$o'") } }
if ((P $m 'sys_csv') -ne $true) { $fail.Add('sys_csv is not true (G11 needs it)') }

# 4. the files
$mPath = Join-Path $Out 'matrix-window6.json'
[IO.File]::WriteAllText($mPath, $txt, $utf8)
$cmd = [IO.File]::ReadAllText((Join-Path $Here 'RUN-WINDOW6.cmd.template')).Replace('__BIN__', $leaf).Replace('__WHEN__', $tag)
$cmd = [regex]::Replace($cmd, "`r?`n", "`r`n")
if ($Only -ne 's0,p2,p2f,p2fc' -or $Repeats -ne 3) { $fail.Add("RUN-WINDOW6.cmd runs -Only s0,p2,p2f,p2fc -Repeats 3; edit it by hand for -Only $Only -Repeats $Repeats") }
$cPath = Join-Path $Out 'RUN-WINDOW6.cmd'
[IO.File]::WriteAllText($cPath, $cmd, [Text.Encoding]::ASCII)

# 5. the runner's own plan (-PlanOnly starts nothing)
$plan = @(); $est = @()
if (-not $NoPlan) {
    (Get-Process -Id $PID).PriorityClass = 'BelowNormal'
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $plan = @(& (Join-Path $PSHOME 'powershell.exe') -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Repo 'bench\agent8\run\run-matrix.ps1') -Matrix $mPath -Only ($onlyList -join ',') -Repeats $Repeats -ColdShared -NoPrompt -PlanOnly 2>&1 | ForEach-Object { "$_" }); $code = $LASTEXITCODE } finally { $ErrorActionPreference = $old }
    $est = @($plan | Where-Object { $_ -match '^estimate (\d+) runs \(\d+ cold\), about (\d+) min' })
    $bad = @($plan | Where-Object { $_ -match '^!!! (ERROR|SKIPPED ARM|MATRIX ERROR)' -or $_ -match '^\s+SKIP ' })
    if ($code -ne 0) { $fail.Add("run-matrix.ps1 -PlanOnly exit $code") }
    if ($bad.Count) { $fail.Add("run-matrix.ps1 -PlanOnly: $($bad -join ' / ')") }
    if (-not $est.Count) { $fail.Add('run-matrix.ps1 -PlanOnly printed no estimate line') }
}

# 6. FINAL.txt
$mSha = Sha $mPath; $cSha = Sha $cPath
$go = "GO W6 matrix-window6.json $mSha only=$($onlyList -join ',') repeats=$Repeats"
$L = New-Object System.Collections.Generic.List[string]
$L.Add("W6 finalize (Agent 5, finalize-w6.ps1), $when, -Bin $b$(if ($Check) { '  [PIPELINE CHECK with a stand-in bin: do not promote]' })")
$L.Add("result: $(if ($fail.Count) { 'NOT OK: ' + ($fail -join ' | ') } else { 'OK' })")
$L.Add("matrix-window6.json  sha256 $mSha  ($mPath)")
$L.Add("RUN-WINDOW6.cmd      sha256 $cSha  ($cPath)")
$L.Add("bin $b  legodimensions.exe sha256 $exeSha")
$L.Add('')
$L.Add('Agent 8: copy matrix-window6.json to bench\agent8\run\ and RUN-WINDOW6.cmd to bench\agent8\ byte for byte, then check both sha256s.')
$L.Add('GO line for the overnight launcher (perf-notes\WINDOW-GO.txt, one line, only after the copy and Agent 1''s go):')
$L.Add($go)
$L.Add('')
$L.Add('--- MANIFEST.txt (first 40 lines)')
foreach ($x in $manHead) { $L.Add($x) }
$L.Add('')
$L.Add("--- run-matrix.ps1 -Matrix <matrix-window6.json> -Only $($onlyList -join ',') -Repeats $Repeats -ColdShared -NoPrompt -PlanOnly$(if ($NoPlan) { ' (skipped: -NoPlan)' })")
foreach ($x in $plan) { $L.Add($x) }
[IO.File]::WriteAllText((Join-Path $Out 'FINAL.txt'), (($L -join "`r`n") + "`r`n"), $utf8)
Write-Host ($L[0..8] -join "`r`n")
if ($est -and $est.Count) { Write-Host $est[0] }
Write-Host "written: $Out\FINAL.txt"
if ($fail.Count) { exit 1 } else { exit 0 }

# Timing matrix (task #16): round-robin timing runs of run-timing.ps1 over the arms of a matrix json.
# Double-click bench\agent8\RUN-TIMING-MATRIX.cmd on the unlocked desktop, or:
#   powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\run\run-matrix.ps1 [-Matrix run\matrix.json]
#       [-Only id,id] [-Repeats N] [-Quick] [-PlanOnly] [-NoPrompt] [-NoCold | -ColdShared] [-OutDir build\agent8\matrix\<yyyyMMdd-HHmm>]
# No -Matrix: lists bench\agent8\run\matrix*.json and asks for a number (Enter = matrix.json; -NoPrompt = matrix.json).
# Fields (anything else is an error):
#   top: title reference warmup_s warmup_from(firstframe|launch) measure_s repeats settle_s cooldown_s boot_timeout_s
#        close_timeout_s menu_s cold_run order(roundrobin|fixed) sys_csv min_window_after_ff_s cold_warmup_s
#        cold_measure_s quick{} notes[] arms[]
#   arm: id group ref repeats frames(perf|native) bin cvars[] env{} toml{} seed_cache seed_recipes_only triggers[]
#        menu menu_s driver(path | {script, args[]}) profile profile_s note
# Order: round k runs the arms with repeats >= k; roundrobin rotates the start arm each round (over the arms of that
# round), fixed keeps file order.
# seed_cache = <arm id> takes the cache of that arm's latest completed run here (the source runs first in every
# round). cold_run: one unscored cold run per bin before round 1 (warm-up min(warmup_s, cold_warmup_s), window
# min(measure_s, cold_measure_s); no seed, driver, profile or triggers). A missing bin (no MANIFEST.txt) skips its arms
# (and arms seeded from them); the rest run. -ColdShared: a single cold run, on the bin of round 1's first arm, instead
# of one per bin (it warms the shared game data; the other bins first launch as scored round-1 runs, whose windows
# still start >= min_window_after_ff_s after the first frame). -NoCold: no cold run.
# Session 3: min_window_after_ff_s (default 60, -Quick 0) = every window, cold runs too, starts >= that many s after the
# first frame: the warm-up is raised to floor - settle - menu (run-timing.ps1 -MinWindowAfterFirstFrame) and a run that
# still misses it is flagged window_before_floor. sys_csv true: every run logs sys.csv (drivers\sys-csv.ps1, 1 s) and
# sys.json. A run with an excluding flag (run.json excluded: light phase, window before the floor, input / foreground /
# power / screensaver changes on the interactive desktop) stays in results.csv but is left out of the summary numbers
# (summary.md "Flagged runs"; matrix_recheck.py --keep-flagged puts them back).
# Each run is run-timing.ps1 called in-process; a failed run is recorded and the matrix goes on; Ctrl+C closes the
# game (run-timing's finally) and still writes the results.
# Writes <OutDir>\results.csv (one row per run), summary.md, plan.txt, matrix.json (copy), logs\, runs\.
# Session 3 (M8, staged): warmup_runs N (top level, default 0; -WarmupRuns N overrides, -Quick 0) = N unscored GPU
# warm-up runs after the cold run(s) and before round 1: full-length runs (same warm-up, window, driver as a scored run)
# cycling over round 1's arms so that the last one is the arm before round 1's first (scored False, round 0, tag
# warm<j>-<arm>). Their numbers stay in results.csv (summary.md lists them as 'warm') and never enter the summary.
# results.csv also has over8 / over10 / over16_7 (frames > 8 / 10 / 16.667 ms, frame_summary.py over_*ms; blank when
# the run's frames.json predates them), frames_lt_light and light_share at full precision; new columns are appended
# after the old ones.
# Exit: 0 all runs OK, 1 some run not OK, 2 matrix/preflight error or cancelled.
param(
    [string]$Matrix = '',
    [string[]]$Only = @(),
    [int]$Repeats = 0,
    [switch]$Quick,
    [switch]$PlanOnly,
    [switch]$NoPrompt,
    [string]$OutDir = '',
    [switch]$NoCold,
    [switch]$ColdShared,        # one cold run (on round 1's first arm's bin) instead of one per bin; -NoCold wins
    [int]$WarmupRuns = -1,      # unscored warm-up runs before round 1 (-1 = the matrix's warmup_runs, default 0)
    [switch]$AllowRunningGame   # self-test only: a running legodimensions.exe is a warning instead of an abort
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\common.ps1"
. "$PSScriptRoot\timing-env.ps1"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$runner = Join-Path $PSScriptRoot 'run-timing.ps1'
$inv = [Globalization.CultureInfo]::InvariantCulture

$TopKeys = @('title', 'reference', 'warmup_s', 'warmup_from', 'measure_s', 'repeats', 'settle_s', 'cooldown_s', 'boot_timeout_s',
             'close_timeout_s', 'menu_s', 'cold_run', 'order', 'sys_csv', 'min_window_after_ff_s', 'cold_warmup_s', 'cold_measure_s',
             'warmup_runs', 'quick', 'notes', 'arms')
$ArmKeys = @('id', 'group', 'ref', 'repeats', 'frames', 'bin', 'cvars', 'env', 'toml', 'seed_cache', 'seed_recipes_only', 'triggers',
             'menu', 'menu_s', 'driver', 'profile', 'profile_s', 'note')
$QuickKeys = @('warmup_s', 'measure_s', 'repeats', 'settle_s', 'cooldown_s', 'boot_timeout_s', 'close_timeout_s', 'menu_s', 'profile_s',
               'min_window_after_ff_s', 'cold_warmup_s', 'cold_measure_s', 'warmup_runs')
$NumKeys = @('warmup_s', 'measure_s', 'repeats', 'settle_s', 'cooldown_s', 'boot_timeout_s', 'close_timeout_s', 'menu_s', 'profile_s',
             'min_window_after_ff_s', 'cold_warmup_s', 'cold_measure_s', 'warmup_runs')
$D = @{ warmup_s = 60; measure_s = 120; repeats = 3; settle_s = 20; cooldown_s = 10; boot_timeout_s = 240; close_timeout_s = 60
        menu_s = 60; profile_s = 120; min_window_after_ff_s = 60; cold_warmup_s = 10; cold_measure_s = 30; warmup_runs = 0 }
$QD = @{ warmup_s = 10; measure_s = 20; settle_s = 5; menu_s = 20; cooldown_s = 5; min_window_after_ff_s = 0; cold_warmup_s = 5; cold_measure_s = 10; warmup_runs = 0 }
# Estimate per run (Agent 8, window 3 runs, 23:45-00:30): warm boot to the first-frame signal ~12 s, first boot of a
# build ~25 s, close ~5 s (WM_CLOSE exit seen within ~1-3 s), post-processing ~5 s.
$Est = @{ boot_warm_s = 12; boot_cold_s = 25; close_s = 5; post_s = 5 }

function Get-P($O, [string]$N, $Default = $null) {
    if ($null -ne $O -and $O -is [System.Management.Automation.PSCustomObject]) {
        $pp = $O.PSObject.Properties[$N]
        if ($null -ne $pp -and $null -ne $pp.Value) { return $pp.Value }
    }
    return $Default
}
function Test-Num($V) { return ($V -is [int] -or $V -is [long] -or $V -is [double] -or $V -is [decimal]) }
function Get-Val($Mx, $Arm, [string]$N) {
    if ($Quick) {
        $v = Get-P (Get-P $Mx 'quick') $N; if ($null -ne $v) { return $v }
        if ($QD.ContainsKey($N)) { return $QD[$N] }
    }
    $v = Get-P $Arm $N; if ($null -ne $v) { return $v }
    $v = Get-P $Mx $N; if ($null -ne $v) { return $v }
    return $D[$N]
}
function N($X, [int]$Dg = 3) {
    if ($null -eq $X -or "$X" -eq '') { return '' }
    if ($X -is [bool]) { return [string]$X }
    try { return ([math]::Round([double]$X, $Dg)).ToString($inv) } catch { return [string]$X }
}
function Find-Script([string]$P, [string]$MatrixDir) {
    if (-not $P) { return $null }
    if ([IO.Path]::IsPathRooted($P)) { return $P }
    foreach ($b in @($MatrixDir, $PSScriptRoot, $repoRoot)) {
        $c = Join-Path $b $P
        if (Test-Path -LiteralPath $c -PathType Leaf) { return (Resolve-Path -LiteralPath $c).Path }
    }
    return (Join-Path $repoRoot $P)
}
function Get-EnvSnap { $h = @{}; foreach ($e in [Environment]::GetEnvironmentVariables('Process').GetEnumerator()) { $h[[string]$e.Key] = [string]$e.Value }; return $h }
function Restore-Env($Snap) {
    $now = Get-EnvSnap; $fixed = New-Object System.Collections.Generic.List[string]
    foreach ($k in @($now.Keys)) {
        if (-not $Snap.ContainsKey($k)) { [Environment]::SetEnvironmentVariable($k, $null, 'Process'); $fixed.Add($k) }
        elseif ($Snap[$k] -cne $now[$k]) { [Environment]::SetEnvironmentVariable($k, $Snap[$k], 'Process'); $fixed.Add($k) }
    }
    foreach ($k in @($Snap.Keys)) { if (-not $now.ContainsKey($k)) { [Environment]::SetEnvironmentVariable($k, $Snap[$k], 'Process'); $fixed.Add($k) } }
    if ($fixed.Count) { Write-Host "ENV LEAK fixed: $($fixed -join ' ')" -ForegroundColor Yellow }
}

# ---------- matrix: read and validate ----------
function Read-Matrix([string]$Path) {
    $R = @{ path = $Path; dir = (Split-Path -Parent $Path); mx = $null; errors = (New-Object System.Collections.Generic.List[string])
            arms = @(); title = (Split-Path -Leaf $Path) }
    $E = $R.errors
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { $E.Add("matrix file not found: $Path"); return $R }
    try { $mx = [IO.File]::ReadAllText($Path) | ConvertFrom-Json } catch { $E.Add("not valid JSON: $($_.Exception.Message)"); return $R }
    $R.mx = $mx
    foreach ($pp in $mx.PSObject.Properties) { if ($TopKeys -notcontains $pp.Name) { $E.Add("unknown top-level field '$($pp.Name)' (allowed: $($TopKeys -join ', '))") } }
    $t = Get-P $mx 'title'; if ($t) { $R.title = [string]$t }
    $q = Get-P $mx 'quick'
    if ($null -ne $q) {
        foreach ($pp in $q.PSObject.Properties) {
            if ($QuickKeys -notcontains $pp.Name) { $E.Add("unknown field 'quick.$($pp.Name)' (allowed: $($QuickKeys -join ', '))") }
            elseif (-not (Test-Num $pp.Value)) { $E.Add("quick.$($pp.Name) must be a number") }
        }
    }
    foreach ($k in $NumKeys) { $v = Get-P $mx $k; if ($null -ne $v -and -not (Test-Num $v)) { $E.Add("$k must be a number, not '$v'") } }
    $wf = [string](Get-P $mx 'warmup_from' 'firstframe'); if (@('firstframe', 'launch') -notcontains $wf) { $E.Add("warmup_from must be firstframe or launch, not '$wf'") }
    $ord = [string](Get-P $mx 'order' 'roundrobin'); if (@('roundrobin', 'fixed') -notcontains $ord) { $E.Add("order must be roundrobin or fixed, not '$ord'") }
    $cr = Get-P $mx 'cold_run'; if ($null -ne $cr -and $cr -isnot [bool]) { $E.Add('cold_run must be true or false') }
    $sc0 = Get-P $mx 'sys_csv'; if ($null -ne $sc0 -and $sc0 -isnot [bool]) { $E.Add('sys_csv must be true or false') }
    foreach ($k in @('min_window_after_ff_s', 'cold_warmup_s', 'cold_measure_s', 'warmup_runs')) { $v = Get-P $mx $k; if ((Test-Num $v) -and $v -lt 0) { $E.Add("$k must be >= 0") } }
    $wr0 = Get-P $mx 'warmup_runs'; if ((Test-Num $wr0) -and ([double]$wr0 -ne [math]::Floor([double]$wr0) -or $wr0 -gt 20)) { $E.Add('warmup_runs must be a whole number 0-20') }
    $arms = @(Get-P $mx 'arms' @())
    if ($arms.Count -eq 0) { $E.Add('no arms'); return $R }
    $ids = @{}
    $list = New-Object System.Collections.Generic.List[object]
    foreach ($a in $arms) {
        if ($a -isnot [System.Management.Automation.PSCustomObject]) { $E.Add("arms: every arm must be an object"); continue }
        $id = [string](Get-P $a 'id' '')
        foreach ($pp in $a.PSObject.Properties) { if ($ArmKeys -notcontains $pp.Name) { $E.Add("arm '$id': unknown field '$($pp.Name)' (allowed: $($ArmKeys -join ', '))") } }
        if ($id -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{0,31}$') { $E.Add("arm id '$id' must be 1-32 of A-Z a-z 0-9 _ . - (it names the run dirs)"); continue }
        if ($ids.ContainsKey($id)) { $E.Add("duplicate arm id '$id'"); continue }
        $ids[$id] = $a; $list.Add($a)
        if (-not (Get-P $a 'bin')) { $E.Add("arm '$id': no bin") }
        $fr = [string](Get-P $a 'frames' 'perf'); if (@('perf', 'native') -notcontains $fr) { $E.Add("arm '$id': frames must be perf or native, not '$fr'") }
        foreach ($k in @('ref', 'profile', 'seed_recipes_only')) { $v = Get-P $a $k; if ($null -ne $v -and $v -isnot [bool]) { $E.Add("arm '$id': $k must be true or false") } }
        foreach ($k in @('repeats', 'menu_s', 'profile_s')) { $v = Get-P $a $k; if ($null -ne $v -and -not (Test-Num $v)) { $E.Add("arm '$id': $k must be a number") } }
        foreach ($k in @('cvars', 'triggers')) { foreach ($x in @(Get-P $a $k @())) { if ("$x" -match ';') { $E.Add("arm '$id': $k item '$x' contains ';' (not supported)") } } }
        foreach ($k in @('env', 'toml')) {
            $o = Get-P $a $k
            if ($null -eq $o) { continue }
            if ($o -isnot [System.Management.Automation.PSCustomObject]) { $E.Add("arm '$id': $k must be an object {name: value}"); continue }
            foreach ($pp in $o.PSObject.Properties) { if ("$($pp.Value)" -match ';') { $E.Add("arm '$id': $k $($pp.Name) value contains ';' (not supported)") } }
        }
        $dr = Get-P $a 'driver'
        if ($null -ne $dr -and $dr -isnot [string] -and -not (Get-P $dr 'script')) { $E.Add("arm '$id': driver must be a path or {script, args}") }
        if ($null -ne $dr -and $dr -isnot [string]) { foreach ($pp in $dr.PSObject.Properties) { if (@('script', 'args') -notcontains $pp.Name) { $E.Add("arm '$id': unknown field 'driver.$($pp.Name)' (allowed: script, args)") } } }
    }
    $R.arms = $list.ToArray()
    $ref = [string](Get-P $mx 'reference' '')
    if ($ref -and -not $ids.ContainsKey($ref)) { $E.Add("reference '$ref' is not an arm id") }
    $refs = @{}
    foreach ($a in $R.arms) {
        if (-not [bool](Get-P $a 'ref' $false)) { continue }
        $g = [string](Get-P $a 'group' '')
        if (-not $g) { $E.Add("arm '$($a.id)': ref needs a group (arms without a group use the top-level reference)") }
        elseif ($refs.ContainsKey($g)) { $E.Add("group '$g' has two ref arms: $($refs[$g]) and $($a.id)") }
        else { $refs[$g] = [string]$a.id }
    }
    foreach ($a in $R.arms) { $sc = [string](Get-P $a 'seed_cache' ''); if ($sc -and $sc -eq [string]$a.id) { $E.Add("arm '$($a.id)': seed_cache cannot name its own arm") } }
    return $R
}

function Order-Round([string[]]$Ids, $P, [bool]$Fixed, [int]$K) {
    if ($Fixed) {
        for ($i = 0; $i -lt $Ids.Count; $i++) {
            $src = $P.arms[$Ids[$i]].seed_arm
            if ($src -and ([array]::IndexOf($Ids, $src) -gt $i)) { $P.errors.Add("order fixed, round ${K}: arm $($Ids[$i]) seeds from $src, which comes later in the file") }
        }
        return , $Ids
    }
    $left = New-Object System.Collections.Generic.List[string]; foreach ($i in $Ids) { $left.Add($i) }
    $out = New-Object System.Collections.Generic.List[string]
    while ($left.Count) {
        $pick = $null
        foreach ($i in $left) { $src = $P.arms[$i].seed_arm; if (-not $src -or -not $left.Contains($src)) { $pick = $i; break } }
        if (-not $pick) { $P.errors.Add("round ${K}: seed_cache cycle among $($left -join ' ')"); $out.AddRange($left); break }
        $out.Add($pick); [void]$left.Remove($pick)
    }
    return , $out.ToArray()
}

# Effective warm-up of a run (s), as run-timing.ps1 will use it: a cold run asks for min(warmup_s, cold_warmup_s);
# with the first-frame floor (firstframe mode, cold runs always), settle + menu + warm-up >= min_window_after_ff_s.
function Get-WarmEff($Mx, $Arm, [bool]$Cold) {
    $menu = [string](Get-P $Arm 'menu' '')
    $warm = [double](Get-Val $Mx $Arm 'warmup_s')
    if ($Cold) { $warm = [math]::Min($warm, [double](Get-Val $Mx $Arm 'cold_warmup_s')) }
    $wf = if ($Cold) { 'firstframe' } else { [string](Get-P $Mx 'warmup_from' 'firstframe') }
    $floor = [double](Get-Val $Mx $Arm 'min_window_after_ff_s')
    if ($floor -gt 0 -and $wf -eq 'firstframe') {
        $pre = [double](Get-Val $Mx $Arm 'settle_s') + $(if ($menu) { [double](Get-Val $Mx $Arm 'menu_s') } else { 0 })
        $need = [math]::Ceiling($floor - $pre)
        if ($warm -lt $need) { $warm = $need }
    }
    return $warm
}
function Get-RunEstimate($Mx, $Arm, [bool]$Cold) {
    $wf = [string](Get-P $Mx 'warmup_from' 'firstframe')
    $menu = [string](Get-P $Arm 'menu' '')
    $warm = Get-WarmEff $Mx $Arm $Cold; $meas = [double](Get-Val $Mx $Arm 'measure_s')
    $boot = if ($Cold) { $Est.boot_cold_s } else { $Est.boot_warm_s }
    if ($Cold) { $wf = 'firstframe'; $meas = [math]::Min($meas, [double](Get-Val $Mx $Arm 'cold_measure_s')) }
    if ($wf -eq 'launch' -and -not $menu) { $t = [math]::Max($warm, $boot) + $meas }
    else { $t = $boot + [double](Get-Val $Mx $Arm 'settle_s') + $(if ($menu) { [double](Get-Val $Mx $Arm 'menu_s') } else { 0 }) + $warm + $meas }
    return $t + $Est.close_s + $Est.post_s + [double](Get-Val $Mx $Arm 'cooldown_s')
}

function Build-Plan($R, [string[]]$OnlyIds, [bool]$AssumeBins = $false) {
    $mx = $R.mx
    $P = @{ arms = [ordered]@{}; skips = (New-Object System.Collections.Generic.List[string]); errors = (New-Object System.Collections.Generic.List[string])
            rounds = (New-Object System.Collections.Generic.List[object]); runs = (New-Object System.Collections.Generic.List[object]); est_s = 0.0
            warmup_runs = 0; order = [string](Get-P $mx 'order' 'roundrobin'); warmup_from = [string](Get-P $mx 'warmup_from' 'firstframe') }
    $sel = @($R.arms)
    if ($OnlyIds.Count) {
        foreach ($o in $OnlyIds) { if (-not @($R.arms | Where-Object { $_.id -eq $o }).Count) { $P.errors.Add("-Only: no arm '$o' in this matrix") } }
        $sel = @($R.arms | Where-Object { $OnlyIds -contains $_.id })
    }
    foreach ($a in $sel) {
        $id = [string]$a.id
        $bin = [string](Get-P $a 'bin' '')
        $binAbs = if ($bin) { Resolve-RepoPath $bin } else { '' }
        $rp = if ($Repeats -gt 0) { $Repeats } else { [int](Get-Val $mx $a 'repeats') }
        $ai = @{ id = $id; arm = $a; bin = $bin; bin_abs = $binAbs; group = [string](Get-P $a 'group' ''); skip = $null; repeats = $rp
                 seed_arm = $null; seed_path = $null; driver = $null; driver_args = @() }
        if (-not $AssumeBins -and (-not $bin -or -not (Test-Path -LiteralPath (Join-Path $binAbs 'MANIFEST.txt') -PathType Leaf))) { $ai.skip = "bin $bin is missing or has no MANIFEST.txt (not staged yet?)" }
        $sc = [string](Get-P $a 'seed_cache' '')
        if ($sc) {
            if (@($R.arms | Where-Object { $_.id -eq $sc }).Count) {
                if (-not @($sel | Where-Object { $_.id -eq $sc }).Count) { $P.errors.Add("arm '$id': its seed_cache source arm '$sc' is not selected (-Only)") }
                $ai.seed_arm = $sc
            } else {
                $ai.seed_path = Resolve-RepoPath $sc
                if (-not (Test-Path -LiteralPath $ai.seed_path) -and -not $ai.skip) { $ai.skip = "seed_cache path $sc does not exist" }
            }
        }
        $dr = Get-P $a 'driver'
        if ($null -ne $dr) {
            $dp = if ($dr -is [string]) { $dr } else { [string](Get-P $dr 'script' '') }
            if ($dr -isnot [string]) { $ai.driver_args = @(@(Get-P $dr 'args' @()) | ForEach-Object { [string]$_ }) }
            $ai.driver = Find-Script $dp $R.dir
            if (-not (Test-Path -LiteralPath $ai.driver -PathType Leaf) -and -not $ai.skip) { $ai.skip = "driver $dp not found" }
        }
        $P.arms[$id] = $ai
    }
    $changed = $true
    while ($changed) {
        $changed = $false
        foreach ($ai in @($P.arms.Values)) {
            if (-not $ai.skip -and $ai.seed_arm -and $P.arms.Contains($ai.seed_arm) -and $P.arms[$ai.seed_arm].skip) { $ai.skip = "its seed source arm $($ai.seed_arm) is skipped"; $changed = $true }
        }
    }
    foreach ($ai in $P.arms.Values) { if ($ai.skip) { $P.skips.Add("$($ai.id): $($ai.skip)") } }
    $runnable = @($P.arms.Values | Where-Object { -not $_.skip } | ForEach-Object { $_.id })
    $maxRep = 0; foreach ($id in $runnable) { if ($P.arms[$id].repeats -gt $maxRep) { $maxRep = $P.arms[$id].repeats } }
    $n = $runnable.Count
    for ($k = 1; $k -le $maxRep; $k++) {
        # Arms of this round first, then the rotation over them (caveat 3: rotating the full list and then dropping
        # the arms that are done could start a round with the arm that ended the previous one).
        $ids = @($runnable | Where-Object { $P.arms[$_].repeats -ge $k })
        $m = $ids.Count
        if ($P.order -ne 'fixed' -and $m -gt 1) {
            $sh = ($k - 1) % $m
            if ($sh -gt 0) { $ids = @($ids[$sh..($m - 1)]) + @($ids[0..($sh - 1)]) }
        }
        $ids = Order-Round $ids $P ($P.order -eq 'fixed') $k
        $P.rounds.Add($ids)
    }
    $seq = 0
    if ([bool](Get-P $mx 'cold_run' $false) -and -not $NoCold -and $P.rounds.Count) {
        $seen = @{}
        foreach ($id in $P.rounds[0]) {
            $b = $P.arms[$id].bin_abs.ToLowerInvariant()
            if ($seen.ContainsKey($b)) { continue }
            if ($ColdShared -and $seen.Count) { break }
            $seen[$b] = 1; $seq++
            $e = Get-RunEstimate $mx $P.arms[$id].arm $true
            $P.runs.Add(@{ seq = $seq; round = 0; id = $id; rep = 0; cold = $true; warm = $false; est_s = $e; tag = "cold-$id" }); $P.est_s += $e
        }
    }
    # Unscored GPU warm-up runs (session 3): full-length runs cycling over round 1's arms, ending with the arm before
    # round 1's first, so no arm runs twice in a row across the warm-up / round-1 boundary (when round 1 has > 1 arm).
    $nWarm = if ($WarmupRuns -ge 0) { $WarmupRuns } else { [int](Get-Val $mx $null 'warmup_runs') }
    $P.warmup_runs = 0
    if ($nWarm -gt 0 -and $P.rounds.Count) {
        $r1 = @($P.rounds[0]); $m1 = $r1.Count
        for ($j = 1; $j -le $nWarm; $j++) {
            $id = $r1[(($m1 - (($nWarm - $j + 1) % $m1)) % $m1)]
            $seq++
            $e = Get-RunEstimate $mx $P.arms[$id].arm $false
            $P.runs.Add(@{ seq = $seq; round = 0; id = $id; rep = 0; cold = $false; warm = $true; est_s = $e; tag = "warm$j-$id" }); $P.est_s += $e
            $P.warmup_runs++
        }
    }
    for ($k = 1; $k -le $P.rounds.Count; $k++) {
        foreach ($id in $P.rounds[$k - 1]) {
            $seq++
            $e = Get-RunEstimate $mx $P.arms[$id].arm $false
            $P.runs.Add(@{ seq = $seq; round = $k; id = $id; rep = $k; cold = $false; warm = $false; est_s = $e; tag = "$id-r$k" }); $P.est_s += $e
        }
    }
    return $P
}

function Get-PlanLines($R, $P) {
    $mx = $R.mx
    $L = New-Object System.Collections.Generic.List[string]
    $L.Add("=== timing matrix: $($R.title) ===")
    $L.Add("matrix   $($R.path)$(if ($Quick) { '   [-Quick: short settle/menu/warm-up/window, FUNCTIONAL ONLY]' })")
    foreach ($nt in @(Get-P $mx 'notes' @())) { $L.Add("note     $nt") }
    $wf = $P.warmup_from
    $floor0 = [double](Get-Val $mx $null 'min_window_after_ff_s')
    $L.Add("settings warm-up from $wf$(if ($wf -eq 'firstframe') { ' (boot timeout ' + (N (Get-Val $mx $null 'boot_timeout_s') 0) + ' s, settle ' + (N (Get-Val $mx $null 'settle_s') 0) + ' s)' }); order $($P.order); close timeout $(N (Get-Val $mx $null 'close_timeout_s') 0) s; cooldown $(N (Get-Val $mx $null 'cooldown_s') 0) s")
    $L.Add("floor    every window >= $(N $floor0 0) s after the first-frame signal$(if ($floor0 -le 0) { ' (OFF)' } else { ' (cold runs too; warm-ups raised to fit, misses flagged window_before_floor)' }); sys.csv $(if ([bool](Get-P $mx 'sys_csv' $false)) { 'ON (1 s system-state log, sys.json per run)' } else { 'off' })")
    if (-not $Quick -and $floor0 -lt 60) { $L.Add("!!! WARNING min_window_after_ff_s is $(N $floor0 0) s: timing windows need >= 60 s after the first frame (Agent 1's floor); fine for functional checks only") }
    $L.Add('arms:')
    foreach ($ai in $P.arms.Values) {
        $a = $ai.arm
        $w0 = [double](Get-Val $mx $a 'warmup_s'); $we = Get-WarmEff $mx $a $false
        $bits = @("bin $($ai.bin)", "frames $([string](Get-P $a 'frames' 'perf'))", "x$($ai.repeats)",
                  "warm-up $(N $we 0) s$(if ($we -ne $w0) { ' (raised from ' + (N $w0 0) + ' s for the floor)' })", "window $(N (Get-Val $mx $a 'measure_s') 0) s")
        if ($ai.group) { $bits += "group $($ai.group)$(if ([bool](Get-P $a 'ref' $false)) { ' (ref)' })" }
        $cv = @(Get-P $a 'cvars' @()); if ($cv.Count) { $bits += "cvars $($cv -join ' ')" }
        $ev = Get-P $a 'env'; if ($null -ne $ev -and @($ev.PSObject.Properties).Count) { $bits += "env $((@($ev.PSObject.Properties) | ForEach-Object { "$($_.Name)=$($_.Value)" }) -join ' ')" }
        $tv = Get-P $a 'toml'; if ($null -ne $tv -and @($tv.PSObject.Properties).Count) { $bits += "toml $((@($tv.PSObject.Properties) | ForEach-Object { "$($_.Name)=$($_.Value)" }) -join '; ')" }
        if ($ai.seed_arm -or $ai.seed_path) { $bits += "seed from $(if ($ai.seed_arm) { "arm $($ai.seed_arm)" } else { $ai.seed_path })$(if ([bool](Get-P $a 'seed_recipes_only' $false)) { ' (recipes only)' })" }
        $tr = @(Get-P $a 'triggers' @()); if ($tr.Count) { $bits += "triggers $($tr -join ' ')" }
        $mn = [string](Get-P $a 'menu' ''); if ($mn) { $bits += "MENU '$mn' ($(N (Get-Val $mx $a 'menu_s') 0) s)" }
        if ($ai.driver) { $bits += "driver $($ai.driver) $($ai.driver_args -join ' ')" }
        if ([bool](Get-P $a 'profile' $false)) { $bits += "PROFILE $(N (Get-Val $mx $a 'profile_s') 0) s (not for timing)" }
        $L.Add("  $(if ($ai.skip) { 'SKIP ' } else { '     ' })$($ai.id): $($bits -join '; ')")
        $nt = [string](Get-P $a 'note' ''); if ($nt) { $L.Add("         $nt") }
    }
    foreach ($s in $P.skips) { $L.Add("!!! SKIPPED ARM $s") }
    $cold = @($P.runs | Where-Object { $_.cold })
    if ($cold.Count) {
        $ca = $P.arms[$cold[0].id].arm
        $L.Add("cold     $(($cold | ForEach-Object { "$($_.id) ($($P.arms[$_.id].bin))" }) -join ', '): unscored, before round 1 (warm-up $(N (Get-WarmEff $mx $ca $true) 0) s, window $(N ([math]::Min([double](Get-Val $mx $ca 'measure_s'), [double](Get-Val $mx $ca 'cold_measure_s'))) 0) s)")
        if ($ColdShared) {
            $nb = @($P.rounds[0] | ForEach-Object { $P.arms[$_].bin_abs.ToLowerInvariant() } | Select-Object -Unique).Count
            $L.Add("         -ColdShared: one cold run for all $nb bin(s); the other bins first launch as scored round-1 runs")
        }
    }
    $warmR = @($P.runs | Where-Object { $_.warm })
    if ($warmR.Count) { $L.Add("warm     $(($warmR | ForEach-Object { $_.id }) -join ' '): $($warmR.Count) unscored GPU warm-up run(s), full length, after the cold run(s) and before round 1") }
    for ($k = 1; $k -le $P.rounds.Count; $k++) { $L.Add("round $k  $($P.rounds[$k - 1] -join ' ')") }
    $L.Add("order    $(if ($P.rounds.Count) { ($P.rounds | ForEach-Object { $_ -join ' ' }) -join ' | ' } else { '(no runnable arms)' })")
    $L.Add("estimate $($P.runs.Count) runs ($($cold.Count) cold$(if ($warmR.Count) { ", $($warmR.Count) warm-up" })), about $([math]::Ceiling($P.est_s / 60)) min (warm boot $($Est.boot_warm_s) s, cold boot $($Est.boot_cold_s) s, close $($Est.close_s) s per run)")
    foreach ($e in $P.errors) { $L.Add("!!! ERROR $e") }
    return , $L
}

# ---------- pick the matrix ----------
$onlyIds = @($Only | ForEach-Object { $_ -split '[,;\s]+' } | Where-Object { $_ })
if (-not $Matrix) {
    $default = Join-Path $PSScriptRoot 'matrix.json'
    $cands = @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter 'matrix*.json' -File | Sort-Object @{ Expression = { $_.Name -ne 'matrix.json' } }, Name)
    if ($NoPrompt -or $PlanOnly -or $cands.Count -le 1) { $Matrix = $default }
    else {
        Write-Host 'Timing matrices:' -ForegroundColor Cyan
        for ($i = 0; $i -lt $cands.Count; $i++) {
            $r0 = Read-Matrix $cands[$i].FullName
            if ($r0.errors.Count) { Write-Host ("  [{0}] {1}: INVALID ({2})" -f ($i + 1), $cands[$i].Name, ($r0.errors -join '; ')) -ForegroundColor Red; continue }
            $p0 = Build-Plan $r0 @()
            $runnable0 = @($p0.arms.Values | Where-Object { -not $_.skip }).Count
            $miss = @($p0.arms.Values | Where-Object { $_.skip } | ForEach-Object { $_.bin } | Sort-Object -Unique)
            Write-Host ("  [{0}] {1}: {2}" -f ($i + 1), $cands[$i].Name, $r0.title)
            Write-Host ("        {0} runnable arms of {1}, {2} runs, about {3} min{4}" -f $runnable0, $p0.arms.Count, $p0.runs.Count, [math]::Ceiling($p0.est_s / 60),
                        $(if ($miss.Count) { "; MISSING BINS: $($miss -join ', ')" } else { '' }))
        }
        $ans = Read-Host 'Pick a number (Enter = matrix.json)'
        if ($ans -match '^\s*(\d+)\s*$' -and [int]$Matches[1] -ge 1 -and [int]$Matches[1] -le $cands.Count) { $Matrix = $cands[[int]$Matches[1] - 1].FullName }
        elseif ($ans.Trim()) { Write-Host "not a number in the list: $ans" -ForegroundColor Red; exit 2 }
        else { $Matrix = $default }
    }
}
if (-not [IO.Path]::IsPathRooted($Matrix)) {
    $found = $null
    foreach ($b in @((Get-Location).Path, (Split-Path -Parent $PSScriptRoot), $PSScriptRoot, $repoRoot)) { $c = Join-Path $b $Matrix; if (Test-Path -LiteralPath $c -PathType Leaf) { $found = (Resolve-Path -LiteralPath $c).Path; break } }
    $Matrix = if ($found) { $found } else { Join-Path $PSScriptRoot $Matrix }
}
$R = Read-Matrix $Matrix
if ($R.errors.Count) { foreach ($e in $R.errors) { Write-Host "!!! MATRIX ERROR: $e" -ForegroundColor Red }; "matrix $Matrix is not valid: nothing started"; exit 2 }
$mx = $R.mx
$P = Build-Plan $R $onlyIds
$planLines = Get-PlanLines $R $P
# Arms skipped for a missing bin: also show the plan as it will be once the bins are staged (order, seeds, estimate).
$stagedErrors = @()
if (@($P.arms.Values | Where-Object { $_.skip -like 'bin *' }).Count) {
    $P2 = Build-Plan $R $onlyIds $true
    $planLines.Add("staged   once the missing bins are staged: order $(if ($P2.rounds.Count) { ($P2.rounds | ForEach-Object { $_ -join ' ' }) -join ' | ' } else { '(none)' }); $($P2.runs.Count) runs, about $([math]::Ceiling($P2.est_s / 60)) min")
    $stagedErrors = @($P2.errors | Where-Object { $P.errors -notcontains $_ })
    foreach ($e in $stagedErrors) { $planLines.Add("!!! ERROR once staged: $e") }
}
$planLines | ForEach-Object { if ($_ -like '!!!*') { Write-Host $_ -ForegroundColor Red } else { $_ } }

# ---------- preflight ----------
$fatal = New-Object System.Collections.Generic.List[string]
foreach ($e in $P.errors) { $fatal.Add($e) }
foreach ($e in $stagedErrors) { $fatal.Add("once staged: $e") }
if ($P.runs.Count -eq 0) { $fatal.Add('no runnable arms') }
$pre = New-Object System.Collections.Generic.List[string]
$desk = Get-DesktopName; $deskOk = Test-TimingDesktop $desk
$pre.Add("desktop    $desk -> $(if ($deskOk) { 'interactive desktop: timing can be valid' } else { 'FUNCTIONAL ONLY: not the interactive desktop (agent command?), timing numbers are not valid' })")
$lu = Test-LogonUI
$pre.Add("LogonUI    $(if ($lu) { 'RUNNING: the PC is locked or at the lock screen -> timing not valid' } else { 'not running' })")
$pw = Get-PowerInfo
$pre.Add("power      $($pw.text)$(if (-not $pw.ac) { ' -> plug in the charger' })")
$ram = Get-FreeRamGB
$pre.Add("free RAM   $ram GB$(if ($ram -lt 6) { ' -> UNDER 6 GB: runs will not start' })")
$games = @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue)
if ($games.Count) {
    $gl = ($games | ForEach-Object { "pid $($_.Id)" }) -join ', '
    if ($AllowRunningGame) { $pre.Add("game       legodimensions.exe RUNNING ($gl): allowed by -AllowRunningGame (self-test)") }
    else { $pre.Add("game       legodimensions.exe RUNNING ($gl) -> close it first"); $fatal.Add("legodimensions.exe is running ($gl)") }
} else { $pre.Add('game       no legodimensions.exe running') }
$bp = @(Get-BuildProcs)
$pre.Add("builds     $(if ($bp.Count) { "RUNNING: $($bp -join ' ') -> timing not valid while they run" } else { "none ($(Get-BuildProcPatternText))" })")
foreach ($b in @($P.arms.Values | ForEach-Object { $_.bin } | Sort-Object -Unique)) {
    $ab = Resolve-RepoPath $b
    $ok = Test-Path -LiteralPath (Join-Path $ab 'MANIFEST.txt') -PathType Leaf
    $users = @($P.arms.Values | Where-Object { $_.bin -eq $b } | ForEach-Object { $_.id })
    $pre.Add("bin        $b : $(if ($ok) { 'ok (MANIFEST.txt)' } else { 'MISSING -> arms skipped: ' + ($users -join ' ') })")
}
$scr = Get-ItemProperty -LiteralPath 'HKCU:\Control Panel\Desktop' -ErrorAction SilentlyContinue
$scrExe = [string](Get-P $scr 'SCRNSAVE.EXE' '')   # via PSObject.Properties: a missing value is '' (a plain read throws under StrictMode: W6 GO refused 00:03:40)
if ([string](Get-P $scr 'ScreenSaveActive' '') -eq '1' -and $scrExe) {
    $pre.Add("screensaver $(Split-Path -Leaf $scrExe) after $(Get-P $scr 'ScreenSaveTimeOut' '?') s$(if ([string](Get-P $scr 'ScreenSaverIsSecure' '') -eq '1') { ', LOCKS on resume' }): the keep-awake request should hold it off; if it starts during timing runs, set it to (None)")
} else { $pre.Add('screensaver none') }
if ([bool](Get-P $mx 'sys_csv' $false)) {
    $sysDrvPath = Join-Path $PSScriptRoot 'drivers\sys-csv.ps1'
    if (Test-Path -LiteralPath $sysDrvPath -PathType Leaf) { $pre.Add('sys.csv    on: drivers\sys-csv.ps1 logs the system state every 1 s in every run (sys.csv, sys.json)') }
    else { $pre.Add('sys.csv    MISSING drivers\sys-csv.ps1'); $fatal.Add('sys_csv is true but drivers\sys-csv.ps1 is missing') }
}
$eta = (Get-Date).AddSeconds($P.est_s)
$pre.Add("estimate   $($P.runs.Count) runs, about $([math]::Ceiling($P.est_s / 60)) min: done around $($eta.ToString('HH:mm'))")
$valid0 = $deskOk -and -not $lu -and $bp.Count -eq 0 -and -not $Quick
''
'--- preflight ---'
foreach ($l in $pre) { if ($l -match 'RUNNING|MISSING|FUNCTIONAL|UNDER|charger') { Write-Host $l -ForegroundColor Yellow } else { $l } }
foreach ($f in $fatal) { Write-Host "!!! FATAL: $f" -ForegroundColor Red }
if (-not $valid0 -and -not $fatal.Count) { Write-Host '!!! These runs will be FUNCTIONAL ONLY (see above): their numbers are not timing results.' -ForegroundColor Yellow }
if ($PlanOnly) {
    # PlanOnly checks the matrix: exit 2 only for matrix/plan errors, not for the state of this PC (bins, game, RAM).
    'PlanOnly: nothing started.'
    if ($P.errors.Count -or $stagedErrors.Count) { exit 2 } else { exit 0 }
}
if ($fatal.Count) { 'not started.'; exit 2 }
if (-not $NoPrompt) {
    Write-Host ''
    Write-Host 'Do not touch the PC while the matrix runs (no mouse, no keyboard, no other programs), except for MENU prompts.' -ForegroundColor Cyan
    [void](Read-Host 'Press Enter to start (Ctrl+C to cancel)')
}

# ---------- run ----------
if (-not $OutDir) { $OutDir = Join-Path 'build\agent8\matrix' (Get-Date -Format 'yyyyMMdd-HHmm') }
$OutDir = Resolve-RepoPath $OutDir
if (Test-Path -LiteralPath $OutDir) { $i = 2; while (Test-Path -LiteralPath "$OutDir-$i") { $i++ }; $OutDir = "$OutDir-$i" }
$runsRoot = Join-Path $OutDir 'runs'; $logDir = Join-Path $OutDir 'logs'
New-Item -ItemType Directory -Force -Path $runsRoot, $logDir | Out-Null
Copy-Item -LiteralPath $R.path -Destination (Join-Path $OutDir 'matrix.json')
($planLines + @('', '--- preflight ---') + $pre) | Set-Content -LiteralPath (Join-Path $OutDir 'plan.txt') -Encoding utf8
$resultsCsv = Join-Path $OutDir 'results.csv'
$rows = New-Object System.Collections.Generic.List[object]
$matrixStart = Get-Date
foreach ($k in @('LEGO_SAMPLE_PROFILE', 'LEGO_SAMPLE_PROFILE_TRIGGER', 'LEGO_NATIVE_FRAME_METRICS')) { [Environment]::SetEnvironmentVariable($k, $null, 'Process') }
"out dir: $OutDir"

function Get-RunSplat($Ai, $Run) {
    $a = $Ai.arm
    $wf = if ($Run.cold) { 'firstframe' } else { $P.warmup_from }
    $s = @{ BinDir = $Ai.bin_abs; Tag = $Run.tag; RunsRoot = $runsRoot; WarmupFrom = $wf
            Warmup = [int](Get-Val $mx $a 'warmup_s'); Seconds = [int](Get-Val $mx $a 'measure_s')
            CloseTimeoutSec = [int](Get-Val $mx $a 'close_timeout_s'); BootTimeoutSec = [int](Get-Val $mx $a 'boot_timeout_s')
            Frames = [string](Get-P $a 'frames' 'perf') }
    if ($wf -eq 'firstframe') { $s.SettleSec = [int](Get-Val $mx $a 'settle_s') }
    if ($Run.cold) { $s.Warmup = [math]::Min($s.Warmup, [int](Get-Val $mx $a 'cold_warmup_s')); $s.Seconds = [math]::Min($s.Seconds, [int](Get-Val $mx $a 'cold_measure_s')) }
    # The floor goes to run-timing.ps1 (it raises the warm-up and records that in run.json), cold runs too.
    $floor = [double](Get-Val $mx $a 'min_window_after_ff_s'); if ($floor -gt 0) { $s.MinWindowAfterFirstFrame = $floor }
    if ([bool](Get-P $mx 'sys_csv' $false)) { $s.SysCsv = $true }
    $cv = @(@(Get-P $a 'cvars' @()) | ForEach-Object { [string]$_ }); if ($cv.Count) { $s.Cvar = $cv }
    $ev = Get-P $a 'env'; if ($null -ne $ev) { $l = @(@($ev.PSObject.Properties) | ForEach-Object { "$($_.Name)=$($_.Value)" }); if ($l.Count) { $s.Env = $l } }
    $tv = Get-P $a 'toml'; if ($null -ne $tv) { $l = @(@($tv.PSObject.Properties) | ForEach-Object { "$($_.Name)=$($_.Value)" }); if ($l.Count) { $s.Toml = $l } }
    $mn = [string](Get-P $a 'menu' ''); if ($mn) { $s.MenuText = $mn; $s.MenuSec = [int](Get-Val $mx $a 'menu_s') }
    if (-not $Run.cold) {
        if ($Ai.driver) { $s.Driver = $Ai.driver; if ($Ai.driver_args.Count) { $s.DriverArgs = $Ai.driver_args } }
        if ([bool](Get-P $a 'profile' $false)) { $s.Profile = $true; $s.ProfileSeconds = [int](Get-Val $mx $a 'profile_s') }
        $tr = @(@(Get-P $a 'triggers' @()) | ForEach-Object { [string]$_ }); if ($tr.Count) { $s.TriggerAtMeasure = $tr }
        if ([bool](Get-P $a 'seed_recipes_only' $false)) { $s.SeedRecipesOnly = $true }
    }
    return $s
}
function Save-Results {
    if ($rows.Count) { $rows | ForEach-Object { [pscustomobject]$_ } | Export-Csv -LiteralPath $resultsCsv -NoTypeInformation -Encoding UTF8 }
}
function Med([double[]]$V) {
    $s = @($V | Sort-Object); $c = $s.Count
    if ($c -eq 0) { return $null }
    if ($c % 2) { return $s[[int](($c - 1) / 2)] }
    return ($s[[int]($c / 2) - 1] + $s[[int]($c / 2)]) / 2
}
function Write-Summary {
    $S = New-Object System.Collections.Generic.List[string]
    $end = Get-Date
    $scored = @($rows | Where-Object { $_.scored -eq 'True' })
    $flaggedRows = @($scored | Where-Object { $_.excluded -eq 'True' })
    $okRows = @($scored | Where-Object { $_.status -eq 'OK' -and $_.median_ms -ne '' -and $_.excluded -ne 'True' })
    $invalid = @($rows | Where-Object { $_.valid_timing -ne 'True' })
    $S.Add("# Timing matrix: $($R.title)")
    $S.Add('')
    $S.Add("- matrix: $($R.path) (copy in matrix.json); out: $OutDir")
    $S.Add("- started $($matrixStart.ToString('yyyy-MM-dd HH:mm')), ended $($end.ToString('HH:mm')); $($rows.Count) runs ($(@($rows | Where-Object { $_.status -eq 'OK' }).Count) OK), $($scored.Count) scored; desktop $desk$(if ($Quick) { '; -Quick' })")
    $S.Add('- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm''s run-to-run spread (max-min)/median of its run medians')
    $S.Add("- flagged: $($flaggedRows.Count) of $($scored.Count) scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs")
    if ($Quick -or $invalid.Count) {
        $S.Add('')
        $S.Add("> **FUNCTIONAL ONLY**: $(if ($Quick) { '-Quick run; ' })$($invalid.Count) of $($rows.Count) runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.")
    }
    $topRef = [string](Get-P $mx 'reference' '')
    $groups = [ordered]@{}
    foreach ($ai in $P.arms.Values) { $g = if ($ai.group) { $ai.group } else { '' }; if (-not $groups.Contains($g)) { $groups[$g] = New-Object System.Collections.Generic.List[string] }; $groups[$g].Add($ai.id) }
    $table = New-Object System.Collections.Generic.List[object]
    $stats = @{}
    foreach ($ai in $P.arms.Values) {
        $rr = @($okRows | Where-Object { $_.arm -eq $ai.id })
        $all = @($scored | Where-Object { $_.arm -eq $ai.id })
        $st = @{ n = $rr.Count; total = $all.Count; valid = @($rr | Where-Object { $_.valid_timing -eq 'True' }).Count; flagged = @($all | Where-Object { $_.excluded -eq 'True' }).Count
                 med = $null; min = $null; max = $null; spread = $null
                 p99 = $null; p999 = $null; o33 = $null; o100 = $null; fps = $null; cpu = $null }
        if ($rr.Count) {
            $meds = @($rr | ForEach-Object { [double]::Parse($_.median_ms, $inv) })
            $st.med = Med $meds; $st.min = ($meds | Measure-Object -Minimum).Minimum; $st.max = ($meds | Measure-Object -Maximum).Maximum
            if ($st.med -gt 0) { $st.spread = ($st.max - $st.min) / $st.med * 100 }
            $st.p99 = Med @($rr | ForEach-Object { [double]::Parse($_.p99_ms, $inv) })
            $st.p999 = Med @($rr | ForEach-Object { [double]::Parse($_.p999_ms, $inv) })
            $mins = 0.0; $c33 = 0.0; $c100 = 0.0
            foreach ($x in $rr) { $mins += [double]::Parse($x.window_s, $inv) / 60; $c33 += [double]::Parse($x.over33, $inv); $c100 += [double]::Parse($x.over100, $inv) }
            if ($mins -gt 0) { $st.o33 = $c33 / $mins; $st.o100 = $c100 / $mins }
            $st.fps = Med @($rr | ForEach-Object { [double]::Parse($_.fps_mean, $inv) })
            $cp = @($rr | Where-Object { $_.cpu_cores_mean -ne '' } | ForEach-Object { [double]::Parse($_.cpu_cores_mean, $inv) })
            if ($cp.Count) { $st.cpu = ($cp | Measure-Object -Average).Average }
        }
        $stats[$ai.id] = $st
    }
    foreach ($g in $groups.Keys) {
        $members = $groups[$g]
        $ref = $null
        foreach ($id in $members) { if ([bool](Get-P $P.arms[$id].arm 'ref' $false)) { $ref = $id } }
        $why = 'ref arm of the group'
        if (-not $ref -and $topRef -and $P.arms.Contains($topRef)) { $ref = $topRef; $why = 'top-level reference' }
        if (-not $ref) { $ref = $members[0]; $why = 'first arm (no ref set)' }
        $rs = $stats[$ref]
        $band = $rs.spread
        $S.Add('')
        $S.Add("## Group $(if ($g) { $g } else { '(none)' }): ref $ref ($why)$(if ($null -ne $band -and $rs.n -ge 2) { ', noise band +-' + (N $band 1) + ' %' } else { ', no noise band (ref has < 2 OK runs)' })")
        $S.Add('')
        $S.Add('| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |')
        $S.Add('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
        $order = @($ref) + @($members | Where-Object { $_ -ne $ref })
        foreach ($id in $order) {
            if (-not $stats.ContainsKey($id)) { continue }
            $st = $stats[$id]
            $dm = $null; $dp = $null; $d33 = $null; $verdict = ''
            if ($id -eq $ref) { $verdict = 'ref' }
            elseif ($null -ne $st.med -and $null -ne $rs.med -and $rs.med -gt 0) {
                $dm = ($st.med - $rs.med) / $rs.med * 100
                if ($rs.p99 -gt 0) { $dp = ($st.p99 - $rs.p99) / $rs.p99 * 100 }
                if ($null -ne $rs.o33 -and $rs.o33 -gt 0) { $d33 = ($st.o33 - $rs.o33) / $rs.o33 * 100 }
                if ($null -eq $band -or $rs.n -lt 2) { $verdict = 'no noise band' }
                elseif ([math]::Abs($dm) -le $band) { $verdict = 'within noise' }
                elseif ($dm -lt 0) { $verdict = 'FASTER (outside noise)' } else { $verdict = 'SLOWER (outside noise)' }
            } elseif ($null -eq $st.med) { $verdict = 'no OK runs' } else { $verdict = 'ref has no OK runs' }
            $skip = $P.arms[$id].skip
            if ($skip) { $verdict = "SKIPPED: $skip" }
            $S.Add("| $id | $($st.n)/$($st.total) | $($st.valid) | $($st.flagged) | $(N $st.med 2) ($(N $st.min 2)..$(N $st.max 2)) | $(N $st.spread 1) | $(N $st.p99 2) | $(N $st.p999 2) | $(N $st.o33 1) | $(N $st.o100 2) | $(N $st.fps 2) | $(N $st.cpu 2) | $(N $dm 1) | $(N $dp 1) | $(N $d33 1) | $verdict |")
            $table.Add([pscustomobject][ordered]@{ group = $g; arm = $id; ok = "$($st.n)/$($st.total)"; valid = $st.valid; flagged = $st.flagged; median = (N $st.med 2); min = (N $st.min 2); max = (N $st.max 2)
                                                   spread = (N $st.spread 1); p99 = (N $st.p99 2); o33pm = (N $st.o33 1); o100pm = (N $st.o100 2); cpu = (N $st.cpu 2)
                                                   d_med = (N $dm 1); d_p99 = (N $dp 1); verdict = $verdict })
        }
    }
    $S.Add('')
    $S.Add('## Runs')
    $S.Add('')
    $S.Add('| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |')
    $S.Add('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    foreach ($x in $rows) {
        $fl = (@(@($x.flags_excluding, $x.flags_info) | Where-Object { $_ }) -join ' ')
        $S.Add("| $($x.seq) | $(if ($x.scored -eq 'True') { $x.round } elseif ($x.kind -eq 'warm') { 'warm' } else { 'cold' }) | $($x.arm) | $($x.rep) | $($x.status) | $($x.valid_timing) | $(if ($x.excluded -eq 'True') { 'EXCL' }) | $($x.boot_s) | $($x.ff_to_window_s) | $($x.frames) | $($x.median_ms) | $($x.p99_ms) | $($x.over33) | $($x.over100) | $($x.cpu_cores_mean) | $($x.light_share) | $($x.close) | $fl | $(if ($x.run_dir) { Split-Path -Leaf $x.run_dir }) | $(($x.notes -replace '\|', '/')) |")
    }
    $flagRows = @($rows | Where-Object { $_.flags_excluding -or $_.flags_info })
    if ($flagRows.Count) {
        $S.Add('')
        $S.Add('## Flagged runs')
        $S.Add('')
        $S.Add('Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.')
        $S.Add('')
        $S.Add('| # | arm | rep | excluding flags | info flags | run dir |')
        $S.Add('|---|---|---|---|---|---|')
        foreach ($x in $flagRows) { $S.Add("| $($x.seq) | $($x.arm) | $(if ($x.scored -eq 'True') { $x.rep } elseif ($x.kind -eq 'warm') { 'warm' } else { 'cold' }) | $($x.flags_excluding) | $($x.flags_info) | $(if ($x.run_dir) { Split-Path -Leaf $x.run_dir }) |") }
    }
    if ($P.skips.Count) { $S.Add(''); $S.Add('## Skipped arms'); $S.Add(''); foreach ($skipLine in $P.skips) { $S.Add("- $skipLine") } }
    $S | Set-Content -LiteralPath (Join-Path $OutDir 'summary.md') -Encoding utf8
    Write-Host ''
    Write-Host "=== matrix summary ($OutDir) ===" -ForegroundColor Cyan
    if ($Quick -or $invalid.Count) { Write-Host "FUNCTIONAL ONLY: $($invalid.Count) of $($rows.Count) runs not valid timing$(if ($Quick) { ' (-Quick)' })" -ForegroundColor Yellow }
    if ($flaggedRows.Count) { Write-Host "FLAGGED: $($flaggedRows.Count) of $($scored.Count) scored runs excluded from the numbers (summary.md, Flagged runs)" -ForegroundColor Yellow }
    if ($table.Count) { Write-Host ($table | Format-Table -AutoSize | Out-String -Width 250) }
    Write-Host "results: $resultsCsv"
    Write-Host "summary: $(Join-Path $OutDir 'summary.md')"
}

# Keep the PC awake and the display on for the whole matrix (quiet window 1 died on a lock): ES_CONTINUOUS |
# ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED on this thread, cleared in the finally below (Windows also clears it when
# this process exits). The second call returns the state the first one set, which proves it took.
$awake = 'not requested'
try {
    Add-Type -Namespace LdPower -Name Exec -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
    [void][LdPower.Exec]::SetThreadExecutionState([uint32]2147483651)
    $esNow = [LdPower.Exec]::SetThreadExecutionState([uint32]2147483651)
    $awake = if ($esNow -eq [uint32]2147483651) { 'ON (SetThreadExecutionState continuous+system+display until the matrix ends)' } else { "FAILED (state 0x$('{0:X8}' -f $esNow))" }
} catch { $awake = "FAILED ($($_.Exception.Message))" }
Write-Host "keep-awake $awake" -ForegroundColor $(if ($awake -like 'ON*') { 'Gray' } else { 'Yellow' })
try { Add-Content -LiteralPath (Join-Path $OutDir 'plan.txt') -Value "keep-awake $awake" -Encoding utf8 } catch { }
$i = 0
$interrupted = $true
try {
    foreach ($run in $P.runs) {
        $i++
        $ai = $P.arms[$run.id]
        $left = 0.0; foreach ($r2 in $P.runs) { if ($r2.seq -ge $run.seq) { $left += $r2.est_s } }
        Write-Host ''
        Write-Host ("=== [{0}/{1}] {2}: arm {3}{4} rep {5} | matrix done around {6} ===" -f $i, $P.runs.Count, $(if ($run.cold) { 'COLD run (unscored)' } elseif ($run.warm) { 'WARM-UP run (unscored)' } else { "round $($run.round)" }),
                    $run.id, $(if ($ai.group) { " (group $($ai.group))" } else { '' }), $run.rep, (Get-Date).AddSeconds($left).ToString('HH:mm')) -ForegroundColor Cyan
        $note = [string](Get-P $ai.arm 'note' ''); if ($note) { Write-Host "    $note" }
        $row = [ordered]@{ seq = $run.seq; round = $run.round; arm = $run.id; group = $ai.group; rep = $run.rep; scored = [string](-not ($run.cold -or $run.warm)); status = ''
                           valid_timing = ''; boot_s = ''; frames = ''; window_s = ''; median_ms = ''; p99_ms = ''; p999_ms = ''; max_ms = ''; over33 = ''; over100 = ''
                           fps_mean = ''; cpu_cores_mean = ''; peak_ws_mb = ''; close = ''; exit_code = ''; frames_source = ''; seed_from = ''; runner_exit = ''
                           excluded = ''; flags_excluding = ''; flags_info = ''; ff_to_window_s = ''; light_share = ''; install_dat_fail = ''; light_phase = ''
                           idle_min_s = ''; fg_share = ''; eff_mhz = ''
                           run_dir = ''; log = ''; notes = ''
                           kind = $(if ($run.cold) { 'cold' } elseif ($run.warm) { 'warm' } else { 'scored' }); over8 = ''; over10 = ''; over16_7 = ''; frames_lt_light = '' }
        $splat = Get-RunSplat $ai $run
        $skipWhy = $null
        if (-not $run.cold) {
            if ($ai.seed_arm -and $run.warm) {
                # A warm-up run never waits for a seed source arm (none has run yet); it runs unseeded.
            } elseif ($ai.seed_arm) {
                $src = @($rows | Where-Object { $_.arm -eq $ai.seed_arm -and @('OK', 'PROFILE') -contains $_.status -and $_.run_dir } | Select-Object -Last 1)
                if ($src.Count) { $splat.SeedCache = $src[0].run_dir; $row.seed_from = $src[0].run_dir }
                else { $skipWhy = "seed source arm $($ai.seed_arm) has no completed run in this matrix" }
            } elseif ($ai.seed_path) { $splat.SeedCache = $ai.seed_path; $row.seed_from = $ai.seed_path }
        }
        if (-not $skipWhy -and -not $AllowRunningGame) {
            $w = 0
            while (@(Get-Process -Name legodimensions -ErrorAction SilentlyContinue).Count -and $w -lt 90) { if ($w -eq 0) { Write-Host 'waiting for a running legodimensions.exe to exit (up to 90 s)' -ForegroundColor Yellow }; Start-Sleep -Seconds 1; $w++ }
            if (@(Get-Process -Name legodimensions -ErrorAction SilentlyContinue).Count) { $skipWhy = 'another legodimensions.exe is still running' }
        }
        if ($skipWhy) {
            Write-Host "!!! SKIPPED: $skipWhy" -ForegroundColor Red
            $row.status = 'SKIPPED'; $row.notes = $skipWhy; $rows.Add($row); Save-Results
            continue
        }
        $log = Join-Path $logDir ('{0:D2}-{1}.txt' -f $run.seq, $run.tag)
        $row.log = $log
        $before = @{}; foreach ($dirItem in @(Get-ChildItem -LiteralPath $runsRoot -Directory -ErrorAction SilentlyContinue)) { $before[$dirItem.Name] = 1 }
        $snap = Get-EnvSnap
        $code = $null; $err = $null
        $global:LASTEXITCODE = 0
        try {
            & $runner @splat | Tee-Object -FilePath $log | Out-Host
            $code = $global:LASTEXITCODE
        } catch {
            $err = "$($_.Exception.Message)"
            Write-Host "!!! run-timing.ps1 failed: $err" -ForegroundColor Red
        } finally { Restore-Env $snap }
        $new = @(Get-ChildItem -LiteralPath $runsRoot -Directory -ErrorAction SilentlyContinue | Where-Object { -not $before.ContainsKey($_.Name) } | Sort-Object CreationTime)
        $rd = if ($new.Count) { $new[$new.Count - 1].FullName } else { $null }
        $row.runner_exit = [string]$code
        $rj = $null
        if ($rd) { $row.run_dir = $rd; $jp = Join-Path $rd 'run.json'; if (Test-Path -LiteralPath $jp) { try { $rj = [IO.File]::ReadAllText($jp) | ConvertFrom-Json } catch { $err = "run.json unreadable: $($_.Exception.Message)" } } }
        if ($rj) {
            $fr = Get-P $rj 'frames'
            $row.status = [string](Get-P $rj 'status' '?')
            $row.valid_timing = [string][bool](Get-P $rj 'valid_timing' $false)
            $row.boot_s = N (Get-P $rj 'boot_s') 2
            $row.frames = N (Get-P $fr 'frames') 0; $row.window_s = N (Get-P $fr 'window_s') 3
            $row.median_ms = N (Get-P $fr 'median_ms') 4; $row.p99_ms = N (Get-P $fr 'p99_ms') 4; $row.p999_ms = N (Get-P $fr 'p99_9_ms') 4; $row.max_ms = N (Get-P $fr 'max_ms') 4
            $row.over33 = N (Get-P $fr 'over_33ms') 0; $row.over100 = N (Get-P $fr 'over_100ms') 0; $row.fps_mean = N (Get-P $fr 'mean_fps') 3
            $row.frames_source = [string](Get-P $fr 'source' '')
            $row.cpu_cores_mean = N (Get-P $rj 'window_cpu_cores_mean') 3; $row.peak_ws_mb = N (Get-P $rj 'window_peak_ws_mb') 0
            $row.exit_code = [string](Get-P $rj 'exit_code_hex' '')
            # Window-4 flags (run-timing.ps1 header): excluded runs stay in results.csv but leave the summary numbers.
            $lt = Get-P $rj 'light'
            $row.light_share = N (Get-P $lt 'share_lt_light') 15
            $fsK = Get-P $fr 'frames_lt_light'
            if ($null -ne $fsK) { $row.frames_lt_light = N $fsK 0 }
            $row.over8 = N (Get-P $fr 'over_8ms') 0; $row.over10 = N (Get-P $fr 'over_10ms') 0; $row.over16_7 = N (Get-P $fr 'over_16_7ms') 0
            $row.install_dat_fail = N (Get-P $lt 'install_dat_fail') 0
            $row.light_phase = N (Get-P $lt 'light_phase')
            $row.ff_to_window_s = N (Get-P $rj 'ff_to_window_s') 1
            $sw = Get-P (Get-P $rj 'sys') 'window'
            $row.idle_min_s = N (Get-P $sw 'idle_min_s') 1; $row.fg_share = N (Get-P $sw 'fg_game_share') 3; $row.eff_mhz = N (Get-P $sw 'eff_mhz_mean') 0
            $fx = @(@(Get-P $rj 'flags_excluding' @()) | ForEach-Object { [string]$_ })
            $fi = @(@(Get-P $rj 'flags_info' @()) | ForEach-Object { [string]$_ })
            $row.flags_excluding = $fx -join ' '; $row.flags_info = $fi -join ' '
            $row.excluded = [string]([bool](Get-P $rj 'excluded' $false) -or $fx.Count -gt 0)
            $cl = Get-P $rj 'close'
            $row.close = if ([bool](Get-P $rj 'exited_early' $false)) { "exited early ($([string](Get-P $rj 'exited_phase' '')))" }
                         elseif ($null -eq $cl) { 'no close' }
                         elseif ([bool](Get-P $cl 'killed' $false)) { 'KILLED' }
                         elseif (-not [bool](Get-P $cl 'exited' $true)) { 'STILL RUNNING' }
                         else { "wm_close $(N (Get-P $cl 'exit_seen_s') 1) s" }
            $nb = @(@(Get-P $rj 'problems' @()) | ForEach-Object { [string]$_ })
            $vw = @(@(Get-P $rj 'valid_timing_why' @()) | ForEach-Object { [string]$_ })
            if ($vw.Count) { $nb += "not timing: $($vw -join ', ')" }
            if ($fx.Count) { $nb += "EXCLUDED: $($fx -join ', ')" }
            if ($err) { $nb += $err }
            $row.notes = ($nb -join ' | ')
        } elseif ($rd) {
            $row.status = 'ERROR'; $row.notes = "no run.json$(if ($err) { ": $err" })"
        } else {
            $tail = @(); if (Test-Path -LiteralPath $log) { $tail = @(Get-Content -LiteralPath $log | Where-Object { $_ -match '!!!|not start' } | Select-Object -Last 2) }
            $row.status = 'NOT STARTED'; $row.notes = (@($tail) + @($(if ($err) { $err })) | Where-Object { $_ }) -join ' | '
        }
        $rows.Add($row); Save-Results
        $color = if ($row.status -eq 'OK') { 'Green' } else { 'Red' }
        Write-Host ("--> {0} {1}: {2}  median {3} ms  p99 {4} ms  >33 {5}  >100 {6}  cpu {7}  {8}" -f $run.tag, $(if ($run.cold) { '(cold)' } elseif ($run.warm) { '(warm-up)' } else { '' }), $row.status, $row.median_ms,
                    $row.p99_ms, $row.over33, $row.over100, $row.cpu_cores_mean, $row.close) -ForegroundColor $color
        if ($row.notes) { Write-Host "    $($row.notes)" -ForegroundColor $(if ($row.status -eq 'OK') { 'Gray' } else { 'Yellow' }) }
        if ($row.excluded -eq 'True') { Write-Host "    EXCLUDED from the summary numbers (flags: $($row.flags_excluding))" -ForegroundColor Yellow }
        if ($row.flags_info -or $row.ff_to_window_s -ne '') { Write-Host "    first frame to window $(if ($row.ff_to_window_s -ne '') { $row.ff_to_window_s + ' s' } else { '-' }); light share $(if ($row.light_share -ne '') { $row.light_share } else { '-' }); info flags: $(if ($row.flags_info) { $row.flags_info } else { 'none' })" -ForegroundColor Gray }
        if ($i -lt $P.runs.Count) {
            $cool = [int](Get-Val $mx $ai.arm 'cooldown_s')
            if ($cool -gt 0) { Write-Host "cooldown $cool s"; Start-Sleep -Seconds $cool }
        }
    }
    $interrupted = $false
} finally {
    if ($interrupted) { Write-Host '!!! matrix interrupted: writing what we have' -ForegroundColor Red }
    try { if ($awake -like 'ON*') { [void][LdPower.Exec]::SetThreadExecutionState([uint32]2147483648); Write-Host 'keep-awake released' } } catch { }
    Save-Results
    try { Write-Summary } catch { Write-Host "!!! summary failed: $($_.Exception.Message) (line $($_.InvocationInfo.ScriptLineNumber))" -ForegroundColor Red }
}
$bad = @($rows | Where-Object { @('OK', 'PROFILE') -notcontains $_.status })
if ($bad.Count) { "$($bad.Count) of $($rows.Count) runs not OK"; exit 1 }
exit 0

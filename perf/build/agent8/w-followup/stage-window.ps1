# Agent 8, run-2 task #7 item 6: stage a window for Agent 5's overnight launcher (bench\agent5\launch\run-night.ps1)
# and print its GO line. Usage (from the repo root):
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent8\w-followup\stage-window.ps1 `
#       -Draft build\agent8\w-followup\matrix-window9.json -Id W9 -Only off,q0,q125,q250,q500 -Repeats 3 `
#       -Expect devoff4b=DE11A914079D7DF7 [-VerifyFiles]
#     TEST (default): copies the draft to build\agent8\w-followup\test\<Id>\ and checks the copy there; no bench writes.
#     -Promote: the draft must be build\agent8\w-followup\matrix-window*.json; copies it byte for byte to
#       bench\agent8\run\<name> (a different file there is replaced only with -Force). -Expect must cover every bin.
#     -Recheck: the matrix is already in bench\agent8\run (e.g. W6 with another repeats=): no copy, the same checks.
# Checks, in order: the draft (no BOM, valid JSON, no DRAFT text, sys_csv, cold_run, the 60 s floor, the reference in
#   only=); every arm (my copy of the launcher's rules, stricter: id, bin, env keys and string values, frames, cvars,
#   driver, no menu/profile/triggers/toml/seed_cache field); the bins (MANIFEST.txt sha256 starts with -Expect, no FAIL
#   check line, legodimensions.exe = its MANIFEST.txt line; -VerifyFiles: every listed file); then the launcher's own
#   functions, loaded read-only from run-night.ps1 with the PowerShell parser: Parse-Go on the GO line, Test-Matrix with
#   the copy's folder as the matrix folder, Get-MatrixWarnings, Get-BinHashes, Get-Plan (run-matrix.ps1 -PlanOnly: reads
#   only, starts no game); then the planned runs (1 cold + arms x repeats), the matrix folder count before and after, and
#   the latest start that still ends by 07:30 under the launcher's rule (now + plan + slack <= 07:30, no start >= 06:45).
# A launcher function is loaded only if every command, method and variable it uses is on the read-only lists below;
#   otherwise the result is NOT OK (-ReplicaOnly: my own copies of Parse-Go and Get-Plan, recorded in the report).
# Reports: build\agent8\readout\w-followup\stage-<Id>-<HHmmss>[-NOTOK].txt and inputs-<Id>-<HHmmss>.txt.
# It never writes perf-notes\WINDOW-GO.txt (Agent 1 does), never adds .py or .cs files, stops if WINDOW-HOLD.txt
# exists, and starts -PlanOnly only in a safe gap of Agent 3's S4b queue (Wait-QueueGap, as in promote-w6.ps1).
# Exit: 0 OK, 1 NOT OK, 2 usage, 4 HOLD.
param(
    [string]$Draft = '',
    [string]$Id = '',
    [string]$Only = '',
    [int]$Repeats = 0,
    [string]$Expect = '',
    [switch]$Promote,
    [switch]$Recheck,
    [switch]$VerifyFiles,
    [switch]$ReplicaOnly,
    [switch]$Force,
    [int]$QueueGapS = 20
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
if ($args.Count) { Write-Host "refused: unknown argument(s) '$($args -join ' ')'" -ForegroundColor Red; exit 2 }
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
function Stop-IfHold { if (Test-Path -LiteralPath (Join-Path $Repo 'perf-notes\WINDOW-HOLD.txt')) { Write-Host 'perf-notes\WINDOW-HOLD.txt exists: a timed window is running. Nothing more done.' -ForegroundColor Red; exit 4 } }
Stop-IfHold
(Get-Process -Id $PID).PriorityClass = 'BelowNormal'
function Sha([string]$P) { return (Get-FileHash -LiteralPath $P -Algorithm SHA256).Hash }
function Rel([string]$P) { if ($P.StartsWith($Repo + '\', [StringComparison]::OrdinalIgnoreCase)) { return $P.Substring($Repo.Length + 1) }; return $P }
function Usage([string]$Msg) { Write-Host "refused: $Msg" -ForegroundColor Red; exit 2 }
function P($O, [string]$N) { if ($null -ne $O -and $O -is [System.Management.Automation.PSCustomObject]) { $pp = $O.PSObject.Properties[$N]; if ($null -ne $pp) { return $pp.Value } }; return $null }

# Agent 3's S4b queue: harness\guard.ps1 counts every run-matrix.ps1 process (-PlanOnly too) as a runner, so a -PlanOnly
# that starts just as the queue launches makes that launch fail (20:57). -PlanOnly therefore starts only while a queue
# game runs, at least -QueueGapS after its LAUNCH (and 30 s before its -Seconds end), or when the queue is idle.
function Get-QueueState([string]$Q) {
    $tail = @(Get-Content -LiteralPath $Q -Tail 60)
    $now = Get-Date
    $s = @{ Now = $now; LastT = $null; Last = ''; LaunchT = $null; LaunchSec = 0; DoneAfter = $false }
    for ($i = $tail.Count - 1; $i -ge 0; $i--) {
        if ($tail[$i] -notmatch '^(\d\d):(\d\d):(\d\d) (\S+)') { continue }
        $t = $now.Date.AddHours([int]$Matches[1]).AddMinutes([int]$Matches[2]).AddSeconds([int]$Matches[3])
        if ($t -gt $now.AddMinutes(5)) { $t = $t.AddDays(-1) }
        $kind = $Matches[4]
        if ($null -eq $s.LastT) { $s.LastT = $t; $s.Last = $tail[$i] }
        # Lines a running game writes (its toypad sidecar, attach) keep it running; LAUNCH ends the scan; any other
        # line after the last LAUNCH (DONE, REFUSED, 'a timing/boot runner is active ... waiting', HOLD, idle) means
        # no queue game is running now, and the queue may launch at any moment.
        if ($kind -eq 'toypad' -or $kind -eq 'attach') { continue }
        elseif ($kind -eq 'LAUNCH') { $s.LaunchT = $t; if ($tail[$i] -match ' -Seconds (\d+)') { $s.LaunchSec = [int]$Matches[1] }; break }
        else { $s.DoneAfter = $true }
    }
    return $s
}
function Wait-QueueGap([int]$GapS, [int]$IdleS, [int]$MaxS) {
    $q = Join-Path $Repo 'build\agent3\s4b\logs\queue.out.txt'
    if (-not (Test-Path -LiteralPath $q)) { return 'no queue log, no wait' }
    $t0 = Get-Date
    while ($true) {
        Stop-IfHold
        $s = Get-QueueState $q
        $waited = [int](($s.Now - $t0).TotalSeconds)
        if ($null -ne $s.LaunchT -and -not $s.DoneAfter) {
            $el = ($s.Now - $s.LaunchT).TotalSeconds
            if ($el -ge $GapS -and ($s.LaunchSec -eq 0 -or $el -le $s.LaunchSec - 30)) { return ('a queue game runs (LAUNCH {0:HH:mm:ss}, {1:N0} s ago); -PlanOnly at {2:HH:mm:ss} after {3} s of waiting' -f $s.LaunchT, $el, $s.Now, $waited) }
        } elseif ($null -ne $s.LastT -and ($s.Now - $s.LastT).TotalSeconds -ge $IdleS) { return ('the queue is idle (last line {0:HH:mm:ss}: {1}); -PlanOnly at {2:HH:mm:ss} after {3} s of waiting' -f $s.LastT, $s.Last, $s.Now, $waited) }
        if ($waited -ge $MaxS) { return ('no safe gap in {0} s; -PlanOnly anyway at {1:HH:mm:ss}' -f $MaxS, $s.Now) }
        Start-Sleep -Seconds 5
    }
}

# ---------- usage ----------
$idRx = '[A-Za-z0-9][A-Za-z0-9_.-]{0,31}'
if (-not $Draft) { Usage '-Draft <matrix json> is required' }
if ($Id -cnotmatch "^$idRx$") { Usage "-Id '$Id' must be 1-32 of A-Z a-z 0-9 _ . - (the GO window id)" }
if ($Only -cnotmatch "^$idRx(,$idRx)*$") { Usage "-Only '$Only' must be arm[,arm...]" }
$onlyList = @($Only -split ',')
if (@($onlyList | Select-Object -Unique).Count -ne $onlyList.Count) { Usage '-Only lists an arm twice' }
if ($Repeats -lt 1 -or $Repeats -gt 20) { Usage '-Repeats must be 1-20 (the launcher takes repeats=1-20)' }
if ($Promote -and $Recheck) { Usage '-Promote and -Recheck exclude each other' }
$expectMap = @{}
foreach ($e in @($Expect -split ',' | Where-Object { $_ })) {
    if ($e -notmatch '^([A-Za-z0-9][A-Za-z0-9_.-]*)=([0-9A-Fa-f]{8,64})$') { Usage "-Expect item '$e' must be <bin name>=<8-64 hex digits of its MANIFEST.txt sha256>" }
    $expectMap[$Matches[1]] = $Matches[2].ToUpperInvariant()
}
$draftPath = (Resolve-Path -LiteralPath $(if ([IO.Path]::IsPathRooted($Draft)) { $Draft } else { Join-Path $Repo $Draft })).Path
$name = Split-Path -Leaf $draftPath
$draftDir = (Split-Path -Parent $draftPath).TrimEnd('\')
$wfDir = Join-Path $Repo 'build\agent8\w-followup'
$RunDir = Join-Path $Repo 'bench\agent8\run'
if ($name -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\.json$' -or $name -match '\.\.') { Usage "matrix name '$name' is not a plain .json name a GO line can carry" }
if ($Promote -and (-not [string]::Equals($draftDir, $wfDir, [StringComparison]::OrdinalIgnoreCase) -or $name -notlike 'matrix-window*.json')) { Usage "-Promote takes only build\agent8\w-followup\matrix-window*.json, not $(Rel $draftPath)" }
if ($Recheck -and -not [string]::Equals($draftDir, $RunDir, [StringComparison]::OrdinalIgnoreCase)) { Usage "-Recheck takes only a matrix already in bench\agent8\run, not $(Rel $draftPath)" }
$modeName = if ($Promote) { 'PROMOTE' } elseif ($Recheck) { 'RECHECK' } else { 'TEST' }
$stamp = Get-Date -Format 'HHmmss'
$when = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$fail = New-Object System.Collections.Generic.List[string]
$notes = New-Object System.Collections.Generic.List[string]

# ---------- 1. the launcher: its lists and its read-only functions ----------
$LauncherPath = Join-Path $Repo 'bench\agent5\launch\run-night.ps1'
$LauncherDir = Split-Path -Parent $LauncherPath
$launcherSha = Sha $LauncherPath
$launcherTime = (Get-Item -LiteralPath $LauncherPath).LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
$F1Env = @('REX_TIMER_WAIT_BLOCKING', 'LEGO_GPU_WAIT_STATS', 'LEGO_GPU_WAIT_BACKOFF_US', 'LEGO_GPU_WAIT_SPIN_US', 'LEGO_NATIVE_FRAME_METRICS', 'LEGO_NATIVE_SHADER_MISS_CACHE',
           'LEGO_NATIVE_THREADED', 'LEGO_NATIVE_PREPARE_THREADS', 'LEGO_NATIVE_SNAPSHOT_STATE', 'LEGO_NATIVE_FULL_DRAW_PREPARATION', 'LEGO_NATIVE_CHAIN_PRIORITY')
$F1Drivers = @('thread-cpu.ps1', 'pso-stats-at-end.ps1', 'io-counters.ps1')
$tok = $null; $perr = $null
$last = [System.Management.Automation.Language.Parser]::ParseFile($LauncherPath, [ref]$tok, [ref]$perr)
$A = 'System.Management.Automation.Language.'
function Get-TopAssign([string]$Var) {
    $hits = @($last.EndBlock.Statements | Where-Object { $_ -is [System.Management.Automation.Language.AssignmentStatementAst] -and $_.Left -is [System.Management.Automation.Language.VariableExpressionAst] -and $_.Left.VariablePath.UserPath -eq $Var })
    if ($hits.Count -ne 1) { return $null }
    return $hits[0]
}
function Get-StringList([string]$Var) {
    $as = Get-TopAssign $Var
    if ($null -eq $as) { return $null }
    $v = @($as.Right.FindAll({ param($n) $n -is [System.Management.Automation.Language.StringConstantExpressionAst] }, $true) | ForEach-Object { $_.Value })
    if (-not $v.Count) { return $null }
    return , $v
}
function Get-Number([string]$Var, [double]$Default) {
    $as = Get-TopAssign $Var
    if ($null -ne $as -and $as.Right -is [System.Management.Automation.Language.CommandExpressionAst] -and $as.Right.Expression -is [System.Management.Automation.Language.ConstantExpressionAst]) { return [double]$as.Right.Expression.Value }
    $notes.Add("run-night.ps1 has no plain number for `$$Var; $Default used"); return $Default
}
$AllowedEnv = Get-StringList 'AllowedEnv'
if ($null -eq $AllowedEnv) { $AllowedEnv = $F1Env; $notes.Add('run-night.ps1: no $AllowedEnv list found; the F1 list (11 keys) used') }
elseif ((@($AllowedEnv) -join ',') -cne ($F1Env -join ',')) { $notes.Add("run-night.ps1 `$AllowedEnv is not the F1 list: $($AllowedEnv -join ', ')") }
$AllowedDrivers = Get-StringList 'AllowedDrivers'
if ($null -eq $AllowedDrivers) { $AllowedDrivers = $F1Drivers; $notes.Add('run-night.ps1: no $AllowedDrivers list found; thread-cpu, pso-stats-at-end and io-counters used') }
$DeadlineSlackMin = Get-Number 'DeadlineSlackMin' 10
$LatestStartTime = Get-Number 'LatestStartTime' 6.75
$RunMatrix = Join-Path $RunDir 'run-matrix.ps1'
$PsExe = Join-Path $PSHOME 'powershell.exe'
$MatrixDirEff = $RunDir

$want = @('Get-PinFiles', 'Test-Pinned', 'Parse-Go', 'Get-P', 'Resolve-Driver', 'Test-Matrix', 'Get-RunnerArgs', 'Get-BinHashes', 'Get-MatrixWarnings', 'Get-Plan')
$okCmds = @('New-Object', 'Join-Path', 'Get-ChildItem', 'Where-Object', 'Test-Path', 'Sort-Object', 'Select-Object', 'Resolve-Path', 'Split-Path', 'Get-FileHash', 'ConvertFrom-Json', 'ConvertTo-Json', 'ForEach-Object') + $want
$given = @('Repo', 'RunDir', 'RunMatrix', 'PsExe', 'MatrixDirEff', 'AllowedEnv', 'AllowedDrivers', 'PSCommandPath', 'PSScriptRoot')
$auto = @('_', 'true', 'false', 'null', 'Matches', 'LASTEXITCODE', 'ErrorActionPreference', 'PSHOME')
$denyMember = '^(Write|Append|Delete|Move|Copy|Create|Kill|Start|Replace|Encrypt|Decrypt|Set|Open|Invoke|Remove|Clear)'
$loadWhy = New-Object System.Collections.Generic.List[string]
$defs = @{}
if ($perr.Count) { $loadWhy.Add("run-night.ps1 has $($perr.Count) parse error(s), the first: $($perr[0].Message) (line $($perr[0].Extent.StartLineNumber))") }
foreach ($st in $last.EndBlock.Statements) {
    if ($st -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $want -ccontains $st.Name) { if ($defs.ContainsKey($st.Name)) { $loadWhy.Add("run-night.ps1 defines $($st.Name) twice") }; $defs[$st.Name] = $st }
}
$fnText = New-Object System.Collections.Generic.List[string]
foreach ($w in $want) {
    if (-not $defs.ContainsKey($w)) { $loadWhy.Add("run-night.ps1 has no top-level function $w"); continue }
    $d = $defs[$w]
    foreach ($c in @($d.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true))) {
        $cn = $c.GetCommandName()
        if ($null -eq $cn) {
            $e0 = $c.CommandElements[0]
            if (-not ($w -eq 'Get-Plan' -and [string]$c.InvocationOperator -eq 'Ampersand' -and $e0 -is [System.Management.Automation.Language.VariableExpressionAst] -and $e0.VariablePath.UserPath -eq 'PsExe')) { $loadWhy.Add("${w} runs '$($c.Extent.Text)'") }
        }
        elseif ($okCmds -notcontains $cn) { $loadWhy.Add("${w} calls $cn") }
        elseif ([string]$c.InvocationOperator -eq 'Dot') { $loadWhy.Add("${w} dot-sources $cn") }
        elseif ($cn -eq 'New-Object') {
            $a1 = if ($c.CommandElements.Count -ge 2) { $c.CommandElements[1] } else { $null }
            if (-not ($a1 -is [System.Management.Automation.Language.StringConstantExpressionAst] -and $a1.Value -ceq 'System.Collections.Generic.List[string]')) { $loadWhy.Add("${w} runs '$($c.Extent.Text)'") }
        }
    }
    foreach ($mm in @($d.FindAll({ param($n) $n -is [System.Management.Automation.Language.InvokeMemberExpressionAst] }, $true))) {
        if ($mm.Member -isnot [System.Management.Automation.Language.StringConstantExpressionAst]) { $loadWhy.Add("${w} calls a method by a computed name: $($mm.Extent.Text)") }
        elseif ($mm.Member.Value -match $denyMember) { $loadWhy.Add("${w} calls .$($mm.Member.Value)()") }
    }
    if (@($d.FindAll({ param($n) $n -is [System.Management.Automation.Language.FileRedirectionAst] }, $true)).Count) { $loadWhy.Add("${w} redirects output to a file") }
    $own = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    $plist = @(); if ($null -ne $d.Parameters) { $plist += @($d.Parameters) }; if ($null -ne $d.Body.ParamBlock) { $plist += @($d.Body.ParamBlock.Parameters) }
    foreach ($pa in $plist) { [void]$own.Add($pa.Name.VariablePath.UserPath) }
    foreach ($as in @($d.FindAll({ param($n) $n -is [System.Management.Automation.Language.AssignmentStatementAst] }, $true))) {
        $lv = $as.Left
        if ($lv -is [System.Management.Automation.Language.ConvertExpressionAst]) { $lv = $lv.Child }
        if ($lv -is [System.Management.Automation.Language.VariableExpressionAst]) {
            if ($lv.VariablePath.IsScript -or $lv.VariablePath.IsGlobal) { $loadWhy.Add("${w} assigns $($lv.Extent.Text)") }
            [void]$own.Add($lv.VariablePath.UserPath)
        }
    }
    foreach ($fe in @($d.FindAll({ param($n) $n -is [System.Management.Automation.Language.ForEachStatementAst] }, $true))) { [void]$own.Add($fe.Variable.VariablePath.UserPath) }
    foreach ($v in @($d.FindAll({ param($n) $n -is [System.Management.Automation.Language.VariableExpressionAst] }, $true))) {
        $vn = $v.VariablePath.UserPath
        if ($v.VariablePath.IsScript -or $v.VariablePath.IsGlobal -or $v.VariablePath.DriveName) { $loadWhy.Add("${w} uses $($v.Extent.Text)"); continue }
        if (-not $own.Contains($vn) -and $given -notcontains $vn -and $auto -notcontains $vn) { $loadWhy.Add("${w} uses `$$vn, which is not given here") }
    }
    # $PSCommandPath / $PSScriptRoot mean the launcher's file and folder, as when run-night.ps1 runs.
    $txt = $d.Extent.Text; $base = $d.Extent.StartOffset
    $subs = @($d.FindAll({ param($n) $n -is [System.Management.Automation.Language.VariableExpressionAst] -and ($n.VariablePath.UserPath -eq 'PSCommandPath' -or $n.VariablePath.UserPath -eq 'PSScriptRoot') }, $true) | Sort-Object { $_.Extent.StartOffset } -Descending)
    foreach ($sv in $subs) {
        $repl = if ($sv.VariablePath.UserPath -eq 'PSCommandPath') { '$LauncherPath' } else { '$LauncherDir' }
        $o = $sv.Extent.StartOffset - $base
        $txt = $txt.Substring(0, $o) + $repl + $txt.Substring($o + $sv.Extent.Text.Length)
    }
    $fnText.Add($txt)
}
$loadWhyU = @($loadWhy | Select-Object -Unique)
$useLauncher = ($loadWhyU.Count -eq 0) -and -not $ReplicaOnly
if ($loadWhyU.Count) {
    if ($ReplicaOnly) { $notes.Add("launcher functions not loaded (-ReplicaOnly): $($loadWhyU -join ' | ')") }
    else { $fail.Add("launcher functions not loaded: $($loadWhyU -join ' | ') (-ReplicaOnly checks with my copies only)") }
} elseif ($ReplicaOnly) { $notes.Add('-ReplicaOnly: the launcher functions load cleanly but were not used (my Parse-Go and Get-Plan copies; no Test-Matrix)') }
if ($useLauncher) { . ([scriptblock]::Create(($fnText -join "`r`n"))) }

# ---------- 2. the draft ----------
$bytes = [IO.File]::ReadAllBytes($draftPath)
$draftSha = Sha $draftPath
if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { $fail.Add("$name starts with a BOM") }
$nonAscii = 0; foreach ($b in $bytes) { if ($b -gt 0x7F) { $nonAscii++ } }
if ($nonAscii) { $notes.Add("$name has $nonAscii non-ASCII bytes") }
$m = $null
try { $m = [IO.File]::ReadAllText($draftPath) | ConvertFrom-Json } catch { $fail.Add("$name is not valid JSON: $($_.Exception.Message)") }
$cold = $false; $ids = New-Object System.Collections.Generic.List[string]; $bins = [ordered]@{}; $armInfo = New-Object System.Collections.Generic.List[string]
if ($null -ne $m) {
    if ([string](P $m 'title') -cmatch 'DRAFT') { $fail.Add('the title says DRAFT') }
    foreach ($x in @(P $m 'notes')) { if ([string]$x -cmatch '^DRAFT') { $fail.Add('a note starts with DRAFT') } }
    if ((P $m 'sys_csv') -ne $true) { $fail.Add('sys_csv is not true (the launcher would only warn; a window without sys.csv has no host data)') }
    $cold = ((P $m 'cold_run') -eq $true); if (-not $cold) { $notes.Add('cold_run is not true: the window has no cold run') }
    $floor = P $m 'min_window_after_ff_s'
    if ($null -eq $floor -or [double]$floor -lt 60) { $fail.Add("min_window_after_ff_s is '$floor', below Agent 1's 60 s floor") }
    $ref = [string](P $m 'reference')
    $arms = @(P $m 'arms')
    if ($arms.Count -eq 0 -or $null -eq $arms[0]) { $fail.Add('the matrix has no arms'); $arms = @() }
    foreach ($a in $arms) {
        $aid = [string](P $a 'id')
        if ($aid -cnotmatch "^$idRx$") { $fail.Add("arm id '$aid' is not 1-32 of A-Z a-z 0-9 _ . -") }
        if ($ids -ccontains $aid) { $fail.Add("arm id '$aid' appears twice") }
        $ids.Add($aid)
        if (((P $a 'ref') -eq $true) -and $aid -cne $ref) { $notes.Add("arm $aid has ref: true but the reference is '$ref'") }
        $bn = ([string](P $a 'bin')) -replace '\\', '/'
        $leaf = '?'
        if ($bn -cnotmatch '^build/agent2/([A-Za-z0-9][A-Za-z0-9_.-]*)-bin/?$' -or $bn -match '\.\.') { $fail.Add("arm ${aid}: bin '$bn' is not build/agent2/<name>-bin") }
        else { $leaf = $Matches[1]; if (-not $bins.Contains($leaf)) { $bins[$leaf] = New-Object System.Collections.Generic.List[string] }; $bins[$leaf].Add($aid) }
        foreach ($k in @('menu', 'profile', 'triggers', 'toml', 'seed_cache')) { if ($null -ne $a.PSObject.Properties[$k]) { $fail.Add("arm ${aid}: has a $k field") } }
        $fr = [string](P $a 'frames')
        if ($fr -cne 'perf' -and $fr -cne 'native') { $fail.Add("arm ${aid}: frames '$fr' is not perf or native") }
        $cvl = @()
        foreach ($c in @(P $a 'cvars')) { if ($null -eq $c) { continue }; if ($c -isnot [string] -or $c -cnotmatch '^[A-Za-z_][A-Za-z0-9_]*=[^;\s]*$') { $fail.Add("arm ${aid}: cvar '$c' is not a name=value string without ; or spaces") } else { $cvl += $c } }
        $evl = @()
        $ev = P $a 'env'
        if ($null -ne $ev) {
            if ($ev -isnot [System.Management.Automation.PSCustomObject]) { $fail.Add("arm ${aid}: env is not an object") }
            else {
                foreach ($pp in $ev.PSObject.Properties) {
                    if ($AllowedEnv -cnotcontains $pp.Name) { $fail.Add("arm ${aid}: env key '$($pp.Name)' is not allowed by the launcher") }
                    if ($pp.Value -isnot [string] -or -not $pp.Value) { $fail.Add("arm ${aid}: env $($pp.Name) is not a non-empty string") }
                    $evl += "$($pp.Name)=$($pp.Value)"
                }
            }
        }
        $dr = P $a 'driver'
        if ($dr -isnot [string] -or $dr -cnotmatch '^drivers/([A-Za-z0-9_-]+\.ps1)$') { $fail.Add("arm ${aid}: driver is not a plain string drivers/<name>.ps1") }
        elseif ($AllowedDrivers -cnotcontains $Matches[1]) { $fail.Add("arm ${aid}: driver $dr is not one of the launcher's $($AllowedDrivers -join ', ')") }
        elseif (-not (Test-Path -LiteralPath (Join-Path $RunDir ('drivers\' + $Matches[1])) -PathType Leaf)) { $fail.Add("arm ${aid}: $dr is not in bench\agent8\run") }
        $armInfo.Add("$aid ($leaf; frames $fr; cvars $($cvl -join ';'); env $(if ($evl.Count) { $evl -join ' ' } else { '{}' }); $dr)")
    }
    foreach ($o in $onlyList) { if ($ids -cnotcontains $o) { $fail.Add("only=: the matrix has no arm '$o'") } }
    if (-not $ref) { $fail.Add('the matrix names no reference arm') } elseif ($onlyList -cnotcontains $ref) { $fail.Add("the reference arm '$ref' is not in only=") }
}

# ---------- 3. the bins of every arm ----------
$binRows = New-Object System.Collections.Generic.List[string]
$binFiles = [ordered]@{}
foreach ($leaf in @($bins.Keys)) {
    $bd = Join-Path $Repo "build\agent2\$leaf-bin"
    $man = Join-Path $bd 'MANIFEST.txt'; $exe = Join-Path $bd 'legodimensions.exe'
    if (-not (Test-Path -LiteralPath $man -PathType Leaf) -or -not (Test-Path -LiteralPath $exe -PathType Leaf)) { $fail.Add("build/agent2/$leaf-bin has no MANIFEST.txt or no legodimensions.exe (not staged)"); $binRows.Add("build/agent2/$leaf-bin (arms $($bins[$leaf] -join ',')): NOT STAGED"); continue }
    $manSha = Sha $man; $binFiles[$man] = $manSha
    $exp = if ($expectMap.ContainsKey($leaf)) { $expectMap[$leaf] } else { '-' }
    if ($exp -ne '-') { if (-not $manSha.StartsWith($exp)) { $fail.Add("$leaf-bin MANIFEST.txt sha256 $manSha does not start with -Expect $exp") } }
    elseif ($Promote -or $Recheck) { $fail.Add("-Expect has no entry for $leaf (every bin needs its MANIFEST.txt sha256 from Agent 2's staging report)") }
    else { $notes.Add("-Expect has no entry for $leaf; its MANIFEST.txt sha256 starts $($manSha.Substring(0, 16))") }
    $lines = @(Get-Content -LiteralPath $man)
    $listed = @{}
    foreach ($ln in $lines) { if ($ln.StartsWith('#')) { continue }; $cc = $ln -split "`t"; if ($cc.Count -ge 4 -and $cc[3] -match '^[0-9A-F]{64}$') { $listed[$cc[0]] = @($cc[1], $cc[3]) } }
    $nPass = @($lines | Where-Object { $_ -match '^#\s+PASS\b' }).Count
    $nFail = @($lines | Where-Object { $_ -match '^#\s+FAIL\b' }).Count
    if ($nFail) { $fail.Add("$leaf-bin MANIFEST.txt has $nFail FAIL check line(s)") }
    if (-not $listed.Count) { $fail.Add("$leaf-bin MANIFEST.txt lists no files") }
    $toHash = @(if ($VerifyFiles) { $listed.Keys | Sort-Object } else { 'legodimensions.exe' })
    $okN = 0
    foreach ($fn in $toHash) {
        $fp = Join-Path $bd $fn
        if (-not $listed.ContainsKey($fn)) { $fail.Add("$leaf-bin MANIFEST.txt does not list $fn"); continue }
        if (-not (Test-Path -LiteralPath $fp -PathType Leaf)) { $fail.Add("$leaf-bin lacks $fn, which its MANIFEST.txt lists"); continue }
        $h = Sha $fp; $len = (Get-Item -LiteralPath $fp).Length; $binFiles[$fp] = $h
        if ($h -ne $listed[$fn][1] -or [string]$len -ne $listed[$fn][0]) { $fail.Add("$leaf-bin\$fn differs from its MANIFEST.txt line (sha256 or size)") } else { $okN++ }
    }
    if ($VerifyFiles) { $unl = @(Get-ChildItem -LiteralPath $bd -File | Where-Object { $_.Name -ne 'MANIFEST.txt' -and -not $listed.ContainsKey($_.Name) } | ForEach-Object { $_.Name }); if ($unl.Count) { $notes.Add("$leaf-bin files MANIFEST.txt does not list: $($unl -join ', ')") } }
    $exeSha = if ($binFiles.Contains($exe)) { $binFiles[$exe] } else { '-' }
    $binRows.Add("build/agent2/$leaf-bin (arms $($bins[$leaf] -join ',')): MANIFEST.txt sha256 $manSha (expected $exp); legodimensions.exe $exeSha; $($listed.Count) files listed, $okN of $($toHash.Count) checked match$(if (-not $VerifyFiles) { ' (the exe; -VerifyFiles checks every file)' }); check lines PASS $nPass, FAIL $nFail")
}
foreach ($k in @($expectMap.Keys)) { if (-not $bins.Contains($k)) { $notes.Add("-Expect names $k, which no arm uses") } }

# ---------- 4. the copy ----------
if ($Recheck) { $dstDir = $RunDir; $dst = $draftPath }
elseif ($Promote) { $dstDir = $RunDir; $dst = Join-Path $RunDir $name }
else { $dstDir = Join-Path $wfDir ('test\' + $Id); $dst = Join-Path $dstDir $name }
$dstSha = '-'; $copied = $false
if (-not $fail.Count -and -not $Recheck) {
    $dstExists = Test-Path -LiteralPath $dst
    if ($dstExists -and ((Sha $dst) -ne $draftSha) -and $Promote -and -not $Force) { $fail.Add("$(Rel $dst) exists with another sha256; -Force replaces it") }
    elseif ($dstExists -and ((Sha $dst) -eq $draftSha)) { $notes.Add("$(Rel $dst) already holds this exact file") }
    else {
        Stop-IfHold
        if ($dstExists) { $notes.Add("$(Rel $dst) replaced (it had another sha256)") }
        New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
        Copy-Item -LiteralPath $draftPath -Destination $dst -Force
        $copied = $true
    }
}
if (Test-Path -LiteralPath $dst -PathType Leaf) { $dstSha = Sha $dst }
if ($copied -and $dstSha -ne $draftSha) { $fail.Add('the copy has another sha256 than the draft') }

# ---------- 5. the launcher's own checks, then the runner's plan ----------
$MatrixDirEff = [IO.Path]::GetFullPath($dstDir).TrimEnd('\')
$goLine = "GO $Id $name $dstSha only=$Only repeats=$Repeats"
$expRuns = $(if ($cold) { 1 } else { 0 }) + $onlyList.Count * $Repeats
$agent7Min = 1.70 + 2.14 * $onlyList.Count * $Repeats
$tmList = @(); $binH = $null; $plan = $null; $before = '-'; $after = '-'; $go = $null
function Get-PlanReplica([string]$Path) {
    $r = @{ ok = $false; why = ''; min = 0; runs = 0; lines = @() }
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $r.lines = @(& $PsExe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $RunMatrix -Matrix $Path -Only $Only -Repeats ([string]$Repeats) -ColdShared -NoPrompt -PlanOnly 2>&1 | ForEach-Object { "$_" }); $code = $LASTEXITCODE } finally { $ErrorActionPreference = $old }
    $est = @($r.lines | Where-Object { $_ -match '^estimate (\d+) runs \(\d+ cold\), about (\d+) min' })
    $bad = @($r.lines | Where-Object { $_ -match '^!!! (ERROR|SKIPPED ARM|MATRIX ERROR)' -or $_ -match '^\s+SKIP ' })
    if ($code -ne 0) { $r.why = "run-matrix.ps1 -PlanOnly exit $code" }
    elseif ($bad.Count) { $r.why = "run-matrix.ps1 -PlanOnly: $($bad -join ' / ')" }
    elseif (-not $est.Count) { $r.why = 'run-matrix.ps1 -PlanOnly printed no estimate line' }
    else { [void]($est[0] -match '^estimate (\d+) runs \(\d+ cold\), about (\d+) min'); $r.runs = [int]$Matches[1]; $r.min = [int]$Matches[2]; $r.ok = $true }
    return $r
}
if (-not $fail.Count) {
    if ($useLauncher) {
        $go = Parse-Go $goLine
        if (-not $go.ok) { foreach ($x in $go.why) { $fail.Add("launcher Parse-Go: $x") } }
        else {
            $tmList = Test-Matrix $go $dst
            foreach ($x in $tmList) { $fail.Add("launcher Test-Matrix: $x") }
            $wl = Get-MatrixWarnings $dst
            foreach ($x in $wl) { $notes.Add("launcher Get-MatrixWarnings: $x") }
            if (-not $fail.Count) { $binH = Get-BinHashes $go $dst }
        }
    }
}
if (-not $fail.Count) {
    $matrixRoot = Join-Path $Repo 'build\agent8\matrix'
    $notes.Add('queue gap: ' + (Wait-QueueGap $QueueGapS 120 600))
    $before = @(Get-ChildItem -LiteralPath $matrixRoot -Directory).Count
    Stop-IfHold
    Push-Location (Join-Path $Repo 'bench\agent8')
    try { $plan = if ($useLauncher) { Get-Plan $dst $go } else { Get-PlanReplica $dst } } finally { Pop-Location }
    $after = @(Get-ChildItem -LiteralPath $matrixRoot -Directory).Count
    if (-not $plan.ok) { $fail.Add($plan.why) }
    elseif ($plan.runs -ne $expRuns) { $fail.Add("-PlanOnly plans $($plan.runs) runs, not $(if ($cold) { '1 cold + ' })$($onlyList.Count) x $Repeats = $expRuns") }
    if ($after -ne $before) { $fail.Add("build\agent8\matrix had $before folders before -PlanOnly and $after after") }
}
$latestTxt = '-'
if ($null -ne $plan -and $plan.ok) {
    $day = [datetime]::Today
    $byEnd = $day.AddHours(7.5).AddMinutes(-($plan.min + $DeadlineSlackMin))
    $cap = $day.AddHours($LatestStartTime)
    $latestTxt = if ($byEnd -lt $cap) { "the launcher accepts this GO until {0:HH:mm} (07:30 - runner estimate {1} min - slack {2} min); started then, it ends about {3:HH:mm} by Agent 7's formula" -f $byEnd, $plan.min, $DeadlineSlackMin, $byEnd.AddMinutes($agent7Min) }
                 else { "the launcher accepts this GO before {0:HH:mm} (no start at or after it; 07:30 - {1} - {2} min would allow {3:HH:mm}); started at {0:HH:mm} it ends about {4:HH:mm} by Agent 7's formula" -f $cap, $plan.min, $DeadlineSlackMin, $byEnd, $cap.AddMinutes($agent7Min) }
}

# ---------- 6. the inputs the window reads ----------
$H = New-Object System.Collections.Generic.List[string]
function Add-H([string]$Path, [string]$Known) {
    if (Test-Path -LiteralPath $Path -PathType Leaf) { $fi = Get-Item -LiteralPath $Path; $hs = if ($Known) { $Known } else { Sha $Path }; $H.Add(('{0}  {1,11}  {2}  {3}' -f $hs, $fi.Length, $fi.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'), (Rel $Path))) }
    else { $H.Add("MISSING  $(Rel $Path)") }
}
if ($null -ne $plan) {
    Add-H $dst $dstSha
    $pins = @(if ($useLauncher) { Get-PinFiles } else {
        $pl = New-Object System.Collections.Generic.List[string]
        $pl.Add($LauncherPath); $pl.Add((Join-Path $LauncherDir 'RUN-NIGHT.cmd'))
        foreach ($n in @('run-matrix.ps1', 'run-timing.ps1', 'common.ps1', 'timing-env.ps1', 'winhelper.cs')) { $pl.Add((Join-Path $RunDir $n)) }
        foreach ($f in @(Get-ChildItem -LiteralPath $RunDir -File | Where-Object { $_.Extension -eq '.py' -or $_.Extension -eq '.cs' })) { $pl.Add($f.FullName) }
        foreach ($f in @(Get-ChildItem -LiteralPath (Join-Path $RunDir 'drivers') -File -Recurse)) { $pl.Add($f.FullName) }
        $pl.Add((Join-Path $Repo 'harness\legodimensions.toml')); $pl.Add((Join-Path $Repo 'harness\nvml.cs'))
        @($pl | Sort-Object -Unique)
    })
    foreach ($p in $pins) { Add-H $p '' }
    foreach ($p in @($binFiles.Keys)) { Add-H $p $binFiles[$p] }
    if (@($H | Where-Object { $_ -like 'MISSING*' }).Count) { $fail.Add('an input file is missing (see the inputs file)') }
}

# ---------- 7. the report ----------
$L = New-Object System.Collections.Generic.List[string]
$L.Add("Window staging (Agent 8, run-2 task #7, build\agent8\w-followup\stage-window.ps1), $when")
$L.Add("mode: $modeName$(switch ($modeName) { 'TEST' { ' (copy in ' + (Rel $dstDir) + '; no bench writes)' } 'PROMOTE' { ' (copied to bench\agent8\run)' } default { ' (already in bench\agent8\run; no copy)' } })")
$L.Add("result: $(if ($fail.Count) { 'NOT OK: ' + ($fail -join ' | ') } else { 'OK' })")
$L.Add("run: only=$Only repeats=$Repeats -ColdShared; $(if ($null -ne $plan -and $plan.ok) { "-PlanOnly: $($plan.runs) runs, about $($plan.min) min (runner)" } else { '-PlanOnly: not run or failed' }); expected $expRuns runs; Agent 7's formula 1.70 + 2.14 x $($onlyList.Count) x $Repeats = $('{0:N1}' -f $agent7Min) min")
$L.Add("latest start: $latestTxt")
$L.Add("GO line$(if ($modeName -eq 'TEST') { ' (TEST: the matrix is not in bench\agent8\run; never write this one to WINDOW-GO.txt)' }): $(if ($fail.Count) { 'none (result NOT OK)' } else { $goLine })")
$L.Add("draft: $(Rel $draftPath)  sha256 $draftSha  $($bytes.Length) bytes")
$L.Add("matrix for the GO: $(Rel $dst)  sha256 $dstSha")
$L.Add("launcher: bench\agent5\launch\run-night.ps1 sha256 $launcherSha ($launcherTime); checked by $(if ($useLauncher) { 'its own functions: ' + ($want -join ', ') } else { 'my copies only' }); env keys $(@($AllowedEnv).Count); drivers $($AllowedDrivers -join ', '); slack $DeadlineSlackMin min; no start at or after $('{0:HH:mm}' -f [datetime]::Today.AddHours($LatestStartTime))")
foreach ($x in $binRows) { $L.Add("bin: $x") }
foreach ($x in $armInfo) { $L.Add("arm: $x") }
$L.Add("matrix folders before/after -PlanOnly: $before / $after")
foreach ($x in $notes) { $L.Add("NOTE: $x") }
$head = $L.Count
$L.Add('')
if ($loadWhyU.Count) { $L.Add('--- launcher functions not loaded because:'); foreach ($x in $loadWhyU) { $L.Add($x) }; $L.Add('') }
if ($null -ne $binH) { $L.Add('--- launcher Get-BinHashes (only= arms)'); foreach ($k in @($binH.Keys)) { $L.Add("$($binH[$k])  $k") }; $L.Add('') }
$L.Add("--- run-matrix.ps1 -Matrix $(Rel $dst) -Only $Only -Repeats $Repeats -ColdShared -NoPrompt -PlanOnly ($(if ($useLauncher) { "launcher Get-Plan" } else { 'my copy' }))")
if ($null -ne $plan) { foreach ($x in $plan.lines) { $L.Add($x) } } else { $L.Add('(not run)') }
$utf8 = New-Object Text.UTF8Encoding $false
$rep = Join-Path $Repo 'build\agent8\readout\w-followup'
New-Item -ItemType Directory -Force -Path $rep | Out-Null
$repPath = Join-Path $rep ("stage-$Id-$stamp" + $(if ($fail.Count) { '-NOTOK' } else { '' }) + '.txt')
$L[2] = "result: $(if ($fail.Count) { 'NOT OK: ' + ($fail -join ' | ') } else { 'OK' })"
$L[5] = "GO line$(if ($modeName -eq 'TEST') { ' (TEST: the matrix is not in bench\agent8\run; never write this one to WINDOW-GO.txt)' }): $(if ($fail.Count) { 'none (result NOT OK)' } else { $goLine })"
[IO.File]::WriteAllText($repPath, (($L -join "`r`n") + "`r`n"), $utf8)
if ($H.Count) {
    $hPath = Join-Path $rep "inputs-$Id-$stamp.txt"
    $hh = @("$Id inputs (Agent 8, stage-window.ps1), $when, mode $modeName, GO sha256 ${dstSha}: sha256, bytes, last write, path") + @($H)
    [IO.File]::WriteAllText($hPath, (($hh -join "`r`n") + "`r`n"), $utf8)
}
Write-Host ($L[0..($head - 1)] -join "`r`n")
Write-Host "written: $(Rel $repPath)$(if ($H.Count) { " and inputs-$Id-$stamp.txt ($($H.Count) files)" })"
if ($fail.Count) { exit 1 } else { exit 0 }

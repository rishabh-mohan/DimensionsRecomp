# test_syscsv_pkg.ps1 - staging test of the package-power columns pkg_w,pp0_w,pp1_w,dram_w in the staged sampler copy
# bench\agent11\syscsv-pkg\{LdSys.cs,sys-csv.ps1} (Agent 11, 2026-11-22).
# Read-only towards bench\agent8\** and build\agent8\**: the staged copy compiles into build\agent11\cache. Agent 8's
# original sampler runs only with -Compare and only when its DLL is already cached (so nothing is written to
# build\agent8\cache; that folder's listing is compared before / after).
# Every sampler run uses this script's own PID as -GamePid and stops by -MaxSec; output in
# build\agent11\syscsv-pkg\test\<stamp>\<nn>-<staged|orig>\ (sys.csv, sys.out.txt, sys.err.txt), the log in result.txt.
# Checks, staged runs: exit 0 and stop reason=max_sec; start line counters=6/6 and no power:* entry in failed=[..]; dll = LdSys-<content key of
# the staged LdSys.cs>.dll and present in build\agent11\cache; header = Agent 8's 24 columns + pkg_w,pp0_w,pp1_w,dram_w;
# 28 fields in every row; rows >= Seconds-1; pkg_w a number in (0.5, 400) W in every row after the first;
# pp0_w <= pkg_w * 1.05 + 0.5 W where both are set. Original runs (-Compare): exit 0, reason=max_sec, counters=5/5,
# dll cached, 24-column header; the columns that are ever filled (rows after the first) are the same 24 in both arms, and
# the same counters failed at init in both arms (tz_temp / tz_passive have no data on the test machine: not a staging fault).
# Always: Agent 8's LdSys.cs / sys-csv.ps1 equal the 06:31 record (originals-0631.txt) and are unchanged by the test.
# Cost (printed, no threshold): sample_ms / sample_cpu_ms (timing line; sample_cpu_ms is first/mean/max, the summary uses
# the mean) and steady_cpu_pct (stop line) per run and arm.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\syscsv-pkg\test_syscsv_pkg.ps1
#          [-Seconds 12] [-Compare] [-Rounds 1]
# Exit: 0 all checks pass, 1 a check failed, 2 setup error.
param(
    [int]$Seconds = 12,
    [switch]$Compare,
    [int]$Rounds = 1
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$inv = [Globalization.CultureInfo]::InvariantCulture
$here = $PSScriptRoot
$repo = [IO.Path]::GetFullPath([IO.Path]::Combine($here, '..\..\..'))
$a8drv = [IO.Path]::Combine($repo, 'bench\agent8\run\drivers')
$a8cache = [IO.Path]::Combine($repo, 'build\agent8\cache')
$a11cache = [IO.Path]::Combine($repo, 'build\agent11\cache')
$stagedCs = [IO.Path]::Combine($here, 'LdSys.cs')
$stagedPs = [IO.Path]::Combine($here, 'sys-csv.ps1')
$origCs = [IO.Path]::Combine($a8drv, 'LdSys.cs')
$origPs = [IO.Path]::Combine($a8drv, 'sys-csv.ps1')
$stamp = [DateTime]::Now.ToString('yyyyMMdd-HHmmss', $inv)
$outRoot = [IO.Path]::Combine($repo, 'build\agent11\syscsv-pkg\test\' + $stamp)
$log = New-Object 'System.Collections.Generic.List[string]'
$script:fails = 0
$script:checks = 0
$script:runN = 0

function Say([string]$M) {
    $l = [DateTime]::Now.ToString('HH:mm:ss', $inv) + ' ' + $M
    [Console]::Out.WriteLine($l)
    $log.Add($l)
}
function Check([bool]$Ok, [string]$What) {
    $script:checks++
    if ($Ok) { Say ('PASS ' + $What) } else { $script:fails++; Say ('FAIL ' + $What) }
}
function Sha([string]$P) {
    $s = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($s.ComputeHash([IO.File]::ReadAllBytes($P))).Replace('-', '') } finally { $s.Dispose() }
}
function CacheList {
    if (-not [IO.Directory]::Exists($a8cache)) { return '<no dir>' }
    $items = @([IO.Directory]::GetFiles($a8cache) | Sort-Object | ForEach-Object {
        $fi = New-Object IO.FileInfo $_
        $fi.Name + ':' + $fi.Length + ':' + $fi.LastWriteTimeUtc.Ticks
    })
    return ($items -join '|')
}
function Field([string]$Line, [string]$Name) {
    if (-not $Line) { return $null }
    $m = [regex]::Match($Line, '(?:^|\s)' + [regex]::Escape($Name) + '=(\[[^\]]*\]|\S+)')
    if ($m.Success) { return $m.Groups[1].Value }
    return $null
}
function Num([string]$S) {
    $v = 0.0
    if ($S -and [double]::TryParse($S, [Globalization.NumberStyles]::Float, $inv, [ref]$v)) { return $v }
    return [double]::NaN
}
function Med([double[]]$A) {
    if ($null -eq $A -or $A.Length -eq 0) { return [double]::NaN }
    $s = [double[]]@($A | Sort-Object)
    $m = [int][Math]::Floor($s.Length / 2)
    if ($s.Length % 2) { return $s[$m] }
    return ($s[$m - 1] + $s[$m]) / 2
}
function F([double]$X, [string]$Fmt = '0.000') {
    if ([double]::IsNaN($X)) { return 'NaN' }
    return $X.ToString($Fmt, $inv)
}
function Stats([double[]]$A) {
    if ($null -eq $A -or $A.Length -eq 0) { return 'n=0' }
    $s = [double[]]@($A | Sort-Object)
    return ('n={0} min={1} med={2} max={3}' -f $s.Length, (F $s[0]), (F (Med $s)), (F $s[$s.Length - 1]))
}
# '+' = the column has a value in at least one row after the first, '-' = never
function Filled($Lines, [int]$NCol) {
    $sb = New-Object Text.StringBuilder
    for ($c = 0; $c -lt $NCol; $c++) {
        $any = $false
        for ($i = 2; $i -lt $Lines.Length; $i++) {
            $f = $Lines[$i].Split(',')
            if ($c -lt $f.Length -and $f[$c] -ne '') { $any = $true; break }
        }
        if ($any) { [void]$sb.Append('+') } else { [void]$sb.Append('-') }
    }
    return $sb.ToString()
}

function RunSampler([string]$Arm, [string]$Script) {
    $script:runN++
    $dir = [IO.Path]::Combine($outRoot, ('{0:00}-{1}' -f $script:runN, $Arm))
    [void][IO.Directory]::CreateDirectory($dir)
    $so = [IO.Path]::Combine($dir, 'sys.out.txt')
    $se = [IO.Path]::Combine($dir, 'sys.err.txt')
    $al = '-NoProfile -ExecutionPolicy Bypass -File "' + $Script + '" -GamePid ' + $PID + ' -RunDir "' + $dir + '" -MaxSec ' + $Seconds
    Say ("run $($script:runN) $Arm : powershell $al")
    $t0 = [DateTime]::Now
    $p = Start-Process -FilePath 'powershell.exe' -ArgumentList $al -NoNewWindow -PassThru -RedirectStandardOutput $so -RedirectStandardError $se
    $null = $p.Handle                                  # keeps ExitCode readable after the exit (PS 5.1)
    $killed = $false
    if (-not $p.WaitForExit(($Seconds + 120) * 1000)) { try { $p.Kill() } catch { }; $killed = $true }
    $p.WaitForExit()
    $wall = ([DateTime]::Now - $t0).TotalSeconds
    $out = @()
    if ([IO.File]::Exists($so)) { $out = @([IO.File]::ReadAllLines($so)) }
    $err = ''
    if ([IO.File]::Exists($se)) { $err = [IO.File]::ReadAllText($se).Trim() }
    $start = $null; $timing = $null; $stop = $null
    foreach ($l in $out) {
        if ($l -match 'sys-csv: start ') { $start = $l }
        elseif ($l -match 'sys-csv: timing ') { $timing = $l }
        elseif ($l -match 'sys-csv: stop ') { $stop = $l }
    }
    $csv = [IO.Path]::Combine($dir, 'sys.csv')
    $lines = @()
    if ([IO.File]::Exists($csv)) { $lines = @([IO.File]::ReadAllLines($csv)) }
    return New-Object PSObject -Property @{
        Arm = $Arm; N = $script:runN; Dir = $dir; Code = $p.ExitCode; Killed = $killed; Wall = $wall
        Err = $err; Start = $start; Timing = $timing; Stop = $stop; Lines = $lines
    }
}

function Analyze($R, [bool]$Staged) {
    $a = '{0}#{1}' -f $R.Arm, $R.N
    Check (($R.Code -eq 0) -and -not $R.Killed) ("$a exit 0 (code=$($R.Code) killed=$([int]$R.Killed) wall=" + (F $R.Wall '0.0') + ' s)')
    $reason = Field $R.Stop 'reason'
    Check ($reason -eq 'max_sec') "$a stop reason=max_sec (got $reason)"
    $ctr = Field $R.Start 'counters'
    $fl = Field $R.Start 'failed'
    $dll = Field $R.Start 'dll'
    $L = $R.Lines
    $rows = [Math]::Max(0, $L.Length - 1)
    if ($R.Err) { Say "$a stderr: $($R.Err -replace '\s+', ' ')" }
    if ($Staged) {
        Check ($ctr -eq '6/6') "$a counters=6/6 (got $ctr)"
        Check (($null -ne $fl) -and ($fl -notmatch '(^|[\[\s])power:')) "$a no power:* entry in failed (got $fl)"
        $want = "LdSys-$stagedKey.dll"
        Check (($null -ne $dll) -and $dll.StartsWith($want + '(') -and [IO.File]::Exists([IO.Path]::Combine($a11cache, $want))) "$a dll=$dll in build\agent11\cache (want $want)"
        Check (($L.Length -ge 1) -and ($L[0] -ceq $hdr28)) "$a header = 24 original columns + $new4"
        $nCol = 28
    } else {
        Check ($ctr -eq '5/5') "$a counters=5/5 (got $ctr)"
        Check (($null -ne $dll) -and ($dll -eq "LdSys-$origKey.dll(cached)")) "$a dll=$dll (want LdSys-$origKey.dll(cached))"
        Check (($L.Length -ge 1) -and ($L[0] -ceq $hdr24)) "$a header = the 24 original columns"
        $nCol = 24
    }
    Check ($rows -ge [Math]::Max(2, $Seconds - 1)) "$a rows=$rows (>= $([Math]::Max(2, $Seconds - 1)))"
    $badN = 0
    for ($i = 1; $i -lt $L.Length; $i++) { if ($L[$i].Split(',').Length -ne $nCol) { $badN++ } }
    Check ($badN -eq 0) "$a $nCol fields in every row ($badN bad)"
    $R | Add-Member -NotePropertyName Filled -NotePropertyValue (Filled $L 24)
    $R | Add-Member -NotePropertyName Failed -NotePropertyValue ([string]$fl)
    Say "$a filled(24 orig cols, rows 2..n)=$($R.Filled)"
    if ($Staged) {
        $pk = New-Object 'System.Collections.Generic.List[double]'
        $p0 = New-Object 'System.Collections.Generic.List[double]'
        $p1 = New-Object 'System.Collections.Generic.List[double]'
        $dr = New-Object 'System.Collections.Generic.List[double]'
        $badPk = 0; $badP0 = 0
        for ($i = 1; $i -lt $L.Length; $i++) {
            $f = $L[$i].Split(',')
            if ($f.Length -ne 28) { continue }
            if ($i -eq 1) { Say "$a first row (not checked): pkg_w=$($f[24]) pp0_w=$($f[25]) pp1_w=$($f[26]) dram_w=$($f[27])"; continue }
            $vk = Num $f[24]; $v0 = Num $f[25]; $v1 = Num $f[26]; $vd = Num $f[27]
            if ([double]::IsNaN($vk) -or $vk -le 0.5 -or $vk -ge 400) { $badPk++ } else { $pk.Add($vk) }
            if (-not [double]::IsNaN($v0)) {
                $p0.Add($v0)
                if (-not [double]::IsNaN($vk) -and $v0 -gt $vk * 1.05 + 0.5) { $badP0++ }
            }
            if (-not [double]::IsNaN($v1)) { $p1.Add($v1) }
            if (-not [double]::IsNaN($vd)) { $dr.Add($vd) }
        }
        Check (($badPk -eq 0) -and ($pk.Count -ge 1)) "$a pkg_w in (0.5, 400) W in every row after the first ($badPk bad)"
        Check ($badP0 -eq 0) "$a pp0_w <= pkg_w * 1.05 + 0.5 ($badP0 bad)"
        Say "$a pkg_w  $(Stats $pk.ToArray())"
        Say "$a pp0_w  $(Stats $p0.ToArray())"
        Say "$a pp1_w  $(Stats $p1.ToArray())"
        Say "$a dram_w $(Stats $dr.ToArray())"
    }
    Say ("$a cost: sample_ms=" + (Field $R.Timing 'sample_ms') + ' sample_ms_max=' + (Field $R.Timing 'sample_ms_max') +
        ' sample_cpu_ms=' + (Field $R.Timing 'sample_cpu_ms') + ' steady_cpu_pct=' + (Field $R.Stop 'steady_cpu_pct') +
        ' parts_mean_ms=' + (Field $R.Timing 'parts_mean_ms') + ' parts_cpu_mean_ms=' + (Field $R.Timing 'parts_cpu_mean_ms'))
}

# ---- setup ----
try {
    [void][IO.Directory]::CreateDirectory($outRoot)
    foreach ($p in @($stagedCs, $stagedPs, $origCs, $origPs)) { if (-not [IO.File]::Exists($p)) { throw "missing $p" } }
    if ($Seconds -lt 3 -or $Seconds -gt 600) { throw "-Seconds $Seconds (3..600)" }
    if ($Rounds -lt 1 -or $Rounds -gt 5) { throw "-Rounds $Rounds (1..5)" }
} catch { [Console]::Out.WriteLine('SETUP ERROR: ' + $_.Exception.Message); exit 2 }
$hdr24 = 't_s,epoch_s,wall,idle_s,fg_pid,fg_game,game_alive,input_desktop,screensaver,' +
    'cpu_util_pct,cpu_perf_pct,base_mhz,eff_mhz,p_eff_mhz,e_eff_mhz,p_util_pct,e_util_pct,' +
    'tz_passive_min_pct,tz_temp_max_c,ac,batt_saver,batt_pct,scheme,overlay'
$new4 = 'pkg_w,pp0_w,pp1_w,dram_w'
$hdr28 = $hdr24 + ',' + $new4
Say ("test_syscsv_pkg: stamp=$stamp seconds=$Seconds rounds=$Rounds compare=$([int][bool]$Compare) pid=$PID out=$outRoot")

# ---- Agent 8's originals: equal to the 06:31 record; cache listing ----
$rec = @{}
foreach ($l in [IO.File]::ReadAllLines([IO.Path]::Combine($here, 'originals-0631.txt'))) {
    $m = [regex]::Match($l, '^([0-9A-Fa-f]{16})\s+(\S+)')
    if ($m.Success) { $rec[$m.Groups[2].Value] = $m.Groups[1].Value.ToUpperInvariant() }
}
$h0cs = Sha $origCs
$h0ps = Sha $origPs
$kcs = 'bench\agent8\run\drivers\LdSys.cs'
$kps = 'bench\agent8\run\drivers\sys-csv.ps1'
Check ($rec.ContainsKey($kcs) -and $h0cs.StartsWith($rec[$kcs])) "Agent 8 LdSys.cs sha256 $($h0cs.Substring(0, 16)) = 06:31 record"
Check ($rec.ContainsKey($kps) -and $h0ps.StartsWith($rec[$kps])) "Agent 8 sys-csv.ps1 sha256 $($h0ps.Substring(0, 16)) = 06:31 record"
$cache0 = CacheList
$stagedKey = (Sha $stagedCs).Substring(0, 8).ToLowerInvariant()
$origKey = $h0cs.Substring(0, 8).ToLowerInvariant()
$origDll = [IO.Path]::Combine($a8cache, "LdSys-$origKey.dll")
$doOrig = $false
if ($Compare) {
    if ([IO.File]::Exists($origDll)) { $doOrig = $true }
    else { Say "SKIP compare: $origDll is not cached (running the original would compile into build\agent8\cache)" }
}
Say "staged key=$stagedKey (dll $(if ([IO.File]::Exists([IO.Path]::Combine($a11cache, "LdSys-$stagedKey.dll"))) { 'cached' } else { 'not cached yet: the first run compiles' })), original key=$origKey"

# ---- runs: staged, original, staged, original, ... ----
$runs = New-Object 'System.Collections.Generic.List[object]'
for ($k = 0; $k -lt $Rounds; $k++) {
    $r = RunSampler 'staged' $stagedPs; $runs.Add($r); Analyze $r $true
    if ($doOrig) { $r = RunSampler 'orig' $origPs; $runs.Add($r); Analyze $r $false }
}

# ---- cross-checks and cost summary ----
$st = @($runs | Where-Object { $_.Arm -eq 'staged' })
$or = @($runs | Where-Object { $_.Arm -eq 'orig' })
if ($or.Length -gt 0) {
    $hs = $st[0].Lines; $ho = $or[0].Lines
    Check (($hs.Length -ge 1) -and ($ho.Length -ge 1) -and ($hs[0] -ceq ($ho[0] + ',' + $new4))) 'staged header = original header + 4 columns'
    $fs = @($st | ForEach-Object { $_.Filled } | Sort-Object -Unique)
    $fo = @($or | ForEach-Object { $_.Filled } | Sort-Object -Unique)
    Check (($fs.Length -eq 1) -and ($fo.Length -eq 1) -and ($fs[0] -eq $fo[0])) "same original columns filled in both arms (staged $($fs -join '/'), orig $($fo -join '/'))"
    $xs = @($st | ForEach-Object { $_.Failed } | Sort-Object -Unique)
    $xo = @($or | ForEach-Object { $_.Failed } | Sort-Object -Unique)
    Check (($xs.Length -eq 1) -and ($xo.Length -eq 1) -and ($xs[0] -eq $xo[0])) "same counters failed at init in both arms (staged $($xs -join '/'), orig $($xo -join '/'))"
}
foreach ($set in @(@{ N = 'staged'; R = $st }, @{ N = 'orig'; R = $or })) {
    if ($set.R.Length -eq 0) { continue }
    $sm = @($set.R | ForEach-Object { Num (Field $_.Timing 'sample_ms') })
    $sc = @($set.R | ForEach-Object {
        $v = Field $_.Timing 'sample_cpu_ms'
        if ($v) { $parts = $v.Split('/'); if ($parts.Length -ge 2) { $v = $parts[1] } }   # first/mean/max -> mean
        Num $v
    })
    $sp = @($set.R | ForEach-Object { Num (Field $_.Stop 'steady_cpu_pct') })
    Say ("cost $($set.N): runs=$($set.R.Length) sample_ms med=" + (F (Med $sm)) + ' sample_cpu_ms(mean) med=' + (F (Med $sc)) + ' steady_cpu_pct med=' + (F (Med $sp)))
}

# ---- Agent 8's files untouched ----
Check (((Sha $origCs) -eq $h0cs) -and ((Sha $origPs) -eq $h0ps)) 'Agent 8 LdSys.cs / sys-csv.ps1 unchanged by the test'
Check ((CacheList) -eq $cache0) 'build\agent8\cache listing unchanged (names, sizes, times)'

$verdict = if ($script:fails -eq 0) { 'PASS' } else { 'FAIL' }
Say ("RESULT: $verdict ($($script:checks - $script:fails)/$($script:checks) checks) out=$outRoot")
[IO.File]::WriteAllLines([IO.Path]::Combine($outRoot, 'result.txt'), $log.ToArray())
if ($script:fails -gt 0) { exit 1 }
exit 0

# heavy_batch.ps1 - heavy-TU compile comparison on IDENTICAL function sets:
#   baseline = build/agent2/gen-noflag/default (pin codegen): TU N compiled as-is. For these TUs it is
#              byte-identical to build/agent9/generated/off3 (checked and printed: TU N, funcs.N.h, pch.h),
#              so the baseline numbers are the off3 numbers.
#   batch    = build/agent9/generated/batch/default (build/agent9/configs/batch.toml: skip_lr, ctr/xer/
#              reserved/cr_as_local, cr_compare_so_zero, rlwinm, flush elision, vmx, musttail)
# The batch TU partition differs (localization shrinks the code), so the batch side of TU N is
# gen_out/batch_tuN.cpp: TU N's DEFINE_REX_FUNC list, in TU N's order, each function copied from the
# batch variant (fails loudly if one is missing or defined twice, or a chunk is not one whole function),
# after the #include lines of the batch TUs those functions come from (a preamble is only
# `#include "legodimensions_funcs.K.h"`, and each funcs header declares only what its own TU references).
# Self-test: the same split/join rebuilds every baseline TU N byte for byte from its own chunks.
# Flags: the real game Release entry of legodimensions_recomp.61.cpp in build/dev/compile_commands.json
# (the entry env/compile-one.ps1 picks; $GameFlagsFull from game_flags.ps1: -O3 -DNDEBUG
# -gline-tables-only -march=x86-64-v3 -msse4.1 -fasync-exceptions ...), with the generated-dir -I
# pointed at each variant and the CMake PCH replaced by a PCH of that variant's own
# legodimensions_pch.h built with the same flags.
# Slots: the main script holds none. The batch scan takes one slot; the clang runs go to -Workers
# background workers (default 2), and every clang run takes ONE Agent 9 slot (slot1.ps1, waits while
# bench/agent9/QUIET exists) and releases it, so no worker holds a slot while waiting for another.
# Jobs are interleaved so a TU's baseline and batch compiles run at about the same time.
#   powershell -NoProfile -File bench/agent9/musttail/heavy_batch.ps1 [-Tus 304,233,52,61] [-Workers 1|2] *> bench/agent9/musttail/heavy_batch.log
param([string]$Tus = '304,233,52,61', [string]$Batch = 'build/agent9/generated/batch/default',
  [string]$Base = 'build/agent2/gen-noflag/default', [string]$Off3 = 'build/agent9/generated/off3/default',
  [int]$Workers = 2, [switch]$NoWhole)
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
. (Join-Path $root 'env/devshell.ps1') | Out-Null
. (Join-Path $PSScriptRoot 'game_flags.ps1')
. (Join-Path $PSScriptRoot 'slot1.ps1')
$slot1 = Join-Path $PSScriptRoot 'slot1.ps1'
$out = Join-Path $PSScriptRoot 'gen_out'
New-Item -ItemType Directory -Force $out | Out-Null
function Resolve-Dir([string]$p) { if ([IO.Path]::IsPathRooted($p)) { $p } else { Join-Path $root $p } }
$baseDir = Resolve-Dir $Base; $batchDir = Resolve-Dir $Batch; $off3Dir = Resolve-Dir $Off3
$tuList = @($Tus -split '[,\s]+' | Where-Object { $_ } | ForEach-Object { [int]$_ })
$outTxt = Join-Path $PSScriptRoot 'heavy_batch.txt'
$devGen = 'DimensionsRecomp/rexlego/generated/default'
$reFn = [regex]'(?m)^DEFINE_REX_FUNC\((\w+)\)'
$reMt = [regex]'\[\[clang::musttail\]\]'
$rows = New-Object System.Collections.Generic.List[string]
function Save { $rows | Set-Content -Encoding ascii $outTxt }
function Note([string]$s) { $rows.Add($s); Write-Host ('[{0}] {1}' -f (Get-Date -Format 'HH:mm:ss'), $s) }
function Fail([string]$msg) { Note "FAILED: $msg"; Save; exit 1 }
function Get-FlagsFor([string]$dir) { @($GameFlagsFull | ForEach-Object { if ($_ -like "-I*$devGen") { '-I' + ($dir -replace '\\', '/') } else { $_ } }) }
function Get-Sha([string]$f) { if (Test-Path $f) { (Get-FileHash $f -Algorithm SHA1).Hash } else { 'missing' } }
function Get-TextBytes([string]$obj) {
  $sum = 0L
  foreach ($l in (& llvm-objdump -h $obj)) { if ($l -match '^\s*\d+\s+(\.text\S*)\s+([0-9a-fA-F]+)\s') { $sum += [Convert]::ToInt64($Matches[2], 16) } }
  $sum
}
# a generated TU = preamble (text before the first DEFINE_REX_FUNC) + chunks; a chunk runs from its
# DEFINE_REX_FUNC line to the next DEFINE_REX_FUNC (or the end of the file)
function Split-Tu([string]$s) {
  $ms = $reFn.Matches($s)
  $chunks = New-Object System.Collections.Generic.List[object]
  for ($i = 0; $i -lt $ms.Count; $i++) {
    $end = if ($i + 1 -lt $ms.Count) { $ms[$i + 1].Index } else { $s.Length }
    $chunks.Add([pscustomobject]@{ name = $ms[$i].Groups[1].Value; text = $s.Substring($ms[$i].Index, $end - $ms[$i].Index) })
  }
  [pscustomobject]@{ pre = $(if ($ms.Count) { $s.Substring(0, $ms[0].Index) } else { $s }); chunks = $chunks }
}
function Get-IncludeLines([string]$pre, [string]$what) {
  $r = New-Object System.Collections.Generic.List[string]
  foreach ($l in ($pre -split "`n")) {
    if (-not $l.Trim()) { continue }
    if ($l -notmatch '^#include\s') { Fail "$what preamble holds more than #include lines: '$l'" }
    $r.Add($l)
  }
  , $r
}
function Join-Tu($inc, $texts) {
  $sb = New-Object System.Text.StringBuilder
  foreach ($l in $inc) { [void]$sb.Append($l).Append("`n") }
  [void]$sb.Append("`n")
  foreach ($t in $texts) { [void]$sb.Append($t) }
  $sb.ToString()
}
# clang jobs (@{ key; cargs; err }) on $Workers background workers; each clang run takes ONE slot
function Invoke-ClangJobs([object[]]$jobs) {
  $res = @{}
  $w = [math]::Max(1, [math]::Min($Workers, $jobs.Count))
  if ($w -eq 1) {
    foreach ($j in $jobs) { $res[$j.key] = Invoke-ClangInSlot $j.cargs $j.err }
    return $res
  }
  $bg = @(for ($k = 0; $k -lt $w; $k++) {
      $mine = @(for ($i = $k; $i -lt $jobs.Count; $i += $w) { $jobs[$i] })
      Start-Job -ArgumentList $slot1, $mine -ScriptBlock {
        param($slot1, $mine)
        Set-ExecutionPolicy -Scope Process Bypass -Force
        . $slot1
        foreach ($j in $mine) {
          $r = Invoke-ClangInSlot ([string[]]@($j.cargs)) $j.err
          [pscustomobject]@{ key = $j.key; code = $r.code; wall = $r.wall; cpu = $r.cpu }
        }
      }
    })
  $null = Wait-Job $bg
  foreach ($b in $bg) {
    $je = $null
    foreach ($o in @(Receive-Job $b -ErrorVariable je)) { if ($o.key) { $res[[string]$o.key] = $o } }
    if ($je) { Note "worker error: $($je -join ' | ')" }
    Remove-Job $b -Force
  }
  foreach ($j in $jobs) { if (-not $res.ContainsKey($j.key)) { Fail "no result for $($j.key) (worker failed; see the log)" } }
  $res
}

Note "heavy-TU comparison on identical function sets ($(Get-Date -Format 'yyyy-MM-dd HH:mm'))"
$batchSha = @(Get-Content (Join-Path $root 'build/agent9/logs/gen-steps.txt') -ErrorAction SilentlyContinue | Where-Object { $_ -match '\[batch\] BEGIN .*sha=(\w+)' } | ForEach-Object { $Matches[1] }) | Select-Object -Last 1
if (-not (Test-Path (Join-Path $batchDir 'legodimensions_pch.h'))) { Fail "batch variant not found: $batchDir" }
$rows.Add("baseline: $baseDir (TU N as-is)")
$rows.Add("batch:    $batchDir ($(@(Get-ChildItem $batchDir -Filter 'legodimensions_recomp.*.cpp').Count) recomp TUs, written $((Get-Item (Join-Path $batchDir 'legodimensions_pch.h')).LastWriteTime.ToString('HH:mm')), rexglue.exe $batchSha per build/agent9/logs/gen-steps.txt); gen_out/batch_tuN.cpp = TU N's functions copied from it")
if (@($GameFlagsFull | Where-Object { $_ -like "-I*$devGen" }).Count -ne 1) { Fail "game flags: expected exactly one -I...$devGen to point at the variant" }
if (@($GameFlagsFull | Where-Object { $_ -match 'cmake_pch|^-include|^-c$|^-o$|legodimensions_recomp\.61' }).Count) { Fail "game flags still hold a CMake PCH / -c / -o token: $(($GameFlagsFull | Where-Object { $_ -match 'cmake_pch|^-include|^-c$|^-o$|legodimensions_recomp\.61' }) -join ' ')" }
if (-not (@($GameFlagsFull) -ccontains '-O3')) { Fail 'game flags: no -O3 (not the Release entry?)' }
$rows.Add('flags: build/dev/compile_commands.json Release entry of legodimensions_recomp.61.cpp (the one env/compile-one.ps1 picks), -I<generated> -> variant dir, CMake PCH -> per-variant PCH of its own legodimensions_pch.h:')
$rows.Add('  ' + ((Get-FlagsFor '<variant>') -join ' '))
$rows.Add("workers: $Workers (each clang run holds one Agent 9 slot)")
$rows.Add("baseline legodimensions_pch.h identical to off3: $((Get-Sha (Join-Path $baseDir 'legodimensions_pch.h')) -eq (Get-Sha (Join-Path $off3Dir 'legodimensions_pch.h')))")
Save

# baseline TUs: function lists, split/join self-test, identity with off3
$need = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
$info = New-Object System.Collections.Generic.List[object]
foreach ($n in $tuList) {
  $f = Join-Path $baseDir "legodimensions_recomp.$n.cpp"
  if (-not (Test-Path $f)) { Fail "baseline TU $n not found: $f" }
  $s = [IO.File]::ReadAllText($f)
  $sp = Split-Tu $s
  $names = @($sp.chunks | ForEach-Object { $_.name })
  if (@($names | Select-Object -Unique).Count -ne $names.Count) { Fail "baseline TU $n defines a function twice" }
  $rebuilt = Join-Tu (Get-IncludeLines $sp.pre "baseline TU $n") @($sp.chunks | ForEach-Object { $_.text })
  if (-not ($rebuilt -ceq $s)) { Fail "self-test: rebuilding baseline TU $n from its own chunks is not byte-identical" }
  $o3 = @("legodimensions_recomp.$n.cpp", "legodimensions_funcs.$n.h" | Where-Object { (Get-Sha (Join-Path $baseDir $_)) -eq (Get-Sha (Join-Path $off3Dir $_)) }).Count -eq 2
  foreach ($x in $names) { [void]$need.Add($x) }
  $info.Add([pscustomobject]@{ n = $n; base = $f; names = $names; baseBytes = (Get-Item $f).Length; baseMt = $reMt.Matches($s).Count; off3 = $o3
      batch = (Join-Path $out "batch_tu$n.cpp"); batchBytes = 0; batchMt = 0 })
  $rows.Add("baseline TU ${n}: $($names.Count) functions, $((Get-Item $f).Length) B; split/join self-test byte-identical: True; TU and funcs header identical to off3: $o3")
}
Save

# batch variant: the needed function bodies, where they live, and every TU's preamble
$bodies = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([StringComparer]::Ordinal)
$fnTu = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([StringComparer]::Ordinal)
$pre = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([StringComparer]::Ordinal)
$dups = New-Object System.Collections.Generic.List[string]
$tuFns = @{}; $tuLen = @{}
$scan = Invoke-InSlot {
  $sw = [Diagnostics.Stopwatch]::StartNew(); $files = 0; $fns = 0
  foreach ($bf in Get-ChildItem $batchDir -Filter 'legodimensions_recomp.*.cpp') {
    $bs = [IO.File]::ReadAllText($bf.FullName); $files++
    $ms = $reFn.Matches($bs)
    $fns += $ms.Count
    $tuFns[$bf.Name] = $ms.Count; $tuLen[$bf.Name] = $bf.Length
    if ($ms.Count -eq 0) { continue }
    $pre[$bf.Name] = $bs.Substring(0, $ms[0].Index)
    for ($i = 0; $i -lt $ms.Count; $i++) {
      $nm = $ms[$i].Groups[1].Value
      if (-not $need.Contains($nm)) { continue }
      $end = if ($i + 1 -lt $ms.Count) { $ms[$i + 1].Index } else { $bs.Length }
      if ($bodies.ContainsKey($nm)) { $dups.Add($nm) }
      $bodies[$nm] = $bs.Substring($ms[$i].Index, $end - $ms[$i].Index)
      $fnTu[$nm] = $bf.Name
    }
  }
  '{0} batch recomp TUs ({1} functions) scanned in {2:n1}s' -f $files, $fns, $sw.Elapsed.TotalSeconds
}
Note $scan
if ($dups.Count) { Fail "functions defined twice in the batch variant: $(($dups | Select-Object -First 10) -join ', ')" }

# gen_out/batch_tuN.cpp
foreach ($e in $info) {
  $missing = @($e.names | Where-Object { -not $bodies.ContainsKey($_) })
  if ($missing.Count) { Fail "the batch variant lacks $($missing.Count) of baseline TU $($e.n)'s $($e.names.Count) functions, e.g. $(($missing | Select-Object -First 10) -join ', ')" }
  # each copied chunk must be one whole function and carry no file-scope preprocessor state of a neighbour
  foreach ($x in $e.names) {
    $b = $bodies[$x]
    if (-not $b.TrimEnd().EndsWith('}')) { Fail "batch chunk of $x ($($fnTu[$x])) does not end with '}'" }
    $pp = @([regex]::Matches($b, '(?m)^[ \t]*#[ \t]*(\w+)') | ForEach-Object { $_.Groups[1].Value })
    if (@($pp | Where-Object { $_ -in 'define', 'undef', 'include', 'pragma' }).Count) { Fail "batch chunk of $x ($($fnTu[$x])) holds #$(($pp | Select-Object -Unique) -join '/#') lines" }
    if (@($pp | Where-Object { $_ -like 'if*' }).Count -ne @($pp | Where-Object { $_ -eq 'endif' }).Count) { Fail "batch chunk of $x ($($fnTu[$x])) has unbalanced #if/#endif" }
  }
  $src = New-Object System.Collections.Generic.List[string]
  foreach ($x in $e.names) { if (-not $src.Contains($fnTu[$x])) { $src.Add($fnTu[$x]) } }
  $inc = New-Object System.Collections.Generic.List[string]
  foreach ($k in $src) { foreach ($l in (Get-IncludeLines $pre[$k] "batch $k")) { if (-not $inc.Contains($l)) { $inc.Add($l) } } }
  $t = Join-Tu $inc @($e.names | ForEach-Object { $bodies[$_] })
  [IO.File]::WriteAllText($e.batch, $t)
  $e.batchBytes = (Get-Item $e.batch).Length; $e.batchMt = $reMt.Matches($t).Count
  $rows.Add(('TU {0}: {1} functions; baseline {2:n0} B, {3} musttail sites; batch_tu{0}.cpp {4:n0} B ({5:p1} of baseline), {6} musttail sites; its functions come from {7} batch TUs ({8} funcs-header #includes): {9}' -f $e.n, $e.names.Count, $e.baseBytes, $e.baseMt, $e.batchBytes, ($e.batchBytes / $e.baseBytes), $e.batchMt, $src.Count, $inc.Count, (($src | ForEach-Object { $_ -replace '^legodimensions_recomp\.|\.cpp$', '' }) -join ',')))
}
Save

# one PCH per variant, from its own legodimensions_pch.h, same flags
$pch = @{ baseline = (Join-Path $out 'hb_pch_baseline.pch'); batch = (Join-Path $out 'hb_pch_batch.pch') }
$jobs = @(foreach ($v in 'baseline', 'batch') {
    $dir = if ($v -eq 'baseline') { $baseDir } else { $batchDir }
    Remove-Item $pch[$v] -ErrorAction SilentlyContinue
    @{ key = "pch/$v"; cargs = @(Get-FlagsFor $dir) + @('-x', 'c++-header', (Join-Path $dir 'legodimensions_pch.h'), '-o', $pch[$v]); err = (Join-Path $out "hb_pch_$v.err") }
  })
$r = Invoke-ClangJobs $jobs
foreach ($v in 'baseline', 'batch') {
  $x = $r["pch/$v"]
  if ($x.code -ne 0 -or -not (Test-Path $pch[$v])) { Fail "PCH build for $v failed, exit $($x.code) (gen_out/hb_pch_$v.err)" }
  Note ('PCH {0}: wall {1:n1}s, CPU {2:n1}s, {3:n0} B' -f $v, $x.wall, $x.cpu, (Get-Item $pch[$v]).Length)
}
Save

# the compiles, interleaved so each TU's pair runs at about the same time on 2 workers
$jobs = New-Object System.Collections.Generic.List[object]
$i = 0
foreach ($e in $info) {
  $pair = if ($i % 2) { 'batch', 'baseline' } else { 'baseline', 'batch' }
  foreach ($v in $pair) {
    $obj = Join-Path $out "hb_${v}_tu$($e.n).obj"
    Remove-Item $obj -ErrorAction SilentlyContinue
    $srcFile = if ($v -eq 'baseline') { $e.base } else { $e.batch }
    $dir = if ($v -eq 'baseline') { $baseDir } else { $batchDir }
    $jobs.Add(@{ key = "$($e.n)/$v"; cargs = @(Get-FlagsFor $dir) + @('-include-pch', $pch[$v], '-c', $srcFile, '-o', $obj); err = (Join-Path $out "hb_${v}_tu$($e.n).err"); obj = $obj })
  }
  $i++
}
Note "compiling $($jobs.Count) TUs on $Workers worker(s)"
$res = Invoke-ClangJobs $jobs.ToArray()
$rows.Add('')
$rows.Add('| TU | variant | source bytes | functions | musttail sites | exit | wall s | CPU s | .obj bytes | .text bytes |')
$rows.Add('|---|---|---:|---:|---:|---:|---:|---:|---:|---:|')
$m = @{}
foreach ($e in $info) {
  foreach ($v in 'baseline', 'batch') {
    $x = $res["$($e.n)/$v"]
    $obj = Join-Path $out "hb_${v}_tu$($e.n).obj"
    $ob = if (Test-Path $obj) { (Get-Item $obj).Length } else { 0 }
    $tb = if ($x.code -eq 0 -and $ob) { Get-TextBytes $obj } else { 0 }
    $bytes = if ($v -eq 'baseline') { $e.baseBytes } else { $e.batchBytes }
    $mt = if ($v -eq 'baseline') { $e.baseMt } else { $e.batchMt }
    $m["$($e.n)/$v"] = [pscustomobject]@{ code = [int]$x.code; wall = [double]$x.wall; cpu = [double]$x.cpu; obj = [double]$ob; text = [double]$tb }
    $rows.Add(('| {0} | {1} | {2:n0} | {3} | {4} | {5} | {6:n1} | {7:n1} | {8:n0} | {9:n0} |' -f $e.n, $v, $bytes, $e.names.Count, $mt, $x.code, $x.wall, $x.cpu, $ob, $tb))
    if ($x.code) { $rows.Add("  ^ clang failed: gen_out/hb_${v}_tu$($e.n).err") }
  }
}
$rows.Add('')
$sa = @{ cpu = 0.0; wall = 0.0; obj = 0.0; text = 0.0 }; $sb2 = @{ cpu = 0.0; wall = 0.0; obj = 0.0; text = 0.0 }; $ok = 0
foreach ($e in $info) {
  $a = $m["$($e.n)/baseline"]; $b = $m["$($e.n)/batch"]
  if ($a.code -ne 0 -or $b.code -ne 0 -or $a.cpu -le 0 -or $a.obj -le 0 -or $a.text -le 0) { continue }
  $ok++
  foreach ($k in 'cpu', 'wall', 'obj', 'text') { $sa[$k] += $a.$k; $sb2[$k] += $b.$k }
  $rows.Add(('TU {0}: batch/baseline  CPU {1:p0}  wall {2:p0}  .obj {3:p0}  .text {4:p0}' -f $e.n, ($b.cpu / $a.cpu), ($b.wall / $a.wall), ($b.obj / $a.obj), ($b.text / $a.text)))
}
if ($ok) { $rows.Add(('all {0} TUs: batch/baseline  CPU {1:n1}s/{2:n1}s = {3:p0}  wall {4:p0}  .obj {5:p0}  .text {6:p0}' -f $ok, $sb2.cpu, $sa.cpu, ($sb2.cpu / $sa.cpu), ($sb2.wall / $sa.wall), ($sb2.obj / $sa.obj), ($sb2.text / $sa.text))) }
Save

# for reference: the real batch TU holding the largest share of each baseline TU's code, compiled as-is
if (-not $NoWhole) {
  $wjobs = New-Object System.Collections.Generic.List[object]; $winfo = @{}
  foreach ($e in $info) {
    $share = @{}; $cnt = @{}; $tot = 0.0
    foreach ($x in $e.names) { $k = $fnTu[$x]; $len = $bodies[$x].Length; $share[$k] = [double]$share[$k] + $len; $cnt[$k] = [int]$cnt[$k] + 1; $tot += $len }
    $top = @($share.Keys | Sort-Object { - $share[$_] })[0]
    $obj = Join-Path $out "hb_whole_tu$($e.n).obj"
    Remove-Item $obj -ErrorAction SilentlyContinue
    $wf = Join-Path $batchDir $top
    $winfo["$($e.n)"] = [pscustomobject]@{ k = $top; fromN = $cnt[$top]; share = $share[$top] / $tot; obj = $obj; mt = $reMt.Matches([IO.File]::ReadAllText($wf)).Count }
    $wjobs.Add(@{ key = "whole/$($e.n)"; cargs = @(Get-FlagsFor $batchDir) + @('-include-pch', $pch['batch'], '-c', $wf, '-o', $obj); err = (Join-Path $out "hb_whole_tu$($e.n).err") })
  }
  Note "compiling $($wjobs.Count) whole batch TUs on $Workers worker(s)"
  $wres = Invoke-ClangJobs $wjobs.ToArray()
  $rows.Add('')
  $rows.Add('For reference: the real batch TU that holds the largest share of each baseline TU''s functions, compiled as-is (batch PCH, same flags). Its function set differs from TU N, so compare per function set with the table above.')
  $rows.Add('| baseline TU | batch TU (as-is) | bytes | functions | of them from TU N | share of TU N''s functions (batch bytes) | musttail sites | exit | wall s | CPU s | .obj bytes | .text bytes |')
  $rows.Add('|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
  foreach ($e in $info) {
    $wi = $winfo["$($e.n)"]; $x = $wres["whole/$($e.n)"]
    $ob = if (Test-Path $wi.obj) { (Get-Item $wi.obj).Length } else { 0 }
    $tb = if ($x.code -eq 0 -and $ob) { Get-TextBytes $wi.obj } else { 0 }
    $rows.Add(('| {0} | {1} | {2:n0} | {3} | {4} | {5:p1} | {6} | {7} | {8:n1} | {9:n1} | {10:n0} | {11:n0} |' -f $e.n, ($wi.k -replace '^legodimensions_recomp\.|\.cpp$', ''), $tuLen[$wi.k], $tuFns[$wi.k], $wi.fromN, $wi.share, $wi.mt, $x.code, $x.wall, $x.cpu, $ob, $tb))
    if ($x.code) { $rows.Add("  ^ clang failed: gen_out/hb_whole_tu$($e.n).err") }
  }
  Save
}
$rows

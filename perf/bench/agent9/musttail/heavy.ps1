# Full -O2 compile (real game flags) of the 3 heaviest recomp TUs (by bytes) of the baseline
# (build/agent2/gen-noflag), without and with musttail. Holds no slot itself: every clang run and
# every objdump parse takes ONE Agent 9 slot for itself (slot1.ps1, same rules as cpu2.ps1; waits
# while bench/agent9/QUIET exists).
# The musttail side is the musttail variant's TU when it holds the same functions; otherwise the
# baseline TU with every plain tail call rewritten exactly as emit_tail_call prints it
# (textcheck.ps1 checks that rewrite against the generator's musttail output, function by function).
# Reports wall and CPU seconds, .obj size, and from llvm-objdump -d -r: guest tail jumps (jmp/jcc
# with a guest relocation), guest calls, and guest calls followed only by epilogue instructions and
# ret (tail calls clang did not lower).
#   powershell -NoProfile -File bench/agent9/musttail/heavy.ps1 *> bench/agent9/musttail/heavy.log
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
. (Join-Path $root 'env/devshell.ps1') | Out-Null
. (Join-Path $PSScriptRoot 'game_flags.ps1')
. (Join-Path $PSScriptRoot 'slot1.ps1')
$out = Join-Path $PSScriptRoot 'gen_out'
New-Item -ItemType Directory -Force $out | Out-Null
$tus = 'legodimensions_recomp.304.cpp', 'legodimensions_recomp.233.cpp', 'legodimensions_recomp.52.cpp'
$baseDir = Join-Path $root 'build/agent2/gen-noflag/default'
$mtDir = Join-Path $root 'build/agent9/generated/musttail/default'
$devGen = 'DimensionsRecomp/rexlego/generated/default'
$guest = '^(sub_[0-9A-Fa-f]+|__imp__\w+|__rest\w+|__save\w+)$'
$reU = [regex]'(?m)^\t([A-Za-z_][A-Za-z0-9_]*)\(ctx, base\);\r?\n\treturn;'
$reC = [regex]'(?m)^\t\t([A-Za-z_][A-Za-z0-9_]*)\(ctx, base\);\r?\n\t\treturn;'
$reFn = [regex]'(?m)^DEFINE_REX_FUNC\((\w+)\)'
$reMt = [regex]'\[\[clang::musttail\]\]'
$outTxt = Join-Path $PSScriptRoot 'heavy.txt'
function Get-FlagsFor([string]$dir) { @($GameFlags | ForEach-Object { if ($_ -like "-I*$devGen") { '-I' + ($dir -replace '\\', '/') } else { $_ } }) }

function Get-ObjStats([string]$obj) {
  $st = [ordered]@{ functions = 0; tail_jmp = 0; tail_jcc = 0; call_guest = 0; call_then_ret = 0; ret = 0 }
  $mn = New-Object System.Collections.Generic.List[string]
  $op = New-Object System.Collections.Generic.List[string]
  $tg = New-Object System.Collections.Generic.List[string]
  $reRel = [regex]'IMAGE_REL_AMD64_\w+\s+(\S+)\s*$'
  $reSym = [regex]'^[0-9a-f]+ <([^>]+)>:'
  $reIns = [regex]'^\s+[0-9a-f]+:\s+([a-z][a-z0-9]*)\s*(.*)$'
  foreach ($l in (& llvm-objdump -d -r --no-show-raw-insn --x86-asm-syntax=intel $obj)) {
    $x = $reRel.Match($l)
    if ($x.Success) { if ($tg.Count) { $tg[$tg.Count - 1] = $x.Groups[1].Value }; continue }
    $x = $reSym.Match($l)
    if ($x.Success) { if ($x.Groups[1].Value.StartsWith('__imp__sub_', [StringComparison]::Ordinal)) { $st.functions++ }; $mn.Add('<fn>'); $op.Add(''); $tg.Add($null); continue }
    $x = $reIns.Match($l)
    if ($x.Success) { $mn.Add($x.Groups[1].Value); $op.Add($x.Groups[2].Value); $tg.Add($null) }
  }
  $n = $mn.Count
  for ($i = 0; $i -lt $n; $i++) {
    $m = $mn[$i]
    if ($m -ceq 'ret') { $st.ret++; continue }
    $t = $tg[$i]
    if (-not $t -or $t -notmatch $guest) { continue }
    if ($m -ceq 'jmp') { $st.tail_jmp++; continue }
    if ($m.StartsWith('j')) { $st.tail_jcc++; continue }
    if ($m -ceq 'call') {
      $st.call_guest++
      for ($j = $i + 1; $j -lt $n; $j++) {
        $y = $mn[$j]; $o = $op[$j]
        if ($y -ceq 'ret') { $st.call_then_ret++; break }
        if ($y -ceq 'nop' -or $y -ceq 'pop' -or $y -ceq 'vzeroupper' -or
          (($y -ceq 'add' -or $y -ceq 'lea') -and $o.StartsWith('rsp,')) -or
          ($y -cmatch '^v?mov(aps|ups|dqa)$' -and $o -match '^xmm\d+, xmmword ptr \[rsp')) { continue }
        break
      }
    }
  }
  [pscustomobject]$st
}

$rows = @("heavy TUs (largest baseline recomp TUs by bytes), -O2 + real game flags, one clang at a time on one Agent 9 slot; counts from llvm-objdump -d -r")
$rows += "baseline: $baseDir"
foreach ($tu in $tus) {
  $id = $tu -replace '^legodimensions_recomp\.|\.cpp$', ''
  $bPath = Join-Path $baseDir $tu
  $b = [IO.File]::ReadAllText($bPath)
  $t = $reC.Replace($reU.Replace($b, "`t[[clang::musttail]] return `$1(ctx, base);"), "`t`t[[clang::musttail]] return `$1(ctx, base);")
  $fb = @($reFn.Matches($b) | ForEach-Object { $_.Groups[1].Value }) -join ','
  $mPath = Join-Path $mtDir $tu
  $m = if (Test-Path $mPath) { [IO.File]::ReadAllText($mPath) } else { '' }
  $fm = @($reFn.Matches($m) | ForEach-Object { $_.Groups[1].Value }) -join ','
  if ($fb -ceq $fm) {
    $mtSrc = $mPath; $mtInc = $mtDir
    $how = "the musttail variant's own $tu (same functions; equals rewritten baseline text: $($t -ceq $m))"
  } else {
    $mtSrc = Join-Path $out "heavy_mt_$id.cpp"; $mtInc = $baseDir
    [IO.File]::WriteAllText($mtSrc, $t)
    $how = "baseline $tu with its tail calls rewritten to the musttail text (the musttail variant's $tu holds other functions: the TU partition differs)"
  }
  $rows += "$tu : $($b.Length) bytes, $($reFn.Matches($b).Count) functions, plain tail sites $($reU.Matches($b).Count + $reC.Matches($b).Count), musttail sites after rewrite $($reMt.Matches($t).Count); musttail side = $how"
  foreach ($v in 'baseline', 'musttail') {
    if ($v -eq 'baseline') { $src = $bPath; $inc = $baseDir } else { $src = $mtSrc; $inc = $mtInc }
    $obj = Join-Path $out "heavy_${v}_$id.obj"
    $r = Invoke-ClangInSlot (@(Get-FlagsFor $inc) + @('-O2', '-c', $src, '-o', $obj)) (Join-Path $out "heavy_${v}_$id.err")
    if ($r.code) { $rows += ('  {0,-8} -O2: clang exit={1} (see gen_out/heavy_{0}_{2}.err)' -f $v, $r.code, $id); $rows | Set-Content -Encoding ascii $outTxt; continue }
    $size = (Get-Item $obj).Length
    $st = Invoke-InSlot { Get-ObjStats $obj }
    $rows += ('  {0,-8} -O2: wall={1,6:n1}s cpu={2,6:n1}s obj={3,9} B functions={4} tail_jmp={5} tail_jcc={6} call_guest={7} call_then_ret={8} ret={9}' -f $v, $r.wall, $r.cpu, $size, $st.functions, $st.tail_jmp, $st.tail_jcc, $st.call_guest, $st.call_then_ret, $st.ret)
    $rows | Set-Content -Encoding ascii $outTxt
  }
}
$rows | Tee-Object -FilePath $outTxt

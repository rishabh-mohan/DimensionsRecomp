# musttail proof on real generated code: one LEGO TU compiled with the real game flags, as
# generated today and with the musttail_calls text. The text transform is exactly what
# emit_tail_call / emit_tail_call_line print with the flag on for LEGO (no SEH_TRY body, no
# setjmp anywhere, so every plain tail call is rewritten; the other forms do not match).
#   powershell -NoProfile -File bench/agent9/cpu2.ps1 -File bench/agent9/musttail/real_tu.ps1 *> bench/agent9/musttail/real_tu.log
param([string]$Tu = 'legodimensions_recomp.61.cpp', [string[]]$Opt = @('-O3', '-O0'))
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
. (Join-Path $root 'env/devshell.ps1') | Out-Null
. (Join-Path $PSScriptRoot 'game_flags.ps1')
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force gen_out | Out-Null
$src = Join-Path $root "DimensionsRecomp/rexlego/generated/default/$Tu"
$s = [IO.File]::ReadAllText($src)
$reU = [regex]'(?m)^\t([A-Za-z_][A-Za-z0-9_]*)\(ctx, base\);\r?\n\treturn;'
$reC = [regex]'(?m)^\t\t([A-Za-z_][A-Za-z0-9_]*)\(ctx, base\);\r?\n\t\treturn;'
$nU = $reU.Matches($s).Count
$nC = $reC.Matches($s).Count
$nF = ([regex]'(?m)^DEFINE_REX_FUNC\(').Matches($s).Count
$t = $reU.Replace($s, "`t[[clang::musttail]] return `$1(ctx, base);")
$t = $reC.Replace($t, "`t`t[[clang::musttail]] return `$1(ctx, base);")
$mt = Join-Path $PSScriptRoot "gen_out/mt_$Tu"
[IO.File]::WriteAllText($mt, $t)
$lines = @("TU $Tu : $nF functions, tail-call sites rewritten: $nU unconditional (b) + $nC conditional/jump-table")

function Get-AsmStats([string]$path) {
  $a = [IO.File]::ReadAllLines((Join-Path $PSScriptRoot $path))  # .NET cwd != Set-Location
  $st = [ordered]@{ functions = 0; jmp_guest = 0; call_guest = 0; call_then_ret = 0; ret = 0; push_rbp_or_sub_rsp = 0 }
  $guest = '(sub_[0-9A-F]+|__imp__\w+|__rest\w+|__save\w+)'
  for ($i = 0; $i -lt $a.Count; $i++) {
    $l = $a[$i]
    if ($l -match '^__imp__sub_[0-9A-F]+:') { $st.functions++ ; continue }
    if ($l -notmatch '^\s+[a-z]' -or $l -match '^\s+\.') { continue }
    if ($l -match "^\s+jmp\s+$guest\b") { $st.jmp_guest++ }
    elseif ($l -match '^\s+ret\b') { $st.ret++ }
    elseif ($l -match '^\s+sub\s+rsp,') { $st.push_rbp_or_sub_rsp++ }
    elseif ($l -match "^\s+call\s+$guest\b") {
      $st.call_guest++
      # call followed only by epilogue instructions and ret (a tail call that was not lowered to jmp)
      for ($j = $i + 1; $j -lt $a.Count; $j++) {
        $m = $a[$j]
        if ($m -notmatch '^\s+[a-z]' -or $m -match '^\s+\.') {
          if ($m -match '^\S' -and $m -notmatch '^#') { break }  # a label: other paths join here
          continue
        }
        if ($m -match '^\s+ret\b') { $st.call_then_ret++; break }
        if ($m -match '^\s+(add\s+rsp|lea\s+rsp|pop\s|nop|vzeroupper)') { continue }
        break
      }
    }
  }
  [pscustomobject]$st
}

foreach ($o in $Opt) {
  foreach ($v in @(@{ n = 'today'; f = $src }, @{ n = 'musttail'; f = $mt })) {
    $asmOut = "gen_out/$($v.n)_$($o.TrimStart('-'))_$($Tu -replace '\.cpp$', '').s"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & clang++ @GameFlags $o -S -masm=intel $v.f -o $asmOut
    $code = $LASTEXITCODE
    $secs = [math]::Round($sw.Elapsed.TotalSeconds, 1)
    if ($code) { $lines += "$o $($v.n): clang exit=$code ($secs s)"; continue }
    $st = Get-AsmStats $asmOut
    $lines += ('{0} {1,-8}: {2,5}s  functions={3} jmp_guest={4} call_guest={5} call_then_ret={6} ret={7} sub_rsp={8}' -f `
        $o, $v.n, $secs, $st.functions, $st.jmp_guest, $st.call_guest, $st.call_then_ret, $st.ret, $st.push_rbp_or_sub_rsp)
  }
}
$lines | Tee-Object -FilePath real_tu.txt

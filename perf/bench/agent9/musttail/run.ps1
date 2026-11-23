# musttail proof, quick part. One clang at a time; run it while holding a CPU slot:
#   powershell -NoProfile -File bench/agent9/cpu2.ps1 -File bench/agent9/musttail/run.ps1 *> bench/agent9/musttail/run.log
#  1. emit_test: the live helpers of context.cpp, text in every case (emit_test.out.txt)
#  2. proof.cpp: generated-style functions with the real LEGO pch and game flags, today's text vs
#     musttail text, -O2 and -O0 (+ -fstack-protector-strong), call/jmp/ret per function
#     (proof_counts.txt, asm in gen_out/proof_*.s)
#  3. acceptance: neg_*.cpp must be rejected, pos_restrict.cpp accepted (acceptance.txt)
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
. (Join-Path $root 'env/devshell.ps1') | Out-Null
. (Join-Path $PSScriptRoot 'game_flags.ps1')
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force gen_out | Out-Null
$sdk = Join-Path $root 'DimensionsRecomp/rexglue-sdk'
$fail = 0

Write-Host '== 1. emit_test (text) =='
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'extract_helpers.ps1')
& clang++ -std=c++20 -O1 emit_test.cpp -o gen_out/emit_test.exe
if ($LASTEXITCODE) { Write-Host 'emit_test build failed'; $fail++ }
else {
  & (Join-Path $PSScriptRoot 'gen_out/emit_test.exe') | Tee-Object -FilePath emit_test.out.txt
  if ($LASTEXITCODE) { $fail++ }
}

Write-Host '== 2. proof.cpp (asm) =='
function Get-TailStats([string]$asmPath, [string[]]$fns) {
  # .NET resolves relative paths against the process cwd, not Set-Location: make it absolute
  $asm = [IO.File]::ReadAllLines((Join-Path $PSScriptRoot $asmPath))
  foreach ($fn in $fns) {
    $i = -1
    for ($k = 0; $k -lt $asm.Count; $k++) { if ($asm[$k] -match "^${fn}:") { $i = $k; break } }
    $r = [ordered]@{ fn = $fn -replace '^__imp__', ''; instr = -1; call_callee = -1; jmp_callee = -1; ret = -1 }
    if ($i -ge 0) {
      $r.instr = 0; $r.call_callee = 0; $r.jmp_callee = 0; $r.ret = 0
      for ($j = $i + 1; $j -lt $asm.Count; $j++) {
        $l = $asm[$j]
        if ($l -match '# -- End function' -or $l -match '^\s*\.seh_endproc') { break }
        if ($l -match '^\s+[a-z]' -and $l -notmatch '^\s+\.') {
          $r.instr++
          if ($l -match '^\s+call\s+callee_') { $r.call_callee++ }
          if ($l -match '^\s+jmp\s+callee_') { $r.jmp_callee++ }
          if ($l -match '^\s+ret\b') { $r.ret++ }
        }
      }
    }
    [pscustomobject]$r
  }
}
$fns = 'ctx_regs', 'locals', 'escaped', 'cond', 'switch', 'vector' | ForEach-Object { "__imp__proof_$_" }
$variants = @(
  @{ name = 'O2_today';    args = @('-O2', '-DMUSTTAIL=0') },
  @{ name = 'O2_musttail'; args = @('-O2', '-DMUSTTAIL=1') },
  @{ name = 'O0_today';    args = @('-O0', '-DMUSTTAIL=0') },
  @{ name = 'O0_musttail'; args = @('-O0', '-DMUSTTAIL=1') },
  @{ name = 'O2_musttail_stackprotector'; args = @('-O2', '-DMUSTTAIL=1', '-fstack-protector-strong') }
)
$report = @()
foreach ($v in $variants) {
  $asmOut = "gen_out/proof_$($v.name).s"
  $sw = [Diagnostics.Stopwatch]::StartNew()
  & clang++ @GameFlags @($v.args) -S -masm=intel proof.cpp -o $asmOut
  $code = $LASTEXITCODE
  $report += "---- $($v.name): clang++ <game flags> $($v.args -join ' ') -S  exit=$code  $([math]::Round($sw.Elapsed.TotalSeconds, 1))s"
  if ($code) { $fail++; continue }
  $report += (Get-TailStats $asmOut $fns | Format-Table -AutoSize | Out-String -Width 200).TrimEnd()
}
$report | Tee-Object -FilePath proof_counts.txt

Write-Host '== 3. acceptance (-fsyntax-only) =='
$checks = @(
  @{ f = 'neg_tracy.cpp'; expect = 'reject'; extra = @('-DREXGLUE_PROFILE_GUEST_FUNCTIONS', '-DREXGLUE_ENABLE_PROFILING', '-DTRACY_ENABLE', "-I$sdk/thirdparty/tracy/public") },
  @{ f = 'neg_seh.cpp'; expect = 'reject'; extra = @() },
  @{ f = 'neg_try.cpp'; expect = 'reject'; extra = @() },
  @{ f = 'neg_sig.cpp'; expect = 'reject'; extra = @() },
  @{ f = 'pos_restrict.cpp'; expect = 'accept'; extra = @() }
)
$acc = @()
foreach ($c in $checks) {
  $cmdline = 'clang++ ' + (($GameFlags + $c.extra) -join ' ') + " -O2 -fsyntax-only $($c.f) 2>&1"
  $out = @(cmd /c $cmdline)
  $code = $LASTEXITCODE
  $ok = ($c.expect -eq 'reject' -and $code -ne 0) -or ($c.expect -eq 'accept' -and $code -eq 0)
  if (-not $ok) { $fail++ }
  $acc += "---- $($c.f): expect $($c.expect), exit=$code -> $(if ($ok) { 'OK' } else { 'UNEXPECTED' })"
  $acc += @($out | Where-Object { $_ -match 'error:|note:' } | ForEach-Object { '  ' + ($_ -replace '^.*[\\/]', '') })
}
$acc | Tee-Object -FilePath acceptance.txt
Write-Host "musttail run.ps1 done, failures: $fail"
exit $fail

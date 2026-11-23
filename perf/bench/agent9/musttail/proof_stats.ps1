# Text only (no compile): per-function call/jmp/ret counts from the existing gen_out/proof_*.s
# (written by run.ps1 step 2) -> proof_counts.txt, plus asm excerpts -> proof_asm_excerpt.txt
#   powershell -NoProfile -File bench/agent9/musttail/proof_stats.ps1
$ErrorActionPreference = 'Stop'
$out = Join-Path $PSScriptRoot 'gen_out'
$fns = 'ctx_regs', 'locals', 'escaped', 'cond', 'switch', 'vector' | ForEach-Object { "__imp__proof_$_" }
$variants = 'O2_today', 'O2_musttail', 'O0_today', 'O0_musttail', 'O2_musttail_stackprotector'

function Get-Body([string[]]$asm, [string]$fn) {
  $i = -1
  for ($k = 0; $k -lt $asm.Count; $k++) { if ($asm[$k] -match "^${fn}:") { $i = $k; break } }
  if ($i -lt 0) { return $null }
  $body = New-Object System.Collections.Generic.List[string]
  for ($j = $i; $j -lt $asm.Count; $j++) {
    $l = $asm[$j]
    if ($j -gt $i -and ($l -match '# -- End function' -or $l -match '^\s*\.seh_endproc')) { break }
    $body.Add($l)
  }
  return $body
}

$report = @()
$excerpt = @()
foreach ($v in $variants) {
  $path = Join-Path $out "proof_$v.s"
  if (-not (Test-Path $path)) { $report += "---- ${v}: missing $path"; continue }
  $asm = [IO.File]::ReadAllLines($path)
  $rows = foreach ($fn in $fns) {
    $b = Get-Body $asm $fn
    $r = [ordered]@{ variant = $v; fn = $fn -replace '^__imp__', ''; instr = -1; call_callee = -1; jmp_callee = -1; ret = -1; stack_adj = -1 }
    if ($b) {
      $r.instr = 0; $r.call_callee = 0; $r.jmp_callee = 0; $r.ret = 0; $r.stack_adj = 0
      foreach ($l in $b) {
        if ($l -match '^\s+[a-z]' -and $l -notmatch '^\s+\.') {
          $r.instr++
          if ($l -match '^\s+call\s+callee_') { $r.call_callee++ }
          if ($l -match '^\s+jmp\s+callee_') { $r.jmp_callee++ }
          if ($l -match '^\s+ret\b') { $r.ret++ }
          if ($l -match '^\s+(sub|add)\s+rsp,') { $r.stack_adj++ }
        }
      }
    }
    [pscustomobject]$r
  }
  $report += "---- $v"
  $report += ($rows | Format-Table -AutoSize | Out-String -Width 200).TrimEnd()
  if ($v -in 'O2_today', 'O2_musttail', 'O0_today', 'O0_musttail') {
    foreach ($fn in '__imp__proof_escaped', '__imp__proof_cond') {
      $b = Get-Body $asm $fn
      $excerpt += "==== $v  $fn"
      $excerpt += @($b | Where-Object { $_ -notmatch '^\s+\.(seh_|p2align|cfi_)' })
    }
  }
}
$report | Set-Content -Encoding ascii (Join-Path $PSScriptRoot 'proof_counts.txt')
$excerpt | Set-Content -Encoding ascii (Join-Path $PSScriptRoot 'proof_asm_excerpt.txt')
$report

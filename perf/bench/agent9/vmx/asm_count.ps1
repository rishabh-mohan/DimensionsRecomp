# Instruction counts of the old/new distinct-operand kernels in harness_<config>.s
# (written by run.ps1). Pure text processing, no compiler: no CPU slot needed.
#   powershell -NoProfile -File bench/agent9/vmx/asm_count.ps1 [-Configs sse41,v3]
# A kernel is the text from its `k_<op>_distinct_<form>:` label (clang appends
# `# @name`) to `# -- End function`; an instruction is an indented line
# that is not a directive. The count includes the loads from / stores to ctx.
param([string[]]$Configs = @('sse41', 'v3'))
Set-Location $PSScriptRoot
foreach ($c in $Configs) {
  $asm = Get-Content "harness_$c.s"
  $rows = foreach ($op in 'vsubsws', 'vsrb', 'vsrab', 'vrlw', 'vsraw', 'vsrw', 'vpkuhus', 'vpkuwus') {
    $n = @{}
    foreach ($form in 'old', 'new') {
      $re = "^k_${op}_distinct_${form}:"
      $i = -1
      for ($k = 0; $k -lt $asm.Count; $k++) { if ($asm[$k] -match $re) { $i = $k; break } }
      $count = -1
      if ($i -ge 0) {
        $count = 0
        for ($j = $i + 1; $j -lt $asm.Count; $j++) {
          $l = $asm[$j]
          if ($l -match '# -- End function' -or $l -match '^\s*\.seh_endproc' -or $l -match '^\.Lfunc_end') { break }
          if ($l -match '^\s+[a-z]' -and $l -notmatch '^\s+\.') { $count++ }
        }
      }
      $n[$form] = $count
    }
    '{0,-8} old {1,3} instr  new {2,3} instr' -f $op, $n['old'], $n['new']
  }
  Write-Host "== asm $c =="
  $rows | Tee-Object -FilePath "asm_$c.txt"
}

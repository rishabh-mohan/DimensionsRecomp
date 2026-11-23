# Print the asm of the old/new distinct-operand kernels from harness_<config>.s to
# asm_kernels_<config>.txt (text processing only, no compiler).
#   powershell -NoProfile -File bench/agent9/vmx/asm_dump.ps1 [-Configs sse41,v3]
param([string[]]$Configs = @('sse41', 'v3'))
Set-Location $PSScriptRoot
foreach ($c in $Configs) {
  $asm = Get-Content "harness_$c.s"
  $out = foreach ($op in 'vsubsws', 'vsrb', 'vsrab', 'vrlw', 'vsraw', 'vsrw', 'vpkuhus', 'vpkuwus') {
    foreach ($form in 'old', 'new') {
      $re = "^k_${op}_distinct_${form}:"
      $i = -1
      for ($k = 0; $k -lt $asm.Count; $k++) { if ($asm[$k] -match $re) { $i = $k; break } }
      "---- k_${op}_distinct_${form} ($c)"
      if ($i -lt 0) { '  (not found)'; continue }
      for ($j = $i + 1; $j -lt $asm.Count; $j++) {
        $l = $asm[$j]
        if ($l -match '# -- End function' -or $l -match '^\s*\.seh_endproc' -or $l -match '^\.Lfunc_end') { break }
        if ($l -match '^\s+[a-z]' -and $l -notmatch '^\s+\.') { ($l -replace '\s+#.*$', '') -replace '\t', ' ' }
        elseif ($l -match '^\.LBB') { $l }
      }
    }
  }
  $out | Set-Content "asm_kernels_$c.txt"
}

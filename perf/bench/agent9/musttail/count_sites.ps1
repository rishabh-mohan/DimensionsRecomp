# Count, in the real generated LEGO code, the tail-call sites the musttail option rewrites
# and the VMX instructions whose emitters vmx_vector_fallbacks replaces.
# Usage: powershell -NoProfile -File bench/agent9/musttail/count_sites.ps1
# Single thread at below-normal priority; reads every legodimensions_recomp.*.cpp once.
$ErrorActionPreference = 'Stop'
[System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'BelowNormal'
$root = Resolve-Path "$PSScriptRoot/../../.."
$dir = Join-Path $root 'DimensionsRecomp/rexlego/generated/default'
$files = Get-ChildItem $dir -Filter 'legodimensions_recomp.*.cpp'
$reUncond = [regex]'(?m)^\t[A-Za-z_][A-Za-z0-9_]*\(ctx, base\);\r?\n\treturn;'
$reCond = [regex]'(?m)^\tif \([^\r\n]*\) \{\r?\n\t\t[A-Za-z_][A-Za-z0-9_]*\(ctx, base\);\r?\n\t\treturn;\r?\n\t\}'
$reCase = [regex]'(?m)^\tcase \d+:\r?\n\t\t[A-Za-z_][A-Za-z0-9_]*\(ctx, base\);\r?\n\t\treturn;'
$reFunc = [regex]'(?m)^DEFINE_REX_FUNC\('
$reSeh = [regex]'(?m)^\tSEH_TRY \{'
$reSetjmp = [regex]'ppc_setjmp\('
$reVmx = [regex]'// (vsubsws|vsrb|vsrab|vrlw128|vrlw|vsraw128|vsraw|vsrw128|vsrw|vpkuhus128|vpkuhus|vpkuwus128|vpkuwus) (v\d+),(v\d+),(v\d+)'
$t = @{ uncond = 0; cond = 0; jtcase = 0; funcs = 0; seh = 0; setjmp = 0; bytes = 0L }
$vmx = @{}; $alias = @{}
foreach ($f in $files) {
  $s = [System.IO.File]::ReadAllText($f.FullName)
  $t.bytes += $s.Length
  $t.uncond += $reUncond.Matches($s).Count
  $t.cond += $reCond.Matches($s).Count
  $t.jtcase += $reCase.Matches($s).Count
  $t.funcs += $reFunc.Matches($s).Count
  $t.seh += $reSeh.Matches($s).Count
  $t.setjmp += $reSetjmp.Matches($s).Count
  foreach ($m in $reVmx.Matches($s)) {
    $op = $m.Groups[1].Value -replace '128$', ''
    $vmx[$op] = 1 + [int]$vmx[$op]
    if ($m.Groups[2].Value -eq $m.Groups[3].Value -or $m.Groups[2].Value -eq $m.Groups[4].Value) {
      $alias[$op] = 1 + [int]$alias[$op]
    }
  }
}
"files=$($files.Count) MB=$([math]::Round($t.bytes / 1MB, 1)) functions=$($t.funcs) seh_try=$($t.seh) ppc_setjmp=$($t.setjmp)"
"tail calls: unconditional b=$($t.uncond) conditional=$($t.cond) jump-table case=$($t.jtcase)"
"vmx (mnemonic, total, vD aliases vA or vB):"
foreach ($k in ($vmx.Keys | Sort-Object)) { "  {0,-8} {1,7} {2,7}" -f $k, $vmx[$k], [int]$alias[$k] }

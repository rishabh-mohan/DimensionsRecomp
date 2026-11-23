# Task #23 step 1: callers of the fence emitter sub_83FC0180 and of the wait sub_83FBF7D0, plus helper definitions.
# Run through bench/agent9/cpu2.ps1 (1 slot). Read-only on the A tree.
$ErrorActionPreference = 'Stop'
$gen = 'baseline/DimensionsRecomp/rexlego/generated/default'
$out = 'build/agent9/s4/spin/grep2.txt'
$pats = @(
  'sub_83FC0180(ctx',
  'DEFINE_REX_FUNC(sub_83FC0C10)', 'sub_83FC0C10(ctx',
  'DEFINE_REX_FUNC(sub_83FAF088)', 'DEFINE_REX_FUNC(sub_83FAF0B8)',
  'sub_83FBF7D0(ctx', 'DEFINE_REX_FUNC(sub_83FC91D0)',
  '+ -25920, '
)
$sw = [Diagnostics.Stopwatch]::StartNew()
Get-ChildItem $gen -Filter 'legodimensions_recomp.*.cpp' | Select-String -SimpleMatch -Pattern $pats |
  ForEach-Object { '{0}:{1}: {2}' -f $_.Filename, $_.LineNumber, $_.Line.Trim() } | Set-Content -Encoding ascii $out
('elapsed {0:n1}s' -f $sw.Elapsed.TotalSeconds) | Add-Content -Encoding ascii $out
exit 0

# S3.3 contingency (task #12): the test half of the patch protocol for `|| !vs`, one process at a time (1 thread).
# Each step's output goes to build\agent4\s33\<step>.log; one status line per step is printed.
#   fixtures-base  run_fixtures.py on the live tree (draw.cpp 5EA1F357, batch 3), the "before" set
#   fixtures-s33   run_fixtures.py on the scratch tree (patched draw.cpp D348B820), the "after" set
#   state_shadow   test_state_shadow.py --no-bench on the scratch tree
#   run_patched    fixtures/run_patched.py on the scratch tree (named s33)
#   pg-live/pg-s33 tools/gpu-aot/test_parallel_geometry.py (not in the 26; broken on live, see S3.2)
# Run only on an idle machine (not during Agent 8's profile or n2/n3 runs), never after 08:30.
param([string[]]$Steps = @('fixtures-base', 'fixtures-s33', 'state_shadow', 'run_patched', 'pg-live', 'pg-s33'))
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot\..\..\..").Path
Set-Location $root
. "$root\env\devshell.ps1" -Quiet 6>$null | Out-Null
$tree = 'build\agent4\s33tree\DimensionsRecomp'
$commands = [ordered]@{
    'fixtures-base' = "python bench\agent4\run_fixtures.py DimensionsRecomp build\agent4\fixtures-s33-base"
    'fixtures-s33'  = "python bench\agent4\run_fixtures.py $tree build\agent4\fixtures-s33"
    'state_shadow'  = "python bench\agent4\test_state_shadow.py --tree $tree --out build\agent4\state_shadow-s33 --no-bench"
    'run_patched'   = "python bench\agent4\fixtures\run_patched.py --trees s33 --tree-path s33=$tree"
    'pg-live'       = "python DimensionsRecomp\tools\gpu-aot\test_parallel_geometry.py build\agent4\s33\pg-live"
    'pg-s33'        = "python $tree\tools\gpu-aot\test_parallel_geometry.py build\agent4\s33\pg-s33"
}
foreach ($step in $Steps) {
    $log = "build\agent4\s33\$step.log"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    cmd /c "$($commands[$step]) > $log 2>&1"
    $rc = $LASTEXITCODE
    "{0} {1}: rc={2} {3}s ({4})" -f (Get-Date -Format 'HH:mm:ss'), $step, $rc, [int]$sw.Elapsed.TotalSeconds, $log
}

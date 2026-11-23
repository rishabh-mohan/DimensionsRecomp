# S3.2 fix (task #12, step 1): the test half of the patch protocol, one process at a time (1 thread).
# Each step's output goes to build\agent4\s32\<step>.log; one status line per step is printed.
#   fixtures-base  run_fixtures.py on the live tree (draw.cpp 50AA3B1D, unchanged), the "before" set
#   fixtures-s32   run_fixtures.py on the scratch tree (patched draw.cpp 5EA1F357), the "after" set
#   state_shadow   test_state_shadow.py --no-bench on the scratch tree
#   run_patched    fixtures/run_patched.py on the scratch tree (named s32)
#   pg-live/pg-s32 tools/gpu-aot/test_parallel_geometry.py (not in the 26; it extracts PrepareDrawGeometry)
param([string[]]$Steps = @('fixtures-base', 'fixtures-s32', 'state_shadow', 'run_patched', 'pg-live', 'pg-s32'))
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot\..\..\..").Path
Set-Location $root
. "$root\env\devshell.ps1" -Quiet 6>$null | Out-Null
$tree = 'build\agent4\s32tree\DimensionsRecomp'
$commands = [ordered]@{
    'fixtures-base' = "python bench\agent4\run_fixtures.py DimensionsRecomp build\agent4\fixtures-s32-base"
    'fixtures-s32'  = "python bench\agent4\run_fixtures.py $tree build\agent4\fixtures-s32"
    'state_shadow'  = "python bench\agent4\test_state_shadow.py --tree $tree --out build\agent4\state_shadow-s32 --no-bench"
    'run_patched'   = "python bench\agent4\fixtures\run_patched.py --trees s32 --tree-path s32=$tree"
    'pg-live'       = "python DimensionsRecomp\tools\gpu-aot\test_parallel_geometry.py build\agent4\s32\pg-live"
    'pg-s32'        = "python $tree\tools\gpu-aot\test_parallel_geometry.py build\agent4\s32\pg-s32"
}
foreach ($step in $Steps) {
    $log = "build\agent4\s32\$step.log"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    cmd /c "$($commands[$step]) > $log 2>&1"
    $rc = $LASTEXITCODE
    "{0} {1}: rc={2} {3}s ({4})" -f (Get-Date -Format 'HH:mm:ss'), $step, $rc, [int]$sw.Elapsed.TotalSeconds, $log
}

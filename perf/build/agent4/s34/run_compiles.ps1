# S3.4 (task #12 (c)): the test half, one process at a time (1 thread, BelowNormal).
#   4 full -c compiles of shaders.cpp with its build/dev command: v3 (the build default) and v2
#   (-march=x86-64-v2), each patched (s34tree) and control (s34base, live bytes), then objdiff
#   control vs patched per ISA and a warning diff. Output: build\agent4\s34\{compile-*,objdiff-*,warn-diff}.txt/.log
param([string[]]$Only = @())
$ErrorActionPreference = 'Stop'
# powershell -File passes "a,b" as one string, so split on commas here.
$Only = @($Only | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$root = (Resolve-Path "$PSScriptRoot\..\..\..").Path
Set-Location $root
. "$root\env\devshell.ps1" -Quiet 6>$null | Out-Null
$s = 'build\agent4\s34'
$patched = 'build\agent4\s34tree\DimensionsRecomp\rexlego\src\gpu_native\shaders.cpp'
$control = 'build\agent4\s34base\DimensionsRecomp\rexlego\src\gpu_native\shaders.cpp'
$jobs = @(
    [pscustomobject]@{ Name = 'v3-patched'; Source = $patched; Extra = '' },
    [pscustomobject]@{ Name = 'v3-control'; Source = $control; Extra = '' },
    [pscustomobject]@{ Name = 'v2-patched'; Source = $patched; Extra = '-march=x86-64-v2' },
    [pscustomobject]@{ Name = 'v2-control'; Source = $control; Extra = '-march=x86-64-v2' }
)
foreach ($job in $jobs) {
    if ($Only -and $Only -notcontains $job.Name) { continue }
    # powershell -File drops an empty-string argument, so pass -Extra only when it is set.
    $call = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "$root\$s\compile_copy_shaders.ps1",
              '-Source', $job.Source, '-OutDir', "$s\obj\$($job.Name)", '-Log', "$s\compile-$($job.Name).log")
    if ($job.Extra) { $call += @('-Extra', $job.Extra) }
    $line = & powershell @call
    "{0} {1}: rc={2} {3}" -f (Get-Date -Format 'HH:mm:ss'), $job.Name, $LASTEXITCODE, ($line | Select-Object -Last 1)
}
foreach ($isa in 'v3', 'v2') {
    $a = "$s\obj\$isa-control\shaders.cpp.obj"; $b = "$s\obj\$isa-patched\shaders.cpp.obj"
    if ((Test-Path $a) -and (Test-Path $b)) {
        cmd /c "python build\agent4\s32\objdiff.py $a $b --top 40 > $s\objdiff-$isa.txt 2>&1"
        "{0} objdiff-{1}: rc={2}" -f (Get-Date -Format 'HH:mm:ss'), $isa, $LASTEXITCODE
    }
}
cmd /c "python $s\warn_diff.py > $s\warn-diff.txt 2>&1"
"{0} warn-diff: rc={1}" -f (Get-Date -Format 'HH:mm:ss'), $LASTEXITCODE

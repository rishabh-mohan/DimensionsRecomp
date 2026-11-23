# Build + run the flush-mode independence harness and the baseline switch scanner.
# Run it through the CPU slot holder (one clang at a time):
#   powershell -NoProfile -File bench/agent9/cpu2.ps1 -File bench/agent9/flush/build.ps1
# Options: -NoHarness, -NoScan, -HarnessArgs "nosweep" | "<scale>", -ScanList "build_fabs,build_fmr,..."
param([switch]$NoHarness, [switch]$NoScan, [string]$HarnessArgs = '', [string]$ScanList = '')
$ErrorActionPreference = 'Continue'
Push-Location (Join-Path $PSScriptRoot '../../..')
$rc = 0
try {
  . .\env\devshell.ps1 | Out-Null
  # Same flags the game uses for the generated code (build/baseline/compile_commands.json).
  $game = @('-O3', '-DNDEBUG', '-std=gnu++23', '-D_DLL', '-D_MT', '-Xclang', '--dependent-lib=msvcrt', '-msse4.1',
    '-fasync-exceptions', '-march=x86-64-v3', '-DNOMINMAX', '-DWIN32_LEAN_AND_MEAN')
  $inc = @('-I', 'DimensionsRecomp/rexglue-sdk/include', '-isystem', 'DimensionsRecomp/rexglue-sdk/thirdparty/simde')
  if (-not $NoHarness) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $out = & clang++ @game @inc bench/agent9/flush/flush_harness.cpp -o bench/agent9/flush/flush_harness.exe 2>&1
    $cc = $LASTEXITCODE
    $out | Select-Object -First 80 | ForEach-Object { "$_" }
    ("harness compile: exit {0} in {1:n1}s" -f $cc, $sw.Elapsed.TotalSeconds)
    if ($cc -eq 0) {
      $sw.Restart()
      cmd /c "bench\agent9\flush\flush_harness.exe $HarnessArgs > bench\agent9\flush\results.txt 2>&1"
      $hr = $LASTEXITCODE
      ("harness run: exit {0} in {1:n1}s" -f $hr, $sw.Elapsed.TotalSeconds)
      Select-String -Path bench/agent9/flush/results.txt -Pattern '^(build:|specials:|variants:|RESULT:)', '^\| \d+ \|' -CaseSensitive |
        ForEach-Object { $_.Line }
      if ($hr -ne 0) { $rc = 1 }
    } else { $rc = 1 }
  }
  if (-not $NoScan) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $out = & clang++ -O2 -std=gnu++23 -D_DLL -D_MT -Xclang --dependent-lib=msvcrt bench/agent9/flush/scan_baseline.cpp -o bench/agent9/flush/scan_baseline.exe 2>&1
    $cc = $LASTEXITCODE
    $out | Select-Object -First 60 | ForEach-Object { "$_" }
    ("scanner compile: exit {0} in {1:n1}s" -f $cc, $sw.Elapsed.TotalSeconds)
    $dir = 'baseline\DimensionsRecomp\rexlego\generated\default'
    if ($cc -eq 0 -and (Test-Path $dir)) {
      $sw.Restart()
      cmd /c "bench\agent9\flush\scan_baseline.exe $dir $ScanList > bench\agent9\flush\baseline_scan.txt 2>&1"
      $sr = $LASTEXITCODE
      ("scanner run: exit {0} in {1:n1}s" -f $sr, $sw.Elapsed.TotalSeconds)
      Select-String -Path bench/agent9/flush/baseline_scan.txt -Pattern '^SCAN:' -CaseSensitive | ForEach-Object { $_.Line }
      if ($sr -ne 0) { $rc = 1 }
    } else { "scanner not run (compile exit $cc, dir exists: $(Test-Path $dir))"; $rc = 1 }
  }
} finally { Pop-Location }
exit $rc

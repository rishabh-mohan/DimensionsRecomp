# Step 5b: run gpu-shader-extract inventory + extract for disc and TU23 (recipe: both into one shader-assets dir).
# Game data is read-only; output goes to DR/rexlego/out/native-gpu/shader-assets. Caller pins to one CPU.
$ErrorActionPreference = 'Continue'
$root = '<workspace>'
$dr = "$root\DimensionsRecomp"
$ex = "$root\build\agent6\aot\extract"
$logs = "$root\build\agent6\aot\logs"
$env:DOTNET_ROOT = "$dr\research\tools\dotnet"
$env:DOTNET_MULTILEVEL_LOOKUP = '0'
$env:DOTNET_CLI_HOME = "$ex\dotnet-home"
$env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'
$env:DOTNET_NOLOGO = '1'
$env:DOTNET_gcServer = '0'
$dotnet = "$dr\research\tools\dotnet\dotnet.exe"
$dll = "$ex\artifacts\bin\gpu-shader-extract\release\gpu-shader-extract.dll"
$out = "$dr\rexlego\out\native-gpu\shader-assets"
"start: $(Get-Date -Format o)"
foreach ($step in @(@('inventory', 'disc'), @('inventory', 'tu23'), @('extract', 'disc'), @('extract', 'tu23'))) {
  $mode = $step[0]; $src = "$root\game\$($step[1])"
  $log = "$logs\extractor-$mode-$($step[1]).log"
  $sw = [Diagnostics.Stopwatch]::StartNew()
  if ($mode -eq 'inventory') { & $dotnet $dll inventory $src *> $log } else { & $dotnet $dll extract $src $out *> $log }
  "$mode $($step[1]): exit=$LASTEXITCODE wall_s=$([math]::Round($sw.Elapsed.TotalSeconds,1)) log=$log"
}
"end: $(Get-Date -Format o)"

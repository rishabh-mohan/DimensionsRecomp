# Step 5a: build tools/gpu-shader-extract (unmodified csproj) with the local .NET SDK 8.0.428.
# Nothing is written into tools/: --artifacts-path puts obj/ and bin/ under build/agent6/aot/extract/artifacts.
# Run pinned to one CPU by the caller (cmd start /affinity), plus -m:1, no node reuse, no shared compiler server.
$ErrorActionPreference = 'Continue'
$root = '<workspace>'
$dr = "$root\DimensionsRecomp"
$ex = "$root\build\agent6\aot\extract"
$env:DOTNET_ROOT = "$dr\research\tools\dotnet"
$env:DOTNET_MULTILEVEL_LOOKUP = '0'
$env:DOTNET_CLI_HOME = "$ex\dotnet-home"
$env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'
$env:DOTNET_NOLOGO = '1'
$env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE = '1'
$env:DOTNET_GENERATE_ASPNET_CERTIFICATE = '0'
$env:DOTNET_ADD_GLOBAL_TOOLS_TO_PATH = '0'
$env:NUGET_PACKAGES = "$ex\nuget-packages"
$env:MSBUILDDISABLENODEREUSE = '1'
$dotnet = "$dr\research\tools\dotnet\dotnet.exe"
$proj = "$dr\tools\gpu-shader-extract\gpu-shader-extract.csproj"
"start: $(Get-Date -Format o)"
"tools/gpu-shader-extract before:"; Get-ChildItem "$dr\tools\gpu-shader-extract" -Force | ForEach-Object { "  $($_.Name)" }
$sw = [Diagnostics.Stopwatch]::StartNew()
& $dotnet build $proj -c Release --artifacts-path "$ex\artifacts" -m:1 -nr:false --disable-build-servers `
  "-p:UseSharedCompilation=false" "-p:CustomBeforeMicrosoftCommonTargets=$ex\inject.targets" `
  "-p:RestoreConfigFile=$ex\NuGet.Config" -v:n 2>&1 | ForEach-Object { "$_" }
"build exit=$LASTEXITCODE wall_s=$([math]::Round($sw.Elapsed.TotalSeconds,1))"
"tools/gpu-shader-extract after:"; Get-ChildItem "$dr\tools\gpu-shader-extract" -Force | ForEach-Object { "  $($_.Name)" }
git -C $dr status --porcelain --ignored -- tools/gpu-shader-extract
Get-ChildItem "$ex\artifacts\bin" -Recurse -File | ForEach-Object { "{0}  {1}" -f $_.Length, $_.FullName }
"end: $(Get-Date -Format o)"

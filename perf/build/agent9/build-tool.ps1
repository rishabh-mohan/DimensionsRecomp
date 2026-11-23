# Agent 9: build the dev-tree codegen tool (rexglue.exe) without rebuilding the runtime.
#   configure : cmake --preset win-amd64 -B DimensionsRecomp/rexglue-sdk/out/build/agent9 (tests ON, compile DB)
#   objects   : ninja only the rexcodegen + rexglue objects and rexcodegen.lib (no runtime TUs)
#   link      : link rexglue.exe (and the regression producer) into build/agent9/bin against the
#               pin (baseline) runtime/thirdparty import libs; copies the pin rexruntime.dll next to it.
# The all-off codegen output of this tool must be byte-identical to the pin tool's (T1), which checks
# that mixing dev codegen objects with the pin runtime is sound for codegen.
# Run: powershell -NoProfile -File build\agent9\build-tool.ps1 [-Steps configure,objects,link] [-Jobs 6]
param([string[]]$Steps = @('configure', 'objects', 'link'), [int]$Jobs = 6)
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
$sdk = "$R\DimensionsRecomp\rexglue-sdk"
$pin = "$R\baseline\DimensionsRecomp\rexglue-sdk"
$bin = "$sdk\out\build\agent9"
$logs = "$R\build\agent9\logs"
$outBin = "$R\build\agent9\bin"
New-Item -ItemType Directory -Force $logs, $outBin | Out-Null
. "$R\env\devshell.ps1" 6>$null | Out-Null
function Note([string]$m) { "$(Get-Date -Format HH:mm:ss) $m" | Tee-Object -Append -FilePath "$logs\build-tool-steps.txt" }
if ($Steps.Count -eq 1 -and $Steps[0] -match ',') { $Steps = $Steps[0] -split ',' }

if ($Steps -contains 'configure') {
    Push-Location $sdk
    $sw = [Diagnostics.Stopwatch]::StartNew()
    Note 'BEGIN configure'
    cmd /d /c "cmake --preset win-amd64 -B `"$bin`" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DREXGLUE_BUILD_TESTS=ON > `"$logs\configure.log`" 2>&1"
    $code = $LASTEXITCODE
    Note "END   configure exit=$code wall=$([int]$sw.Elapsed.TotalSeconds)s"
    Pop-Location
    if ($code -ne 0) { exit 1 }
}

$ninja = @('-C', $bin, '-f', 'build-Release.ninja')
if ($Steps -contains 'objects') {
    $all = & ninja @ninja -t targets all 2>$null
    $objs = @($all | ForEach-Object { if ($_ -match '^(.*?\.obj): ') { $Matches[1] } } |
        Where-Object { $_ -match '[\\/](rexcodegen|rexglue)\.dir[\\/]Release[\\/]' })
    $lib = @($all | ForEach-Object { if ($_ -match '^(.*?rexcodegen\.lib): ') { $Matches[1] } }) | Select-Object -First 1
    Note "objects: $($objs.Count) objects + $lib"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    Note "BEGIN objects -j $Jobs"
    & ninja @ninja -j $Jobs @objs $lib *> "$logs\objects.log"
    $code = $LASTEXITCODE
    Note "END   objects exit=$code wall=$([int]$sw.Elapsed.TotalSeconds)s"
    if ($code -ne 0) { Get-Content "$logs\objects.log" | Select-String -Pattern 'error|FAILED' | Select-Object -First 20 | ForEach-Object { Note "  $($_.Line)" }; exit 2 }
}

if ($Steps -contains 'link') {
    $all = & ninja @ninja -t targets all 2>$null
    $exe = @($all | ForEach-Object { if ($_ -match '^(.*?rexglue\.exe): ') { $Matches[1] } }) | Select-Object -First 1
    $cmds = @(& ninja @ninja -t commands $exe 2>$null)
    $link = $cmds[-1]
    Set-Content "$logs\link-original.txt" $link
    # Every runtime/thirdparty library comes from the pin build; only rexcodegen.lib is ours.
    $devOut = "$sdk\out\win-amd64\Release"
    $pinOut = "$pin\out\win-amd64\Release"
    foreach ($f in Get-ChildItem $pinOut -Filter *.lib) {
        if ($f.Name -eq 'rexcodegen.lib') { continue }
        foreach ($sep in @('\', '/')) {
            $from = ($devOut + '\' + $f.Name).Replace('\', $sep)
            $link = $link.Replace($from, $f.FullName)
        }
    }
    $exeOut = "$outBin\rexglue.exe"
    $link = $link.Replace($exe, $exeOut).Replace($exe.Replace('\', '/'), $exeOut)
    Set-Content "$logs\link-agent9.txt" $link
    $sw = [Diagnostics.Stopwatch]::StartNew()
    Note 'BEGIN link rexglue.exe'
    Push-Location $bin
    cmd /d /c "$link > `"$logs\link.log`" 2>&1"
    $code = $LASTEXITCODE
    Pop-Location
    Note "END   link exit=$code wall=$([int]$sw.Elapsed.TotalSeconds)s"
    if ($code -ne 0) { Get-Content "$logs\link.log" | Select-Object -First 30 | ForEach-Object { Note "  $_" }; exit 3 }
    foreach ($dll in 'rexruntime.dll', 'TracyClient.dll') { Copy-Item "$pinOut\$dll" $outBin -Force }
    Note "rexglue.exe $((Get-Item $exeOut).Length) bytes sha256 $((Get-FileHash $exeOut).Hash)"
}
exit 0

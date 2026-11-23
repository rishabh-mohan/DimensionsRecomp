# Agent 2 - plan (c) probe: does toggling NATIVE_GPU OFF -> ON in ONE find_package tree recompile the
# generated TUs?  Configure-only, twice, in build/agent2/probe-toggle (dev rexlego, find_package against
# build/sdk/install, Agent 6 stubs, frozen codegen tool, compat shim). Nothing is built.
# Compares every compile_commands.json entry between the two configures: ninja reruns an edge whose command
# changed, so identical generated-TU (and PCH) commands mean no recompile on the toggle.
# Then compile-one -SyntaxOnly on the two SDK sources the ON game compiles itself (texture util/info.cpp).
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\probe-toggle.ps1
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
Set-Location $R
. "$R\env\devshell.ps1" 6>$null | Out-Null
$Rf = $R -replace '\\', '/'
$root = "$Rf/DimensionsRecomp"; $stub = "$root/rexlego/out/native-gpu/stubs"
$P = "$R\build\agent2\probe-toggle"; $log = "$R\build\agent2\probe-toggle.log"
"# probe-toggle $(Get-Date -Format HH:mm:ss)" | Out-File -Encoding utf8 $log
filter Log { $_ | Out-File -Append -Encoding utf8 $log; Write-Host $_ }   # NOT Tee-Object: it writes UTF-16 and leaks into function return values
$common = @(
    "-G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++",
    "-DLEGODIMENSIONS_X86_BASELINE=x86-64-v3 -DCMAKE_PREFIX_PATH=$Rf/build/sdk/install",
    "-DREXGLUE_HOST_CODEGEN_EXECUTABLE=$Rf/build/agent2/codegen-tool/rexglue.exe",
    "-DCMAKE_PROJECT_INCLUDE=$Rf/build/agent2/compat/project-include.cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON"
) -join ' '
$onFlags = @(
    "-DLEGO_TEMPORAL_SHADER_BANK=$stub/temporal-bank",
    "-DLEGO_FLOAT_BLEND_INDICES_BANK=$stub/float-blend-indices-bank",
    "-DLEGO_NATIVE_SHADER_CACHE=$stub/lego-dxil-cache.cpp",
    "-DLEGO_NATIVE_RUNTIME_SHADER_CACHE=$stub/runtime-cache.cpp",
    "-DLEGO_NATIVE_FIDELITYFX_RUNTIME=$root/rexglue-sdk/thirdparty/FidelityFX-SDK/PrebuiltSignedDLL/amd_fidelityfx_dx12.dll",
    "-DLEGO_NATIVE_BINARY_CACHE=OFF",
    "`"-DLEGO_HOST_DXC_EXECUTABLE=C:/Program Files (x86)/Windows Kits/10/bin/10.0.22621.0/x64/dxc.exe`""
) -join ' '
function Cfg([string]$tag, [string]$extra) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    cmd /d /c "cmake -S `"$R\DimensionsRecomp\rexlego`" -B `"$P`" $common $extra > `"$R\build\agent2\probe-toggle-$tag.log`" 2>&1"
    $code = $LASTEXITCODE
    "configure $tag exit=$code wall=$([Math]::Round($sw.Elapsed.TotalSeconds,1))s" | Log
    if (Test-Path "$P\compile_commands.json") { Copy-Item "$P\compile_commands.json" "$R\build\agent2\probe-toggle-$tag.json" -Force }
    return $code
}
if (Test-Path $P) { Remove-Item $P -Recurse -Force }
$c1 = Cfg 'off' '-DLEGODIMENSIONS_NATIVE_GPU=OFF'
$c2 = Cfg 'on' "-DLEGODIMENSIONS_NATIVE_GPU=ON $onFlags"
if ($c1 -ne 0 -or $c2 -ne 0) { "configure failed; see probe-toggle-off/on.log" | Log; Get-Content "$R\build\agent2\probe-toggle-on.log" -Tail 25 | Out-File -Append -Encoding utf8 $log; exit 1 }
Add-Type -AssemblyName System.Web.Extensions
$ser = New-Object System.Web.Script.Serialization.JavaScriptSerializer; $ser.MaxJsonLength = [int]::MaxValue
function Load([string]$f) { $m = @{}; foreach ($e in $ser.DeserializeObject([IO.File]::ReadAllText($f))) { $m[[string]$e['file'] + '|' + [string]$e['output']] = [string]$e['command'] }; $m }
$off = Load "$R\build\agent2\probe-toggle-off.json"; $on = Load "$R\build\agent2\probe-toggle-on.json"
$cls = { param($k) if ($k -match '[\\/]generated[\\/]default[\\/]') { 'generated' } elseif ($k -match 'cmake_pch') { 'pch' } elseif ($k -match '[\\/]rexlego[\\/]src[\\/]') { 'src' } else { 'other' } }
$stats = @{}
foreach ($k in ($off.Keys + $on.Keys | Sort-Object -Unique)) {
    $c = & $cls $k
    $state = if (-not $off.ContainsKey($k)) { 'ON-only' } elseif (-not $on.ContainsKey($k)) { 'OFF-only' } elseif ($off[$k] -ceq $on[$k]) { 'identical' } else { 'changed' }
    $key = "$c/$state"; if (-not $stats.ContainsKey($key)) { $stats[$key] = 0 }; $stats[$key]++
    if ($state -eq 'changed' -and $c -in 'generated', 'pch' -and -not $script:shown) {
        $script:shown = $true
        $a = $off[$k] -split ' '; $b = $on[$k] -split ' '
        "FIRST CHANGED $c entry: $k" | Log
        "  OFF-only: $((Compare-Object $a $b | Where-Object SideIndicator -eq '<=' | ForEach-Object InputObject) -join ' ')" | Log
        "  ON-only : $((Compare-Object $a $b | Where-Object SideIndicator -eq '=>' | ForEach-Object InputObject) -join ' ')" | Log
    }
}
$stats.GetEnumerator() | Sort-Object Name | ForEach-Object { "{0,-22} {1}" -f $_.Name, $_.Value } | Log
# -I paths of a generated TU in the ON configure (must be build/sdk/install/include here; the snapshot build checks its own)
$g = $on.Keys | Where-Object { $_ -match 'legodimensions_recomp\.0\.cpp' } | Select-Object -First 1
"generated TU -I/-isystem dirs (ON): " + ((([regex]::Matches($on[$g], '(?:-I|-isystem\s+)("[^"]+"|\S+)') | ForEach-Object { $_.Groups[1].Value }) | Sort-Object -Unique) -join ' ') | Log
# the SDK sources the ON game compiles itself must build against the INSTALLED SDK headers
foreach ($s in 'DimensionsRecomp\rexglue-sdk\src\graphics\pipeline\texture\util.cpp', 'DimensionsRecomp\rexglue-sdk\src\graphics\pipeline\texture\info.cpp') {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $o = powershell -NoProfile -ExecutionPolicy Bypass -File "$R\env\compile-one.ps1" $s -OutDir "$R\build\agent2\obj-probe" -Db "$P\compile_commands.json" -SyntaxOnly 2>&1
    "compile-one -SyntaxOnly $(Split-Path -Leaf $s) exit=$LASTEXITCODE wall=$([Math]::Round($sw.Elapsed.TotalSeconds,1))s" | Log
    if ($LASTEXITCODE -ne 0) { $o | Select-Object -Last 15 | Out-File -Append -Encoding utf8 $log }
}
"# done $(Get-Date -Format HH:mm:ss)" | Log

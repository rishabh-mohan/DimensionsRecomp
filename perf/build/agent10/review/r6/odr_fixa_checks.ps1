param()
$ErrorActionPreference = 'Continue'
$w = '<workspace>'
$d = "$w\DimensionsRecomp"
$s = "$d\rexglue-sdk"
$lg = "$d\rexlego\src"
$out = "$w\build\agent10\review\r6"

function Show($m) { $m | ForEach-Object { '{0}:{1}: {2}' -f ($_.Path.Substring($d.Length + 1)), $_.LineNumber, $_.Line.Trim() } }

'=== 1. workspace git?'
'workspace .git: ' + (Test-Path "$w\.git") + '; DimensionsRecomp .git: ' + (Test-Path "$d\.git")

'=== 2. REX_HAS_FIDELITYFX users (SDK src+include, rexlego src+gpu_native, cmake)'
$sdkfiles = @(Get-ChildItem "$s\src", "$s\include" -Recurse -File -Include *.cpp, *.h, *.hpp, *.inl, *.cc -ErrorAction SilentlyContinue)
$lgfiles = @(Get-ChildItem "$lg\*.cpp", "$lg\*.h", "$lg\gpu_native\*.cpp", "$lg\gpu_native\*.h", "$lg\gpu\*.cpp", "$lg\gpu\*.h" -File -ErrorAction SilentlyContinue)
"sdk files: $($sdkfiles.Count); rexlego files: $($lgfiles.Count)"
$hits = Select-String -Path ($sdkfiles + $lgfiles).FullName -Pattern 'REX_HAS_FIDELITYFX' 
$hits | Group-Object Path | ForEach-Object { '{0}  ({1} lines)' -f $_.Name.Substring($d.Length + 1), $_.Count }

'=== 3. includes of presenter headers outside src/ui and include/rex/ui'
$nonui = @($sdkfiles | Where-Object { $_.FullName -notlike "$s\src\ui\*" -and $_.FullName -notlike "$s\include\rex\ui\*" }) + $lgfiles
Show (Select-String -Path $nonui.FullName -Pattern '#\s*include\s*[<"].*(presenter|d3d12_provider|graphics_provider)\.h[>"]')

'=== 4. layout-dependent names used outside rexui (src/ui) -- SDK non-ui + rexlego + rex_app/windowed_app_main_sdl'
$pat = 'GuestOutputPaintConfig|GuestOutputPaintFlow|kMaxGuestOutputPaintEffects|GuestOutputPaintEffect|GetGuestOutputPaintConfigFromUIThread|SetGuestOutputPaintConfigFromUIThread|D3D12Presenter::Create|GuestOutputPaintRootSignature|PaintContext|AddUIDrawerFromUIThread|sizeof\(\s*(rex::ui::)?(D3D12)?Presenter\s*\)'
$extra = @(Get-Item "$s\src\ui\rex_app.cpp", "$s\src\ui\windowed_app_main_sdl.cpp")
Show (Select-String -Path ($nonui + $extra).FullName -Pattern $pat)

'=== 5. Presenter / D3D12Presenter member use outside src/ui (-> presenter-> / ->presenter())'
Show (Select-String -Path ($nonui + $extra).FullName -Pattern 'presenter(_)?\s*(\(\))?\s*->\s*\w+|Presenter\s*\*|unique_ptr<\s*(rex::ui::)?Presenter' | Select-Object -First 60)

'=== 6. guard structure in presenter.h and d3d12_presenter.h'
foreach ($h in @("$s\include\rex\ui\presenter.h", "$s\include\rex\ui\d3d12\d3d12_presenter.h", "$s\src\ui\presenter.h", "$s\src\ui\d3d12\d3d12_presenter.h")) {
  if (Test-Path $h) {
    "--- $($h.Substring($d.Length + 1)) ($((Get-Item $h).Length) B)"
    Show (Select-String -Path $h -Pattern '^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b|guest_output_paint_config_\s*;|GetGuestOutputPaintConfigFromUIThread\(|SetGuestOutputPaintConfigFromUIThread\(|kMaxGuestOutputPaintEffects\s*=|kGuestOutputPaintRootSignatureCount|guest_output_intermediate_textures|kViewCount|virtual ')
  }
}

'=== 7. src/ui/CMakeLists.txt FidelityFX lines'
Show (Select-String -Path "$s\src\ui\CMakeLists.txt" -Pattern 'FIDELITYFX|add_library|OBJECT|target_compile_definitions|target_link_libraries')
Show (Select-String -Path "$s\src\graphics\CMakeLists.txt" -Pattern 'rexui|add_library|SHARED|rexruntime')

'=== 8. catalog key registrations'
$keys = 'fullscreen','native_vsync','native_fps_limit','native_show_fps','native_resolution_scale','native_bloom','native_cel_shading','native_fsr3','native_fsr3_quality','native_fsr3_sharpen','native_fsr3_sharpness','native_fsr3_mip_bias','present_effect','present_fsr_sharpness_reduction','present_fsr_max_upsampling_passes','native_anisotropic_override','depth_of_field'
$reg = Select-String -Path ($sdkfiles + $lgfiles).FullName -Pattern ('REXCVAR_DEFINE_\w+\(\s*(' + ($keys -join '|') + ')\s*,')
foreach ($k in $keys) {
  $m = @($reg | Where-Object { $_.Line -match ('REXCVAR_DEFINE_\w+\(\s*' + $k + '\s*,') })
  '{0,-36} {1}' -f $k, (($m | ForEach-Object { '{0}:{1}' -f (Split-Path $_.Path -Leaf), $_.LineNumber }) -join ', ')
}

'=== 9. patch apply in scratch (GIT_CEILING_DIRECTORIES isolates from any outer repo)'
$fx = "$out\fixa"
if (Test-Path $fx) { Remove-Item $fx -Recurse -Force }
foreach ($v in 'a', 'ac', 'c') {
  New-Item -ItemType Directory -Force "$fx\$v\rexlego\src" | Out-Null
  Copy-Item "$lg\settings_registry.cpp", "$lg\settings_preferences.cpp" "$fx\$v\rexlego\src\"
}
$env:GIT_CEILING_DIRECTORIES = $fx
$env:GIT_OPTIONAL_LOCKS = '0'
$pa = "$w\build\agent6\fix-a\fix-a.patch"
$pc = "$w\build\agent6\fix-a\fix-a-commit.patch"
Push-Location "$fx\a";  git apply --check $pa; "a check rc=$LASTEXITCODE"; git apply $pa; "a apply rc=$LASTEXITCODE"; git apply -R --check $pa; "a -R check rc=$LASTEXITCODE"; Pop-Location
Push-Location "$fx\ac"; git apply $pa; "ac apply1 rc=$LASTEXITCODE"; git apply --check $pc; "ac check2 rc=$LASTEXITCODE"; git apply $pc; "ac apply2 rc=$LASTEXITCODE"; Pop-Location
Push-Location "$fx\c";  git apply --check $pc; "c (commit alone) check rc=$LASTEXITCODE"; git apply $pc; "c apply rc=$LASTEXITCODE"; Pop-Location
Get-ChildItem $fx -Recurse -File | ForEach-Object { '{0}  {1,6}  {2}' -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.Substring(0, 16), $_.Length, $_.FullName.Substring($fx.Length + 1) }
'--- diff a vs live (registry, prefs) and ac vs a (registry)'
git -c core.autocrlf=false diff --no-index -U1 -- "$lg\settings_registry.cpp" "$fx\a\rexlego\src\settings_registry.cpp" | ForEach-Object { $_.TrimEnd("`r") }
git -c core.autocrlf=false diff --no-index -U1 -- "$lg\settings_preferences.cpp" "$fx\a\rexlego\src\settings_preferences.cpp" | ForEach-Object { $_.TrimEnd("`r") }
git -c core.autocrlf=false diff --no-index -U1 -- "$fx\a\rexlego\src\settings_registry.cpp" "$fx\ac\rexlego\src\settings_registry.cpp" | ForEach-Object { $_.TrimEnd("`r") }
'--- CRLF check on outputs (count of LF without CR)'
foreach ($f in Get-ChildItem $fx -Recurse -File) { $t = [IO.File]::ReadAllText($f.FullName, [Text.Encoding]::GetEncoding(28591)); $lf = ([regex]::Matches($t, "(?<!`r)`n")).Count; '{0}: bare LF={1}' -f $f.FullName.Substring($fx.Length + 1), $lf }

'=== 10. proposal file state'
foreach ($f in "$w\perf-notes\agent7-s3-proposal.md", "$w\perf-notes\agent6-crash-triage.md", "$w\perf-notes\agent7-odr-ffx.md") { $i = Get-Item $f; '{0}  {1}  {2:HH:mm:ss}  {3}' -f (Get-FileHash $f -Algorithm SHA256).Hash.Substring(0, 16), $i.Length, $i.LastWriteTime, $i.Name }

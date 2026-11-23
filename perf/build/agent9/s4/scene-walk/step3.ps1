$ErrorActionPreference = 'Continue'
$out = 'build/agent9/s4/scene-walk/step3.log'
$src = 'DimensionsRecomp/rexlego'
"=== CMakeLists source gating" | Out-File $out -Encoding ascii
Select-String -Path "$src/CMakeLists.txt" -Pattern 'native_memops|native_markers|native_saverest|settings_native|NATIVE_GPU|gpu_native/|scene_distance|native_lock_elide|native_atomics|native_constants|main_menu_extras|LEGODIMENSIONS_SOURCES' | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" } | Out-File $out -Append -Encoding ascii
"=== draw.cpp swap/vblank/present" | Out-File $out -Append -Encoding ascii
Select-String -Path "$src/src/gpu_native/draw.cpp" -Pattern 'SwapHook|83FB33E0|VdSwap|vblank|VBlank|Interrupt|interrupt|frame_index|FrameIndex|Sleep\(|WaitForSingle|Present\(|present_count|swap_count' | Select-Object -First 90 | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" } | Out-File $out -Append -Encoding ascii
"=== device.cpp vblank/fence/rptr" | Out-File $out -Append -Encoding ascii
Select-String -Path "$src/src/gpu_native/device.cpp" -Pattern 'vblank|VBlank|Interrupt|interrupt|ReadPtr|read_ptr|rptr|RPTR|wptr|WritePtr|fence_value|GuestFence|guest_fence|Callback\(' | Select-Object -First 90 | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" } | Out-File $out -Append -Encoding ascii
"=== agent4-draw-path.md keywords" | Out-File $out -Append -Encoding ascii
Select-String -Path 'perf-notes/agent4-draw-path.md' -Pattern 'vblank|VBlank|interrupt|Interrupt|ZPD|EVENT_WRITE|occlusion|Occlusion|GetQueryData|frame delta|frame-delta|readback|Readback|BlockOnFence|KickOff|InsertCallback|ring' | Select-Object -First 80 | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" } | Out-File $out -Append -Encoding ascii
"=== src (non gpu_native) gating keywords" | Out-File $out -Append -Encoding ascii
foreach ($f in @('native_memops.cpp','native_markers.cpp','native_saverest.cpp','native_lock_elide.cpp','native_atomics.cpp','scene_distance.cpp','native_constants.cpp')) {
  "--- $f" | Out-File $out -Append -Encoding ascii
  Select-String -Path "$src/src/$f" -Pattern 'LEGODIMENSIONS_NATIVE|#if|getenv|GetEnv|Enabled\(|REX_HOOK|cvar|REXCVAR|DEFINE_bool|static bool' | Select-Object -First 40 | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" } | Out-File $out -Append -Encoding ascii
}
"=== settings_native_hooks gating" | Out-File $out -Append -Encoding ascii
Select-String -Path "$src/src/settings_native_hooks.cpp" -Pattern 'native_settings_frontend|REX_HOOK|#if|Enabled|return;' | Select-Object -First 80 | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" } | Out-File $out -Append -Encoding ascii
"done" | Out-File $out -Append -Encoding ascii

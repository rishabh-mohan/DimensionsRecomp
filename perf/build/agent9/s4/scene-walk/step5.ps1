$ErrorActionPreference = 'Continue'
$env:PYTHONDONTWRITEBYTECODE = '1'
$out = 'build/agent9/s4/scene-walk/step5.log'
$py = 'build/agent9/s4/scene-walk/find.py'
"=== main loop body callees (sub_82AFAB68?)" | Out-File $out -Encoding ascii
python $py calls 59 sub_82FEB7B8 2>&1 | Select-String -Pattern 'sub_82AFAB68|sub_82AB2040|sub_82FE9068|range' | ForEach-Object { $_.Line } | Out-File $out -Append -Encoding ascii
"=== main_menu_extras.cpp gating" | Out-File $out -Append -Encoding ascii
Select-String -Path 'DimensionsRecomp/rexlego/src/main_menu_extras.cpp' -Pattern '#if|#endif|REX_HOOK|Enabled|getenv|REXCVAR' | Select-Object -First 50 | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" } | Out-File $out -Append -Encoding ascii
"=== hooks_device.cpp key lines" | Out-File $out -Append -Encoding ascii
Select-String -Path 'DimensionsRecomp/rexlego/src/gpu_native/hooks_device.cpp' -Pattern 'REX_HOOK|fence|Fence|ctx.r3.u64 =|return|Store|store|Wait|wait' | Select-Object -First 90 | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" } | Out-File $out -Append -Encoding ascii
"=== map scan" | Out-File $out -Append -Encoding ascii
python build/agent9/s4/scene-walk/mapscan.py 2>&1 | Out-File $out -Append -Encoding ascii
"done" | Out-File $out -Append -Encoding ascii

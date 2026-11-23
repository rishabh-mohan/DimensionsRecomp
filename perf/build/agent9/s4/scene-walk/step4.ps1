$ErrorActionPreference = 'Continue'
$env:PYTHONDONTWRITEBYTECODE = '1'
$out = 'build/agent9/s4/scene-walk/step4.log'
$py = 'build/agent9/s4/scene-walk/find.py'
"=== map lookups" | Out-File $out -Encoding ascii
python $py map sub_82B612F0 sub_82B61320 sub_82B61378 sub_82B60E08 sub_82B62040 sub_82B62070 sub_82B60E48 sub_82B6FC70 sub_82EF0918 sub_82EF0A68 sub_82EF1A70 sub_82EFB870 sub_82EF94E0 sub_82FBC4D8 sub_82EF4338 sub_82EFB260 2>&1 | Out-File $out -Append -Encoding ascii
foreach ($p in @(@('391','sub_82B61580'),@('137','sub_82B62C1C'),@('135','sub_82B62528'),@('259','sub_82B53308'))) {
  "=== calls $($p[0]) $($p[1])" | Out-File $out -Append -Encoding ascii
  python $py calls $p[0] $p[1] 2>&1 | Out-File $out -Append -Encoding ascii
}
"=== agent7-present methodology" | Out-File $out -Append -Encoding ascii
Select-String -Path 'perf-notes/agent7-present.md' -Pattern 'guest-only|frontend|host frame|host frames|hook|an-main-tree|native2|native3d|n-prof|a-prof' | Select-Object -First 60 | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" } | Out-File $out -Append -Encoding ascii
"done" | Out-File $out -Append -Encoding ascii

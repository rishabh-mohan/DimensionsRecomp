# Validate sharding on the 50-shader sample: 2 shards via run_shards.py (CPU1 only) + merge, compared with the
# single-process run in aot/sample-50-single (lego-dxil-cache.cpp sha256 646479C8...9968).
$ErrorActionPreference = 'Continue'
$w = '<workspace>'
$a = "$w\DimensionsRecomp\rexlego\out\native-gpu\aot"
$s = "$w\build\agent6\aot\scripts"
$exe = "$w\build\agent6\aot\gradient-build\gradient_compiler.exe"
$common = "$w\DimensionsRecomp\rexlego\out\native-gpu\current-compiler\gradients\source\shader_common.h"
$merge = "$w\build\agent6\aot\merge\merge_dxil_cache.exe"
Remove-Item -Recurse -Force "$a\sample-50-shards-out", "$a\sample-50-merged" -ErrorAction SilentlyContinue
$t0 = Get-Date
& python "$s\run_shards.py" --shards-dir "$a\sample-50-shards" --out-dir "$a\sample-50-shards-out" --exe $exe --common $common --cpus 1
"run_shards exit=$LASTEXITCODE wall_s=$([math]::Round(((Get-Date)-$t0).TotalSeconds,2))"
New-Item -ItemType Directory -Force "$a\sample-50-merged" | Out-Null
$t0 = Get-Date
& $merge merge "$a\sample-50-merged\lego-dxil-cache.cpp" "$a\sample-50-shards-out\shard00\lego-dxil-cache.cpp" "$a\sample-50-shards-out\shard01\lego-dxil-cache.cpp"
"merge exit=$LASTEXITCODE wall_s=$([math]::Round(((Get-Date)-$t0).TotalSeconds,2))"
"merged sha256=$((Get-FileHash "$a\sample-50-merged\lego-dxil-cache.cpp" -Algorithm SHA256).Hash)"
"single sha256=$((Get-FileHash "$a\sample-50-single\lego-dxil-cache.cpp" -Algorithm SHA256).Hash)"
& $merge compare "$a\sample-50-single\lego-dxil-cache.cpp" "$a\sample-50-merged\lego-dxil-cache.cpp"
"compare exit=$LASTEXITCODE"
& python "$s\merge_dumps.py" "$a\sample-50-merged\hlsl-dump" "$a\sample-50-shards-out\shard00\hlsl-dump" "$a\sample-50-shards-out\shard01\hlsl-dump" --compare "$a\sample-50-single\hlsl-dump"
"merge_dumps exit=$LASTEXITCODE"

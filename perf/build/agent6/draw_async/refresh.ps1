# Re-bases bench\agent6\draw-async.patch onto the live draw.cpp if it changed.
# Read-only for every repo: the patch is applied to a scratch copy here, with git
# repo discovery stopped at this directory. Then regenerates the patch, checks it
# against the live file (git apply --check) and, unless -NoCheck, syntax-checks
# the new patched copy (check.ps1, ~40 s, one clang process).
param([switch]$NoCheck)
$root = (Resolve-Path "$PSScriptRoot\..\..\..").Path
Set-Location $root
$live = 'DimensionsRecomp\rexlego\src\gpu_native\draw.cpp'
$dir = 'build\agent6\draw_async'
$patch = "$root\bench\agent6\draw-async.patch"
$liveHash = (Get-FileHash $live).Hash
$baseHash = (Get-FileHash "$dir\draw.orig.cpp").Hash
"live $liveHash $((Get-Item $live).LastWriteTime.ToString('o')) $((Get-Item $live).Length) bytes"
"base $baseHash"
if ($liveHash -eq $baseHash) { 'unchanged'; exit 0 }

$scratch = "$dir\rebase"
if (Test-Path $scratch) { Remove-Item -Recurse -Force $scratch }
New-Item -ItemType Directory "$scratch\rexlego\src\gpu_native" | Out-Null
Copy-Item $live "$scratch\base.cpp"
"snapshot $((Get-FileHash "$scratch\base.cpp").Hash)"
Copy-Item "$scratch\base.cpp" "$scratch\rexlego\src\gpu_native\draw.cpp"
$env:GIT_CEILING_DIRECTORIES = (Resolve-Path $dir).Path
Push-Location $scratch
git apply -v $patch 2>&1 | ForEach-Object { "$_" }
$applied = $LASTEXITCODE
Pop-Location
Remove-Item Env:GIT_CEILING_DIRECTORIES
if ($applied -ne 0) { 'APPLY FAILED: re-apply the 5 edits by hand'; exit 1 }

$old = $baseHash.Substring(0, 8)
Copy-Item "$dir\draw.orig.cpp" "$dir\draw.orig.$old.cpp" -Force
Copy-Item "$dir\draw.cpp" "$dir\draw.$old.cpp" -Force
Copy-Item "$scratch\base.cpp" "$dir\draw.orig.cpp" -Force
Copy-Item "$scratch\rexlego\src\gpu_native\draw.cpp" "$dir\draw.cpp" -Force
git -c core.autocrlf=false diff --no-index --no-color --no-ext-diff --output="$dir/raw-crlf.patch" "$dir/draw.orig.cpp" "$dir/draw.cpp"
python "$dir/mkpatch.py"
git -C DimensionsRecomp apply --check -v ../bench/agent6/draw-async.patch 2>&1 | ForEach-Object { "$_" }
"apply --check exit $LASTEXITCODE"
"new base $((Get-FileHash "$dir\draw.orig.cpp").Hash)"
"new copy $((Get-FileHash "$dir\draw.cpp").Hash)"
"patch $((Get-FileHash $patch).Hash)"
if (-not $NoCheck) {
  cmd /c "powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\check.ps1`" > `"$PSScriptRoot\check-copy.txt`" 2>&1"
  "check exit $LASTEXITCODE"
  $log = Get-Content "$PSScriptRoot\check-copy.txt"
  "warnings $(@($log | Select-String -Pattern ' warning: ').Count) errors $(@($log | Select-String -Pattern ' error: ').Count)"
  $log | Select-String -Pattern ' error: ' | Select-Object -First 10 | ForEach-Object { "$_" }
}

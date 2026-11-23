# Task #26: build plume-winsdk-compat.patch from Agent 2's p2 reference file (read-only on all inputs).
$ErrorActionPreference = 'Stop'
$root = '<workspace>'
$dr = Join-Path $root 'DimensionsRecomp'
$plume = Join-Path $dr 'thirdparty\plume'
$live = Join-Path $plume 'plume_d3d12.cpp'
$snap = Join-Path $root 'build\agent2\snap1\DimensionsRecomp\thirdparty\plume\plume_d3d12.cpp'
$pin = 'e0c8871b930dc1a6544bf457f2348c456b9d7e13'
$want = '564568D4D5853F22B6823884A79556C773C7679692B3C9022F4DD45B55F6E09E'
$latin1 = [Text.Encoding]::GetEncoding(28591)
$sha = [Security.Cryptography.SHA256]::Create()
function HexOf([byte[]]$b) { ([BitConverter]::ToString($sha.ComputeHash($b))).Replace('-', '') }

$snapHash = (Get-FileHash $snap -Algorithm SHA256).Hash
$liveHash = (Get-FileHash $live -Algorithm SHA256).Hash
"snap1 sha256 = $snapHash"
"live  sha256 = $liveHash"
if ($snapHash -ne $want) { throw "snap1 is not p2" }

$S = [IO.File]::ReadAllLines($snap)
$P = @(& git -C $plume show "${pin}:plume_d3d12.cpp")
"snap1 lines = $($S.Count); PIN blob lines = $($P.Count)"
$old = '            return D3D12_HEAP_TYPE_GPU_UPLOAD;'
if ($P[486] -ne $old) { throw "PIN L487 is [$($P[486])]" }
for ($k = 0; $k -lt 3; $k++) {
    if ($P[483 + $k] -ne $S[501 + $k]) { throw "pre-context $k differs" }
    if ($P[487 + $k] -ne $S[505 + $k]) { throw "post-context $k differs" }
}
$new = $S[504]
if ($new -notmatch '^ {12}return static_cast<D3D12_HEAP_TYPE>\(5\);') { throw "unexpected new line [$new]" }
if ($new -match '[^\x20-\x7E]') { throw 'non-ASCII or control character in the new line' }
"PIN L484-490 context == snap1 L502-508 context: OK"

# In-memory reverse of the hunk on the p2 bytes must give the pre-p2 (six-patch) file.
$tsv = Join-Path $root 'build\agent2\snap1\PATCHES-S1.tsv'
Get-Content $tsv | Where-Object { $_ -match 'plume' } | ForEach-Object { "TSV: $_" }
$text = $latin1.GetString([IO.File]::ReadAllBytes($snap))
$crlf = [regex]::Matches($text, "`r`n").Count
$bareLf = [regex]::Matches($text, "(?<!`r)`n").Count
"snap1 line endings: CRLF=$crlf bare-LF=$bareLf"
$count = [regex]::Matches($text, [regex]::Escape($new)).Count
if ($count -ne 1) { throw "new line occurs $count times" }
$pre = $text.Replace($new, $old)
"reverse-applied (pre-p2) sha256 = $(HexOf $latin1.GetBytes($pre))"

$out = New-Object System.Collections.Generic.List[string]
$out.Add('diff --git a/plume_d3d12.cpp b/plume_d3d12.cpp')
$out.Add('--- a/plume_d3d12.cpp')
$out.Add('+++ b/plume_d3d12.cpp')
$out.Add('@@ -502,7 +502,7 @@ namespace plume {')
for ($i = 501; $i -le 503; $i++) { $out.Add(' ' + $S[$i]) }
$out.Add('-' + $old)
$out.Add('+' + $new)
for ($i = 505; $i -le 507; $i++) { $out.Add(' ' + $S[$i]) }
$patchText = ($out -join "`r`n") + "`r`n"
$patch = Join-Path $dr 'tools\gpu-aot\patches\plume-winsdk-compat.patch'
if (Test-Path $patch) { throw "already exists: $patch" }
[IO.File]::WriteAllText($patch, $patchText, (New-Object Text.UTF8Encoding $false))
$pb = [IO.File]::ReadAllBytes($patch)
$pt = $latin1.GetString($pb)
"patch: bytes=$($pb.Length) CRLF=$([regex]::Matches($pt, "`r`n").Count) bare-LF=$([regex]::Matches($pt, "(?<!`r)`n").Count) sha256=$(HexOf $pb)"
foreach ($sib in 'plume-graphics-read.patch', 'plume-adapter-query.patch') {
    $st = $latin1.GetString([IO.File]::ReadAllBytes((Join-Path $dr "tools\gpu-aot\patches\$sib")))
    "sibling ${sib}: CRLF=$([regex]::Matches($st, "`r`n").Count) bare-LF=$([regex]::Matches($st, "(?<!`r)`n").Count)"
}
'--- patch ---'
Get-Content $patch
'--- line endings / links / config ---'
$lt = $latin1.GetString([IO.File]::ReadAllBytes($live))
"live line endings: CRLF=$([regex]::Matches($lt, "`r`n").Count) bare-LF=$([regex]::Matches($lt, "(?<!`r)`n").Count)"
try { & fsutil hardlink list $live } catch { "fsutil failed: $_" }
"plume core.autocrlf (local/effective) = [$(& git -C $plume config --get core.autocrlf)]"
"DR core.autocrlf (effective) = [$(& git -C $dr config --get core.autocrlf)]"
$ga = Join-Path $dr '.gitattributes'
if (Test-Path $ga) { Get-Content $ga | ForEach-Object { "gitattributes: $_" } } else { 'no DR .gitattributes' }
"git ls-files --eol for siblings:"
& git -C $dr ls-files --eol -- tools/gpu-aot/patches tools/gpu-aot/prepare_plume.py tools/gpu-aot/test_prepare_plume.py

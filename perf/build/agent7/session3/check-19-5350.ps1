# S3T-7 item 2: is #19's staged diff unchanged, and does it still apply to SDK 5350b1d? Paper only, scratch copy only.
# Read-only on DimensionsRecomp/rexglue-sdk (git show / rev-parse / diff --quiet only). Writes only under
# build/agent7/session3/scratch-5350/. Run from the workspace root.
$ErrorActionPreference = 'Stop'
$ws = (Get-Location).Path
$sdk = Join-Path $ws 'DimensionsRecomp\rexglue-sdk'
$st = Join-Path $ws 'build\agent7\s4-r1s2'
$scr = Join-Path $ws 'build\agent7\session3\scratch-5350'
$rev = '5350b1d'
$files = @(
  'include/rex/graphics/d3d12/command_processor.h',
  'include/rex/graphics/d3d12/deferred_command_list.h',
  'src/graphics/d3d12/command_processor.cpp',
  'src/graphics/d3d12/deferred_command_list.cpp',
  'src/graphics/d3d12/shared_memory.cpp',
  'src/graphics/d3d12/texture_cache.cpp')
$fail = 0
function Sha($p) { (Get-FileHash -Algorithm SHA256 $p).Hash }

"== 1. staged hashes vs SHA256SUMS.txt"
foreach ($line in Get-Content (Join-Path $st 'SHA256SUMS.txt')) {
  if ($line -notmatch '^([0-9A-F]{64})  (\S+)') { continue }
  $want = $Matches[1]; $rel = $Matches[2]
  $got = Sha (Join-Path $st $rel)
  $ok = $got -eq $want; if (-not $ok) { $fail++ }
  "{0} {1} {2}" -f ($(if ($ok) {'OK  '} else {'FAIL'})), $got.Substring(0,8), $rel
}
$rr = Sha (Join-Path $st 'RATE-REQUEST.md')
"RATE-REQUEST.md {0} (expect 1C2B8688...) {1}" -f $rr.Substring(0,16), $(if ($rr.StartsWith('1C2B8688')) {'OK'} else {$fail++; 'FAIL'})

"== 2. SDK HEAD and the 6 files at $rev"
$head = (git -C $sdk rev-parse HEAD).Trim()
"HEAD $head"
$full = (git -C $sdk rev-parse "$rev^{commit}").Trim()
"rev  $full"
if (Test-Path $scr) { Remove-Item -Recurse -Force $scr }
New-Item -ItemType Directory -Force $scr | Out-Null
foreach ($f in $files) {
  $dst = Join-Path $scr ('sdk/' + $f)
  New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
  # raw blob bytes: these paths carry `eol: lf` in the SDK's .gitattributes, so blob == worktree bytes (no CRLF step)
  cmd /c "git -C `"$sdk`" show ${full}:$f > `"$dst`""
  if ($LASTEXITCODE -ne 0) { "FAIL git show $f"; $fail++; continue }
  $eol = (git -C $sdk check-attr eol -- $f) -replace '^.*: eol: ',''
  $orig = Join-Path $st ('orig/sdk/' + $f)
  $live = Join-Path $sdk $f
  $hb = Sha $dst; $ho = Sha $orig; $hl = Sha $live
  $okb = $hb -eq $ho; $okl = $hl -eq $ho
  if (-not $okb) { $fail++ }
  "{0} blob@5350b1d={1} orig={2} live-worktree={3} live==orig:{4} eol:{5}  {6}" -f ($(if ($okb) {'OK  '} else {'FAIL'})), $hb.Substring(0,8), $ho.Substring(0,8), $hl.Substring(0,8), $okl, $eol, $f
}

"== 3. git apply --check on the scratch copy (outside any git repo: paths are cwd-relative)"
Push-Location (Join-Path $scr 'sdk')
try {
  $top = cmd /c "git rev-parse --show-toplevel 2>&1"
  "git toplevel from scratch: $top"
  $o = cmd /c "git -c core.autocrlf=false apply --check --verbose `"$st\s4-r1s2.diff`" 2>&1"; $e = $LASTEXITCODE
  $o; "forward exit $e (expect 0)"; if ($e -ne 0 -or ($o -match 'Skipped')) { $fail++ }
  # apply for real on the scratch copy, then compare with new/
  $o = cmd /c "git -c core.autocrlf=false apply `"$st\s4-r1s2.diff`" 2>&1"; $e = $LASTEXITCODE
  $o; "apply exit $e (expect 0)"; if ($e -ne 0) { $fail++ }
} finally { Pop-Location }
foreach ($f in $files) {
  if ($f -like '*deferred_command_list.cpp') { continue }
  $a = Sha (Join-Path $scr ('sdk/' + $f)); $n = Sha (Join-Path $st ('new/sdk/' + $f))
  $ok = $a -eq $n; if (-not $ok) { $fail++ }
  "{0} applied={1} new={2} {3}" -f ($(if ($ok) {'OK  '} else {'FAIL'})), $a.Substring(0,8), $n.Substring(0,8), $f
}
"== RESULT: $(if ($fail -eq 0) {'PASS'} else {"FAIL ($fail)"})"

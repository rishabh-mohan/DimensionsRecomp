# Agent 1: promote Agent 8's W5 S3d draft (README "Promoting it" steps 1, 2 and 4), then hash the window's inputs.
$ErrorActionPreference = 'Stop'
$w     = '<workspace>'
$src   = Join-Path $w 'build\agent8\readout\w5-draft'
$stamp = Get-Date -Format 'HH:mm'
$dstJ  = Join-Path $w 'bench\agent8\run\matrix-window5-s3d.json'
$dstC  = Join-Path $w 'bench\agent8\RUN-WINDOW5-S3D.cmd'
if ((Test-Path $dstJ) -or (Test-Path $dstC)) { throw 'already promoted (a target exists)' }

# JSON: title and first note only
$j = [IO.File]::ReadAllText((Join-Path $src 'matrix-window5-s3d.json'))
$oldTitle = 'Window 5, S3d line (DRAFT, Agent 8, task #10): '
$newTitle = "Window 5, S3d line (Agent 8's task #10 draft, promoted by Agent 1 at $stamp after W4b): "
$oldNote  = '"DRAFT (Agent 8, 2026-11-22 ~14:20, task #10 standby work). Not approved; for after window 4b. Kept in build/agent8/readout/w5-draft/. To use it, with Agent 1''s go: copy this file to bench/agent8/run/ and RUN-WINDOW5-S3D.cmd to bench/agent8/."'
$newNote  = '"Promoted by Agent 1 at ' + $stamp + ' on 2026-11-22, after window 4b (17/17 runs OK; codegen B within noise, so the S3d line; user delegation 14:44). Drafted by Agent 8 (task #10); the draft and its -PlanOnly checks stay in build/agent8/readout/w5-draft/."'
if (-not $j.Contains($oldTitle)) { throw 'JSON title not found' }
if (-not $j.Contains($oldNote))  { throw 'JSON first note not found' }
$j = $j.Replace($oldTitle, $newTitle).Replace($oldNote, $newNote)
$p = $j | ConvertFrom-Json
if ($j -match '[^\x00-\x7F]') { throw 'non-ASCII in JSON' }
if ($j -cmatch '(?<!S4-)DRAFT|Not approved') { throw 'DRAFT text left in JSON' }

# CMD: header comment and the missing-file message only (CRLF kept)
$c = [IO.File]::ReadAllText((Join-Path $src 'RUN-WINDOW5-S3D.cmd'))
$oldHdr = "rem DRAFT (Agent 8, 2026-11-22, task #10 standby work; not approved). Window 5, S3d line. It lives in`r`nrem build\agent8\readout\w5-draft\ until window 4b is done and Agent 1 approves it. To use it: copy this file to`r`nrem bench\agent8\ and matrix-window5-s3d.json to bench\agent8\run\. From any other folder it stops and starts nothing,`r`nrem and it also stops when a bin of the window has no MANIFEST.txt.`r`n"
$newHdr = "rem Window 5, S3d line: Agent 8's task #10 draft, promoted by Agent 1 at $stamp on 2026-11-22 after window 4b.`r`nrem It starts nothing when bench\agent8\run\ lacks run-matrix.ps1 or matrix-window5-s3d.json, or when a bin of the`r`nrem window has no MANIFEST.txt.`r`n"
$oldMsg = "echo This is the window 5 DRAFT (S3d line). Nothing was started.`r`necho To use it: copy it to bench\agent8\ and matrix-window5-s3d.json to bench\agent8\run\ (after window 4b, with Agent 1's go).`r`n"
$newMsg = "echo bench\agent8\run\ has no run-matrix.ps1 or matrix-window5-s3d.json. Nothing was started.`r`n"
if (-not $c.Contains($oldHdr)) { throw 'CMD header not found' }
if (-not $c.Contains($oldMsg)) { throw 'CMD draft message not found' }
$c = $c.Replace($oldHdr, $newHdr).Replace($oldMsg, $newMsg)
if ($c -match '[^\x00-\x7F]') { throw 'non-ASCII in CMD' }
if ($c -cmatch '(?<!S4-)DRAFT|not approved') { throw 'DRAFT text left in CMD' }
$cr = ([regex]::Matches($c, "`r")).Count; $lf = ([regex]::Matches($c, "`n")).Count
if ($cr -ne $lf) { throw "CMD line endings: CR $cr, LF $lf" }

[IO.File]::WriteAllText($dstJ, $j, [Text.Encoding]::ASCII)
[IO.File]::WriteAllText($dstC, $c, [Text.Encoding]::ASCII)
'promoted at {0}: JSON arms {1} ({2}); CMD CR {3} / LF {4}' -f $stamp, $p.arms.Count, (($p.arms | ForEach-Object id) -join ','), $cr, $lf

# R1 steps 4-6 of M10 stopR-rating.md (B67F3E2C). Run only after PAUSE is confirmed in queue.out.txt and no game runs.
$ErrorActionPreference = 'Stop'
$WS = '<workspace>'
$S4B = "$WS\build\agent3\s4b"
$SR = "$WS\build\agent3\session3\s33-rows\stopR"
function H8($p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.Substring(0, 8) }
if (Get-Process legodimensions -ErrorAction SilentlyContinue) { 'STOP: legodimensions runs'; exit 2 }
if (-not (Test-Path -LiteralPath "$S4B\PAUSE")) { 'STOP: PAUSE missing'; exit 2 }
if (Test-Path -LiteralPath "$S4B\queue.jsonl.bak-stopR") { 'STOP: .bak-stopR exists'; exit 2 }
$live0 = H8 "$S4B\queue.jsonl"
if ($live0 -ne '69C77DA7') { "STOP: live queue $live0"; exit 2 }
Copy-Item -LiteralPath "$SR\queue.jsonl.stopR" -Destination "$S4B\queue.jsonl.tmp-stopR"
$tmp = H8 "$S4B\queue.jsonl.tmp-stopR"
"step 4: tmp-stopR $tmp"
if ($tmp -ne 'CB502E8C') { 'STOP: tmp sha'; exit 2 }
try {
    [IO.File]::Replace("$S4B\queue.jsonl.tmp-stopR", "$S4B\queue.jsonl", "$S4B\queue.jsonl.bak-stopR")
} catch { "STOP: Replace threw: $($_.Exception.Message)"; exit 3 }
"step 5: Replace done $(Get-Date -Format 'HH:mm:ss')"
"step 6: queue.jsonl $(H8 "$S4B\queue.jsonl") (want CB502E8C), bak-stopR $(H8 "$S4B\queue.jsonl.bak-stopR") (want 69C77DA7), tmp left: $(Test-Path -LiteralPath "$S4B\queue.jsonl.tmp-stopR")"

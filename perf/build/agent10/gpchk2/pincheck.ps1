$ws = '<workspace>'
$k = Join-Path $ws 'build\agent3\gameplay'
foreach ($c in 'RUN-MANUAL.cmd', 'RUN-EXPLORE.cmd', 'RUN-GAMEPLAY.cmd') {
    $p = Join-Path $k $c
    $b = [IO.File]::ReadAllBytes($p)
    $lf = 0; $crlf = 0
    for ($i = 0; $i -lt $b.Length; $i++) { if ($b[$i] -eq 10) { if ($i -gt 0 -and $b[$i - 1] -eq 13) { $crlf++ } else { $lf++ } } }
    $nonascii = @($b | Where-Object { $_ -gt 127 }).Count
    $pins = @(Get-Content $p | Where-Object { $_ -match '^set "GPPIN_(\d+)=([0-9A-F]{64})\|([^"]+)"$' } | ForEach-Object { $null = $_ -match '^set "GPPIN_(\d+)=([0-9A-F]{64})\|([^"]+)"$'; [pscustomobject]@{ n = $Matches[1]; h = $Matches[2]; f = $Matches[3] } })
    $bad = 0
    foreach ($e in $pins) {
        $fp = Join-Path $ws $e.f
        $a = if (Test-Path -LiteralPath $fp -PathType Leaf) { (Get-FileHash -LiteralPath $fp -Algorithm SHA256).Hash } else { 'MISSING' }
        if ($a -ne $e.h) { "  MISMATCH $($e.n) $($e.f) is $a"; $bad++ }
    }
    $cnt = (Select-String -Path $p -Pattern 'pins.Count -ne (\d+)').Matches | ForEach-Object { $_.Groups[1].Value }
    "$c : CRLF=$crlf bareLF=$lf nonascii=$nonascii pins=$($pins.Count) mismatches=$bad countcheck=$($cnt -join ',') nums=$(($pins.n) -join ' ')"
}
"--- Compare-Object MANUAL vs EXPLORE"
Compare-Object (Get-Content (Join-Path $k 'RUN-MANUAL.cmd')) (Get-Content (Join-Path $k 'RUN-EXPLORE.cmd')) | ForEach-Object { "$($_.SideIndicator) $($_.InputObject)" }
"--- pin lines identical across the 3 cmds?"
$sets = foreach ($c in 'RUN-MANUAL.cmd', 'RUN-EXPLORE.cmd', 'RUN-GAMEPLAY.cmd') { ((Get-Content (Join-Path $k $c)) | Where-Object { $_ -match '^set "GPPIN_' }) -join "`n" }
"manual==explore: $($sets[0] -eq $sets[1]); manual==gameplay: $($sets[0] -eq $sets[2])"
"--- tags dir"
Get-ChildItem (Join-Path $k 'tags') -Force | ForEach-Object { "{0} {1} {2}" -f $_.Mode, $_.Length, $_.Name }

# probe.ps1 - small Windows PowerShell 5.1 behaviour probes used as evidence in REPORT.md section 5.
# Read-only; writes nothing. Run: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent11\s4a\slowstate3-check\probe.ps1
$r = "a,b`r`n1" | ConvertFrom-Csv
"short csv row: missing field is null: $($null -eq $r.b); passes the -ne '' filter: $($r.b -ne ''); [double] of it: $([double]$r.b)"
"[math]::Round(2.5,0)=$([math]::Round(2.5,0)) [math]::Round(3.5,0)=$([math]::Round(3.5,0)) [math]::Round(0.25,1)=$([math]::Round(0.25,1))"
$rx = 'timer_queue_precise_wait(=(true|1))?(\s|$)'
foreach ($s in @('--timer_queue_precise_wait=true', '--timer_queue_precise_wait=TRUE', '--timer_queue_precise_wait=false',
                 '--timer_queue_precise_wait false', '--timer_queue_precise_wait=yes', '--timer_queue_precise_wait=on',
                 '--no_timer_queue_precise_wait', '--timer_queue_precise_wait=true,x')) {
    "pcvar regex on '$s' -> $($s -match $rx)"
}
$o = [pscustomobject]@{ m = 'x'; a = 'Y' }, [pscustomobject]@{ m = 'x'; a = 'y' }
"Group-Object m, a on arms 'Y','y' -> groups: $(@($o | Group-Object m, a).Count)"
"ConvertTo-Json of params.cvar-like hashtable: " + ([pscustomobject]@{ timer_queue_precise_wait = $true } | ForEach-Object { "$_" })
[Threading.Thread]::CurrentThread.CurrentCulture = [Globalization.CultureInfo]'de-DE'
"de-DE culture: ConvertTo-Csv of 13.5 -> " + (([pscustomobject]@{ x = 13.5 }) | ConvertTo-Csv -NoTypeInformation | Select-Object -Last 1) + "; string interpolation -> $(13.5)"

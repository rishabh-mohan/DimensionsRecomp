<#
.SYNOPSIS
  Static check of the test G scripts: compiles testg_win.cs with Add-Type and parses
  testg_driver.ps1, testg_launch.ps1, testg_selftest.ps1, testg_session.ps1 and testg_dump.ps1
  (those present). Exit 0 if all are clean.
#>
$ErrorActionPreference = 'Continue'
$bad = 0
try {
    Add-Type -TypeDefinition ([IO.File]::ReadAllText((Join-Path $PSScriptRoot 'testg_win.cs'))) -Language CSharp -ErrorAction Stop
    $members = @([TestGWin].GetMethods() | Where-Object { $_.IsStatic -and $_.DeclaringType -eq [TestGWin] } | ForEach-Object { $_.Name } | Select-Object -Unique)
    Write-Host ("testg_win.cs: compiled; TestGWin static methods: {0}" -f ($members -join ', '))
}
catch {
    $bad++
    Write-Host "testg_win.cs: COMPILE FAILED: $($_.Exception.Message)"
    if ($_.Exception.Errors) { $_.Exception.Errors | ForEach-Object { Write-Host "  $_" } }
}
foreach ($n in 'testg_driver.ps1', 'testg_launch.ps1', 'testg_selftest.ps1', 'testg_session.ps1', 'testg_dump.ps1') {
    $f = Join-Path $PSScriptRoot $n
    if (-not (Test-Path -LiteralPath $f)) { continue }
    $tokens = $null; $errs = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($f, [ref]$tokens, [ref]$errs)
    Write-Host ("{0}: {1} parse error(s)" -f $n, $errs.Count)
    foreach ($e in $errs) { $bad++; Write-Host ("  line {0}: {1}" -f $e.Extent.StartLineNumber, $e.Message) }
}
if ($bad) { exit 1 }
exit 0

# test_quiet.ps1 - Agent 3, task #23: parse-checks the patched s4b-queue.ps1 and runs its QuietReason once, outside the
# queue (the function and $buildNames are taken from the file's AST, so this tests the exact patched text).
$ErrorActionPreference = 'Stop'
$t = $null; $e = $null
$path = (Resolve-Path 'build\agent3\s4b\s4b-queue.ps1').Path
$ast = [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$t, [ref]$e)
"parse errors: $($e.Count)"
foreach ($x in $e) { "  " + $x.ToString() }
$fn = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'QuietReason' }, $true)
$bn = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.AssignmentStatementAst] -and $n.Left.Extent.Text -eq '$buildNames' }, $true)
if (-not $fn -or -not $bn) { 'QuietReason or $buildNames not found'; exit 1 }
$QuietCpuPct = 20; $QuietSampleSec = 5
Invoke-Expression $bn.Extent.Text
Invoke-Expression $fn.Extent.Text
$script:quietTxt = ''
$r = QuietReason
"reason: [$r]"
"quietTxt: $script:quietTxt"
# negative test: a 0 % limit must report busy
$QuietCpuPct = 0
$r2 = QuietReason
"limit 0 -> reason: [$r2]"

# Static test of the kit shot job's LdKitCap type (extracted from rt-smoke-run.ps1 by AST): compile + NonBlack values.
param([string]$Kit = '<workspace>\build\agent2\s5\rt-smoke-run.ps1')
$t = $null; $e = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Kit, [ref]$t, [ref]$e)
"parse errors: $($e.Count)"
$hs = $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.StringConstantExpressionAst] -and $n.StringConstantType -eq 'SingleQuotedHereString' -and $n.Value -match 'class LdKitCap' }, $true) | Select-Object -First 1
if (-not $hs) { 'LdKitCap here-string not found'; exit 1 }
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition $hs.Value
'LdKitCap compiled'
$R = '<workspace>\build\agent2\s5'
foreach ($f in @("$R\rt-smoke\runs\20261126-013637-s5rt-f3a\kit-shots\shot-060s.png", "$R\rt-smoke\runs\20261126-014102-s5rt-f3b\kit-shots\shot-200s.png",
        "$R\nops-smoke\runs\20261125-201249-s5nops-t1\kit-shots\shot-120s.png", "$R\nops-smoke\runs\20261125-201719-s5nops-t2\kit-shots\shot-060s.png")) {
    '{0:N2}% {1}' -f (100 * [LdKitCap]::NonBlack($f)), $f.Substring($R.Length + 1)
}
"ScreenCopy(0): $([LdKitCap]::ScreenCopy([IntPtr]::Zero, (Join-Path $env:TEMP 'x.png')))"
$me = (Get-Process -Id $PID); "ScreenCopy(own console, not foreground on this desktop expected): $([LdKitCap]::ScreenCopy($me.MainWindowHandle, (Join-Path $env:TEMP 'ldkitcap-test.png')))"

# test-plan.ps1 - offline test of the staged run-matrix.ps1 plan logic (M8, session 3). Launches nothing.
# Extracts the functions from a run-matrix.ps1 (staged or pinned original) via the AST and runs Read-Matrix /
# Build-Plan / Get-PlanLines on given matrices. Its command line never contains "run-matrix.ps1", so harness guards
# do not count it as a runner.
param([string]$Script, [string]$Matrix, [string[]]$Only = @(), [int]$Repeats = 0, [switch]$ColdShared, [int]$WarmupRuns = -1, [switch]$Lines)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
. (Join-Path $repo 'bench\agent8\run\common.ps1')   # Set-StrictMode 2 + Resolve-RepoPath, as in run-matrix
$Quick = $false; $NoCold = $false; $PlanOnly = $true
$inv = [Globalization.CultureInfo]::InvariantCulture
$repoRoot = $repo
$tok = $null; $err = $null
$ast = [Management.Automation.Language.Parser]::ParseFile((Resolve-Path $Script).Path, [ref]$tok, [ref]$err)
if ($err.Count) { throw "parse errors in $Script" }
# top-level assignments of the key tables, then every top-level function
foreach ($st in $ast.EndBlock.Statements) {
    if ($st -is [Management.Automation.Language.AssignmentStatementAst] -and $st.Left.Extent.Text -match '^\$(TopKeys|ArmKeys|QuickKeys|NumKeys|D|QD|Est)$') { . ([scriptblock]::Create($st.Extent.Text)) }
    elseif ($st -is [Management.Automation.Language.FunctionDefinitionAst]) { . ([scriptblock]::Create($st.Extent.Text)) }
}
$R = Read-Matrix (Resolve-Path $Matrix).Path
if ($R.errors.Count) { "MATRIX ERRORS: $($R.errors -join ' | ')"; exit 3 }
$mx = $R.mx
$P = Build-Plan $R @($Only | ForEach-Object { $_ -split '[,;\s]+' } | Where-Object { $_ }) $true
"runs $($P.runs.Count); est_min $([math]::Ceiling($P.est_s / 60)); errors $($P.errors.Count)"
foreach ($ru in $P.runs) { $wm = $ru.ContainsKey('warm') -and $ru['warm']; "{0,2} {1,-14} round {2} cold {3} warm {4} scored {5}" -f $ru.seq, $ru.tag, $ru.round, $ru.cold, [bool]$wm, (-not ($ru.cold -or $wm)) }
if ($Lines) { Get-PlanLines $R $P | Where-Object { $_ -match '^(cold|warm|round|order|estimate)' } }

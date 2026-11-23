# e2e-driver.ps1: helper for test-scrnsave.ps1 -E2E (Agent 5, task #26). In its own powershell process it redirects
# Get-ItemProperty of 'HKCU:\Control Panel\Desktop' to a scratch key, then runs <Target> (a run-matrix.ps1) with the
# launcher's arguments plus -PlanOnly (reads only, starts nothing). It writes nothing itself.
param([string]$Target, [string]$Matrix, [string]$Only, [int]$Repeats, [string]$FakeDesk)
$global:FakeDesk = $FakeDesk; $global:RedirectHits = 0
function global:Get-ItemProperty {
    [CmdletBinding()]
    param([Parameter(Position = 0)][string[]]$Path, [string[]]$LiteralPath, [Parameter(Position = 1)][string[]]$Name)
    foreach ($pn in 'Path', 'LiteralPath') {
        if ($PSBoundParameters.ContainsKey($pn) -and @($PSBoundParameters[$pn]).Count -eq 1 -and @($PSBoundParameters[$pn])[0] -eq 'HKCU:\Control Panel\Desktop') {
            $PSBoundParameters[$pn] = @($global:FakeDesk); $global:RedirectHits++
        }
    }
    Microsoft.PowerShell.Management\Get-ItemProperty @PSBoundParameters
}
try {
    & $Target -Matrix $Matrix -Only $Only -Repeats $Repeats -ColdShared -NoPrompt -PlanOnly 2>&1 | ForEach-Object { "$_" }
    "E2E-EXIT=$LASTEXITCODE"
} catch { "E2E-THREW=$($_.Exception.Message)" }
"E2E-REDIRECTS=$global:RedirectHits"

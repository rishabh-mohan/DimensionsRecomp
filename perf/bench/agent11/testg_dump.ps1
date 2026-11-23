<#
.SYNOPSIS
  Offline analysis of a test G hang minidump (TestGWin.MiniDump, written by testg_driver.ps1 as
  hang-HHmmss.dmp): where it hung and what every thread was doing. No debugger needed.
.DESCRIPTION
  Report (stdout and -Out): header (dump time, pid, threads, main modules), one block per thread
  (id, name, suspend count, priority, CPU time, start address, RIP, RSP, heuristic call stack) and a
  summary (suspended threads, waiting threads with their first frame outside
  ntdll/KernelBase/kernel32/win32u, threads not in a wait, the UI thread).
  The call stack is a heuristic scan of the captured stack (no unwinding): values that point into a
  module right after a CALL instruction, checked in the module file found in -BinDir, the dump's
  directory, or at the path recorded in the dump. Symbols: <module>.map next to the module file
  (legodimensions.map), else the nearest PE export. Reads files only; starts nothing.
  -BinDir default: the bin named on the first line of MANIFEST.txt in the dump's directory (or its
  parent), else the dump's directory if it holds legodimensions.exe (testg_launch.ps1 run dirs
  hard-link the bin), else build\baseline-bin.
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_dump.ps1 -Dump build\agent11\runs\<run>\hang-201234.dmp
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_dump.ps1 -Dump x.dmp -BinDir build\agent2\devoff1-bin -Out x.txt -MaxFrames 40
#>
param(
    [Parameter(Mandatory = $true)][string]$Dump,
    [string]$BinDir = '',
    [string]$Out = '',
    [int]$MaxFrames = 24
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

function Find-Path([string]$p) {
    if ([IO.Path]::IsPathRooted($p)) { return $p }
    $here = Join-Path (Get-Location).Path $p
    if (Test-Path -LiteralPath $here) { return $here }
    return (Join-Path $root $p)
}

$dumpPath = [IO.Path]::GetFullPath((Find-Path $Dump))
if (-not (Test-Path -LiteralPath $dumpPath)) { Write-Host "testg_dump: no such dump: $dumpPath"; exit 2 }
$dumpDir = Split-Path -Parent $dumpPath

$binNote = ''
if ($BinDir) {
    $BinDir = [IO.Path]::GetFullPath((Find-Path $BinDir))
    $binNote = '-BinDir'
}
else {
    foreach ($m in @((Join-Path $dumpDir 'MANIFEST.txt'), (Join-Path (Split-Path -Parent $dumpDir) 'MANIFEST.txt'))) {
        if (-not (Test-Path -LiteralPath $m)) { continue }
        $first = Get-Content -LiteralPath $m -TotalCount 1
        if ($first -match '^#\s*(\S+)\s+-') {
            $cand = Join-Path $root ($Matches[1] -replace '/', '\')
            if (Test-Path -LiteralPath (Join-Path $cand 'legodimensions.exe')) { $BinDir = $cand; $binNote = "named in $m"; break }
        }
    }
    if (-not $BinDir -and (Test-Path -LiteralPath (Join-Path $dumpDir 'legodimensions.exe'))) { $BinDir = $dumpDir; $binNote = 'the dump directory holds legodimensions.exe' }
    if (-not $BinDir) { $BinDir = Join-Path $root 'build\baseline-bin'; $binNote = 'default' }
}
if (-not $Out) { $Out = [IO.Path]::ChangeExtension($dumpPath, '.txt') }
else { $Out = [IO.Path]::GetFullPath((Find-Path $Out)) }

if (-not ('TestGDump' -as [type])) {
    Add-Type -TypeDefinition ([IO.File]::ReadAllText((Join-Path $PSScriptRoot 'testg_dump.cs'))) -Language CSharp
}
try { $report = [TestGDump]::Analyze($dumpPath, $BinDir, $binNote, $MaxFrames) }
catch { Write-Host "testg_dump: analysis failed: $($_.Exception.InnerException.Message) $($_.Exception.Message)"; exit 2 }
[IO.File]::WriteAllText($Out, $report)
Write-Output $report.TrimEnd()
Write-Output "report: $Out"
exit 0

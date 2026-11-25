# Make build\agent8\session3\confirm\stage-confirm.ps1 from build\agent8\w-followup\stage-window.ps1 (read-only source).
$ErrorActionPreference = 'Stop'
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$src = Join-Path $Repo 'build\agent8\w-followup\stage-window.ps1'
$dst = Join-Path $PSScriptRoot 'stage-confirm.ps1'
$t = [IO.File]::ReadAllText($src)
$nl = if ($t.Contains("`r`n")) { "`r`n" } else { "`n" }
$subs = @(
  @('$Repo = (Resolve-Path (Join-Path $PSScriptRoot ''..\..\..'')).Path', '$Repo = (Resolve-Path (Join-Path $PSScriptRoot ''..\..\..\..'')).Path'),
  @(('    [int]$QueueGapS = 20' + $nl + ')'), ('    [int]$QueueGapS = 20,' + $nl + '    [string]$Launcher = ''bench\agent5\day\run-day.ps1''' + $nl + ')')),
  @('$wfDir = Join-Path $Repo ''build\agent8\w-followup''', '$wfDir = Join-Path $Repo ''build\agent8\session3\confirm'''),
  @('if ($Promote -and (', ('if ($Promote) { Usage ''stage-confirm.ps1 is TEST/RECHECK only (M8 never promotes without the Overseer)'' }' + $nl + 'if ($Promote -and (')),
  @('$LauncherPath = Join-Path $Repo ''bench\agent5\launch\run-night.ps1''', '$LauncherPath = Join-Path $Repo $Launcher'),
  @('$rep = Join-Path $Repo ''build\agent8\readout\w-followup''', '$rep = Join-Path $PSScriptRoot ''stage'''),
  @('$L.Add("launcher: bench\agent5\launch\run-night.ps1 sha256', '$L.Add("launcher: $Launcher sha256'),
  @('$L.Add("Window staging (Agent 8, run-2 task #7, build\agent8\w-followup\stage-window.ps1), $when")', '$L.Add("Window staging (M8 session 3, build\agent8\session3\confirm\stage-confirm.ps1 = stage-window.ps1 with -Launcher $Launcher), $when; latest-start line below uses the night rule (07:30); the day launcher instead refuses when now + estimate + slack passes its -StopAt")')
)
foreach ($s in $subs) {
  $n = ([regex]::Matches($t, [regex]::Escape($s[0]))).Count
  if ($n -ne 1) { throw "pattern hits $n times: $($s[0])" }
  $t = $t.Replace($s[0], $s[1])
}
[IO.File]::WriteAllText($dst, $t, (New-Object Text.UTF8Encoding $false))
"written $dst $((Get-FileHash $dst).Hash)"

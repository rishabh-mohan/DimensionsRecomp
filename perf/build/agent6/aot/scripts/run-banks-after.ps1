# Banks after the slot: waits for run-slot.ps1's "float-blend inputs exit=" line, then runs the
# unmodified build_float_blend_indices_bank.py (and optionally the instanced bank) pinned to -Mask
# until -DropAt, then to -DropMask (1 CPU) for the python process and every live child (DXC).
# Children spawned later inherit the parent's mask (Windows process-affinity inheritance).
param(
  [long]$Mask = 0xFC0,
  [string]$DropAt = '20:14:30',
  [long]$DropMask = 0x20,
  [string]$WaitUntil = '20:16:00',
  [switch]$NoWait,
  [switch]$SkipFloatBlend,
  [switch]$Instanced,
  [int]$InstancedJobs = 1
)
$ErrorActionPreference = 'Continue'
$w = '<workspace>'
$r = "$w\DimensionsRecomp"
$a = "$r\rexlego\out\native-gpu\aot"
$s = "$w\build\agent6\aot\scripts"
$slotLog = "$w\build\agent6\aot\logs\slot.log"
$dxc = "$r\research\dxc-1.9.2609\bin\x64\dxc.exe"
$mc = "$w\toolchain\llvm-23.1.6\bin\llvm-mc.exe"
$env:PYTHONDONTWRITEBYTECODE = '1'
$drop = [datetime]::ParseExact($DropAt, 'HH:mm:ss', $null)
$waitEnd = [datetime]::ParseExact($WaitUntil, 'HH:mm:ss', $null)
function Now { Get-Date -Format 'HH:mm:ss' }
function Show-Files([string]$Dir, [string]$Filter) {
  Get-ChildItem $Dir -File -Filter $Filter -ErrorAction SilentlyContinue |
    ForEach-Object { Write-Host "  $($_.Name) bytes=$($_.Length) sha256=$((Get-FileHash $_.FullName -Algorithm SHA256).Hash)" }
}
function Set-TreeAffinity([int]$RootId, [long]$M) {
  $all = @(Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId)
  $ids = New-Object System.Collections.Generic.List[int]
  $ids.Add($RootId)
  for ($i = 0; $i -lt $ids.Count; $i++) {
    $cur = $ids[$i]
    foreach ($c in $all) { if ($c.ParentProcessId -eq $cur -and -not $ids.Contains([int]$c.ProcessId)) { $ids.Add([int]$c.ProcessId) } }
  }
  $n = 0
  foreach ($id in $ids) { try { (Get-Process -Id $id -ErrorAction Stop).ProcessorAffinity = [IntPtr]$M; $n++ } catch {} }
  return $n
}
function Invoke-Py([string]$Name, [string]$Arguments) {
  $psi = New-Object System.Diagnostics.ProcessStartInfo 'python'
  $psi.Arguments = $Arguments
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $t0 = Get-Date
  $p = [Diagnostics.Process]::Start($psi)
  $dropped = ((Get-Date) -ge $drop)
  $m = if ($dropped) { $DropMask } else { $Mask }
  $p.ProcessorAffinity = [IntPtr]$m
  Write-Host "[$(Now)] start $Name pid=$($p.Id) mask=0x$('{0:X}' -f $m) (drops to 0x$('{0:X}' -f $DropMask) at $DropAt)"
  Write-Host "  cmd: python $Arguments"
  $so = $p.StandardOutput.ReadToEndAsync(); $se = $p.StandardError.ReadToEndAsync()
  while (-not $p.WaitForExit(1000)) {
    if (-not $dropped -and (Get-Date) -ge $drop) {
      $n = Set-TreeAffinity $p.Id $DropMask
      $dropped = $true
      Write-Host "[$(Now)] affinity dropped to 0x$('{0:X}' -f $DropMask) on $n process(es)"
    }
  }
  $p.WaitForExit()
  Write-Host "--- $Name stdout"; Write-Host $so.Result; Write-Host "--- $Name stderr"; Write-Host $se.Result
  Write-Host "[$(Now)] end $Name exit=$($p.ExitCode) wall_s=$([math]::Round(((Get-Date)-$t0).TotalSeconds,2)) cpu_s(python only)=$([math]::Round($p.TotalProcessorTime.TotalSeconds,2))"
  return $p.ExitCode
}

Write-Host "[$(Now)] run-banks-after start (mask 0x$('{0:X}' -f $Mask) until $DropAt, then 0x$('{0:X}' -f $DropMask); instanced=$Instanced jobs=$InstancedJobs)"
$inputsRc = 0
if (-not $NoWait) {
  $line = $null
  while ((Get-Date) -lt $waitEnd) {
    $line = Select-String -Path $slotLog -Pattern 'float-blend inputs exit=(\d+)' -ErrorAction SilentlyContinue | Select-Object -Last 1
    if ($line) { break }
    Start-Sleep -Seconds 2
  }
  if (-not $line) { Write-Host "[$(Now)] no 'float-blend inputs exit=' line by $WaitUntil; giving up"; exit 5 }
  $inputsRc = [int]$line.Matches[0].Groups[1].Value
  Write-Host "[$(Now)] slot float-blend inputs exit=$inputsRc"
}
if (-not $SkipFloatBlend) {
  if ($inputsRc -ne 0) {
    if (Test-Path "$a\float-blend-inputs") { Remove-Item -Recurse -Force "$a\float-blend-inputs" }
    $inputsRc = Invoke-Py 'make_float_blend_inputs' "`"$s\make_float_blend_inputs.py`" `"$a\float-blend-inputs`" --source `"$a\hlsl-dump`""
    Write-Host "[$(Now)] float-blend inputs (re-run) exit=$inputsRc"
    if ($inputsRc -ne 0) { exit 6 }
  }
  if (Test-Path "$a\float-blend-indices-bank") { Remove-Item -Recurse -Force "$a\float-blend-indices-bank" }
  $rc = Invoke-Py 'float-blend-indices-bank' "`"$r\tools\gpu-aot\build_float_blend_indices_bank.py`" `"$a\float-blend-indices-bank`" --source `"$a\float-blend-inputs`" --dxc `"$dxc`" --llvm-mc `"$mc`""
  Write-Host "[$(Now)] float-blend exit=$rc"
  Show-Files "$a\float-blend-indices-bank" 'float-blend-indices-bank.*'
  Show-Files "$a\float-blend-indices-bank" 'verification.json'
}

if ($Instanced) {
  # Built in a .partial dir and renamed only on success, so a copy taken mid-build never sees a half bank
  # (CMake enables instancing when .obj and .cpp both exist). The .obj embeds the blob, so the rename is safe.
  $dst = "$a\instanced-constants-bank"; $tmp = "$dst.partial"
  if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
  $rc2 = Invoke-Py 'instanced-constants-bank' "`"$r\tools\gpu-aot\build_instanced_constants_bank.py`" `"$tmp`" --source `"$a\hlsl-dump`" --dxc `"$dxc`" --llvm-mc `"$mc`" --jobs $InstancedJobs"
  Write-Host "[$(Now)] instanced exit=$rc2"
  if ($rc2 -eq 0 -and (Test-Path "$tmp\verification.json") -and (Test-Path "$tmp\instanced-constants-bank.obj")) {
    if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
    Rename-Item $tmp (Split-Path $dst -Leaf)
    Write-Host "[$(Now)] STAGED $dst"
  }
  Show-Files $dst 'instanced-constants-bank.*'
  Show-Files $dst 'verification.json'
}
Write-Host "[$(Now)] run-banks-after end"

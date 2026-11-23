# Agent 9 chain6 (session 3, 02:06): pre-stage the recipe step 9 rollback trees, so a B failure doesn't wait on a regen.
#   rb1-nolocal    = batch-nolr minus the four *_as_local keys and cr_compare_so_zero (step 9.1: the game gate fails)
#   rb2-nomusttail = batch-nolr minus musttail_calls (step 9.2: a TU fails to compile with musttail)
# Each: config (make-batch-config.ps1 -Drop) -> gen -> gate -> install tree -> hashes; then count2 batch-nolr vs each.
# A rollback tree is built ONLY after a B failure and Agent 1's GO. B itself is built from install\batch-nolr only.
$ErrorActionPreference = 'Stop'
$R = '<workspace>'
Set-Location $R
$steps = "$R\build\agent9\logs\chain6-steps.txt"
function Note([string]$m) { "$(Get-Date -Format HH:mm:ss) chain6 $m" | Tee-Object -Append -FilePath $steps }
$variants = [ordered]@{
  'rb1-nolocal'    = 'ctr_as_local,xer_as_local,reserved_as_local,cr_as_local,cr_compare_so_zero'
  'rb2-nomusttail' = 'musttail_calls'
}
Note 'BEGIN rollback trees rb1-nolocal, rb2-nomusttail (config -> gen -> gate -> install), then count2 vs batch-nolr'
foreach ($v in $variants.Keys) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\make-batch-config.ps1 -Out "$v.toml" -Drop $variants[$v] *>&1 | Tee-Object -Append -FilePath $steps
  if ($LASTEXITCODE) { Note "[$v] make-batch-config exit=$LASTEXITCODE"; exit 1 }
  $cfg = "build\agent9\configs\$v.toml"
  foreach ($k in @('skip_lr') + @($variants[$v] -split ',')) {
    if (Select-String -Path $cfg -Pattern "^\s*$k\s*=" -Quiet) { Note "[$v] $cfg still sets $k"; exit 1 }
  }
  Note ("[$v] config sha256=" + (Get-FileHash $cfg -Algorithm SHA256).Hash)
  & powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\gen.ps1 -Variant $v -ConfigFile $cfg *>&1 | Tee-Object -Append -FilePath $steps
  $g = $LASTEXITCODE
  Note "[$v] gen exit=$g"
  if ($g) { exit 1 }
  $log = Get-Content "build\agent9\logs\gen-$v.log" -Raw
  $blocked = ([regex]::Matches($log, 'Code generation blocked')).Count
  $handoff = ([regex]::Matches($log, '(?i)handoff')).Count
  Note "[$v] gate: blocked=$blocked handoff_lines=$handoff"
  if ($blocked) { exit 1 }
  & powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\make-install.ps1 -Variant $v *>&1 | Tee-Object -Append -FilePath $steps
  Note "[$v] make-install exit=$LASTEXITCODE"
  if ($LASTEXITCODE) { exit 1 }
  $inst = "build\agent9\install\$v"
  Note ("[$v] SHA256SUMS.txt sha256=" + (Get-FileHash "$inst\SHA256SUMS.txt" -Algorithm SHA256).Hash + " lines=" + (Get-Content "$inst\SHA256SUMS.txt").Count)
  Note ("[$v] install config sha256=" + (Get-FileHash "$inst\legodimensions_config.toml" -Algorithm SHA256).Hash)
}
foreach ($v in $variants.Keys) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent9\cpu2.ps1 -Command "py -3 build\agent9\count2.py build\agent9\diff\$v batch-nolr=build\agent9\generated\batch-nolr\default $v=build\agent9\generated\$v\default" *> "build\agent9\logs\count2-$v.txt"
  Note "[$v] count2 exit=$LASTEXITCODE (build\agent9\logs\count2-$v.txt)"
}
Note 'END'

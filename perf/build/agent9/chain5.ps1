# Agent 9 chain5 (23:52): batch without skip_lr (Agent 10 Review 4 row 21; Agent 1 directive 23:51).
#   config batch-nolr.toml -> gen batch-nolr -> install tree batch-nolr -> count2 off3 vs batch-nolr
# The 23:28 tree build\agent9\install\batch (with skip_lr) is kept for diffing; it must not be built.
$ErrorActionPreference = 'Stop'
$R = '<workspace>'
Set-Location $R
$steps = "$R\build\agent9\logs\chain5-steps.txt"
function Note([string]$m) { "$(Get-Date -Format HH:mm:ss) chain5 $m" | Tee-Object -Append -FilePath $steps }
Note 'BEGIN make-batch-config -> gen batch-nolr -> make-install batch-nolr -> count2 off3 vs batch-nolr'
& powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\make-batch-config.ps1 -Out batch-nolr.toml *>&1 | Tee-Object -Append -FilePath $steps
if ($LASTEXITCODE) { Note "make-batch-config exit=$LASTEXITCODE"; exit 1 }
if (Select-String -Path build\agent9\configs\batch-nolr.toml -Pattern '^\s*skip_lr\s*=' -Quiet) { Note 'batch-nolr.toml still sets skip_lr'; exit 1 }
Note ("config sha256=" + (Get-FileHash build\agent9\configs\batch-nolr.toml -Algorithm SHA256).Hash)
& powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\gen.ps1 -Variant batch-nolr -ConfigFile build\agent9\configs\batch-nolr.toml *>&1 | Tee-Object -Append -FilePath $steps
$g = $LASTEXITCODE
Note "gen exit=$g"
if ($g) { exit 1 }
$log = Get-Content build\agent9\logs\gen-batch-nolr.log -Raw
$blocked = ([regex]::Matches($log, 'Code generation blocked')).Count
$handoff = ([regex]::Matches($log, '(?i)handoff')).Count
Note "gate: blocked=$blocked handoff_lines=$handoff"
if ($blocked) { exit 1 }
& powershell -NoProfile -ExecutionPolicy Bypass -File build\agent9\make-install.ps1 -Variant batch-nolr *>&1 | Tee-Object -Append -FilePath $steps
Note "make-install exit=$LASTEXITCODE"
if ($LASTEXITCODE) { exit 1 }
Note ("SHA256SUMS.txt sha256=" + (Get-FileHash build\agent9\install\batch-nolr\SHA256SUMS.txt -Algorithm SHA256).Hash + " lines=" + (Get-Content build\agent9\install\batch-nolr\SHA256SUMS.txt).Count)
Note ("install config sha256=" + (Get-FileHash build\agent9\install\batch-nolr\legodimensions_config.toml -Algorithm SHA256).Hash)
& powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent9\cpu2.ps1 -Command "py -3 build\agent9\count2.py build\agent9\diff\batch-nolr off3=build\agent9\generated\off3\default batch-nolr=build\agent9\generated\batch-nolr\default" *> build\agent9\logs\count2-batch-nolr.txt
Note "count2 exit=$LASTEXITCODE (build\agent9\logs\count2-batch-nolr.txt)"
Note 'END'

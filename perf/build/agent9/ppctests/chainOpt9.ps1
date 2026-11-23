# T8 opt9 run (S2.10's 9 keys = opt without skip_lr = LEGO build B's key set), one Agent 9 CPU slot per step.
#   powershell -NoProfile -File build/agent9/ppctests/chainOpt9.ps1 *> build/agent9/ppctests/logs/chainOpt9.txt
$ErrorActionPreference = 'Continue'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')))
$c = 'bench/agent9/cpu2.ps1'
"$(Get-Date -Format HH:mm:ss) START chainOpt9"
powershell -NoProfile -File $c -Command "powershell -NoProfile -File bench/agent9/ppctests/gen.ps1 -Variant opt9"; "$(Get-Date -Format HH:mm:ss) C0 opt9 gen exit=$LASTEXITCODE"
powershell -NoProfile -File $c -Command "powershell -NoProfile -File bench/agent9/ppctests/compile.ps1 -Variant opt9 -Tu functions"; "$(Get-Date -Format HH:mm:ss) C1 opt9 functions exit=$LASTEXITCODE"
powershell -NoProfile -File $c -Command "powershell -NoProfile -File bench/agent9/ppctests/link.ps1 -Variant opt9"; $l = $LASTEXITCODE; "$(Get-Date -Format HH:mm:ss) C2 opt9 link exit=$l"
if ($l -eq 2) {
  powershell -NoProfile -File $c -Command "powershell -NoProfile -File bench/agent9/ppctests/compile.ps1 -Variant opt9 -Tu cases"; "$(Get-Date -Format HH:mm:ss) C3 opt9 cases exit=$LASTEXITCODE"
  powershell -NoProfile -File $c -Command "powershell -NoProfile -File bench/agent9/ppctests/link.ps1 -Variant opt9"; "$(Get-Date -Format HH:mm:ss) C4 opt9 relink exit=$LASTEXITCODE"
}
powershell -NoProfile -File $c -Command "& bench/agent9/ppctests/runtests.ps1 -Variants default,opt,crso,opt9"; "$(Get-Date -Format HH:mm:ss) C5 runtests exit=$LASTEXITCODE"
"$(Get-Date -Format HH:mm:ss) END chainOpt9"

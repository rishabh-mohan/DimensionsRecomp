$env:PYTHONDONTWRITEBYTECODE = 1
$f = 'build/agent9/s4/scene-walk/find.py'
$pairs = @(
  @('210','sub_82AFAB68'), @('216','sub_82AF9BC0'), @('173','sub_82FCC500'), @('220','sub_82FCB308'),
  @('340','sub_82F050B0'), @('230','sub_82EF8C18'), @('41','sub_82F0CCD8'), @('45','sub_82EFE948'),
  @('266','sub_82EF3B38'), @('34','sub_82EF3180'), @('397','sub_82EF2FE0'), @('193','sub_82EF2E28'),
  @('176','sub_82EF2368'), @('391','sub_82B61580'), @('137','sub_82B62C1C'), @('135','sub_82B62528'),
  @('259','sub_82B53308'), @('59','sub_82FEB7B8')
)
foreach ($p in $pairs) { Write-Output ("TU " + $p[0]); python $f def $p[0] $p[1] }
Write-Output '--- REX_HOOK in rexlego/src (non-recursive by folder)'
$dirs = @('DimensionsRecomp/rexlego/src', 'DimensionsRecomp/rexlego/src/gpu_native', 'DimensionsRecomp/rexlego/src/gpu')
foreach ($d in $dirs) {
  Get-ChildItem -Path $d -File -Include *.cpp,*.h,*.inc -ErrorAction SilentlyContinue | Out-Null
  Select-String -Path (Join-Path $d '*.cpp'), (Join-Path $d '*.h') -Pattern 'REX_HOOK|REX_PPC_HOOK|PPC_HOOK|HOOK_FUNC|RegisterHook|0x82[0-9A-Fa-f]{6}|sub_82[0-9A-Fa-f]{6}' -ErrorAction SilentlyContinue | ForEach-Object { "{0}:{1}: {2}" -f $_.Path.Replace((Get-Location).Path + '\', ''), $_.LineNumber, $_.Line.Trim().Substring(0, [Math]::Min(220, $_.Line.Trim().Length)) }
}

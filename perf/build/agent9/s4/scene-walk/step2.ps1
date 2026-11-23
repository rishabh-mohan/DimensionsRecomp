$env:PYTHONDONTWRITEBYTECODE = 1
$f = 'build/agent9/s4/scene-walk/find.py'
$pairs = @(
  @('210','sub_82AFAB68'), @('216','sub_82AF9BC0'), @('173','sub_82FCC500'), @('220','sub_82FCB308'),
  @('340','sub_82F050B0'), @('230','sub_82EF8C18'), @('41','sub_82F0CCD8'), @('45','sub_82EFE948'),
  @('266','sub_82EF3B38'), @('34','sub_82EF3180'), @('397','sub_82EF2FE0'), @('193','sub_82EF2E28')
)
foreach ($p in $pairs) { Write-Output ("=== TU " + $p[0] + " " + $p[1]); python $f calls $p[0] $p[1] }

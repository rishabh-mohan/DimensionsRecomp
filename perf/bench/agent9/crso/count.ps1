# Counts CR compares with SO folded to zero ({}), with SO read from xer, and
# ctx.xer reads, per generated variant.
#   powershell -NoProfile -File bench\agent9\cpu2.ps1 -File bench\agent9\crso\count.ps1
param([string[]]$Variants = @('off2', 'crso', 'locA', 'crsoA'))
$R = '<workspace>'
$out = "$R\bench\agent9\crso\counts.txt"
$folded = [regex]'compare<[^>]+>\([^;\n]*,\s*\{\}\);'
$unfolded = [regex]'compare<[^>]+>\([^;\n]*,\s*(ctx\.)?xer\);'
$soStore = [regex]'(ctx\.)?cr0\.so = 0;'
$soLoad = [regex]'(ctx\.)?cr0\.so = (ctx\.)?xer\.so;'
"$(Get-Date -Format HH:mm:ss) count BEGIN" | Out-File -Append $out
foreach ($v in $Variants) {
  $dir = "$R\build\agent9\generated\$v\default"
  if (-not (Test-Path $dir)) { "${v}: missing" | Out-File -Append $out; continue }
  $f = 0; $u = 0; $ss = 0; $sl = 0; $hit = ''
  foreach ($file in Get-ChildItem $dir -Filter '*_recomp.*.cpp') {
    $text = [IO.File]::ReadAllText($file.FullName)
    $f += $folded.Matches($text).Count
    $u += $unfolded.Matches($text).Count
    $ss += $soStore.Matches($text).Count
    $sl += $soLoad.Matches($text).Count
    $i = $text.IndexOf('DEFINE_REX_FUNC(sub_83E5C88C)')
    if ($i -ge 0) {
      $j = $text.IndexOf('DEFINE_REX_FUNC(', $i + 10)
      if ($j -lt 0) { $j = $text.Length }
      $body = $text.Substring($i, $j - $i)
      $hit = "sub_83E5C88C in $($file.Name): folded=$($folded.Matches($body).Count) unfolded=$($unfolded.Matches($body).Count)"
    }
  }
  "${v}: compares folded={} $f, from xer $u; stwcx cr0.so=0 $ss, cr0.so=xer.so $sl; $hit" | Out-File -Append $out
}
"$(Get-Date -Format HH:mm:ss) count END" | Out-File -Append $out

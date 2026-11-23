# Tail-chain depth test (see chain.cpp). Holds no slot itself: every clang run and every test run
# takes ONE Agent 9 slot for itself (slot1.ps1, same rules as cpu2.ps1; waits while
# bench/agent9/QUIET exists):
#   powershell -NoProfile -File bench/agent9/musttail/chain.ps1 *> bench/agent9/musttail/chain.log
# Builds {-O0,-O2} x {escape 0,1} x {musttail 0,1} with the real game flags and the real generated
# headers and runs each with 1,000,000 chained hops -> chain.txt
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
. (Join-Path $root 'env/devshell.ps1') | Out-Null
. (Join-Path $PSScriptRoot 'game_flags.ps1')
. (Join-Path $PSScriptRoot 'slot1.ps1')
Set-Location $PSScriptRoot
$out = Join-Path $PSScriptRoot 'gen_out'
New-Item -ItemType Directory -Force $out | Out-Null
$depth = 1000000
$lines = @("tail-chain depth test: chain_a->b->c->a..., $depth hops; real game flags + generated headers; default 1 MB main-thread stack; 0xC00000FD = host stack overflow")
$mode = @()
foreach ($opt in '-O0', '-O2') {
  foreach ($esc in 0, 1) {
    foreach ($mt in 0, 1) {
      $name = "chain_$($opt.TrimStart('-'))_mt$($mt)_esc$($esc)"
      $exe = Join-Path $out "$name.exe"
      $buildLog = Join-Path $out "$name.build.txt"
      $cargs = @($GameFlags) + $mode + @($opt, "-DMUSTTAIL=$mt", "-DESCAPE=$esc", 'chain.cpp', 'chain_hook.cpp', '-lkernel32', '-o', $exe)
      Invoke-InSlot { & clang++ @cargs *> $buildLog }
      if ($LASTEXITCODE -and $mode.Count -eq 0) {
        $lines += "real-pch build of $name failed (gen_out/$name.build.txt); falling back to -DCHAIN_NO_PCH"
        $mode = @('-DCHAIN_NO_PCH')
        $cargs = @($GameFlags) + $mode + @($opt, "-DMUSTTAIL=$mt", "-DESCAPE=$esc", 'chain.cpp', 'chain_hook.cpp', '-lkernel32', '-o', $exe)
        Invoke-InSlot { & clang++ @cargs *> $buildLog }
      }
      if ($LASTEXITCODE) { $lines += ('{0,-20} build failed (gen_out/{0}.build.txt)' -f $name); continue }
      $sFile = Join-Path $out "$name.s"
      $sargs = @($GameFlags) + $mode + @($opt, "-DMUSTTAIL=$mt", "-DESCAPE=$esc", '-S', '-masm=intel', 'chain.cpp', '-o', $sFile)
      Invoke-InSlot { & clang++ @sargs *> $null }
      $asm = @(Get-Content $sFile -ErrorAction SilentlyContinue)
      $nCall = @($asm | Where-Object { $_ -cmatch '^\s+call\s+(__imp__)?chain_[abc]\b' }).Count
      # tail jumps: jmp, or jcc when clang folds `if (..) return; f()` into a conditional tail call
      $nJmp = @($asm | Where-Object { $_ -cmatch '^\s+j[a-z]*\s+(__imp__)?chain_[abc]\b' }).Count
      $runOut = Join-Path $out "$name.run.txt"
      $res = Invoke-InSlot {
        $p = Start-Process -FilePath $exe -ArgumentList "$depth" -NoNewWindow -PassThru -RedirectStandardOutput $runOut
        $null = $p.Handle
        if (-not $p.WaitForExit(120000)) { try { $p.Kill() } catch { }; 'TIMEOUT' }
        elseif ($p.ExitCode -eq 0) { 'PASS' }
        elseif ($p.ExitCode -eq -1073741571) { 'STACK OVERFLOW (0xC00000FD)' }
        else { "exit $($p.ExitCode)" }
      }
      $printed = (@(Get-Content $runOut -ErrorAction SilentlyContinue) -join ' ')
      $lines += ('{0,-20} musttail={1} escape={2}: {3,-28} asm: call chain_x={4} tail jmp/jcc chain_x={5}  {6}' -f $name, $mt, $esc, $res, $nCall, $nJmp, $printed)
      $lines | Set-Content -Encoding ascii (Join-Path $PSScriptRoot 'chain.txt')
    }
  }
}
if ($mode.Count) { $lines += 'NOTE: built with -DCHAIN_NO_PCH (stand-in headers: same signature, same weak-alias DEFINE_REX_FUNC)' }
$lines | Tee-Object -FilePath (Join-Path $PSScriptRoot 'chain.txt')

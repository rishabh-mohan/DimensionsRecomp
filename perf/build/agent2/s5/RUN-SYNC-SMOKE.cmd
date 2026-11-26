@echo off
rem RUN-SYNC-SMOKE.cmd - S5 sync-pipeline diag smoke (M2) on build\agent2\s5\devs5sync-bin, two arms, one approval:
rem   off = plain default; on = d3d12_log_sync_pipeline_creation=true;slow_frame_log_ms=1 (attribution only, D2).
rem   attract-long pad route, 240 s each, 20 s settle, then sync_smoke_post.py (D3 checks + 322 ms attribution).
rem   RUN-SYNC-SMOKE.cmd            real run (interactive desktop; ~2 x 4.5 min + 20 s + checks, about 10 min; self-closing)
rem   RUN-SYNC-SMOKE.cmd dryrun     no game: verify-bins, command lines, run-game -DryRun, post self-test; exit 0 = pass
rem   extra words: allowhidden, onfirst
setlocal
set "KIT=%~dp0"
set "DRY="
for %%A in (%*) do if /i "%%~A"=="dryrun" set "DRY=1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%KIT%sync-smoke-run.ps1" %*
set "RC=%ERRORLEVEL%"
echo [sync-smoke] exit %RC%
if not defined DRY timeout /t 15 >nul 2>&1
exit /b %RC%

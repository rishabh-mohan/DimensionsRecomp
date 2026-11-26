@echo off
rem RUN-DUMP.cmd - S5 phase 0.4(a) (M16): attract shader dump on a COPY of nativefinal2-bin.
rem   RUN-DUMP.cmd            real run (interactive desktop; copy ~10 s + 300 s game + close/post ~1 min = about 6.5 min; self-closing)
rem   RUN-DUMP.cmd dryrun     no game: preconditions, copy + hash check, command line, run-game -DryRun, post self-test; exit 0 = pass
rem   extra words: allowhidden, long (540 s instead of 300 s: about 10.5 min)
rem Output: build\agent16\dump\runs\<stamp>-dump-attract-nf2, shader-dumps-<stamp>, trace-<stamp>, pack-input-<stamp>,
rem         post\dump-post-<stamp>.txt, post\SHA256SUMS-<stamp>.txt, LATEST.txt
setlocal
set "KIT=%~dp0dump\"
set "DRY="
for %%A in (%*) do if /i "%%~A"=="dryrun" set "DRY=1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%KIT%run-dump.ps1" %*
set "RC=%ERRORLEVEL%"
echo [dump] exit %RC%
if not defined DRY timeout /t 15 >nul 2>&1
exit /b %RC%

"""mkpins_rt.py - (re)write RUN-RT-SMOKE.cmd with sha256 pins of the kit scripts and every helper they run (M2).

Same conventions as mkpins.py (RUN-NOPS-SMOKE.cmd): the waiter pins only the .cmd, so the .cmd refuses (exit 3)
unless each file below matches, and the launch also needs PINOK == the pin count (fail closed).
Re-run after any change to a pinned file.
Usage: python -B mkpins_rt.py [--kit DIR]   (DIR = the kit dir to write into, default: this script's dir)
"""
import argparse, hashlib, os, sys

PINNED = [  # relative to WS (= kit\..\..\..)
    r'build\agent2\s5\rt-smoke-run.ps1',
    r'build\agent2\s5\rt_smoke_post.py',
    r'harness\run-game.ps1',
    r'harness\guard.ps1',
    r'harness\winhelper.cs',
    r'harness\nvml.cs',
    r'harness\runstats.py',
    r'harness\vpad\vpadhost.cs',
    r'harness\legodimensions.toml',
    r'harness\routes\attract-long.txt',
    r'build\agent3\vpad\xinput1_4.dll',
    r'build\agent2\session3\verify-bins.py',
    r'build\agent2\final\check-defaults.py',
    r'build\agent2\s5\native-fsr1\perf-bilinear.toml',
]

HEAD = r'''@echo off
rem RUN-RT-SMOKE.cmd - S5 Phase 3 T2/F3 smoke (M2), three FUNCTIONAL arms (untimed, no perf verdicts; M10 P1/P2), one approval:
rem   T2   build\agent2\s5\devs5toml-bin, harness toml: one present_effect 'fsr' rejected line, no new ERROR vs devfinal2
rem   F3A  build\agent2\s5\natives5fsr1-bin, harness toml (present_effect fsr): spatial_fsr_presented=1 (P4)
rem   F3B  natives5fsr1-bin, -Toml native-fsr1\perf-bilinear.toml (pinned): spatial_fsr_presented=0 (P4)
rem   attract-long pad route, 240 s each, fresh run dir per arm, then rt_smoke_post.py (per-arm verdicts +
rem   FSR1-vs-bilinear side-by-side PNGs into rt-smoke\post\sbs-*). F3A F3B take PrintWindow shots at 60 120 146 200 s.
rem   RUN-RT-SMOKE.cmd               real run (interactive desktop; 3 x ~4.5 min, about 15 min; self-closing)
rem   RUN-RT-SMOKE.cmd dryrun        no game: verify-bins, command lines, run-game -DryRun, post self-test; exit 0 = pass
rem   RUN-RT-SMOKE.cmd pinsonly      only check the sha256 pins below; exit 0 = all match, 3 = changed or missing
rem   extra words: allowhidden, arms=T2,F3A,F3B (subset/order)
rem   P5: bin MANIFEST pins are checked by the ps1 (fail closed, before and after every arm), one kit at a time,
rem   interactive desktop only (unless allowhidden).
rem   Pins: the waiter pins only this .cmd, so it pins the ps1, the post script, perf-bilinear.toml and every helper
rem   they run (sha256 via certutil, before anything else; any mismatch or missing file = exit 3; fail closed: the
rem   launch also needs PINOK == the pin count, so a pin line that is skipped or removed = exit 3). Written by mkpins_rt.py.
setlocal
set "KIT=%~dp0"
for %%W in ("%KIT%..\..\..") do set "WS=%%~fW"
set "DRY="
set "PINSONLY="
for %%A in (%*) do (
    if /i "%%~A"=="dryrun" set "DRY=1"
    if /i "%%~A"=="pinsonly" set "PINSONLY=1"
)
set "BAD=0"
set "PINOK=0"
rem PINS-BEGIN (mkpins_rt.py)
'''

TAIL = r'''rem PINS-END
if not "%BAD%"=="0" (
    echo [rt-smoke] REFUSED: %BAD% pinned file^(s^) changed or missing ^(WS %WS%^)
    if not defined DRY if not defined PINSONLY timeout /t 15 >nul 2>&1
    exit /b 3
)
rem fail closed: every pin must have been checked and matched (M10 NIT, as natcmp)
if not "%PINOK%"=="{n}" (
    echo [rt-smoke] REFUSED: %PINOK% of {n} pins verified ^(WS %WS%^)
    if not defined DRY if not defined PINSONLY timeout /t 15 >nul 2>&1
    exit /b 3
)
echo [rt-smoke] pins OK: {n} files ^(WS %WS%^)
if defined PINSONLY exit /b 0
powershell -NoProfile -ExecutionPolicy Bypass -File "%KIT%rt-smoke-run.ps1" %*
set "RC=%ERRORLEVEL%"
echo [rt-smoke] exit %RC%
if not defined DRY timeout /t 15 >nul 2>&1
exit /b %RC%

:pin
set "H="
if exist "%WS%\%~1" for /f "skip=1 delims=" %%H in ('certutil -hashfile "%WS%\%~1" SHA256 2^>nul') do if not defined H set "H=%%H"
if not defined H set "H=MISSING"
set "H=%H: =%"
if /i not "%H%"=="%~2" (
    echo [rt-smoke] PIN MISMATCH %~1: got %H%, pinned %~2
    set /a BAD+=1
) else (
    set /a PINOK+=1
)
exit /b 0
'''


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kit', default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()
    kit = os.path.abspath(a.kit)
    ws = os.path.abspath(os.path.join(kit, '..', '..', '..'))
    lines = []
    for rel in PINNED:
        p = os.path.join(ws, rel)
        if not os.path.isfile(p):
            sys.exit('missing %s' % p)
        h = sha(p)
        lines.append('call :pin "%s" %s\n' % (rel, h))
        print(h[:16], rel)
    text = HEAD + ''.join(lines) + TAIL.replace('{n}', str(len(PINNED)))
    text.encode('ascii')
    out = os.path.join(kit, 'RUN-RT-SMOKE.cmd')
    with open(out, 'wb') as f:
        f.write(text.replace('\n', '\r\n').encode('ascii'))  # CRLF: cmd label lookup (call :pin) is unreliable with LF
    print(sha(out)[:16], out)


if __name__ == '__main__':
    main()

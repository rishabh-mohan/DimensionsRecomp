"""mkpins.py - (re)write RUN-NOPS-SMOKE.cmd with sha256 pins of the kit scripts and every helper they run (M2).

The waiter pins only the .cmd, so the .cmd refuses (exit 3) unless each file below matches.
Re-run after any change to a pinned file (e.g. after setting $pin in nops-smoke-run.ps1).
Usage: python mkpins.py [--kit DIR]   (DIR = the kit dir to write into, default: this script's dir)
"""
import argparse, hashlib, os, sys

PINNED = [  # relative to WS (= kit\..\..\..)
    r'build\agent2\s5\nops-smoke-run.ps1',
    r'build\agent2\s5\nops_smoke_post.py',
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
]

HEAD = r'''@echo off
rem RUN-NOPS-SMOKE.cmd - S5 Phase 2.1 nops-async smoke (M2) on build\agent2\s5\devs5nops-bin, up to six arms, one approval:
rem   T1 default | T2 opt-in | N1 no_wait | N2 no_wait + opt-in   (timing; only the 10 s zpd log)
rem   A1 sync-log + slow_frame_log_ms=1 | A2 A1 + opt-in            (attribution only, D2)
rem   attract-long pad route, 240 s each, 20 s settle, then nops_smoke_post.py (gates + timing/attribution report).
rem   RUN-NOPS-SMOKE.cmd               real run (interactive desktop; 6 x ~4.5 min + 5 x 20 s, about 30 min; self-closing)
rem   RUN-NOPS-SMOKE.cmd dryrun        no game: verify-bins, command lines, run-game -DryRun, post self-test; exit 0 = pass
rem   RUN-NOPS-SMOKE.cmd pinsonly      only check the sha256 pins below; exit 0 = all match, 3 = changed or missing
rem   extra words: allowhidden, arms=T1,T2,... (order), allowsubset (arms= without N1+N2), nozpd
rem   S1: every arm adds d3d12_log_occlusion_queries=true (zpd-log diag) unless nozpd; post gives the S1 verdict
rem   N2: each arm starts from a fresh <run>\user (cold shader/pipeline storage); post gates it
rem   N3: a real run needs both N1 and N2 (unless allowsubset); T1 T2 N1 N2 take PrintWindow shots
rem       at 60 120 146 152 200 s into <run>\kit-shots (read-only job; post gates 5 ok shots per arm)
rem   Pins: the waiter pins only this .cmd, so it pins the ps1, the post script and every helper they run
rem   (sha256 via certutil, before anything else; any mismatch or missing file = exit 3; fail closed: the launch also
rem   needs PINOK == the pin count, so a pin line that is skipped or removed = exit 3). Written by mkpins.py.
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
rem PINS-BEGIN (mkpins.py)
'''

TAIL = r'''rem PINS-END
if not "%BAD%"=="0" (
    echo [nops-smoke] REFUSED: %BAD% pinned file^(s^) changed or missing ^(WS %WS%^)
    if not defined DRY if not defined PINSONLY timeout /t 15 >nul 2>&1
    exit /b 3
)
rem fail closed: every pin must have been checked and matched (M10 NIT, as natcmp)
if not "%PINOK%"=="{n}" (
    echo [nops-smoke] REFUSED: %PINOK% of {n} pins verified ^(WS %WS%^)
    if not defined DRY if not defined PINSONLY timeout /t 15 >nul 2>&1
    exit /b 3
)
echo [nops-smoke] pins OK: {n} files ^(WS %WS%^)
if defined PINSONLY exit /b 0
powershell -NoProfile -ExecutionPolicy Bypass -File "%KIT%nops-smoke-run.ps1" %*
set "RC=%ERRORLEVEL%"
echo [nops-smoke] exit %RC%
if not defined DRY timeout /t 15 >nul 2>&1
exit /b %RC%

:pin
set "H="
if exist "%WS%\%~1" for /f "skip=1 delims=" %%H in ('certutil -hashfile "%WS%\%~1" SHA256 2^>nul') do if not defined H set "H=%%H"
if not defined H set "H=MISSING"
set "H=%H: =%"
if /i not "%H%"=="%~2" (
    echo [nops-smoke] PIN MISMATCH %~1: got %H%, pinned %~2
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
    out = os.path.join(kit, 'RUN-NOPS-SMOKE.cmd')
    with open(out, 'wb') as f:
        f.write(text.replace('\n', '\r\n').encode('ascii'))  # CRLF: cmd label lookup (call :pin) is unreliable with LF
    print(sha(out)[:16], out)


if __name__ == '__main__':
    main()

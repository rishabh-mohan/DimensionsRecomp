"""mkdelta-fsr1p.py - build the natives5fsr1p bin-pin CANDIDATE for the RT kit (M2). The live kit is not touched.

Writes rt-smoke/delta-fsr1p/{orig,new}/{rt-smoke-run.ps1,rt_smoke_post.py,RUN-RT-SMOKE.cmd,manual-capture.ps1} +
fsr1p.diff (M10 natives5fsr1p-rating D3E2EF03, P2):
  F3A/F3B bin natives5fsr1-bin -> natives5fsr1p-bin (native4bp exe + natives5fsr1 rexruntime, s5/black-scene-diag.md),
  MANIFEST pin 102AAD90... -> --manifest, BIN-PINS-natives5fsr1.md -> BIN-PINS-natives5fsr1p.md, the cmd's ps1 + post
  pins re-hashed on the new files; S1: post F3 refs nativefinal2 -> native4bp 1812-cold-n4bp60 + 1825-n4bp60-r1;
  manual-capture (SCR, fix1) N5 at >= 120 s. Every replacement has an exact expected count; all 14 pins re-checked.
Usage: python -B build/agent2/s5/pins-test/mkdelta-fsr1p.py --manifest <sha256 of natives5fsr1p-bin/MANIFEST.txt>
       ... --trial   (no bin needed: a dummy pin, output into SCR/delta-fsr1p-trial, for an offline check only)
"""
import argparse, hashlib, os, re, shutil, subprocess, sys

S5 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = os.path.abspath(os.path.join(S5, '..', '..', '..'))
OUT = os.path.join(S5, 'rt-smoke', 'delta-fsr1p')
OLD_PIN = '102AAD905209F57F7CF80CBC9F280CDDACDB1FD38063475E2F9EF07E14E5B8F0'
FILES = ('rt-smoke-run.ps1', 'rt_smoke_post.py', 'RUN-RT-SMOKE.cmd', 'manual-capture.ps1')
SCR = r'C:\Users\<user>\.gemini\antigravity-cli\brain\a657e030-6ccb-4c5f-a989-c912a51530ce\scratch'
SRC = {f: os.path.join(SCR if f == 'manual-capture.ps1' else S5, f) for f in FILES}
LIVE = {'rt-smoke-run.ps1': '02C6C88C89BE91248C0055D62D76061454087214B36960EAFB157D99FDE1A92E',
        'rt_smoke_post.py': '6034CA362A1FDDFAAD8580EE7E7E1308BF9ACA53EF4632ACCA9AA71E5E4F801F',
        'RUN-RT-SMOKE.cmd': '34425077',  # cmd: prefix only (GO pin)
        'manual-capture.ps1': '2689413732758F9F919D9AE34602743E18EFF0C8292B158FF85FD5386513BE8E'}  # fix1
REF_OLD = ('F2F652C2294936545A15E01FDE8322788562D9EC236189286ED77249F30F8990',   # 1809-cold-nat60 game.log
           '6F17177FC99557D6177963C925C86B98367F82E55B864E47BE6826DA745818FB')   # 1820-nat60-r1
REF_NEW = ('93E1754B876684F286C13EF6923ACFEA46B89C994B4269D36D13EC2795533502',   # 1812-cold-n4bp60 game.log
           '5AD5426AE17EAB2F9C22E22E688C4A75C0B5407DE92860D48D5D236EB892D1E9')   # 1825-n4bp60-r1


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def rep(text, old, new, n, what):
    c = text.count(old)
    if c != n:
        sys.exit('FAIL %s: %r found %d times, expected %d' % (what, old, c, n))
    print('  %-18s %d x %r -> %r' % (what, n, old, new))
    return text.replace(old, new)


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest')
    ap.add_argument('--trial', action='store_true')
    a = ap.parse_args()
    if a.trial:
        m, OUT = 'AB' * 32, os.path.join(SCR, 'delta-fsr1p-trial')
        shutil.rmtree(OUT, ignore_errors=True)
    else:
        m = (a.manifest or '').upper()
        if not re.fullmatch(r'[0-9A-F]{64}', m) or m == OLD_PIN:
            sys.exit('bad --manifest')
        mf = os.path.join(S5, 'natives5fsr1p-bin', 'MANIFEST.txt')
        if sha(open(mf, 'rb').read()) != m:
            sys.exit('FAIL --manifest != sha256(%s)' % mf)
    if os.path.exists(OUT):
        sys.exit('FAIL %s exists' % OUT)
    orig = {f: open(SRC[f], 'rb').read() for f in FILES}
    mx = os.path.join(WS, 'build', 'agent8', 's5', 'matrix', '20261125-1804', 'runs')
    for d, h in zip(('1812-cold-n4bp60', '1825-n4bp60-r1'), REF_NEW):
        if sha(open(os.path.join(mx, d, 'game.log'), 'rb').read()) != h:
            sys.exit('FAIL S1 ref %s game.log != %s' % (d, h[:8]))
    for f in FILES:
        if not sha(orig[f]).startswith(LIVE[f]):
            sys.exit('FAIL live %s sha %s, expected %s' % (f, sha(orig[f])[:16], LIVE[f][:16]))
    new = {}
    t = orig['rt-smoke-run.ps1'].decode('ascii')
    t = rep(t, 'natives5fsr1-bin', 'natives5fsr1p-bin', 3, 'ps1 bin')
    t = rep(t, 'BIN-PINS-natives5fsr1.md', 'BIN-PINS-natives5fsr1p.md', 2, 'ps1 BIN-PINS')
    t = rep(t, OLD_PIN, m, 1, 'ps1 pin')
    t = rep(t, 'MANIFEST pin 102AAD90,', 'MANIFEST pin %s,' % m[:8], 1, 'ps1 pin comment')
    new['rt-smoke-run.ps1'] = t.encode('ascii')
    t = orig['rt_smoke_post.py'].decode('utf-8')
    t = rep(t, 'natives5fsr1-bin', 'natives5fsr1p-bin', 5, 'post bin')
    # S1 (M10 natives5fsr1p-rating D3E2EF03): F3 refs = native4bp runs of the same matrix window, not no-pack nativefinal2
    t = rep(t, 'F3: nativefinal2', 'F3: native4bp', 1, 'post S1 doc')
    t = rep(t, 'cold-nat60 + nat60-r1', 'cold-n4bp60 + n4bp60-r1', 1, 'post S1 doc')
    t = rep(t, "    'nativefinal2': [(MX + r'\\1809-cold-nat60', '%s')," % REF_OLD[0],
            "    'native4bp': [(MX + r'\\1812-cold-n4bp60', '%s')," % REF_NEW[0], 1, 'post S1 ref 1')
    t = rep(t, "%s(MX + r'\\1820-nat60-r1', '%s')]," % (' ' * 21, REF_OLD[1]),
            "%s(MX + r'\\1825-n4bp60-r1', '%s')]," % (' ' * 18, REF_NEW[1]), 1, 'post S1 ref 2')
    t = rep(t, "ref='nativefinal2'", "ref='native4bp'", 2, 'post S1 arms')
    if 'nativefinal2' in t:
        sys.exit('FAIL post still names nativefinal2')
    new['rt_smoke_post.py'] = t.encode('utf-8')
    # M10 P2/P4: N5 at >= 120 s (FE state 0 / intro), not the 60 s install prompt: drop the 60/62 s captures
    t = orig['manual-capture.ps1'].decode('utf-8-sig')
    t = rep(t, '[double[]]$Times = @(60, 62, 122.25, 146.75, 201.5)', '[double[]]$Times = @(122.25, 146.75, 201.5)', 1,
            'capture N5 time')
    new['manual-capture.ps1'] = (b'\xef\xbb\xbf' if orig['manual-capture.ps1'][:3] == b'\xef\xbb\xbf' else b'') + \
        t.encode('utf-8')
    t = orig['RUN-RT-SMOKE.cmd'].decode('ascii')
    t = rep(t, 'natives5fsr1-bin', 'natives5fsr1p-bin', 2, 'cmd bin')
    for f in ('rt-smoke-run.ps1', 'rt_smoke_post.py'):
        t = rep(t, '"build\\agent2\\s5\\%s" %s' % (f, sha(orig[f])), '"build\\agent2\\s5\\%s" %s' % (f, sha(new[f])),
                1, 'cmd pin ' + f[:6])
    new['RUN-RT-SMOKE.cmd'] = t.encode('ascii')
    # pins: every pin line of the new cmd matches the new kit file or the (unchanged) live WS file; count 14
    pins = re.findall(r'^call :pin "([^"]+)" ([0-9A-F]{64})\r$', t, re.M)
    bad = []
    for rel, h in pins:
        f = os.path.basename(rel) if rel.startswith('build\\agent2\\s5\\') and os.path.basename(rel) in FILES else None
        got = sha(new[f]) if f else sha(open(os.path.join(WS, rel), 'rb').read())
        if got != h:
            bad.append(rel)
    if len(pins) != 14 or bad or 'PINOK%"=="14"' not in t:
        sys.exit('FAIL pins: %d lines, bad %s' % (len(pins), bad))
    print('  pins: 14 of 14 match (new ps1/post + live WS files)')
    for sub, d in (('orig', orig), ('new', new)):
        os.makedirs(os.path.join(OUT, sub))
        for f in FILES:
            open(os.path.join(OUT, sub, f), 'wb').write(d[f])
    os.chdir(OUT)
    diff = subprocess.run(['git', '-c', 'core.autocrlf=false', 'diff', '--no-index', 'orig', 'new'],
                          capture_output=True).stdout
    open('fsr1p.diff', 'wb').write(diff)
    for sub in ('orig', 'new'):
        for f in FILES:
            print(sha(open(os.path.join(sub, f), 'rb').read()), sub + '/' + f)
    print(sha(diff), 'fsr1p.diff (%d lines)' % diff.count(b'\n'))
    print('RESULT PASS')


if __name__ == '__main__':
    main()

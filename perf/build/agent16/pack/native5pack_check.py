#!/usr/bin/env python3
# native5pack_check.py - M16 (S5), build/agent16/pack: read-only post-checks of the candidate bin native5pack-bin.
#
#   python build\agent16\pack\native5pack_check.py
#
# Sets Idle priority + affinity 0x3 on itself first (children inherit). Writes ONLY build\agent16\pack\
# native5pack-check-<stamp>\ (refuses to reuse a dir). Checks:
#   C1 verify-bins.py native5pack-bin (MANIFEST rows = files, sizes, sha256)        -> verify-bins-native5pack.txt
#   C2 verify-bins.py native4bp-bin + nativefinal2-bin (pinned bins untouched)       -> verify-bins-pinned.txt
#   C3 pinned shas: native4bp MANIFEST C5181520 / exe FA761654, nf2 MANIFEST 4E5E2620, LATEST-pack AC7B9053,
#      LATEST-bin 76D0EFB9 (unchanged)
#   C4 pe-check.py native5pack exe vs nativefinal2 exe and vs native4bp exe (exports/imports equal)
#   C5 MANIFEST title fingerprint: present in the exe; 1616ce65e973c583 and 39129c4c059be5f0 absent
#   C6 the 6 non-exe/map files are byte-identical to nativefinal2-bin; exe+map differ from nf2 and native4bp
# Exit 0 = RESULT PASS, 1 = FAIL, 2 = refused.
import ctypes, datetime, hashlib, os, re, subprocess, sys

W = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
PACK = os.path.join(W, 'build', 'agent16', 'pack')
NEW = os.path.join(PACK, 'native5pack-bin')
N4 = os.path.join(PACK, 'native4bp-bin')
NF2 = os.path.join(W, 'build', 'agent2', 'nativefinal2-bin')
VB = os.path.join(W, 'build', 'agent2', 'session3', 'verify-bins.py')
PEC = os.path.join(W, 'build', 'agent2', 'final', 'pe-check.py')
TOOLS = {VB: '80FF4C5F581C4B1BC02C8E98039CBA6A62BEB4CE5F0E267885F9DA7F17C9B95E',
         PEC: 'F4368C32076AAA3EF4BD087E82A3FCA623F8D4FDCA363E2713825A52CD813E27'}
PINNED = [
    (os.path.join(N4, 'MANIFEST.txt'), 'C518152026695279993085A8497E7B14D318C1DFF54B57F2767670B90A7AA690'),
    (os.path.join(N4, 'legodimensions.exe'), 'FA761654D665BC928B9FC82AC5DCE58E25EE2E87BF60ED519CC5480A3012187C'),
    (os.path.join(NF2, 'MANIFEST.txt'), '4E5E2620F38F7D09E064FB191BA396D7149B27A593C5158EF317CB2D9A31A163'),
    (os.path.join(PACK, 'LATEST-pack.txt'), 'AC7B9053C05BB53A9BD62CF191093F72CE85E9A4253FAE6987992D1C3E75E320'),
    (os.path.join(PACK, 'LATEST-bin.txt'), '76D0EFB9F59DD2679735A5857B2D7805F8FE4C0091940E13DE4CC8C0A2AEE82E'),
]
OLD_FPS = ('1616ce65e973c583', '39129c4c059be5f0')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def main():
    k = ctypes.windll.kernel32
    hp = k.GetCurrentProcess()
    k.SetPriorityClass(hp, 0x40)
    k.SetProcessAffinityMask(hp, ctypes.c_size_t(3))
    if not os.path.isdir(NEW):
        print('REFUSED: %s missing' % NEW)
        return 2
    out = os.path.join(PACK, 'native5pack-check-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    if not os.path.normcase(out).startswith(os.path.normcase(PACK) + os.sep) or os.path.exists(out):
        print('REFUSED: bad or existing out dir %s' % out)
        return 2
    os.makedirs(out)
    lines, fails = [], []

    def rec(ok, what):
        lines.append('%s %s' % ('PASS' if ok else 'FAIL', what))
        print(lines[-1], flush=True)
        if not ok:
            fails.append(what)

    for p, h in TOOLS.items():
        rec(sha(p) == h, 'tool pin %s %s' % (os.path.relpath(p, W), h[:8]))
    if fails:
        return finish(out, lines, fails)

    def runlog(name, cmd):
        r = subprocess.run(cmd, cwd=out, capture_output=True, text=True, errors='replace')
        with open(os.path.join(out, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write('$ %s\n%s%s\nexit=%d\n' % (' '.join(cmd), r.stdout, r.stderr, r.returncode))
        tail = [l for l in r.stdout.splitlines() if l.startswith('RESULT')]
        return r.returncode, tail[-1] if tail else ''

    rc, t = runlog('verify-bins-native5pack.txt.log', [sys.executable, VB, NEW, '--out',
                                                        os.path.join(out, 'verify-bins-native5pack.txt')])
    rec(rc == 0, 'C1 verify-bins native5pack-bin (exit %d) %s' % (rc, t))
    rc, t = runlog('verify-bins-pinned.txt.log', [sys.executable, VB, N4, NF2, '--out',
                                                   os.path.join(out, 'verify-bins-pinned.txt')])
    rec(rc == 0, 'C2 verify-bins native4bp-bin + nativefinal2-bin (exit %d) %s' % (rc, t))
    for p, h in PINNED:
        got = sha(p)
        rec(got == h, 'C3 pinned %s = %s (got %s)' % (os.path.relpath(p, W), h[:8], got[:8]))
    exe = os.path.join(NEW, 'legodimensions.exe')
    for ref, tag in ((NF2, 'nf2'), (N4, 'native4bp')):
        rc, t = runlog('pe-check-vs-%s.txt' % tag, [sys.executable, PEC, '--new', exe, '--ref',
                                                    os.path.join(ref, 'legodimensions.exe')])
        rec(rc == 0, 'C4 pe-check native5pack exe vs %s exe (exit %d) %s' % (tag, rc, t))
    mf = open(os.path.join(NEW, 'MANIFEST.txt'), encoding='utf-8', errors='replace').read()
    m = re.search(r'native GPU fingerprint ([0-9a-f]{16})', mf)
    fp = m.group(1) if m else None
    b = open(exe, 'rb').read()
    rec(bool(fp) and fp not in OLD_FPS, 'C5 MANIFEST fingerprint %s is new' % fp)
    rec(bool(fp) and fp.encode() in b, 'C5 exe contains %s' % fp)
    for o in OLD_FPS:
        rec(o.encode() not in b, 'C5 exe lacks %s' % o)
    del b
    names = sorted(n for n in os.listdir(NEW) if n != 'MANIFEST.txt')
    rec(names == sorted(n for n in os.listdir(NF2) if n != 'MANIFEST.txt'), 'C6 file set = nativefinal2-bin (%d files)'
        % len(names))
    for n in names:
        a, r2 = sha(os.path.join(NEW, n)), sha(os.path.join(NF2, n)) if os.path.exists(os.path.join(NF2, n)) else '-'
        lines.append('HASH %s %s nf2=%s' % (a, n, r2))
        if n in ('legodimensions.exe', 'legodimensions.map'):
            n4 = sha(os.path.join(N4, n))
            rec(a != r2 and a != n4, 'C6 %s differs from nf2 and native4bp' % n)
        else:
            rec(a == r2, 'C6 %s identical to nf2' % n)
    lines.append('HASH %s MANIFEST.txt' % sha(os.path.join(NEW, 'MANIFEST.txt')))
    return finish(out, lines, fails)


def finish(out, lines, fails):
    res = 'RESULT: %s' % ('PASS' if not fails else 'FAIL (%d)' % len(fails))
    lines.append(res)
    p = os.path.join(out, 'native5pack-check.txt')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    print(res)
    print('report %s %s' % (p, sha(p)))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())

"""maplines.py (Agent 9, run-2 task #22): the hooked aliases in a devoff link map today, and the expected map change
after S4c (#24): sub_83FBF7D0 (H0), sub_83FAF180 (H1), sub_83FB09E8 (H2) and sub_83FC0C10 (H3) move to
gpu_wait_backoff.cpp.obj, so 27 hooked aliases become 31 (29 without LEGO_GPU_WAIT_HOOK_GETDATA).

Usage: python maplines.py [--map MAP] [--out FILE]
Default map: build/agent2/devoff4-bin/legodimensions.map (the S4a devoff bin); default out: expected-map.txt here.
Read-only, one thread. Same parser and the same 'hooked' test as build/agent9/mapcmp.py: an __imp__sub_X public that
is not at the address of sub_X.
"""
import argparse, hashlib, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.abspath(os.path.join(HERE, *(['..'] * 5)))
sys.path.insert(0, os.path.join(R, 'build', 'agent9'))
import mapcmp  # noqa: E402  parse(), summarize(), TU

TARGETS = [('sub_83FBF7D0', 'H0', 'fence wait, loop L1'),
           ('sub_83FAF180', 'H1', "L1's poll step"),
           ('sub_83FB09E8', 'H2', 'GetData, loop L2; needs LEGO_GPU_WAIT_HOOK_GETDATA'),
           ('sub_83FC0C10', 'H3', 'kick counter, STATS only; needs LEGO_GPU_WAIT_HOOK_GETDATA')]
NEW_OBJ = 'gpu_wait_backoff.cpp.obj'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--map', default=os.path.join(R, 'build', 'agent2', 'devoff4-bin', 'legodimensions.map'))
    ap.add_argument('--out', default=os.path.join(HERE, 'expected-map.txt'))
    a = ap.parse_args()
    t0 = time.time()
    h = hashlib.sha256()
    with open(a.map, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    sections, publics = mapcmp.parse(a.map)
    subs, imps, other_tu, size = mapcmp.summarize(publics)
    hooked = sorted(n for n, v in imps.items() if subs.get(n, (None, None))[:2] != v[:2])
    names = set(hooked) | {t[0] for t in TARGETS}
    raw, state = {}, 0
    with open(a.map, encoding='utf-8', errors='replace') as f:
        for line in f:
            s = line.rstrip('\r\n')
            st = s.strip()
            if state == 0:
                if st.startswith('Address') and 'Publics by Value' in st:
                    state = 1
                continue
            if st.startswith('entry point at'):
                break
            p = st.split()
            if len(p) < 4 or ':' not in p[0]:
                continue
            n = p[1][7:] if p[1].startswith('__imp__') else p[1]
            if n in names:
                raw.setdefault(p[1], s)
    out = []
    say = out.append
    st = os.stat(a.map)
    say('# maplines (#24 S4c: expected map change; Agent 9, task #22)  ' + time.strftime('%Y-%m-%d %H:%M:%S'))
    say('map: %s  %d B  mtime %s  sha256 %s' % (os.path.relpath(a.map, R).replace('\\', '/'), st.st_size,
                                               time.strftime('%m-%d %H:%M', time.localtime(st.st_mtime)),
                                               h.hexdigest().upper()[:16]))
    say('publics %d; sub_ %d (%d in recompiled-TU objects); __imp__sub_ aliases %d; hooked (__imp__sub_X not at '
        'sub_X): %d' % (len(publics), len(subs), sum(1 for v in subs.values() if mapcmp.TU.match(v[2])), len(imps),
                        len(hooked)))
    by_obj = {}
    for n in hooked:
        by_obj.setdefault(subs[n][2] if n in subs else '(no sub_ public)', []).append(n)
    say('hooked today, by the object that defines sub_X:')
    for obj in sorted(by_obj):
        say('  %-36s %2d  %s' % (obj, len(by_obj[obj]), ' '.join(by_obj[obj])))
    if hooked:
        ex = hooked[0]
        say('format (the raw lines of one hooked function today):')
        say('  ' + raw.get(ex, '?'))
        say('  ' + raw.get('__imp__' + ex, '?'))
    say('the 4 #24 targets today (each must be unhooked: sub_X at __imp__sub_X, in the same recompiled TU):')
    bad = 0
    for n, tag, what in TARGETS:
        s, i = subs.get(n), imps.get(n)
        if not s or not i:
            state_s, bad = 'MISSING', bad + 1
        elif s[:2] == i[:2] and s[2] == i[2] and mapcmp.TU.match(s[2]):
            state_s = 'unhooked (%s)' % s[2]
        else:
            state_s, bad = 'ALREADY HOOKED (%s)' % s[2], bad + 1
        say('  %s %s (%s): %s' % (tag, n, what, state_s))
        say('    ' + raw.get(n, '?'))
        say('    ' + raw.get('__imp__' + n, '?'))
    say('expected after S4c on the OFF devoff bin (the CMake block sets LEGO_GPU_WAIT_HOOK_GETDATA=1):')
    for n, tag, what in TARGETS:
        i = imps.get(n)
        where = '%04X:%08X in %s' % (i[0], i[1], i[2]) if i else '?'
        say('  %s  %s -> %s   (__imp__%s stays at %s)' % (tag, n, NEW_OBJ, n, where))
    k = len(hooked)
    say('  hooked aliases %d -> %d. The other %d stay as they are, and the sub_ and __imp__ name sets do not change '
        '(the new TU defines only these 4 sub_ publics plus its own statics).' % (k, k + 4, k))
    say('  Without the define (H0/H1 only): %d -> %d. Native bins: no change (the file is not compiled when '
        'LEGODIMENSIONS_NATIVE_GPU is ON; native defines sub_83FB09E8 and sub_83FC0C10 itself, '
        'gpu_native/queries.cpp:320 and hooks_device.cpp:340).' % (k, k + 2))
    t = raw.get(TARGETS[0][0])
    if t:
        p = t.split()
        say('  template: the H0 line today with the object replaced (the address moves into the rexlego objects):')
        say('    ' + t.replace(p[-1], NEW_OBJ).replace(p[0], '????:????????').replace(p[2], '?' * len(p[2])))
    say('expected hooked set after S4c (%d names, sorted):' % (k + 4))
    say('  ' + ' '.join(sorted(set(hooked) | {t[0] for t in TARGETS})))
    say('RESULT: %s  (%.1fs)' % ('PASS: %d hooked today, all 4 targets unhooked' % k if not bad else
                                 'FAIL (%d target problem(s))' % bad, time.time() - t0))
    with open(a.out, 'w', encoding='ascii', errors='replace', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print('\n'.join(out))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())

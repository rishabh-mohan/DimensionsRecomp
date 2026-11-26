#!/usr/bin/env python3
# selftest_dump6.py - M16 (S5): synthetic fixtures + runner for dump6_post.py (M10 C-C5).
#   python -B build\agent16\cg7\selftest\selftest_dump6.py
# Writes deterministic fixtures to build\agent16\cg7\selftest\fixtures\<case>\ (re-written each run, same bytes),
# fixtures\SHA256SUMS.txt, and runs dump6_post.py per case into a NEW build\agent16\cg7\selftest\run-<stamp>\.
# Prints PASS/FAIL per case (expected exit code, RESULT prefix and report lines) and ALL PASS / N FAILED.
import datetime, hashlib, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, 'fixtures')
POST = os.path.join(os.path.dirname(HERE), 'dump6_post.py')
T0 = datetime.datetime(2026, 11, 26, 10, 0, 0)
UNIX = int(T0.timestamp() * 1000)
RED = 100000.0                      # trace ms of the red start (game.log 10:01:40.000)
FP = 'a349d5292f67b127'
W1V, W1P, W2V, W2P = 0xAB80F350, 0xAB77B580, 0xA7F7A100, 0xA7F79ED0
W1P_BACK = 0xED25B8E0
ROOT_PHYS = bytes((i * 7 + 3) & 0xFF for i in range(400))


def wtxt(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)


def wbin(p, b):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(b)


def container(vb, pb, phys=None, seed=1):
    v = bytearray((i * seed + 11) & 0xFF for i in range(vb))
    v[8:12] = b'\x10\x20\x30\x40'
    return bytes(v) + bytes(v[8:12]) + (phys if phys is not None else bytes((i * seed + 5) & 0xFF for i in range(pb)))


def ident(ms, st, g, phys, vb, pb, ch, phh):
    return (ms, 'missing_placement_shader_identity', 'stage= %d guest= %d physical= %d virtual_bytes= %d '
            'physical_bytes= %d container_hash= %d physical_hash= %d' % (st, g, phys, vb, pb, ch, phh))


# identity specs: key -> (stage, guest, physical, vb, pb, container_hash, physical_hash, d6 match?)
IDS = {
    'w1v': (6, W1V, 0xED25B6A0, 640, 144, 0x1111111111111111, 0xAAAA000000000001, False),
    'w1p': (7, 0x12345678, W1P_BACK, 896, 412, 0x2222222222222222, 0xAAAA000000000002, False),   # backing match
    'w2v': (6, W2V, 0xED3549C0, 640, 400, 0x3333333333333333, 0xAAAA000000000003, True),          # D6 MATCH
    'w2p': (7, W2P, 0xED354BE0, 896, 412, 0x4444444444444444, 0xAAAA000000000004, False),
}


def build(case, stop_s=90.0, gate_line=55, prompts='batman:1/1 gandalf:1/1 wyldstyle:1/1', ids=('w1v', 'w1p', 'w2v',
          'w2p'), extra_ids=(), bad_size=(), dump=True, early_noident=False, misses=True, id_ms=None, pre_rows=False):
    d = os.path.join(FIX, case)
    if os.path.isdir(d):
        shutil.rmtree(d)
    tr = os.path.join(d, 'trace')
    wtxt(os.path.join(tr, 'trace-start.json'), json.dumps({'unix_ms': UNIX}))
    ev = []
    stop = RED + 1000.0 * stop_s
    t = 0.0
    while t <= stop:
        ev.append((t, 'frame', 'n= 1'))
        t += 500.0
    dd = os.path.join(d, 'shader-dumps-native-fixture')
    if early_noident:
        ev.append(ident(RED + 10000.0, 6, 0xA7FA6EA0, 0xED000000, 640, 144, 0x5555555555555555, 0xBBBB))
        if dump:
            wbin(os.path.join(dd, 'placement-containers', 'vs-5555555555555555.bin'), container(640, 144, seed=6))
    if misses:
        for k in range(3):                                          # W1 at red+45..47 s
            ms = RED + 45000.0 + 1000.0 * k + 1
            ev += [(ms, 'unrecognized_shader', 'guest= %d stage= 6' % W1V),
                   (ms, 'unrecognized_shader', 'guest= %d stage= 7' % W1P),
                   (ms + 0.1, 'draw_missing_vertex_shader', 'guest_vs= %d' % W1V)]
        if stop_s >= 76:
            for k in range(3):                                      # W2 at red+75..77 s
                ms = RED + 75000.0 + 1000.0 * k + 1
                ev += [(ms, 'unrecognized_shader', 'guest= %d stage= 6' % W2V),
                       (ms, 'unrecognized_shader', 'guest= %d stage= 7' % W2P),
                       (ms + 0.1, 'draw_missing_vertex_shader', 'guest_vs= %d' % W2V)]
    first = {'w1v': RED + 45000.5, 'w1p': RED + 45000.6, 'w2v': RED + 75000.5, 'w2p': RED + 75000.6}
    first.update(id_ms or {})
    if pre_rows:                                                    # W1 VS rows before W1 at red+20..22 s (B-N1)
        for k in range(3):
            ev.append((RED + 20000.0 + 1000.0 * k + 1, 'unrecognized_shader', 'guest= %d stage= 6' % W1V))
    dd = os.path.join(d, 'shader-dumps-native-fixture')
    for key in list(ids) + list(extra_ids):
        st, g, ph, vb, pb, ch, phh, m = IDS[key] if key in IDS else key
        ms = first.get(key, RED + 46000.0) if key in IDS else RED + 46000.0
        if key not in IDS or ms <= stop:
            ev.append(ident(ms, st, g, ph, vb, pb, ch, phh))
            if dump:
                b = container(vb, pb, ROOT_PHYS if m else None, seed=(ch & 0xF) + 1)
                if key in bad_size:
                    b = b[:-1]
                wbin(os.path.join(dd, 'placement-containers', '%s-%016X.bin' % ('vs' if st == 6 else 'ps', ch)), b)
    ev.sort(key=lambda x: x[0])
    lines = ['elapsed_ms\tframe\tevent\tanomaly\tdetails']
    fr = 0
    for ms, e, det in ev:
        if e == 'frame':
            fr += 1
        lines.append('%.3f\t%d\t%s\t%d\t%s' % (ms, fr, e, 0 if e == 'frame' else 1, det))
    wtxt(os.path.join(tr, 'events.tsv'), '\n'.join(lines) + '\n')
    if dump:
        wbin(os.path.join(dd, 'placement-raw', 'vs-C77B3ABB6F87ACD9.bin'), b'\0' * 2048)   # dedup: 1 per stage
        wbin(os.path.join(dd, 'placement-raw', 'ps-C77B3ABB6F87ACD9.bin'), b'\0' * 1184)
        wbin(os.path.join(dd, 'ps-93B9F93B535E7CCA.bin'), b'\1' * 156)
        wbin(os.path.join(dd, 'vs-A58EBA123EFB541C.bin'), b'\0' * 304 + ROOT_PHYS)
    redwall = (T0 + datetime.timedelta(milliseconds=RED)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    wtxt(os.path.join(d, 'game.log'), '\n'.join([
        '[2026-11-26 09:59:59.000] [info] [core] [t1] Native GPU [%s]: D3D12 ready' % FP,
        '[2026-11-26 10:00:30.000] [info] [core] [t2] Toypad: pad 1 mode 3 lit FF 00 00 (on 0 off 0 count 1 speed 30)',
        '[%s] [info] [core] [t2] Toypad: pad 1 mode 3 lit FF 00 00 (on 0 off 0 count 1 speed 18)' % redwall,
        '[2026-11-26 10:02:25.000] [warning] [core] [t3] Native GPU: placement pixel shader 0x%08X backing 0x%08X '
        'prefix=0xC77B3ABB6F87ACD9 words=0 missing from AOT index' % (W1P, W1P_BACK),
    ]) + '\n')
    wtxt(os.path.join(d, 'post.txt'), 'PASS native clean exit: exit 0x00000000\n'
         'steps 302/302 stopped_by_script True error None\n'
         'wait line %d current=5 pending=0 1234  ok after 3.2 s\n' % gate_line)
    wtxt(os.path.join(d, 'runlog.txt'), 'steps 302/302 (last: done)\n[gameplay] run-game (native) exit 0\n'
         'sidecar exit 0\nholdwatch exit 0\nwatcher exit 0\nGAMEPLAY DONE: run-game exit 0; post exit 0\n')
    wtxt(os.path.join(d, 'sidecar.txt'), '10:01:40.240 alert pad 1 lit FF 00 00 speed 18: all-pads fast red\n'
         '10:02:40.000 result listener=True prompts=%s ctl=0 done/0 err route=0 ok/0 err zone=done zone-skips=0\n'
         % prompts)
    wtxt(os.path.join(d, 'noident.txt'), 'VS A7FA6EA0 events 1 draws 1\n')
    return d


def args(d, out, dump=True, **kw):
    a = ['--trace', os.path.join(d, 'trace', 'events.tsv'), '--log', os.path.join(d, 'game.log'),
         '--post', os.path.join(d, 'post.txt'), '--runlog', os.path.join(d, 'runlog.txt'),
         '--sidecar', os.path.join(d, 'sidecar.txt'), '--fp', FP, '--noident', os.path.join(d, 'noident.txt'),
         '--root-vs', os.path.join(d, 'shader-dumps-native-fixture', 'vs-A58EBA123EFB541C.bin')
         if dump else os.path.join(FIX, 'covered', 'shader-dumps-native-fixture', 'vs-A58EBA123EFB541C.bin'),
         '--out', out]
    if dump:
        a += ['--dump-dir', os.path.join(d, 'shader-dumps-native-fixture')]
    for k, v in kw.items():
        a += ['--' + k.replace('_', '-'), v]
    return a


def main():
    unrelated = (7, 0x0BADF00D, 0xEE000000, 896, 412, 0x6666666666666666, 0xAAAA000000000004, False)
    cases = [
        # name, build kwargs, expected exit, RESULT prefix, required report substrings
        ('covered', dict(early_noident=True), 0, 'COVERED (4/4',
         ['W1/W2 split: W1 COVERED; W2 COVERED', 'MATCHED by backing ED25B8E0',
          'vs-3333333333333333.bin guest A7F7A100 physical 400 B: MATCH',
          'vs-1111111111111111.bin guest AB80F350 physical 144 B: DIFF',
          'raw VS: 1 file(s) = unique (stage, prefix) for 3 identities', 'raw PS: 1 file(s) = unique (stage, prefix) '
          'for 2 identities', 'D5 identity events before red+40 s: 1', 'IN noident (one of the 22)', 'D4: PASS',
          "boot files present: ['ps-93B9F93B535E7CCA.bin', 'vs-A58EBA123EFB541C.bin']; other: none"]),
        ('partial', dict(ids=('w1v', 'w1p', 'w2v')), 1, 'PARTIAL (3/4',
         ['W1 COVERED; W2 PARTIAL (1/2)', 'PS A7F79ED0: 3, 0', 'UNMATCHED']),
        ('notreached', dict(stop_s=70.0), 1, 'NOT-REACHED', ['W1 COVERED; W2 NOT-REACHED', 'D2 reach: stop = red + '
                                                             '70.0 s (need >= red + 80 s): FAIL']),
        ('gate56', dict(gate_line=56), 1, 'INCONCLUSIVE (D1 route: title gate HIT', []),
        ('prompts110', dict(prompts='batman:1/10 gandalf:1/1 wyldstyle:1/1'), 1, 'INCONCLUSIVE (D1 route: prompts '
                                                                               '3/3', []),
        ('falsecover', dict(ids=('w1v', 'w1p', 'w2v'), extra_ids=(unrelated,)), 1, 'PARTIAL (3/4',
         ['physical_hash joins between identity events (information; never used to cover a target): 0',
          'PS A7F79ED0: 3, 0']),
        ('falsecover2', dict(ids=('w1v', 'w1p', 'w2v', 'w2p'), extra_ids=(), ), None, None, []),  # placeholder
        ('d4bad', dict(bad_size=('w2p',)), 1, 'PARTIAL (4/4 targets matched; D4 FAIL',
         ['ps-4444444444444444.bin size 1311 (expect 1312) BAD']),
        ('nodump', dict(dump=False, ids=()), 1, 'NOT-COVERED (0/4', ['D4: FAIL (no dump dir', 'identity events: 0']),
        ('nodump-ids', dict(dump=False), 1, 'PARTIAL (4/4 targets matched; D4 FAIL', ['vs-1111111111111111.bin MISSING']),
        ('notargets', dict(misses=False, ids=()), 1, 'INCONCLUSIVE (no target rows', []),
        # v2 (B-N1 + C-S1)
        ('cs1-early', dict(id_ms={'w1v': RED - 10000.0}), 1,
         'PARTIAL (4/4 targets matched; C-S1 flagged: W1 VS AB80F350 EARLY)',
         ['W1/W2 split: W1 PARTIAL (2/2; C-S1 flagged 1); W2 COVERED', 'identity at red-10.0 s; C-S1 EARLY',
          'true first red+45.0 s']),
        ('cs1-truefirst', dict(pre_rows=True, id_ms={'w1v': RED + 20000.5}), 0, 'COVERED (4/4',
         ['VS AB80F350: 3, 3, +45.0..+47.0  MATCHED by guest -> container 1111111111111111; true first red+20.0 s; '
          'identity at red+20.0 s; C-S1 OK', 'W1/W2 split: W1 COVERED; W2 COVERED']),
        ('cs1-backing-early', dict(id_ms={'w1p': RED - 5000.0}), 0, 'COVERED (4/4',
         ['MATCHED by backing ED25B8E0', 'identity at red-5.0 s; C-S1 OK (backing)']),
        ('cs1-cap', dict(extra_ids=tuple((7, 0x0C000000 + i, 0xEF000000 + 64 * i, 16, 8, 0x8800000000000000 + i,
                                          0xCC00000000000000 + i, False) for i in range(252))), 1,
         'PARTIAL (4/4 targets matched; C-S1 flagged: W1 VS AB80F350 CAP',
         ['C-S1: identity events 256 (capture cap 256): CAP', 'W1 PARTIAL (2/2; C-S1 flagged 2); W2 PARTIAL (2/2; '
          'C-S1 flagged 2)', 'C-S1 CAP', 'D4: PASS']),
    ]
    # falsecover2: W2 PS identity removed, an unrelated PS guest carries the SAME physical_hash as w2p would have
    # and joins an identity of the W2 VS by physical_hash: the join is listed, the target stays UNMATCHED.
    joined = (7, 0x0BADF00D, 0xEE000000, 896, 412, 0x7777777777777777, IDS['w2v'][6], False)
    cases[6] = ('falsecover2', dict(ids=('w1v', 'w1p', 'w2v'), extra_ids=(joined,)), 1, 'PARTIAL (3/4',
                ['physical_hash joins between identity events (information; never used to cover a target): 1',
                 'PS A7F79ED0: 3, 0, +75.0..+77.0  UNMATCHED'])
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    run = os.path.join(HERE, 'run-' + stamp)
    os.makedirs(run)
    fails = 0
    for name, kw, ex, pre, need in cases:
        d = build(name, **kw)
        r = subprocess.run([sys.executable, '-B', POST] + args(d, os.path.join(run, name), dump=kw.get('dump', True)),
                           capture_output=True, text=True)
        rep = os.path.join(run, name, 'dump6_post.txt')
        body = open(rep, encoding='utf-8').read() if os.path.isfile(rep) else ''
        res = [l for l in r.stdout.splitlines() if l.startswith('RESULT: ')]
        res = res[0][8:] if res else ''
        miss = [n for n in need if n not in body]
        ok = r.returncode == ex and res.startswith(pre) and not miss
        fails += not ok
        print('%s %-12s exit %d (expect %d) RESULT: %s%s' % ('PASS' if ok else 'FAIL', name, r.returncode, ex, res,
                                                             '' if not miss else '  MISSING: %s' % miss))
    # refusals: missing input, existing --out, --out outside cg7, bad --dump-dir
    d = os.path.join(FIX, 'covered')
    ref = [('refuse-missing-trace', args(d, os.path.join(run, 'r1'))[:1] + [os.path.join(d, 'nope.tsv')]
            + args(d, os.path.join(run, 'r1'))[2:]),
           ('refuse-out-exists', args(d, os.path.join(run, 'covered'))),
           ('refuse-out-outside', args(d, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'x-dump6'))),
           ('refuse-bad-dumpdir', args(d, os.path.join(run, 'r4'), dump=False) + ['--dump-dir',
                                                                                 os.path.join(d, 'nodir')])]
    for name, a in ref:
        r = subprocess.run([sys.executable, '-B', POST] + a, capture_output=True, text=True)
        ok = r.returncode == 2 and r.stdout.startswith('REFUSED')
        fails += not ok
        print('%s %-20s exit %d (expect 2) %s' % ('PASS' if ok else 'FAIL', name, r.returncode, r.stdout.strip()))
    sums = []
    for root, _, files in os.walk(FIX):
        for fn in sorted(files):
            if fn == 'SHA256SUMS.txt':
                continue
            p = os.path.join(root, fn)
            sums.append('%s  %s' % (hashlib.sha256(open(p, 'rb').read()).hexdigest().upper(),
                                    os.path.relpath(p, FIX).replace('\\', '/')))
    sums.sort(key=lambda s: s[66:])
    wtxt(os.path.join(FIX, 'SHA256SUMS.txt'), '\n'.join(sums) + '\n')
    print('fixtures: %d files, SHA256SUMS.txt %s' % (len(sums), hashlib.sha256(
        open(os.path.join(FIX, 'SHA256SUMS.txt'), 'rb').read()).hexdigest().upper()))
    print('run dir %s' % run)
    print('ALL PASS' if not fails else '%d FAILED' % fails)
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())

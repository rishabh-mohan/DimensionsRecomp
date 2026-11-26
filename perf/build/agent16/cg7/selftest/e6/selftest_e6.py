#!/usr/bin/env python3
# selftest_e6.py - M16 (S5): synthetic fixtures + runner for e6_roles.py (information-only by-role report).
#   python -B build\agent16\cg7\selftest\e6\selftest_e6.py
# Writes deterministic fixtures to build\agent16\cg7\selftest\e6\fixtures\<case>\ (re-written each run, same bytes),
# fixtures\SHA256SUMS.txt, and runs e6_roles.py per case into a NEW build\agent16\cg7\selftest\e6\run-<stamp>\.
# Prints PASS/FAIL per case (expected exit code + expected report lines) and ALL PASS / N FAILED.
import datetime, hashlib, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, 'fixtures')
TOOL = os.path.abspath(os.path.join(HERE, '..', '..', 'e6_roles.py'))
CG7 = os.path.dirname(TOOL)
T0 = datetime.datetime(2026, 11, 26, 10, 0, 0)
UNIX = int(T0.timestamp() * 1000)
RED = 100000.0                      # trace ms of the red start (game.log 10:01:40.000)
FP = 'a349d5292f67b127'
A_V, A_P = 0xAB80F350, 0xAB77B580   # W1a (073150 names)
B_V, B_P = 0xAB64C0E0, 0xABB3F110   # W1b
C_V, C_P = 0xA7F7A100, 0xA7F79ED0   # W2


def wtxt(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)


def vs(g, s0, n, step=1.0):
    """n VS miss rows (with unrecognized rows) from red + s0 s, every step s."""
    out = []
    for k in range(n):
        ms = RED + 1000.0 * (s0 + step * k)
        out += [(ms, 'unrecognized_shader', 'guest= %d stage= 6' % g),
                (ms + 0.1, 'draw_missing_vertex_shader', 'guest_vs= %d' % g)]
    return out


def ps(g, s0, n, step=1.0):
    out = []
    for k in range(n):
        ms = RED + 1000.0 * (s0 + step * k)
        out += [(ms, 'unrecognized_shader', 'guest= %d stage= 7' % g),
                (ms + 0.1, 'draw_missing_pixel_shader', 'guest_ps= %d' % g)]
    return out


def build(case, rows, stop_s=100.0, red=True, backs=(), idents=(), mcache='ON', diag=False):
    d = os.path.join(FIX, case)
    if os.path.isdir(d):
        shutil.rmtree(d)
    tr = os.path.join(d, 'trace')
    wtxt(os.path.join(tr, 'trace-start.json'), json.dumps({'unix_ms': UNIX}))
    ev = []
    t = 0.0
    while t <= RED + 1000.0 * stop_s:
        ev.append((t, 'frame', 'n= 1'))
        t += 500.0
    ev += rows
    for st, g, ph, s0 in idents:
        ev.append((RED + 1000.0 * s0, 'missing_placement_shader_identity',
                   'stage= %d guest= %d physical= %d virtual_bytes= 120 physical_bytes= 376 container_hash= 1 '
                   'physical_hash= 2' % (st, g, ph)))
    ev.append((RED + 1000.0 * 50, 'shader_miss_cache_insert', 'guest= 1'))
    ev.sort(key=lambda x: x[0])
    lines = ['elapsed_ms\tframe\tevent\tanomaly\tdetails']
    fr = 0
    for ms, e, det in ev:
        if e == 'frame':
            fr += 1
        lines.append('%.3f\t%d\t%s\t%d\t%s' % (ms, fr, e, 0 if e == 'frame' else 1, det))
    wtxt(os.path.join(tr, 'events.tsv'), '\n'.join(lines) + '\n')
    redwall = (T0 + datetime.timedelta(milliseconds=RED)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    gl = ['[2026-11-26 09:59:59.000] [info] [core] [t1] Native GPU [%s]: D3D12 ready' % FP]
    if mcache:
        gl.append('[2026-11-26 09:59:59.500] [info] [core] [t1] Native GPU: shader miss cache %s (build default)'
                  % mcache)
    gl.append('[2026-11-26 10:00:30.000] [info] [core] [t2] Toypad: pad 1 mode 3 lit FF 00 00 (on 0 off 0 count 1 '
              'speed 30)')
    if red:
        gl.append('[%s] [info] [core] [t2] Toypad: pad 1 mode 3 lit FF 00 00 (on 0 off 0 count 1 speed 18)' % redwall)
    for kind, g, b in backs:
        gl.append('[2026-11-26 10:02:25.000] [warning] [core] [t3] Native GPU: placement %s shader 0x%08X backing '
                  '0x%08X prefix=0xC77B3ABB6F87ACD9 words=0 missing from AOT index' % (kind, g, b))
    wtxt(os.path.join(d, 'game.log'), '\n'.join(gl) + '\n')
    wtxt(os.path.join(d, 'runlog.txt'), '[gameplay 10:00:00] start\n' + (
        '[gameplay 10:00:00] DIAGNOSTIC: dump run, timing invalid, miss cache OFF\n' if diag else '') +
        '[gameplay 10:05:00] GAMEPLAY DONE\n')
    return d


BASE = vs(A_V, 43.5, 5) + vs(B_V, 44.5, 3) + vs(C_V, 75.7, 4)
UNC = 'CLASS: known uncovered VS, no identity in B (U-ABA99710 VS) '
CASES = [
    # (case, rows, build kw, extra args ('RUNLOG' = the fixture runlog.txt), expected exit, expected lines)
    ('base', BASE, dict(backs=[('vertex', A_V, 0xED25B6A0)]), ['--runlog', 'RUNLOG'], 0, [
        'E-C4 windows: W1a red+40..59 s 8; W1b red+59..65 s 0; W2 red+65 s..stop 4; TOTAL at >= red+40 s 12; '
        'PRE 0; stop red+100.0 s',
        'ROLES: A-AB7D1200 5 (VS 5, PS 0); U-ABA99710 3 (VS 3, PS 0); C-A7F79FD0 4 (VS 4, PS 0); OTHER 0 (VS 0, PS 0)',
        UNC + '3; covered-role misses (high priority) 9 [A-AB7D1200 VS 5, C-A7F79FD0 VS 4]; OTHER (no role) 0',
        'HYGIENE (E-C6 part): game.log shader miss cache ON; runlog DIAGNOSTIC lines 0',
        'FLAGS: none', 'VS AB80F350: 5 [5 / 0 / 0], 5, +43.5..+47.5, backing ED25B6A0 AGREES (A-AB7D1200 ref)',
        'VS class: covered (B container 56F18006)', 'VS class: known uncovered VS, no identity in B',
        'trace: frames 401; stop (last frame) red+100.0 s; miss-cache inserts 1']),
    ('bshape-c-at-59', vs(A_V, 43.5, 2) + vs(B_V, 44.5, 2) + vs(C_V, 59.0, 5, step=2.0), {}, [], 0, [
        'E-C4 windows: W1a red+40..59 s 4; W1b red+59..65 s 3; W2 red+65 s..stop 2; TOTAL at >= red+40 s 9',
        'ROLES: A-AB7D1200 2 (VS 2, PS 0); U-ABA99710 2 (VS 2, PS 0); C-A7F79FD0 5 (VS 5, PS 0)',
        'VS A7F7A100: 5 [0 / 3 / 2], 5, +59.0..+67.0, backing unknown',
        'HYGIENE (E-C6 part): game.log shader miss cache ON; runlog DIAGNOSTIC lines runlog not given']),
    ('only-u-vs', vs(B_V, 44.5, 3), {}, [], 0, [
        'ROLES: A-AB7D1200 0 (VS 0, PS 0); U-ABA99710 3 (VS 3, PS 0); C-A7F79FD0 0 (VS 0, PS 0); OTHER 0 (VS 0, PS 0)',
        UNC + '3; covered-role misses (high priority) 0; OTHER (no role) 0']),
    ('clean', [], {}, ['--runlog', 'RUNLOG'], 0, [
        'E-C4 windows: W1a red+40..59 s 0; W1b red+59..65 s 0; W2 red+65 s..stop 0; TOTAL at >= red+40 s 0; PRE 0',
        'ROLES: A-AB7D1200 0 (VS 0, PS 0); U-ABA99710 0 (VS 0, PS 0); C-A7F79FD0 0 (VS 0, PS 0); OTHER 0 (VS 0, PS 0)',
        UNC + '0; covered-role misses (high priority) 0; OTHER (no role) 0', 'FLAGS: none']),
    ('ps-only-u', ps(B_P, 44.6, 2), {}, [], 0, [
        'ROLES: A-AB7D1200 0 (VS 0, PS 0); U-ABA99710 2 (VS 0, PS 2)',
        UNC + '0; covered-role misses (high priority) 2 [U-ABA99710 PS 2]; OTHER (no role) 0',
        'PS class: covered (B container 6EE915B0)']),
    ('pre-and-other', vs(0xA0000010, 30.0, 2) + vs(0xA0000020, 50.0, 2) + vs(0xA0000010, 52.0, 1), {}, [], 0, [
        'OTHER 3 (VS 3, PS 0)', UNC + '0; covered-role misses (high priority) 0; OTHER (no role) 3',
        'TOTAL at >= red+40 s 3; PRE 2', 'PRE: miss rows before red+40 s: 2',
        'VS A0000010: 1 [1 / 0 / 0], 3, +52.0..+52.0', 'VS class: OTHER (no role)']),
    ('dup-a', vs(A_V, 43.2, 2) + vs(0xAB000000, 43.8, 2), {}, [], 0, [
        'ROLES: A-AB7D1200 4 (VS 4, PS 0)', 'FLAGS: DUP A-AB7D1200 VS']),
    ('backing-conflict', BASE, dict(backs=[('vertex', B_V, 0xED25B6A0)]), [], 0, [
        'VS AB64C0E0: 3 [3 / 0 / 0], 3, +44.5..+46.5, backing ED25B6A0 CONFLICT (A-AB7D1200 ref)',
        'FLAGS: BACKING-CONFLICT U-ABA99710 VS AB64C0E0']),
    ('identity-backing', BASE + ps(B_P, 44.5, 1), dict(idents=[(7, B_P, 0xED25BC80, 44.5)]), [], 0, [
        'PS ABB3F110: 1 [1 / 0 / 0], 1, +44.5..+44.5, backing ED25BC80 AGREES (U-ABA99710 ref)',
        'ROLES: A-AB7D1200 5 (VS 5, PS 0); U-ABA99710 4 (VS 3, PS 1)', 'FLAGS: none']),
    ('no-red', BASE, dict(red=False), [], 0, [
        'ROLES: NO-RED (no red-18 start in game.log; nothing assigned)',
        'HYGIENE (E-C6 part): game.log shader miss cache ON; runlog DIAGNOSTIC lines runlog not given']),
    ('fp-missing', BASE, {}, ['--fp', 'e5c874ca2b87a59d'], 0, [
        'fingerprint e5c874ca2b87a59d in game.log: False', 'FLAGS: FP-MISSING']),
    ('fp-ok', BASE, {}, ['--fp', FP, '--label', 'cand6'], 0, [
        'fingerprint %s in game.log: True' % FP, 'label cand6', 'FLAGS: none']),
    ('miss-cache-off-diag', BASE, dict(mcache='OFF', diag=True), ['--runlog', 'RUNLOG'], 0, [
        'HYGIENE (E-C6 part): game.log shader miss cache OFF; runlog DIAGNOSTIC lines 1',
        'FLAGS: MISS-CACHE-OFF, DIAGNOSTIC']),
    ('no-miss-cache-line', BASE, dict(mcache=None), [], 0, [
        'HYGIENE (E-C6 part): game.log shader miss cache not found; runlog DIAGNOSTIC lines runlog not given']),
]
# refusals: (case, args builder, expected stdout prefix); each must exit 2 and write nothing
REFUSE = [
    ('out-outside-cg7', lambda d, o: ['--out', os.path.join(os.path.dirname(CG7), 'e6-refuse-test')], 'REFUSED: --out'),
    ('out-exists', lambda d, o: ['--out', HERE], 'REFUSED: --out'),
    ('bad-fp', lambda d, o: ['--out', o, '--fp', 'XYZ'], 'REFUSED: --fp'),
    ('bad-label', lambda d, o: ['--out', o, '--label', 'a b'], 'REFUSED: --label'),
    ('missing-runlog', lambda d, o: ['--out', o, '--runlog', os.path.join(d, 'nope.txt')], 'REFUSED: missing input'),
    ('missing-trace-start', lambda d, o: ['--out', o], 'REFUSED: missing input'),
]


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest().upper()


def run(d, args):
    cmd = [sys.executable, '-B', TOOL, '--trace', os.path.join(d, 'trace', 'events.tsv'),
           '--log', os.path.join(d, 'game.log')] + args
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    rundir = os.path.join(HERE, 'run-' + stamp)
    os.makedirs(rundir)
    print('e6_roles.py %s' % sha(TOOL))
    fails = 0
    for case, rows, kw, extra, ecode, exp in CASES:
        d = build(case, rows, **kw)
        out = os.path.join(rundir, case)
        code, so = run(d, ['--out', out] + [os.path.join(d, 'runlog.txt') if x == 'RUNLOG' else x for x in extra])
        rp = os.path.join(out, 'e6_roles.txt')
        rep = open(rp, encoding='utf-8').read() if os.path.isfile(rp) else ''
        miss = [e for e in exp if e not in rep]
        ok = code == ecode and not miss
        fails += not ok
        print('%s %-18s exit %d%s' % ('PASS' if ok else 'FAIL', case, code,
                                      '' if ok else '; missing: %r; stdout: %s' % (miss, so.strip())))
    d = build('refuse', BASE)
    os.remove(os.path.join(d, 'trace', 'trace-start.json'))
    for case, mk, pre in REFUSE:
        out = os.path.join(rundir, 'refuse-' + case)
        dd = d
        if case != 'missing-trace-start':
            dd = build('refuse-ok', BASE)
        before = set(os.listdir(rundir)) | set(os.listdir(os.path.dirname(CG7)))
        code, so = run(dd, mk(dd, out))
        after = set(os.listdir(rundir)) | set(os.listdir(os.path.dirname(CG7)))
        ok = code == 2 and so.startswith(pre) and before == after
        fails += not ok
        print('%s refuse-%-18s exit %d%s' % ('PASS' if ok else 'FAIL', case, code,
                                             '' if ok else '; stdout: %s; new: %s' % (so.strip(), after - before)))
    sums = []
    for root, _, files in os.walk(FIX):
        for f in sorted(files):
            p = os.path.join(root, f)
            if f != 'SHA256SUMS.txt':
                sums.append('%s  %s' % (sha(p), os.path.relpath(p, FIX).replace('\\', '/')))
    sums.sort(key=lambda s: s[66:])
    wtxt(os.path.join(FIX, 'SHA256SUMS.txt'), '\n'.join(sums) + '\n')
    print('fixtures SHA256SUMS %s (%d files)' % (sha(os.path.join(FIX, 'SHA256SUMS.txt')), len(sums)))
    print('run dir %s' % rundir)
    print('ALL PASS' if not fails else '%d FAILED' % fails)
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())

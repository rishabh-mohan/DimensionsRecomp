#!/usr/bin/env python3
# selftest_stage6.py - M16: synthetic self-test of stage6_inputs.py (writes only selftest6\run-<stamp>\).
import datetime, hashlib, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), 'stage6_inputs.py')
RUN = os.path.join(HERE, 'run-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))


def sha_b(b):
    return hashlib.sha256(b).hexdigest().upper()


def put(p, b):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(b)


def mkbase(d, files):
    for n, b in files.items():
        put(os.path.join(d, n), b)
    with open(os.path.join(d, 'SHA256SUMS.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join('%s  %s  (%s; from fixture)\n' % (sha_b(b), n, 'root' if n == ROOT else 'placement-containers')
                        for n, b in sorted(files.items())))
    return hashlib.sha256(open(os.path.join(d, 'SHA256SUMS.txt'), 'rb').read()).hexdigest().upper()[:8]


A, B, C = b'A' * 40, b'B' * 41, b'C' * 42
N1, N2 = b'N1' * 30, b'N2' * 31
ROOT = 'vs-A58EBA123EFB541C.bin'
BASE = {'vs-AAAAAAAAAAAAAAAA.bin': A, 'ps-BBBBBBBBBBBBBBBB.bin': B, 'vs-CCCCCCCCCCCCCCCC.bin': C, ROOT: b'root' * 9}


def case(name, dump, want_rc, want_lines=(), base_sums=None, extra=(), dry=False, expect_dirs=None):
    d = os.path.join(RUN, name)
    base = os.path.join(d, 'base')
    bs = mkbase(base, BASE)
    for n, b in dump.items():
        put(os.path.join(d, 'dump', n), b)
    outr = os.path.join(d, 'out')
    os.makedirs(outr)
    cmd = [sys.executable, '-B', SCRIPT, '--dump-dir', os.path.join(d, 'dump'), '--base', base,
           '--base-sums', base_sums or bs, '--out-root', outr] + (['--dry'] if dry else []) + list(extra)
    if name == 'refuse-nodir':
        cmd[cmd.index('--dump-dir') + 1] = os.path.join(d, 'nope')
    r = subprocess.run(cmd, capture_output=True, text=True)
    ok = r.returncode == want_rc and all(w in r.stdout for w in want_lines)
    dirs = sorted(x for x in os.listdir(outr) if os.path.isdir(os.path.join(outr, x)))
    if expect_dirs is not None:
        ok = ok and len(dirs) == expect_dirs
    if ok and expect_dirs:
        comb = [x for x in dirs if x.startswith('pack-input-combined6-')][0]
        zone = [x for x in dirs if x.startswith('pack-input-zone-')][0]
        zn = sorted(os.listdir(os.path.join(outr, zone)))
        cn = sorted(os.listdir(os.path.join(outr, comb)))
        ok = ok and zn == ['SHA256SUMS.txt', 'ps-2222222222222222.bin', 'vs-1111111111111111.bin'] and len(cn) == 6
        ok = ok and ROOT not in cn
        sums = open(os.path.join(outr, comb, 'SHA256SUMS.txt'), 'rb').read()
        ok = ok and b'\r' not in sums and sums.count(b'\n') == 5 and b'from ' + zone.encode() in sums
    print('%s %-14s rc=%d (want %d) dirs=%d' % ('PASS' if ok else 'FAIL', name, r.returncode, want_rc, len(dirs)))
    with open(os.path.join(d, 'stdout.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(' '.join(cmd) + '\n' + r.stdout + r.stderr)
    if not ok:
        print(r.stdout + r.stderr)
    return ok


PC = 'placement-containers/'
good = {PC + 'vs-AAAAAAAAAAAAAAAA.bin': A,              # in base, same bytes
        PC + 'vs-1111111111111111.bin': N1,             # NEW
        PC + 'ps-2222222222222222.bin': N2,             # NEW
        PC + 'ps-3333333333333333.bin': B,              # same bytes as a base file under another name
        'vs-A58EBA123EFB541C.bin': b'root' * 9,          # root dump: never read (D-C2)
        'placement-raw/vs-0000000000000000.bin': b'raw'}  # raw: never read
res = [
    case('pass', good, 0, ('1 already in base', '1 same bytes as a base file', '2 NEW',
                           'RESULT PASS (NEW 2, base 4, root dropped 1, combined 5)',
                           '1 root file(s) not carried into combined6 (D-C2): vs-A58EBA123EFB541C.bin'), expect_dirs=2),
    case('dry', good, 0, ('2 NEW', 'RESULT PASS', ' DRY'), dry=True, expect_dirs=0),
    case('collision', dict(good, **{PC + 'ps-BBBBBBBBBBBBBBBB.bin': b'other'}), 1,
         ('name collision: ps-BBBBBBBBBBBBBBBB.bin', 'RESULT FAIL'), expect_dirs=0),
    case('nothing-new', {PC + 'vs-AAAAAAAAAAAAAAAA.bin': A}, 3, ('RESULT NOTHING-NEW',), expect_dirs=0),
    case('bad-base-sums', good, 1, ('base SHA256SUMS.txt', 'RESULT FAIL'), base_sums='00000000', expect_dirs=0),
    case('bad-name', dict(good, **{PC + 'vs-xyz.bin': b'x'}), 1, ('unexpected entry in placement-containers: vs-xyz.bin',),
         expect_dirs=0),
    case('refuse-nodir', good, 2, ('REFUSED: missing',), expect_dirs=0),
]
print('ALL PASS' if all(res) else 'FAILURES: %d' % res.count(False))
sys.exit(0 if all(res) else 1)

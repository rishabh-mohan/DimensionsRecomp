"""M3 session 3 (Overseer 01:41-01:49): proof lines for tonight's functional gate rows. Read-only.
  python -B build/agent3/session3/wc_proof.py <run dir> <arm>
arm: win3 | c1np  (bench/agent8/run/matrix-windowC.json "Proof per run": cvars/env copied from the matrix json)
     cg26         (cg26b0 / cg26L: CG26 bin, toml defaults: no back-off, no precise-wait, no LEGO_GPU_WAIT_*, no C1)
Reads every game*.log in the run dir (rotated oldest first) and run.json. Not checked here: TimerQueue < 15 % of a core
(threads.csv; s4b runs have none). Exit 0 = all proofs ok, 1 = a proof miss, 2 = usage.
"""
import glob
import hashlib
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MATRIX = os.path.join(ROOT, 'bench', 'agent8', 'run', 'matrix-windowC.json')
BAD = ['Recovered stale physical page protection', 'Unhandled guest physical write fault', 'PhysicalHeap::Protect failed',
       'is not a plain number']
EXE = {'devoff4b': 'DFBE1D43B28861A6', 'cg26': '45952D171D6204A1'}  # legodimensions.exe sha256 prefixes


def logs(run):
    fs = glob.glob(os.path.join(run, 'game*.log'))

    def key(p):
        m = re.match(r'game(?:\.(\d+))?\.log$', os.path.basename(p), re.I)
        return -(int(m.group(1)) if m and m.group(1) else 0)
    out = []
    for p in sorted(fs, key=key):
        with open(p, encoding='utf-8', errors='replace') as fh:
            out.extend(fh.read().splitlines())
    return out


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in ('win3', 'c1np', 'cg26'):
        print(__doc__)
        return 2
    run, arm = sys.argv[1], sys.argv[2]
    lines = logs(run)
    with open(os.path.join(run, 'run.json'), encoding='utf-8-sig') as fh:
        rj = json.load(fh)
    env = rj.get('env') or {}
    toml = {}  # run-game writes the cvars into the run's legodimensions.toml (key = value)
    tp = os.path.join(run, 'legodimensions.toml')
    if os.path.exists(tp):
        with open(tp, encoding='utf-8', errors='replace') as fh:
            for x in fh:
                m = re.match(r'^\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$', x)
                if m:
                    toml[m.group(1)] = m.group(2).strip('"\'')
    cnt = lambda s: sum(1 for x in lines if s in x)
    res = []

    def chk(ok, txt):
        res.append(ok)
        print('PROOF %s %s' % ('ok  ' if ok else 'MISS', txt))
    print('# wc_proof %s %s: %d log lines, exit %s, elapsed %s' % (arm, os.path.basename(run.rstrip('\\/')), len(lines),
                                                                 rj.get('exit_code'), rj.get('elapsed_s')))
    chk(rj.get('exit_code') == 0 and not rj.get('crash_events') and not rj.get('dumps'),
        'exit 0, no crash event, no dump (exit %s, crash_events %s, dumps %s)' % (
            rj.get('exit_code'), rj.get('crash_events'), rj.get('dumps')))
    # M10 review S3: bin identity from the run dir's exe copy (matrix-windowC.json notes; M10 checked the CG26 exe)
    want_exe = EXE['cg26' if arm == 'cg26' else 'devoff4b']
    h = hashlib.sha256()
    with open(os.path.join(run, 'legodimensions.exe'), 'rb') as fh:
        for blk in iter(lambda: fh.read(1 << 20), b''):
            h.update(blk)
    got = h.hexdigest().upper()
    chk(got.startswith(want_exe), 'bin: run-dir legodimensions.exe sha256 %s, want %s (%s)' % (
        got[:16], want_exe, 'devoff4b-cg26-bin' if arm == 'cg26' else 'devoff4b-bin'))
    sl = cnt('STUCK-LOCK')
    chk(sl == 0, 'STUCK-LOCK lines %d (any > 0: finding-10 rule, logs\\<id>.f10.txt)' % sl)
    for b in BAD:
        n = cnt(b)
        chk(n == 0, '"%s" x%d' % (b, n))
    gw_keys = sorted(k for k in env if k.startswith('LEGO_GPU_WAIT_'))
    backoff = [x for x in lines if 'GPU wait back-off:' in x]
    pw = cnt('TimerQueue: precise wait (timer_queue_precise_wait)')
    c1on = cnt('C1 keep-watch: on (with physical_protect_hold_global_lock)')
    c1first = cnt('C1 keep-watch: first kept protect at')
    von = cnt('C1 verify: on')
    if arm in ('win3', 'c1np'):
        with open(MATRIX, encoding='utf-8') as fh:
            a = next(x for x in json.load(fh)['arms'] if x['id'] == arm)
        miss = {c: toml.get(c.split('=', 1)[0]) for c in a['cvars'] if toml.get(c.split('=', 1)[0]) != c.split('=', 1)[1]}
        chk(not miss, 'matrix %s cvars in the run toml (%d): %s' % (arm, len(a['cvars']), 'all' if not miss else 'DIFFER %s' % miss))
        chk(c1on >= 1, '"C1 keep-watch: on (with physical_protect_hold_global_lock)" x%d' % c1on)
        chk(c1first >= 1, '"C1 keep-watch: first kept protect at" x%d' % c1first)
        chk(von == 0, 'no "C1 verify: on" (x%d)' % von)
        if arm == 'win3':
            want = a['env']
            bad = {k: env.get(k) for k, v in want.items() if env.get(k) != v}
            chk(not bad, 'run.json env %s' % ('holds %s' % want if not bad else 'DIFFERS %s' % bad))
            n1 = cnt('Host timer resolution set to 1 ms (background opt-out on)')
            chk(n1 >= 1, '"Host timer resolution set to 1 ms (background opt-out on)" x%d' % n1)
            chk(pw == 1, 'exactly one "TimerQueue: precise wait (timer_queue_precise_wait)" (x%d)' % pw)
            on = 'GPU wait back-off: ON (quantum 500 us, spin 30 us); stats OFF; GetData hook built.'
            chk(len(backoff) == 1 and on in backoff[0], 'exactly one "%s" (back-off lines x%d: %s)' % (
                on, len(backoff), backoff[0][-100:] if backoff else '-'))
        else:
            ht = cnt('Host timer resolution set to')
            chk(not backoff and pw == 0 and not gw_keys and ht == 0, 'no back-off line (x%d), no precise-wait line (x%d), no '
                '"Host timer resolution set to" line (x%d), no LEGO_GPU_WAIT_* key (%s)' % (len(backoff), pw, ht, gw_keys))
    else:
        chk(not backoff, 'no back-off init line (x%d)' % len(backoff))
        ht = cnt('Host timer resolution set to')
        chk(pw == 0 and not gw_keys and ht == 0, 'no precise-wait line (x%d), no "Host timer resolution set to" line (x%d), '
            'no LEGO_GPU_WAIT_* key (%s)' % (pw, ht, gw_keys))
        c1 = cnt('C1 keep-watch')
        chk(c1 == 0, 'no C1 line (x%d)' % c1)
    ok = all(res)
    print('RESULT: %s (%d proofs, %d miss)' % ('PASS' if ok else 'MISS', len(res), res.count(False)))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

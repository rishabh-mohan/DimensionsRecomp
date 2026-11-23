#!/usr/bin/env python3
"""W9 q-arm env / quantum proof check (Agent 6, task #22). Read-only.

matrix.json's proof rule for W9 (notes[4]): every q* game.log has exactly one
'GPU wait back-off: ON (quantum <Q> us, spin 30 us); stats OFF; GetData hook built.'
with its arm's Q, and run.json env_set holds LEGO_GPU_WAIT_BACKOFF_US=<Q> and
LEGO_GPU_WAIT_SPIN_US=30. The off arm has no 'GPU wait back-off' line and no
LEGO_GPU_WAIT_* key. No arm may log 'is not a plain number'. STUCK-LOCK counts
are reported per owner site.

Per run this script checks:
  * run.json env_set (and params.env) against matrix.json's arm env, for every
    LEGO_GPU_WAIT_* key (cold-<arm> uses <arm>'s env);
  * the number of 'GPU wait back-off' lines in game.log, and the quantum, spin,
    stats and hook fields of the init line against the arm's env;
  * 'GPU wait stats' lines (must be 0: no STATS in a timed arm);
  * 'is not a plain number' lines (must be 0);
  * STUCK-LOCK lines, with the owner lr if one is printed.

Usage: python -B w9_envcheck.py [--out FILE] <matrix_dir> [<matrix_dir> ...]
Exit:  0 all runs OK, 1 any mismatch, 2 usage error, 3 HOLD file present.
"""
import json
import os
import re
import sys

HOLD = os.path.join('perf-notes', 'WINDOW-HOLD.txt')
PREFIX = 'LEGO_GPU_WAIT_'
INIT_RE = re.compile(r'GPU wait back-off: ON \(quantum (\d+) us, spin (\d+) us\); '
                     r'stats (\w+); (.*?)\s*$')
RUN_RE = re.compile(r'^\d{4}-(cold-)?(.+?)(?:-r(\d+))?$')
LR_RE = re.compile(r'lr=([0-9A-Fa-f]{8})')


def load_json(path):
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def env_to_dict(v):
    """env_set / params.env may be a dict, a list of 'K=V' strings or None."""
    if v is None:
        return {}
    if isinstance(v, dict):
        return {str(k): str(x) for k, x in v.items()}
    out = {}
    if isinstance(v, list):
        for item in v:
            if isinstance(item, str) and '=' in item:
                k, x = item.split('=', 1)
                out[k] = x
            elif isinstance(item, dict):
                for k, x in item.items():
                    out[str(k)] = str(x)
    return out


def only_gpu(d):
    return {k: v for k, v in d.items() if k.upper().startswith(PREFIX)}


def check_dir(mdir, w):
    matrix = load_json(os.path.join(mdir, 'matrix.json'))
    arms = {a['id'].lower(): a for a in matrix.get('arms', [])}
    runs_root = os.path.join(mdir, 'runs')
    names = sorted(n for n in os.listdir(runs_root)
                   if os.path.isdir(os.path.join(runs_root, n)))
    w('== %s  (%d runs; arms in matrix.json: %s)' % (
        mdir.replace('\\', '/'), len(names), ', '.join(arms)))
    w('%-16s %-5s %-24s %-24s %5s %-22s %5s %5s %5s  %s' % (
        'run', 'arm', 'env_set LEGO_GPU_WAIT_*', 'params.env', 'init#',
        'init (Q/spin/stats)', 'stat#', 'pnum#', 'stuck', 'verdict'))
    bad_total = 0
    per_arm = {}
    for n in names:
        m = RUN_RE.match(n)
        arm = (m.group(2) if m else n).lower()
        problems = []
        a = arms.get(arm)
        if a is None:
            problems.append('arm %r not in matrix.json' % arm)
            want = {}
        else:
            want = only_gpu(env_to_dict(a.get('env')))
        rd = os.path.join(runs_root, n)
        try:
            rj = load_json(os.path.join(rd, 'run.json'))
        except Exception as e:  # noqa: BLE001
            rj = {}
            problems.append('run.json unreadable: %s' % e)
        env_set = only_gpu(env_to_dict(rj.get('env_set')))
        penv = only_gpu(env_to_dict((rj.get('params') or {}).get('env')))
        if 'env_set' not in rj:
            problems.append('run.json has no env_set')
        if env_set != want:
            problems.append('env_set %s != matrix %s' % (env_set, want))
        if penv != want:
            problems.append('params.env %s != matrix %s' % (penv, want))
        init_lines, stats_n, pnum_n, stuck = [], 0, 0, []
        try:
            with open(os.path.join(rd, 'game.log'), encoding='utf-8',
                      errors='replace') as f:
                for line in f:
                    if 'GPU wait back-off' in line:
                        init_lines.append(line.rstrip('\n'))
                    if 'GPU wait stats' in line:
                        stats_n += 1
                    if 'is not a plain number' in line:
                        pnum_n += 1
                    if 'STUCK-LOCK' in line:
                        lr = LR_RE.search(line)
                        stuck.append(lr.group(1).upper() if lr else '?')
        except OSError as e:
            problems.append('game.log unreadable: %s' % e)
        init_desc = '-'
        if want:
            q = want.get('LEGO_GPU_WAIT_BACKOFF_US')
            s = want.get('LEGO_GPU_WAIT_SPIN_US')
            if len(init_lines) != 1:
                problems.append('%d back-off lines (want 1)' % len(init_lines))
            if init_lines:
                im = INIT_RE.search(init_lines[0])
                if not im:
                    problems.append('init line not parsed: %r' % init_lines[0])
                else:
                    init_desc = '%s/%s/%s' % (im.group(1), im.group(2), im.group(3))
                    if q is not None and im.group(1) != q:
                        problems.append('quantum %s != env %s' % (im.group(1), q))
                    if s is not None and im.group(2) != s:
                        problems.append('spin %s != env %s' % (im.group(2), s))
                    if im.group(3) != 'OFF':
                        problems.append('stats %s (want OFF)' % im.group(3))
                    if im.group(4) != 'GetData hook built.':
                        problems.append('tail %r' % im.group(4))
        else:
            if init_lines:
                problems.append('%d back-off lines (want 0)' % len(init_lines))
        if stats_n:
            problems.append('%d GPU wait stats lines' % stats_n)
        if pnum_n:
            problems.append('%d "is not a plain number" lines' % pnum_n)
        if stuck:
            problems.append('STUCK-LOCK x%d (owner lr %s)' % (
                len(stuck), ','.join(stuck)))
        verdict = 'OK' if not problems else 'MISMATCH: ' + '; '.join(problems)
        bad_total += bool(problems)
        st = per_arm.setdefault(arm, {'runs': 0, 'ok': 0, 'q': set(), 'env': set()})
        st['runs'] += 1
        st['ok'] += not problems
        st['q'].add(init_desc)
        st['env'].add(' '.join('%s=%s' % kv for kv in sorted(env_set.items())) or '(none)')
        def short(d):
            if not d:
                return '(none)'
            return ' '.join('%s=%s' % (k.replace(PREFIX, ''), v)
                            for k, v in sorted(d.items()))
        w('%-16s %-5s %-24s %-24s %5d %-22s %5d %5d %5d  %s' % (
            n, arm, short(env_set), short(penv), len(init_lines), init_desc,
            stats_n, pnum_n, len(stuck), verdict))
    w('-- per arm:')
    for arm, st in per_arm.items():
        w('   %-5s runs %d, OK %d; init Q/spin/stats seen: %s; env_set seen: %s' % (
            arm, st['runs'], st['ok'], ', '.join(sorted(st['q'])),
            ' | '.join(sorted(st['env']))))
    w('-- %s: %d run(s) with a mismatch' % (os.path.basename(mdir.rstrip('/\\')), bad_total))
    w('')
    return bad_total


def main(argv):
    if os.path.exists(HOLD):
        print('HOLD file present (%s): not running.' % HOLD)
        return 3
    out_path = None
    dirs = []
    i = 0
    while i < len(argv):
        if argv[i] == '--out' and i + 1 < len(argv):
            out_path = argv[i + 1]
            i += 2
            continue
        dirs.append(argv[i])
        i += 1
    if not dirs:
        print(__doc__)
        return 2
    lines = []

    def w(s):
        print(s)
        lines.append(s)

    w('W9 env / quantum proof check (build/agent6/wnight/w9_envcheck.py)')
    w('Columns: env_set / params.env show only LEGO_GPU_WAIT_* keys (prefix dropped);')
    w('init# = game.log lines with "GPU wait back-off"; stat# = "GPU wait stats";')
    w('pnum# = "is not a plain number"; stuck = STUCK-LOCK lines.')
    w('')
    bad = 0
    for d in dirs:
        bad += check_dir(d, w)
    w('TOTAL: %d run(s) with a mismatch' % bad)
    if out_path:
        with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(lines) + '\n')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

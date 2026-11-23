#!/usr/bin/env python3
"""Agent 6, task #25 Q4: earlier native runs - any frame with pipeline_creation_ms > 2 s, or a STUCK-LOCK?

Targeted, single-threaded, read-only.  No recursive walk: it lists <parent>/<run> (or
<matrix>/<id>/runs/<run>) one level at a time, keeps runs whose run.json bin_dir names a
native bin, and reads only frames.csv (3 columns) and game.log.  Files that cannot be
opened (a live run holds a lock) are reported and skipped.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
STUCK = re.compile(r'STUCK-LOCK: critical section (0x[0-9a-fA-F]+)')
SAVED = re.compile(r'saved (\d+) startup pipeline recipes')


def candidates():
    out = []
    for parent in (r'build\agent3\runs', r'build\agent8\runs'):
        p = os.path.join(ROOT, parent)
        if os.path.isdir(p):
            out += [os.path.join(p, d) for d in sorted(os.listdir(p))]
    m = os.path.join(ROOT, r'build\agent8\matrix')
    if os.path.isdir(m):
        for mid in sorted(os.listdir(m)):
            r = os.path.join(m, mid, 'runs')
            if os.path.isdir(r):
                out += [os.path.join(r, d) for d in sorted(os.listdir(r))]
    return [d for d in out if os.path.isdir(d)]


def scan(run):
    rj = os.path.join(run, 'run.json')
    try:
        j = json.load(open(rj, encoding='utf-8-sig'))
    except Exception:
        return None
    bin_dir = str(j.get('bin_dir') or '')
    if 'native' not in os.path.basename(bin_dir.rstrip('\\/')).lower():
        return None
    res = {'run': os.path.relpath(run, ROOT), 'bin': os.path.basename(bin_dir.rstrip('\\/')),
           'started': str(j.get('started') or j.get('start') or '')[:19].replace(' ', 'T'),
           'exe': str(j.get('exe_sha256', ''))[:8],
           'route': os.path.basename(str((j.get('input_script') or {}).get('script') or '-')),
           'elapsed': j.get('elapsed_s')}
    fr = os.path.join(run, 'frames.csv')
    if not os.path.exists(fr):
        fr = os.path.join(run, 'native-frames.csv')  # Agent 8's runner
    try:
        with open(fr, encoding='utf-8', errors='replace') as f:
            head = f.readline().strip().split(',')
            ia, ib, ic = head.index('pipeline_creation_ms'), head.index('pipeline_creations'), head.index('interval_ms')
            n = tot_n = 0
            tot_ms = max_ms = max_iv = 0.0
            max_row = None
            for line in f:
                p = line.split(',')
                if len(p) != len(head):
                    continue
                n += 1
                ms, cn, iv = float(p[ia]), float(p[ib]), float(p[ic])
                tot_ms += ms
                tot_n += cn
                max_iv = max(max_iv, iv)
                if ms > max_ms:
                    max_ms, max_row = ms, (p[0], int(cn), iv)
            res.update(frames=n, pso_n=int(tot_n), pso_ms=tot_ms, max_ms=max_ms, max_row=max_row, max_iv=max_iv)
    except (OSError, ValueError) as e:
        res['frames_err'] = type(e).__name__
    gl = os.path.join(run, 'game.log')
    try:
        stuck, saved, cold = [], 0, False
        with open(gl, encoding='utf-8', errors='replace') as f:
            for line in f:
                m = STUCK.search(line)
                if m:
                    stuck.append(line[12:24] + ' ' + m.group(1))
                m = SAVED.search(line)
                if m:
                    saved = max(saved, int(m.group(1)))
                if 'no startup pipeline recipes yet' in line:
                    cold = True
        res.update(stuck=stuck, recipes_saved=saved, cold_recipes=cold)
    except OSError as e:
        res['log_err'] = type(e).__name__
    return res


def main():
    rows = [r for r in (scan(d) for d in candidates()) if r]
    print('%-62s %-12s %-19s %-8s %-24s %6s %5s %8s %8s %8s %4s %s' % (
        'run', 'bin', 'started', 'exe', 'route', 'frames', 'pso_n', 'pso_ms', 'max_ms', 'max_iv', 'rec', 'stuck'))
    for r in rows:
        print('%-62s %-12s %-19s %-8s %-24s %6s %5s %8.1f %8.1f %8.1f %4s %s%s%s' % (
            r['run'][-62:], r['bin'][:12], r['started'], r['exe'], r['route'][:24], r.get('frames', '-'),
            r.get('pso_n', '-'), r.get('pso_ms', 0.0), r.get('max_ms', 0.0), r.get('max_iv', 0.0),
            r.get('recipes_saved', '-'), len(r.get('stuck', [])),
            (' ' + ';'.join(r['stuck'][:3])) if r.get('stuck') else '',
            (' [%s %s]' % (r.get('frames_err', ''), r.get('log_err', ''))) if ('frames_err' in r or 'log_err' in r) else ''))
        if r.get('max_ms', 0) > 2000:
            print('    >2 s creation frame: frame %s, %d creations, interval %.1f ms' % r['max_row'])
    print('native runs: %d; with a >2 s creation frame: %d; with STUCK-LOCK: %d' % (
        len(rows), sum(1 for r in rows if r.get('max_ms', 0) > 2000), sum(1 for r in rows if r.get('stuck'))))
    return 0


if __name__ == '__main__':
    sys.exit(main())

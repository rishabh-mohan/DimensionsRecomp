#!/usr/bin/env python3
"""sync_smoke_post.py - post checks for RUN-SYNC-SMOKE.cmd (M2, S5) on devs5sync-bin.

Arms (run dirs from harness\\run-game.ps1):
  --off <dir>  plain default run (no cvars). Gates: smoke3d_post.py --arm xenos=<dir> exit 0 (clean exit, plain
               default, route, first 3D, check-defaults --mode xenos) and D3-OFF: 0 'd3d12_log_sync_pipeline_creation:'
               lines and 0 'sync pipeline #' lines.
  --on <dir>   d3d12_log_sync_pipeline_creation=true (+ slow_frame_log_ms=1 for the per-frame join). Gates: clean exit,
               cvars as expected, check-defaults --mode xenos PASS, D3-ON: the Initialize line exactly once.
               Then an ATTRIBUTION-ONLY summary (D2: logging perturbs timing; no timing claims) of the sync creations:
               reasons, ps none / memexport / RT path, slowest, and each slow frame with 'pipeline create' > 0
               joined to the sync lines logged before it on the same thread (tests the 322 ms / 8x no-PS hypothesis
               of build/agent3/runs/20261125-095932-s33-onsf/game.2.log:7573).
Exit 0 = every gate PASS. --selftest LOG: parse one log only (no gates), used by the dry run.
"""
import argparse, json, os, re, subprocess, sys
from collections import Counter, defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CD = os.path.join(ROOT, 'build', 'agent2', 'final', 'check-defaults.py')
SMOKE3D = os.path.join(ROOT, 'build', 'agent8', 'session3', 'smoke-final2', 'smoke3d_post.py')
INIT = 'd3d12_log_sync_pipeline_creation:'
SYNC_RE = re.compile(r'\[t(\d+)\] sync pipeline #(\d+) ([0-9A-F]{16}): ([\d.]+) ms \(([^)]*)\) \| vs ([0-9A-F]{16}) '
                     r'\(host type (\d+)\) ps (\S+) \| memexport vs ([0-9A-F]+) ps ([0-9A-F]+) \| ([^|]+?) \| '
                     r'rt bits ([0-9A-F]+) color mask ([0-9A-F]+) z (\d+) write (\d+) \| prim (\d+) \| (\w+) \| '
                     r'total ([\d.]+) ms, (\d+) lines suppressed')
SLOW_RE = re.compile(r'\[t(\d+)\] slow frame #(\d+): ([\d.]+) ms .*?\| pipeline create ([\d.]+) \((\d+)x\), new (\d+)')

out_lines = []
fails = []


def say(s=''):
    print(s)
    out_lines.append(s)


def check(name, ok, detail=''):
    say('%s  %s%s' % ('PASS' if ok else 'FAIL', name, ('  [' + detail + ']') if detail else ''))
    if not ok:
        fails.append(name)


def joined_log(rd):
    """game.N.log (oldest first = highest N) then game.log -> (lines, path of a joined copy for check-defaults)."""
    rot = sorted([f for f in os.listdir(rd) if re.fullmatch(r'game\.\d+\.log', f)], key=lambda f: -int(f.split('.')[1]))
    files = rot + (['game.log'] if os.path.exists(os.path.join(rd, 'game.log')) else [])
    lines = []
    for f in files:
        with open(os.path.join(rd, f), 'r', encoding='utf-8', errors='replace') as fh:
            lines += fh.read().splitlines()
    if len(files) == 1:
        return lines, os.path.join(rd, files[0]), files
    jp = os.path.join(HERE, 'sync-smoke', 'post', 'joined-%s.log' % os.path.basename(rd))
    os.makedirs(os.path.dirname(jp), exist_ok=True)
    with open(jp, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')
    return lines, jp, files


def run_json(rd):
    p = os.path.join(rd, 'run.json')
    if not os.path.exists(p):
        return {}
    with open(p, 'r', encoding='utf-8-sig') as fh:
        return json.load(fh)


def clean_exit(tag, J):
    check('%s clean exit (run.json exit_code 0, not early, wm_close)' % tag,
          J.get('exit_code') == 0 and not J.get('exited_early') and J.get('close_method') in ('wm_close', 'script_stop', None),
          'exit %s early %s close %s' % (J.get('exit_code_hex', J.get('exit_code')), J.get('exited_early'), J.get('close_method')))


def check_defaults(tag, logp):
    cp = subprocess.run([sys.executable, '-B', CD, logp, '--mode', 'xenos'], capture_output=True, text=True,
                        encoding='utf-8', errors='replace')
    check('%s check-defaults --mode xenos PASS' % tag, cp.returncode == 0 and 'RESULT PASS' in cp.stdout,
          'exit %d; %s' % (cp.returncode, (cp.stdout.strip().splitlines() or ['?'])[-1]))


def attribution(lines):
    say('')
    say('=== ATTRIBUTION ONLY (D2): d3d12_log_sync_pipeline_creation=true perturbs timing; counts and joins only ===')
    syncs, slow = [], []
    for i, l in enumerate(lines):
        if 'sync pipeline #' in l:
            m = SYNC_RE.search(l)
            if m:
                syncs.append(dict(i=i, t=m.group(1), n=int(m.group(2)), hash=m.group(3), ms=float(m.group(4)),
                                  reason=m.group(5), vs=m.group(6), host=int(m.group(7)), ps=m.group(8),
                                  mvs=int(m.group(9), 16), mps=int(m.group(10), 16), rt=m.group(11).strip(),
                                  rtbits=m.group(12), cmask=m.group(13), z=m.group(14), zw=m.group(15),
                                  prim=int(m.group(16)), st=m.group(17), total=float(m.group(18)), supp=int(m.group(19))))
            else:
                say('UNPARSED sync line %d: %s' % (i + 1, l[:200]))
        elif 'slow frame #' in l:
            m = SLOW_RE.search(l)
            if m:
                slow.append(dict(i=i, t=m.group(1), n=int(m.group(2)), ms=float(m.group(3)), pc=float(m.group(4)),
                                 pcx=int(m.group(5)), new=int(m.group(6))))
    say('sync lines logged %d; last #%s, last total %.1f ms, suppressed %d' % (
        len(syncs), syncs[-1]['n'] if syncs else '-', syncs[-1]['total'] if syncs else 0, syncs[-1]['supp'] if syncs else 0))
    if not syncs:
        return
    ms = sorted(s['ms'] for s in syncs)
    say('per-create ms: min %.1f median %.1f p90 %.1f max %.1f sum(logged) %.1f' % (
        ms[0], ms[len(ms) // 2], ms[min(len(ms) - 1, int(len(ms) * 0.9))], ms[-1], sum(ms)))
    for k, name in (('reason', 'reason'), ('ps', None), ('rt', 'RT path'), ('st', 'state'), ('prim', 'host prim'),
                    ('host', 'host vs type')):
        c = Counter(('none' if s['ps'] == 'none' else 'present') if k == 'ps' else s[k] for s in syncs)
        say('%-13s %s' % ((name or 'pixel shader') + ':', ', '.join('%s %d' % kv for kv in c.most_common())))
    say('memexport: vs!=0 %d, ps!=0 %d' % (sum(1 for s in syncs if s['mvs']), sum(1 for s in syncs if s['mps'])))
    say('distinct pipelines %d, distinct vs %d' % (len({s['hash'] for s in syncs}), len({s['vs'] for s in syncs})))
    say('slowest 10:')
    for s in sorted(syncs, key=lambda s: -s['ms'])[:10]:
        say('  line %d #%d %s %.1f ms (%s) vs %s ps %s rt bits %s mask %s z %s/%s prim %d' % (
            s['i'] + 1, s['n'], s['hash'], s['ms'], s['reason'], s['vs'], s['ps'], s['rtbits'], s['cmask'], s['z'],
            s['zw'], s['prim']))
    # Join: sync lines on a thread belong to the next slow-frame line on that thread.
    by_t = defaultdict(list)
    for s in syncs:
        by_t[s['t']].append(s)
    joins = []
    for f in slow:
        if f['pc'] <= 0 and f['pcx'] == 0:
            continue
        mine = [s for s in by_t.get(f['t'], []) if s['i'] < f['i'] and not s.get('used')]
        for s in mine:
            s['used'] = True
        joins.append((f, mine))
    say('slow frames with pipeline create > 0: %d (slow-frame lines total %d)' % (len(joins), len(slow)))
    if not slow:
        say('  (no slow-frame lines: slow_frame_log_ms not set?)')
    say('top 15 by pipeline-create ms: frame ms | create ms (Nx) | joined sync lines: n, sum ms, ps none, reasons')
    for f, mine in sorted(joins, key=lambda j: -j[0]['pc'])[:15]:
        say('  line %d frame #%d %.1f ms | create %.1f (%dx) new %d | sync %d, %.1f ms, ps none %d, %s' % (
            f['i'] + 1, f['n'], f['ms'], f['pc'], f['pcx'], f['new'], len(mine), sum(s['ms'] for s in mine),
            sum(1 for s in mine if s['ps'] == 'none'), dict(Counter(s['reason'] for s in mine))))
    big = [(f, m) for f, m in joins if f['pc'] >= 100]
    if big:
        say('frames with create >= 100 ms: %d; count match (Nx == joined sync lines) %d; all no-PS %d' % (
            len(big), sum(1 for f, m in big if f['pcx'] == len(m)),
            sum(1 for f, m in big if m and all(s['ps'] == 'none' for s in m))))
    unjoined = sum(1 for s in syncs if not s.get('used'))
    say('sync lines not before any slow frame with create > 0: %d' % unjoined)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--off')
    ap.add_argument('--on')
    ap.add_argument('--out')
    ap.add_argument('--selftest', help='parse one game.log (no gates)')
    a = ap.parse_args()
    say('# sync_smoke_post %s' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    if a.selftest:
        with open(a.selftest, 'r', encoding='utf-8', errors='replace') as fh:
            lines = fh.read().splitlines()
        say('selftest on %s: %d lines, Initialize lines %d, sync lines %d' % (
            a.selftest, len(lines), sum(INIT in l for l in lines), sum('sync pipeline #' in l for l in lines)))
        attribution(lines)
        say('RESULT: SELFTEST (no gates)')
    else:
        if not (a.off or a.on):
            ap.error('--off and/or --on')
        if a.off:
            say('--- OFF arm %s' % a.off)
            J = run_json(a.off)
            say('bin %s exe %s cvars %s' % (J.get('bin_dir'), (J.get('exe_sha256') or '')[:16], J.get('cvars')))
            cp = subprocess.run([sys.executable, '-B', SMOKE3D, '--arm', 'xenos=%s' % a.off,
                                 '--out', os.path.join(HERE, 'sync-smoke', 'post', 'smoke3d-off-%s.txt' % os.path.basename(a.off))],
                                capture_output=True, text=True, encoding='utf-8', errors='replace')
            for l in cp.stdout.splitlines():
                say('  | ' + l)
            check('OFF smoke3d_post.py (clean exit, plain default, route, first 3D, check-defaults) exit 0',
                  cp.returncode == 0, 'exit %d' % cp.returncode)
            lines, logp, files = joined_log(a.off)
            say('logs %s, %d lines' % (files, len(lines)))
            check('D3 OFF: 0 Initialize lines (%s)' % INIT, sum(INIT in l for l in lines) == 0,
                  '%d' % sum(INIT in l for l in lines))
            check("D3 OFF: 0 'sync pipeline #' lines", sum('sync pipeline #' in l for l in lines) == 0,
                  '%d' % sum('sync pipeline #' in l for l in lines))
        if a.on:
            say('')
            say('--- ON arm %s' % a.on)
            J = run_json(a.on)
            cv = {k: str(v).lower() for k, v in (J.get('cvars') or {}).items()}
            say('bin %s exe %s cvars %s' % (J.get('bin_dir'), (J.get('exe_sha256') or '')[:16], J.get('cvars')))
            clean_exit('ON', J)
            check('ON cvars: d3d12_log_sync_pipeline_creation=true (+ slow_frame_log_ms only)',
                  cv.get('d3d12_log_sync_pipeline_creation') == 'true' and set(cv) <= {'d3d12_log_sync_pipeline_creation', 'slow_frame_log_ms'},
                  str(cv))
            lines, logp, files = joined_log(a.on)
            say('logs %s, %d lines' % (files, len(lines)))
            init = [l for l in lines if INIT in l]
            check('D3 ON: the Initialize line exactly once', len(init) == 1, '%d; %s' % (len(init), init[0][-120:] if init else ''))
            check_defaults('ON', logp)
            attribution(lines)
        say('')
        say('RESULT: %s' % ('PASS' if not fails else 'FAIL (%d): %s' % (len(fails), '; '.join(fails))))
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(out_lines) + '\n')
    sys.exit(0 if not fails else 1)


if __name__ == '__main__':
    main()

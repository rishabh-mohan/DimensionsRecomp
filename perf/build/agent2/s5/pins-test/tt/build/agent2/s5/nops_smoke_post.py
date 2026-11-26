#!/usr/bin/env python3
"""nops_smoke_post.py - post checks for RUN-NOPS-SMOKE.cmd (M2, S5 Phase 2.1) on devs5nops-bin.

Arms (run dirs from harness\\run-game.ps1), any subset:
  --A1 <dir>  d3d12_log_sync_pipeline_creation=true; slow_frame_log_ms=1                 attribution, opt-in OFF
  --A2 <dir>  same + d3d12_async_depth_only_pipelines=true                              attribution, opt-in ON
  --T1 <dir>  plain default                                                             timing, opt-in OFF
  --T2 <dir>  d3d12_async_depth_only_pipelines=true                                     timing, opt-in ON
  --N1 <dir>  d3d12_pipeline_creation_no_wait=true                                      timing (s33 config), OFF
  --N2 <dir>  d3d12_pipeline_creation_no_wait=true; d3d12_async_depth_only_pipelines=true  timing, ON
Gates (every arm): run.json clean exit, no dumps/crash events/WER, cvars exactly as the arm, check-defaults
--mode xenos PASS, 0 'Failed to create graphics pipeline', and the Initialize lines:
  nops  'd3d12_async_depth_only_pipelines: creating' once iff the opt-in is on; never '... ignored'
  log   'd3d12_log_sync_pipeline_creation:' once iff logging; 0 'sync pipeline #' lines otherwise
  nw    'd3d12_pipeline_creation_no_wait: not waiting' once iff no_wait; never '... ignored'
  A2    0 'sync pipeline #' lines with ps none + memexport vs 0 + host render targets (the opt-in moved them all)
Report only (no gate): attribution for A1/A2 (sync lines, slow frames with 'pipeline create' joined to them,
dropped draws), timing for T/N from perf.csv (3D section stats, pipeline-miss burst frames) and the pair deltas.
Also every arm (unless --nozpd): cvar d3d12_log_occlusion_queries=true and its counter lines (S1: ZPD queries,
draws dropped inside a query, split ps / no ps; report only; Z4 gate: one 'shutdown' line, or none after the
title's hard exit, where the last counter line stands in); N2 gate: cold storage
(run.json seed_xenos empty, user_data_root = <run>/user, no storage file older than the run start); N3 gate for
T1 T2 N1 N2: kit-shots/shots.txt has one line per shot time, none black, no window problems.
Exit 0 = every gate PASS. --selftest A1=<dir> T1=<dir> ...: parse only (no gates), for the dry run.
"""
import argparse, csv, json, os, re, subprocess, sys
from collections import Counter, defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CD = os.path.join(ROOT, 'build', 'agent2', 'final', 'check-defaults.py')
LOG, NOPS, NW, SF = ('d3d12_log_sync_pipeline_creation', 'd3d12_async_depth_only_pipelines',
                     'd3d12_pipeline_creation_no_wait', 'slow_frame_log_ms')
ZPD = 'd3d12_log_occlusion_queries'
SHOT_ARMS, SHOT_TIMES = ('T1', 'T2', 'N1', 'N2'), (60, 120, 146, 152, 200)
ZPD_RE = re.compile(r'd3d12_occlusion_queries \((\w+)\): frame=(\d+) zpd=(\d+) zpd_no_host=(\d+) begun=(\d+) '
                    r"resolved=(\d+) fallback=(\d+) disabled=(\d+) reason='([^']*)' ended_by_submission=(\d+) "
                    r'draws_in_query=(\d+) dropped_in_query_ps=(\d+) dropped_in_query_no_ps=(\d+)')
ZPD_KEYS = ('frame', 'zpd', 'zpd_no_host', 'begun', 'resolved', 'fallback', 'disabled', 'reason',
            'ended_by_submission', 'draws_in_query', 'dropped_in_query_ps', 'dropped_in_query_no_ps')
ARMS = {
    'A1': {LOG: 'true', SF: '1'},
    'A2': {LOG: 'true', SF: '1', NOPS: 'true'},
    'T1': {},
    'T2': {NOPS: 'true'},
    'N1': {NW: 'true'},
    'N2': {NW: 'true', NOPS: 'true'},
}
PAIRS = (('A1', 'A2'), ('T1', 'T2'), ('N1', 'N2'))
L_NOPS_ON = 'd3d12_async_depth_only_pipelines: creating'
L_NOPS_IGN = 'd3d12_async_depth_only_pipelines ignored'
L_LOG = 'd3d12_log_sync_pipeline_creation:'
L_NW_ON = 'd3d12_pipeline_creation_no_wait: not waiting'
L_NW_IGN = 'd3d12_pipeline_creation_no_wait ignored'
L_FAILED = 'Failed to create graphics pipeline'
L_HARD_EXIT = 'Title terminated; hard-exiting process'
SYNC_RE = re.compile(r'\[t(\d+)\] sync pipeline #(\d+) ([0-9A-F]{16}): ([\d.]+) ms \(([^)]*)\) \| vs ([0-9A-F]{16}) '
                     r'\(host type (\d+)\) ps (\S+) \| memexport vs ([0-9A-F]+) ps ([0-9A-F]+) \| ([^|]+?) \| '
                     r'rt bits ([0-9A-F]+) color mask ([0-9A-F]+) z (\d+) write (\d+) \| prim (\d+) \| (\w+) \| '
                     r'total ([\d.]+) ms, (\d+) lines suppressed')
SLOW_RE = re.compile(r'\[t(\d+)\] slow frame #(\d+): ([\d.]+) ms .*?\| pipeline create ([\d.]+) \((\d+)x\), new (\d+)'
                     r'.*?\| dropped draws (\d+) \| forced pipeline waits ([\d.]+) \((\d+)x\)')

out_lines, fails = [], []


def say(s=''):
    print(s)
    out_lines.append(s)


def check(name, ok, detail='', gate=True):
    say('%s  %s%s' % ('PASS' if ok else ('FAIL' if gate else 'note'), name, ('  [' + detail + ']') if detail else ''))
    if gate and not ok:
        fails.append(name)


def joined_log(rd):
    rot = sorted([f for f in os.listdir(rd) if re.fullmatch(r'game\.\d+\.log', f)], key=lambda f: -int(f.split('.')[1]))
    files = rot + (['game.log'] if os.path.exists(os.path.join(rd, 'game.log')) else [])
    lines = []
    for f in files:
        with open(os.path.join(rd, f), 'r', encoding='utf-8', errors='replace') as fh:
            lines += fh.read().splitlines()
    if len(files) == 1:
        return lines, os.path.join(rd, files[0]), files
    jp = os.path.join(HERE, 'nops-smoke', 'post', 'joined-%s.log' % os.path.basename(rd))
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


def parse(lines):
    syncs, slow = [], []
    for i, l in enumerate(lines):
        if 'sync pipeline #' in l:
            m = SYNC_RE.search(l)
            if m:
                syncs.append(dict(i=i, t=m.group(1), n=int(m.group(2)), ms=float(m.group(4)), reason=m.group(5),
                                  ps=m.group(8), mvs=int(m.group(9), 16), rt=m.group(11).strip()))
            else:
                say('UNPARSED sync line %d: %s' % (i + 1, l[:160]))
        elif 'slow frame #' in l:
            m = SLOW_RE.search(l)
            if m:
                slow.append(dict(i=i, t=m.group(1), n=int(m.group(2)), ms=float(m.group(3)), pc=float(m.group(4)),
                                 pcx=int(m.group(5)), new=int(m.group(6)), dropped=int(m.group(7)),
                                 await_ms=float(m.group(8)), awaitx=int(m.group(9))))
    return syncs, slow


def nops_movable(s):
    return s['ps'] == 'none' and s['mvs'] == 0 and s['rt'] == 'host render targets'


def attribution(arm, lines):
    syncs, slow = parse(lines)
    say('  attribution (D2: logging perturbs timing; counts and joins only)')
    ms = sorted(s['ms'] for s in syncs)
    say('  sync lines %d, sum %.1f ms, max %.1f ms; movable by the opt-in (ps none, memexport vs 0, host RT) %d; '
        'memexport-vs %d; reasons %s' % (len(syncs), sum(ms), ms[-1] if ms else 0, sum(map(nops_movable, syncs)),
                                         sum(1 for s in syncs if s['mvs']), dict(Counter(s['reason'] for s in syncs))))
    by_t = defaultdict(list)
    for s in syncs:
        by_t[s['t']].append(s)
    joins = []
    for f in slow:
        mine = [s for s in by_t.get(f['t'], []) if s['i'] < f['i'] and not s.get('used')]
        for s in mine:
            s['used'] = True
        if f['pc'] > 0 or f['pcx'] or mine:
            joins.append((f, mine))
    say('  slow-frame lines %d; total pipeline create %.1f ms (%dx) on the command thread; dropped draws %d; '
        'forced pipeline waits %.1f ms (%dx)' % (len(slow), sum(f['pc'] for f in slow), sum(f['pcx'] for f in slow),
                                                  sum(f['dropped'] for f in slow), sum(f['await_ms'] for f in slow),
                                                  sum(f['awaitx'] for f in slow)))
    say('  top 10 frames by pipeline create: frame ms | create ms (Nx) new | dropped | sync joined n / ms / movable')
    for f, mine in sorted(joins, key=lambda j: -j[0]['pc'])[:10]:
        say('    line %d frame #%d %.1f ms | create %.1f (%dx) new %d | dropped %d | sync %d / %.1f / %d' % (
            f['i'] + 1, f['n'], f['ms'], f['pc'], f['pcx'], f['new'], f['dropped'], len(mine),
            sum(s['ms'] for s in mine), sum(map(nops_movable, mine))))
    say('  top 5 frames by frame time: frame ms | create ms (Nx) new | dropped | waits')
    for f in sorted(slow, key=lambda f: -f['ms'])[:5]:
        say('    line %d frame #%d %.1f ms | create %.1f (%dx) new %d | dropped %d | waits %.1f (%dx)' % (
            f['i'] + 1, f['n'], f['ms'], f['pc'], f['pcx'], f['new'], f['dropped'], f['await_ms'], f['awaitx']))
    return dict(syncs=syncs, slow=slow, movable=sum(map(nops_movable, syncs)),
                create_ms=sum(f['pc'] for f in slow), worst_create=max((f['pc'] for f in slow), default=0.0),
                dropped=sum(f['dropped'] for f in slow))


def pct(v, p):
    return v[min(len(v) - 1, int(len(v) * p))] if v else 0.0


def timing(arm, rd):
    p = os.path.join(rd, 'perf.csv')
    if not os.path.exists(p):
        say('  timing: no perf.csv')
        return None
    with open(p, 'r', encoding='utf-8', errors='replace') as fh:
        rows = list(csv.DictReader(fh))
    ft = [int(r['frame_time_us'] or 0) / 1000.0 for r in rows]
    draws = [int(r['draw_calls'] or 0) for r in rows]
    miss = [int(r['pipeline_cache_misses'] or 0) for r in rows]
    t, acc = [], 0.0
    for x in ft:
        acc += x
        t.append(acc / 1000.0)
    first3d = next((i for i, d in enumerate(draws) if d >= 600), None)
    if first3d is None:
        say('  timing: no 3D frame (draws >= 600) in perf.csv (%d rows)' % len(rows))
        return None
    sec = sorted(ft[first3d + 1:])
    big = sum(1 for x in sec if x > 100)
    say('  timing (perf.csv, %d rows; 3D from data row %d (0-based) at %.1f s): %d frames mean %.2f p99 %.1f p99.9 %.1f max %.1f ms; '
        '>100 ms %d, >250 ms %d; misses %d' % (len(rows), first3d, t[first3d], len(sec), sum(sec) / max(1, len(sec)),
                                               pct(sec, 0.99), pct(sec, 0.999), sec[-1] if sec else 0, big,
                                               sum(1 for x in sec if x > 250), sum(miss[first3d:])))
    bursts = [i for i in range(first3d, len(rows)) if miss[i] >= 20]
    say('  pipeline-miss bursts (>= 20 misses in a frame): %d' % len(bursts))
    for i in bursts:
        w = ft[i:i + 3]
        say('    data row %d at %.1f s: misses %d, frame %.1f ms, next-2 %s ms' % (
            i, t[i], miss[i], ft[i], ' '.join('%.1f' % x for x in w[1:])))
    return dict(sec=sec, bursts=[(i, t[i], miss[i], ft[i], max(ft[i:i + 3])) for i in bursts],
                p99=pct(sec, 0.99), max=sec[-1] if sec else 0, big=big)


def zpd_report(arm, lines, g):
    rows = []
    for l in lines:
        if 'd3d12_occlusion_queries (' in l:
            m = ZPD_RE.search(l)
            if m:
                v = list(m.groups())
                rows.append(dict(when=v[0], **{k: (x if k == 'reason' else int(x)) for k, x in zip(ZPD_KEYS, v[1:])}))
            else:
                say('UNPARSED occlusion line: %s' % l[:160])
    # Z4 (M10 zpd-log rating): every run logs one "shutdown" line; a "first" line means the route issued ZPDs.
    # On WM_CLOSE the title hard-exits ('Title terminated; hard-exiting process') before the GPU shutdown runs, so
    # with that line in the log and no shutdown line, the last counter line (normally periodic) stands in.
    n_sd, cnt = sum(r['when'] == 'shutdown' for r in rows), dict(Counter(r['when'] for r in rows))
    if n_sd == 0 and rows and any(L_HARD_EXIT in l for l in lines):
        check('%s Z4 occlusion-query "shutdown" line once' % arm, True,
              'shutdown line absent: hard-exit; counters from the last line (%s, frame %d); %d lines, %s' % (
                  rows[-1]['when'], rows[-1]['frame'], len(rows), cnt), g)
    else:
        check('%s Z4 occlusion-query "shutdown" line once' % arm, n_sd == 1, '%d lines, %s' % (len(rows), cnt), g)
    if not rows:
        say('  S1: no occlusion counter lines (no ZPD packet and no shutdown line): unknown')
        return None
    last = rows[-1]
    say('  S1 last (%s): %s' % (last['when'], ' '.join('%s=%s' % (k, last[k]) for k in ZPD_KEYS)))
    for r in rows:
        if r['when'] in ('first', 'disabled'):
            say('  S1 %s at frame %d: zpd %d begun %d resolved %d fallback %d disabled %d reason %r' % (
                r['when'], r['frame'], r['zpd'], r['begun'], r['resolved'], r['fallback'], r['disabled'], r['reason']))
    # Z5 read-out: no_ps > 0 confirms S1; a 0 counts only with begun > 0, resolved > 0 and no early loss of host
    # queries (the disable came after half the ZPDs or never, and at least half the ZPDs had host queries).
    dis = [r for r in rows if r['disabled']]
    zpd_at_disable = dis[0]['zpd'] if dis else None
    host_frac = (last['zpd'] - last['zpd_no_host']) / last['zpd'] if last['zpd'] else 0.0
    late = zpd_at_disable is None or zpd_at_disable >= 0.5 * last['zpd']
    ps = (' (+%d PS draws dropped inside a query: HEAD behaviour)' % last['dropped_in_query_ps']
          if last['dropped_in_query_ps'] else '')
    if not any(r['when'] == 'first' for r in rows) or last['zpd'] == 0:
        v = 'no ZPD on this route: the arm proves nothing about S1 (Z4)'
    elif last['dropped_in_query_no_ps']:
        v = 'S1 CONFIRMED (Z5): %d depth-only (no PS) draws dropped inside a query' % last['dropped_in_query_no_ps']
    elif last['begun'] and last['resolved'] and late and host_frac >= 0.5:
        v = 'valid 0 (Z5, this route only, lower bound): %d ZPD, begun %d, resolved %d, host fraction %.2f' % (
            last['zpd'], last['begun'], last['resolved'], host_frac)
    else:
        v = '0 NOT valid (Z5): begun %d resolved %d, first disable at zpd %s of %d, host fraction %.2f' % (
            last['begun'], last['resolved'], zpd_at_disable, last['zpd'], host_frac)
    v += ps
    say('  S1 verdict: %s' % v)
    return dict(last, s1=v)


def n2_n3_gates(arm, rd, J, g):
    seed = J.get('seed_xenos')
    udr = os.path.normcase(os.path.normpath(J.get('user_data_root') or ''))
    want = os.path.normcase(os.path.abspath(os.path.join(rd, 'user')))
    sd = os.path.join(rd, 'user', 'cache', 'shaders')
    t0 = float(J.get('started_epoch_s') or 0)
    files = [os.path.join(dp, f) for dp, _, fs in os.walk(sd) for f in fs] if os.path.isdir(sd) else []
    old = [f for f in files if os.path.getmtime(f) < t0 - 1]
    check('%s N2 cold storage (no seed, user_data_root = run/user, no file older than the run)' % arm,
          not seed and udr == want and t0 > 0 and not old,
          'seed %r, user_data_root %s, %d storage files (%s), older %d' % (
              seed, J.get('user_data_root'), len(files),
              ', '.join('%s %d B' % (os.path.basename(f), os.path.getsize(f)) for f in files), len(old)), g)
    if arm not in SHOT_ARMS:
        return
    sp = os.path.join(rd, 'kit-shots', 'shots.txt')
    sl = open(sp, encoding='utf-8', errors='replace').read().splitlines() if os.path.exists(sp) else []
    okl = [l for l in sl if re.search(r': (printwindow|screen copy) -> ', l)]
    check('%s N3 screenshots (%d times, none black)' % (arm, len(SHOT_TIMES)), len(okl) == len(sl) == len(SHOT_TIMES),
          '%d ok of %d lines: %s' % (len(okl), len(sl), ' | '.join(l.split(': ', 1)[-1][:60] for l in sl if l not in okl)
                                     or os.path.dirname(sp)), g)


def arm_gates(arm, rd, gates=True, zpd=True):
    exp = dict(ARMS[arm], **({ZPD: 'true'} if zpd else {}))
    say('')
    say('--- %s %s' % (arm, rd))
    J = run_json(rd)
    cv = {k: str(v).lower() for k, v in (J.get('cvars') or {}).items()}
    say('bin %s exe %s cvars %s' % (J.get('bin_dir'), (J.get('exe_sha256') or '')[:16], J.get('cvars')))
    g = gates
    check('%s clean exit (exit 0, not early, wm_close)' % arm,
          J.get('exit_code') == 0 and not J.get('exited_early') and J.get('close_method') in ('wm_close', 'script_stop', None),
          'exit %s early %s close %s' % (J.get('exit_code_hex', J.get('exit_code')), J.get('exited_early'),
                                         J.get('close_method')), g)
    check('%s no dumps / crash events / WER' % arm, not J.get('dumps') and not J.get('crash_events') and not J.get('wer_seen'),
          'dumps %s crash %s wer %s' % (J.get('dumps'), J.get('crash_events'), J.get('wer_seen')), g)
    check('%s cvars exactly %s' % (arm, exp or 'none'), cv == exp, str(cv), g)
    lines, logp, files = joined_log(rd)
    say('logs %s, %d lines' % (files, len(lines)))
    cp = subprocess.run([sys.executable, '-B', CD, logp, '--mode', 'xenos'], capture_output=True, text=True,
                        encoding='utf-8', errors='replace')
    check('%s check-defaults --mode xenos PASS' % arm, cp.returncode == 0 and 'RESULT PASS' in cp.stdout,
          'exit %d; %s' % (cp.returncode, (cp.stdout.strip().splitlines() or ['?'])[-1]), g)
    n = lambda s: sum(s in l for l in lines)
    check('%s nops Initialize line %s' % (arm, 'once' if NOPS in exp else 'absent'), n(L_NOPS_ON) == (1 if NOPS in exp else 0),
          '%d' % n(L_NOPS_ON), g)
    check('%s no "%s"' % (arm, L_NOPS_IGN), n(L_NOPS_IGN) == 0, '%d' % n(L_NOPS_IGN), g)
    check('%s sync-log Initialize line %s' % (arm, 'once' if LOG in exp else 'absent'), n(L_LOG) == (1 if LOG in exp else 0),
          '%d' % n(L_LOG), g)
    if LOG not in exp:
        check("%s 0 'sync pipeline #' lines" % arm, n('sync pipeline #') == 0, '%d' % n('sync pipeline #'), g)
    check('%s no_wait Initialize line %s' % (arm, 'once' if NW in exp else 'absent'), n(L_NW_ON) == (1 if NW in exp else 0),
          '%d' % n(L_NW_ON), g)
    check('%s no "%s"' % (arm, L_NW_IGN), n(L_NW_IGN) == 0, '%d' % n(L_NW_IGN), g)
    check('%s 0 "%s"' % (arm, L_FAILED), n(L_FAILED) == 0, '%d' % n(L_FAILED), g)
    n2_n3_gates(arm, rd, J, g)
    res = {'rd': rd}
    if zpd:
        res['zpd'] = zpd_report(arm, lines, g)
    if LOG in exp:
        res['attr'] = attribution(arm, lines)
        if NOPS in exp:
            check('%s 0 movable no-PS sync creates (ps none, memexport vs 0, host RT)' % arm, res['attr']['movable'] == 0,
                  '%d' % res['attr']['movable'], g)
    else:
        res['timing'] = timing(arm, rd)
    return res


def pair_report(R):
    say('')
    say('=== PAIRS (report only; success is judged by the Overseer / user, README section 6) ===')
    for a, b in PAIRS:
        if a not in R or b not in R:
            continue
        x, y = R[a], R[b]
        if x.get('zpd') and y.get('zpd'):
            zx, zy = x['zpd'], y['zpd']
            say('%s -> %s S1: zpd %d -> %d, draws in a query %d -> %d, dropped in a query no-PS %d -> %d, PS %d -> %d, '
                'disabled %d -> %d' % (a, b, zx['zpd'], zy['zpd'], zx['draws_in_query'], zy['draws_in_query'],
                                       zx['dropped_in_query_no_ps'], zy['dropped_in_query_no_ps'],
                                       zx['dropped_in_query_ps'], zy['dropped_in_query_ps'], zx['disabled'], zy['disabled']))
            say('    %s S1: %s' % (a, zx['s1']))
            say('    %s S1: %s' % (b, zy['s1']))
        if 'attr' in x and 'attr' in y:
            say('%s -> %s: command-thread create %.1f -> %.1f ms, worst frame create %.1f -> %.1f ms, movable sync '
                'creates %d -> %d, dropped draws %d -> %d' % (
                    a, b, x['attr']['create_ms'], y['attr']['create_ms'], x['attr']['worst_create'],
                    y['attr']['worst_create'], x['attr']['movable'], y['attr']['movable'], x['attr']['dropped'],
                    y['attr']['dropped']))
        elif x.get('timing') and y.get('timing'):
            tx, ty = x['timing'], y['timing']
            say('%s -> %s: 3D p99 %.1f -> %.1f ms, max %.1f -> %.1f ms, >100 ms frames %d -> %d' % (
                a, b, tx['p99'], ty['p99'], tx['max'], ty['max'], tx['big'], ty['big']))
            for k in range(max(len(tx['bursts']), len(ty['bursts']))):
                bx = tx['bursts'][k] if k < len(tx['bursts']) else None
                by = ty['bursts'][k] if k < len(ty['bursts']) else None
                f = lambda q: ('%.1f s misses %d frame %.1f (max of 3: %.1f)' % q[1:]) if q else '-'
                say('    burst %d: %s | %s' % (k + 1, f(bx), f(by)))


def main():
    ap = argparse.ArgumentParser()
    for a in ARMS:
        ap.add_argument('--' + a)
    ap.add_argument('--out')
    ap.add_argument('--nozpd', action='store_true', help='bin/kit without d3d12_log_occlusion_queries')
    ap.add_argument('--selftest', nargs='+', metavar='ARM=DIR', help='parse only, no gates')
    a = ap.parse_args()
    say('# nops_smoke_post %s' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    R = {}
    if a.selftest:
        for kv in a.selftest:
            arm, rd = kv.split('=', 1)
            R[arm] = arm_gates(arm, rd, gates=False, zpd=not a.nozpd)
        pair_report(R)
        say('')
        say('RESULT: SELFTEST (no gates)')
    else:
        given = [(k, getattr(a, k)) for k in ARMS if getattr(a, k)]
        if not given:
            ap.error('give at least one arm')
        for arm, rd in given:
            R[arm] = arm_gates(arm, rd, zpd=not a.nozpd)
        pair_report(R)
        say('')
        say('RESULT: %s' % ('PASS' if not fails else 'FAIL (%d): %s' % (len(fails), '; '.join(fails))))
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(out_lines) + '\n')
    sys.exit(0 if not fails else 1)


if __name__ == '__main__':
    main()

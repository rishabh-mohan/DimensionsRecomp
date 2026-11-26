#!/usr/bin/env python3
"""dtime_post.py - S5, M16: read-out of the RUN-DTIME arms (diagnostic only, never scored as timing).

Arms: d-timing (LEGO_NATIVE_TIMING=1) and d-slowops (LEGO_NATIVE_SLOW_OPERATIONS=1), attract-long, cold, uncapped.
Per arm (read-only over <run>\\frames.csv and <run>\\game.log):
  - the switch frame: the largest interval_ms at t 70-115 s (t = cumulative interval_ms); found if >= 150 ms.
    The draw step (prev >= 20 draws, stall <= 2, next >= 20) is reported; psorows saw 41 > 1 > 59/61.
  - every nonzero frames.csv column for frames -2..+4 around it;
  - the stall frame: top-level renderer ms (texture, draw stages, buffer hash, sync, frame-slot wait, present cpu)
    vs interval_ms (approximate: the columns may overlap);
  - detailed_timing_enabled of the stall frame;
  - the anchor: the first game.log "BeginTiling ... host=1280x720" line (the scene switch, psorows NOTE-worst-frame-t90);
  - the Native timing/draw/constants/buffer/synchronization/callback lines and the "Native slow CPU operation" lines
    within [anchor - 2.0 s, anchor + 2.0 s], plus exact "Native timing: frame=<stall frame>" matches anywhere;
  - slow-op lines: total, before the window (the game logs only the first 128 in total).
RESULT: PASS = both arms: switch found; d-timing: detailed_timing_enabled=1 in the stall frame; d-slowops: >= 1 slow-op
line in the window. PASS-WITH-CHECKS = an item missing (listed). FAIL = an arm missing, or no frames.csv / no rows.
Usage: dtime_post.py --arm d-timing=<run dir> --arm d-slowops=<run dir> --out <file>
       dtime_post.py --selftest [--out <file>]
Exit: 0 = report written (any RESULT) / selftest pass, 1 = selftest fail, 2 = usage error.
"""
import csv
import datetime as dt
import os
import re
import shutil
import sys
import tempfile

ARMS = ('d-timing', 'd-slowops')
T_LO, T_HI = 70000.0, 115000.0
SWITCH_MS = 150.0
WIN_BEFORE, WIN_AFTER = 2.0, 2.0
SLOW_CAP = 128
TOP_LEVEL = ('texture_ms', 'bindings_ms', 'begin_ms', 'pipeline_ms', 'constants_ms', 'vertices_ms', 'issue_ms',
             'tail_ms', 'buffer_hash_ms', 'sync_ms', 'frame_slot_wait_ms', 'present_cpu_ms')
CONFIG = {'fsr_enabled', 'scene_render_width', 'scene_render_height', 'output_width', 'output_height',
          'presentation_focused', 'native_vsync', 'present_timing_enabled', 'presentation_borderless',
          'presentation_monitor_index', 'presentation_refresh_hz', 'native_fps_limit_cvar', 'present_source_width',
          'present_source_height', 'spatial_fsr_presented', 'detailed_timing_enabled'}
TS_RE = re.compile(r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]')
ANCHOR_RE = re.compile(r'BeginTiling .*host=1280x720')
TIMING_RE = re.compile(r'Native (timing|draw timing|constants timing|buffer timing|synchronization timing|'
                       r'synchronization reasons ms|callback queue): ')
SLOW_RE = re.compile(r'Native slow CPU operation: (\S+) total_ms=([\d.]+)')


class Usage(Exception):
    pass


def fnum(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return 0.0


def ts(line):
    m = TS_RE.match(line)
    return dt.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f') if m else None


def read_frames(path):
    with open(path, newline='', encoding='utf-8', errors='replace') as f:
        return list(csv.DictReader(f))


def find_switch(rows):
    t = 0.0
    best = None
    for i, r in enumerate(rows):
        iv = fnum(r.get('interval_ms'))
        t += iv
        if T_LO <= t <= T_HI and (best is None or iv > best[1]):
            best = (i, iv, t)
    return best


def analyse(name, run):
    """returns (lines, checks, fatal)"""
    out, checks = [], []
    out.append(f'== arm {name}: {run}')
    fp = os.path.join(run, 'frames.csv')
    if not os.path.isdir(run) or not os.path.isfile(fp):
        out.append('  FAIL: no run dir or no frames.csv')
        return out, checks, f'{name}: no frames.csv'
    rows = read_frames(fp)
    if not rows:
        out.append('  FAIL: frames.csv has no rows')
        return out, checks, f'{name}: frames.csv empty'
    out.append(f'  frames.csv rows {len(rows)}')
    sw = find_switch(rows)
    stall = None
    if not sw or sw[1] < SWITCH_MS:
        checks.append(f'{name}: no switch frame (max interval at t 70-115 s '
                      f'{"%.1f" % sw[1] if sw else "n/a"} ms < {SWITCH_MS:.0f})')
        out.append('  switch: NOT FOUND')
    else:
        i, iv, t = sw
        stall = rows[i]
        dc = lambda k: int(fnum(rows[k].get('draw_calls'))) if 0 <= k < len(rows) else -1
        step = f'{dc(i - 1)} > {dc(i)} > {dc(i + 1)}'
        stepok = dc(i - 1) >= 20 and 0 <= dc(i) <= 2 and dc(i + 1) >= 20
        out.append(f'  switch: frame {stall.get("frame")} at t={t / 1000:.2f} s, interval {iv:.2f} ms, '
                   f'draw step {step} ({"ok" if stepok else "NOT the 41>1>59 shape"})')
        if not stepok:
            checks.append(f'{name}: draw step {step} is not the psorows shape')
        out.append('  config (stall frame): ' + ' '.join(f'{c}={stall.get(c)}' for c in stall if c in CONFIG))
        for k in range(i - 2, i + 5):
            if not 0 <= k < len(rows):
                continue
            nz = [f'{c}={v}' for c, v in rows[k].items() if c and c != 'frame' and c not in CONFIG and fnum(v) != 0.0]
            out.append(f'    [{k - i:+d}] frame {rows[k].get("frame")}: {" ".join(nz)}')
        parts = [(c, fnum(stall.get(c))) for c in TOP_LEVEL if c in stall]
        tot = sum(v for _, v in parts)
        out.append(f'  stall frame renderer-measured {tot:.2f} ms of interval {iv:.2f} ms '
                   f'(unaccounted {iv - tot:.2f} ms; columns may overlap): '
                   + ' '.join(f'{c}={v:.2f}' for c, v in parts if v))
        fu = rows[i + 1] if i + 1 < len(rows) else None
        if fu:
            fparts = [(c, fnum(fu.get(c))) for c in TOP_LEVEL if c in fu]
            ftot = sum(v for _, v in fparts)
            out.append(f'  follow-up frame renderer-measured {ftot:.2f} ms of interval {fnum(fu.get("interval_ms")):.2f} ms, '
                       f'pipeline_creations {fu.get("pipeline_creations")} ({fnum(fu.get("pipeline_creation_ms")):.2f} ms): '
                       + ' '.join(f'{c}={v:.2f}' for c, v in fparts if v))
    dte = stall.get('detailed_timing_enabled') if stall else None
    out.append(f'  detailed_timing_enabled (stall frame) = {dte}')
    if name == 'd-timing' and stall is not None and fnum(dte) != 1.0:
        checks.append('d-timing: detailed_timing_enabled is not 1 in the stall frame')
    # game.log
    gl = os.path.join(run, 'game.log')
    lines = []
    if os.path.isfile(gl):
        with open(gl, encoding='utf-8', errors='replace') as f:
            lines = f.read().splitlines()
    else:
        checks.append(f'{name}: no game.log')
    t_first = next((x for x in (ts(l) for l in lines) if x), None)
    anchor = None
    for l in lines:
        if ANCHOR_RE.search(l):
            anchor = ts(l)
            if anchor:
                break
    slow_all = [l for l in lines if SLOW_RE.search(l)]
    if anchor is None:
        checks.append(f'{name}: no BeginTiling 1280x720 anchor in game.log')
        out.append('  anchor: NOT FOUND')
        near = []
        before = len(slow_all)
    else:
        off = (anchor - t_first).total_seconds() if t_first else float('nan')
        out.append(f'  anchor: first BeginTiling 1280x720 at {anchor:%H:%M:%S.%f}'[:-3]
                   + f' (+{off:.1f} s after the first log line)')
        lo, hi = anchor - dt.timedelta(seconds=WIN_BEFORE), anchor + dt.timedelta(seconds=WIN_AFTER)
        near = [l for l in lines if (TIMING_RE.search(l) or SLOW_RE.search(l)) and (ts(l) and lo <= ts(l) <= hi)]
        before = sum(1 for l in slow_all if ts(l) and ts(l) < lo)
    nt = sum(1 for l in near if TIMING_RE.search(l))
    ns = sum(1 for l in near if SLOW_RE.search(l))
    out.append(f'  window [anchor -{WIN_BEFORE:.1f} s, +{WIN_AFTER:.1f} s]: {nt} timing lines, {ns} slow-op lines')
    for l in near:
        out.append(f'    {l}')
    if stall is not None:
        exact = [l for l in lines if f'Native timing: frame={stall.get("frame")} ' in l]
        out.append(f'  exact "Native timing: frame={stall.get("frame")}" lines: {len(exact)}')
        for l in exact:
            if l not in near:
                out.append(f'    {l}')
    out.append(f'  slow-op lines: {len(slow_all)} total, {before} before the window (cap {SLOW_CAP})')
    if name == 'd-slowops':
        if len(slow_all) >= SLOW_CAP:
            checks.append(f'd-slowops: slow-op cap reached ({len(slow_all)} lines, {before} before the window)')
        if ns == 0:
            checks.append('d-slowops: no slow-op line in the window around the anchor')
        labels = {}
        for l in near:
            m = SLOW_RE.search(l)
            if m:
                labels[m.group(1)] = labels.get(m.group(1), 0.0) + float(m.group(2))
        if labels:
            out.append('  slow-op total_ms by label in the window: '
                       + ' '.join(f'{k}={v:.1f}' for k, v in sorted(labels.items(), key=lambda kv: -kv[1])))
    if name == 'd-timing' and anchor is not None and nt == 0:
        out.append('  note: no Native timing line in the window (logging is limited: first 16 frames > 40 ms, then every 30th)')
    return out, checks, ''


def report(arms, outp):
    """arms: dict name -> dir. Returns the RESULT line."""
    lines = ['S5 dtime read-out (M16): DIAGNOSTIC ONLY - LEGO_NATIVE_TIMING perturbs frame times; never scored as timing.',
             f'arms: {" ".join(f"{k}={v}" for k, v in arms.items())}']
    checks, fatal = [], []
    for name in ARMS:
        if name not in arms:
            fatal.append(f'{name}: arm missing')
            lines.append(f'== arm {name}: MISSING')
            continue
        o, c, f = analyse(name, arms[name])
        lines += o
        checks += c
        if f:
            fatal.append(f)
    if fatal:
        res = 'RESULT: FAIL (' + '; '.join(fatal) + ')'
    elif checks:
        res = 'RESULT: PASS-WITH-CHECKS (' + '; '.join(checks) + ')'
    else:
        res = 'RESULT: PASS'
    lines += [f'CHECK: {c}' for c in checks] + [res]
    os.makedirs(os.path.dirname(os.path.abspath(outp)), exist_ok=True)
    with open(outp, 'w', encoding='ascii', errors='replace', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    return res


def parse_args(argv):
    arms, outp, selftest = {}, None, False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--selftest':
            selftest = True
        elif a in ('--arm', '--out'):
            if i + 1 >= len(argv):
                raise Usage(f'{a} needs a value')
            v = argv[i + 1]
            i += 1
            if a == '--out':
                outp = v
            else:
                if '=' not in v:
                    raise Usage(f'--arm wants name=dir, got {v}')
                k, d = v.split('=', 1)
                if k not in ARMS:
                    raise Usage(f'unknown arm {k} (want {" or ".join(ARMS)})')
                if k in arms:
                    raise Usage(f'arm {k} given twice')
                arms[k] = d
        else:
            raise Usage(f'unknown argument {a}')
        i += 1
    if not selftest and not outp:
        raise Usage('--out is required')
    if selftest and arms:
        raise Usage('--selftest takes no --arm')
    return arms, outp, selftest


# --- selftest ---
HDR = ['frame', 'interval_ms', 'texture_ms', 'draw_calls', 'sync_ms', 'bindings_ms', 'pipeline_ms', 'issue_ms',
       'detailed_timing_enabled', 'pipeline_creations', 'pipeline_creation_ms']
T0 = dt.datetime(2026, 11, 26, 4, 0, 0)


def L(sec, msg):
    t = T0 + dt.timedelta(seconds=sec)
    return f'[{t:%Y-%m-%d %H:%M:%S}.{t.microsecond // 1000:03d}] [info] [core] [t1] {msg}'


def make_run(root, name, dte=1, switch=True, anchor=True, slow_near=True, slow_boot=3, timing_near=True):
    d = os.path.join(root, name)
    os.makedirs(d)
    rows = []
    for k in range(6000):            # 16.7 ms frames: t reaches ~100 s
        rows.append({'frame': k + 2, 'interval_ms': '16.7', 'draw_calls': '41', 'detailed_timing_enabled': str(dte)})
    if switch:
        s = 5700                     # t ~ 95.2 s
        rows[s].update({'interval_ms': '350.5', 'draw_calls': '1', 'texture_ms': '0.5' if dte else '0'})
        rows[s + 1].update({'interval_ms': '90.2', 'draw_calls': '59', 'pipeline_creations': '29',
                            'pipeline_creation_ms': '19.1', 'texture_ms': '30.0', 'bindings_ms': '5.0'})
    with open(os.path.join(d, 'frames.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=HDR, restval='0')
        w.writeheader()
        w.writerows(rows)
    g = [L(0, 'GPU route: direct native D3D-to-RHI; PM4 disabled')]
    g += [L(5 + k * 0.1, f'Native slow CPU operation: boot_op total_ms=5.000 a=1.000 b=1.000 c=1.000 d=1.000 tail_ms=1.000')
          for k in range(slow_boot)]
    if anchor:
        g.append(L(95.0, 'Native GPU: BeginTiling flags=1 tiles=2 host=1280x720 viewport=1280x720 guest_count=0'))
    if timing_near:
        g.append(L(95.4, 'Native timing: frame=5702 interval=350.50ms texture_cpu=0.50ms calls=1 source_hits=0 converted=0 bytes source=0.00ms hash=0.00ms hashed=0'))
        g.append(L(95.4, 'Native draw timing: calls=1 bindings=0.00 begin=0.00 pipeline=0.00 constants=0.00 vertices=0.00 issue=0.00 tail=0.00ms'))
    if slow_near:
        g.append(L(95.6, 'Native slow CPU operation: texture_upload total_ms=25.000 convert=20.000 b=1.000 c=1.000 d=1.000 tail_ms=2.000'))
    with open(os.path.join(d, 'game.log'), 'w') as f:
        f.write('\n'.join(g) + '\n')
    return d


def selftest(outp):
    root = tempfile.mkdtemp(prefix='dtime-selftest-')
    log = []
    bad = 0
    try:
        def case(label, kw_t, kw_s, want, missing=None):
            nonlocal bad
            r = os.path.join(root, label)
            os.makedirs(r)
            arms = {}
            if missing != 'd-timing':
                arms['d-timing'] = make_run(r, 'd-timing', **kw_t)
            if missing != 'd-slowops':
                arms['d-slowops'] = make_run(r, 'd-slowops', **kw_s)
            res = report(arms, os.path.join(r, 'post.txt'))
            ok = res.startswith(f'RESULT: {want}') and (want != 'PASS' or res == 'RESULT: PASS')
            bad += 0 if ok else 1
            log.append(f'{"ok  " if ok else "BAD "} {label}: want {want}, got {res}')
            return os.path.join(r, 'post.txt')

        p = case('good', {}, {'dte': 0}, 'PASS')
        with open(p) as f:
            txt = f.read()
        for needle in ('switch: frame 5702 at t=95.', 'draw step 41 > 1 > 59 (ok)', 'exact "Native timing: frame=5702" lines: 1',
                       'slow-op total_ms by label in the window: texture_upload=25.0', 'follow-up frame renderer-measured 35.00 ms'):
            ok = needle in txt
            bad += 0 if ok else 1
            log.append(f'{"ok  " if ok else "BAD "} good report contains: {needle}')
        case('missing-arm', {}, {}, 'FAIL', missing='d-slowops')
        case('timing-off', {'dte': 0}, {'dte': 0}, 'PASS-WITH-CHECKS')
        case('slowop-cap', {}, {'dte': 0, 'slow_boot': 128, 'slow_near': False}, 'PASS-WITH-CHECKS')
        case('no-anchor', {'anchor': False}, {'dte': 0, 'anchor': False}, 'PASS-WITH-CHECKS')
        case('no-switch', {'switch': False}, {'dte': 0}, 'PASS-WITH-CHECKS')
        # no frames.csv -> FAIL
        r = os.path.join(root, 'no-frames')
        os.makedirs(os.path.join(r, 'd-timing'))
        res = report({'d-timing': os.path.join(r, 'd-timing'), 'd-slowops': make_run(r, 'd-slowops', dte=0)},
                     os.path.join(r, 'post.txt'))
        ok = res.startswith('RESULT: FAIL')
        bad += 0 if ok else 1
        log.append(f'{"ok  " if ok else "BAD "} no-frames: want FAIL, got {res}')
        # usage errors
        for argv in ([], ['--arm', 'd-timing'], ['--arm', 'bogus=x', '--out', 'o'], ['--bogus'],
                     ['--arm', 'd-timing=a', '--arm', 'd-timing=b', '--out', 'o'], ['--selftest', '--arm', 'd-timing=a']):
            try:
                parse_args(argv)
                ok = False
            except Usage:
                ok = True
            bad += 0 if ok else 1
            log.append(f'{"ok  " if ok else "BAD "} usage error for {argv}')
    finally:
        shutil.rmtree(root, ignore_errors=True)
    log.append(f'SELFTEST {"PASS" if not bad else "FAIL (%d)" % bad}')
    txt = '\n'.join(log)
    print(txt)
    if outp:
        os.makedirs(os.path.dirname(os.path.abspath(outp)), exist_ok=True)
        with open(outp, 'w', encoding='ascii', newline='\n') as f:
            f.write(txt + '\n')
    return 0 if not bad else 1


def main(argv):
    try:
        arms, outp, st = parse_args(argv)
    except Usage as e:
        print(f'usage error: {e}\n' + __doc__.split('Usage: ')[1].split('Exit:')[0].rstrip(), file=sys.stderr)
        return 2
    if st:
        return selftest(outp)
    res = report(arms, outp)
    print(res)
    print(f'report {outp}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

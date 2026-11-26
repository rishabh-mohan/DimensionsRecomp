#!/usr/bin/env python3
"""S5 natcmp post (M16): n4bp60 vs a base arm (ship60 or nat60) ABBA pairs with a per-second nongame-load flag.
Python 3, stdlib only.

  python -B cmp_post.py --run LABEL=OUTDIR [--run ...] [--gate-timeout LABEL ...] [--base ship60|nat60] --out FILE
  python -B cmp_post.py --selftest --out FILE

LABEL = prime-<arm> (unscored) or sN-<arm> (scored; pair k = s(2k-1) + s(2k), one base arm and one n4bp60).
The base arm = --base, else the base arm of the scored runs (ship60 or nat60; more than one is flagged and only pairs
  with the chosen base are valid).
OUTDIR = a run-matrix -OutDir (the newest runs\\* with run.json is used) or a run dir itself.
Per run: run.json status/excluded; score3d.json (else run.json score3d): fps, p99, >100 ms, 1% low, draws, GPU.
  Frames as score3d.py load_frames: native-frames.csv / frames.csv (interval_ms) for native arms, else perf.csv
  (frame_time_us, xenos ship60). The window = score3d's frames (from the start frame, frame-time sum to s3d_span_s); fps
  recomputed (warn > 1 %).
  sys.csv rows with t_s in [s3d_window_start_s, + span): nongame cores, eff MHz, game cores; MsMpEng cores from the
  top_cpu snapshots (window, and launch t_s < 30). A clean second = nongame < 4.0 cores (eff MHz is info only: it tracks
  the arm's own GPU power, M12 p03);
  more than 25 % unclean seconds = CONFOUNDED. Clean fps = frames / frame time in the clean seconds (a frame's second
  = int(frame end + s3d_launch_offset_s), the sys t_s axis). Draw bins (mean ms); PSO creations in the window (native
  frames only; '-' for perf.csv).
Pair valid = both runs OK (status OK, s3d OK, not excluded), neither CONFOUNDED nor GATE-TIMEOUT.
Verdict over valid pairs, diff = (n4bp60 - base) / base on s3d fps: none valid = INCONCLUSIVE; all < -5 % = n4bp60
  SLOWER; all > +5 % = n4bp60 FASTER; else NO CLEAR DIFFERENCE; fewer than 2 valid pairs = INCONCLUSIVE (the n=1
  direction is quoted as indicative, M10 S2). Info: clean-seconds fps per arm (runs >= 30 clean s).
Exit 0 report written (any verdict); 1 no runs / unreadable; 2 usage. --selftest: nonzero on any failed check.
"""
import argparse
import csv
import json
import os
import re
import shutil
import statistics as st
import sys
import tempfile

TEST, BASES = 'n4bp60', ('ship60', 'nat60')
ARMS = BASES + (TEST,)
NG_MAX, EFF_MIN, UNCLEAN_MAX, THR, MIN_CLEAN, MIN_PAIRS = 4.0, 2200.0, 0.25, 5.0, 30, 2
# The CPU clock is not a clean-second criterion: M12 p03 shows it tracks the arm's own GPU power (shared cooling), so
# gating on it would flag the heavier arm itself. eff MHz is reported per run as info.
CLEAN_USES_EFF = False


def clean_rule():
    return 'nongame < %.1f cores%s' % (NG_MAX, (' and eff >= %.0f MHz' % EFF_MIN) if CLEAN_USES_EFF else ' (eff MHz info only)')
BINS = [(0, 500), (500, 1000), (1000, 2000), (2000, 3000), (3000, 4000), (4000, 6000), (6000, 10 ** 9)]


def num(v, d=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def read_json(p):
    try:
        with open(p, encoding='utf-8-sig') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def read_rows(p):
    with open(p, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def find_run(outdir):
    if os.path.exists(os.path.join(outdir, 'run.json')):
        return outdir
    rr = os.path.join(outdir, 'runs')
    if not os.path.isdir(rr):
        return None
    c = [os.path.join(rr, n) for n in os.listdir(rr) if os.path.exists(os.path.join(rr, n, 'run.json'))]
    return max(c, key=os.path.getmtime) if c else None


def load_frames(rd):
    """-> kind, source, [(dt_s, row)]; the order and columns of score3d.py load_frames"""
    for name in ('native-frames.csv', 'frames.csv'):
        p = os.path.join(rd, name)
        if os.path.exists(p):
            rows = read_rows(p)
            if rows and 'interval_ms' in rows[0] and 'draw_calls' in rows[0]:
                return 'native', name, [(num(x.get('interval_ms'), 0.0) / 1e3, x) for x in rows]
    p = os.path.join(rd, 'perf.csv')
    if os.path.exists(p):
        rows = read_rows(p)
        return 'xenos', 'perf.csv', [(num(x.get('frame_time_us'), 0.0) / 1e6, x) for x in rows]
    return None, None, []


def msmp(top):
    """MsMpEng cores in one top_cpu snapshot 'name:pid:cores;...'"""
    v = 0.0
    for it in (top or '').split(';'):
        p = it.rsplit(':', 2)
        if len(p) == 3 and p[0].lower().startswith('msmpeng'):
            v += num(p[2], 0.0)
    return v


def analyse(label, outdir, gate_to):
    r = {'label': label, 'arm': label.split('-', 1)[-1], 'outdir': outdir, 'gate_timeout': label in gate_to,
         'notes': [], 'ok': False, 'confounded': False}
    m = re.match(r'^s(\d+)-', label)
    r['seq'] = int(m.group(1)) if m else None
    rd = find_run(outdir)
    r['run_dir'] = rd
    if not rd:
        r['notes'].append('no run dir with run.json')
        return r
    rj = read_json(os.path.join(rd, 'run.json')) or {}
    sc = read_json(os.path.join(rd, 'score3d.json'))
    if isinstance(sc, list):
        sc = sc[0] if sc else None
    if not isinstance(sc, dict):
        sc = rj.get('score3d') if isinstance(rj.get('score3d'), dict) else {}
    r['status'] = rj.get('status')
    r['excluded'] = bool(rj.get('excluded'))
    r['s3d_status'] = sc.get('s3d_status')
    for k in ('s3d_fps', 's3d_p99_ms', 's3d_over100', 's3d_low1_ms', 's3d_draws_med', 'gpu_gr_mhz_med',
              'gpu_power_w_med', 'gpu_powercap_share', 's3d_start_s', 's3d_span_s', 's3d_launch_offset_s',
              's3d_window_start_s', 's3d_frames'):
        r[k] = num(sc.get(k))
    r['ok'] = r['status'] == 'OK' and r['s3d_status'] == 'OK' and not r['excluded'] and r['s3d_fps'] is not None
    if not r['ok']:
        r['notes'].append('not OK: status %s, s3d %s%s %s' % (r['status'], r['s3d_status'], ', excluded' if r['excluded'] else '',
                                                             sc.get('s3d_void_reason') or ''))
    s0, span, off = r['s3d_start_s'], r['s3d_span_s'], r['s3d_launch_offset_s']
    if s0 is None or span is None:
        return r
    # window frames (score3d.py selection: from the frame starting at s0, until the frame-time sum >= span)
    kind, src, frames = load_frames(rd)
    r['frames_src'] = src
    persec = {}
    if frames:
        t, acc, win = 0.0, 0.0, []
        for dt, fr in frames:
            st_ = t
            t += dt
            if st_ >= s0 - 0.005 and acc < span - 1e-6:
                acc += dt
                win.append((t, dt, fr))
        iv = [dt for _, dt, _ in win]
        r['win_frames'] = len(win)
        r['win_fps'] = len(win) / sum(iv) if iv and sum(iv) > 0 else None
        if r['win_fps'] and r['s3d_fps'] and abs(r['win_fps'] - r['s3d_fps']) / r['s3d_fps'] > 0.01:
            r['notes'].append('recomputed fps %.2f differs > 1 %% from score3d %.2f' % (r['win_fps'], r['s3d_fps']))
        r['bins'] = []
        for lo, hi in BINS:
            sel = [dt * 1e3 for _, dt, fr in win if lo <= num(fr.get('draw_calls'), 0) < hi]
            r['bins'].append('%d/%.1f' % (len(sel), st.mean(sel)) if sel else '-')
        if kind == 'native':
            r['pso_n'] = sum(num(fr.get('pipeline_creations'), 0) for _, _, fr in win)
            r['pso_ms'] = sum(num(fr.get('pipeline_creation_ms'), 0) for _, _, fr in win)
        if off is not None:
            for te, dt, _ in win:
                persec.setdefault(int(te + off), []).append(dt)
    else:
        r['notes'].append('no native-frames.csv / frames.csv / perf.csv')
    # sys.csv
    sp = os.path.join(rd, 'sys.csv')
    w0 = r['s3d_window_start_s']
    if not os.path.exists(sp) or w0 is None:
        r['notes'].append('no sys.csv or no launch-clock window: clean seconds unknown (CONFOUNDED)')
        r['confounded'] = True
        return r
    srows = [x for x in read_rows(sp) if num(x.get('t_s')) is not None]
    wr = [x for x in srows if w0 <= num(x['t_s']) < w0 + span]
    lr = [x for x in srows if num(x['t_s']) < 30]

    def mean(rows, k):
        v = [num(x.get(k)) for x in rows if num(x.get(k)) is not None]
        return st.mean(v) if v else None
    r['ng'], r['eff'], r['game'] = mean(wr, 'nongame_cores'), mean(wr, 'eff_mhz'), mean(wr, 'game_cores')
    snaps = [msmp(x['top_cpu']) for x in wr if x.get('top_cpu')]
    lsnaps = [msmp(x['top_cpu']) for x in lr if x.get('top_cpu')]
    r['msmp_win'] = st.mean(snaps) if snaps else None
    r['msmp_launch_max'] = max(lsnaps) if lsnaps else None
    clean, unclean, cf, ct = 0, 0, 0, 0.0
    for x in wr:
        ng, eff = num(x.get('nongame_cores')), num(x.get('eff_mhz'))
        ok = ng is not None and ng < NG_MAX and (not CLEAN_USES_EFF or (eff is not None and eff >= EFF_MIN))
        if ok:
            clean += 1
            s = persec.get(int(num(x['t_s'])), [])
            cf += len(s)
            ct += sum(s)
        else:
            unclean += 1
    r['clean_s'], r['unclean_s'] = clean, unclean
    r['clean_fps'] = cf / ct if ct > 0 else None
    tot = clean + unclean
    if tot == 0 or unclean / tot > UNCLEAN_MAX:
        r['confounded'] = True
        r['notes'].append('CONFOUNDED: %d/%d unclean seconds (clean = %s)' % (unclean, tot, clean_rule()))
    return r


def f(v, p=2):
    return '-' if v is None else ('%.*f' % (p, v))


def pick_base(runs, base=None):
    """-> base arm, notes: --base if given, else the base arm of the scored runs (the most frequent; ties -> ship60)"""
    seen = [r['arm'] for r in runs if r['seq'] is not None and r['arm'] in BASES]
    present = sorted(set(seen), key=BASES.index)
    notes = []
    if not base:
        base = max(present, key=lambda a: (seen.count(a), -BASES.index(a))) if present else BASES[0]
    if len(present) > 1:
        notes.append('MIXED BASE ARMS in the scored runs (%s): only pairs with %s are valid' % (' '.join(present), base))
    elif present and present[0] != base:
        notes.append('the scored runs use %s, not the base %s: no pair is valid' % (present[0], base))
    return base, notes


def report(runs, gate_to, base=None):
    base, bnotes = pick_base(runs, base)
    pair_arms = {base, TEST}
    if base == 'nat60':
        bn = ('note: nat60 skips the ~13 % missing draws that n4bp60 renders, so it is the lighter GPU load (M12 p03: GPU ~11 W'
              ' vs ~25 W, CPU clock 2875 vs ~2230 MHz on quiet runs); a gap here is renderer cost + the shared-cooling clock,'
              ' not host noise')
    else:
        bn = ('note: base ship60 (xenos, devfinal2-bin, perf.csv frames) renders every draw like n4bp60 (M12 p03: GPU ~25 W'
              ' both, CPU clock ~2250 vs ~2230 MHz), so this is the fair renderer comparison; the window had n4bp60 +5.5 %')
    L = ['# S5 natcmp report (cmp_post.py): n4bp60 vs %s' % base, '',
         'clean second = %s; CONFOUNDED > %d %% unclean; verdict threshold +-%g %%, >= %d valid pairs' % (
             clean_rule(), int(UNCLEAN_MAX * 100), THR, MIN_PAIRS), bn] + ['note: %s' % x for x in bnotes] + [
         'gate timeouts (excluded): %s' % (' '.join(gate_to) or 'none'), '', '## Runs', '',
         'label | ok | fps (recalc) | p99 ms | >100 | 1%low ms | draws | gpu MHz/W/pcap | nongame | eff MHz | game | MsMpEng win/launch-max | clean s | clean fps | PSO n/ms | frames | flags | run dir']
    for r in runs:
        fl = ' '.join(x for x in ('CONFOUNDED' if r['confounded'] else '', 'GATE-TIMEOUT' if r['gate_timeout'] else '') if x)
        L.append('%s | %s | %s (%s) | %s | %s | %s | %s | %s/%s/%s | %s | %s | %s | %s/%s | %s/%s | %s | %s/%s | %s | %s | %s' % (
            r['label'], 'OK' if r['ok'] else 'NO', f(r.get('s3d_fps')), f(r.get('win_fps')), f(r.get('s3d_p99_ms'), 1),
            f(r.get('s3d_over100'), 0), f(r.get('s3d_low1_ms'), 1), f(r.get('s3d_draws_med'), 0), f(r.get('gpu_gr_mhz_med'), 0),
            f(r.get('gpu_power_w_med'), 0), f(r.get('gpu_powercap_share')), f(r.get('ng')), f(r.get('eff'), 0), f(r.get('game')),
            f(r.get('msmp_win')), f(r.get('msmp_launch_max')), r.get('clean_s', '-'), (r.get('clean_s', 0) or 0) + (r.get('unclean_s', 0) or 0),
            f(r.get('clean_fps')), f(r.get('pso_n'), 0), f(r.get('pso_ms'), 0), r.get('frames_src') or '-', fl or '-', r.get('run_dir') or '?'))
        if r.get('bins'):
            L.append('    draw bins n/mean ms %s: %s' % (' '.join('%d-%s' % (lo, hi if hi < 10 ** 9 else 'inf') for lo, hi in BINS), ' '.join(r['bins'])))
        for n in r['notes']:
            L.append('    note: %s' % n)
    # pairs
    by = {r['seq']: r for r in runs if r['seq'] is not None}
    npairs = (max(by) + 1) // 2 if by else 0
    L += ['', '## Pairs', '', 'pair | %s | %s | fps diff %% | p99 diff ms | >100 diff | clean fps diff %% | valid' % (base, TEST)]
    diffs, valid = [], 0
    for k in range(1, npairs + 1):
        a, b = by.get(2 * k - 1), by.get(2 * k)
        pr = {x['arm']: x for x in (a, b) if x}
        why = []
        if set(pr) != pair_arms or not a or not b:
            why.append('missing or not one %s + one %s' % (base, TEST))
        else:
            for x in (a, b):
                if not x['ok']:
                    why.append('%s not OK' % x['label'])
                if x['confounded']:
                    why.append('%s CONFOUNDED' % x['label'])
                if x['gate_timeout']:
                    why.append('%s GATE-TIMEOUT' % x['label'])
        n, q = pr.get(base), pr.get(TEST)
        d = 100.0 * (q['s3d_fps'] - n['s3d_fps']) / n['s3d_fps'] if n and q and n.get('s3d_fps') and q.get('s3d_fps') is not None else None
        cd = 100.0 * (q['clean_fps'] - n['clean_fps']) / n['clean_fps'] if n and q and n.get('clean_fps') and q.get('clean_fps') is not None else None
        p99 = q['s3d_p99_ms'] - n['s3d_p99_ms'] if n and q and None not in (n.get('s3d_p99_ms'), q.get('s3d_p99_ms')) else None
        o100 = q['s3d_over100'] - n['s3d_over100'] if n and q and None not in (n.get('s3d_over100'), q.get('s3d_over100')) else None
        ok = not why and d is not None
        if ok:
            valid += 1
            diffs.append(d)
        L.append('%d | %s | %s | %s | %s | %s | %s | %s' % (k, n['label'] if n else '-', q['label'] if q else '-', f(d, 1), f(p99, 1),
                                                         f(o100, 0), f(cd, 1), 'yes' if ok else 'no (%s)' % '; '.join(why or ['no fps'])))
    if not diffs:
        v = 'INCONCLUSIVE (confounded/gate)'
    elif all(x < -THR for x in diffs):
        v = 'n4bp60 SLOWER than %s' % base
    elif all(x > THR for x in diffs):
        v = 'n4bp60 FASTER than %s' % base
    else:
        v = 'NO CLEAR DIFFERENCE (n4bp60 vs %s)' % base
    if diffs and len(diffs) < MIN_PAIRS:   # M10 S2: no directional verdict from one pair
        v = 'INCONCLUSIVE (only %d valid pair; indicative: %s)' % (len(diffs), v)
    # info: clean-seconds view
    L += ['', '## Clean-seconds view (info; scored OK runs with >= %d clean s)' % MIN_CLEAN, '']
    cm = {}
    for arm in ARMS:
        cv = [r['clean_fps'] for r in runs if r['seq'] is not None and r['arm'] == arm and r['ok'] and r.get('clean_fps') and (r.get('clean_s') or 0) >= MIN_CLEAN]
        if not cv and not any(r['arm'] == arm for r in runs):
            continue
        cm[arm] = st.median(cv) if cv else None
        L.append('%s: %d runs, median clean fps %s' % (arm, len(cv), f(cm[arm])))
    if cm.get(base) and cm.get(TEST):
        L.append('clean-seconds diff %s vs %s: %+.1f %%' % (TEST, base, 100.0 * (cm[TEST] - cm[base]) / cm[base]))
    res = 'RESULT: %s; valid pairs %d/%d; median fps diff %s%% (range %s); base %s' % (
        v, valid, npairs, ('%+.1f' % st.median(diffs)) if diffs else '-',
        ('%+.1f..%+.1f%%' % (min(diffs), max(diffs))) if diffs else '-', base)
    L += ['', res]
    return '\n'.join(L) + '\n', res


# ---------------- self-test ----------------
def mk_run(root, name, fps, ng=2.0, eff=2700.0, status='OK', unclean_s=0, perf=False):
    """synthetic run-matrix out dir: 100 s pre-3D at 30 fps (800 draws), 120 s window at fps (2500 draws), 10 s tail.
    perf=True writes a xenos perf.csv (frame_time_us) instead of native-frames.csv."""
    od = os.path.join(root, name)
    rd = os.path.join(od, 'runs', '1200-' + name)
    os.makedirs(rd)
    off, s0, span = 5.0, 100.0, 120.0
    fr, t = [], 0.0
    for dt, n, dr in ((1 / 30, 3000, 800), (1 / fps, int(round(span * fps)), 2500), (1 / 30, 300, 2500)):
        for _ in range(n):
            fr.append((dt, dr))
    with open(os.path.join(rd, 'perf.csv' if perf else 'native-frames.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        if perf:
            w.writerow(['frame', 'frame_time_us', 'draw_calls'])
            for i, (dt, dr) in enumerate(fr):
                w.writerow([i, '%.1f' % (dt * 1e6), dr])
        else:
            w.writerow(['frame', 'interval_ms', 'draw_calls', 'pipeline_creations', 'pipeline_creation_ms'])
            for i, (dt, dr) in enumerate(fr):
                w.writerow([i, '%.6f' % (dt * 1e3), dr, 1 if i % 1000 == 0 else 0, '0.5' if i % 1000 == 0 else '0'])
    # score3d values as score3d.py would compute them on these frames
    t, acc, n = 0.0, 0.0, 0
    for dt, _ in fr:
        st_ = t
        t += dt
        if st_ >= s0 - 0.005 and acc < span - 1e-6:
            acc += dt
            n += 1
    sc = {'s3d_status': 'OK', 's3d_fps': round(n / acc, 3), 's3d_p99_ms': round(1e3 / fps, 2), 's3d_over100': 0,
          's3d_low1_ms': round(1e3 / fps, 2), 's3d_draws_med': 2500, 's3d_start_s': s0, 's3d_span_s': round(acc, 3),
          's3d_launch_offset_s': off, 's3d_window_start_s': s0 + off, 's3d_frames': n, 'gpu_gr_mhz_med': 1800,
          'gpu_power_w_med': 120, 'gpu_powercap_share': 0}
    with open(os.path.join(rd, 'score3d.json'), 'w') as fh:
        json.dump(sc, fh)
    with open(os.path.join(rd, 'run.json'), 'w') as fh:
        json.dump({'status': status, 'excluded': False, 'flags_excluding': '', 'score3d': sc}, fh)
    with open(os.path.join(rd, 'sys.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['t_s', 'eff_mhz', 'nongame_cores', 'game_cores', 'top_cpu'])
        for s in range(0, 240):
            bad = s0 + off + 10 <= s < s0 + off + 10 + unclean_s
            top = 'MsMpEng.exe:4242:0.50;chrome.exe:77:0.30' if s % 5 == 0 else ''
            w.writerow([s, eff, 5.0 if bad else ng, 2.0, top])
    return od


def selftest(out):
    root = tempfile.mkdtemp(prefix='cmp_post_selftest_')
    L, bad = [], 0

    def check(name, cond, extra=''):
        nonlocal bad
        L.append('%s %s %s' % ('ok  ' if cond else 'FAIL', name, extra))
        bad += 0 if cond else 1

    try:
        cases = {
            'A': ({'nat60': dict(fps=50), 'n4bp60': dict(fps=40)}, [], 'n4bp60 SLOWER'),
            'B': ({'nat60': dict(fps=50), 'n4bp60': dict(fps=40, ng=6.0)}, [], 'INCONCLUSIVE'),
            'C': ({'nat60': dict(fps=50), 'n4bp60': dict(fps=40)}, ['s2-n4bp60', 's3-n4bp60'], 'INCONCLUSIVE'),
            'D': ({'nat60': dict(fps=50, unclean_s=12), 'n4bp60': dict(fps=50)}, [], 'NO CLEAR DIFFERENCE'),
            'E': ({'nat60': dict(fps=40), 'n4bp60': dict(fps=50)}, [], 'n4bp60 FASTER'),
        }
        for cn, (spec, gto, want) in cases.items():
            cr = os.path.join(root, cn)
            labels = ['prime-nat60', 'prime-n4bp60', 's1-nat60', 's2-n4bp60', 's3-n4bp60', 's4-nat60']
            runs = [analyse(lb, mk_run(cr, '%02d-%s' % (i + 1, lb), **spec[lb.split('-', 1)[1]]), gto) for i, lb in enumerate(labels)]
            txt, res = report(runs, gto)
            check('case %s verdict' % cn, res.startswith('RESULT: ' + want), res)
            if cn == 'A':
                s1 = runs[2]
                check('A fps recomputed', s1.get('win_fps') is not None and abs(s1['win_fps'] - 50) < 0.5, f(s1.get('win_fps')))
                check('A MsMpEng window mean 0.50', s1.get('msmp_win') is not None and abs(s1['msmp_win'] - 0.5) < 1e-9, f(s1.get('msmp_win')))
                check('A MsMpEng launch max 0.50', s1.get('msmp_launch_max') == 0.5, f(s1.get('msmp_launch_max')))
                check('A clean seconds 120', s1.get('clean_s') == 120 and s1.get('unclean_s') == 0, '%s/%s' % (s1.get('clean_s'), s1.get('unclean_s')))
                check('A clean fps ~50', s1.get('clean_fps') is not None and abs(s1['clean_fps'] - 50) < 1.0, f(s1.get('clean_fps')))
                check('A median diff -20', '-20.0%' in res, res)
                check('A PSO counted', (s1.get('pso_n') or 0) >= 5, f(s1.get('pso_n'), 0))
                check('A report has RESULT line', txt.rstrip().endswith(res))
            if cn == 'B':
                check('B n4bp CONFOUNDED', runs[3]['confounded'] and not runs[2]['confounded'])
            if cn == 'D':
                s1 = runs[2]
                check('D 12 unclean s not CONFOUNDED', s1.get('unclean_s') == 12 and not s1['confounded'], '%s/%s' % (s1.get('clean_s'), s1.get('unclean_s')))
                check('D clean fps ~50', s1.get('clean_fps') is not None and abs(s1['clean_fps'] - 50) < 1.0, f(s1.get('clean_fps')))
        # a not-OK run and a missing run dir make the pair invalid
        cr = os.path.join(root, 'F')
        runs = [analyse('s1-nat60', mk_run(cr, '01-s1', fps=50, status='FAILED'), []),
                analyse('s2-n4bp60', mk_run(cr, '02-s2', fps=40), []),
                analyse('s3-n4bp60', os.path.join(cr, 'missing'), []), analyse('s4-nat60', mk_run(cr, '04-s4', fps=50), [])]
        txt, res = report(runs, [])
        check('F not-OK + missing -> INCONCLUSIVE 0/2', res.startswith('RESULT: INCONCLUSIVE') and 'valid pairs 0/2' in res, res)
        # M10 S2: one valid pair (the other confounded) gives no directional verdict
        cr = os.path.join(root, 'G')
        runs = [analyse('s1-nat60', mk_run(cr, '01-s1', fps=50), []), analyse('s2-n4bp60', mk_run(cr, '02-s2', fps=40), []),
                analyse('s3-n4bp60', mk_run(cr, '03-s3', fps=40, ng=6.0), []), analyse('s4-nat60', mk_run(cr, '04-s4', fps=50), [])]
        txt, res = report(runs, [])
        check('G one valid pair -> INCONCLUSIVE 1/2 (indicative SLOWER)', res.startswith('RESULT: INCONCLUSIVE (only 1 valid pair; indicative: n4bp60 SLOWER than nat60)') and 'valid pairs 1/2' in res, res)
        check('G base auto nat60', res.endswith('base nat60'), res)
        # base ship60 (xenos perf.csv frames): ship 40 vs n4bp 46 in both pairs -> FASTER
        sp = lambda fps, **k: dict(fps=fps, perf=True, **k)
        cr = os.path.join(root, 'H')
        labels = ['prime-ship60', 'prime-n4bp60', 's1-ship60', 's2-n4bp60', 's3-n4bp60', 's4-ship60']
        spec = {'ship60': sp(40), 'n4bp60': dict(fps=46)}
        runs = [analyse(lb, mk_run(cr, '%02d-%s' % (i + 1, lb), **spec[lb.split('-', 1)[1]]), []) for i, lb in enumerate(labels)]
        txt, res = report(runs, [])
        s1 = runs[2]
        check('H ship base -> n4bp60 FASTER than ship60 2/2', res.startswith('RESULT: n4bp60 FASTER than ship60') and 'valid pairs 2/2' in res and res.endswith('base ship60'), res)
        check('H perf.csv frames used', s1.get('frames_src') == 'perf.csv', str(s1.get('frames_src')))
        check('H perf fps recomputed ~40', s1.get('win_fps') is not None and abs(s1['win_fps'] - 40) < 0.5 and not any('differs' in n for n in s1['notes']), f(s1.get('win_fps')))
        check('H perf clean fps ~40', s1.get('clean_fps') is not None and abs(s1['clean_fps'] - 40) < 1.0, f(s1.get('clean_fps')))
        check('H perf PSO not counted', s1.get('pso_n') is None and (runs[3].get('pso_n') or 0) >= 5, '%s/%s' % (s1.get('pso_n'), runs[3].get('pso_n')))
        check('H median diff +15', '+15.0%' in res, res)
        check('H header + ship note', 'n4bp60 vs ship60' in txt and 'note: base ship60' in txt and 'nat60 skips' not in txt)
        check('H clean diff line', 'clean-seconds diff n4bp60 vs ship60: +15.0 %' in txt)
        check('H draw bins on perf (2000-3000 = window)', s1.get('bins') and s1['bins'][3].startswith('4800/25.0'), str(s1.get('bins')))
        # ship base, one valid pair (the other n4bp confounded) -> INCONCLUSIVE indicative
        cr = os.path.join(root, 'I')
        runs = [analyse('s1-ship60', mk_run(cr, '01-s1', **sp(40)), []), analyse('s2-n4bp60', mk_run(cr, '02-s2', fps=46), []),
                analyse('s3-n4bp60', mk_run(cr, '03-s3', fps=46, ng=6.0), []), analyse('s4-ship60', mk_run(cr, '04-s4', **sp(40)), [])]
        txt, res = report(runs, [])
        check('I ship one valid pair -> INCONCLUSIVE 1/2', res.startswith('RESULT: INCONCLUSIVE (only 1 valid pair; indicative: n4bp60 FASTER than ship60)') and 'valid pairs 1/2' in res, res)
        # mixed base arms: pair 2 = n4bp60 + nat60 under base ship60 -> invalid, flagged
        cr = os.path.join(root, 'J')
        runs = [analyse('s1-ship60', mk_run(cr, '01-s1', **sp(40)), []), analyse('s2-n4bp60', mk_run(cr, '02-s2', fps=46), []),
                analyse('s3-n4bp60', mk_run(cr, '03-s3', fps=46), []), analyse('s4-nat60', mk_run(cr, '04-s4', fps=50), [])]
        txt, res = report(runs, [])
        check('J mixed base -> flagged, 1/2 valid, base ship60', 'MIXED BASE ARMS' in txt and 'valid pairs 1/2' in res and res.endswith('base ship60'), res)
        # explicit --base nat60 with ship60 runs -> no valid pair
        txt, res = report(runs[:2], [], base='nat60')
        check('K base nat60 on ship runs -> 0/1 valid', res.startswith('RESULT: INCONCLUSIVE') and 'valid pairs 0/1' in res and 'not the base nat60' in txt, res)
        check('msmp parse', msmp('a.exe:1:1.0;MsMpEng.exe:2:0.25;msmpeng.exe:3:0.25') == 0.5)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    L.append('SELFTEST %s: %d checks, %d failed' % ('PASS' if not bad else 'FAIL', len(L), bad))
    txt = '\n'.join(L) + '\n'
    print(txt, end='')
    if out:
        with open(out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(txt)
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--run', action='append', default=[], help='LABEL=OUTDIR, in run order')
    ap.add_argument('--gate-timeout', action='append', default=[])
    ap.add_argument('--base', choices=BASES, default=None)
    ap.add_argument('--out', default=None)
    ap.add_argument('--selftest', action='store_true')
    try:
        a = ap.parse_args()
    except SystemExit:
        return 2
    if a.selftest:
        return selftest(a.out)
    if not a.out:
        print('usage: --out FILE is required')
        return 2
    runs = []
    for x in a.run:
        if '=' not in x:
            print('usage: --run LABEL=OUTDIR (got %s)' % x)
            return 2
        lb, od = x.split('=', 1)
        if not re.match(r'^(prime|s\d+)-(%s)$' % '|'.join(ARMS), lb):
            print('usage: bad label %s' % lb)
            return 2
        try:
            runs.append(analyse(lb, od, set(a.gate_timeout)))
        except (OSError, csv.Error, ValueError, KeyError) as e:
            print('error reading %s: %s' % (od, e))
            return 1
    if not runs:
        txt, res = '# S5 natcmp report (cmp_post.py)\n\nno runs\n\nRESULT: INCONCLUSIVE (no runs)\n', 'RESULT: INCONCLUSIVE (no runs)'
    else:
        txt, res = report(runs, a.gate_timeout, a.base)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(txt)
    print(txt, end='')
    return 0 if runs else 1


if __name__ == '__main__':
    sys.exit(main())

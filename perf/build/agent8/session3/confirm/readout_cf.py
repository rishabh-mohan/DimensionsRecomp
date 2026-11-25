#!/usr/bin/env python3
"""M8 confirmation-window read-out (CF1 / CF2), strictly per confirm/READOUT-PLAN.md (18F69B57).

Read-only on one run-matrix out dir; stdlib only; BelowNormal (set by readout_night on import).
Usage: python -B readout_cf.py --window CF1 [--hash-bins] [--json OUT] MATRIX_OUT_DIR > out.md

Per-run values and the bootstrap come from readout_night.py (byte copy of build/agent8/session3/readout/readout_night.py,
sha256 1A5F9BE0..., the READOUT-NIGHT code path M10 confirmed 25BF9B1C). Bootstrap: 10 000 draws, seed 1, percentiles
2.5 / 97.5, runs resampled within each arm; arm value = median of per-run values.

Fixed before the window's data was read (11:40, CF1 running):
- scored set = rounds 2-6 of scored runs (the cold run is unscored); round 1 = side note only.
- a run counts if: status OK, valid_timing, not excluded by the runner, exit 0, no WER / dump, no fatal line, STUCK-LOCK
  only in the finding-10 form (else FAIL), sys.csv 31 columns on every row, proof PASS (MANIFEST sha + staged exe/DLL shas
  when --hash-bins + bin_dir + env_set + check-defaults D9936C56 mode / absent-line check).
- void: proof FAIL -> run void; 2nd proof FAIL in an arm (any round, cold included) -> arm void; functional FAIL of a
  final-bin arm run (ship / nf) -> arm void; arm with < 4 counted scored runs -> "no verdict (n < 4)".
- M12 host-load gate (w6_env_record.py formula): non-game = sys.json window cpu_util_mean * ncpu / 100 - results.csv
  cpu_cores_mean; flag a scored run above the median of the scored runs + 1.0 core.
- gpu plateau: round 2 is on the plateau if every counted round-2 run's median gr_mhz >= 0.97 x the median of the counted
  rounds 3-6 runs' gr_mhz. If not, the rounds 3-6 table is also given (headline stays rounds 2-6).
- level reached: the timed route is the light title route (no level), so it reads "reached the 50 s window" (status OK).
"""
import argparse, csv, hashlib, json, os, statistics as st, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import readout_night as rn  # noqa: E402  (sets BelowNormal)

REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
CHECK = os.path.join(REPO, 'build', 'agent2', 'final', 'check-defaults.py')
CHECK_SHA8 = 'D9936C56'
NBOOT, SEED = 10000, 1
VKEYS = [('fps', 'fps mean'), ('p99', 'p99 ms'), ('low1_ms', '1% low ms'), ('cores', 'process cores'),
         ('median', 'median ms (info)')]
BAD = ["Recovered stale physical page protection", "Unhandled guest physical write fault", "PhysicalHeap::Protect failed",
       "is not a plain number", "C1 verify: on"]
FATAL = ['BaseHeap::Protect failed', 'REX_FATAL', 'Minidump written to']
S0_ABSENT = ["Final defaults", "GPU wait back-off:", "C1 keep-watch: on", "TimerQueue: precise wait",
             "Host timer resolution set to"]
MISS_KEYS = ['shader not present in AOT cache', 'missing from AOT index', 'unrecognized vertex shader resource',
             'unrecognized pixel shader resource']
MC_ABSENT = 'miss cache ON (build default) line: 0 (want 1)'
F10 = ('84959EDC', ('83FAF188', '83FAF200'), '82A2A270')
M_DEVFINAL = 'F9C2BE722E5B3517D1CA7AB1A0F79BA9B7AADF59D4EF0E43384CE307C7084621'
M_DEVOFF4B = 'DE11A914079D7DF7080CAA86B05DAE151CEFA017FDE15713CB85FA79F86339FA'
M_NATFINAL = 'D7C7B7060519A4950EE794FB5FF51D1E1BFB62394DBBF132D1AA99FFE7A6EE79'
M_NATIVE4B = 'B63769FE46CC04592F2BEDAF04A51C362000325D3291BC4D7489369C2160B817'
WC = {('fps', 7.7, 6.3, 8.7), ('p99', -14.8, -17.1, -14.0), ('low1_ms', -17.0, -18.0, -14.9), ('cores', -38.7, -40.3, -35.2)}

WIN = {
    'CF1': dict(ref='s0', final=['ship'],
                pairs=[('ship', 's0', 'diff'), ('win3', 's0', 'diff'), ('ship', 'win3', 'equiv')],
                margins={'fps': 2, 'p99': 5, 'low1_ms': 5, 'cores': 5, 'median': 3},
                proof={'ship': dict(manifest=M_DEVFINAL, bin='devfinal-bin', mode='xenos', env_no=['LEGO_GPU_WAIT_'], env_eq={}, env_key=[]),
                       's0': dict(manifest=M_DEVOFF4B, bin='devoff4b-bin', mode='absent', env_no=['LEGO_GPU_WAIT_'], env_eq={}, env_key=[]),
                       'win3': dict(manifest=M_DEVOFF4B, bin='devoff4b-bin', mode='legacy', env_no=[],
                                    env_eq={'LEGO_GPU_WAIT_BACKOFF_US': '500', 'LEGO_GPU_WAIT_SPIN_US': '30'}, env_key=[])}),
    'CF2': dict(ref='mc', final=['nf'], pairs=[('nf', 'mc', 'equiv')],
                margins={'fps': 3, 'p99': 5, 'low1_ms': 5, 'cores': 5, 'median': 3},
                proof={'nf': dict(manifest=M_NATFINAL, bin='nativefinal-bin', mode='native-old',
                                  env_no=['LEGO_NATIVE_SHADER_MISS_CACHE'], env_eq={}, env_key=['LEGO_NATIVE_FRAME_METRICS']),
                       'mc': dict(manifest=M_NATIVE4B, bin='native4b-bin', mode='bad', env_no=[],
                                  env_eq={'LEGO_NATIVE_SHADER_MISS_CACHE': '1'}, env_key=['LEGO_NATIVE_FRAME_METRICS'])}),
}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def read_lines(p):
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8', errors='replace') as f:
        return [rn_msg(l.rstrip('\r\n')) for l in f]


def rn_msg(line):
    # same message split as check-defaults.msg: "[ts] [lvl] [cat] [tid] message" -> message
    parts = line.split('] ', 4)
    return parts[4] if len(parts) == 5 and line.startswith('[') else line


def proof(rd, j, spec, hash_bins):
    """-> (ok, [fail texts], [notes], misses)"""
    fails, notes = [], []
    mp = os.path.join(rd, 'MANIFEST.txt')
    if not os.path.exists(mp):
        fails.append('MANIFEST.txt missing in run dir')
    else:
        ms = sha(mp)
        (notes if ms == spec['manifest'] else fails).append('MANIFEST %s (want %s)' % (ms[:16], spec['manifest'][:16]))
        if hash_bins:
            with open(mp, encoding='utf-8', errors='replace') as f:
                for ln in f:
                    p = ln.rstrip('\r\n').split('\t')
                    if len(p) >= 4 and not ln.startswith('#') and p[0].lower().endswith(('.exe', '.dll')):
                        fp = os.path.join(rd, p[0])
                        if not os.path.exists(fp):
                            fails.append('%s missing' % p[0])
                            continue
                        fs = sha(fp)
                        (notes if fs == p[3].upper() else fails).append('%s %s (MANIFEST %s)' % (p[0], fs[:16], p[3][:16]))
    bd = os.path.basename((j.get('bin_dir') or '').rstrip('\\/'))
    (notes if bd == spec['bin'] else fails).append('bin_dir %s (want %s)' % (bd, spec['bin']))
    env = j.get('env_set') or {}
    if not isinstance(env, dict):
        env = {}
    for pre in spec['env_no']:
        bad = [k for k in env if k.startswith(pre)]
        (fails if bad else notes).append('env_set %s* keys: %s' % (pre, bad or 'none'))
    for k, v in spec['env_eq'].items():
        (notes if str(env.get(k)) == v else fails).append('env_set %s=%s (want %s)' % (k, env.get(k), v))
    for k in spec['env_key']:
        (notes if k in env else fails).append('env_set has %s: %s' % (k, k in env))
    gl = os.path.join(rd, 'game.log')
    lines = read_lines(gl)
    misses = None
    if lines is None:
        fails.append('game.log missing')
        return False, fails, notes, misses
    misses = sum(1 for l in lines for k in MISS_KEYS if k in l)
    if spec['mode'] in ('xenos', 'legacy', 'native-old'):
        cp = subprocess.run([sys.executable, '-B', CHECK, gl, '--mode', spec['mode']], capture_output=True, text=True)
        cf = [l.strip()[5:] for l in cp.stdout.splitlines() if l.startswith('  FAIL ')]
        if cp.returncode not in (0, 1):
            fails.append('check-defaults rc %d' % cp.returncode)
        if spec['mode'] == 'native-old' and cf and all(MC_ABSENT in x for x in cf):
            if misses == 0:
                notes.append('check-defaults native-old: only the miss-cache ON line is absent, 0 shader misses (S1: listed, not void)')
                cf = []
            else:
                cf = ['miss-cache ON line absent with %d shader misses' % misses]
        fails += ['check-defaults --mode %s: %s' % (spec['mode'], x) for x in cf]
        if not cf:
            notes.append('check-defaults --mode %s PASS' % spec['mode'])
    else:
        if spec['mode'] == 'absent':
            for s in S0_ABSENT:
                c = sum(1 for l in lines if s in l)
                (fails if c else notes).append("'%s' lines: %d (want 0)" % (s, c))
        for b in BAD:
            c = sum(1 for l in lines if b in l)
            (fails if c else notes).append("bad string '%s': %d" % (b, c))
    return not fails, fails, notes, misses


def functional(rd, j, r):
    """-> (ok, [fail texts], [warn texts])"""
    fails, warns = [], []
    if r['status'] != 'OK':
        fails.append('status %s' % r['status'])
    if j.get('exit_code') != 0:
        fails.append('exit %s' % j.get('exit_code'))
    if j.get('werfault_seen'):
        fails.append('WER seen')
    if r['dumps']:
        fails.append('%d dump/artifact entries' % r['dumps'])
    lines = read_lines(os.path.join(rd, 'game.log')) or []
    for s in FATAL:
        c = sum(1 for l in lines if s in l)
        if c:
            fails.append("'%s' x%d" % (s, c))
    stuck = [l for l in lines if 'STUCK-LOCK' in l or 'still not acquired after' in l]
    if stuck:
        txt = '\n'.join(stuck)
        f10 = F10[0] in txt and any(x in txt for x in F10[1]) and F10[2] in txt
        if f10 and not fails:
            warns.append('STUCK-LOCK x%d: WARN, finding 10 (CS %s, owner lr %s, waiter %s)' % (len(stuck), F10[0], '/'.join(F10[1]), F10[2]))
        else:
            fails.append('STUCK-LOCK x%d not in the finding-10 form' % len(stuck))
    return not fails, fails, warns


def sys31(rd):
    p = os.path.join(rd, 'sys.csv')
    if not os.path.exists(p):
        return False, 'sys.csv missing'
    with open(p, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))
    if not rows:
        return False, 'sys.csv empty'
    bad = [i for i, x in enumerate(rows) if len(x) != 31]
    return (not bad), '%d rows, header %d cols, %d rows != 31' % (len(rows) - 1, len(rows[0]), len(bad))


def gpu_med(rd):
    p = os.path.join(rd, 'gpu.csv')
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8-sig', newline='') as f:
        v = [rn.fnum(x.get('gr_mhz')) for x in csv.DictReader(f)]
    v = [x for x in v if x is not None]
    return st.median(v) if v else None


def render_ms(rd, r):
    """CF2: the native threads.csv has no named render thread (W8a: Main XThread, XThread*, TimerQueue, 0xc0550001),
    so give the 3 busiest threads as ms of CPU per frame = busy% x window / frames, with their names."""
    p = os.path.join(rd, 'threads.csv')
    if not os.path.exists(p) or not r.get('frames') or not r.get('window_s'):
        return None
    th = []
    with open(p, encoding='utf-8-sig', newline='') as f:
        for x in csv.DictReader(f):
            b = rn.fnum(x.get('busy_pct'))
            if b is not None:
                th.append((b, (x.get('name') or '?').split(' (')[0]))
    th.sort(reverse=True)
    return [(n, b / 100.0 * r['window_s'] * 1000.0 / r['frames']) for b, n in th[:3]]


def contrast(by, A, B, kind, margins):
    rows = []
    for key, lab in VKEYS:
        ma, mb, d, lo, hi = rn.boot_diff(by[A], by[B], key, n=NBOOT, seed=SEED)
        pr = rn.paired(by[A], by[B], key)
        pct, plo, phi = d / mb * 100, lo / mb * 100, hi / mb * 100
        excl = plo > 0 or phi < 0
        if kind == 'equiv':
            m = margins[key]
            claim = 'equal' if (plo >= -m and phi <= m) else ('different' if excl else 'not shown different')
        else:
            claim = 'overlap (not shown different)' if not excl else ('%s higher' % A if plo > 0 else '%s lower' % A)
        rows.append(dict(A=A, B=B, kind=kind, key=key, label=lab, a_med=ma, b_med=mb, pct=pct, lo=plo, hi=phi, excl=excl,
                         claim=claim, paired=pr, margin=margins[key] if kind == 'equiv' else None))
    return rows


def table(name, runs, cfg, keep):
    arms = list(cfg['proof'])
    by = {a: [r for r in runs if keep(r) and r['arm'] == a] for a in arms}
    out = ['### ' + name, '', 'n per arm: ' + ', '.join('%s %d' % (a, len(by[a])) for a in arms), '']
    out.append('| arm | n | fps mean (median of runs) | p99 ms | 1% low ms | cores | median ms | GPU MHz | eff MHz |')
    out.append('|---|---|---|---|---|---|---|---|---|')
    for a in arms:
        v = by[a]
        if not v:
            out.append('| %s | 0 | | | | | | | |' % a)
            continue
        md = lambda k: st.median([r[k] for r in v if r.get(k) is not None]) if any(r.get(k) is not None for r in v) else None
        out.append('| %s | %d | %.1f | %.3f | %.3f | %.2f | %.3f | %s | %s |' % (
            a, len(v), md('fps'), md('p99'), md('low1_ms'), md('cores'), md('median'), rn.fmt(md('gpu'), 0), rn.fmt(md('eff'), 0)))
    out += ['', '| pair | metric | A | B | A vs B % | 95% CI % | margin | claim | paired rounds % [t-CI] (A<B) |', '|---|---|---|---|---|---|---|---|---|']
    res = []
    for A, B, kind in cfg['pairs']:
        if cfg.get('void', {}).get(A) or cfg.get('void', {}).get(B):
            out.append('| %s vs %s | all | | | | | | no verdict (arm void) | |' % (A, B))
            continue
        if len(by[A]) < 4 or len(by[B]) < 4:
            out.append('| %s vs %s | all | | | | | | no verdict (n < 4) | |' % (A, B))
            continue
        for c in contrast(by, A, B, kind, cfg['margins']):
            res.append(c)
            pr = c['paired']
            prs = '-' if pr is None else '%+.1f [%+.1f, %+.1f] (%d/%d)' % (pr[1], pr[2], pr[3], pr[4], pr[0])
            out.append('| %s vs %s | %s | %.3f | %.3f | %+.1f | [%+.1f, %+.1f] | %s | %s | %s |' % (
                A, B, c['label'], c['a_med'], c['b_med'], c['pct'], c['lo'], c['hi'],
                '±%g' % c['margin'] if c['margin'] is not None else '-', c['claim'], prs))
    return out + [''], res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--window', required=True, choices=list(WIN))
    ap.add_argument('--hash-bins', action='store_true')
    ap.add_argument('--ncpu', type=int, default=os.cpu_count())
    ap.add_argument('--json')
    ap.add_argument('outdir')
    a = ap.parse_args()
    cfg = WIN[a.window]
    cs = sha(CHECK)
    if not cs.startswith(CHECK_SHA8):
        sys.exit('check-defaults.py sha %s != %s' % (cs[:8], CHECK_SHA8))
    runs = rn.load([a.outdir], 1)
    with open(os.path.join(a.outdir, 'results.csv'), encoding='utf-8-sig', newline='') as f:
        res_rows = {int(x['seq']): x for x in csv.DictReader(f)}
    arms = list(cfg['proof'])
    for r in runs:
        rd = res_rows[r['seq']]['run_dir']
        j = rn.jload(os.path.join(rd, 'run.json'))
        fj = j['frames']
        r['frames'], r['window_s'] = fj.get('frames'), fj.get('window_s')
        r['base_ok'] = r['scored'] and r['status'] == 'OK' and r['valid'] and not r['excluded']
        if r['arm'] in cfg['proof']:
            r['proof_ok'], r['proof_fail'], r['proof_notes'], r['misses'] = proof(rd, j, cfg['proof'][r['arm']], a.hash_bins)
        else:
            r['proof_ok'], r['proof_fail'], r['proof_notes'], r['misses'] = False, ['arm not in plan'], [], None
        r['func_ok'], r['func_fail'], r['func_warn'] = functional(rd, j, r)
        r['sys31'], r['sys31_txt'] = sys31(rd)
        r['gpu'] = gpu_med(rd)
        r['render_ms'] = render_ms(rd, r)
        w = (rn.jload(os.path.join(rd, 'sys.json')).get('window') or {}) if os.path.exists(os.path.join(rd, 'sys.json')) else {}
        util, cc = rn.fnum(w.get('cpu_util_mean')), rn.fnum(res_rows[r['seq']].get('cpu_cores_mean'))
        r['nongame'] = round(util * a.ncpu / 100 - cc, 2) if util is not None and cc is not None else None
        r['nongame_sys'] = w.get('nongame_cores_mean')
        r['ac'] = (w.get('ac') or {}).get('first') if isinstance(w.get('ac'), dict) else w.get('ac')
        ss = j.get('sys_sampler') or {}
        r['stop_line'] = ss.get('stop_line')
        r['sample_ms_max'] = (rn.jload(os.path.join(rd, 'sys.json')).get('run') or {}).get('sample_ms_max') if os.path.exists(os.path.join(rd, 'sys.json')) else None
    # void logic
    void_arm, notes = {}, []
    for arm in arms:
        pf = [r for r in runs if r['arm'] == arm and not r['proof_ok']]
        if len(pf) >= 2:
            void_arm[arm] = 'proof FAIL x%d (%s)' % (len(pf), ', '.join(r['name'] for r in pf))
        if arm in cfg['final']:
            ff = [r for r in runs if r['arm'] == arm and not r['func_ok']]
            if ff:
                void_arm[arm] = (void_arm.get(arm, '') + '; ' if arm in void_arm else '') + 'final-bin functional FAIL (%s)' % ', '.join(r['name'] for r in ff)
    cfg['void'] = void_arm
    for r in runs:
        why = []
        if not r['base_ok']:
            why.append('runner: scored=%s status=%s valid=%s excluded=%s %s' % (r['scored'], r['status'], r['valid'], r['excluded'], r['flags_ex']))
        if not r['func_ok']:
            why.append('functional: ' + '; '.join(r['func_fail']))
        if not r['proof_ok']:
            why.append('proof: ' + '; '.join(r['proof_fail']))
        if not r['sys31']:
            why.append('sys.csv: ' + r['sys31_txt'])
        if r['arm'] in void_arm:
            why.append('arm void')
        r['why'] = why
        r['count'] = not why
    # M12 host-load gate over scored runs
    ng = [r['nongame'] for r in runs if r['scored'] and r['nongame'] is not None]
    ng_med = st.median(ng) if ng else None
    for r in runs:
        r['m12'] = bool(r['scored'] and ng_med is not None and r['nongame'] is not None and r['nongame'] > ng_med + 1.0)
    # gpu plateau
    g2 = [r['gpu'] for r in runs if r['count'] and r['round'] == 2 and r['gpu']]
    g36 = [r['gpu'] for r in runs if r['count'] and 3 <= r['round'] <= 6 and r['gpu']]
    plateau = bool(g2 and g36 and min(g2) >= 0.97 * st.median(g36))

    P = print
    P('## %s read-out tables (readout_cf.py; bootstrap %d draws, seed %d; check-defaults %s)' % (a.window, NBOOT, SEED, cs[:8]))
    P('out dir: `%s`; runs %d; ncpu %d' % (a.outdir, len(runs), a.ncpu))
    P()
    P('> Note (M10 C2): a raw "equal" claim printed below for a tail metric (p99, 1% low) is quoted as '
      '"not shown different" (n.s.d.) in the READOUT; tails are never claimed equal. Non-tail metrics (fps, cores) '
      'may be called equal only by the CI-within-margin rule.')
    P()
    P('### Runs')
    P()
    P('| run | rnd | pos | arm | counts | proof | func | sys.csv | runner flags (info / excl.) | GPU MHz | eff MHz | non-game (M12 / sys) | fps | p99 | 1% low ms | cores | median | STUCK | misses | stop_line |')
    P('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for r in runs:
        P('| %s | %d | %d | %s | %s | %s | %s | %s | %s / %s | %s | %s | %s%s / %s | %.1f | %.3f | %.3f | %s | %.3f | %d | %s | %s |' % (
            r['name'], r['round'], r['slot'], r['arm'], 'Y' if r['count'] else '-', 'PASS' if r['proof_ok'] else 'FAIL',
            'PASS' if r['func_ok'] else 'FAIL', '31' if r['sys31'] else 'BAD', r['flags_info'] or '-', r['flags_ex'] or '-',
            rn.fmt(r['gpu'], 0), rn.fmt(r['eff'], 0), rn.fmt(r['nongame'], 2), ' FLAG' if r['m12'] else '', rn.fmt(r['nongame_sys'], 2),
            r['fps'], r['p99'], r['low1_ms'], rn.fmt(r['cores'], 2), r['median'], r['stuck'],
            '-' if r['misses'] is None else r['misses'], 'set' if r['stop_line'] else 'null'))
    P()
    P('### Void and exclusion list')
    P()
    for arm in arms:
        P('- arm %s: %s' % (arm, 'VOID: ' + void_arm[arm] if arm in void_arm else 'not void'))
    for r in runs:
        if r['why']:
            P('- %s (round %d, %s): %s' % (r['name'], r['round'], r['arm'], ' | '.join(r['why'])))
        for wtxt in r['func_warn']:
            P('- %s: %s' % (r['name'], wtxt))
        for n in r['proof_notes']:
            if 'S1' in n:
                P('- %s: %s' % (r['name'], n))
    P()
    P('M12 host-load gate: scored non-game median %s cores, threshold %s; flagged: %s' % (
        rn.fmt(ng_med, 2), rn.fmt(ng_med + 1.0 if ng_med is not None else None, 2),
        ', '.join('%s %.2f' % (r['name'], r['nongame']) for r in runs if r['m12']) or 'none'))
    P()
    P('GPU plateau: round-2 counted runs %s MHz; rounds 3-6 median %s MHz; round 2 on plateau (>= 97 %%): %s' % (
        ', '.join('%.0f' % x for x in g2) or '-', rn.fmt(st.median(g36) if g36 else None, 0), 'yes' if plateau else 'NO'))
    byr = {}
    for r in runs:
        if r['gpu'] and r['scored']:
            byr.setdefault(r['round'], []).append(r['gpu'])
    P('GPU MHz by round (median of scored runs): ' + ', '.join('r%d %.0f' % (k, st.median(v)) for k, v in sorted(byr.items())))
    sm = [r['sample_ms_max'] for r in runs if r['sample_ms_max'] is not None]
    P('sys sampler: stop_line set on %d/%d runs; sample_ms_max max %s' % (sum(1 for r in runs if r['stop_line']), len(runs), rn.fmt(max(sm) if sm else None, 0)))
    sc = lambda r: r['count'] and 2 <= r['round'] <= 6
    if a.window == 'CF2':
        P('Thread CPU ms per frame (3 busiest threads, busy% x window / frames; no thread is named render in native threads.csv):')
        P()
        for arm in arms:
            v = [r for r in runs if sc(r) and r['arm'] == arm and r['render_ms']]
            names = []
            for r in v:
                for n, _ in r['render_ms']:
                    if n not in names:
                        names.append(n)
            P('- %s (headline runs, median): ' % arm + ', '.join('%s %.3f' % (n, st.median(
                [m for r in v for nn, m in r['render_ms'] if nn == n])) for n in names[:4]))
    P()
    variants = [('Headline: rounds 2-6, counted runs, M12-flagged runs kept', sc),
                ('Rounds 2-6 without M12-flagged runs', lambda r: sc(r) and not r['m12']),
                ('Side note: rounds 1-6 (with round 1; never decides)', lambda r: r['count'] and 1 <= r['round'] <= 6),
                ('Rounds 3-6 (%s)' % ('given because round 2 is not on the plateau' if not plateau else 'info only; round 2 is on the plateau'),
                 lambda r: r['count'] and 3 <= r['round'] <= 6)]
    allres = {}
    for name, keep in variants:
        if 'without M12' in name and not any(r['m12'] for r in runs):
            P('### ' + name + '\n\nno M12-flagged run: same as the headline.\n')
            continue
        lines, res = table(name, runs, cfg, keep)
        P('\n'.join(lines))
        allres[name] = res
    head = allres[variants[0][0]]
    # order (N1): position split, headline set
    P('### Order (N1): position within the round, headline set')
    P()
    P('| arm | positions (1st/2nd/3rd) | metric | median at 1st | median at later | n 1st / later |')
    P('|---|---|---|---|---|---|')
    for arm in arms:
        v = [r for r in runs if sc(r) and r['arm'] == arm]
        pos = '/'.join(str(sum(1 for r in v if r['slot'] == k)) for k in (1, 2, 3))
        for key, lab in VKEYS[:4]:
            f1 = [r[key] for r in v if r['slot'] == 1 and r[key] is not None]
            fl = [r[key] for r in v if r['slot'] > 1 and r[key] is not None]
            P('| %s | %s | %s | %s | %s | %d / %d |' % (arm, pos, lab, rn.fmt(st.median(f1) if f1 else None, 3),
                                                     rn.fmt(st.median(fl) if fl else None, 3), len(f1), len(fl)))
    P()
    # claims
    P('### Claims (S1) and WC comparison (S2), headline set')
    P()
    for c in head:
        if c['key'] != 'median':
            P('- %s vs %s, %s: %+.1f %% [%+.1f, %+.1f] -> %s' % (c['A'], c['B'], c['label'], c['pct'], c['lo'], c['hi'], c['claim']))
    if a.window == 'CF1':
        eq = [c for c in head if c['A'] == 'ship' and c['B'] == 'win3' and c['key'] != 'median']
        ds = {c['key']: c for c in head if c['A'] == 'ship' and c['B'] == 's0'}
        ok1 = len(eq) == 4 and all(c['claim'] in ('equal', 'not shown different') for c in eq)
        ok2 = 'fps' in ds and 'cores' in ds and ds['fps']['lo'] > 0 and ds['cores']['hi'] < 0
        P('- CF1 overall: ship vs win3 equal / not shown different on all four: %s; ship vs s0 fps CI > 0 and cores CI < 0: %s -> %s' % (
            'yes' if ok1 else 'NO', 'yes' if ok2 else 'NO',
            'the shipped defaults reproduce win3' if ok1 and ok2 else 'NOT shown that the shipped defaults reproduce win3'))
        P()
        P('| pair | metric | CF1 % [CI] | WC pooled % [CI] | S2 |')
        P('|---|---|---|---|---|')
        for A in ('ship', 'win3'):
            for key, wv, wlo, whi in sorted(WC, key=lambda x: [k for k, _ in VKEYS].index(x[0])):
                c = next((c for c in head if c['A'] == A and c['B'] == 's0' and c['key'] == key), None)
                if not c:
                    continue
                same = (c['pct'] > 0) == (wv > 0)
                ovl = c['lo'] <= whi and c['hi'] >= wlo
                P('| %s vs s0 | %s | %+.1f [%+.1f, %+.1f] | %+.1f [%+.1f, %+.1f] | %s |' % (
                    A, c['label'], c['pct'], c['lo'], c['hi'], wv, wlo, whi, 'consistent' if same and ovl else 'differs from WC'))
    else:
        eq = [c for c in head if c['key'] != 'median']
        ok = len(eq) == 4 and all(c['claim'] in ('equal', 'not shown different') for c in eq)
        P('- CF2 overall: %s' % ('the shipped native default reproduces mc' if ok else 'NOT shown that the shipped native default reproduces mc'))
        P('- S2: CF2 has no WC counterpart. Context only: W8a mc vs n0 median about -29 %, fps about +44 % (READOUT-NIGHT).')
    P()
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(dict(window=a.window, outdir=a.outdir, void=void_arm, m12_median=ng_med, plateau=plateau,
                           contrasts=allres, runs=runs), f, indent=1, default=str)


if __name__ == '__main__':
    main()

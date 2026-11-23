#!/usr/bin/env python3
"""Agent 6, tasks #5 (old #31, W4b) and #13 (W5): extra checks beside w4b_logdiff.py. Read-only, stdlib only.

  python -B build/agent6/w4b/w4b_extra.py <matrix_dir> [--base ARM] [--count TEXT]... [--out FILE]

Arms come from the run-dir names (HHMM-<arm>-rN). A cold run (HHMM-cold-<arm>) is its own arm, cold-<arm>.
--base picks the reference arm (default d0, as in W4b; W5 uses s0 or base).
1. run.json close/crash fields for every run, plus the last game.log lines (clean-exit sequence), the bin dir,
   env_set, the cvars added/removed relative to the base arm's first run, and STUCK / WM_CLOSE text hits in the
   run dir's text files (and in the matrix dir's top-level files).
2. Exact-text game.log diff per arm vs the base arm's runs: timestamps, [tNNN] and the run-dir name are dropped, but
   there is NO number/hex normalisation, so a changed address, count or value shows up. Toypad payload lines are
   reduced to their frame header (Write: first 5 bytes = prefix 16 55 len cmd; Read: first 4 bytes), because the
   challenge bytes are random per run.
3. Toypad write-command sequence per run, and the B1 (challenge) times in s after the first Toypad write.
4. Boot milestones in s after the first log line (median per arm).
5. Run order (run.json start): per run the log size, level counts, Toypad counts, close time, frame stats, the sys
   window and build processes, and the --count texts (lines containing TEXT); then per-arm lists of the counts.
6. Per-arm presence of every exact key that is not in all runs. SIG = every arm has it in all or none of its runs.
bench/agent8/run/gate_logdiff.py is imported read-only (LINE_RE, log_files); no bytecode is written.
"""
import sys
sys.dont_write_bytecode = True
import argparse, datetime, glob, importlib.util, json, os, re, statistics
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
_spec = importlib.util.spec_from_file_location('gate_logdiff', os.path.join(ROOT, 'bench', 'agent8', 'run', 'gate_logdiff.py'))
gl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gl)

RUNDIR_RE = re.compile(r'runs[\\/]\d{4}-[^\\/\s\'"]+')
TOY_RE = re.compile(r'Toypad\s*\[\s*([A-Za-z]+)\s*\]\s*(.*)$')
ARM_RE = re.compile(r'^\d{4}-(cold-[A-Za-z0-9]+|[A-Za-z0-9]+)(?:-|$)')
MILESTONES = [
    ('launch', 'Startup: launching the module'),
    ('storage', 'Initializing shader storage'),
    ('audio', 'audio endpoint'),
    ('toyB0', 'Toypad[Write] 0B 16 55 0F B0'),
    ('hdr_fail', 'INSTALL0_2.HDR'),
    ('dat_fail', 'INSTALL0_2.DAT'),
    ('closing', 'Window closing'),
    ('exit', 'Title terminated'),
]
EXIT_SEQ = ('Window closing, shutting down', 'Execution complete', 'Title terminated; hard-exiting process')
TEXT_EXT = ('.json', '.txt', '.log', '.md', '.out', '.err', '.tsv')
WORDS = ('STUCK', 'WM_CLOSE')
LEVELS = ('info', 'warning', 'error', 'critical')


def ts(s):
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def fv(v, spec='%s'):
    return '-' if v is None else (spec % v)


def scan(rd, counts=()):
    r = dict(keys=Counter(), toy_seq=[], b1=[], first=None, t0toy=None, close_rel=None, ms={}, tail=[],
             lvl=Counter(), toyw=0, toyr=0, cnt=Counter(), lines=0, bytes=0)
    for fp in gl.log_files(rd):
        try:
            r['bytes'] += os.path.getsize(fp)
        except OSError:
            pass
        with open(fp, encoding='utf-8', errors='replace') as fh:
            for raw in fh:
                line = raw.rstrip('\r\n')
                if not line:
                    continue
                r['lines'] += 1
                for c in counts:
                    if c in line:
                        r['cnt'][c] += 1
                r['tail'] = (r['tail'] + [line])[-3:]
                m = gl.LINE_RE.match(line)
                if not m:
                    r['keys']['[raw] ' + line] += 1
                    continue
                t = ts(m.group('ts'))
                if r['first'] is None:
                    r['first'] = t
                lvl, cat, msg = m.group('lvl'), m.group('cat'), m.group('msg')
                r['lvl'][lvl] += 1
                for name, pat in MILESTONES:
                    if name not in r['ms'] and pat in msg:
                        r['ms'][name] = (t - r['first']).total_seconds()
                if 'Window closing' in msg and r['t0toy'] is not None:
                    r['close_rel'] = (t - r['t0toy']).total_seconds()
                ty = TOY_RE.search(msg)
                if ty:
                    kind = ty.group(1).capitalize()
                    toks = ty.group(2).split()
                    hdr = ' '.join(toks[:5] if kind == 'Write' else toks[:4])
                    r['keys']['[%s] [%s] Toypad[%s] %s' % (lvl, cat, kind, hdr)] += 1
                    if kind == 'Write':
                        r['toyw'] += 1
                        if r['t0toy'] is None:
                            r['t0toy'] = t
                        cmd = toks[4] if len(toks) > 4 else '?'
                        r['toy_seq'].append(cmd)
                        if cmd == 'B1':
                            r['b1'].append((t - r['t0toy']).total_seconds())
                    else:
                        r['toyr'] += 1
                    continue
                r['keys']['[%s] [%s] %s' % (lvl, cat, RUNDIR_RE.sub('runs/<run>', msg))] += 1
    return r


def facts(rd):
    p = os.path.join(rd, 'run.json')
    try:
        with open(p, encoding='utf-8-sig') as fh:
            d = json.load(fh)
    except Exception as e:  # noqa: BLE001
        return dict(run_json_error=str(e))
    c = d.get('close') or {}
    pr = d.get('params') or {}
    fr = d.get('frames') or {}
    sw = (d.get('sys') or {}).get('window') or {}
    return dict(status=d.get('status'), problems=len(d.get('problems') or []), exit=d.get('exit_code_hex'),
                early=d.get('exited_early'), wm_close=c.get('wm_close_posted'), repost=c.get('wm_close_repost_s'),
                exit_wait_s=c.get('exit_wait_s'), killed=c.get('killed'), clean=c.get('clean'),
                wer=d.get('werfault_seen'), foreign_dumps=len(d.get('foreign_crash_dumps') or []),
                dialogs=len(d.get('dialogs') or []), not_resp=d.get('not_responding_samples'),
                perf_stalled=d.get('perf_csv_stalled'), artifacts=len(d.get('artifacts') or []),
                log_lines=d.get('log_lines'), runner_error=d.get('runner_error'), excluded=d.get('excluded'),
                dmp=len(glob.glob(os.path.join(rd, '**', '*.dmp'), recursive=True)),
                _bin=os.path.basename(str(d.get('bin_dir') or '').rstrip('\\/')), _env=d.get('env_set') or {},
                _cvar=list(pr.get('cvar') or []), _start=d.get('start'), _flags_info=d.get('flags_info'),
                _flags_excl=d.get('flags_excluding'), _median=fr.get('median_ms'), _p99=fr.get('p99_ms'),
                _max=fr.get('max_ms'), _over33=fr.get('over_33ms'), _mhz=sw.get('eff_mhz_mean'),
                _pmhz=sw.get('p_eff_mhz_mean'), _emhz=sw.get('e_eff_mhz_mean'), _util=sw.get('cpu_util_mean'),
                _putil=sw.get('p_util_mean'), _cores=d.get('window_cpu_cores_mean'),
                _bprocs=len(d.get('build_procs_window') or []), _bprocs_warm=len(d.get('build_procs_warmup') or []),
                _boot=d.get('boot_s'), _free=d.get('free_ram_gb_at_start'), _input=sw.get('input_events'),
                _fg=sw.get('fg_game_share'), _ticks=d.get('ticks_skipped_window'),
                _nogrowth=d.get('perf_csv_max_no_growth_window_s'), _nrw=d.get('not_responding_window_samples'),
                _sysflags=(d.get('sys') or {}).get('flags'))


def textscan(paths):
    hits, lines = Counter(), defaultdict(list)
    for fp in paths:
        if not os.path.isfile(fp) or not fp.lower().endswith(TEXT_EXT):
            continue
        try:
            if os.path.getsize(fp) > 20 * 1024 * 1024:
                continue
            with open(fp, encoding='utf-8', errors='replace') as fh:
                for raw in fh:
                    for wd in WORDS:
                        if wd in raw:
                            hits[wd] += 1
                            if len(lines[wd]) < 12:
                                lines[wd].append('%s: %s' % (os.path.basename(fp), raw.strip()[:220]))
        except OSError:
            pass
    return hits, lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('matrix')
    ap.add_argument('--base', default='d0', help='reference arm (default d0)')
    ap.add_argument('--count', action='append', default=[], help='text to count per run (repeatable)')
    ap.add_argument('--out')
    a = ap.parse_args()
    B = a.base.lower()
    mdir = os.path.abspath(a.matrix)
    rdirs = sorted(d for d in glob.glob(os.path.join(mdir, 'runs', '*')) if os.path.isdir(d) and gl.log_files(d))
    arms, armof = defaultdict(list), {}
    for rd in rdirs:
        m = ARM_RE.match(os.path.basename(rd))
        armof[rd] = m.group(1).lower() if m else '?'
        arms[armof[rd]].append(rd)
    S = {rd: scan(rd, a.count) for rd in rdirs}
    F = {rd: facts(rd) for rd in rdirs}
    T = {rd: textscan(glob.glob(os.path.join(rd, '**', '*'), recursive=True)) for rd in rdirs}
    nm = os.path.basename
    out = []
    w = out.append
    w('W4b/W5 extra checks (Agent 6, tasks #5/#13): %s; base arm %s' % (mdir, B))
    w('arms: ' + '; '.join('%s=%d' % (k, len(v)) for k, v in sorted(arms.items())))
    w('')
    w('1. run.json close/crash fields; exit_seq = the last 3 game.log lines are closing / complete / terminated;'
      ' STUCK/WM_CLOSE = text-file lines in the run dir that contain the word')
    base_cv = (F[arms[B][0]].get('_cvar') or []) if arms.get(B) else []
    for arm in sorted(arms):
        for rd in arms[arm]:
            tail = S[rd]['tail']
            ok = len(tail) == 3 and all(p in l for p, l in zip(EXIT_SEQ, tail))
            f = F[rd]
            w('  %-9s %-17s exit_seq=%s %s' % (arm, nm(rd), 'ok' if ok else 'NO: %r' % tail,
                                                ' '.join('%s=%s' % kv for kv in f.items() if not kv[0].startswith('_'))))
            cv = f.get('_cvar') or []
            plus = [x for x in cv if x not in base_cv]
            minus = [x for x in base_cv if x not in cv]
            env = ','.join('%s=%s' % kv for kv in sorted((f.get('_env') or {}).items())) or '-'
            w('  %-9s %-17s bin=%s env=%s cvar+%s cvar-%s flags_info=%s flags_excl=%s sys_flags=%s STUCK=%d WM_CLOSE=%d'
              % ('', '', f.get('_bin'), env, plus, minus, f.get('_flags_info'), f.get('_flags_excl'),
                 f.get('_sysflags'), T[rd][0]['STUCK'], T[rd][0]['WM_CLOSE']))
    for rd in rdirs:
        for wd in WORDS:
            for l in T[rd][1][wd]:
                w('    %s %s' % (nm(rd), l))
    mh, ml = textscan(glob.glob(os.path.join(mdir, '*')))
    w('  matrix top-level text files: STUCK=%d WM_CLOSE=%d' % (mh['STUCK'], mh['WM_CLOSE']))
    for wd in WORDS:
        for l in ml[wd]:
            w('    %s' % l)
    base = arms.get(B, [])
    w('')
    if not base:
        w('2. no %s runs: exact-text diff skipped' % B)
    else:
        bunion = set().union(*[set(S[b]['keys']) for b in base])
        ball = set.intersection(*[set(S[b]['keys']) for b in base])
        bmax, bmin = Counter(), {}
        for b in base:
            for k, v in S[b]['keys'].items():
                bmax[k] = max(bmax[k], v)
        for k in bunion:
            bmin[k] = min(S[b]['keys'].get(k, 0) for b in base)
        w('2. exact-text diff vs %s (%s)' % (B, ', '.join(nm(b) for b in base)))
        w('   %s keys: union %d, in all %d runs %d; %s-internal variable keys (count range):'
          % (B, len(bunion), len(base), len(ball), B))
        for k in sorted(bunion):
            if bmin[k] != bmax[k]:
                w('     %s %d..%d  %s' % (B, bmin[k], bmax[k], k[:200]))
        for arm in sorted(arms):
            if arm == B:
                continue
            only, gone, cnt = defaultdict(list), defaultdict(list), defaultdict(list)
            for rd in arms[arm]:
                c = S[rd]['keys']
                for k, v in c.items():
                    if k not in bunion:
                        only[k].append('%s=%d' % (nm(rd), v))
                    elif not (bmin[k] <= v <= bmax[k]):
                        cnt[k].append('%s=%d' % (nm(rd), v))
                for k in ball:
                    if k not in c:
                        gone[k].append(nm(rd))
            n = len(arms[arm])
            w('  arm %s (%d runs): ONLY-exact %d, GONE-exact %d, count outside %s min..max %d'
              % (arm, n, len(only), len(gone), B, len(cnt)))
            for k, v in sorted(only.items()):
                w('    ONLY %d/%d  %s   [%s]' % (len(v), n, k[:220], ', '.join(v)))
            for k, v in sorted(gone.items()):
                w('    GONE %d/%d  %s   [%s]' % (len(v), n, k[:220], ', '.join(v)))
            for k, v in sorted(cnt.items()):
                w('    COUNT %s %d..%d, %s  %s' % (B, bmin[k], bmax[k], ', '.join(v), k[:200]))
    w('')
    w('3. Toypad: write-command sequence; B1 (challenge) times and window close, s after the first Toypad write')
    for arm in sorted(arms):
        ivs = []
        for rd in arms[arm]:
            s = S[rd]
            b1 = s['b1']
            iv = [round(y - x, 1) for x, y in zip(b1, b1[1:])]
            ivs.extend(iv)
            w('  %-9s %-17s seq %s | B1 at %s | intervals %s | close at %s'
              % (arm, nm(rd), ' '.join(s['toy_seq']), [round(x, 1) for x in b1], iv,
                 ('%.1f' % s['close_rel']) if s['close_rel'] is not None else '?'))
        if ivs:
            w('  %-9s B1 intervals: n=%d mean %.1f median %.1f min %.1f max %.1f'
              % (arm, len(ivs), statistics.mean(ivs), statistics.median(ivs), min(ivs), max(ivs)))
    w('')
    w('4. boot milestones, s after the first log line (median per arm; min..max)')
    for arm in sorted(arms):
        row = []
        for name, _ in MILESTONES:
            vals = [S[rd]['ms'][name] for rd in arms[arm] if name in S[rd]['ms']]
            row.append('%s %s' % (name, ('%.2f (%.2f..%.2f)' % (statistics.median(vals), min(vals), max(vals))) if vals else '-'))
        w('  %-9s %s' % (arm, ' | '.join(row)))
    w('')
    w('5. run order (run.json start). close = s after the first Toypad write; med/p99/max = frame ms; mhz/P/E = sys'
      ' window eff MHz; util/Putil = %%; cores = window CPU cores; bprocs = build procs window/warmup')
    for i, c in enumerate(a.count):
        w('   c%d = lines containing %r' % (i + 1, c))
    order = sorted(rdirs, key=lambda rd: (str(F[rd].get('_start') or ''), nm(rd)))
    for rd in order:
        s, f = S[rd], F[rd]
        lv = s['lvl']
        other = sum(v for k, v in lv.items() if k not in LEVELS)
        w('  %-17s %-9s %-12s %s lines=%d B=%d info=%d warn=%d err=%d other=%d toyW=%d toyR=%d B1=%d close=%s'
          ' exit_wait=%s med=%s p99=%s max=%s mhz=%s P=%s E=%s util=%s Putil=%s cores=%s bprocs=%d/%d boot=%s'
          ' free=%s input=%s fg=%s nogrowth=%s %s'
          % (nm(rd), armof[rd], f.get('_bin'), (str(f.get('_start') or '?'))[11:19], s['lines'], s['bytes'],
             lv['info'], lv['warning'], lv['error'] + lv['critical'], other, s['toyw'], s['toyr'], len(s['b1']),
             fv(s['close_rel'], '%.1f'), fv(f.get('exit_wait_s')), fv(f.get('_median')), fv(f.get('_p99')),
             fv(f.get('_max')), fv(f.get('_mhz')), fv(f.get('_pmhz')), fv(f.get('_emhz')), fv(f.get('_util')),
             fv(f.get('_putil')), fv(f.get('_cores'), '%.2f'), f.get('_bprocs', 0), f.get('_bprocs_warm', 0),
             fv(f.get('_boot')), fv(f.get('_free')), fv(f.get('_input')), fv(f.get('_fg')), fv(f.get('_nogrowth')),
             ' '.join('c%d=%d' % (i + 1, s['cnt'][c]) for i, c in enumerate(a.count))))
    for i, c in enumerate(a.count):
        w('  c%d per arm: %s' % (i + 1, '; '.join('%s=%s' % (arm, [S[rd]['cnt'][c] for rd in arms[arm]])
                                                  for arm in sorted(arms))))
    w('  env_set per arm: %s' % '; '.join('%s=%s' % (arm, [','.join(sorted(F[rd].get('_env') or {})) or '-'
                                                           for rd in arms[arm]]) for arm in sorted(arms)))
    w('')
    w('6. per-arm presence (runs with the key / runs) of every exact key that is not in all %d runs' % len(rdirs))
    armorder = sorted(arms)
    allk = set().union(*[set(S[rd]['keys']) for rd in rdirs]) if rdirs else set()
    sig, var = [], []
    for k in sorted(allk):
        pres = {arm: sum(1 for rd in arms[arm] if k in S[rd]['keys']) for arm in armorder}
        if all(pres[arm] == len(arms[arm]) for arm in armorder):
            continue
        clean = all(pres[arm] in (0, len(arms[arm])) for arm in armorder)
        row = ' '.join('%s=%d/%d' % (arm, pres[arm], len(arms[arm])) for arm in armorder)
        (sig if clean else var).append('%s  %s' % (row, k[:200]))
    w('  SIG (every arm all-or-none): %d' % len(sig))
    for l in sig:
        w('    ' + l)
    w('  VAR (present in only some runs of an arm): %d' % len(var))
    for l in var:
        w('    ' + l)
    txt = '\n'.join(out)
    print(txt)
    if a.out:
        with open(a.out, 'w', encoding='utf-8') as fh:
            fh.write(txt + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())

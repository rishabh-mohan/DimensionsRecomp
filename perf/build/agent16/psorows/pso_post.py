#!/usr/bin/env python3
"""pso_post.py (E16.2 for M16, S5 2.2/2.3 functional rows and the 2.4 A/B): read-only post of harness run dirs.

usage:
  pso_post.py --mode rows|ab --arm NAME=RUN_DIR [--arm ...] --expect-fp HEX --out FILE
  pso_post.py --selftest [--selftest-dir DIR] [--smoke RUN_DIR]

Each RUN_DIR is a harness\\run-game.ps1 run dir (game.log, run.json, summary.json; frames.csv is not read:
fps / p99 / 1% low / >50 ms come from summary.json "frames" (the harness's frames.csv digest after its warm-up),
falling back to summary.json "perf" (perf.csv digest); the source is printed per arm).
Every arm runs with LEGO_NATIVE_PSO_STATS=1 and LEGO_NATIVE_PSO_STATS_INTERVAL=10. The PSO summary block used is
the last one with reason "exit" (else the last one). Log formats: pipeline_library.cpp (HEAD + 2.2 + 2.3 r2) and
pipeline_stats.h at HEAD a8e8dc8; see RX below.
rows mode arms: s0-ref-cold c-pso-t1 c-pso-unl w-ref-t1 w-pso-t1 w-ref-t4 w-pso-t2 w-pso-t4 w-pso-unl
ab mode arms:   prime c0-1..3 c1-1..3 w0-1..3 w1-1..3 w2-1..2   (all native4bp; AB-PLAN.md sections 4-6)
Exit 0 = every hard check passed (RESULT PASS or PASS-WITH-CHECKS), 1 = any FAIL, 2 = usage error.
The last line of --out is "RESULT: PASS|PASS-WITH-CHECKS: <soft>|FAIL: <reasons>".
"""
import argparse, collections, hashlib, json, os, re, statistics, sys

F = r'([\d.]+)'
RX = {
    # pipeline_library.cpp
    'fp': r'Native GPU \[([0-9a-f]{16})\]',
    'cache_rejected': r'Native GPU: pipeline cache (.+) rejected by the driver \(0x([0-9A-Fa-f]{8})\); rebuilding',
    'cache_unavailable': r'Native GPU: pipeline cache unavailable \(0x([0-9A-Fa-f]{8})\)',
    'cache_opened': r'Native GPU: pipeline cache (.+) opened \((\d+) bytes\)',
    'cache_off': r'Native GPU: pipeline cache disabled by LEGO_NATIVE_PSO_CACHE=0',
    'cache_capture': r'Native GPU: pipeline cache skipped while a capture layer is active',
    'env_save_unl': r'Native GPU: pipeline cache saves serialize outside the library lock \(LEGO_NATIVE_PSO_SAVE_UNLOCKED\)',
    'env_aux_unl': r'Native GPU: auxiliary pipelines compile outside the library lock \(LEGO_NATIVE_PSO_AUX_UNLOCKED\)',
    'prep_disabled': r'Native GPU: startup pipeline preparation disabled by LEGO_NATIVE_PSO_PRECOMPILE=0',
    'prep_threads': r'Native GPU: startup pipeline preparation uses (\d+) threads \(LEGO_NATIVE_PSO_PREPARE_THREADS\)',
    'prep_processed': r'Native GPU: startup pipeline preparation processed (\d+) recipes',
    'seed': r'Native GPU: using startup pipeline seed (.+) with (\d+) recipes',
    'removed_seeded': r'Native GPU: removed (\d+) seeded pipelines from local recording',
    'no_recipes': r'Native GPU: no startup pipeline recipes yet; recording during gameplay',
    'startup': r'Native GPU: startup pipelines loaded=(\d+) compiled=(\d+) failed=(\d+) resident=(\d+) elapsed_ms=' + F,
    'stop_stats': r'Native GPU: pipeline cache hits=(\d+) misses=(\d+) stored=(\d+) saves=(\d+)',
    'seed_dir_fail': r'Native GPU: could not enumerate startup seed directory ',
    'recipes_ignored': r'Native GPU: ignoring invalid or incompatible pipeline recipes ',
    'recipes_saved': r'Native GPU: saved (\d+) startup pipeline recipes',
    'recipes_save_fail': r'Native GPU: could not save startup pipeline recipes ',
    'gave_up': r'Native GPU: unlocked pipeline cache save gave up after (\d+) passes',
    'postponed': r'Native GPU: pipeline cache save postponed; (\d+) bytes unavailable',
    'write_fail': r'Native GPU: could not write pipeline cache ',
    'replace_fail': r'Native GPU: could not replace pipeline cache ',
    'einval': r'E_INVALIDARG|0x80070057',
    'cache_saved': r'Native GPU: pipeline cache saved, (\d+) new pipelines, (\d+) bytes',
    # pipeline_async.h
    'async_on': r'Native GPU: async PSO compile on \(threads=(\d+) wait_us=(\d+) frame_us=(\d+)\)',
    # pipeline_stats.h
    'stats_on': r'Native GPU: PSO stats on \(LEGO_NATIVE_PSO_STATS\); summary at exit and whenever (.+) is created, delta every (\d+) s',
    'stats_interval': (r'Native GPU PSO stats, last ' + F + r' s: (\d+) frames, ' + F + r' fps, worst ' + F + r' ms, (\d+) hitches, '
                       r'(\d+) compile frames; (\d+) compiles, ' + F + r' ms \(' + F + r' ms blocking\), (\d+) misses, (\d+) hits, '
                       r'(\d+) skipped draws'),
    'sum_head': r'Native GPU PSO stats \(([^)]*)\): (\d+) frames over ' + F + r' s',
    'sum_startup': r'PSO startup: cache (.+?), file (\d+) bytes, read ' + F + r' ms, library create ' + F + r' ms',
    'sum_prep': (r'PSO startup preparation: loaded (\d+), compiled (\d+), failed (\d+), resident (\d+), threads (\d+), ' + F +
                 r' ms \(library loads ' + F + r' ms, compiles ' + F + r' ms, worst compile ' + F + r' ms\)'),
    'sum_lookups': (r'PSO lookups: (\d+) \(warm (\d+), library (\d+), miss (\d+)\), avg ' + F + r' ms, worst ' + F +
                    r' ms; mutex wait ' + F + r' ms in total, worst ' + F + r' ms, (\d+) waits of 1 ms or more; library loads (\d+), avg '
                    + F + r' ms, worst ' + F + r' ms'),
    'sum_compiles': (r'PSO compiles: (\d+) taking ' + F + r' ms \(avg ' + F + r' ms, worst ' + F + r' ms\); <1 ms (\d+), 1-4 (\d+), '
                     r'4-16 (\d+), 16-64 (\d+), 64-256 (\d+), >=256 (\d+); untimed stores (\d+); store\(\) avg ' + F + r' ms, worst '
                     + F + r' ms'),
    'sum_threads': (r'PSO compiles by thread: present (\d+) \(' + F + r' ms\), async (\d+) \(' + F + r' ms\), other (\d+) \(' + F +
                    r' ms\)'),
    'sum_aux': (r'PSO auxiliary: (\d+) requests, (\d+) library hits, (\d+) compiles, (\d+) failed, ' + F + r' ms compiling, worst '
                + F + r' ms'),
    'sum_saves': (r'PSO saves: (\d+) written \((\d+) bytes\), (\d+) failed, (\d+) postponed; mutex held ' + F + r' ms in total, worst '
                  + F + r' ms; copy ' + F + r' ms, allocation outside the mutex ' + F + r' ms, write ' + F + r' ms; (\d+) retries, '
                  r'(\d+) allocations under the mutex'),
    'sum_async': (r'PSO async: (\d+) posted, (\d+) ready, (\d+) failed, (\d+) skipped draws, (\d+) waits \(' + F + r' ms\), (\d+) '
                  r'timeouts'),
    'sum_frames': (r'PSO frames: (\d+) at ' + F + r' fps, worst ' + F + r' ms; <=16\.7 ms (\d+), <=33\.3 (\d+), <=50 (\d+), <=100 (\d+), '
                   r'<=250 (\d+), >250 (\d+); hitches of 50 ms or more (\d+), frames with 4 ms or more of blocking compiles (\d+), '
                   r'both (\d+)'),
    'sum_minute_hdr': r'PSO minute    #: frames    fps worst_ms hitch cfrm  comp  comp_ms block_ms  miss   hits  skip',
    'sum_minute': (r'PSO minute\s+(\d+):\s+(\d+)\s+' + F + r'\s+' + F + r'\s+(\d+)\s+(\d+)\s+(\d+)\s+' + F + r'\s+' + F +
                   r'\s+(\d+)\s+(\d+)\s+(\d+)( \(partial\))?\s*$'),
}
FIELDS = {
    'startup': ['loaded', 'compiled', 'failed', 'resident', 'elapsed_ms'],
    'stop_stats': ['hits', 'misses', 'stored', 'saves'],
    'stats_interval': ['seconds', 'frames', 'fps', 'worst_ms', 'hitches', 'compile_frames', 'compiles', 'compile_ms',
                       'blocking_ms', 'misses', 'hits', 'skipped'],
    'sum_head': ['reason', 'frames', 'seconds'],
    'sum_startup': ['state', 'file_bytes', 'read_ms', 'create_ms'],
    'sum_prep': ['loaded', 'compiled', 'failed', 'resident', 'threads', 'ms', 'load_ms', 'compile_ms', 'worst_compile_ms'],
    'sum_lookups': ['lookups', 'warm', 'library', 'miss', 'avg_ms', 'worst_ms', 'wait_total_ms', 'wait_worst_ms', 'waits_1ms',
                    'lib_loads', 'lib_avg_ms', 'lib_worst_ms'],
    'sum_compiles': ['compiles', 'ms', 'avg_ms', 'worst_ms', 'lt1', 'b1_4', 'b4_16', 'b16_64', 'b64_256', 'ge256', 'untimed',
                     'store_avg_ms', 'store_worst_ms'],
    'sum_threads': ['present', 'present_ms', 'async', 'async_ms', 'other', 'other_ms'],
    'sum_aux': ['requests', 'hits', 'compiles', 'failed', 'ms', 'worst_ms'],
    'sum_saves': ['written', 'bytes', 'failed', 'postponed', 'held_ms', 'held_worst_ms', 'copy_ms', 'alloc_ms', 'write_ms',
                  'retries', 'under_lock'],
    'sum_async': ['posted', 'ready', 'failed', 'skipped', 'waits', 'wait_ms', 'timeouts'],
    'sum_frames': ['frames', 'fps', 'worst_ms', 'le16', 'le33', 'le50', 'le100', 'le250', 'gt250', 'hitches50', 'block_frames',
                   'both'],
    'sum_minute': ['index', 'frames', 'fps', 'worst_ms', 'hitches', 'cfrm', 'comp', 'comp_ms', 'block_ms', 'miss', 'hits', 'skip',
                   'partial'],
    'async_on': ['threads', 'wait_us', 'frame_us'],
    'cache_opened': ['path', 'bytes'],
    'cache_saved': ['new', 'bytes'],
}
CRX = {k: re.compile(v) for k, v in RX.items()}
SUMMARY_KEYS = [k for k in RX if k.startswith('sum_') and k != 'sum_head']
HARD_WARN = ('invalidated by failed draw', 'pipeline cache unavailable', 'could not write pipeline cache',
             'could not replace pipeline cache', 'gave up after', 'E_INVALIDARG')
ROWS_ARMS = ['s0-ref-cold', 'c-pso-t1', 'c-pso-unl', 'w-ref-t1', 'w-pso-t1', 'w-ref-t4', 'w-pso-t2', 'w-pso-t4', 'w-pso-unl']
AB_ARMS = ['prime'] + [f'{t}-{k}' for t in ('c0', 'c1', 'w0', 'w1') for k in (1, 2, 3)] + ['w2-1', 'w2-2']
MATCHED = collections.Counter()   # regex coverage (selftest)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def num(s):
    if s is None:
        return None
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


def fields(key, m):
    names = FIELDS.get(key)
    g = m.groups()
    if not names:
        return [num(x) for x in g]
    return {n: (num(v) if n not in ('path', 'state', 'reason', 'partial') else v) for n, v in zip(names, g)}


def norm_warn(line):   # from smoke_post.py
    m = re.match(r'^\[[^\]]*\] \[(warning|warn|error|critical)\] \[(\w+)\] \[t\d+\] (.*)$', line.rstrip('\r\n'))
    if not m:
        return None
    s = re.sub(r'0x[0-9A-Fa-f]+', '0x#', m.group(3))
    s = re.sub(r'\b[0-9A-Fa-f]{8,}\b', '#', s)
    s = re.sub(r'\d+', '#', s)
    s = re.sub(r"'[^']*'", "'*'", s)
    return f'[{m.group(1)}] [{m.group(2)}] {s[:140]}'


def parse_log(path):
    r = {'lines': 0, 'fp': None, 'warn': collections.Counter(), 'blocks': [], 'intervals': 0, 'iv': [], 'hard_exit': 0,
         'all': collections.defaultdict(list)}
    if not os.path.exists(path):
        r['missing'] = True
        return r
    block = None
    single = [k for k in RX if not k.startswith('sum_') and k not in ('fp', 'stats_interval')]
    for idx, line in enumerate(open(path, encoding='utf-8', errors='replace')):
        r['lines'] += 1
        k = norm_warn(line)
        if k:
            r['warn'][k] += 1
        if r['fp'] is None:
            m = CRX['fp'].search(line)
            if m:
                r['fp'] = m.group(1); MATCHED['fp'] += 1
        if 'PSO' in line:
            m = CRX['sum_head'].search(line)
            if m:
                MATCHED['sum_head'] += 1
                block = {'head': fields('sum_head', m), 'line': idx, 'sum_minute': []}
                r['blocks'].append(block)
                continue
            m = CRX['stats_interval'].search(line)
            if m:
                MATCHED['stats_interval'] += 1; r['intervals'] += 1
                r['iv'].append(fields('stats_interval', m))
                continue
            hit = False
            for key in SUMMARY_KEYS:
                m = CRX[key].search(line)
                if m:
                    MATCHED[key] += 1; hit = True
                    if block is not None:
                        if key == 'sum_minute':
                            block['sum_minute'].append(fields(key, m))
                        elif key != 'sum_minute_hdr':
                            block[key] = fields(key, m)
                    break
            if hit:
                continue
        if 'Native GPU' not in line and 'E_INVALIDARG' not in line and '0x80070057' not in line:
            if 'Title terminated; hard-exiting process' in line:
                r['hard_exit'] += 1
            continue
        for key in single:
            m = CRX[key].search(line)
            if not m:
                continue
            if key == 'einval' and CRX['cache_rejected'].search(line):
                continue   # a rejected blob may legitimately report E_INVALIDARG; judged by the rejection check
            MATCHED[key] += 1
            r['all'][key].append((idx, fields(key, m)))
    return r


def pick_block(blocks):
    """Last 'exit' block, else last 'pso-stats.now' block (the runner's trigger), else the last block of any reason."""
    for want in ('exit', 'pso-stats.now'):
        ex = [b for b in blocks if b['head']['reason'] == want]
        if ex:
            return ex[-1]
    return blocks[-1] if blocks else None


def pacing(sj):
    for src in ('frames', 'perf'):
        d = sj.get(src) or {}
        if d.get('fps_mean') is not None:
            return {'src': f'summary.json {src}', 'fps': d.get('fps_mean'), 'p99': d.get('p99_ms'),
                    'low1': d.get('fps_1pct_low'), 'gt50': d.get('hitches_over_50ms')}
    return {'src': 'none'}


def load_arm(name, run):
    a = {'name': name, 'run': run, 'present': bool(run) and os.path.isdir(run)}
    if not a['present']:
        return a
    try:
        a['rj'] = json.load(open(os.path.join(run, 'run.json'), encoding='utf-8-sig'))
    except Exception as e:  # noqa
        a['rj'] = None; a['rj_err'] = str(e)
    try:
        sj = json.load(open(os.path.join(run, 'summary.json'), encoding='utf-8-sig'))
    except Exception:  # noqa
        sj = {}
    a['pace'] = pacing(sj)
    a['first_frame_s'] = sj.get('first_frame_s')
    lg = parse_log(os.path.join(run, 'game.log'))
    a['log'] = lg
    a['blk'] = pick_block(lg['blocks']) or {}
    al = lg['all']
    last = lambda k: al[k][-1][1] if al.get(k) else None
    a['startup'] = last('startup'); a['opened'] = last('cache_opened'); a['stop'] = last('stop_stats')
    a['threads_line'] = last('prep_threads')
    a['processed'] = last('prep_processed')
    stop_idx = al['stop_stats'][-1][0] if al.get('stop_stats') else None
    saves = [i for i, _ in al.get('cache_saved', [])]
    a['saves_after_stop'] = sum(1 for i in saves if stop_idx is not None and i > stop_idx)
    a['stop_own_save'] = bool(stop_idx is not None and saves and any(i < stop_idx for i in saves))
    iv = lg['iv']
    a['iv'] = ({'frames': sum(x['frames'] for x in iv), 'hitches50': sum(x['hitches'] for x in iv),
                'block_frames': sum(x['compile_frames'] for x in iv), 'worst_ms': max(x['worst_ms'] for x in iv),
                'compiles': sum(x['compiles'] for x in iv), 'compile_ms': sum(x['compile_ms'] for x in iv),
                'skipped': sum(x['skipped'] for x in iv)} if iv else {})
    a['sumsrc'] = g(a, 'blk', 'head', 'reason') or ('10s-lines' if iv else None)
    return a


def fr(a, key):
    """PSO frames metric: the summary block, else the sum of the 10 s delta lines (exit summary lost)."""
    v = g(a, 'blk', 'sum_frames', key)
    return v if v is not None else g(a, 'iv', key)


def g(a, *path, default=None):
    v = a
    for p in path:
        if not isinstance(v, dict) or p not in v or v[p] is None:
            return default
        v = v[p]
    return v


def fmt(v, w=None):
    if v is None:
        s = '-'
    elif isinstance(v, float):
        s = f'{v:.1f}'
    else:
        s = str(v)
    return s


class Report:
    def __init__(self):
        self.out, self.fails, self.checks = [], [], []

    def say(self, s=''):
        self.out.append(s)

    def check(self, ok, name, detail, soft=False):
        tag = 'PASS' if ok else ('CHECK' if soft else 'FAIL')
        self.say(f'{tag} {name}: {detail}')
        if not ok:
            (self.checks if soft else self.fails).append(name)

    def info(self, name, detail):
        self.say(f'INFO {name}: {detail}')

    def table(self, cols, rows):
        w = [max(len(c), *(len(r[i]) for r in rows)) if rows else len(c) for i, c in enumerate(cols)]
        self.say('  '.join(c.ljust(w[i]) for i, c in enumerate(cols)))
        self.say('  '.join('-' * w[i] for i in range(len(cols))))
        for r in rows:
            self.say('  '.join(r[i].ljust(w[i]) for i in range(len(cols))))

    def result(self):
        if self.fails:
            v = 'FAIL: ' + '; '.join(self.fails)
        elif self.checks:
            v = 'PASS-WITH-CHECKS: ' + '; '.join(self.checks)
        else:
            v = 'PASS'
        self.say(f'RESULT: {v}')
        return 1 if self.fails else 0


def common_checks(R, a, fp, base_warn):
    n = a['name']
    j = a.get('rj')
    if not j:
        R.check(False, f'{n} run.json', f"unreadable: {a.get('rj_err')}")
    else:
        ins = j.get('input_script') or {}
        R.check(j.get('exit_code') == 0 and not j.get('exited_early') and not j.get('wer_seen') and not j.get('crash_events')
                and not j.get('dumps') and j.get('close_method') == 'wm_close', f'{n} clean exit',
                f"exit {j.get('exit_code_hex')} early {j.get('exited_early')} close {j.get('close_method')} {j.get('close_seconds')} s "
                f"wer {j.get('wer_seen')} crash {len(j.get('crash_events') or [])} dumps {len(j.get('dumps') or [])}")
        R.check(ins.get('timeouts') == 0 and not ins.get('error'), f'{n} route ran',
                f"steps {ins.get('steps_done')}/{ins.get('steps_total')} last {ins.get('last_step')} timeouts {ins.get('timeouts')} "
                f"error {ins.get('error')}")
    lg = a['log']
    if lg.get('missing'):
        R.check(False, f'{n} game.log', 'missing')
        return
    R.check(lg['fp'] == fp, f'{n} fingerprint', f"{lg['fp']} (want {fp})")
    al = lg['all']
    have = bool(al.get('stats_on')) and (bool(a['blk']) or lg['intervals'] > 0)
    R.check(have, f'{n} PSO stats lines', f"stats-on {len(al.get('stats_on', []))}, interval lines {lg['intervals']}, "
            f"summary blocks {len(lg['blocks'])} ({', '.join(b['head']['reason'] for b in lg['blocks']) or 'none'})")
    if have:
        R.check('sum_frames' in a['blk'], f'{n} PSO summary block', f"used {a['sumsrc']}" + (
            '' if 'sum_frames' in a['blk'] else ' (no full summary: the close watchdog hard-exits before StopPipelineLibrary, '
            'agent6-pipelines.md L37; create <run>\\cache\\pso-stats.now before close. Frame metrics come from the 10 s lines; '
            'saves/aux/lookups/async totals are unknown)'), soft=True)
    if a['blk']:
        b = a['blk']
        R.info(f'{n} PSO summary used', f"reason '{b['head']['reason']}' at game.log line {b['line'] + 1}, {b['head']['frames']} frames over "
               f"{b['head']['seconds']} s; {len(lg['blocks'])} block(s) in the log")
        R.check(b['head']['reason'] in ('pso-stats.now', 'exit'), f'{n} PSO summary reason',
                f"'{b['head']['reason']}' (want pso-stats.now or exit)")
    bad = {k: len(al.get(k, [])) for k in ('write_fail', 'replace_fail', 'einval', 'gave_up', 'cache_unavailable')}
    R.check(not any(bad.values()), f'{n} no cache write/replace/E_INVALIDARG/gave-up/unavailable lines',
            ', '.join(f'{k} {v}' for k, v in bad.items()))
    if al.get('recipes_save_fail') or al.get('seed_dir_fail') or al.get('postponed'):
        R.check(False, f'{n} recipe save / seed dir / postponed warnings',
                f"recipes_save_fail {len(al.get('recipes_save_fail', []))}, seed_dir_fail {len(al.get('seed_dir_fail', []))}, "
                f"postponed {len(al.get('postponed', []))}", soft=True)
    if base_warn is not None:
        new = sorted(set(lg['warn']) - set(base_warn))
        hard = [k for k in new if any(h in k for h in HARD_WARN)]
        R.check(not hard, f'{n} no new hard WARN/ERROR types vs baseline', f'{len(hard)} hard' +
                ''.join(f'\n    {k} x{lg["warn"][k]}' for k in hard[:10]))
        R.check(not new, f'{n} no new WARN/ERROR types vs baseline', f'{len(new)} new' +
                ''.join(f'\n    {k} x{lg["warn"][k]}' for k in new[:15]), soft=True)


def cold_checks(R, a):
    al = a['log']['all']
    R.check(bool(al.get('no_recipes')) and not a['startup'], f"{a['name']} cold confirmed",
            f"'no startup pipeline recipes yet' {len(al.get('no_recipes', []))}, startup line {'yes' if a['startup'] else 'no'}, "
            f"opened {g(a, 'opened', 'bytes')} bytes, summary cache {g(a, 'blk', 'sum_startup', 'state')}")


def warm_checks(R, a):
    n = a['name']; al = a['log']['all']; st = a['startup'] or {}
    ob = g(a, 'opened', 'bytes', default=0)
    R.check(ob > 0 and not al.get('cache_rejected') and not al.get('recipes_ignored'), f'{n} warm cache accepted',
            f"opened {ob} bytes, rejected {len(al.get('cache_rejected', []))}, recipes ignored {len(al.get('recipes_ignored', []))}, "
            f"summary cache {g(a, 'blk', 'sum_startup', 'state')}")
    lc = (st.get('loaded') or 0) + (st.get('compiled') or 0)
    R.check(bool(st) and lc > 0, f'{n} startup replay', 'no startup line' if not st else
            f"loaded {st['loaded']} compiled {st['compiled']} failed {st['failed']} resident {st['resident']} elapsed_ms {st['elapsed_ms']}")
    R.check(bool(st) and st.get('failed') == 0, f'{n} startup failed = 0', f"failed {st.get('failed')}", soft=True)


def threads_check(R, a, want):
    tl = a['threads_line']
    if want > 1:
        R.check(tl == [want], f"{a['name']} 'uses {want} threads' line", f'{tl}')
    else:
        R.check(tl is None, f"{a['name']} no 'uses N threads' line (threads 1)", f'{tl}', soft=True)


def tail_checks(R, a, hard):
    n = a['name']
    if a['stop'] is not None:
        R.check(a['saves_after_stop'] == 0, f'{n} no cache save after Stop', f"saves after the Stop line {a['saves_after_stop']}, "
                f"Stop/earlier save present {a['stop_own_save']}; Stop hits/misses/stored/saves {a['stop']}", soft=not hard)
    else:
        R.info(f'{n} Stop()', f"not reached ('Title terminated; hard-exiting' x{a['log']['hard_exit']}): the shutdown-save check "
               f"does not apply; cache saves logged {len(a['log']['all'].get('cache_saved', []))}")
    sv = g(a, 'blk', 'sum_saves')
    if sv:
        R.check(sv['failed'] == 0, f'{n} PSO saves failed = 0', f'{sv}')
    else:
        R.info(f'{n} PSO saves', 'no summary block: failed count unknown (write/replace/E_INVALIDARG lines are checked above)')


def row(a, cols):
    out = []
    for c, f in cols:
        try:
            out.append(fmt(f(a)) if a.get('present') else ('MISSING' if c == 'arm' else '-'))
        except Exception:  # noqa
            out.append('?')
    if not a.get('present'):
        out[0] = a['name'] + ' (MISSING)'
    return out


def exit_str(a):
    j = a.get('rj') or {}
    return 'ok' if j.get('exit_code') == 0 and j.get('close_method') == 'wm_close' and not j.get('wer_seen') else f"{j.get('exit_code_hex')}"


COMMON_COLS = [
    ('arm', lambda a: a['name']),
    ('exit', exit_str),
    ('fp', lambda a: (a['log']['fp'] or '-')[:8]),
    ('cache', lambda a: g(a, 'blk', 'sum_startup', 'state', default=(
        'rejected' if a['log']['all'].get('cache_rejected') else 'opened' if a.get('opened') else '-')).split(' ')[0]),
    ('open_B', lambda a: g(a, 'opened', 'bytes')),
    ('L', lambda a: g(a, 'startup', 'loaded')),
    ('C', lambda a: g(a, 'startup', 'compiled')),
    ('F', lambda a: g(a, 'startup', 'failed')),
    ('R', lambda a: g(a, 'startup', 'resident')),
    ('thr', lambda a: g(a, 'blk', 'sum_prep', 'threads', default=(a['threads_line'] or [1 if a.get('startup') else None])[0])),
    ('elapsed', lambda a: g(a, 'startup', 'elapsed_ms')),
]
PACE_COLS = [
    ('sum', lambda a: a.get('sumsrc')),
    ('hitch50', lambda a: fr(a, 'hitches50')),
    ('blockfr', lambda a: fr(a, 'block_frames')),
    ('worst', lambda a: fr(a, 'worst_ms')),
    ('fps', lambda a: g(a, 'pace', 'fps')),
    ('p99', lambda a: g(a, 'pace', 'p99')),
    ('1%low', lambda a: g(a, 'pace', 'low1')),
    ('1st_fr_s', lambda a: a.get('first_frame_s')),
]
ROWS_COLS = COMMON_COLS + [
    ('compiles', lambda a: g(a, 'blk', 'sum_compiles', 'compiles')),
    ('aux_req', lambda a: g(a, 'blk', 'sum_aux', 'requests')),
    ('aux_cmp', lambda a: g(a, 'blk', 'sum_aux', 'compiles')),
    ('aux_ms', lambda a: g(a, 'blk', 'sum_aux', 'ms')),
    ('saves', lambda a: g(a, 'blk', 'sum_saves', 'written')),
    ('svfail', lambda a: g(a, 'blk', 'sum_saves', 'failed')),
    ('held_ms', lambda a: g(a, 'blk', 'sum_saves', 'held_ms')),
    ('copy_ms', lambda a: g(a, 'blk', 'sum_saves', 'copy_ms')),
    ('retry', lambda a: g(a, 'blk', 'sum_saves', 'retries')),
    ('mwait_wst', lambda a: g(a, 'blk', 'sum_lookups', 'wait_worst_ms')),
] + PACE_COLS
AB_COLS = COMMON_COLS + [
    ('present', lambda a: g(a, 'blk', 'sum_threads', 'present')),
    ('async', lambda a: g(a, 'blk', 'sum_threads', 'async')),
    ('other', lambda a: g(a, 'blk', 'sum_threads', 'other')),
    ('posted', lambda a: g(a, 'blk', 'sum_async', 'posted', default=0)),
    ('ready', lambda a: g(a, 'blk', 'sum_async', 'ready', default=0)),
    ('afail', lambda a: g(a, 'blk', 'sum_async', 'failed', default=0)),
    ('skip', lambda a: g(a, 'blk', 'sum_async', 'skipped', default=g(a, 'iv', 'skipped', default=0 if a.get('blk') else None))),
    ('waits', lambda a: g(a, 'blk', 'sum_async', 'waits', default=0)),
    ('tmo', lambda a: g(a, 'blk', 'sum_async', 'timeouts', default=0)),
    ('recipes', lambda a: (a['log']['all'].get('recipes_saved') or [(0, [None])])[-1][1][0]),
] + PACE_COLS


def header(R, mode, arms, fp):
    R.say(f'pso_post.py mode {mode}; expect fingerprint {fp}')
    for a in arms.values():
        R.say(f"  arm {a['name']}: {a['run'] or '(not given)'}" + ('' if a['present'] else '  <- MISSING'))
    srcs = sorted({g(a, 'pace', 'src', default='none') for a in arms.values() if a['present']})
    R.say(f"  frame pacing (fps mean, p99 ms, 1% low fps) from: {', '.join(srcs) or 'none'}; hitch50/blockfr/worst from the "
          f"'PSO frames:' line of the exit summary")


def run_rows(R, arms, fp):
    header(R, 'rows', arms, fp)
    R.say('== table'); R.table([c for c, _ in ROWS_COLS], [row(a, ROWS_COLS) for a in arms.values()])
    R.say('== checks')
    for n, a in arms.items():
        if not a['present']:
            R.check(False, f'arm {n} missing', a['run'] or 'not given')
    P = {n: a for n, a in arms.items() if a['present']}
    s0 = P.get('s0-ref-cold')
    base = s0['log']['warn'] if s0 and not s0['log'].get('missing') else None
    if base is None:
        R.info('warning baseline', 's0-ref-cold missing: the new-WARN-type check is skipped')
    for n, a in P.items():
        R.say(f'-- {n}')
        common_checks(R, a, fp, base if n != 's0-ref-cold' else None)
        (cold_checks if n.startswith(('s0', 'c-')) else warm_checks)(R, a)
        unl = n.endswith('-unl')
        al = a['log']['all']
        envs = (len(al.get('env_save_unl', [])), len(al.get('env_aux_unl', [])))
        if unl:
            R.check(envs[0] >= 1 and envs[1] >= 1, f'{n} SAVE_UNLOCKED and AUX_UNLOCKED env lines', f'save {envs[0]}, aux {envs[1]}')
        else:
            R.check(envs == (0, 0), f'{n} no unlocked env lines (envs unset)', f'save {envs[0]}, aux {envs[1]}')
        tn = re.search(r'-t(\d+)$', n)
        if n.startswith('w-'):
            threads_check(R, a, int(tn.group(1)) if tn else 1)
        tail_checks(R, a, hard='-pso-' in n)
        sv = g(a, 'blk', 'sum_saves')
        if unl and sv:
            R.check(sv['held_ms'] < sv['copy_ms'] or sv['written'] == 0, f'{n} save mutex held < copy',
                    f"held {sv['held_ms']} ms (worst {sv['held_worst_ms']}), copy {sv['copy_ms']} ms, retries {sv['retries']}, "
                    f"under-lock allocations {sv['under_lock']}", soft=True)
        aux = g(a, 'blk', 'sum_aux')
        if aux:
            R.check(aux['failed'] == 0, f'{n} auxiliary failed = 0', f'{aux}', soft=True)
        if n == 's0-ref-cold':
            R.check(bool(al.get('recipes_saved')) and bool(al.get('cache_saved')), f'{n} seed written',
                    f"recipes saved {[x[1][0] for x in al.get('recipes_saved', [])]}, cache saves {len(al.get('cache_saved', []))}")
        if a['processed'] or al.get('seed') or al.get('removed_seeded'):
            R.info(f'{n} replay lines', f"processed {a['processed']}, seeds {[(os.path.basename(s[1][0]), s[1][1]) for s in al.get('seed', [])]}, "
                   f"removed seeded {[x[1][0] for x in al.get('removed_seeded', [])]}")

    def st(n):
        return (P.get(n) or {}).get('startup') or {}

    def seeds(n):
        al = P[n]['log']['all']
        return ([(os.path.basename(s[1][0]), s[1][1]) for s in al.get('seed', [])], [x[1][0] for x in al.get('removed_seeded', [])])

    def lc(s):
        return (s.get('loaded') or 0) + (s.get('compiled') or 0)

    R.say('== 2.2 recipe replay')
    if all(n in P for n in ('w-pso-t1', 'w-ref-t1')):
        a, b = st('w-pso-t1'), st('w-ref-t1')
        keys = ('loaded', 'compiled', 'failed', 'resident')
        R.check(bool(a) and bool(b) and all(a.get(k) == b.get(k) for k in keys), 'w-pso-t1 vs w-ref-t1 startup counts exactly equal',
                f"pso {[a.get(k) for k in keys]} ref {[b.get(k) for k in keys]}")
        R.check(seeds('w-pso-t1') == seeds('w-ref-t1'), 'w-pso-t1 vs w-ref-t1 seed lines and removed-seeded equal',
                f"pso {seeds('w-pso-t1')} ref {seeds('w-ref-t1')}")
    else:
        R.check(False, '2.2 t1 comparison', 'w-pso-t1 or w-ref-t1 missing')
    t1 = st('w-pso-t1')
    for n in ('w-pso-t2', 'w-pso-t4'):
        if n not in P or not t1:
            R.check(False, f'2.2 {n} vs w-pso-t1', f'{n} or w-pso-t1 missing or without a startup line')
            continue
        s = st(n)
        R.check(bool(s) and lc(s) == lc(t1), f'{n} loaded+compiled == w-pso-t1', f'{lc(s)} vs {lc(t1)} (L/C {s.get("loaded")}/{s.get("compiled")} vs '
                f'{t1.get("loaded")}/{t1.get("compiled")})')
        R.check(bool(s) and s.get('resident') == min(512, lc(s)), f'{n} resident == min(512, L+C)', f"{s.get('resident')} vs {min(512, lc(s))}")
        R.check(bool(s) and (s.get('failed') or 0) <= (t1.get('failed') or 0), f'{n} failed <= w-pso-t1', f"{s.get('failed')} vs {t1.get('failed')}")
    if t1:
        R.info('w-pso-t1 resident vs min(512, L+C)', f"{t1.get('resident')} vs {min(512, lc(t1))}")
    if all(n in P for n in ('w-pso-t4', 'w-ref-t4')):
        a, b = st('w-pso-t4'), st('w-ref-t4')
        R.check(bool(a) and bool(b) and lc(a) == lc(b) and a.get('failed') == b.get('failed') and a.get('resident') == b.get('resident'),
                'w-pso-t4 vs w-ref-t4 L+C, failed, resident equal', f"pso L+C {lc(a)} F {a.get('failed')} R {a.get('resident')}; "
                f"ref L+C {lc(b)} F {b.get('failed')} R {b.get('resident')}")
        R.check(a.get('loaded') == b.get('loaded') and a.get('compiled') == b.get('compiled'), 'w-pso-t4 vs w-ref-t4 L/C split equal',
                f"{a.get('loaded')}/{a.get('compiled')} vs {b.get('loaded')}/{b.get('compiled')}", soft=True)
    else:
        R.check(False, '2.2 t4 comparison', 'w-pso-t4 or w-ref-t4 missing')
    R.info('elapsed_ms', ', '.join(f"{n} {st(n).get('elapsed_ms')}" for n in ('w-ref-t1', 'w-pso-t1', 'w-pso-t2', 'w-ref-t4', 'w-pso-t4') if n in P))
    if st('w-pso-t4') and t1:
        R.check(st('w-pso-t4')['elapsed_ms'] < t1['elapsed_ms'], 'w-pso-t4 elapsed_ms < w-pso-t1',
                f"{st('w-pso-t4')['elapsed_ms']} vs {t1['elapsed_ms']}", soft=True)

    R.say('== 2.3 unlocked aux/save')
    for n, ref in (('c-pso-unl', 'c-pso-t1'), ('w-pso-unl', 'w-pso-t1')):
        if n in P and ref in P:
            x, y = g(P[n], 'blk', 'sum_aux') or {}, g(P[ref], 'blk', 'sum_aux') or {}
            R.check(bool(x) and all(x.get(k) == y.get(k) for k in ('requests', 'hits', 'compiles', 'failed')),
                    f'{n} auxiliary counts == {ref}', f"{n} req/hits/comp/fail {[x.get(k) for k in ('requests', 'hits', 'compiles', 'failed')]} "
                    f"{ref} {[y.get(k) for k in ('requests', 'hits', 'compiles', 'failed')]}; ms {x.get('ms')} vs {y.get('ms')}", soft=True)
            lx, ly = g(P[n], 'blk', 'sum_lookups') or {}, g(P[ref], 'blk', 'sum_lookups') or {}
            R.info(f'{n} lookups mutex wait vs {ref}', f"worst {lx.get('wait_worst_ms')} vs {ly.get('wait_worst_ms')} ms, total "
                   f"{lx.get('wait_total_ms')} vs {ly.get('wait_total_ms')} ms, waits>=1ms {lx.get('waits_1ms')} vs {ly.get('waits_1ms')}")
        else:
            R.check(False, f'2.3 {n} vs {ref}', 'arm missing')
    if 'w-pso-unl' in P:
        a = P['w-pso-unl']; s = a['startup'] or {}
        R.check(g(a, 'opened', 'bytes', default=0) > 0 and not a['log']['all'].get('cache_rejected') and (s.get('loaded') or 0) > 0,
                'w-pso-unl reload of the c-pso-unl cache', f"opened {g(a, 'opened', 'bytes')} bytes, rejected "
                f"{len(a['log']['all'].get('cache_rejected', []))}, loaded {s.get('loaded')}, summary cache {g(a, 'blk', 'sum_startup', 'state')}")
    if 'c-pso-t1' in P and s0:
        x, y = P['c-pso-t1'], s0
        R.info('c-pso-t1 vs s0-ref-cold (driver cache primed by s0)',
               f"hitch50 {g(x, 'blk', 'sum_frames', 'hitches50')} vs {g(y, 'blk', 'sum_frames', 'hitches50')}, compiles "
               f"{g(x, 'blk', 'sum_compiles', 'compiles')} vs {g(y, 'blk', 'sum_compiles', 'compiles')} ({g(x, 'blk', 'sum_compiles', 'ms')} vs "
               f"{g(y, 'blk', 'sum_compiles', 'ms')} ms), p99 {g(x, 'pace', 'p99')} vs {g(y, 'pace', 'p99')}")


def med(vals):
    v = [x for x in vals if isinstance(x, (int, float))]
    return statistics.median(v) if v else None


def run_ab(R, arms, fp, n2=False):
    header(R, 'ab' + (' (n2: K = 1..2, no W2)' if n2 else ''), arms, fp)
    R.say('== per-arm table'); R.table([c for c, _ in AB_COLS], [row(a, AB_COLS) for a in arms.values()])
    P = {n: a for n, a in arms.items() if a['present']}
    types = ['c0', 'c1', 'w0', 'w1'] + ([] if n2 else ['w2'])
    MET = [('hitch50', lambda a: fr(a, 'hitches50')), ('blockfr', lambda a: fr(a, 'block_frames')),
           ('worst', lambda a: fr(a, 'worst_ms')), ('fps', lambda a: g(a, 'pace', 'fps')),
           ('p99', lambda a: g(a, 'pace', 'p99')), ('1%low', lambda a: g(a, 'pace', 'low1')),
           ('elapsed', lambda a: g(a, 'startup', 'elapsed_ms')),
           ('compiles', lambda a: g(a, 'blk', 'sum_compiles', 'compiles', default=g(a, 'iv', 'compiles'))),
           ('present', lambda a: g(a, 'blk', 'sum_threads', 'present')), ('async', lambda a: g(a, 'blk', 'sum_threads', 'async')),
           ('skip', lambda a: g(a, 'blk', 'sum_async', 'skipped', default=g(a, 'iv', 'skipped', default=0 if a.get('blk') else None))),
           ('tmo', lambda a: g(a, 'blk', 'sum_async', 'timeouts', default=0 if a.get('blk') else None))]
    M = {}
    for t in types:
        ms = [a for n, a in P.items() if n.startswith(t + '-')]
        M[t] = {k: med([f(a) for a in ms]) for k, f in MET}
        M[t]['n'] = len(ms)
    R.say('== median over K per arm type')
    R.table(['type', 'n'] + [k for k, _ in MET], [[t, str(M[t]['n'])] + [fmt(M[t][k]) for k, _ in MET] for t in types])

    def delta(x, y):
        rows = []
        for k, _ in MET:
            a, b = M[x][k], M[y][k]
            d = (a - b) if a is not None and b is not None else None
            pct = (100.0 * d / b) if d is not None and b else None
            rows.append([k, fmt(b), fmt(a), fmt(d), (f'{pct:+.0f}%' if pct is not None else '-')])
        return rows
    for x, y in (('c1', 'c0'), ('w0', 'c0'), ('w1', 'c0'), ('w2', 'w0')):
        if x not in M:
            R.say(f'== delta {x.upper()} vs {y.upper()}: not run (n2)')
            continue
        R.say(f'== delta {x.upper()} vs {y.upper()} (medians)')
        R.table(['metric', y.upper(), x.upper(), 'delta', 'pct'], delta(x, y))

    R.say('== checks')
    for n, a in arms.items():
        if not a['present']:
            R.check(False, f'arm {n} missing', a['run'] or 'not given')
    bw = collections.Counter()
    for n, a in P.items():
        if n.startswith('c0-') and not a['log'].get('missing'):
            bw.update(a['log']['warn'])
    base = bw if any(n.startswith('c0-') for n in P) else None
    if base is None:
        R.info('warning baseline', 'no c0 arm: the new-WARN-type check is skipped')
    c0_hitch = M['c0']['hitch50']
    for n, a in P.items():
        R.say(f'-- {n}')
        t = n.split('-')[0]
        common_checks(R, a, fp, None if t == 'c0' else base)
        al = a['log']['all']
        asy = t in ('c1', 'w1')
        R.check(bool(al.get('async_on')) == asy, f"{n} async {'on' if asy else 'off'}", f"async-on lines {len(al.get('async_on', []))}")
        sa = g(a, 'blk', 'sum_async')
        if a['blk']:
            R.check(not sa or sa['failed'] == 0, f'{n} async failed = 0', f'{sa}' if sa else 'no PSO async line (0 posted, 0 skipped)')
        else:
            R.check(not asy, f'{n} async failed = 0', 'unknown: no PSO summary block' + (
                f" (10 s lines: {g(a, 'iv', 'skipped')} skipped draws)" if asy else ' (async off)'), soft=True)
        if asy and sa and c0_hitch is not None:
            R.check(sa['timeouts'] <= c0_hitch, f'{n} async timeouts <= C0 median hitch50', f"{sa['timeouts']} vs {c0_hitch}", soft=True)
        if t in ('prime', 'c0', 'c1'):
            cold_checks(R, a)
        else:
            warm_checks(R, a)
            st = a['startup'] or {}
            R.check(bool(st) and st.get('failed') == 0, f'{n} warm startup failed = 0 (hard)', f"failed {st.get('failed')}")
            threads_check(R, a, 4 if t == 'w2' else 1)
        rs = al.get('recipes_saved', [])
        R.check(bool(rs), f'{n} recipes saved', f"{[x[1][0] for x in rs]}", soft=t != 'prime')
        tail_checks(R, a, hard=False)

    R.say('== section 6 decision lines (INFO only; n is tiny, no statistics)')
    c0, w0, c1, w2 = M['c0'], M['w0'], M['c1'], M.get('w2')
    if c0['hitch50'] is not None and w0['hitch50'] is not None:
        cut = 100.0 * (c0['hitch50'] - w0['hitch50']) / c0['hitch50'] if c0['hitch50'] else 0.0
        el = w0['elapsed']
        R.info('#35 seeded boot', f"W0 hitch50 {fmt(w0['hitch50'])} vs C0 {fmt(c0['hitch50'])} (cut {cut:.0f}%, want >= 50%); W0 elapsed_ms "
               f"{fmt(el)} (want < ~3000) -> {'MEETS' if cut >= 50 and el is not None and el < 3000 else 'does not meet'} the #35 rule")
    else:
        R.info('#35 seeded boot', 'C0 or W0 medians missing')
    if c0['hitch50'] is not None and c1['hitch50'] is not None and c0['p99'] is not None and c1['p99'] is not None:
        win = c1['hitch50'] < c0['hitch50'] and c1['p99'] < c0['p99']
        R.info('async', f"C1 hitch50 {fmt(c1['hitch50'])} vs C0 {fmt(c0['hitch50'])}, p99 {fmt(c1['p99'])} vs {fmt(c0['p99'])}, fps {fmt(c1['fps'])} "
               f"vs {fmt(c0['fps'])} -> C1 {'beats' if win else 'does not beat'} C0 on both (still needs the functional row and the user's eye review)")
    else:
        R.info('async', 'C0 or C1 medians missing')
    if w2 is None:
        R.info('W2 parallel replay', 'not run (n2)')
    elif w2['elapsed'] is not None and w0['elapsed'] is not None:
        R.info('W2 parallel replay', f"W2 elapsed_ms {fmt(w2['elapsed'])} vs W0 {fmt(w0['elapsed'])} -> {'lower' if w2['elapsed'] < w0['elapsed'] else 'not lower'}")
    else:
        R.info('W2 parallel replay', 'W0 or W2 medians missing')


N2_SKIP = ['c0-3', 'c1-3', 'w0-3', 'w1-3', 'w2-1', 'w2-2']


def analyse(mode, arm_specs, fp, n2=False):
    expected = ROWS_ARMS if mode == 'rows' else [n for n in AB_ARMS if not (n2 and n in N2_SKIP)]
    given = collections.OrderedDict()
    for n, d in arm_specs:
        given[n] = d
    arms = collections.OrderedDict()
    for n in expected + [n for n in given if n not in expected]:
        arms[n] = load_arm(n, given.get(n))
    R = Report()
    extra = [n for n in given if n not in expected]
    sel = collections.OrderedDict((n, arms[n]) for n in expected)
    if mode == 'rows':
        run_rows(R, sel, fp)
    else:
        run_ab(R, sel, fp, n2)
    for n in extra:
        R.info(f'extra arm {n}', 'present but not expected with --n2; ignored' if n2 and n in N2_SKIP else f'not a {mode} arm; ignored')
    rc = R.result()
    return R, rc


def parse_arms(specs):
    out, seen = [], set()
    for s in specs:
        n, eq, d = s.partition('=')
        n = n.strip()
        if not eq or not n or not d.strip():
            raise ValueError(f'malformed --arm {s!r} (want NAME=RUN_DIR)')
        if n in seen:
            raise ValueError(f'duplicate --arm {n}')
        seen.add(n); out.append((n, d.strip().strip('"')))
    return out


# ---------------------------------------------------------------- selftest
P0 = '[2026-11-25 19:00:{:02d}.000] [{}] [core] [t{}] {}'


def fx_log(path, kind, fp='39129c4c059be5f0', **o):
    L = []
    i = [0]

    def add(msg, lvl='info', t=100):
        L.append(P0.format(i[0] % 60, lvl, t, msg)); i[0] += 1
    cache = f'X:\\runs\\{kind}\\cache\\native-pso.bin'
    add('GPU route: direct native D3D-to-RHI; PM4 disabled')
    add('Native GPU: PSO stats on (LEGO_NATIVE_PSO_STATS); summary at exit and whenever X:\\cache\\pso-stats.now is created, '
        'delta every 10 s (LEGO_NATIVE_PSO_STATS_INTERVAL, 0 = off)')
    if o.get('unl'):
        add('Native GPU: pipeline cache saves serialize outside the library lock (LEGO_NATIVE_PSO_SAVE_UNLOCKED)')
        add('Native GPU: auxiliary pipelines compile outside the library lock (LEGO_NATIVE_PSO_AUX_UNLOCKED)')
    if o.get('async_on'):
        add('Native GPU: async PSO compile on (threads=2 wait_us=2000 frame_us=4000)')
    if o.get('rejected'):
        add(f'Native GPU: pipeline cache {cache} rejected by the driver (0x887E0002); rebuilding')
    warm = o.get('warm')
    add(f"Native GPU: pipeline cache {cache} opened ({o.get('bytes', 31457280 if warm else 0)} bytes)")
    if warm:
        th = o.get('threads', 1)
        if th > 1:
            add(f'Native GPU: startup pipeline preparation uses {th} threads (LEGO_NATIVE_PSO_PREPARE_THREADS)')
        if o.get('seed'):
            add('Native GPU: using startup pipeline seed X:\\bin\\native-pso-seed.bin with 40 recipes')
        add(f"Native GPU: startup pipeline preparation processed {o.get('L', 400) + o.get('C', 72) + o.get('F', 0)} recipes")
        if o.get('seed'):
            add('Native GPU: removed 40 seeded pipelines from local recording')
        add(f"Native GPU: startup pipelines loaded={o.get('L', 400)} compiled={o.get('C', 72)} failed={o.get('F', 0)} "
            f"resident={o.get('R', 472)} elapsed_ms={o.get('E', 1800)}")
    else:
        add('Native GPU: no startup pipeline recipes yet; recording during gameplay')
    add(f'Native GPU [{fp}]: D3D12 ready on \'NVIDIA GeForce MX570\' (2240x1294, 3 images)')
    add('Native GPU: shader not present in AOT cache, hash=0xA58EBA123EFB541C', 'warning', 200)
    for w in o.get('warns', []):
        add(w, 'warning', 200)
    add('Native GPU PSO stats, last 10 s: 1700 frames, 170.0 fps, worst 85.2 ms, 3 hitches, 12 compile frames; 30 compiles, '
        '410.5 ms (380.1 ms blocking), 30 misses, 900 hits, 0 skipped draws')
    add('Native GPU: pipeline cache saved, 120 new pipelines, 20971520 bytes', t=300)
    if o.get('gave_up'):
        add('Native GPU: unlocked pipeline cache save gave up after 3 passes; saving under the lock', 'warning', 300)
    if o.get('bad_write'):
        add('Native GPU: could not write pipeline cache X:\\cache\\native-pso.bin.tmp', 'warning', 300)
        add('Native GPU: could not replace pipeline cache X:\\cache\\native-pso.bin: access denied', 'warning', 300)
        add('Native GPU: pipeline cache save postponed; 123 bytes unavailable', 'warning', 300)
        add('Native GPU: Serialize failed E_INVALIDARG', 'warning', 300)
        add('Native GPU: could not save startup pipeline recipes X:\\cache\\native-pso-recipes.bin', 'warning', 300)
        add('Native GPU: could not enumerate startup seed directory X:\\seeds: not found', 'warning', 300)
        add('Native GPU: ignoring invalid or incompatible pipeline recipes X:\\cache\\native-pso-recipes.bin', 'warning', 300)
        add('Native GPU: pipeline cache unavailable (0x80004005)', 'warning', 300)
        add('Native GPU: startup pipeline preparation disabled by LEGO_NATIVE_PSO_PRECOMPILE=0')
        add('Native GPU: pipeline cache disabled by LEGO_NATIVE_PSO_CACHE=0')
        add('Native GPU: pipeline cache skipped while a capture layer is active')
    # an on-request block first: the exit / trigger block must win
    if o.get('reason', 'exit'):
        add('Native GPU PSO stats (request): 100 frames over 1.0 s')
        add('PSO startup: cache new (no usable file), file 0 bytes, read 0.0 ms, library create 1.0 ms')
        add('PSO frames: 100 at 100.0 fps, worst 999.0 ms; <=16.7 ms 1, <=33.3 0, <=50 0, <=100 0, <=250 0, >250 0; hitches of 50 ms or more '
            '999, frames with 4 ms or more of blocking compiles 0, both 0')
    add('Native GPU: saved 472 startup pipeline recipes', t=300)
    stop = o.get('stop', True)
    if stop:
        add('Native GPU: pipeline cache saved, 3 new pipelines, 21000000 bytes', t=300)
        add('Native GPU: pipeline cache hits=900 misses=30 stored=30 saves=2')
    if o.get('late_save'):
        add('Native GPU: pipeline cache saved, 1 new pipelines, 21000100 bytes', t=300)
    h = o.get('H', 40)
    reason = o.get('reason', 'exit')
    if reason:
        add(f"Native GPU PSO stats ({reason}): 29000 frames over 290.0 s")
    else:
        add('Window closing, shutting down...')
        add('Title terminated; hard-exiting process.')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'w', encoding='utf-8', newline='\r\n').write('\n'.join(L) + '\n')
        return
    add(f"PSO startup: cache {'loaded' if warm else 'new (no usable file)'}, file {31457280 if warm else 0} bytes, read 12.5 ms, "
        "library create 30.2 ms")
    if warm:
        add(f"PSO startup preparation: loaded {o.get('L', 400)}, compiled {o.get('C', 72)}, failed {o.get('F', 0)}, resident "
            f"{o.get('R', 472)}, threads {o.get('threads', 1)}, {o.get('E', 1800)}.0 ms (library loads 300.0 ms, compiles 1400.0 ms, "
            "worst compile 60.0 ms)")
    add(f"PSO lookups: 50000 (warm 49000, library 500, miss 500), avg 0.004 ms, worst 30.123 ms; mutex wait {o.get('MW', 120.0)} ms in "
        f"total, worst {o.get('MWW', 25.0)} ms, 7 waits of 1 ms or more; library loads 500, avg 0.300 ms, worst 4.000 ms")
    add('PSO compiles: 500 taking 6500.0 ms (avg 13.00 ms, worst 300.0 ms); <1 ms 10, 1-4 100, 4-16 200, 16-64 150, 64-256 39, >=256 1; '
        'untimed stores 0; store() avg 0.120 ms, worst 9.000 ms')
    ac = o.get('async_n', 0)
    add(f'PSO compiles by thread: present {500 - ac} ({6500 - ac * 10}.0 ms), async {ac} ({ac * 10}.0 ms), other 0 (0.0 ms)')
    add(f"PSO auxiliary: {o.get('AUX', 12)} requests, 0 library hits, {o.get('AUX', 12)} compiles, 0 failed, 900.0 ms compiling, "
        "worst 400.0 ms")
    held, copy = (5.0, 40.0) if o.get('unl') else (45.0, 40.0)
    add(f"PSO saves: 2 written (41971520 bytes), {o.get('SF', 0)} failed, 0 postponed; mutex held {held} ms in total, worst {held} ms; "
        f"copy {copy} ms, allocation outside the mutex 3.0 ms, write 20.0 ms; {1 if o.get('unl') else 0} retries, 0 allocations under the mutex")
    if ac:
        add(f"PSO async: {ac} posted, {ac} ready, {o.get('AF', 0)} failed, 25 skipped draws, 4 waits (6.0 ms), 2 timeouts")
    add(f'PSO frames: 29000 at 100.0 fps, worst 1130.0 ms; <=16.7 ms 25000, <=33.3 2500, <=50 1000, <=100 400, <=250 90, >250 10; '
        f'hitches of 50 ms or more {h}, frames with 4 ms or more of blocking compiles 120, both {h // 2}')
    add('PSO minute    #: frames    fps worst_ms hitch cfrm  comp  comp_ms block_ms  miss   hits  skip')
    add('PSO minute    0:  10000  166.7    120.5   10   40   100   1300.0   1200.0   100  10000     0')
    add('PSO minute    4:   5000   83.3   1130.0   30   80   400   5200.0   5000.0   400  39000    25 (partial)')
    if not stop:
        add('Window closing, shutting down...')
        add('Title terminated; hard-exiting process.')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8', newline='\r\n').write('\n'.join(L) + '\n')


def fx_run(d, kind, rj_over=None, p99=60.0, fps=100.0, low=12.0, **o):
    os.makedirs(d, exist_ok=True)
    fx_log(os.path.join(d, 'game.log'), kind, **o)
    rj = {'exit_code': 0, 'exit_code_hex': '0x00000000', 'exited_early': False, 'wer_seen': False, 'crash_events': [], 'dumps': [],
          'close_method': 'wm_close', 'close_seconds': 3.1, 'desktop': 'Default', 'elapsed_s': 303.0,
          'input_script': {'steps_done': 55, 'steps_total': 91, 'last_step': 'halted', 'timeouts': 0, 'error': None}}
    rj.update(rj_over or {})
    json.dump(rj, open(os.path.join(d, 'run.json'), 'w', encoding='utf-8'))
    json.dump({'first_frame_s': 5.0, 'frames': {'fps_mean': fps, 'p99_ms': p99, 'fps_1pct_low': low, 'hitches_over_50ms': 500}},
              open(os.path.join(d, 'summary.json'), 'w', encoding='utf-8'))
    return d


def selftest(sd, smoke, out=None):
    os.makedirs(sd, exist_ok=True)
    fx = os.path.join(sd, 'fixtures')
    lines, ok_all = [], True

    def expect(label, mode, specs, want_rc, must=(), must_not=(), n2=False):
        nonlocal ok_all
        R, rc = analyse(mode, specs, '39129c4c059be5f0', n2)
        txt = '\n'.join(R.out) + '\n'
        open(os.path.join(sd, f'{label}.txt'), 'w', encoding='utf-8').write(txt)
        miss = [m for m in must if m not in txt]
        bad = [m for m in must_not if m in txt]
        ok = rc == want_rc and not miss and not bad
        ok_all &= ok
        lines.append(f"{'ok ' if ok else 'BAD'} {label}: rc {rc} (want {want_rc}); {R.out[-1][:300]}"
                     + (f'\n    missing expected text: {miss}' if miss else '') + (f'\n    unexpected text: {bad}' if bad else ''))

    # rows, all good
    R0 = os.path.join(fx, 'rows-good')
    good = {
        's0-ref-cold': dict(), 'c-pso-t1': dict(), 'c-pso-unl': dict(unl=True),
        'w-ref-t1': dict(warm=True, seed=True), 'w-pso-t1': dict(warm=True, seed=True),
        'w-ref-t4': dict(warm=True, threads=4, seed=True, E=900), 'w-pso-t2': dict(warm=True, threads=2, seed=True, L=410, C=62, E=1200),
        'w-pso-t4': dict(warm=True, threads=4, seed=True, E=900), 'w-pso-unl': dict(warm=True, unl=True, seed=True),
    }
    specs = [(n, fx_run(os.path.join(R0, n), n, **o)) for n, o in good.items()]
    expect('rows-good', 'rows', specs, 0, must=('RESULT: PASS', 'PASS w-pso-t2 loaded+compiled == w-pso-t1',
                                                'PASS w-pso-unl reload of the c-pso-unl cache'), must_not=('FAIL ',))
    # rows, real-life exits: the close watchdog hard-exits (no Stop, no exit summary) ...
    for label, reason, must in (('rows-hardexit', None, ('CHECK s0-ref-cold PSO summary block', 'INFO w-pso-unl Stop(): not reached',
                                                         'RESULT: PASS-WITH-CHECKS')),
                                # ... or the runner touched cache\pso-stats.now before close
                                ('rows-trigger', 'pso-stats.now', ('PASS w-pso-t4 PSO summary block: used pso-stats.now',
                                                                   "PASS w-pso-t4 PSO summary reason: 'pso-stats.now'",
                                                                   "INFO w-pso-t4 PSO summary used: reason 'pso-stats.now'",
                                                                   'INFO c-pso-unl Stop(): not reached'))):
        RD = os.path.join(fx, label)
        specs = [(n, fx_run(os.path.join(RD, n), n, stop=False, reason=reason, **o)) for n, o in good.items()]
        expect(label, 'rows', specs, 0, must=must, must_not=('FAIL ',))
    # rows, bad: wrong L+C at t2, gave-up + write errors on unl, late save after Stop, missing arm, new hard warning, wrong fp
    R1 = os.path.join(fx, 'rows-bad')
    bad = dict(good)
    bad['w-pso-t2'] = dict(warm=True, threads=2, L=300, C=60, R=360)
    bad['c-pso-unl'] = dict(unl=True, gave_up=True, bad_write=True, late_save=True, SF=1)
    bad['w-pso-t4'] = dict(warm=True, threads=1, warns=['Native GPU: draw invalidated by failed draw 12'])
    bad['w-ref-t1'] = dict(warm=True, seed=True, fp='1616ce65e973c583', rejected=True)
    bad['c-pso-t1'] = dict(reason='request', stop=False)   # only an on-request summary: wrong reason (hard)
    del bad['w-pso-unl']
    specs = [(n, fx_run(os.path.join(R1, n), n, **o)) for n, o in bad.items()]
    specs.append(('w-pso-unl', os.path.join(R1, 'does-not-exist')))
    specs.append(('extra-arm', os.path.join(R1, 's0-ref-cold')))
    expect('rows-bad', 'rows', specs, 1,
           must=('FAIL arm w-pso-unl missing', 'FAIL w-pso-t2 loaded+compiled == w-pso-t1', 'FAIL c-pso-unl no cache write/replace',
                 'FAIL c-pso-unl no cache save after Stop', 'FAIL c-pso-unl PSO saves failed = 0', "FAIL w-pso-t4 'uses 4 threads' line",
                 'FAIL w-pso-t4 no new hard WARN', 'FAIL w-ref-t1 fingerprint', 'FAIL w-ref-t1 warm cache accepted',
                 "FAIL c-pso-t1 PSO summary reason: 'request'", "INFO c-pso-t1 PSO summary used: reason 'request'",
                 'INFO extra arm extra-arm', 'RESULT: FAIL'))
    # ab, all good
    A0 = os.path.join(fx, 'ab-good')
    specs = []
    for n in AB_ARMS:
        t = n.split('-')[0]
        o = dict(warm=t in ('w0', 'w1', 'w2'), async_on=t in ('c1', 'w1'), threads=4 if t == 'w2' else 1,
                 async_n=60 if t in ('c1', 'w1') else 0, H={'c0': 200, 'c1': 60, 'w0': 80, 'w1': 30, 'w2': 80}.get(t, 220),
                 E=1500 if t == 'w2' else 2500)
        specs.append((n, fx_run(os.path.join(A0, n), n, p99=90.0 if t == 'c0' else 50.0, **o)))
    expect('ab-good', 'ab', specs, 0, must=('MEETS the #35 rule', 'C1 beats C0', 'delta C1 vs C0', 'RESULT: PASS'))
    # ab, bad: async failed, warm rejected, missing arms
    A1 = os.path.join(fx, 'ab-bad')
    specs2 = [s for s in specs if s[0] not in ('c1-2', 'w0-3', 'w2-2')]
    specs2.append(('c1-2', fx_run(os.path.join(A1, 'c1-2'), 'c1-2', async_on=True, async_n=50, AF=2)))
    specs2.append(('w0-3', fx_run(os.path.join(A1, 'w0-3'), 'w0-3', warm=True, rejected=True, F=3,
                                  rj_over={'exit_code': 3221225477, 'exit_code_hex': '0xC0000005', 'wer_seen': True})))
    expect('ab-bad', 'ab', specs2, 1, must=('FAIL arm w2-2 missing', 'FAIL c1-2 async failed = 0', 'FAIL w0-3 warm cache accepted',
                                             'FAIL w0-3 warm startup failed = 0', 'FAIL w0-3 clean exit', 'RESULT: FAIL'))
    # ab --n2: prime + K = 1..2, no W2 -> PASS; the skipped arms are not reported ...
    specs3 = [s for s in specs if s[0] not in N2_SKIP]
    expect('ab-n2', 'ab', specs3, 0, n2=True,
           must=('mode ab (n2: K = 1..2, no W2)', '== delta W2 vs W0: not run (n2)', 'INFO W2 parallel replay: not run (n2)',
                 'MEETS the #35 rule', 'RESULT: PASS'),
           must_not=('FAIL ', 'c0-3', 'w2-1', 'w2-2'))
    # ... and if present anyway they are INFO and ignored
    expect('ab-n2-extra', 'ab', specs3 + [s for s in specs if s[0] in ('c0-3', 'w2-1')], 0, n2=True,
           must=('INFO extra arm c0-3: present but not expected with --n2; ignored',
                 'INFO extra arm w2-1: present but not expected with --n2; ignored', 'RESULT: PASS'), must_not=('FAIL ',))
    # usage errors
    for bad_arm in (['noequals'], ['a=x', 'a=y']):
        try:
            parse_arms(bad_arm); lines.append(f'BAD usage {bad_arm}: accepted'); ok_all = False
        except ValueError as e:
            lines.append(f'ok  usage {bad_arm}: {e}')
    # the real smoke run (STATS off): PSO lines missing, no crash
    if smoke and os.path.isdir(smoke):
        expect('smoke-rows', 'rows', [('s0-ref-cold', smoke)], 1,
               must=('FAIL s0-ref-cold PSO stats lines', 'PASS s0-ref-cold clean exit', 'PASS s0-ref-cold fingerprint',
                     'PASS s0-ref-cold cold confirmed', 'FAIL arm c-pso-t1 missing'))
        expect('smoke-ab', 'ab', [('prime', smoke)], 1, must=('FAIL prime PSO stats lines', 'FAIL arm c0-1 missing'))
    else:
        lines.append(f'BAD smoke dir not found: {smoke}'); ok_all = False
    unmatched = [k for k in RX if not MATCHED[k]]
    lines.append(f"regex coverage: {len(RX) - len(unmatched)}/{len(RX)} matched at least once" +
                 (f'; UNMATCHED {unmatched}' if unmatched else ''))
    ok_all &= not unmatched
    lines.append('RESULT: selftest ' + ('ok' if ok_all else 'FAILED'))
    txt = '\n'.join(lines) + '\n'
    open(os.path.join(sd, 'selftest.txt'), 'w', encoding='utf-8').write(txt)
    if out:
        od = os.path.dirname(os.path.abspath(out))
        os.makedirs(od, exist_ok=True)
        open(out, 'w', encoding='utf-8').write(txt)
    print(txt, end='')
    return 0 if ok_all else 1


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--mode', choices=['rows', 'ab'])
    ap.add_argument('--arm', action='append', default=[])
    ap.add_argument('--expect-fp')
    ap.add_argument('--out')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--n2', action='store_true', help='ab only: K = 1..2, no W2 (c0-3 c1-3 w0-3 w1-3 w2-1 w2-2 not expected)')
    ap.add_argument('--selftest-dir', default=os.path.join(here, 'selftest'))
    ap.add_argument('--smoke', default=os.path.join(os.path.dirname(here), 'smoke4bp', 'runs', '20261125-174131-smoke-4bp'))
    a = ap.parse_args()   # argparse exits 2 on a usage error
    if a.selftest:
        return selftest(a.selftest_dir, a.smoke, a.out)
    if not a.mode or not a.out or not a.expect_fp:
        ap.print_usage(sys.stderr); print('pso_post.py: --mode, --expect-fp and --out are required', file=sys.stderr)
        return 2
    if not re.fullmatch(r'[0-9a-f]{16}', a.expect_fp):
        print(f'pso_post.py: --expect-fp {a.expect_fp!r} is not 16 lower-case hex digits', file=sys.stderr)
        return 2
    try:
        specs = parse_arms(a.arm)
    except ValueError as e:
        print(f'pso_post.py: {e}', file=sys.stderr)
        return 2
    if a.n2 and a.mode != 'ab':
        print('pso_post.py: --n2 is only valid with --mode ab', file=sys.stderr)
        return 2
    R, rc = analyse(a.mode, specs, a.expect_fp, a.n2)
    od = os.path.dirname(os.path.abspath(a.out))
    os.makedirs(od, exist_ok=True)
    open(a.out, 'w', encoding='utf-8').write('\n'.join(R.out) + '\n')
    print('\n'.join(R.out))
    return rc


if __name__ == '__main__':
    sys.exit(main())

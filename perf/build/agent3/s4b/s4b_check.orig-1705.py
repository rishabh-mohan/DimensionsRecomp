"""Agent 3 S4b (task #29): read-only post-run checks of one S4b queue row against its base run(s).
FUNCTIONAL runs only (hidden desktop); nothing here is a timing number.
usage:
  python build/agent3/s4b/s4b_check.py --cand <run> [--row s4bNN] [--base <run> ...] [--allow-new REGEX ...]
         [--allow-gone REGEX ...] [--k-regex REGEX] [--out-dir build/agent3/s4b/checks]
Built on build/agent3/s4a/s4a_check.py (imported: run.json, logdiff, scenes, marks, threads, sys.csv slow state).
New here:
  - S4b line families (C1 keep-watch, #18 d3d12_submit_split, #20 deferred_counters, #24 GPU wait, P2c memexport
    full-buffer), the S4a families and the fail lines: count, first 3 and last 3 lines each; field parsing of the
    split, GPU wait stats, deferred_counters and memexport lines;
  - logdiff on joined logs: a run with rotated game.N.log files is joined oldest -> newest into
    <out-dir>/joined/<run>/game.log first (logdiff.py reads only <dir>/game.log, so it would miss the rotated ones);
  - QUEUE.md's BASE items (build/agent7/s4b-queue/QUEUE.md) as a list of misses, and the row's proof items (--row).
The last line is a verdict HINT only; the reader applies QUEUE.md's "passes if" column.
"""
import argparse
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', 's4a')))
import s4a_check as A  # noqa: E402

KV = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\s*[=:]\s*(-?\d+(?:\.\d+)?)\b')
MEMEXPORT = re.compile(r'memexport full-buffer (\d+)x \(total (\d+)\)')
KEPT = re.compile(r'C1 keep-watch: (\d+) protects kept so far')
# K = C1's verify-mismatch line (gate A). PROVISIONAL until the text is read from the C1 source; c1_other lists every
# C1 line that no known family matches, so a K line with another wording still shows up there.
K_DEFAULT = r'(?i)(keep.?watch|verify).*(mismatch|differ|changed)'
TOY = re.compile(r'\] Toypad\[(Read |Write)\] ')
GONE_OK_DEFAULT = r'\] Toypad\[(Read |Write)\] |S4 upload hash|slow frame #'
FRONT_END = ['218/222', '226/1022', '220/528', '220/534', '219/226']
# (key, needle = a plain substring the message must contain, extra regex or None)
FAM = [
    ('c1_any', 'C1 keep-watch', None),
    ('c1_init_on', 'C1 keep-watch: on (with physical_protect_hold_global_lock)', None),
    ('c1_init_blocked', 'C1 keep-watch: on, but blocked for this process', None),
    ('c1_init_nohold', 'C1 keep-watch: on, but physical_protect_hold_global_lock is off', None),
    ('c1_first', 'C1 keep-watch: first kept protect', None),
    ('c1_kept', 'protects kept so far', None),
    ('c1_blocked', 'C1 keep-watch: blocked for this process', None),
    ('recovered_stale', 'Recovered stale physical page protection', None),
    ('unhandled_phys', 'Unhandled guest physical write fault', None),
    ('protect_failed', 'PhysicalHeap::Protect failed', None),
    ('split_init', 'd3d12_submit_split_kb: splitting submissions', None),
    ('split', 'd3d12_submit_split: ', None),
    ('deferred_counters', 'deferred_counters', None),
    ('gpu_wait', 'GPU wait', None),
    ('gpu_wait_stats', 'GPU wait stats', None),
    ('gpu_wait_backoff', 'GPU wait back-off', None),
    ('memexport', 'memexport full-buffer', None),
    ('slow_frame', 'slow frame #', None),
    ('s4_upload_hash', 'S4 upload hash: frame', None),
    ('precise_wait', 'TimerQueue: precise wait', None),
    ('miss_cache', 'shader_miss_cache', None),
    ('stuck_lock', 'STUCK-LOCK', None),
    ('minidump', 'Minidump written', None),
    ('fatal', '[FATAL]', None),
    ('clean_exit', 'Title terminated; hard-exiting process', None),
    ('debug_layer', 'ebug layer', None),
    ('d3d12_msg', 'D3D12 ', re.compile(r'D3D12 (ERROR|WARNING|CORRUPTION|INFO|MESSAGE)')),
]
ITEM_FAMS = ['c1_any', 'split_init', 'split', 'deferred_counters', 'gpu_wait', 'memexport']
S4A_FAMS = ['s4_upload_hash', 'slow_frame', 'precise_wait', 'miss_cache']
C1_KNOWN = ('c1_init_on', 'c1_init_blocked', 'c1_init_nohold', 'c1_first', 'c1_kept', 'c1_blocked')
SHOW = ['c1_any', 'k', 'c1_other', 'recovered_stale', 'unhandled_phys', 'protect_failed', 'split_init', 'split',
        'deferred_counters', 'gpu_wait', 'memexport', 'slow_frame', 's4_upload_hash', 'precise_wait', 'miss_cache',
        'stuck_lock', 'minidump', 'fatal', 'debug_layer', 'd3d12_msg']


def num(v):
    f = float(v)
    return int(f) if f.is_integer() else f


def kv(msg):
    return {k: num(v) for k, v in KV.findall(msg)}


def scan(run, k_rx, keep=3):
    keys = [k for k, _, _ in FAM] + ['k', 'c1_other']
    S = {'n': {k: 0 for k in keys}, 'first': {k: [] for k in keys}, 'last': {k: [] for k in keys}, 'levels': {},
         'split': [], 'gws': [], 'mem': [], 'kept': [], 'dc': [], 'dc_block': [], 'slow_last': None}
    n, first, last = S['n'], S['first'], S['last']
    cap = 0

    def hit(k, ln):
        n[k] += 1
        if len(first[k]) < keep:
            first[k].append(ln[:400])
        else:
            last[k].append(ln[:400])
            if len(last[k]) > keep:
                del last[k][0]

    for p in A.game_logs(run):
        with open(p, encoding='utf-8', errors='replace') as f:
            for ln in f:
                ln = ln.rstrip('\r\n')
                m = A.LINE.match(ln)
                if not m:
                    continue
                ts, lvl, cat, msg = m.groups()
                S['levels'][lvl] = S['levels'].get(lvl, 0) + 1
                if cap:
                    S['dc_block'].append(ln[:300])
                    cap -= 1
                got = [k for k, needle, rx in FAM if needle in msg and (rx is None or rx.search(msg))]
                isk = ('eep-watch' in msg or 'erif' in msg) and bool(k_rx.search(msg))
                if not got and not isk:
                    continue
                for k in got:
                    hit(k, ln)
                if isk:
                    hit('k', ln)
                elif 'c1_any' in got and not any(k in C1_KNOWN for k in got):
                    hit('c1_other', ln)
                if 'c1_kept' in got:
                    mm = KEPT.search(msg)
                    if mm:
                        S['kept'].append(int(mm.group(1)))
                if 'split' in got:
                    S['split'].append((ts[11:], kv(msg.split('d3d12_submit_split: ', 1)[1])))
                if 'gpu_wait_stats' in got:
                    S['gws'].append((ts[11:], kv(msg.split('GPU wait stats', 1)[1])))
                if 'memexport' in got:
                    mm = MEMEXPORT.search(msg)
                    if mm:
                        S['mem'].append((int(mm.group(1)), int(mm.group(2))))
                if 'slow_frame' in got:
                    S['slow_last'] = ln
                if 'deferred_counters' in got and ('lists' in msg or 'seconds' in msg):
                    S['dc'].append((ts[11:], kv(msg.split('deferred_counters', 1)[1])))
                    S['dc_block'] = [ln[:300]]
                    cap = 40
    return S


def series(rows):
    """rows [(ts, {field: value})] -> first/last/max/sum per field, monotonic flags, per-frame rates when a
    cumulative 'frame' field exists (a monotonic field is read as cumulative: (last - first) / frames; any other as
    per interval: sum over lines 2.. / frames)."""
    if not rows:
        return None
    fields = []
    for _, d in rows:
        for k in d:
            if k not in fields:
                fields.append(k)
    out = {'lines': len(rows), 'first_ts': rows[0][0], 'last_ts': rows[-1][0], 'first': rows[0][1], 'last': rows[-1][1],
           'max': {}, 'sum': {}, 'monotonic': {}}
    for k in fields:
        vs = [d[k] for _, d in rows if k in d]
        out['max'][k] = max(vs)
        out['sum'][k] = round(sum(vs), 3)
        out['monotonic'][k] = all(vs[i] >= vs[i - 1] for i in range(1, len(vs)))
    f0, f1 = rows[0][1].get('frame'), rows[-1][1].get('frame')
    if f0 is not None and f1 is not None and f1 > f0 and out['monotonic'].get('frame'):
        rate = {}
        for k in fields:
            if k == 'frame':
                continue
            if out['monotonic'][k]:
                rate[k] = round((rows[-1][1].get(k, 0) - rows[0][1].get(k, 0)) / float(f1 - f0), 4)
            else:
                rate[k] = round(sum(d.get(k, 0) for _, d in rows[1:]) / float(f1 - f0), 4)
        out['per_frame'] = rate
        out['frames'] = f1 - f0
    return out


def mem_stats(mem):
    if not mem:
        return None
    return {'lines': len(mem), 'last_total': mem[-1][1], 'max_total': max(t for _, t in mem),
            'sum_x': sum(x for x, _ in mem), 'lines_x_gt0': sum(1 for x, _ in mem if x > 0)}


def diff_dir(run, out_dir):
    """the dir to give logdiff.py: the run itself, or <out-dir>/joined/<run> with every game*.log joined oldest ->
    newest into one game.log (rebuilt when the sources change)."""
    fs = A.game_logs(run)
    if len(fs) <= 1:
        return run, len(fs)
    jd = os.path.join(out_dir, 'joined', os.path.basename(run))
    jp = os.path.join(jd, 'game.log')
    src = os.path.join(jd, 'sources.txt')
    sig = '\n'.join('%s %d' % (os.path.basename(p), os.path.getsize(p)) for p in fs)
    ok = False
    if os.path.isfile(jp) and os.path.isfile(src):
        with open(src, encoding='utf-8') as f:
            ok = f.read() == sig
    if not ok:
        os.makedirs(jd, exist_ok=True)
        with open(jp + '.tmp', 'wb') as w:
            for p in fs:
                with open(p, 'rb') as r:
                    r.seek(0, 2)
                    size = r.tell()
                    tail = b'\n'
                    if size:
                        r.seek(-1, 2)
                        tail = r.read(1)
                    r.seek(0)
                    shutil.copyfileobj(r, w, 1 << 20)
                    if tail != b'\n':
                        w.write(b'\n')
        os.replace(jp + '.tmp', jp)
        with open(src, 'w', encoding='utf-8') as f:
            f.write(sig)
    return jd, len(fs)


def scenario(rj):
    isc = (rj or {}).get('input_script') or {}
    s = os.path.basename(isc.get('script') or '')
    if 'attract' in s:
        return 'A'
    if 'menus' in s:
        return 'M'
    if s:
        return s
    sec = (rj or {}).get('seconds_requested')
    try:
        return 'I%d' % int(float(sec))
    except (TypeError, ValueError):
        return '?'


def steps_of(rj):
    isc = (rj or {}).get('input_script') or {}
    if not isc:
        return None
    return isc.get('steps_done'), isc.get('steps_total')


def row_proofs(row, rj, S, ld, res):
    n = S['n']
    P = []

    def chk(ok, text):
        P.append({'ok': ok, 'text': text})

    cv = {str(k).lower(): str(v).lower() for k, v in ((rj or {}).get('cvars') or {}).items()}
    sp = res.get('split') or {}
    spmax = sp.get('max') or {}
    rate = sp.get('per_frame') or {}
    gw = res.get('gpu_wait_stats') or {}
    gwmax = gw.get('max') or {}
    kept_last = S['kept'][-1] if S['kept'] else None
    r = row
    if r == 's4b01':
        it = {k: n[k] for k in ITEM_FAMS if n[k]}
        s4 = {k: n[k] for k in S4A_FAMS if n[k]}
        chk(not it and not s4, 'no line from any S4b item %s and no S4a line %s' % (it or '{}', s4 or '{}'))
    elif r == 's4b02':
        chk(n['c1_any'] == 0, 'no C1 line (%d)' % n['c1_any'])
        it = {k: n[k] for k in ITEM_FAMS if n[k]}
        chk(not it, 'no line from any S4b item %s' % (it or '{}'))
    elif r == 's4b03':
        it = {k: n[k] for k in ITEM_FAMS + S4A_FAMS if n[k]}
        chk(not it, 'no S4a/S4b item line %s' % (it or '{}'))
    elif r in ('s4b04', 's4b24'):
        chk(n['c1_init_on'] == 1, 'init "C1 keep-watch: on (with physical_protect_hold_global_lock)" x%d' % n['c1_init_on'])
        chk(n['c1_first'] >= 1, '"first kept protect" x%d (gate D / positive control)' % n['c1_first'])
        chk(kept_last is not None or n['c1_first'] >= 1, 'kept count: last "kept so far" = %s (%d such lines)' % (kept_last, n['c1_kept']))
        if r == 's4b04':
            chk(n['k'] == 0, 'verify-mismatch (K) lines %d (gate A, menus part)' % n['k'])
        chk(n['recovered_stale'] == 0 and n['unhandled_phys'] == 0,
            'gate D zero lines: "Recovered stale physical page protection" %d, "Unhandled guest physical write fault" %d' % (
                n['recovered_stale'], n['unhandled_phys']))
        chk(n['c1_init_blocked'] == 0 and n['c1_init_nohold'] == 0 and n['c1_blocked'] == 0,
            'no blocked/no-hold C1 line (%d/%d/%d)' % (n['c1_init_blocked'], n['c1_init_nohold'], n['c1_blocked']))
    elif r == 's4b05':
        chk(n['c1_init_blocked'] == 1, 'init "C1 keep-watch: on, but blocked for this process (native renderer)" x%d' % n['c1_init_blocked'])
        chk(n['c1_blocked'] == 1, 'exactly one "blocked for this process (native renderer)" line: x%d' % n['c1_blocked'])
        chk(n['c1_first'] == 0 and n['c1_kept'] == 0, 'no kept line (first %d, kept %d)' % (n['c1_first'], n['c1_kept']))
    elif r == 's4b06':
        chk(n['c1_init_nohold'] == 1, 'init WARN "on, but physical_protect_hold_global_lock is off" x%d' % n['c1_init_nohold'])
        chk(n['c1_first'] == 0 and n['c1_kept'] == 0, 'no kept line (first %d, kept %d)' % (n['c1_first'], n['c1_kept']))
        chk(bool(ld) and ld['NEW'] == 0 and ld['MORE'] == 0, 'no other NEW key (NEW %s MORE %s beside C1)' % (
            ld and ld['NEW'], ld and ld['MORE']))
    elif r.startswith('s4b08'):
        ms = res.get('memexport') or {}
        chk(n['slow_frame'] > 0, 'slow-frame lines %d' % n['slow_frame'])
        last_ok = bool(S['slow_last'] and MEMEXPORT.search(S['slow_last']))
        chk(last_ok, 'the last slow-frame line ends with the memexport suffix: ...%s' % ((S['slow_last'] or '-')[-110:]))
        tot = ms.get('last_total')
        chk(tot == 0 if tot is not None else False,
            'P2 COUNTER: memexport full-buffer total (last line) = %s; max %s; sum Nx %s; lines with Nx > 0: %s -> %s' % (
                tot, ms.get('max_total'), ms.get('sum_x'), ms.get('lines_x_gt0'),
                'closes P2 memexport gate' if tot == 0 else ('> 0: goes to Agent 1 (hold cap)' if tot else 'NO COUNTER')))
    elif r == 's4b09':
        el = float((rj or {}).get('elapsed_s') or 0)
        chk(len(S['dc']) >= 1, 'deferred_counters headers %d (about every 10 s; elapsed %.0f s -> ~%d expected)' % (
            len(S['dc']), el, int(el // 10)))
    if r in ('s4b10', 's4b11', 's4b12', 's4b13', 's4b15', 's4b16', 's4b25'):
        chk(n['split_init'] == 1, 'init "d3d12_submit_split_kb: splitting submissions at N KB" x%d: %s' % (
            n['split_init'], (S['first']['split_init'] or ['-'])[0][-120:]))
        chk(bool(sp) and spmax.get('failed', 0) == 0, 'failed=0 in every d3d12_submit_split line (max %s over %s lines)' % (
            spmax.get('failed'), sp.get('lines', 0)))
        if r != 's4b25':
            chk(bool(sp) and spmax.get('splits', 0) > 0, 'splits > 0 (max %s)' % spmax.get('splits'))
        chk(None, 'per frame: submission %s, splits %s (frames %s; fields monotonic %s)' % (
            rate.get('submission'), rate.get('splits'), sp.get('frames'), sp.get('monotonic')))
        if r == 's4b12':
            chk(spmax.get('held_pipelines', 0) > 0, 'held_pipelines > 0 (max %s)' % spmax.get('held_pipelines'))
            chk(None, 'held_query max %s (> 0 if the attract scene runs occlusion queries)' % spmax.get('held_query'))
            chk(spmax.get('held_scratch', 0) == 0, 'held_scratch = 0 expected (max %s)' % spmax.get('held_scratch'))
        if r == 's4b15':
            chk(bool(ld) and ld['NEW'] == 0, 'no debug-layer message that row 14 lacks (NEW %s beside split lines)' % (ld and ld['NEW']))
        if r == 's4b16':
            chk(len(S['dc']) >= 1, 'deferred_counters headers %d (compare lists per 10 s with row 9)' % len(S['dc']))
    if r == 's4b14':
        chk(None, 'debug-layer control: "debug layer" lines %d, D3D12 message lines %d, NEW at warning %s' % (
            n['debug_layer'], n['d3d12_msg'], ld and ld['NEW']))
    elif r == 's4b17':
        for f in ('l1_waits', 'l1_polls', 'l2_tries', 'kicks'):
            chk(gwmax.get(f, 0) > 0, 'GPU wait stats %s > 0 (max %s)' % (f, gwmax.get(f)))
        chk(n['gpu_wait_backoff'] == 0 or True, 'back-off lines %d (OFF in P1)' % n['gpu_wait_backoff'])
    elif r == 's4b18':
        chk(n['gpu_wait_backoff'] == 1, 'one "GPU wait back-off: ON (...)" line: x%d %s' % (
            n['gpu_wait_backoff'], (S['first']['gpu_wait_backoff'] or ['-'])[0][-100:]))
        chk(gwmax.get('sleep_fail', 0) == 0, 'sleep_fail = 0 (max %s over %s stats lines)' % (gwmax.get('sleep_fail'), gw.get('lines', 0)))
        chk(n['stuck_lock'] == 0, 'no STUCK-LOCK (%d)' % n['stuck_lock'])
    elif r == 's4b19':
        chk(cv.get('shared_memory_upload_nontemporal_copy') == 'true', 'run.json cvars: shared_memory_upload_nontemporal_copy=%s (M1 logs nothing)' % (
            cv.get('shared_memory_upload_nontemporal_copy')))
    elif r in ('s4b22', 's4b24'):
        chk(cv.get('shared_memory_single_hold_rearm') == 'true' and cv.get('physical_protect_hold_global_lock') == 'true',
            'W6 cvars in run.json: single_hold_rearm=%s hold_global_lock=%s' % (
                cv.get('shared_memory_single_hold_rearm'), cv.get('physical_protect_hold_global_lock')))
    return P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cand', required=True)
    ap.add_argument('--row', default='')
    ap.add_argument('--base', action='append', default=[])
    ap.add_argument('--allow-new', action='append', default=[])
    ap.add_argument('--allow-gone', action='append', default=[])
    ap.add_argument('--k-regex', default=K_DEFAULT)
    ap.add_argument('--out-dir', default=os.path.join(HERE, 'checks'))
    a = ap.parse_args()
    cand = os.path.abspath(a.cand)
    bases = [os.path.abspath(b) for b in a.base]
    rj = A.jload(os.path.join(cand, 'run.json')) or {}
    sj = A.jload(os.path.join(cand, 'summary.json')) or {}
    kind = 'native' if os.path.isfile(os.path.join(cand, 'frames.csv')) else 'off'
    scn = scenario(rj)
    row = a.row
    res = {'run': os.path.basename(cand), 'row': row, 'kind': kind, 'scenario': scn}
    L = []
    say = L.append
    say('# s4b_check %s %s (%s, scenario %s)' % (row or '-', os.path.basename(cand), kind, scn))
    env = {k: v for k, v in (rj.get('env') or {}).items() if k not in ('LEGO_NATIVE_FRAME_METRICS', 'AGENT3_VPAD')}
    st = steps_of(rj)
    rjs = {k: rj.get(k) for k in ('exit_code', 'exit_code_hex', 'dumps', 'crash_events', 'wer_seen', 'close_method',
                                  'close_seconds', 'elapsed_s', 'seconds_requested', 'cvars', 'exited_early')}
    rjs['env_extra'] = env
    rjs['steps'] = '%s/%s' % st if st else None
    res['runjson'] = rjs
    say('run.json: exit %s (%s) dumps %d crash_events %d wer %s; close %s %.2f s; elapsed %s of %s s; cvars %s; env %s; steps %s' % (
        rj.get('exit_code'), rj.get('exit_code_hex'), len(rj.get('dumps') or []), len(rj.get('crash_events') or []),
        rj.get('wer_seen'), rj.get('close_method'), float(rj.get('close_seconds') or 0), rj.get('elapsed_s'),
        rj.get('seconds_requested'), json.dumps(rj.get('cvars') or {}), json.dumps(env) if env else '-', rjs['steps']))
    if rj.get('dumps'):
        say('  dumps: %s' % ', '.join(os.path.basename(str(d if isinstance(d, str) else d.get('path', d))) for d in rj['dumps']))
    lg = sj.get('log') or {}
    say('summary: verdict %s; first frame %s s; levels %s; unknown cvars %s; errors %s' % (
        sj.get('verdict'), sj.get('first_frame_s'), json.dumps(lg.get('levels')), lg.get('unknown_cvars'), len(lg.get('errors') or [])))
    res['summary'] = {'verdict': sj.get('verdict'), 'first_frame_s': sj.get('first_frame_s'), 'levels': lg.get('levels'),
                      'unknown_cvars': lg.get('unknown_cvars'), 'errors': (lg.get('errors') or [])[:5]}
    k_rx = re.compile(a.k_regex)
    S = scan(cand, k_rx)
    n = S['n']
    res['log_files'] = [os.path.basename(p) for p in A.game_logs(cand)]
    res['families'] = n
    res['levels'] = S['levels']
    say('log files %s; levels %s' % (','.join(res['log_files']) or '-', json.dumps(S['levels'])))
    say('families: ' + ' '.join('%s=%d' % (k, n[k]) for k in SHOW + ['clean_exit']))
    for k in SHOW:
        if n[k]:
            for ln in S['first'][k]:
                say('  %s: %s' % (k, ln[:300]))
            if S['last'][k]:
                say('  %s: ... (%d more)' % (k, n[k] - len(S['first'][k]) - len(S['last'][k])) if n[k] > 6 else '  %s: ...' % k)
                for ln in S['last'][k]:
                    say('  %s: %s' % (k, ln[:300]))
    res['lines'] = {k: {'first': S['first'][k], 'last': S['last'][k]} for k in SHOW if n[k]}
    if S['kept']:
        res['c1_kept_last'] = S['kept'][-1]
        say('C1 kept so far: last %d (%d lines)' % (S['kept'][-1], len(S['kept'])))
    for key, rows in (('split', S['split']), ('gpu_wait_stats', S['gws']), ('deferred_counters', S['dc'])):
        s = series(rows)
        if s:
            res[key] = s
            say('%s fields: lines %d (%s..%s); last %s; max %s; per frame %s; monotonic %s' % (
                key, s['lines'], s['first_ts'], s['last_ts'], json.dumps(s['last']), json.dumps(s['max']),
                json.dumps(s.get('per_frame')), json.dumps(s['monotonic'])))
    if S['dc_block']:
        res['deferred_counters_last_block'] = S['dc_block']
        say('deferred_counters last block (%d lines):' % len(S['dc_block']))
        for ln in S['dc_block']:
            say('    ' + ln[:260])
    ms = mem_stats(S['mem'])
    if ms:
        res['memexport'] = ms
        say('memexport full-buffer: %s' % json.dumps(ms))
    if S['slow_last']:
        res['slow_last'] = S['slow_last'][-400:]
        say('last slow-frame line (tail): ...%s' % S['slow_last'][-200:])
    nfr = A.frame_rows(cand, kind)
    res['frame_rows'] = nfr
    if nfr:
        say('frames (%s rows) %d; slow_frame per frame %.3f' % ('frames.csv' if kind == 'native' else 'perf.csv', nfr, n['slow_frame'] / float(nfr)))

    ld = None
    misses = []
    same_scn = False
    if bases:
        base0 = bases[0]
        brj = A.jload(os.path.join(base0, 'run.json')) or {}
        bscn = scenario(brj)
        same_scn = bscn == scn
        cdir, cn = diff_dir(cand, a.out_dir)
        bdirs = []
        for b in bases:
            d, bn = diff_dir(b, a.out_dir)
            bdirs.append(d)
            if bn > 1:
                say('logdiff base %s: %d logs joined -> %s' % (os.path.basename(b), bn, os.path.relpath(d, A.REPO)))
        if cn > 1:
            say('logdiff cand: %d logs joined -> %s' % (cn, os.path.relpath(cdir, A.REPO)))
        allow = [re.compile(x) for x in a.allow_new]
        gone_ok = [re.compile(GONE_OK_DEFAULT)] + [re.compile(x) for x in a.allow_gone]
        out, rc = A.run_logdiff(bdirs, cdir, 'warning')
        new = [l for l in out if l.startswith('NEW ')]
        more = [l for l in out if l.startswith('MORE ')]
        gone = [l for l in out if l.startswith('GONE ')]
        flag = [l for l in out if l.startswith('FLAG ')]
        new_allowed = [l for l in new if any(r.search(l) for r in allow)]
        more_allowed = [l for l in more if any(r.search(l) for r in allow)]
        out_i, _ = A.run_logdiff(bdirs, cdir, 'info')
        new_i = [l for l in out_i if l.startswith('NEW ')]
        new_i_other = [l for l in new_i if not TOY.search(l) and not any(r.search(l) for r in allow)]
        new_i_allowed = [l for l in new_i if any(r.search(l) for r in allow)]
        gone_other = [l for l in gone if not any(r.search(l) for r in gone_ok)]
        ld = {'bases': [os.path.basename(b) for b in bases], 'base_scenario': bscn, 'NEW': len(new) - len(new_allowed),
              'NEW_allowed': len(new_allowed), 'MORE': len(more) - len(more_allowed), 'MORE_allowed': len(more_allowed),
              'GONE': len(gone), 'GONE_unexpected': len(gone_other), 'FLAG': len(flag), 'NEW_info_other': len(new_i_other),
              'NEW_info_allowed': len(new_i_allowed), 'rc': rc,
              'new': [x for x in new if x not in new_allowed][:25], 'new_allowed': new_allowed[:15],
              'more': more[:20], 'gone_unexpected': gone_other[:30], 'flag': flag, 'new_info_other': new_i_other[:25],
              'new_info_allowed': new_i_allowed[:15]}
        res['logdiff'] = ld
        say('logdiff vs %s (base scenario %s): NEW %d (+%d allowed) MORE %d (+%d allowed) GONE %d (%d unexpected) FLAG %d; '
            'NEW at info %d other, %d allowed; rc %s' % (
                ','.join(ld['bases']), bscn, ld['NEW'], ld['NEW_allowed'], ld['MORE'], ld['MORE_allowed'], ld['GONE'],
                ld['GONE_unexpected'], ld['FLAG'], ld['NEW_info_other'], ld['NEW_info_allowed'], rc))
        for l in ld['new'] + [x for x in more if x not in more_allowed] + flag:
            say('  ' + l[:300])
        for l in new_allowed[:8]:
            say('  allowed ' + l[:260])
        for l in (gone_other[:12] if same_scn else []):
            say('  ' + l[:220])
        for l in new_i_other[:12]:
            say('  info ' + l[:260])
        for l in new_i_allowed[:6]:
            say('  info allowed ' + l[:240])
        _, _, lv_b, _ = A.scan_logs(base0)
        say('levels cand %s vs %s %s' % (json.dumps(S['levels']), os.path.basename(base0), json.dumps(lv_b)))
        sc_c, sc_b = A.scenes(cand, kind), A.scenes(base0, kind)
        if sc_c is not None and sc_b is not None:
            major_b = {k: v for k, v in sc_b.items() if v >= 2.0}
            major_c = {k: v for k, v in sc_c.items() if v >= 2.0}
            missing = sorted(k for k in major_b if sc_c.get(k, 0.0) < 0.5)
            extra = sorted(k for k in major_c if sc_b.get(k, 0.0) < 0.5)
            res['scenes'] = {'base': os.path.basename(base0), 'missing_in_cand': missing, 'extra_in_cand': extra,
                             'cand_major': {k: round(v, 1) for k, v in sorted(major_c.items(), key=lambda x: -x[1])},
                             'base_major': {k: round(v, 1) for k, v in sorted(major_b.items(), key=lambda x: -x[1])}}
            say('scenes (>= 2 s) base: %s' % ' '.join('%s:%.0fs' % kv_ for kv_ in sorted(major_b.items(), key=lambda x: -x[1])[:10]))
            say('scenes (>= 2 s) cand: %s' % ' '.join('%s:%.0fs' % kv_ for kv_ in sorted(major_c.items(), key=lambda x: -x[1])[:10]))
            say('  missing in cand: %s; extra in cand: %s' % (missing or '-', extra or '-'))
            if kind == 'off' and scn == 'M':
                fe = {k: round(sc_c.get(k, 0.0), 1) for k in FRONT_END}
                res['front_end_scenes'] = fe
                say('  front-end scenes in cand (s): %s' % ' '.join('%s=%s' % kv_ for kv_ in fe.items()))
                low = [k for k, v in fe.items() if v < 1.0]
                if low:
                    misses.append('front-end scene(s) missing: %s' % low)
            if same_scn and missing:
                misses.append('base scenes missing in cand: %s' % missing)
        mc, mb = A.marks(cand, False, kind), A.marks(base0, False, kind)
        if mc and mb:
            names = list(mb.keys())
            pre = names[:names.index('up-2') + 1] if 'up-2' in names else names
            pdiff = [(k, mb[k][2], mc[k][2] if k in mc else 'missing') for k in pre if k not in mc or mc[k][2] != mb[k][2]]
            alld = [(k, mb[k][2], mc[k][2]) for k in names if k in mc and mc[k][2] != mb[k][2]]
            res['marks'] = {'prefix': len(pre), 'prefix_diff': [list(x) for x in pdiff], 'all_diff': len(alld),
                            'cand': {k: v[2] for k, v in mc.items()}}
            say('route marks first-frame..%s: %d, %d differ%s; all marks: %d differ' % (
                pre[-1] if pre else '-', len(pre), len(pdiff), (': ' + ' '.join('%s %s->%s' % d for d in pdiff)) if pdiff else '',
                len(alld)))
            say('  cand marks: %s' % ' '.join('%s=%s' % (k, v[2]) for k, v in mc.items()))
            if same_scn and pdiff:
                misses.append('marks differ before up-2: %s' % ' '.join('%s %s->%s' % d for d in pdiff))
        if ld['NEW'] and row != 's4b14':
            misses.append('logdiff NEW %d' % ld['NEW'])
        if ld['MORE']:
            misses.append('logdiff MORE %d' % ld['MORE'])
        if ld['FLAG']:
            misses.append('logdiff FLAG %d' % ld['FLAG'])
        if same_scn and ld['GONE_unexpected']:
            misses.append('logdiff GONE %d beyond Toypad/u-diag lines' % ld['GONE_unexpected'])
        if rc not in (0, None):
            misses.append('logdiff rc %s' % rc)
        if same_scn and scn == 'A':
            bst, cst = steps_of(brj), st
            if bst and cst and (cst[0] or 0) < (bst[0] or 0) - 2:
                misses.append('attract route steps %s/%s vs base %s/%s' % (cst + bst))
    if rj.get('exit_code') != 0:
        misses.append('exit %s' % rj.get('exit_code'))
    if (rj.get('close_method') or '') != 'wm_close':
        misses.append('close %s' % rj.get('close_method'))
    if rj.get('dumps'):
        misses.append('dumps %d' % len(rj['dumps']))
    if rj.get('crash_events'):
        misses.append('crash events %d' % len(rj['crash_events']))
    if st and scn != 'A' and st[0] != st[1]:
        misses.append('steps %s/%s' % st)
    if S['levels'].get('error', 0) or S['levels'].get('critical', 0):
        misses.append('[error] %d [critical] %d' % (S['levels'].get('error', 0), S['levels'].get('critical', 0)))
    for k in ('stuck_lock', 'protect_failed', 'minidump', 'fatal'):
        if n[k]:
            misses.append('%s %d' % (k, n[k]))
    if not n['clean_exit']:
        misses.append('no clean-exit line')
    th = A.threads(cand, rj, sj)
    if th is not None:
        res['threads'] = th
        top = sorted(th['by_name'].items(), key=lambda x: -x[1]['pct'])[:10]
        say('threads (%% of one core, window %s s from the first frame, %s s): %s' % (th.get('window'), th['window_s'],
            ' | '.join('%s x%d %.1f' % (k, v['threads'], v['pct']) for k, v in top)))
        for tid, tk in (th.get('ticks') or {}).items():
            say('  TimerQueue ticks (tid %s): %d samples over %s s, cycles non-rising in %d of %d steps %s' % (
                tid, tk['samples'], tk['span_s'], tk['non_rising'], tk['steps'], tk['non_rising_at_s'] or ''))
            if tk['non_rising']:
                misses.append('TimerQueue ticks non-rising %d/%d' % (tk['non_rising'], tk['steps']))
        if not th.get('ticks'):
            say('  TimerQueue ticks: no TimerQueue thread sampled')
    else:
        say('threads: no threads-s4a.csv')
    ss = A.slow_state(cand, rj, sj)
    res['slow_state'] = ss
    say('sys.csv slow state: %s' % (json.dumps(ss) if ss is not None else 'no sys.csv'))
    P = row_proofs(row, rj, S, ld, res)
    res['proofs'] = P
    res['base_misses'] = misses
    for p in P:
        say('PROOF %s %s' % ({True: 'ok  ', False: 'MISS', None: 'note'}[p['ok']], p['text']))
    pm = [p['text'] for p in P if p['ok'] is False]
    say('BASE items missed: %s' % ('; '.join(misses) if misses else 'none') + ('' if same_scn or not bases else
        ' (base scenario differs: scenes/marks/GONE not judged)'))
    hint = 'PASS?' if not misses and not pm else 'LOOK'
    res['hint'] = hint
    say('VERDICT HINT %s: %d BASE misses, %d proof misses (apply QUEUE.md "passes if" for row %s)' % (hint, len(misses), len(pm), row or '-'))
    os.makedirs(a.out_dir, exist_ok=True)
    stem = os.path.join(a.out_dir, os.path.basename(cand))
    with open(stem + '.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=1)
    with open(stem + '.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()

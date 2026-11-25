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
import csv
import datetime
import hashlib
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
# GPU wait stats line (rexlego/src/gpu_wait_backoff.cpp:237-241, S4b snap1): one line per 5 s, every counter taken and
# cleared, so each field is per interval. It has no key=value pairs (KV finds nothing in it).
GWS = re.compile(r'GPU wait stats \((\d+) s\): L1 waits (\d+) polls (\d+) moved (\d+) gpu_off (\d+) sleep>moved (\d+) '
                 r'sleep>done (\d+) \| L2 tries (\d+) waits (\d+) polls (\d+) delayed (\d+) sleep>ready (\d+) \| kicks (\d+) '
                 r'\| pause (\d+) yield (\d+) sleep (\d+) sleep_sum ([\d.]+) ms sleep_fail (\d+) \| L1 sum ([\d.]+) ms '
                 r'max ([\d.]+) ms hist <50us (\d+) <200us (\d+) <1ms (\d+) <4ms (\d+) >=4ms (\d+) \| L2 sum ([\d.]+) ms '
                 r'max ([\d.]+) ms')
GWS_KEYS = ['interval_s', 'l1_waits', 'l1_polls', 'l1_moved', 'l1_gpu_off', 'l1_sleep_moved', 'l1_sleep_done', 'l2_tries',
            'l2_waits', 'l2_polls', 'l2_delayed', 'l2_sleep_ready', 'kicks', 'pause', 'yield', 'sleep', 'sleep_sum_ms',
            'sleep_fail', 'l1_sum_ms', 'l1_max_ms', 'h_lt50us', 'h_lt200us', 'h_lt1ms', 'h_lt4ms', 'h_ge4ms', 'l2_sum_ms',
            'l2_max_ms']
# deferred_counters header (d3d12/deferred_command_list.cpp:668, CTR bin only): counts since the last header (reset).
DC_HDR = re.compile(r'deferred_counters: ([\d.]+) s, (\d+) lists, (\d+) KB, (\d+) barriers')
# K = C1's verify-mismatch line at a keep-watch protect (gate A), src/graphics/shared_memory.cpp:733-735 (S4b snap1):
#   "C1 verify {}: page {:08X} changed since its upload ({} so far){}", {} = K (keep-watch protect, suffix "; protect
#   keeps the normal path") or F (write fault: family c1_verify_f, not K). c1_other lists every C1 keep-watch line that
#   no known family matches.
K_DEFAULT = r'C1 verify K: page [0-9A-F]{8} changed since its upload \((\d+) so far\)'
TOY = re.compile(r'\] Toypad\[(Read |Write)\] ')
# logdiff keys print digits as '#' ("[gpu] S# upload hash: frame # calls # ..."), hence S[#\d].
# 21:56: also the Toy Pad LED lines ("Toypad: pad # mode # lit FE #E # ..."): the game picks the colour, so the
# normalised key changes with route timing (s4b23 vs s4bL0: one false "unexpected GONE"; subagent check).
GONE_OK_DEFAULT = r'\] Toypad\[(Read |Write)\] |\] Toypad: pad [#\d]+ mode |S[#\d] upload hash|slow frame #'
FRONT_END = ['218/222', '226/1022', '220/528', '220/534', '219/226']
# run-2 task 2: the W6 untimed runs (build/agent12/w6-gates/W6-GATES.md v2, "Untimed runs"); every one has
# framerate_limit=0. Values as run.json records them (lower case).
P2F = {'framerate_limit': '0', 'shared_memory_single_hold_rearm': 'true', 'physical_protect_hold_global_lock': 'true'}
W6_CVARS = {
    'w6s1': dict(P2F, shared_memory_upload_hash_log='true', slow_frame_log_ms='1'),
    'w6s2': dict(P2F, physical_protect_keep_watch='true', physical_protect_keep_watch_verify='false',
                 shared_memory_upload_hash_log='true', slow_frame_log_ms='1'),
    'w6gA': dict(P2F, physical_protect_keep_watch='true', physical_protect_keep_watch_verify='true', slow_frame_log_ms='1'),
    'w6s3': dict(P2F, physical_protect_keep_watch='true', physical_protect_keep_watch_verify='false', slow_frame_log_ms='1'),
    # 21:25 extra row (not in W6-GATES.md): gate A without verify = W6's p2fc arm on the L route (w6gA hung with verify on)
    'w6gB': dict(P2F, physical_protect_keep_watch='true', physical_protect_keep_watch_verify='false', slow_frame_log_ms='1'),
}
# 22:44 (Agent 1): Agent 6's direct test for finding 10, first after the windows on the quiet host: untimed vpad L route,
# tags via the fixed sidecar, slow_frame_log_ms=1; f10a = s4b20's set (C1 OFF), f10b = w6gB's set (p2fc).
F10_CVARS = {
    'f10a': {'shared_memory_upload_nontemporal_copy': 'true', 'slow_frame_log_ms': '1'},
    'f10b': dict(W6_CVARS['w6gB']),
}
# rows that read P2's counter (memexport full-buffer total; must be 0)
P2_ROWS = ('s4b23', 'w6s1', 'w6s2', 'w6gA', 'w6s3', 'w6gB', 'f10b')
# the L route's marks whose scenes do not depend on how long the level load takes
L_FIXED_MARKS = ('first-frame', 'title', 'pads-white', 'tags-placed')
# (key, needle = a plain substring the message must contain, extra regex or None)
FAM = [
    ('c1_any', 'C1 keep-watch', None),
    ('c1_init_on', 'C1 keep-watch: on (with physical_protect_hold_global_lock)', None),
    ('c1_init_blocked', 'C1 keep-watch: on, but blocked for this process', None),
    ('c1_init_nohold', 'C1 keep-watch: on, but physical_protect_hold_global_lock is off', None),
    ('c1_first', 'C1 keep-watch: first kept protect', None),
    ('c1_kept', 'protects kept so far', None),
    ('c1_blocked', 'C1 keep-watch: blocked for this process', None),
    ('c1_verify_on', 'C1 verify: on. Hashing CPU uploads', None),
    ('c1_verify_f', 'C1 verify F: page ', None),
    ('recovered_stale', 'Recovered stale physical page protection', None),
    ('unhandled_phys', 'Unhandled guest physical write fault', None),
    ('protect_failed', 'PhysicalHeap::Protect failed', None),
    ('split_init', 'd3d12_submit_split_kb: splitting submissions', None),
    ('split', 'd3d12_submit_split: ', None),
    ('deferred_counters', 'deferred_counters', None),
    ('gpu_wait', 'GPU wait', None),
    ('gpu_wait_stats', 'GPU wait stats', None),
    ('gpu_wait_backoff', 'GPU wait back-off', None),
    ('gpu_wait_on', 'GPU wait back-off: ON (', None),
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
    ('dred', 'DRED (Device Removed Extended Data) enabled', None),
    ('d3d12_msg', 'D3D12 ', re.compile(r'D3D12 (ERROR|WARNING|CORRUPTION|INFO|MESSAGE)')),
]
ITEM_FAMS = ['c1_any', 'c1_verify_on', 'c1_verify_f', 'k', 'split_init', 'split', 'deferred_counters', 'gpu_wait',
             'memexport']
S4A_FAMS = ['s4_upload_hash', 'slow_frame', 'precise_wait', 'miss_cache']
C1_KNOWN = ('c1_init_on', 'c1_init_blocked', 'c1_init_nohold', 'c1_first', 'c1_kept', 'c1_blocked')
SHOW = ['c1_any', 'k', 'c1_verify_on', 'c1_verify_f', 'c1_other', 'recovered_stale', 'unhandled_phys', 'protect_failed',
        'split_init', 'split', 'deferred_counters', 'gpu_wait', 'memexport', 'slow_frame', 's4_upload_hash', 'precise_wait',
        'miss_cache', 'stuck_lock', 'minidump', 'fatal', 'debug_layer', 'dred', 'd3d12_msg']


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
                    mm = GWS.search(msg)
                    if mm:
                        S['gws'].append((ts[11:], {k: num(v) for k, v in zip(GWS_KEYS, mm.groups())}))
                if 'memexport' in got:
                    mm = MEMEXPORT.search(msg)
                    if mm:
                        S['mem'].append((int(mm.group(1)), int(mm.group(2))))
                if 'slow_frame' in got:
                    S['slow_last'] = ln
                mh = DC_HDR.search(msg) if 'deferred_counters' in got else None
                if mh:
                    g = [num(x) for x in mh.groups()]
                    S['dc'].append((ts[11:], {'seconds': g[0], 'lists': g[1], 'kb': g[2], 'barriers': g[3],
                                              'kb_per_list': round(g[2] / float(g[1]), 2) if g[1] else 0}))
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


# Agent 10 (22:06): PROOF labels must name the real coverage. L-route runs that stop before the 'vortex' mark (verify runs
# at the 600 s cap) cover boot, menus and story-load only, not the level load.
COVER = {'marks': []}


def route_marks(run):
    """The 'mark' steps reached, in order, from <run>/input.csv (columns: t, step, kind, arg, ...)."""
    out = []
    try:
        with open(os.path.join(run, 'input.csv'), encoding='utf-8', errors='replace') as f:
            for line in f:
                c = line.split(',')
                if len(c) > 3 and c[2] == 'mark':
                    out.append(c[3].strip())
    except OSError:
        pass
    return out


def cover_txt():
    ms = COVER['marks'] or []
    if 'vortex' in ms:
        return 'through the level load (last mark %s)' % ms[-1]
    return 'to route mark %s only, no level load' % (ms[-1] if ms else '?')


STUCK_TS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d(?:\.\d+)?)\]')
STUCK_LR = re.compile(r'parked at lr[=: ]+(?:0x)?([0-9A-Fa-f]{8})\b')  # owner lr only: the waiter's callers line has lr= too
HOSTLOAD = os.path.join(HERE, 'logs', 'hostload.csv')


def _ts(s):
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def hang_scan(cand, hostload=HOSTLOAD):
    """Agent 1 (22:44): host CPU at any hang. STUCK-LOCK lines in every game*.log (lines <= 3 s apart = one event),
    each with the run's sys.csv (about 1 Hz) cpu_util_pct / e_eff_mhz over [-10 s, +2 s], hostload.csv (compiler
    processes, about every 30 s, from hostload.ps1) over +-60 s, and the lr values in its lines (finding 10 = owner in
    sub_83FAF180, 83FAF180-83FAF25F). Also the hostload rows during the run (quiet host = no clang/cl/ninja/link)
    and the Toy Pad LOAD confirmations (game.log lines + the sidecar's result row)."""
    stamps, loads = [], 0
    for name in sorted(os.listdir(cand)):
        if not re.match(r'game(\.\d+)?\.log$', name):
            continue
        with open(os.path.join(cand, name), encoding='utf-8', errors='replace') as f:
            for line in f:
                if 'STUCK-LOCK' in line:
                    m = STUCK_TS.match(line)
                    t = _ts(m.group(1)) if m else None
                    if t:
                        stamps.append((t, line.rstrip()))
                elif 'Toypad listener: LOAD ->' in line:
                    loads += 1
    stamps.sort(key=lambda x: x[0])
    events = []
    for t, line in stamps:
        if events and (t - events[-1][-1][0]).total_seconds() <= 3:
            events[-1].append((t, line))
        else:
            events.append([(t, line)])

    def rows(p):
        if not os.path.exists(p):
            return []
        with open(p, newline='', encoding='utf-8-sig') as f:
            return list(csv.DictReader(f))

    def fnum(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    sysrows = [(fnum(r.get('epoch_s')), r) for r in rows(os.path.join(cand, 'sys.csv'))]
    sysrows = [(e, r) for e, r in sysrows if e is not None]
    if stamps:
        day = stamps[0][0].date()
    elif sysrows:
        day = datetime.datetime.fromtimestamp(sysrows[0][0]).date()
    else:
        day = datetime.date.today()
    hl = []
    for r in rows(hostload):
        try:
            t = datetime.datetime.combine(day, datetime.datetime.strptime(r.get('time') or '', '%H:%M:%S').time())
        except ValueError:
            continue
        busy = sum(int(fnum(r.get(k)) or 0) for k in ('clang', 'cl', 'ninja', 'link'))
        hl.append((t.timestamp(), busy, '%s clang %s cl %s ninja %s link %s cpu %s%%%s' % (
            r.get('time'), r.get('clang'), r.get('cl'), r.get('ninja'), r.get('link'), r.get('cpu_pct'),
            (' top ' + r['top']) if r.get('top') else '')))   # task #23: hostload.ps1's top-4 column (11-23)
    out = []
    for ev in events:
        e0 = ev[0][0].timestamp()
        win = [r for e, r in sysrows if e0 - 10 <= e <= e0 + 2]
        cpu = [x for x in (fnum(r.get('cpu_util_pct')) for r in win) if x is not None]
        emhz = [x for x in (fnum(r.get('e_eff_mhz')) for r in win) if x is not None]
        lrs = sorted(set(m.group(1).upper() for _t, line in ev for m in STUCK_LR.finditer(line)))
        f10 = bool(lrs) and all(0x83FAF180 <= int(x, 16) <= 0x83FAF25F for x in lrs)
        out.append({'at': ev[0][0].strftime('%H:%M:%S.%f')[:-3], 'lines': len(ev), 'lr': lrs,
                    'finding10': f10 if lrs else None, 'first_line': ev[0][1][-220:], 'sys_rows': len(win),
                    'cpu_util_pct': [round(x) for x in cpu], 'cpu_util_max': round(max(cpu), 1) if cpu else None,
                    'e_eff_mhz_min': round(min(emhz)) if emhz else None,
                    'hostload': [s for t, _b, s in hl if abs(t - e0) <= 60]})
    quiet = {}
    if sysrows:
        a, b = sysrows[0][0], sysrows[-1][0]
        inrun = [busy for t, busy, _s in hl if a <= t <= b]
        quiet = {'rows': len(inrun), 'busy_rows': sum(1 for busy in inrun if busy)}
    res_row = ''
    for r in rows(os.path.join(cand, 'toypad-events.csv')):
        if r.get('kind') == 'result':
            res_row = r.get('detail') or ''
    return out, quiet, {'confirms': loads, 'result': res_row}


# post-window rows (M3, 11-25): the bin each must run on, as sha256 prefixes (16 hex) of the files the run dir holds.
# Sources: build/agent2/<bin>/MANIFEST.txt (devoff4bv 353846A3, staged 02:43:40; devoff4b-s33 50CC5BE2, 02:44:14;
# devoff4b DE11A914). Only rexgpu-xenos.dll differs between the three bins.
_EXE = 'DFBE1D43B28861A6'
_RT = 'A33801D1538D6175'
_GPU = {'devoff4b-bin': 'E3CB99CFDEA95E66', 'devoff4bv-bin': '82A0DE742AAAAE44', 'devoff4b-s33-bin': '0B57BBD5D7B96CBD'}


def _pw(bin_name):
    return {'bin': bin_name, 'sha': {'legodimensions.exe': _EXE, 'rexruntime.dll': _RT, 'rexgpu-xenos.dll': _GPU[bin_name]}}


POSTWIN = {'s4bV0f': _pw('devoff4bv-bin'), 's4b07f': _pw('devoff4bv-bin'),
           's33base': _pw('devoff4b-bin'), 's33basesf': _pw('devoff4b-bin'),
           's33off': _pw('devoff4b-s33-bin'), 's33offsf': _pw('devoff4b-s33-bin')}


def sha16(p):
    if not os.path.isfile(p):
        return None
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()[:16]


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
    # task #23 (Agent 1, 11-23 06:23): the second f10 pair (f10a2, f10b2) gets the same proofs as f10a/f10b
    # session 3 (M3, RUNPLANS.md): new ids get the proofs of the row they repeat: f10a3/f10aL, f10b3/f10bL (third quiet
    # pair, controlled-load pair), s4bLV = w6gA's cvar set with a 1800 s cap (G5: 0 K, 0 F), s4b07r = row 7 re-run beside
    # s4bV0, s4bQ5 = s4b18 at quantum 500 us, s4bN16 = the ready-N measurement (split 16 on the W7 title scene, row 11's
    # proofs: init line, failed=0, splits > 0; read K and KB per list from the per-frame line, READY-N.md)
    # post-window (M3, 11-25): s4b07f / s4bV0f = s4b07r / s4bV0 on devoff4bv (C1 verify-only fix; M10
    # c1-verify-fix-rating.md S2, Agent 12 RATIONALE.md L86-118): the same proofs plus POSTWIN below
    r = {'f10a2': 'f10a', 'f10b2': 'f10b', 'f10a3': 'f10a', 'f10b3': 'f10b', 'f10aL': 'f10a', 'f10bL': 'f10b',
         's4bLV': 'w6gA', 's4b07r': 's4b07', 's4bQ5': 's4b18', 's4bN16': 's4b11', 's4bN4': 's4b11',
         's4b07f': 's4b07', 's4bV0f': 's4bV0'}.get(row, row)
    if r in ('s4b01', 's4bL0'):
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
    elif r in ('s4b04', 's4b24', 's4b07', 'w6s2', 'w6gA', 'w6s3', 'w6gB', 'f10b'):
        chk(n['c1_init_on'] == 1, 'init "C1 keep-watch: on (with physical_protect_hold_global_lock)" x%d' % n['c1_init_on'])
        chk(n['c1_first'] >= 1, '"first kept protect" x%d (gate D / positive control)' % n['c1_first'])
        chk(kept_last is not None or n['c1_first'] >= 1, 'kept count: last "kept so far" = %s (%d such lines)' % (kept_last, n['c1_kept']))
        if r in ('s4b04', 's4b07', 'w6gA'):
            chk(n['c1_verify_on'] >= 1, 'C1 verify armed: "C1 verify: on. Hashing CPU uploads ..." x%d (without it K = 0 '
                'proves nothing)' % n['c1_verify_on'])
            chk(n['k'] == 0, 'verify-mismatch (K) lines %d (gate A%s)' % (
                n['k'], ', menus part' if r == 's4b04' else ' / G5, ' + cover_txt()))
            fl = (S['first']['c1_verify_f'] or ['-'])[0][-100:]
            if r == 'w6gA':
                # W6-GATES.md v2 G5: 0 "C1 verify K:" and 0 "C1 verify F:" lines
                chk(n['c1_verify_f'] == 0, 'G5: C1 verify F lines %d (G5 needs 0 K and 0 F) %s' % (n['c1_verify_f'], fl))
            else:
                chk(None, 'C1 verify F lines (write-fault side, not gate A): %d %s' % (n['c1_verify_f'], fl))
            if r in ('s4b07', 'w6gA'):
                ks = S['kept']
                txt = 'kept count rises %s: first %s -> last %s (%d "kept so far" lines)' % (
                    cover_txt(), ks[0] if ks else None, ks[-1] if ks else None, len(ks))
                chk((ks[-1] > ks[0]) if len(ks) >= 2 else None, txt)
        elif r in ('w6s2', 'w6s3', 'w6gB', 'f10b'):
            chk(n['c1_verify_on'] == 0 and n['k'] == 0, 'verify off (keep_watch_verify=false): "C1 verify: on" x%d, K lines %d' % (
                n['c1_verify_on'], n['k']))
            if r in ('w6gB', 'f10b'):
                ks = S['kept']
                txt = 'kept count rises %s: first %s -> last %s (%d "kept so far" lines)' % (
                    cover_txt(), ks[0] if ks else None, ks[-1] if ks else None, len(ks))
                chk((ks[-1] > ks[0]) if len(ks) >= 2 else None, txt)
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
    elif r == 's4bV0':
        # session 3: C1-OFF verify control (Agent 12 22:15: row 7 + keep_watch=false); Agent 12 predicts F > 0
        chk(n['c1_init_on'] == 0 and n['c1_first'] == 0 and n['c1_kept'] == 0,
            'keep-watch off: init-on x%d, first kept x%d, kept x%d' % (n['c1_init_on'], n['c1_first'], n['c1_kept']))
        fl = (S['first']['c1_verify_f'] or ['-'])[0][-100:]
        # M10 review S1 (01:58): verify must be armed, or F = 0 / K = 0 prove nothing (as s4b04/s4b07/w6gA, L451)
        chk(n['c1_verify_on'] == 1, 'C1 verify armed: "C1 verify: on. Hashing CPU uploads ..." x%d (without it F = 0 proves '
            'nothing: INCONCLUSIVE)' % n['c1_verify_on'])
        chk(None, 'K lines %d; F lines %d (Agent 12 predicts F > 0; F = 0 refutes it; compare s4b07r '
            'over the same marks) %s' % (n['k'], n['c1_verify_f'], fl))
        chk(n['recovered_stale'] == 0 and n['unhandled_phys'] == 0,
            'gate D zero lines: "Recovered stale physical page protection" %d, "Unhandled guest physical write fault" %d' % (
                n['recovered_stale'], n['unhandled_phys']))
    if r.startswith('s4b08') or r in P2_ROWS:
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
        kpl = sorted(d['kb_per_list'] for _, d in S['dc'] if d.get('lists'))
        med = kpl[len(kpl) // 2] if kpl else None
        chk(None, 'KB per list per header: median %s (min %s, max %s; %d headers); half the median %s (QUEUE.md: <N> ~ '
            'half; Agent 7 sets N)' % (med, kpl[0] if kpl else None, kpl[-1] if kpl else None, len(kpl),
                                        round(med / 2.0, 1) if kpl else None))
    if r in ('s4b10', 's4b11', 's4b12', 's4b13', 's4b15', 's4b16', 's4b25'):
        chk(n['split_init'] == 1, 'init "d3d12_submit_split_kb: splitting submissions at N KB" x%d: %s' % (
            n['split_init'], (S['first']['split_init'] or ['-'])[0][-120:]))
        if row in ('s4bN16', 's4bN4'):  # M10 review N4: the init line names this row's N
            kb = row[4:]
            chk(('at %s KB' % kb) in (S['first']['split_init'] or [''])[0], 'init line says "at %s KB"' % kb)
        if sp or r != 's4b25':
            chk(bool(sp) and spmax.get('failed', 0) == 0, 'failed=0 in every d3d12_submit_split line (max %s over %s lines)' % (
                spmax.get('failed'), sp.get('lines', 0)))
        else:
            chk(None, 'no d3d12_submit_split line (printed only while a split is due, at most every 10 s): failed not judged')
        if r != 's4b25':
            chk(bool(sp) and spmax.get('splits', 0) > 0, 'splits > 0 (max %s)' % spmax.get('splits'))
        chk(None, 'per frame: submission %s, splits %s (frames %s; fields monotonic %s)' % (
            rate.get('submission'), rate.get('splits'), sp.get('frames'), sp.get('monotonic')))
        if r == 's4b12':
            chk(spmax.get('held_pipelines', 0) > 0, 'held_pipelines > 0 (max %s)' % spmax.get('held_pipelines'))
            chk(None, 'held_query max %s (> 0 if the attract scene runs occlusion queries)' % spmax.get('held_query'))
            chk(spmax.get('held_scratch', 0) == 0, 'held_scratch = 0 expected (max %s)' % spmax.get('held_scratch'))
        if r == 's4b15':
            chk(n['dred'] >= 1 and n['debug_layer'] == 0, 'd3d12_debug on: DRED line x%d, debug-layer enable failure x%d' % (
                n['dred'], n['debug_layer']))
            chk(bool(ld) and ld['NEW'] == 0, 'no NEW warning key vs row 14 (NEW %s beside split lines)' % (ld and ld['NEW']))
            chk(None, 'debug-layer messages go to the debugger (the InfoQueue has no log callback), not game.log: "no '
                'message row 14 lacks" is not testable headless')
        if r == 's4b16':
            chk(len(S['dc']) >= 1, 'deferred_counters headers %d (compare lists per 10 s with row 9)' % len(S['dc']))
    if r == 's4b14':
        chk(n['dred'] >= 1 and n['debug_layer'] == 0, 'd3d12_debug on: DRED line x%d, debug-layer enable failure x%d' % (
            n['dred'], n['debug_layer']))
        chk(None, 'debug-layer control: NEW at warning %s (debug-layer messages go to the debugger, not game.log)' % (
            ld and ld['NEW']))
    elif r in ('s4b17', 's4b18'):
        chk(n['gpu_wait_stats'] >= 1 and gw.get('lines', 0) == n['gpu_wait_stats'], 'GPU wait stats lines %d, %s parsed' % (
            n['gpu_wait_stats'], gw.get('lines', 0)))
    if r == 's4b17':
        for f in ('l1_waits', 'l1_polls', 'l2_tries', 'kicks'):
            chk(gwmax.get(f, 0) > 0, 'GPU wait stats %s > 0 (max per 5 s %s, sum %s)' % (f, gwmax.get(f), (gw.get('sum') or {}).get(f)))
        chk(None, 'init lines %d (P1: one "GPU wait back-off: OFF (...); stats ON; GetData hook built."): %s' % (
            n['gpu_wait_backoff'], (S['first']['gpu_wait_backoff'] or ['-'])[0][-110:]))
    elif r == 's4b18':
        on1 = (S['first']['gpu_wait_on'] or ['-'])[0]
        q = 'quantum %d us' % (500 if row == 's4bQ5' else 250)
        chk(n['gpu_wait_on'] == 1 and n['gpu_wait_backoff'] == 1 and q in on1 and 'GetData hook built' in on1,
            'one "GPU wait back-off: ON (%s, ...); ...; GetData hook built." line (ON x%d, back-off lines x%d): %s' % (
                q, n['gpu_wait_on'], n['gpu_wait_backoff'], on1[-110:]))
        chk(gwmax.get('sleep_fail', 0) == 0, 'sleep_fail = 0 (max %s over %s stats lines)' % (gwmax.get('sleep_fail'), gw.get('lines', 0)))
        chk(n['stuck_lock'] == 0, 'no STUCK-LOCK (%d)' % n['stuck_lock'])
    elif r in ('s4b19', 's4b20', 'f10a'):
        chk(cv.get('shared_memory_upload_nontemporal_copy') == 'true', 'run.json cvars: shared_memory_upload_nontemporal_copy=%s (M1 logs nothing)' % (
            cv.get('shared_memory_upload_nontemporal_copy')))
    elif r in ('s4b22', 's4b24', 's4b23') or r in W6_CVARS:
        chk(cv.get('shared_memory_single_hold_rearm') == 'true' and cv.get('physical_protect_hold_global_lock') == 'true',
            'W6 cvars in run.json: single_hold_rearm=%s hold_global_lock=%s' % (
                cv.get('shared_memory_single_hold_rearm'), cv.get('physical_protect_hold_global_lock')))
    if r in W6_CVARS:
        want = W6_CVARS[r]
        bad = {k: cv.get(k) for k, v in want.items() if cv.get(k) != v}
        chk(not bad, 'W6 %s cvars in run.json (%d expected): %s' % (r, len(want), 'all as W6-GATES.md v2' if not bad else 'DIFFER %s' % bad))
        if r == 'w6s1':
            chk(n['c1_any'] == 0, 'p2f: no C1 line (%d)' % n['c1_any'])
    if r == 's4b23' or r in W6_CVARS or r == 's4b07':
        chk(n['protect_failed'] == 0 and n['recovered_stale'] == 0 and n['unhandled_phys'] == 0,
            'G8 bad lines: "PhysicalHeap::Protect failed" %d, "Recovered stale physical page protection" %d, '
            '"Unhandled guest physical write fault" %d' % (n['protect_failed'], n['recovered_stale'], n['unhandled_phys']))
    if r in F10_CVARS:
        want = F10_CVARS[r]
        bad = {k: cv.get(k) for k, v in want.items() if cv.get(k) != v}
        chk(not bad, 'f10 %s cvars in run.json (%d expected, %s): %s' % (
            r, len(want), "s4b20's set + slow_frame_log_ms=1" if r == 'f10a' else "w6gB's set",
            'all as planned' if not bad else 'DIFFER %s' % bad))
        if r == 'f10a':
            chk(n['c1_any'] == 0, 'C1 off: no C1 line (%d)' % n['c1_any'])
            chk(n['slow_frame'] > 0, 'slow-frame lines %d' % n['slow_frame'])
            ms = res.get('memexport') or {}
            chk(None, 'memexport full-buffer total with P2 off (not a gate): last %s, max %s' % (
                ms.get('last_total'), ms.get('max_total')))
        tp = res.get('toypad') or {}
        chk((tp.get('confirms') or 0) >= 3, 'tags placed: %s game.log LOAD lines (3 needed); sidecar: %s' % (
            tp.get('confirms'), tp.get('result') or 'no result row'))
        chk('vortex' in (COVER['marks'] or []), 'L route reached the level: ' + cover_txt())
        hc = res.get('hang_cpu') or []
        chk(None, 'FINDING 10 (Agent 6 direct test): STUCK-LOCK events %d%s' % (len(hc), ''.join(
            '; at %s lr %s (finding 10: %s) cpu_util max %s' % (h['at'], ','.join(h['lr']) or '?', h['finding10'],
                                                               h['cpu_util_max']) for h in hc)))
        hq = res.get('host_quiet') or {}
        chk((hq.get('busy_rows') == 0) if hq.get('rows') else None,
            'quiet host: hostload.csv rows with clang/cl/ninja/link during the run: %s of %s' % (
                hq.get('busy_rows'), hq.get('rows')))
        chk(n['protect_failed'] == 0 and n['recovered_stale'] == 0 and n['unhandled_phys'] == 0,
            'G8 bad lines: Protect failed %d, Recovered stale %d, Unhandled guest physical write fault %d' % (
                n['protect_failed'], n['recovered_stale'], n['unhandled_phys']))
    pw = POSTWIN.get(row)
    if pw:
        # post-window rows (M3, 11-25): bin identity from the run dir's own copies (run-game copies the bin's files into
        # the run dir; run.json run_dir / bin_dir), then the positive controls that make a 0 count mean something
        rd = (rj or {}).get('run_dir') or ''
        bd = os.path.normpath((rj or {}).get('bin_dir') or '')
        chk(os.path.basename(bd).lower() == pw['bin'].lower(), 'bin dir %s (want build\\agent2\\%s)' % (bd or '-', pw['bin']))
        for fn, want in sorted(pw['sha'].items()):
            got = sha16(os.path.join(rd, fn))
            chk(got == want, 'bin: run-dir %s sha256 %s, want %s (%s MANIFEST)' % (fn, got, want, pw['bin']))
        marks = COVER['marks'] or []
        if row in ('s4b07f', 's4bV0f'):
            chk(n['c1_verify_on'] == 1, 'positive control: \"C1 verify: on.\" x%d (RATIONALE L104: x1; else INCOMPLETE)' % (
                n['c1_verify_on']))
            chk('story-load' in marks, 'positive control: the route reaches story-load (RATIONALE L104; else INCOMPLETE): '
                'marks ..%s' % (','.join(marks[-3:]) or '-'))
        if row == 's4b07f':
            chk(kept_last is not None and kept_last >= 32768, 'positive control: last "kept so far" %s >= 32768 (row 7 '
                'level, RATIONALE L104; else INCOMPLETE)' % kept_last)
            chk(None, 'reading (RATIONALE L107-118): K %d, F %d; compare the F of s4bV0f, s4b07r F 51 and s4bV0 F 70 (devoff4b, '
                'quiet host, 11-25)' % (n['k'], n['c1_verify_f']))
        elif row == 's4bV0f':
            chk(None, 'reading: F %d on the fixed bin (s4bV0 on devoff4b: F 70): F 0 = the fix removed the race; F > 0 = a '
                'non-race source (file-read path / real miss, RATIONALE L68-70), compare pages with s4b07f' % n['c1_verify_f'])
        elif row.startswith('s33'):
            # #33 row 1 (M6 TESTPLAN.md section 2): cvar off must be the old code path; the kit (RUN-S33-LOGDIFF.cmd) is
            # the row's gate, these are the cheap proofs
            nw = 0
            for fn in os.listdir(rd) if os.path.isdir(rd) else []:
                if re.match(r'game(\.\d+)?\.log$', fn):
                    with open(os.path.join(rd, fn), encoding='utf-8', errors='replace') as f:
                        nw += sum(1 for ln in f if 'd3d12_pipeline_creation_no_wait' in ln)
            chk(nw == 0, 'no \"d3d12_pipeline_creation_no_wait\" text in game*.log (x%d; TESTPLAN row 1a)' % nw)
            chk(not cv.get('d3d12_pipeline_creation_no_wait'), 'cvar d3d12_pipeline_creation_no_wait not set (run.json: %s)' % (
                cv.get('d3d12_pipeline_creation_no_wait') or '-'))
            chk((rj or {}).get('close_method') == 'wm_close', 'closed via WM_CLOSE (%s)' % (rj or {}).get('close_method'))
            if row.endswith('sf'):
                chk(n['slow_frame'] > 0, 'slow-frame lines %d (slow_frame_log_ms=1)' % n['slow_frame'])
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
    COVER['marks'] = route_marks(cand)
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
            lroute = scn.startswith('level-')
            soft = [k for k in missing if k not in FRONT_END] if scn in ('A', 'M') or scn.startswith('I') or lroute else []
            hard = [k for k in missing if k not in soft]
            if same_scn and hard:
                misses.append('base scenes missing in cand: %s' % hard)
            if same_scn and soft:
                say('  note: attract/idle scenes missing in cand (timing after the route; not a BASE item): %s' % soft)
        mc, mb = A.marks(cand, False, kind), A.marks(base0, False, kind)
        if mc and mb:
            names = list(mb.keys())
            pre = names[:names.index('up-2') + 1] if 'up-2' in names else [k for k in names if not k.startswith('idle-') and k != 'end']
            if scn.startswith('level-'):
                # L route: scenes at the later marks depend on how long the level load takes; judge only the fixed ones
                pre = [k for k in pre if k in L_FIXED_MARKS]
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
    hc, hq, tp = hang_scan(cand)
    res['hang_cpu'], res['host_quiet'], res['toypad'] = hc, hq, tp
    for i, h in enumerate(hc, 1):
        say('hang %d: STUCK-LOCK at %s (%d lines, lr %s, finding 10: %s); sys.csv cpu_util_pct [-10, +2] s: %s (max %s), '
            'e_eff_mhz min %s; hostload +-60 s: %s' % (i, h['at'], h['lines'], ','.join(h['lr']) or '?', h['finding10'],
                                                      h['cpu_util_pct'], h['cpu_util_max'], h['e_eff_mhz_min'],
                                                      '; '.join(h['hostload']) or 'no rows'))
        say('  first line: %s' % h['first_line'])
    say('hangs: %d STUCK-LOCK event(s); hostload rows during the run: %s; toypad: %s' % (
        len(hc), json.dumps(hq), json.dumps(tp)))
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

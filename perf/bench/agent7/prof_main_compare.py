#!/usr/bin/env python3
"""Main XThread hot spots, A vs B, in ms of CPU per frame, from two sample-profiler runs.

Agent 7, session 3. Built on DimensionsRecomp/tools/native-cpu/analyze_profile.py (imported,
not copied). Stdlib only, one thread (plus analyze_profile's single llvm-undname call per side).

usage:
  python bench/agent7/prof_main_compare.py A B [--label-a a-prof] [--label-b n-prof]
         [--thread-re "^Main XThread"] [--all-threads] [--tid-a TID] [--tid-b TID]
         [--fps-a F] [--fps-b F] [--map-a MAP] [--map-b MAP] [--top 25]
         [-o OUT.txt] [--json OUT.json] [--search DIR] [--driverstore] [--no-undname]
         [--handoff]

A and B are runner run dirs (profile-*.bin, legodimensions.map, frames.json, run.json; the
largest profile-*.bin is used) or profile .bin paths (then --fps-a/--fps-b unless a
frames.json sits next to the .bin, and --map-a/--map-b unless a legodimensions.map does).

Normalisation. One sampler round samples every live thread once, so one sample of a thread
stands for 1/rounds of the recording, and
    w = 1000 / (rounds * fps)   ms per frame, per sample
rounds = the LSPX trailer's round count (else the largest per-thread sample count) and fps =
the runner's measure-window fps (frames.json window.rows_by_end_bytes / end_bytes_window_s;
the runner holds the profile trigger for the first profile_s of that window, so with
profile_s == measure_s the two windows coincide). "busy" = the leaf is not a wait/io syscall
(analyze_profile LEAF_CLASS_RULES): running, or runnable but preempted. Kernel time spent on
a fault before KiUserExceptionDispatcher runs is attributed to the faulting guest
instruction (the user context), i.e. to "guest code", not to the fault bucket.
Noise: Poisson, se = w*sqrt(n); '~' marks |delta| < 2*se(delta).

Buckets: first match over the host frames above the first guest frame (seg):
  guest code                  leaf is guest code (sub_X / __imp__sub_X / recomp objects,
                              __savegpr*/__restgpr* helpers)
  write-tracking fault (VEH)  KiUserExceptionDispatcher, RtlDispatchException,
                              ExceptionHandlerCallback, TriggerPhysicalMemoryCallbacks,
                              MemoryWritten
  write-tracking arm/protect  WatchCpuMemory, Enable*AccessCallbacks, memory::Protect,
                              NtProtectVirtualMemory, VirtualProtect
  CPU pool copy               PoolCopy*, FlushPoolCopyBatch, sub_82BD2868
  sync/spin/yield (busy)      Ke/Nt wait, delay, event, semaphore, critical section/region,
                              spin lock, yield, SRW, WaitOnAddress, std mutex/condvar
  d3d12+driver                a D3D12/DXGI/driver frame
  native upload/copy/hash     a native-gpu frame + memcpy/Upload/Copy/Hash/XXH/Content/...
  native-gpu other            any other native-gpu frame
  rexlego host / rexruntime / system/other
Wait/io samples are not busy; they are tabled separately by boundary (where Main blocks).

Tables: per-side header, buckets, ranked candidates, leaf categories, boundary (host entry
called by guest code, with its top guest callers), self, inclusive, guest self, guest
inclusive, blocked (wait/io) by boundary, fault detail (faulting guest function, handler
leaf), pool-copy callers, fault-linked guest self (the faulting guest functions' own guest
self time, which holds the kernel fault-entry time), threads by role, busiest threads per
side. --json writes all of it.

Threads by role (all threads, whatever the selection). XThread names and tids differ between
runs, so threads are matched by role, with the w3_thread_per_frame.py rules on the LSPX
trailer names:
  main      "Main XThread"
  gpu_cmd   "GPU Commands"
  vsync     "GPU VSync"
  timerq    "TimerQueue"
  audio     /audio|xma/i
  render    the busiest other "XThread*" (by busy samples)
  worker2   the next busiest
  xt_other  the remaining XThreads
  other     everything else, unnamed threads included
Columns: busy, guest-leaf busy, blocked.

--handoff: one more sequential pass over the samples, in sampling order. A sampler round
samples every live thread once, so a new round starts when a tid repeats. Main and render
are tracked (the busiest thread of each role; gpu_cmd too, if present). Each round gives a
joint state (busy / wait / absent). The output tables that state in ms/frame (= share of
rounds x frame time), next to the independence expectation, plus:
  - Main's busy buckets and where it is busy while render waits (render idles on Main: the
    critical-path Main work), and render's wait boundary meanwhile;
  - Main's wait boundary (<- guest caller) and render's work while Main waits;
  - the overlap (both busy) and both-waiting.
Samples in a round are taken one after another, so the joint state is approximate.
"""
from __future__ import annotations

import argparse
import collections
import csv
import gc
import glob
import importlib.util
import json
import math
import os
import re
import struct
import sys
import time
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
AP_PATH = os.path.join(ROOT, 'DimensionsRecomp', 'tools', 'native-cpu', 'analyze_profile.py')

GUEST_HELPER_RE = re.compile(r'__(?:save|rest)(?:gpr|fpr|vmx|vr)\w*')
FAULT_RE = re.compile(r'KiUserExceptionDispatcher|RtlDispatchException|RtlpCallVectoredHandlers|'
                      r'RtlpExecuteHandlerForException|ExceptionHandlerCallback|'
                      r'TriggerPhysicalMemoryCallbacks|MemoryWritten|AccessViolationCallback|'
                      r'PhysicalHeap::TriggerCallbacks')
ARM_RE = re.compile(r'WatchCpuMemory|EnablePhysicalMemoryAccessCallbacks|EnableAccessCallbacks|'
                    r'memory::Protect\b|PhysicalHeap::Protect|NtProtectVirtualMemory|'
                    r'VirtualProtect')
POOL_RE = re.compile(r'PoolCopy|FlushPoolCopyBatch|sub_82BD2868')
SYNC_RE = re.compile(
    r'NtYieldExecution|SwitchToThread|MaybeYield|SleepPrecise|AlertableSleep|thread::Sleep|'
    r'NtDelayExecution|SleepEx|\bSleep\b|KeDelayExecutionThread|KeWait|NtWait|WaitFor|'
    r'WaitMultiple|KeSetEvent|KeResetEvent|KePulseEvent|NtSetEvent|NtClearEvent|NtPulseEvent|'
    r'ReleaseSemaphore|ReleaseMutant|SignalAndWait|CriticalSection|CriticalRegion|SpinLock|'
    r'KfAcquire|KfRelease|KeAcquire|KeRelease|SRWLock|WaitOnAddress|WakeByAddress|'
    r'AlertThreadByThreadId|RtlpWaitOn|_Mtx_|_Cnd_|mutex|condition_variable|Semaphore',
    re.I)
UPLOAD_RE = re.compile(r'memcpy|memmove|Upload|Copy|XXH|Hash|Checksum|Content|Unchanged|'
                       r'Swizzle|Untile|Convert|Decode|Stamp', re.I)
ALIAS_RE = re.compile(r' \{\+\d+ alias(?:es)?\}$')
MODPFX_RE = re.compile(r'^([\w.\-]+\.(?:dll|exe|sys|drv))!(.*)$', re.I)
FN_RE = re.compile(r'^fn_[0-9A-Fa-f]+ \(near (.+?)\+0x[0-9A-Fa-f]+\)$')

BUCKETS = ('guest code', 'write-tracking fault (VEH)', 'write-tracking arm/protect',
           'CPU pool copy', 'sync/spin/yield (busy)', 'd3d12+driver', 'native upload/copy/hash',
           'native-gpu other', 'rexlego host', 'rexruntime', 'system/other')
CATEGORIES = ('guest', 'rexruntime', 'native-gpu', 'rexlego', 'd3d12+driver', 'system', 'other',
              'unknown')
ROLES = ('main', 'render', 'gpu_cmd', 'timerq', 'worker2', 'vsync', 'audio', 'xt_other', 'other')
HANDOFF_ROLES = ('main', 'render', 'gpu_cmd')
PAIR_KEYS = ('main busy / render busy', 'main busy / render wait', 'main wait / render busy',
             'main wait / render wait')
HANDOFF_DETAILS = (
    ('crit_main_bucket', 'Main busy while render waits, by bucket (render idles on Main: '
                         'critical-path Main work)'),
    ('crit_main_where', 'Main busy while render waits, by guest leaf or host boundary '
                        '(<- guest caller)'),
    ('crit_render_wait', 'render wait boundary while Main is busy'),
    ('mw_main_wait', 'Main wait boundary (<- guest caller) while render is busy'),
    ('mw_render_bucket', 'render busy while Main waits, by bucket'),
    ('mw_render_where', 'render busy while Main waits, by guest leaf or host boundary'),
    ('overlap_main_bucket', 'Main busy while render is busy too (overlap), by bucket'),
    ('both_wait', 'both waiting: Main boundary | render boundary'),
)
SCAN_CHUNK = 1 << 24

_ap = None


def load_ap(path: str = AP_PATH):
    """Import analyze_profile.py once (re-uses an already imported module)."""
    global _ap
    if _ap is None:
        mod = sys.modules.get('analyze_profile')
        if mod is None:
            spec = importlib.util.spec_from_file_location('analyze_profile', path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules['analyze_profile'] = mod
            spec.loader.exec_module(mod)
        _ap = mod
    return _ap


# =============================================================================
# Names and classification (pure functions; unit-tested)
# =============================================================================

def simplify_decorated(raw: str) -> str:
    """'?Name@Ns@@<params>' -> 'Ns::Name' (params dropped); other names unchanged."""
    if not raw.startswith('?'):
        return raw
    s = load_ap().simplify_msvc(raw)
    if s:
        return s
    head = raw[1:].split('@@', 1)[0]
    parts = [p for p in head.split('@') if p]
    return '::'.join(reversed(parts)) if parts else raw


def short_name(name: str) -> str:
    """Display/match key for an analyze_profile Func.name: alias suffix dropped, decorated
    DLL export names simplified, 'fn_<RVA> (near X+0x..)' -> '~X' (RVA-free, so the key
    survives a rebuild of that DLL)."""
    n = ALIAS_RE.sub('', name or '?')
    m = MODPFX_RE.match(n)
    mod, rest = (m.group(1), m.group(2)) if m else (None, n)
    f = FN_RE.match(rest)
    if f:
        rest = '~' + simplify_decorated(f.group(1))
    elif rest.startswith('?'):
        rest = simplify_decorated(rest)
    return f'{mod}!{rest}' if mod else rest


def is_guest(func) -> bool:
    return func.category == 'guest' or bool(GUEST_HELPER_RE.fullmatch(func.raw or ''))


def classify(seg_names, seg_cats, leaf_is_guest: bool) -> str:
    """Bucket of one busy sample. seg_* = the host frames above the first guest frame
    (leaf first); leaf_is_guest = the leaf itself is guest code."""
    if leaf_is_guest:
        return 'guest code'
    if any(FAULT_RE.search(n) for n in seg_names):
        return 'write-tracking fault (VEH)'
    if any(ARM_RE.search(n) for n in seg_names):
        return 'write-tracking arm/protect'
    if any(POOL_RE.search(n) for n in seg_names):
        return 'CPU pool copy'
    if any(SYNC_RE.search(n) for n in seg_names):
        return 'sync/spin/yield (busy)'
    cats = set(seg_cats)
    if 'd3d12+driver' in cats:
        return 'd3d12+driver'
    if 'native-gpu' in cats:
        return ('native upload/copy/hash' if any(UPLOAD_RE.search(n) for n in seg_names)
                else 'native-gpu other')
    if 'rexlego' in cats:
        return 'rexlego host'
    if 'rexruntime' in cats:
        return 'rexruntime'
    return 'system/other'


def compare_rows(ca, cb, wa: float, wb: float, keys=None, top=None, sort=True):
    """Rows {key, a, b, delta, se2, na, nb, noise}; a/b/delta in ms per frame."""
    out = []
    for k in (keys if keys is not None else set(ca) | set(cb)):
        na, nb = ca.get(k, 0), cb.get(k, 0)
        a, b = na * wa, nb * wb
        se2 = 2.0 * math.sqrt(na * wa * wa + nb * wb * wb)
        out.append({'key': k, 'a': a, 'b': b, 'delta': b - a, 'se2': se2, 'na': na, 'nb': nb,
                    'noise': abs(b - a) < se2})
    if sort:
        out.sort(key=lambda r: (-abs(r['delta']), -max(r['a'], r['b']), str(r['key'])))
    return out[:top] if top else out


def fps_from_frames(fj: dict):
    w = (fj or {}).get('window') or {}
    n, s = w.get('rows_by_end_bytes'), w.get('end_bytes_window_s')
    if n and s:
        return n / s, 'frames.json window rows_by_end_bytes/end_bytes_window_s'
    if fj and fj.get('frames') and fj.get('window_s'):
        return fj['frames'] / fj['window_s'], 'frames.json frames/window_s'
    if fj and fj.get('mean_ms'):
        return 1000.0 / fj['mean_ms'], 'frames.json 1000/mean_ms'
    return None, None


def base_role(name: str):
    """w3_thread_per_frame.py role of a thread name; None = an 'XThread*' (ranked later)."""
    if 'Main XThread' in name:
        return 'main'
    if 'GPU Commands' in name:
        return 'gpu_cmd'
    if 'GPU VSync' in name:
        return 'vsync'
    if 'TimerQueue' in name:
        return 'timerq'
    if re.search(r'audio|xma', name, re.I):
        return 'audio'
    if name.startswith('XThread'):
        return None
    return 'other'


def assign_roles(names: dict, busy: dict) -> dict:
    """tid -> role for every tid in busy (busy samples per tid). 'XThread*' threads are
    ranked by busy samples: render, worker2, then xt_other."""
    roles, xt = {}, []
    for t in busy:
        r = base_role((names.get(t) or '').strip())
        if r is None:
            xt.append(t)
        else:
            roles[t] = r
    xt.sort(key=lambda t: (-busy[t], t))
    for i, t in enumerate(xt):
        roles[t] = 'render' if i == 0 else 'worker2' if i == 1 else 'xt_other'
    return roles


def stack_facts(fs, funcs, S):
    """(leaf cls, first guest depth g, host segment above it, boundary key, guest caller) of
    one function stack, leaf first. fs may stop at its first guest frame."""
    g = next((d for d, f in enumerate(fs) if is_guest(funcs[f])), None)
    seg = fs[:g] if g is not None else fs
    if g == 0:
        bkey = '(guest code)'
    elif g is None:
        bkey = '(no guest frame) ' + S(seg[-1])
    else:
        bkey = S(seg[-1])
    return funcs[fs[0]].cls, g, seg, bkey, (S(fs[g]) if g else None)


def pair_stats(pc: dict):
    """Main/render 2x2 over the rounds with both sampled: marginals, conditionals, and the
    counts expected if the two threads were independent."""
    bb, bw = pc.get(PAIR_KEYS[0], 0), pc.get(PAIR_KEYS[1], 0)
    wb, ww = pc.get(PAIR_KEYS[2], 0), pc.get(PAIR_KEYS[3], 0)
    n = bb + bw + wb + ww
    if not n:
        return None
    pm, pr = (bb + bw) / n, (bb + wb) / n
    return {'n_both': n, 'p_main_busy': pm, 'p_render_busy': pr,
            'p_render_wait_given_main_busy': bw / (bb + bw) if bb + bw else None,
            'p_main_wait_given_render_busy': wb / (bb + wb) if bb + wb else None,
            'expected': dict(zip(PAIR_KEYS, (pm * pr * n, pm * (1 - pr) * n,
                                             (1 - pm) * pr * n, (1 - pm) * (1 - pr) * n)))}


# =============================================================================
# Inputs
# =============================================================================

def load_json(path: str):
    try:
        with open(path, encoding='utf-8-sig') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def resolve_side(path: str, label: str, map_override, fps_override, warns: list) -> dict:
    ap = load_ap()
    if os.path.isdir(path):
        run_dir = os.path.abspath(path)
        bins = sorted(glob.glob(os.path.join(run_dir, 'profile-*.bin')), key=os.path.getsize,
                      reverse=True)
        if not bins:
            raise SystemExit(f'{label}: no profile-*.bin in {run_dir}')
        if len(bins) > 1:
            warns.append(f'{label}: {len(bins)} profiles in {run_dir}; using the largest, '
                         f'{os.path.basename(bins[0])}')
        prof = bins[0]
    elif os.path.isfile(path):
        prof = os.path.abspath(path)
        run_dir = os.path.dirname(prof)
    else:
        raise SystemExit(f'{label}: {path} is neither a run dir nor a file')
    run = load_json(os.path.join(run_dir, 'run.json')) or {}
    frames = load_json(os.path.join(run_dir, 'frames.json')) or run.get('frames') or {}
    mp = map_override
    if not mp:
        cands = [os.path.join(run_dir, 'legodimensions.map')]
        meta = run.get('profile_meta') or {}
        if isinstance(meta.get('map'), str):
            cands.insert(0, meta['map'])
        if isinstance(run.get('bin_dir'), str):
            cands.append(os.path.join(run['bin_dir'], 'legodimensions.map'))
        mp = next((c for c in cands if os.path.isfile(c) and os.path.getsize(c) > 4096), None)
        if mp is None:
            raise SystemExit(f'{label}: no legodimensions.map (> 4 KB) in {run_dir} or the run '
                             f'bin_dir; pass --map-{label[-1:] if label else "a"} / '
                             f'--map-a/--map-b')
    bin_dir = run_dir
    if (not os.path.isfile(os.path.join(run_dir, 'rexruntime.dll'))
            and isinstance(run.get('bin_dir'), str) and os.path.isdir(run['bin_dir'])):
        bin_dir = run['bin_dir']
    if fps_override:
        fps, fps_src = float(fps_override), '--fps'
    else:
        fps, fps_src = fps_from_frames(frames)
    if not fps:
        raise SystemExit(f'{label}: no fps (no usable frames.json next to {prof}); pass --fps')
    dur = None
    meta = run.get('profile_meta') or {}
    try:
        dur = max(float(meta['profile_trigger_end']) - float(meta['profile_trigger_start'])
                  - ap.TRIGGER_LATENCY_S, 1e-6)
    except (KeyError, TypeError, ValueError):
        pass
    tcsv = os.path.join(run_dir, 'threads.csv')
    return {'label': label, 'input': path, 'run_dir': run_dir, 'profile': prof, 'map': mp,
            'bin_dir': bin_dir, 'fps': fps, 'fps_source': fps_src, 'duration_fallback': dur,
            'threads_csv': tcsv if os.path.isfile(tcsv) else None,
            'arm_args': run.get('args'), 'env_set': run.get('env_set'),
            'profile_seconds_requested': meta.get('profile_seconds_requested')}


def threads_csv_ms(path, thread_re, fps):
    """thread-cpu cross-check: (name, busy_pct, ms/frame) of the best-matching row."""
    if not path:
        return None
    try:
        with open(path, newline='', encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))
    except OSError:
        return None
    best = None
    for r in rows:
        if thread_re.search(r.get('name') or ''):
            try:
                pct = float(r.get('busy_pct') or 0)
            except ValueError:
                continue
            if best is None or pct > best[1]:
                best = (r['name'], pct)
    return (best[0], best[1], best[1] * 10.0 / fps) if best else None


# =============================================================================
# Per-side analysis
# =============================================================================

def analyse(side: dict, args, thread_re, tid_override, all_threads: bool, warns: list) -> dict:
    ap = load_ap()
    ap._warnings.clear()
    ns = types.SimpleNamespace(no_undname=args.no_undname, keep_params=False,
                               bin_dir=side['bin_dir'], search=args.search or [],
                               driverstore=args.driverstore, extra_map=[],
                               trigger_latency=ap.TRIGGER_LATENCY_S)
    an = ap.Analysis(side['profile'], side['map'], ns, duration_s=side['duration_fallback'],
                     meta=None)
    funcs = an.funcs()
    names = an.prof.thread_names
    label = side['label']
    per_tid = collections.defaultdict(collections.Counter)
    guest_leaf = collections.Counter()
    for (t, fsid), n in an.agg.items():
        leaf = funcs[an.fstacks[fsid][0]]
        per_tid[t][leaf.cls] += n
        if leaf.cls == 'busy' and is_guest(leaf):
            guest_leaf[t] += n
    rounds = an.duration.get('rounds') or an.duration.get('rounds_estimated') or 0
    if not rounds:
        raise SystemExit(f'{label}: profile has no samples')
    w = 1000.0 / (rounds * side['fps'])
    # thread selection
    if all_threads:
        tids = set(per_tid)
        tsel = {'mode': 'all threads', 'tids': sorted(tids)}
    elif tid_override is not None:
        tids = {int(tid_override, 0)}
        tsel = {'mode': '--tid', 'tids': sorted(tids)}
    else:
        cands = sorted((t for t, nm in names.items() if thread_re.search(nm or '')),
                       key=lambda t: -sum(per_tid[t].values()))
        if cands:
            tids = {cands[0]}
            tsel = {'mode': f'name /{thread_re.pattern}/', 'tids': [cands[0]]}
            if len(cands) > 1:
                warns.append(f'{label}: {len(cands)} threads match /{thread_re.pattern}/; using '
                             f'{cands[0]} ({names.get(cands[0])}), the one with most samples')
        else:
            t0 = guest_leaf.most_common(1)[0][0] if guest_leaf else max(
                per_tid, key=lambda t: per_tid[t]['busy'])
            tids = {t0}
            tsel = {'mode': 'fallback: most busy guest-leaf samples', 'tids': [t0]}
            warns.append(f'{label}: no thread name matches /{thread_re.pattern}/ (trailer names: '
                         f'{len(names)}); using tid {t0}, the thread with the most busy '
                         f'guest-code samples. Check the threads table and pass --tid-'
                         f'{"a" if label == args.label_a else "b"} if wrong')
    short_cache = {}

    def S(fid):
        s = short_cache.get(fid)
        if s is None:
            s = short_cache[fid] = short_name(funcs[fid].name)
        return s

    C = collections.Counter
    res = {k: C() for k in ('bucket', 'leafcat', 'boundary', 'self', 'incl', 'guest_self',
                            'guest_incl', 'blocked', 'fault_guest', 'fault_leaf', 'pool_caller',
                            'sync_boundary')}
    callers = collections.defaultdict(C)
    blocked_callers = collections.defaultdict(C)
    totals = C()
    for (t, fsid), n in an.agg.items():
        if t not in tids:
            continue
        fs = an.fstacks[fsid]
        leaf = funcs[fs[0]]
        cls, g, seg, bkey, caller = stack_facts(fs, funcs, S)
        totals[cls] += n
        if cls != 'busy':
            k = bkey if cls == 'wait' else f'[io] {bkey}'
            res['blocked'][k] += n
            if caller:
                blocked_callers[k][caller] += n
            continue
        seg_names = [S(f) for f in seg]
        bucket = classify(seg_names, [funcs[f].category for f in seg], g == 0)
        res['bucket'][bucket] += n
        res['leafcat'][leaf.category] += n
        res['boundary'][bkey] += n
        if caller:
            callers[bkey][caller] += n
        res['self'][S(fs[0])] += n
        for k in {S(f) for f in fs}:
            res['incl'][k] += n
        if g == 0:
            res['guest_self'][S(fs[0])] += n
        for k in {S(f) for f in fs if is_guest(funcs[f])}:
            res['guest_incl'][k] += n
        if bucket == 'write-tracking fault (VEH)':
            res['fault_guest'][caller or bkey] += n
            res['fault_leaf'][S(fs[0])] += n
        elif bucket == 'CPU pool copy':
            res['pool_caller'][caller or bkey] += n
        elif bucket == 'sync/spin/yield (busy)':
            res['sync_boundary'][bkey] += n
    roles = assign_roles(names, {t: c['busy'] for t, c in per_tid.items()})
    threads = []
    for t, c in per_tid.items():
        threads.append({'tid': t, 'name': names.get(t, ''), 'role': roles[t],
                        'samples': sum(c.values()), 'busy': c['busy'], 'wait': c['wait'],
                        'io': c['io'], 'guest': guest_leaf[t], 'busy_ms_per_frame': c['busy'] * w})
    threads.sort(key=lambda r: (-r['busy'], r['tid']))
    by_role = {}
    for r in threads:
        for key in (r['role'], 'all'):
            d = by_role.setdefault(key, {'busy': 0, 'wait': 0, 'io': 0, 'guest': 0, 'samples': 0,
                                         'threads': []})
            for k in ('busy', 'wait', 'io', 'guest', 'samples'):
                d[k] += r[k]
            d['threads'].append([r['tid'], r['name'], r['busy']])
    dur = dict(an.duration)
    tr = an.prof.trailer or {}
    hdr = {
        'label': label, 'run_dir': side['run_dir'], 'profile': side['profile'],
        'profile_bytes': os.path.getsize(side['profile']), 'map': an.map_path,
        'samples': an.prof.sample_count, 'threads_seen': len(per_tid), 'rounds': rounds,
        'rounds_source': 'trailer' if dur.get('rounds') else 'estimated (max per-thread count)',
        'duration': dur, 'timer_mode': tr.get('timer_mode'),
        'observer_effect': an.prof.observer_effect(), 'trailer': bool(tr),
        'fps': side['fps'], 'fps_source': side['fps_source'], 'w_ms_per_frame_per_sample': w,
        'thread_select': tsel, 'thread_names': [names.get(t, '') for t in sorted(tids)],
        'thread_samples': sum(totals.values()), 'busy': totals['busy'], 'wait': totals['wait'],
        'io': totals['io'], 'busy_ms_per_frame': totals['busy'] * w,
        'blocked_ms_per_frame': (totals['wait'] + totals['io']) * w,
        'threads_csv': threads_csv_ms(side['threads_csv'], thread_re, side['fps'])
        if not all_threads else None,
        'arm_args': side.get('arm_args'), 'env_set': side.get('env_set'),
        'timing': an.timing, 'warnings': list(ap._warnings),
    }
    if not all_threads and rounds and hdr['thread_samples'] < 0.9 * rounds:
        warns.append(f'{label}: the selected thread has {hdr["thread_samples"]} samples for '
                     f'{rounds} rounds (< 90%): it was not sampled in every round (started late, '
                     f'exited, or the round count is an estimate)')
    if dur.get('rounds_per_s') and dur['rounds_per_s'] < 250:
        warns.append(f'{label}: {dur["rounds_per_s"]:.0f} rounds/s (< 250): CPU-saturated sampler, '
                     f'attribution usable but noisy')
    handoff = run_handoff(an, side, roles, per_tid, warns) if getattr(
        args, 'handoff', False) else None
    out = {'header': hdr, 'counts': res, 'callers': callers, 'blocked_callers': blocked_callers,
           'threads': threads, 'roles': by_role, 'handoff': handoff, 'w': w}
    del an
    gc.collect()
    return out


# =============================================================================
# Handoff (one sequential pass over the samples)
# =============================================================================

def make_sid_facts(an):
    """sid -> (busy, bucket, boundary, guest caller, where) of one raw profile stack, resolved
    only up to its first guest frame (cached per sid and per address)."""
    funcs = an.funcs()
    resolve = an.sym.resolve
    stacks = an.prof.stacks
    empty = an.sym.empty
    acache, scache, cache = {}, {}, {}

    def S(fid):
        s = scache.get(fid)
        if s is None:
            f = funcs[fid]
            s = scache[fid] = short_name(f.name if f.name is not None else f.raw)
        return s

    def facts(sid):
        r = cache.get(sid)
        if r is not None:
            return r
        key = stacks[sid]
        fs = []
        for d in range(len(key) >> 3):
            a = int.from_bytes(key[d * 8:d * 8 + 8], 'little') - (1 if d else 0)
            f = acache.get(a)
            if f is None:
                f = acache[a] = resolve(a)
            fs.append(f)
            if is_guest(funcs[f]):
                break
        if not fs:
            fs = [empty]
        cls, g, seg, bkey, caller = stack_facts(fs, funcs, S)
        busy = cls == 'busy'
        bucket = classify([S(f) for f in seg], [funcs[f].category for f in seg],
                          g == 0) if busy else None
        where = S(fs[0]) if g == 0 else (f'{bkey} <- {caller}' if caller else bkey)
        r = cache[sid] = (busy, bucket, bkey, caller, where)
        return r

    return facts


def handoff_scan(path, pick, facts, stack_sids, max_depth, chunk=None):
    """One pass over the LSP1 samples in sampling order, streamed chunk bytes at a time. A new
    sampler round starts when a tid repeats. pick: role -> tid of the tracked threads;
    stack_sids: raw stack bytes -> sid for their stacks. Returns round-level counters."""
    chunk = chunk or SCAN_CHUNK
    tid_role = {t: r for r, t in pick.items()}
    roles = [r for r in HANDOFF_ROLES if r in pick]
    joint, pair = collections.Counter(), collections.Counter()
    det = {k: collections.Counter() for k, _ in HANDOFF_DETAILS}
    hdr = struct.Struct('<II').unpack_from
    last, cur = {}, {}
    rnd = nsamp = rounds = 0
    stop = None

    def close():
        st, fx = {}, {}
        for r in roles:
            sid = cur.get(r)
            if sid is None:
                st[r] = 'absent'
            else:
                fx[r] = facts(sid)
                st[r] = 'busy' if fx[r][0] else 'wait'
        joint[' / '.join(f'{r} {st[r]}' for r in roles)] += 1
        pair[f"main {st['main']} / render {st['render']}"] += 1
        m, rd = fx.get('main'), fx.get('render')
        if m is not None and rd is not None:
            if m[0] and not rd[0]:
                det['crit_main_bucket'][m[1]] += 1
                det['crit_main_where'][m[4]] += 1
                det['crit_render_wait'][rd[2]] += 1
            elif rd[0] and not m[0]:
                det['mw_main_wait'][m[4]] += 1
                det['mw_render_bucket'][rd[1]] += 1
                det['mw_render_where'][rd[4]] += 1
            elif m[0]:
                det['overlap_main_bucket'][m[1]] += 1
            else:
                det['both_wait'][f'{m[2]} | {rd[2]}'] += 1
        cur.clear()

    with open(path, 'rb') as f:
        head = f.read(8)
        if head[:4] != b'LSP1':
            raise SystemExit(f'{path}: not an LSP1 profile')
        (nmod,) = struct.unpack_from('<I', head, 4)
        for _ in range(nmod):
            _base, _size, nlen = struct.unpack('<QII', f.read(16))
            f.seek(nlen, 1)
        (nsamples,) = struct.unpack('<Q', f.read(8))
        data, off = f.read(chunk), 0
        end = len(data)
        for _ in range(nsamples):
            if off + 8 > end:
                data, off = data[off:] + f.read(chunk), 0
                end = len(data)
                if end < 8:
                    stop = f'truncated after {nsamp} of {nsamples} samples'
                    break
            tid, depth = hdr(data, off)
            if depth > max_depth:
                stop = f'corrupt sample {nsamp} (depth {depth})'
                break
            need = 8 + (depth << 3)
            if off + need > end:
                data, off = data[off:] + f.read(max(chunk, need)), 0
                end = len(data)
                if need > end:
                    stop = f'truncated after {nsamp} of {nsamples} samples'
                    break
            if last.get(tid) == rnd:
                close()
                rounds += 1
                rnd += 1
            last[tid] = rnd
            role = tid_role.get(tid)
            if role is not None:
                cur[role] = stack_sids.get(data[off + 8:off + need])
            off += need
            nsamp += 1
    if nsamp:
        close()
        rounds += 1
    return {'rounds': rounds, 'samples': nsamp, 'roles': roles, 'tids': dict(pick),
            'joint': joint, 'pair': pair, 'details': det, 'stop': stop}


def run_handoff(an, side, roles, per_tid, warns):
    """--handoff for one side: pick the busiest thread of each tracked role, then scan."""
    label = side['label']
    pick = {}
    for t, r in roles.items():
        if r in HANDOFF_ROLES and (r not in pick or per_tid[t]['busy'] > per_tid[pick[r]]['busy']):
            pick[r] = t
    if 'main' not in pick or 'render' not in pick:
        warns.append(f'{label}: --handoff skipped: it needs a "Main XThread" and a render thread '
                     f'(busiest other "XThread*") among the LSPX trailer names (roles found: '
                     f'{", ".join(sorted(set(roles.values())))})')
        return None
    tracked = set(pick.values())
    stacks = an.prof.stacks
    stack_sids = {stacks[k >> 32]: k >> 32 for k in an.prof.counts
                  if (k & 0xFFFFFFFF) in tracked}
    t0 = time.perf_counter()
    h = handoff_scan(side['profile'], pick, make_sid_facts(an), stack_sids, load_ap().MAX_DEPTH)
    h['seconds'] = round(time.perf_counter() - t0, 2)
    h['names'] = {r: an.prof.thread_names.get(t, '') for r, t in pick.items()}
    h['rounds_trailer'] = an.duration.get('rounds')
    if h['stop']:
        warns.append(f"{label}: handoff scan stopped: {h['stop']}")
    if h['samples'] != an.prof.sample_count:
        warns.append(f"{label}: the handoff scan read {h['samples']} samples, the profile parse "
                     f"{an.prof.sample_count}")
    rt = h['rounds_trailer']
    if rt and abs(h['rounds'] - rt) > 0.02 * rt:
        warns.append(f"{label}: the handoff scan found {h['rounds']} rounds by tid repetition, "
                     f"the trailer {rt} (> 2% apart): the joint states are approximate")
    return h


# =============================================================================
# Report
# =============================================================================

def table(rows, headers, right=()):
    w = [len(h) for h in headers]
    for r in rows:
        for k, c in enumerate(r):
            w[k] = max(w[k], len(str(c)))
    fmt = lambda r: '  '.join(str(c).rjust(w[k]) if k in right else str(c).ljust(w[k])
                              for k, c in enumerate(r)).rstrip()
    return '\n'.join([fmt(headers), fmt(['-' * x for x in w])] + [fmt(r) for r in rows])


def _cut(s, n=96):
    s = str(s)
    return s if len(s) <= n else s[:n - 3] + '...'


def _top_callers(counter, n=3):
    tot = sum(counter.values()) or 1
    return '; '.join(f'{_cut(k, 44)} {100.0 * c / tot:.0f}%' for k, c in counter.most_common(n))


def _cmp_lines(rows, extra=None, keyw=96):
    body = []
    for r in rows:
        line = [f"{r['a']:.3f}", f"{r['b']:.3f}", f"{r['delta']:+.3f}{'~' if r['noise'] else ' '}",
                f"{r['se2']:.3f}", r['na'], r['nb'], _cut(r['key'], keyw)]
        if extra is not None:
            line.append(extra(r))
        body.append(line)
    hdr = ['A ms/f', 'B ms/f', 'delta', '2se', 'nA', 'nB', 'key']
    if extra is not None:
        hdr.append('top guest callers (B, else A)')
    return table(body, hdr, right=(0, 1, 2, 3, 4, 5))


def _role_names(d) -> str:
    th = d['threads']
    if len(th) == 1:
        return th[0][1] or f'tid {th[0][0]}'
    return f'{len(th)} threads' if th else ''


def role_rows(A: dict, B: dict) -> list:
    """Threads matched by role: busy, guest-leaf busy and blocked ms/frame, A vs B."""
    wa, wb = A['w'], B['w']
    E = {'busy': 0, 'wait': 0, 'io': 0, 'guest': 0, 'samples': 0, 'threads': []}
    rows = []
    for role in ROLES + ('all',):
        a, b = A['roles'].get(role, E), B['roles'].get(role, E)
        if not (a['samples'] or b['samples']):
            continue
        r = compare_rows({role: a['busy']}, {role: b['busy']}, wa, wb)[0]
        g = compare_rows({role: a['guest']}, {role: b['guest']}, wa, wb)[0]
        r.update(guest_a=g['a'], guest_b=g['b'], guest_delta=g['delta'], guest_se2=g['se2'],
                 blocked_a=(a['wait'] + a['io']) * wa, blocked_b=(b['wait'] + b['io']) * wb,
                 threads_a=len(a['threads']), threads_b=len(b['threads']),
                 names_a=_role_names(a), names_b=_role_names(b))
        rows.append(r)
    return rows


def _joint_rows(h: dict, w: float) -> list:
    if len(h.get('roles') or ()) < 3:
        return []
    return [[k, n, n * w] for k, n in sorted(h['joint'].items(), key=lambda kv: (-kv[1], kv[0]))]


def handoff_report(A: dict, B: dict, top: int):
    hA, hB = A.get('handoff'), B.get('handoff')
    if not hA and not hB:
        return None
    E = {'rounds': 0, 'samples': 0, 'pair': {}, 'joint': {}, 'roles': [], 'tids': {},
         'names': {}, 'rounds_trailer': None, 'seconds': None,
         'details': {k: {} for k, _ in HANDOFF_DETAILS}}
    ha, hb = hA or E, hB or E
    wa = 1000.0 / (ha['rounds'] * A['header']['fps']) if ha['rounds'] else 0.0
    wb = 1000.0 / (hb['rounds'] * B['header']['fps']) if hb['rounds'] else 0.0
    keys = list(PAIR_KEYS) + sorted((set(ha['pair']) | set(hb['pair'])) - set(PAIR_KEYS))
    out = {'w_a': wa, 'w_b': wb,
           'pair': [r for r in compare_rows(ha['pair'], hb['pair'], wa, wb, keys=keys, sort=False)
                    if r['na'] or r['nb']],
           'pair_counts': {'a': dict(ha['pair']), 'b': dict(hb['pair'])},
           'stats': {'a': pair_stats(ha['pair']), 'b': pair_stats(hb['pair'])},
           'details': {k: compare_rows(ha['details'][k], hb['details'][k], wa, wb, top=top)
                       for k, _ in HANDOFF_DETAILS},
           'joint': {'a': _joint_rows(ha, wa), 'b': _joint_rows(hb, wb)}}
    for s, h, side in (('a', ha, A), ('b', hb, B)):
        out[s] = {'label': side['header']['label'], 'rounds': h['rounds'],
                  'rounds_trailer': h['rounds_trailer'], 'samples': h['samples'],
                  'roles': h['roles'], 'tids': h['tids'], 'names': h['names'],
                  'seconds': h['seconds'], 'frame_ms': 1000.0 / side['header']['fps']}
    return out


def build_report(A: dict, B: dict, args, warns: list) -> dict:
    wa, wb = A['w'], B['w']
    ca, cb = A['counts'], B['counts']
    top = args.top
    rep = {'tool': 'prof_main_compare.py', 'schema': 1, 'a': A['header'], 'b': B['header'],
           'units': 'ms of CPU per frame (busy samples) unless noted'}
    rep['buckets'] = compare_rows(ca['bucket'], cb['bucket'], wa, wb, keys=BUCKETS, sort=False)
    rep['buckets'].append(compare_rows({'total busy': A['header']['busy']},
                                       {'total busy': B['header']['busy']}, wa, wb)[0])
    rep['buckets'].append(compare_rows(
        {'blocked (wait/io, not CPU)': A['header']['wait'] + A['header']['io']},
        {'blocked (wait/io, not CPU)': B['header']['wait'] + B['header']['io']}, wa, wb)[0])
    rep['candidates'] = sorted((r for r in rep['buckets'][:len(BUCKETS)] if r['delta'] > 0),
                               key=lambda r: -r['delta'])
    rep['leaf_categories'] = compare_rows(ca['leafcat'], cb['leafcat'], wa, wb, keys=CATEGORIES,
                                          sort=False)
    for key in ('boundary', 'self', 'incl', 'guest_self', 'guest_incl', 'blocked',
                'fault_guest', 'fault_leaf', 'pool_caller', 'sync_boundary'):
        rep[key] = compare_rows(ca[key], cb[key], wa, wb, top=top)
    for r in rep['boundary']:
        src = B['callers'].get(r['key']) or A['callers'].get(r['key']) or {}
        r['callers'] = collections.Counter(src).most_common(5)
    for r in rep['blocked']:
        src = B['blocked_callers'].get(r['key']) or A['blocked_callers'].get(r['key']) or {}
        r['callers'] = collections.Counter(src).most_common(5)
    rep['threads'] = {'a': A['threads'][:12], 'b': B['threads'][:12]}
    rep['roles'] = role_rows(A, B)
    rep['fault_linked'] = []
    for r in rep['fault_guest']:
        k = r['key']
        g = compare_rows({k: ca['guest_self'].get(k, 0)}, {k: cb['guest_self'].get(k, 0)},
                         wa, wb)[0]
        g.update(fault_a=r['a'], fault_b=r['b'], fault_delta=r['delta'])
        rep['fault_linked'].append(g)
    rep['handoff'] = handoff_report(A, B, top)
    rep['warnings'] = list(warns) + [f'A: {x}' for x in A['header']['warnings']] + \
        [f'B: {x}' for x in B['header']['warnings']]
    return rep


def render(rep: dict) -> str:
    L = []
    a, b = rep['a'], rep['b']
    L.append(f"prof_main_compare: A = {a['label']}, B = {b['label']}; {rep['units']}")
    L.append("'~' = |delta| < 2se (Poisson); w = 1000/(rounds*fps) ms/frame per sample")
    for side, h in (('A', a), ('B', b)):
        d = h['duration']
        tc = h['threads_csv']
        L += ['', f"[{side}] {h['label']}: {h['run_dir']}",
              f"  profile {os.path.basename(h['profile'])} ({h['profile_bytes'] / 1e6:.1f} MB), "
              f"map {h['map']}",
              f"  samples {h['samples']}, threads {h['threads_seen']}, rounds {h['rounds']} "
              f"({h['rounds_source']}), duration "
              f"{(str(round(d['seconds'], 2)) + ' s') if d.get('seconds') else 'n/a'} "
              f"[{d.get('source')}], rounds/s {d.get('rounds_per_s', 'n/a')}, timer_mode "
              f"{h['timer_mode']} (observer effect {h['observer_effect']})",
              f"  fps {h['fps']:.2f} [{h['fps_source']}] -> w {h['w_ms_per_frame_per_sample']:.6f}",
              f"  thread {h['thread_select']['mode']}: tids {h['thread_select']['tids'][:6]}"
              f"{' ...' if len(h['thread_select']['tids']) > 6 else ''} "
              f"{', '.join(n for n in h['thread_names'][:3] if n)}",
              f"  thread samples {h['thread_samples']} (busy {h['busy']}, wait {h['wait']}, io "
              f"{h['io']}): busy {h['busy_ms_per_frame']:.3f} ms/frame, blocked "
              f"{h['blocked_ms_per_frame']:.3f} ms/frame"
              + (f"; threads.csv {tc[0]} {tc[1]}% -> {tc[2]:.3f} ms/frame" if tc else '')]
        if h.get('arm_args'):
            L.append('  args: ' + ' '.join(x for x in h['arm_args'] if not x.startswith(
                ('--log_file', '--perf_log_csv'))))
        if h.get('env_set'):
            L.append('  env: ' + ', '.join(f'{k}={_cut(v, 40)}' for k, v in h['env_set'].items()))
    if rep['warnings']:
        L.append('')
        L += [f'warning: {w}' for w in rep['warnings']]
    L += ['', '== buckets (busy ms/frame; first match over the host frames above the first '
              'guest frame) ==', _cmp_lines(rep['buckets'], keyw=40)]
    L += ['', '== ranked candidates (buckets with B > A, largest first) ==']
    for i, r in enumerate(rep['candidates'], 1):
        L.append(f"{i:2}. {r['key']:<28} {r['delta']:+.3f} ms/frame (2se {r['se2']:.3f})"
                 f"{'  ~noise' if r['noise'] else ''}")
    L += ['', '== leaf categories (busy) ==', _cmp_lines(rep['leaf_categories'], keyw=20)]
    sections = (
        ('boundary', 'boundary: host function entered from guest code (busy, by |delta|)', True),
        ('self', 'self (leaf function, busy)', False),
        ('incl', 'inclusive (busy)', False),
        ('guest_self', 'guest self (guest leaf, busy)', False),
        ('guest_incl', 'guest inclusive (guest functions on the stack, busy)', False),
        ('blocked', 'blocked: wait/io samples by boundary (ms/frame blocked, not CPU)', True),
        ('fault_guest', 'write-tracking faults by faulting guest function', False),
        ('fault_leaf', 'write-tracking faults by handler leaf', False),
        ('pool_caller', 'CPU pool copy by guest caller', False),
        ('sync_boundary', 'sync/spin/yield (busy) by boundary', False),
    )
    for key, title, with_callers in sections:
        rows = rep[key]
        if not rows:
            continue
        L += ['', f'== {title} ==']
        L.append(_cmp_lines(rows, extra=(lambda r: _top_callers(collections.Counter(
            dict(r.get('callers') or [])))) if with_callers else None))
    if rep.get('fault_linked'):
        L += ['', '== fault-linked: guest self of the faulting guest functions (it holds the '
                  'kernel fault-entry time) ==']
        L.append(table([[f"{r['fault_delta']:+.3f}", f"{r['a']:.3f}", f"{r['b']:.3f}",
                         f"{r['delta']:+.3f}{'~' if r['noise'] else ' '}", f"{r['se2']:.3f}",
                         _cut(r['key'], 80)] for r in rep['fault_linked']],
                       ['fault delta', 'A self', 'B self', 'self delta', '2se',
                        'faulting guest function'], right=(0, 1, 2, 3, 4)))
    hr = rep.get('handoff')
    if hr:
        L += ['', '== handoff: Main vs render, joint state per sampler round (ms/frame = share of '
                  'rounds x frame time) ==',
              'busy = running or runnable; wait = wait/io leaf; absent = not sampled that round. '
              'A round samples threads one after another, so the joint state is approximate.']
        for s in ('a', 'b'):
            m = hr[s]
            L.append(f"  [{s.upper()}] {m['label']}: rounds {m['rounds']} (trailer "
                     f"{m['rounds_trailer']}), samples {m['samples']}, frame {m['frame_ms']:.3f} "
                     f"ms, scan {m['seconds']} s; tracked " + ', '.join(
                         f"{r} {t} {_cut(m['names'].get(r, ''), 28)}" for r, t in m['tids'].items()))
        L.append(_cmp_lines(hr['pair'], keyw=40))
        rows = []
        for k in PAIR_KEYS:
            row = [k]
            for s in ('a', 'b'):
                st, w = hr['stats'][s], hr['w_' + s]
                row += [f"{hr['pair_counts'][s].get(k, 0) * w:.3f}",
                        f"{st['expected'][k] * w:.3f}" if st else '-']
            rows.append(row)
        L += ['', 'observed vs expected if Main and render were independent (ms/frame):',
              table(rows, ['state', 'A obs', 'A indep', 'B obs', 'B indep'], right=(1, 2, 3, 4))]
        pct = lambda x: f'{x:.1%}' if x is not None else 'n/a'
        for s in ('a', 'b'):
            st = hr['stats'][s]
            if st:
                L.append(f"  [{s.upper()}] P(main busy) {pct(st['p_main_busy'])}, P(render busy) "
                         f"{pct(st['p_render_busy'])}, P(render wait | main busy) "
                         f"{pct(st['p_render_wait_given_main_busy'])}, P(main wait | render busy) "
                         f"{pct(st['p_main_wait_given_render_busy'])}")
        for k, title in HANDOFF_DETAILS:
            if hr['details'][k]:
                L += ['', f'== handoff: {title} ==', _cmp_lines(hr['details'][k])]
        for s in ('a', 'b'):
            if hr['joint'][s]:
                L += ['', f"== handoff: joint state of {', '.join(hr[s]['roles'])}, "
                          f"{hr[s]['label']} =="]
                L.append(table([[k, n, f'{ms:.3f}'] for k, n, ms in hr['joint'][s]],
                               ['state', 'rounds', 'ms/f'], right=(1, 2)))
    if rep.get('roles'):
        L += ['', '== threads by role (all threads, matched by role; busy ms/frame; guest = busy '
                  'with a guest leaf; blocked = wait/io) ==']
        L.append(table([[r['key'], f"{r['a']:.3f}", f"{r['b']:.3f}",
                         f"{r['delta']:+.3f}{'~' if r['noise'] else ' '}", f"{r['se2']:.3f}",
                         f"{r['guest_a']:.3f}", f"{r['guest_b']:.3f}", f"{r['guest_delta']:+.3f}",
                         f"{r['blocked_a']:.3f}", f"{r['blocked_b']:.3f}", r['na'], r['nb'],
                         _cut(r['names_a'], 26), _cut(r['names_b'], 26)] for r in rep['roles']],
                       ['role', 'A busy', 'B busy', 'delta', '2se', 'A guest', 'B guest',
                        'g delta', 'A blocked', 'B blocked', 'nA', 'nB', 'A thread', 'B thread'],
                       right=tuple(range(1, 12))))
    for side in ('a', 'b'):
        L += ['', f"== busiest threads, {rep[side]['label']} (busy ms/frame) =="]
        L.append(table([[t['tid'], t.get('role', ''), _cut(t['name'], 32), t['samples'],
                         t['busy'], t['wait'], t['io'], f"{t['busy_ms_per_frame']:.3f}"]
                        for t in rep['threads'][side]],
                       ['tid', 'role', 'name', 'samples', 'busy', 'wait', 'io', 'busy ms/f'],
                       right=(0, 3, 4, 5, 6, 7)))
    return '\n'.join(L) + '\n'


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('a', help='A run dir or profile .bin (the reference)')
    p.add_argument('b', help='B run dir or profile .bin')
    p.add_argument('--label-a', default='A')
    p.add_argument('--label-b', default='B')
    p.add_argument('--thread-re', default=r'^Main XThread',
                   help='thread-name regex (LSPX trailer names); default %(default)s')
    p.add_argument('--all-threads', action='store_true', help='all threads together')
    p.add_argument('--tid-a')
    p.add_argument('--tid-b')
    p.add_argument('--fps-a', type=float)
    p.add_argument('--fps-b', type=float)
    p.add_argument('--map-a')
    p.add_argument('--map-b')
    p.add_argument('--top', type=int, default=25)
    p.add_argument('-o', '--output')
    p.add_argument('--json')
    p.add_argument('--search', action='append', metavar='DIR')
    p.add_argument('--driverstore', action='store_true')
    p.add_argument('--no-undname', action='store_true')
    p.add_argument('--handoff', action='store_true',
                   help='Main/render joint-state analysis (one more sequential pass)')
    args = p.parse_args(argv)
    load_ap()
    thread_re = re.compile(args.thread_re)
    warns: list[str] = []
    sa = resolve_side(args.a, args.label_a, args.map_a, args.fps_a, warns)
    sb = resolve_side(args.b, args.label_b, args.map_b, args.fps_b, warns)
    A = analyse(sa, args, thread_re, args.tid_a, args.all_threads, warns)
    B = analyse(sb, args, thread_re, args.tid_b, args.all_threads, warns)
    rep = build_report(A, B, args, warns)
    text = render(rep)
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    else:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stdout.write(text)
    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(rep, f, indent=1, default=str)
    return 0


if __name__ == '__main__':
    sys.exit(main())

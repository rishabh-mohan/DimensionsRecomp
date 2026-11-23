"""Agent 3 helper preflight (read-only outside build/agent3/s4b/preflight/).
1. Builds preflight/s4b_check_proposed.py from build/agent3/s4b/s4b_check.py by exact-string replacements (each old
   string must occur exactly once) and writes preflight/s4b_check_proposed.diff (unified diff of the PROPOSAL; the copy
   has one extra preflight-only sys.path line so it can import ../../s4a/s4a_check.py from here).
2. Regex unit checks: every proof-line regex/needle of the old and the proposed script against lines made from the C++
   format strings of the S4b sources (fmt {} placeholders rendered with Python str.format, same spec syntax).
3. Synthetic run dirs (preflight/synth/<case>/game.log + run.json) made from the same format strings; runs the old and
   the proposed script on each (--row, no base) -> preflight/synth-compare.txt.
usage: python -B build/agent3/s4b/preflight/make_proposed.py
"""
import difflib
import importlib.util
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, '..', 's4b_check.py'))
OUT = os.path.join(HERE, 's4b_check_proposed.py')
DIFF = os.path.join(HERE, 's4b_check_proposed.diff')
SYN = os.path.join(HERE, 'synth')
SYN_OUT = os.path.join(HERE, 'synth-out')
CMP = os.path.join(HERE, 'synth-compare.txt')


def b(s):
    return s[1:] if s.startswith('\n') else s


R = []


def rep(label, old, new):
    R.append((label, b(old), b(new)))


# ---------------------------------------------------------------- 1. the proposal
rep('K_DEFAULT (+GWS, DC_HDR)', r'''
# K = C1's verify-mismatch line (gate A). PROVISIONAL until the text is read from the C1 source; c1_other lists every
# C1 line that no known family matches, so a K line with another wording still shows up there.
K_DEFAULT = r'(?i)(keep.?watch|verify).*(mismatch|differ|changed)'
''', r'''
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
''')
rep('GONE_OK_DEFAULT', r'''
GONE_OK_DEFAULT = r'\] Toypad\[(Read |Write)\] |S4 upload hash|slow frame #'
''', r'''
# logdiff keys print digits as '#' ("[gpu] S# upload hash: frame # calls # ..."), hence S[#\d].
GONE_OK_DEFAULT = r'\] Toypad\[(Read |Write)\] |S[#\d] upload hash|slow frame #'
''')
rep('FAM c1_verify_on/c1_verify_f', r'''
    ('c1_blocked', 'C1 keep-watch: blocked for this process', None),
''', r'''
    ('c1_blocked', 'C1 keep-watch: blocked for this process', None),
    ('c1_verify_on', 'C1 verify: on. Hashing CPU uploads', None),
    ('c1_verify_f', 'C1 verify F: page ', None),
''')
rep('FAM gpu_wait_on', r'''
    ('gpu_wait_backoff', 'GPU wait back-off', None),
''', r'''
    ('gpu_wait_backoff', 'GPU wait back-off', None),
    ('gpu_wait_on', 'GPU wait back-off: ON (', None),
''')
rep('FAM dred', r'''
    ('debug_layer', 'ebug layer', None),
''', r'''
    ('debug_layer', 'ebug layer', None),
    ('dred', 'DRED (Device Removed Extended Data) enabled', None),
''')
rep('ITEM_FAMS', r'''
ITEM_FAMS = ['c1_any', 'split_init', 'split', 'deferred_counters', 'gpu_wait', 'memexport']
''', r'''
ITEM_FAMS = ['c1_any', 'c1_verify_on', 'c1_verify_f', 'k', 'split_init', 'split', 'deferred_counters', 'gpu_wait',
             'memexport']
''')
rep('SHOW', r'''
SHOW = ['c1_any', 'k', 'c1_other', 'recovered_stale', 'unhandled_phys', 'protect_failed', 'split_init', 'split',
        'deferred_counters', 'gpu_wait', 'memexport', 'slow_frame', 's4_upload_hash', 'precise_wait', 'miss_cache',
        'stuck_lock', 'minidump', 'fatal', 'debug_layer', 'd3d12_msg']
''', r'''
SHOW = ['c1_any', 'k', 'c1_verify_on', 'c1_verify_f', 'c1_other', 'recovered_stale', 'unhandled_phys', 'protect_failed',
        'split_init', 'split', 'deferred_counters', 'gpu_wait', 'memexport', 'slow_frame', 's4_upload_hash', 'precise_wait',
        'miss_cache', 'stuck_lock', 'minidump', 'fatal', 'debug_layer', 'dred', 'd3d12_msg']
''')
rep('scan: GPU wait stats parse', r'''
                if 'gpu_wait_stats' in got:
                    S['gws'].append((ts[11:], kv(msg.split('GPU wait stats', 1)[1])))
''', r'''
                if 'gpu_wait_stats' in got:
                    mm = GWS.search(msg)
                    if mm:
                        S['gws'].append((ts[11:], {k: num(v) for k, v in zip(GWS_KEYS, mm.groups())}))
''')
rep('scan: deferred_counters header parse', r'''
                if 'deferred_counters' in got and ('lists' in msg or 'seconds' in msg):
                    S['dc'].append((ts[11:], kv(msg.split('deferred_counters', 1)[1])))
''', r'''
                mh = DC_HDR.search(msg) if 'deferred_counters' in got else None
                if mh:
                    g = [num(x) for x in mh.groups()]
                    S['dc'].append((ts[11:], {'seconds': g[0], 'lists': g[1], 'kb': g[2], 'barriers': g[3],
                                              'kb_per_list': round(g[2] / float(g[1]), 2) if g[1] else 0}))
''')
rep('row s4b04: verify armed + F note', r'''
        if r == 's4b04':
            chk(n['k'] == 0, 'verify-mismatch (K) lines %d (gate A, menus part)' % n['k'])
''', r'''
        if r == 's4b04':
            chk(n['c1_verify_on'] >= 1, 'C1 verify armed: "C1 verify: on. Hashing CPU uploads ..." x%d (without it K = 0 '
                'proves nothing)' % n['c1_verify_on'])
            chk(n['k'] == 0, 'verify-mismatch (K) lines %d (gate A, menus part)' % n['k'])
            chk(None, 'C1 verify F lines (write-fault side, not gate A): %d %s' % (
                n['c1_verify_f'], (S['first']['c1_verify_f'] or ['-'])[0][-100:]))
''')
rep('row s4b09: KB per list for <N>', r'''
        chk(len(S['dc']) >= 1, 'deferred_counters headers %d (about every 10 s; elapsed %.0f s -> ~%d expected)' % (
            len(S['dc']), el, int(el // 10)))
''', r'''
        chk(len(S['dc']) >= 1, 'deferred_counters headers %d (about every 10 s; elapsed %.0f s -> ~%d expected)' % (
            len(S['dc']), el, int(el // 10)))
        kpl = sorted(d['kb_per_list'] for _, d in S['dc'] if d.get('lists'))
        med = kpl[len(kpl) // 2] if kpl else None
        chk(None, 'KB per list per header: median %s (min %s, max %s; %d headers); half the median %s (QUEUE.md: <N> ~ '
            'half; Agent 7 sets N)' % (med, kpl[0] if kpl else None, kpl[-1] if kpl else None, len(kpl),
                                        round(med / 2.0, 1) if kpl else None))
''')
rep('split rows: s4b25 may have no split line', r'''
        chk(bool(sp) and spmax.get('failed', 0) == 0, 'failed=0 in every d3d12_submit_split line (max %s over %s lines)' % (
            spmax.get('failed'), sp.get('lines', 0)))
''', r'''
        if sp or r != 's4b25':
            chk(bool(sp) and spmax.get('failed', 0) == 0, 'failed=0 in every d3d12_submit_split line (max %s over %s lines)' % (
                spmax.get('failed'), sp.get('lines', 0)))
        else:
            chk(None, 'no d3d12_submit_split line (printed only while a split is due, at most every 10 s): failed not judged')
''')
rep('row s4b15: DRED + not testable note', r'''
        if r == 's4b15':
            chk(bool(ld) and ld['NEW'] == 0, 'no debug-layer message that row 14 lacks (NEW %s beside split lines)' % (ld and ld['NEW']))
''', r'''
        if r == 's4b15':
            chk(n['dred'] >= 1 and n['debug_layer'] == 0, 'd3d12_debug on: DRED line x%d, debug-layer enable failure x%d' % (
                n['dred'], n['debug_layer']))
            chk(bool(ld) and ld['NEW'] == 0, 'no NEW warning key vs row 14 (NEW %s beside split lines)' % (ld and ld['NEW']))
            chk(None, 'debug-layer messages go to the debugger (the InfoQueue has no log callback), not game.log: "no '
                'message row 14 lacks" is not testable headless')
''')
rep('rows s4b14/17/18', r'''
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
''', r'''
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
        chk(n['gpu_wait_on'] == 1 and n['gpu_wait_backoff'] == 1 and 'quantum 250 us' in on1 and 'GetData hook built' in on1,
            'one "GPU wait back-off: ON (quantum 250 us, ...); ...; GetData hook built." line (ON x%d, back-off lines x%d): %s' % (
                n['gpu_wait_on'], n['gpu_wait_backoff'], on1[-110:]))
        chk(gwmax.get('sleep_fail', 0) == 0, 'sleep_fail = 0 (max %s over %s stats lines)' % (gwmax.get('sleep_fail'), gw.get('lines', 0)))
        chk(n['stuck_lock'] == 0, 'no STUCK-LOCK (%d)' % n['stuck_lock'])
''')
rep('scenes: attract/idle misses -> note', r'''
            if same_scn and missing:
                misses.append('base scenes missing in cand: %s' % missing)
''', r'''
            soft = [k for k in missing if k not in FRONT_END] if scn in ('A', 'M') or scn.startswith('I') else []
            hard = [k for k in missing if k not in soft]
            if same_scn and hard:
                misses.append('base scenes missing in cand: %s' % hard)
            if same_scn and soft:
                say('  note: attract/idle scenes missing in cand (timing after the route; not a BASE item): %s' % soft)
''')
rep('marks prefix without up-2', r'''
            pre = names[:names.index('up-2') + 1] if 'up-2' in names else names
''', r'''
            pre = names[:names.index('up-2') + 1] if 'up-2' in names else [k for k in names if not k.startswith('idle-') and k != 'end']
''')

IMPORT_OLD = "sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', 's4a')))\n"
IMPORT_NEW = IMPORT_OLD + "sys.path.insert(1, os.path.normpath(os.path.join(HERE, '..', '..', 's4a')))  # preflight copy only\n"


def build():
    with open(SRC, encoding='utf-8', newline='') as f:
        raw = f.read()
    nl = '\r\n' if '\r\n' in raw else '\n'
    orig = raw.replace('\r\n', '\n')
    text = orig
    log = []
    for label, old, new in R:
        c = text.count(old)
        if c != 1:
            raise SystemExit('replacement %r: old text found %d times' % (label, c))
        text = text.replace(old, new)
        log.append('applied: %s' % label)
    d = difflib.unified_diff(orig.splitlines(True), text.splitlines(True), 'a/build/agent3/s4b/s4b_check.py',
                             'b/build/agent3/s4b/s4b_check.py', n=2)
    with open(DIFF, 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(d)
    assert text.count(IMPORT_OLD) == 1
    runnable = text.replace(IMPORT_OLD, IMPORT_NEW)
    compile(runnable, OUT, 'exec')
    with open(OUT, 'w', encoding='utf-8', newline=nl) as f:
        f.write(runnable)
    return log, nl


# ---------------------------------------------------------------- 2./3. format strings (C++ fmt -> Python format)
F = {
    # sdk/src/system/xmemory.cpp (o1-v3 / snap1)
    'c1_init_on': 'C1 keep-watch: on (with physical_protect_hold_global_lock)',                     # :174
    'c1_init_blocked': 'C1 keep-watch: on, but blocked for this process (native renderer)',          # :169
    'c1_init_nohold': 'C1 keep-watch: on, but physical_protect_hold_global_lock is off, so no protect is kept',  # :171
    'c1_first': 'C1 keep-watch: first kept protect at {:08X}, {} bytes',                             # :784
    'c1_kept': 'C1 keep-watch: {} protects kept so far',                                             # :786
    'c1_blocked': 'C1 keep-watch: blocked for this process (native renderer); every protect takes the normal path',  # :794
    # src/graphics/shared_memory.cpp
    'c1_verify_on': 'C1 verify: on. Hashing CPU uploads; K checks keep-watch protects, F checks write faults',  # :689
    'c1_verify': 'C1 verify {}: page {:08X} changed since its upload ({} so far){}',                 # :733
    # src/graphics/d3d12/command_processor.cpp
    'split_init': 'd3d12_submit_split_kb: splitting submissions at {} KB of deferred commands',       # :1204
    'split': 'd3d12_submit_split: frame={} submission={} splits={} failed={} held_query={} held_scratch={} '
             'held_pipelines={}',                                                                     # :4412
    'slow': 'slow frame #{}: {:.1f} ms | gpu-thread idle {:.1f} | host-gpu wait {:.1f} ({}x) | '
            'shader translate {:.1f} ({}x) | pipeline create {:.1f} ({}x), new {} | '
            'texture load {:.1f} ({}x) | readback {}x {} KB, {} stalled | '
            'cpu-write invalidations {}x {} KB (on memexport pages {}x {} KB) | '
            'memexport syncs {} ({} KB), on demand {} ({} KB) | '
            'memexport full-buffer {}x (total {})',                                                   # :290
    # src/graphics/d3d12/deferred_command_list.cpp
    'dc_hdr': 'deferred_counters: {:.1f} s, {} lists, {} KB, {} barriers',                          # :668
    'dc_cmd': 'deferred_counters:   {:<33} total={:<8} repeat={:<8} ({:.1f}%)',                     # :673
    # rexlego/src/gpu_wait_backoff.cpp (s4c-24-30 / snap1)
    'gw_init': 'GPU wait back-off: {} (quantum {} us, spin {} us); stats {}; GetData hook {}.',      # :142
    'gw_stats': 'GPU wait stats (5 s): L1 waits {} polls {} moved {} gpu_off {} sleep>moved {} sleep>done {} | '
                'L2 tries {} waits {} polls {} delayed {} sleep>ready {} | kicks {} | pause {} yield {} sleep {} '
                'sleep_sum {:.2f} ms sleep_fail {} | L1 sum {:.2f} ms max {:.3f} ms hist <50us {} <200us {} <1ms {} '
                '<4ms {} >=4ms {} | L2 sum {:.2f} ms max {:.3f} ms',                                # :237
    # DimensionsRecomp/rexglue-sdk/src/ui/d3d12/d3d12_provider.cpp (not among the 16 S4b files)
    'dred': 'DRED (Device Removed Extended Data) enabled',                                           # :237
    'dbg_fail': 'Failed to enable the Direct3D 12 debug layer',                                      # :227
}
CLEAN = ('info', 'kernel', 'Title terminated; hard-exiting process')


def stats(sleep_fail=0, sleep=0):
    return F['gw_stats'].format(1500, 30000, 1400, 0, 0, 0, 800, 50, 900, 10, 0, 120, 25000, 4000, sleep,
                                0.25 * sleep, sleep_fail, 850.25, 3.512, 900, 400, 150, 45, 5, 12.5, 0.875)


def slow(i, total):
    return F['slow'].format(i, 34.5, 1.0, 2.0, 3, 0.0, 0, 0.0, 0, 0, 0.5, 2, 0, 0, 0, 5, 20, 0, 0, 1, 4, 0, 0, 0, total)


C1V = [('info', 'sys', F['c1_init_on']), ('info', 'gpu', F['c1_verify_on']),
       ('info', 'sys', F['c1_first'].format(0x0A1B2000, 4096)), ('info', 'sys', F['c1_kept'].format(2)),
       ('info', 'sys', F['c1_kept'].format(4)),
       ('warning', 'gpu', F['c1_verify'].format('F', 0x0A1B3000, 1, '')),
       ('warning', 'gpu', F['c1_verify'].format('F', 0x0A1B4000, 2, ''))]
C1V_CV = {'physical_protect_hold_global_lock': 'true', 'physical_protect_keep_watch': 'true',
          'physical_protect_keep_watch_verify': 'true'}
DC = []
for sec, lists, kb, bar in ((10.0, 1200, 96000, 5400), (10.0, 1100, 99000, 5000), (10.1, 1250, 93750, 5600)):
    DC.append(('info', 'gpu', F['dc_hdr'].format(sec, lists, kb, bar)))
    for name, tot, rp in (('SetGraphicsRootSignature', lists, lists // 2), ('D3DDrawInstanced', lists * 9, lists),
                          ('ResourceBarrier', bar, bar // 3)):
        DC.append(('info', 'gpu', F['dc_cmd'].format(name, tot, rp, 100.0 * rp / tot)))
GW18 = [('info', 'rex', F['gw_init'].format('ON', 250, 20, 'ON', 'built'))]
CASES = [  # (case, row, cvars, env, lines, expected hint old, expected hint new)
    ('s4b04', 's4b04', C1V_CV, {}, C1V, 'LOOK', 'PASS?'),
    ('s4b04k', 's4b04', C1V_CV, {}, C1V + [('warning', 'gpu', F['c1_verify'].format(
        'K', 0x0A1B2000, 1, '; protect keeps the normal path'))], 'LOOK', 'LOOK'),
    ('s4b08', 's4b08', {'shared_memory_single_hold_rearm': 'true', 'slow_frame_log_ms': '1'}, {},
     [('info', 'gpu', slow(100, 0)), ('info', 'gpu', slow(240, 0))], 'PASS?', 'PASS?'),
    ('s4b08x', 's4b08', {'shared_memory_single_hold_rearm': 'true', 'slow_frame_log_ms': '1'}, {},
     [('info', 'gpu', slow(100, 3)), ('info', 'gpu', slow(240, 7))], 'LOOK', 'LOOK'),
    ('s4b09', 's4b09', {}, {}, DC, 'PASS?', 'PASS?'),
    ('s4b10', 's4b10', {'d3d12_submit_split_kb': '40'}, {},
     [('info', 'gpu', F['split_init'].format(40)), ('info', 'gpu', F['split'].format(600, 1900, 1200, 0, 3, 0, 12)),
      ('info', 'gpu', F['split'].format(1200, 3800, 2400, 0, 5, 0, 20))], 'PASS?', 'PASS?'),
    ('s4b25', 's4b25', {'d3d12_submit_split_kb': '40', 'framerate_limit': '0'}, {},
     [('info', 'gpu', F['split_init'].format(40))], 'LOOK', 'PASS?'),
    ('s4b14', 's4b14', {'d3d12_debug': 'true'}, {}, [('info', 'gpu', F['dred'])], 'PASS?', 'PASS?'),
    ('s4b14x', 's4b14', {'d3d12_debug': 'true'}, {}, [('warning', 'gpu', F['dbg_fail'])], 'PASS?', 'LOOK'),
    ('s4b17', 's4b17', {}, {'LEGO_GPU_WAIT_STATS': '1'},
     [('info', 'rex', F['gw_init'].format('OFF', 0, 20, 'ON', 'built'))] + [('info', 'rex', stats())] * 3,
     'LOOK', 'PASS?'),
    ('s4b18', 's4b18', {}, {'LEGO_GPU_WAIT_BACKOFF_US': '250', 'LEGO_GPU_WAIT_STATS': '1'},
     GW18 + [('info', 'rex', stats(0, 40))] * 2, 'PASS?', 'PASS?'),
    ('s4b18f', 's4b18', {}, {'LEGO_GPU_WAIT_BACKOFF_US': '250', 'LEGO_GPU_WAIT_STATS': '1'},
     GW18 + [('info', 'rex', stats(0, 40)), ('info', 'rex', stats(3, 40))], 'PASS?', 'LOOK'),
]


def write_case(case, row, cv, env, lines):
    d = os.path.join(SYN, case)
    os.makedirs(d, exist_ok=True)
    out = []
    for i, (lvl, cat, msg) in enumerate(list(lines) + [CLEAN]):
        t = 5 * (i + 1)
        out.append('[2026-11-22 20:%02d:%02d.%03d] [%s] [%s] [t4242] %s' % (10 + t // 60, t % 60, i % 1000, lvl, cat, msg))
    with open(os.path.join(d, 'game.log'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    rj = {'exit_code': 0, 'exit_code_hex': '0x00000000', 'dumps': [], 'crash_events': [], 'wer_seen': False,
          'close_method': 'wm_close', 'close_seconds': 1.0, 'elapsed_s': 40.0, 'seconds_requested': 420, 'cvars': cv,
          'env': env}
    with open(os.path.join(d, 'run.json'), 'w', encoding='utf-8') as f:
        json.dump(rj, f, indent=1)
    return d


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def unit_checks(W):
    old, new = load('s4b_old', SRC), load('s4b_new', OUT)
    import re
    K = F['c1_verify'].format('K', 0x0A1B2000, 7, '; protect keeps the normal path')
    Fl = F['c1_verify'].format('F', 0x0A1B3000, 2, '')
    st = stats(1, 40)
    hdr = F['dc_hdr'].format(10.0, 1200, 96000, 5400)
    W('== regex unit checks (old -> proposed) ==')
    for lab, rx_old, rx_new in (('K regex on K line', old.K_DEFAULT, new.K_DEFAULT),):
        W('%s: old %s, new %s   | %s' % (lab, bool(re.search(rx_old, K)), bool(re.search(rx_new, K)), K))
    W('K regex on F line: old %s (counts F as K: BUG), new %s   | %s' % (
        bool(re.search(old.K_DEFAULT, Fl)), bool(re.search(new.K_DEFAULT, Fl)), Fl))
    W('K regex on verify init: old %s, new %s' % (bool(re.search(old.K_DEFAULT, F['c1_verify_on'])),
                                                  bool(re.search(new.K_DEFAULT, F['c1_verify_on']))))
    W('GPU wait stats: old kv() -> %s; new GWS -> %d fields, sleep_fail=%s l1_waits=%s l1_max_ms=%s l2_max_ms=%s' % (
        old.kv(st.split('GPU wait stats', 1)[1]), len(new.GWS.search(st).groups()),
        new.GWS.search(st).group(18), new.GWS.search(st).group(2), new.GWS.search(st).group(20),
        new.GWS.search(st).group(27)))
    W('  len(GWS_KEYS) %d == groups %d' % (len(new.GWS_KEYS), new.GWS.groups))
    W('deferred_counters header: old kv() -> %s; new DC_HDR -> %s' % (
        old.kv(hdr.split('deferred_counters', 1)[1]), new.DC_HDR.search(hdr).groups()))
    sp = F['split'].format(600, 1900, 1200, 0, 3, 0, 12)
    W('split kv (both): %s' % old.kv(sp.split('d3d12_submit_split: ', 1)[1]))
    sl = slow(100, 5)
    W('MEMEXPORT on slow-frame line: %s (suffix printed by cp.cpp:296)' % (old.MEMEXPORT.search(sl).groups(),))
    W('KEPT on kept line: %s' % (old.KEPT.search(F['c1_kept'].format(4096)).groups(),))
    g = 'GONE build\\agent3\\runs\\x\\game.log [info] [gpu] S# upload hash: frame # calls # ranges # pages # (# KB)'
    W('GONE_OK on logdiff key "S# upload hash": old %s, new %s' % (bool(re.search(old.GONE_OK_DEFAULT, g)),
                                                                   bool(re.search(new.GONE_OK_DEFAULT, g))))
    W('== family needles per format line (old | proposed) ==')
    samples = dict(F)
    samples['c1_first'] = F['c1_first'].format(0x0A1B2000, 4096)
    samples['c1_kept'] = F['c1_kept'].format(16)
    samples['c1_verify_K'] = K
    samples['c1_verify_F'] = Fl
    del samples['c1_verify']
    samples['split_init'] = F['split_init'].format(40)
    samples['split'] = sp
    samples['slow'] = sl
    samples['dc_hdr'] = hdr
    samples['dc_cmd'] = F['dc_cmd'].format('ResourceBarrier', 5400, 1800, 33.3)
    samples['gw_init_on'] = F['gw_init'].format('ON', 250, 20, 'ON', 'built')
    samples['gw_init_p1'] = F['gw_init'].format('OFF', 0, 20, 'ON', 'built')
    del samples['gw_init']
    samples['gw_stats'] = st
    for k, msg in samples.items():
        fo = [kk for kk, nd, rx in old.FAM if nd in msg and (rx is None or rx.search(msg))]
        fn = [kk for kk, nd, rx in new.FAM if nd in msg and (rx is None or rx.search(msg))]
        ko = ('eep-watch' in msg or 'erif' in msg) and bool(re.search(old.K_DEFAULT, msg))
        kn = ('eep-watch' in msg or 'erif' in msg) and bool(re.search(new.K_DEFAULT, msg))
        W('  %-16s old %s%s | new %s%s' % (k, fo, ' +K' if ko else '', fn, ' +K' if kn else ''))


def run_cases(W):
    W('')
    W('== synthetic runs: old script vs proposed (no base; row proofs + base items of the run itself) ==')
    bad = 0
    for case, row, cv, env, lines, exp_old, exp_new in CASES:
        d = write_case(case, row, cv, env, lines)
        W('')
        W('### %s (--row %s): %d log lines; expected old %s, new %s' % (case, row, len(lines) + 1, exp_old, exp_new))
        for tag, script, exp in (('old', SRC, exp_old), ('new', OUT, exp_new)):
            od = os.path.join(SYN_OUT, tag)
            r = subprocess.run([sys.executable, '-B', script, '--cand', d, '--row', row, '--out-dir', od],
                               capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
            outl = r.stdout.splitlines()
            keep = [l for l in outl if l.startswith(('PROOF', 'VERDICT', 'BASE items', 'gpu_wait_stats fields',
                                                     'deferred_counters fields', 'split fields', 'memexport'))]
            hint = next((l.split()[2].rstrip(':') for l in outl if l.startswith('VERDICT HINT')), 'NONE')
            okx = hint == exp
            bad += 0 if okx else 1
            W('[%s] rc %s hint %s (%s)' % (tag, r.returncode, hint, 'as expected' if okx else 'UNEXPECTED'))
            for l in keep:
                W('  ' + l[:330])
            if r.returncode or r.stderr.strip():
                W('  stderr: ' + r.stderr.strip()[-1500:])
    W('')
    W('synthetic cases with an unexpected hint: %d' % bad)
    return bad


def main():
    log, nl = build()
    L = []
    W = L.append
    W('# make_proposed.py: %s -> %s (newline %r); diff -> %s' % (os.path.relpath(SRC, HERE), os.path.basename(OUT), nl,
                                                                  os.path.basename(DIFF)))
    L.extend(log)
    unit_checks(W)
    if os.path.isdir(SYN_OUT):
        shutil.rmtree(SYN_OUT)
    bad = run_cases(W)
    with open(CMP, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())

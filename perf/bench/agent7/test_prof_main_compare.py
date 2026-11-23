#!/usr/bin/env python3
"""Tests for prof_main_compare.py (Agent 7). Stdlib unittest, one thread.

    python bench/agent7/test_prof_main_compare.py [-v]

Pure-function tests plus an aggregation test that swaps analyze_profile.Analysis for a fake
with known stacks, so the bucket arithmetic is checked exactly (w = 1000/(rounds*fps)).
The optional smoke test runs the real analyser on build/agent8/runs/2008-dry1prof if present.
"""
import collections
import contextlib
import io
import os
import re
import struct
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prof_main_compare as pmc  # noqa: E402

AP = pmc.load_ap()


class F:
    """Minimal stand-in for analyze_profile.Func."""

    def __init__(self, name, category, cls='busy', raw=None):
        self.name, self.category, self.cls = name, category, cls
        self.raw = raw if raw is not None else name
        self.guest = category == 'guest'


FUNCS = [
    F('sub_82000000 [guest 0x82000000]', 'guest', raw='sub_82000000'),            # 0
    F('sub_82000100 [guest 0x82000100] {+2 aliases}', 'guest', raw='sub_82000100'),  # 1
    F('ntdll.dll!KiUserExceptionDispatcher', 'system'),                              # 2
    F('rexruntime.dll!?TriggerPhysicalMemoryCallbacks@Memory@memory@rex@@QEAA_NAEAV?$'
      'unique_lock@Vrecursive_mutex@std@@@std@@I_K@Z', 'rexruntime'),                 # 3
    F('ntdll.dll!RtlEnterCriticalSection', 'system'),                                 # 4
    F('ntdll.dll!NtWaitForSingleObject', 'system', cls='wait'),                       # 5
    F('ntdll.dll!NtYieldExecution', 'system'),                                        # 6
    F('rexruntime.dll!?MaybeYield@thread@rex@@YAXXZ', 'rexruntime'),                 # 7
    F('VCRUNTIME140.dll!memcpy', 'system'),                                           # 8
    F('legodimensions::gpu_native::UploadBuffer', 'native-gpu'),                     # 9
    F('__restgprlr_29', 'rexlego'),                                                   # 10
    F('ntdll.dll!RtlUserThreadStart', 'system'),                                      # 11
    F('ntdll.dll!NtReadFile', 'system', cls='io'),                                    # 12
]
STACKS = [
    (0, 1, 11),               # s0 guest leaf
    (4, 3, 2, 0, 1, 11),      # s1 write-tracking fault, busy (CS inside the handler)
    (5, 3, 2, 0, 1, 11),      # s2 blocked inside the fault handler
    (6, 7, 1, 11),            # s3 yield, busy
    (8, 9, 1, 11),            # s4 native upload
    (10, 1, 11),              # s5 guest helper leaf (counts as guest code)
    (5, 11),                  # s6 wait, no guest frame
    (12, 1, 11),              # s7 io from guest
]
MAIN, RENDER = 100, 200


def make_fake(counts_main, counts_render, rounds=1000):
    class FakeProf:
        thread_names = {MAIN: 'Main XThread (F8000024)', RENDER: 'XThread2228 (F8000190)'}
        trailer = {'timer_mode': 'hr-test'}
        sample_count = sum(counts_main) + sum(counts_render)

        def observer_effect(self):
            return False

    class FakeAnalysis:
        def __init__(self, prof, mp, ns, duration_s=None, meta=None):
            self.prof = FakeProf()
            self.map_path = mp
            self.timing = {}
            self.duration = {'rounds': rounds, 'seconds': rounds / 250.0, 'source': 'trailer',
                             'rounds_per_s': 250.0}
            self.fstacks = STACKS
            self.agg = {}
            for tid, counts in ((MAIN, counts_main), (RENDER, counts_render)):
                for s, n in enumerate(counts):
                    if n:
                        self.agg[(tid, s)] = n

        def funcs(self):
            return FUNCS

    return FakeAnalysis


@contextlib.contextmanager
def fake_analysis(cls):
    saved = AP.Analysis
    AP.Analysis = cls
    try:
        yield
    finally:
        AP.Analysis = saved


def args_ns(**kw):
    d = dict(no_undname=True, search=None, driverstore=False, label_a='A', label_b='B', top=25)
    d.update(kw)
    return types.SimpleNamespace(**d)


class ShortName(unittest.TestCase):
    def test_alias_strip(self):
        self.assertEqual(pmc.short_name('sub_82A32950 [guest 0x82A32950] {+2 aliases}'),
                         'sub_82A32950 [guest 0x82A32950]')
        self.assertEqual(pmc.short_name('foo {+1 alias}'), 'foo')

    def test_decorated_export(self):
        self.assertEqual(pmc.short_name('rexruntime.dll!?MaybeYield@thread@rex@@YAXXZ'),
                         'rexruntime.dll!rex::thread::MaybeYield')

    def test_fn_near(self):
        self.assertEqual(pmc.short_name('rexruntime.dll!fn_1A2B (near ?Foo@Bar@@QEAAXXZ+0x10)'),
                         'rexruntime.dll!~Bar::Foo')

    def test_plain_and_operators(self):
        self.assertEqual(pmc.short_name('ntdll.dll!KiUserExceptionDispatcher'),
                         'ntdll.dll!KiUserExceptionDispatcher')
        self.assertEqual(pmc.short_name('rex::foo::operator!='), 'rex::foo::operator!=')
        self.assertEqual(pmc.short_name(None), '?')


class Classify(unittest.TestCase):
    def c(self, names, cats=None, guest=False):
        return pmc.classify(names, cats or ['system'] * len(names), guest)

    def test_guest_leaf_wins(self):
        self.assertEqual(self.c(['ntdll.dll!KiUserExceptionDispatcher'], guest=True), 'guest code')

    def test_fault_before_sync(self):
        names = ['ntdll.dll!RtlEnterCriticalSection',
                 pmc.short_name(FUNCS[3].name), 'ntdll.dll!KiUserExceptionDispatcher']
        self.assertEqual(self.c(names), 'write-tracking fault (VEH)')
        self.assertEqual(self.c(["legodimensions::gpu_native::`anonymous namespace'::"
                                 "MemoryWritten"]), 'write-tracking fault (VEH)')
        # SDK fault path (xmemory.cpp): the handler frames alone classify the sample, even
        # when the walk stops before KiUserExceptionDispatcher.
        self.assertEqual(self.c(['ntdll.dll!RtlEnterCriticalSection',
                                 'rex::memory::PhysicalHeap::TriggerCallbacks',
                                 'rex::memory::Memory::AccessViolationCallback']),
                         'write-tracking fault (VEH)')
        self.assertEqual(self.c(['rex::memory::PhysicalHeap::Protect']),
                         'write-tracking arm/protect')

    def test_arm_pool_sync(self):
        self.assertEqual(self.c(['ntdll.dll!NtProtectVirtualMemory', 'KERNELBASE.dll!VirtualProtect',
                                 'legodimensions::gpu_native::WatchCpuMemory']),
                         'write-tracking arm/protect')
        self.assertEqual(self.c(['rex::memory::Protect']), 'write-tracking arm/protect')
        self.assertEqual(self.c(['VCRUNTIME140.dll!memcpy', 'legodimensions::PoolCopyHook']),
                         'CPU pool copy')
        self.assertEqual(self.c(['ntdll.dll!NtYieldExecution', 'rexruntime.dll!rex::thread::MaybeYield']),
                         'sync/spin/yield (busy)')
        self.assertEqual(self.c(['KERNELBASE.dll!WaitForSingleObjectEx']), 'sync/spin/yield (busy)')

    def test_category_fallbacks(self):
        self.assertEqual(self.c(['nvwgf2umx.dll!fn_1 (near OpenAdapter12+0x5)', 'D3D12Core.dll!x'],
                                ['d3d12+driver', 'd3d12+driver']), 'd3d12+driver')
        self.assertEqual(self.c(['VCRUNTIME140.dll!memcpy', 'legodimensions::gpu_native::UploadBuffer'],
                                ['system', 'native-gpu']), 'native upload/copy/hash')
        self.assertEqual(self.c(['legodimensions::gpu_native::Draw'], ['native-gpu']),
                         'native-gpu other')
        self.assertEqual(self.c(['legodimensions::Foo'], ['rexlego']), 'rexlego host')
        self.assertEqual(self.c(['rexruntime.dll!rex::Foo'], ['rexruntime']), 'rexruntime')
        self.assertEqual(self.c(['ntdll.dll!RtlFoo']), 'system/other')


class CompareRows(unittest.TestCase):
    def test_values_and_noise(self):
        rows = pmc.compare_rows({'x': 100, 'y': 1}, {'x': 144, 'y': 2}, 0.01, 0.0125)
        x = next(r for r in rows if r['key'] == 'x')
        self.assertAlmostEqual(x['a'], 1.0)
        self.assertAlmostEqual(x['b'], 1.8)
        self.assertAlmostEqual(x['delta'], 0.8)
        self.assertAlmostEqual(x['se2'], 2 * (0.01 + 0.0225) ** 0.5)
        self.assertFalse(x['noise'])
        self.assertTrue(next(r for r in rows if r['key'] == 'y')['noise'])
        self.assertEqual(rows[0]['key'], 'x')          # sorted by |delta|

    def test_keys_order_and_top(self):
        rows = pmc.compare_rows({'b': 5}, {'a': 9}, 1, 1, keys=('z', 'b', 'a'), sort=False)
        self.assertEqual([r['key'] for r in rows], ['z', 'b', 'a'])
        self.assertEqual(rows[0]['a'], 0)
        self.assertEqual(len(pmc.compare_rows({'a': 1, 'b': 2, 'c': 3}, {}, 1, 1, top=2)), 2)


class FpsFromFrames(unittest.TestCase):
    def test_sources(self):
        self.assertEqual(pmc.fps_from_frames({'window': {'rows_by_end_bytes': 1430,
                                                         'end_bytes_window_s': 10.0}})[0], 143.0)
        self.assertEqual(pmc.fps_from_frames({'frames': 500, 'window_s': 5.0})[0], 100.0)
        self.assertEqual(pmc.fps_from_frames({'mean_ms': 8.0})[0], 125.0)
        self.assertEqual(pmc.fps_from_frames({}), (None, None))
        self.assertEqual(pmc.fps_from_frames(None), (None, None))


class Aggregation(unittest.TestCase):
    # Main: s0 400, s1 100, s2 50, s3 60, s4 40, s5 10, s6 330, s7 10 = 1000 = rounds
    A_MAIN = [400, 100, 50, 60, 40, 10, 330, 10]
    B_MAIN = [480, 200, 40, 60, 40, 10, 160, 10]
    RENDER = [500, 0, 0, 0, 0, 0, 500, 0]

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.prof = os.path.join(self.tmp.name, 'profile-1.bin')
        with open(self.prof, 'wb') as f:
            f.write(b'LSP1' + b'\0' * 60)

    def tearDown(self):
        self.tmp.cleanup()

    def side(self, label, fps):
        return {'label': label, 'input': self.prof, 'run_dir': self.tmp.name,
                'profile': self.prof, 'map': 'x.map', 'bin_dir': self.tmp.name, 'fps': fps,
                'fps_source': 'test', 'duration_fallback': None, 'threads_csv': None,
                'arm_args': None, 'env_set': None, 'profile_seconds_requested': None}

    def run_side(self, counts, fps, label='A', **kw):
        warns = []
        with fake_analysis(make_fake(counts, self.RENDER)):
            out = pmc.analyse(self.side(label, fps), args_ns(), re.compile(r'^Main XThread'),
                              kw.get('tid'), kw.get('all_threads', False), warns)
        return out, warns

    def test_main_buckets_exact(self):
        A, warns = self.run_side(self.A_MAIN, 100.0)
        self.assertEqual(warns, [])
        self.assertAlmostEqual(A['w'], 0.01)
        h, c = A['header'], A['counts']
        self.assertEqual(h['thread_select']['tids'], [MAIN])
        self.assertEqual((h['busy'], h['wait'], h['io']), (610, 380, 10))
        self.assertEqual(c['bucket']['guest code'], 410)
        self.assertEqual(c['bucket']['write-tracking fault (VEH)'], 100)
        self.assertEqual(c['bucket']['sync/spin/yield (busy)'], 60)
        self.assertEqual(c['bucket']['native upload/copy/hash'], 40)
        self.assertEqual(sum(c['bucket'].values()), 610)
        self.assertAlmostEqual(h['busy_ms_per_frame'], 6.10)
        self.assertAlmostEqual(h['blocked_ms_per_frame'], 3.90)
        self.assertEqual(c['fault_guest'], {'sub_82000000 [guest 0x82000000]': 100})
        self.assertEqual(c['fault_leaf'], {'ntdll.dll!RtlEnterCriticalSection': 100})
        self.assertEqual(c['boundary']['ntdll.dll!KiUserExceptionDispatcher'], 100)
        self.assertEqual(c['boundary']['(guest code)'], 410)
        self.assertEqual(c['sync_boundary'], {'rexruntime.dll!rex::thread::MaybeYield': 60})
        self.assertEqual(c['blocked']['ntdll.dll!KiUserExceptionDispatcher'], 50)
        self.assertEqual(c['blocked']['(no guest frame) ntdll.dll!RtlUserThreadStart'], 330)
        self.assertEqual(c['blocked']['[io] ntdll.dll!NtReadFile'], 10)
        self.assertEqual(c['guest_self']['__restgprlr_29'], 10)
        self.assertEqual(c['guest_incl']['sub_82000100 [guest 0x82000100]'], 610)
        self.assertEqual(c['incl']['ntdll.dll!RtlUserThreadStart'], 610)
        self.assertEqual(A['callers']['ntdll.dll!KiUserExceptionDispatcher'],
                         {'sub_82000000 [guest 0x82000000]': 100})
        roles = A['roles']
        self.assertEqual((roles['main']['busy'], roles['main']['guest']), (610, 410))
        self.assertEqual((roles['render']['busy'], roles['render']['wait']), (500, 500))
        self.assertEqual(roles['all']['busy'], 1110)
        self.assertEqual([t['role'] for t in A['threads']], ['main', 'render'])
        self.assertIsNone(A['handoff'])

    def test_thread_modes(self):
        A, _ = self.run_side(self.A_MAIN, 100.0, all_threads=True)
        self.assertEqual(A['header']['busy'], 610 + 500)
        R, _ = self.run_side(self.A_MAIN, 100.0, tid=str(RENDER))
        self.assertEqual(R['header']['busy'], 500)
        busiest = R['threads'][0]
        self.assertEqual((busiest['tid'], busiest['busy']), (MAIN, 610))

    def test_report_and_render(self):
        A, _ = self.run_side(self.A_MAIN, 100.0, 'a-prof')
        B, _ = self.run_side(self.B_MAIN, 80.0, 'n-prof')
        self.assertAlmostEqual(B['w'], 0.0125)
        rep = pmc.build_report(A, B, args_ns(), [])
        rows = {r['key']: r for r in rep['buckets']}
        self.assertAlmostEqual(rows['write-tracking fault (VEH)']['delta'], 200 * 0.0125 - 1.0)
        self.assertAlmostEqual(rows['guest code']['delta'], 490 * 0.0125 - 4.10)
        self.assertAlmostEqual(rows['total busy']['b'], 790 * 0.0125)   # 480+200+60+40+10
        self.assertAlmostEqual(rows['blocked (wait/io, not CPU)']['b'], 210 * 0.0125)
        self.assertEqual(rep['candidates'][0]['key'], 'guest code')
        self.assertEqual(rep['candidates'][1]['key'], 'write-tracking fault (VEH)')
        kiued = next(r for r in rep['boundary'] if r['key'] == 'ntdll.dll!KiUserExceptionDispatcher')
        self.assertEqual(kiued['callers'], [('sub_82000000 [guest 0x82000000]', 200)])
        self.assertEqual(next(r for r in rep['boundary'] if r['key'] == '(guest code)')['callers'],
                         [])
        roles = {r['key']: r for r in rep['roles']}
        self.assertEqual(list(roles), ['main', 'render', 'all'])
        self.assertAlmostEqual(roles['main']['delta'], 790 * 0.0125 - 6.10)
        self.assertAlmostEqual(roles['main']['guest_b'], 490 * 0.0125)
        self.assertAlmostEqual(roles['main']['blocked_a'], 3.90)
        self.assertAlmostEqual(roles['render']['b'], 500 * 0.0125)
        self.assertAlmostEqual(roles['all']['a'], 11.10)
        self.assertEqual(roles['main']['names_b'], 'Main XThread (F8000024)')
        self.assertEqual(roles['all']['names_a'], '2 threads')
        fl = rep['fault_linked'][0]
        self.assertEqual(fl['key'], 'sub_82000000 [guest 0x82000000]')
        self.assertAlmostEqual(fl['a'], 4.00)                # its guest self: s0, 400 samples
        self.assertAlmostEqual(fl['b'], 480 * 0.0125)
        self.assertAlmostEqual(fl['fault_delta'], 200 * 0.0125 - 1.0)
        self.assertIsNone(rep['handoff'])
        text = pmc.render(rep)
        for s in ('== buckets', 'ranked candidates', ' 1. guest code', 'write-tracking faults by '
                  'faulting guest function', 'busiest threads, n-prof', 'timer_mode hr-test',
                  '== threads by role', '== fault-linked'):
            self.assertIn(s, text)
        self.assertNotIn('== handoff', text)

    def test_fallback_thread_pick_warns(self):
        warns = []
        with fake_analysis(make_fake(self.A_MAIN, self.RENDER)):
            out = pmc.analyse(self.side('A', 100.0), args_ns(), re.compile(r'^NoSuchThread'),
                              None, False, warns)
        self.assertEqual(out['header']['thread_select']['tids'], [RENDER])   # most guest-leaf
        self.assertTrue(any('no thread name matches' in w for w in warns))


class Roles(unittest.TestCase):
    def test_assign(self):
        names = {1: 'Main XThread (F8000024)', 2: 'XThread2228 (F8000190)',
                 3: 'XThread1729C (F8000128)', 4: 'GPU Commands (F8000018)',
                 5: 'rex::thread::TimerQueue', 6: 'Audio Worker (F8000014)',
                 7: 'XThread1575C (F800010C)', 8: '0xc0550001', 9: 'SDLAudioP19',
                 11: 'GPU VSync (F800001C)'}
        busy = {1: 770, 2: 704, 3: 169, 4: 0, 5: 520, 6: 27, 7: 45, 8: 110, 9: 24, 10: 5, 11: 3}
        self.assertEqual(pmc.assign_roles(names, busy),
                         {1: 'main', 2: 'render', 3: 'worker2', 7: 'xt_other', 4: 'gpu_cmd',
                          5: 'timerq', 6: 'audio', 9: 'audio', 8: 'other', 10: 'other',
                          11: 'vsync'})

    def test_pair_stats(self):
        st = pmc.pair_stats({pmc.PAIR_KEYS[0]: 4, pmc.PAIR_KEYS[1]: 3, pmc.PAIR_KEYS[2]: 2,
                             pmc.PAIR_KEYS[3]: 1, 'main absent / render busy': 7})
        self.assertEqual(st['n_both'], 10)
        self.assertAlmostEqual(st['p_render_wait_given_main_busy'], 3 / 7)
        self.assertAlmostEqual(st['p_main_wait_given_render_busy'], 2 / 6)
        self.assertAlmostEqual(st['expected'][pmc.PAIR_KEYS[0]], 0.7 * 0.6 * 10)
        self.assertAlmostEqual(st['expected'][pmc.PAIR_KEYS[3]], 0.3 * 0.4 * 10)
        self.assertIsNone(pmc.pair_stats({}))


def addr(f):
    """Fake code address of FUNCS[f]; the fake resolver maps addr(f) and addr(f) - 1 to f."""
    return 0x1000 + 16 * f + 8


def key_of(stack):
    return struct.pack(f'<{len(stack)}Q', *[addr(f) for f in stack])


OTHER = 300


def make_seq_fake(samples, rounds):
    """Fake Analysis whose prof.stacks/counts and resolver match a real LSP1 file of samples."""
    stacks = [key_of(s) for s in STACKS]
    counts = collections.Counter((s << 32) | t for t, s in samples)
    agg = collections.Counter((t, s) for t, s in samples)

    class FakeProf:
        thread_names = {MAIN: 'Main XThread (F8000024)', RENDER: 'XThread2228 (F8000190)',
                        OTHER: 'XThread1729C (F8000128)'}
        trailer = {'timer_mode': 'hr-test'}
        sample_count = len(samples)

        def __init__(self):
            self.stacks, self.counts = stacks, dict(counts)

        def observer_effect(self):
            return False

    class FakeSym:
        empty = 11

        @staticmethod
        def resolve(a):
            return (a - 0x1000) // 16

    class FakeAnalysis:
        def __init__(self, prof, mp, ns, duration_s=None, meta=None):
            self.prof, self.sym, self.map_path, self.timing = FakeProf(), FakeSym(), mp, {}
            self.duration = {'rounds': rounds, 'seconds': rounds / 250.0, 'source': 'trailer',
                             'rounds_per_s': 250.0}
            self.fstacks = STACKS
            self.agg = dict(agg)

        def funcs(self):
            return FUNCS

    return FakeAnalysis


class Handoff(unittest.TestCase):
    # (Main stack, render stack) per round; OTHER is always s6 (wait, no guest frame)
    SPEC = [(0, 0)] * 4 + [(1, 6)] * 3 + [(2, 0)] * 2 + [(6, 6)]
    FAULT = 'ntdll.dll!KiUserExceptionDispatcher <- sub_82000000 [guest 0x82000000]'
    NOG = '(no guest frame) ntdll.dll!RtlUserThreadStart'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.samples = []
        for i, (ms, rs) in enumerate(self.SPEC):
            order = [(MAIN, ms), (RENDER, rs), (OTHER, 6)]
            if i % 3 == 1:
                order.reverse()                  # the sampler order may change between rounds
            self.samples += order
        body = b''.join(struct.pack('<II', t, len(STACKS[s])) + key_of(STACKS[s])
                        for t, s in self.samples)
        self.prof = os.path.join(self.tmp.name, 'profile-1.bin')
        with open(self.prof, 'wb') as f:
            f.write(b'LSP1' + struct.pack('<IQ', 0, len(self.samples)) + body)

    def tearDown(self):
        self.tmp.cleanup()

    def run_side(self, chunk=None, label='A'):
        warns, saved = [], pmc.SCAN_CHUNK
        side = {'label': label, 'input': self.prof, 'run_dir': self.tmp.name,
                'profile': self.prof, 'map': 'x.map', 'bin_dir': self.tmp.name, 'fps': 100.0,
                'fps_source': 'test', 'duration_fallback': None, 'threads_csv': None,
                'arm_args': None, 'env_set': None, 'profile_seconds_requested': None}
        try:
            pmc.SCAN_CHUNK = chunk or saved
            with fake_analysis(make_seq_fake(self.samples, len(self.SPEC))):
                out = pmc.analyse(side, args_ns(handoff=True), re.compile(r'^Main XThread'),
                                  None, False, warns)
        finally:
            pmc.SCAN_CHUNK = saved
        return out, warns

    def test_joint_states_and_details(self):
        out, warns = self.run_side()
        self.assertEqual(warns, [])
        h = out['handoff']
        self.assertEqual((h['rounds'], h['samples'], h['stop']), (10, 30, None))
        self.assertEqual(h['tids'], {'main': MAIN, 'render': RENDER})
        self.assertEqual(dict(h['pair']), {'main busy / render busy': 4,
                                           'main busy / render wait': 3,
                                           'main wait / render busy': 2,
                                           'main wait / render wait': 1})
        d = h['details']
        self.assertEqual(dict(d['crit_main_bucket']), {'write-tracking fault (VEH)': 3})
        self.assertEqual(dict(d['crit_main_where']), {self.FAULT: 3})
        self.assertEqual(dict(d['crit_render_wait']), {self.NOG: 3})
        self.assertEqual(dict(d['mw_main_wait']), {self.FAULT: 2})
        self.assertEqual(dict(d['mw_render_bucket']), {'guest code': 2})
        self.assertEqual(dict(d['mw_render_where']), {'sub_82000000 [guest 0x82000000]': 2})
        self.assertEqual(dict(d['overlap_main_bucket']), {'guest code': 4})
        self.assertEqual(dict(d['both_wait']), {f'{self.NOG} | {self.NOG}': 1})
        self.assertEqual(out['roles']['worker2']['busy'], 0)

    def test_small_chunks_same_result(self):
        a, _ = self.run_side()
        b, warns = self.run_side(chunk=5)
        self.assertEqual(warns, [])
        self.assertEqual((a['handoff']['pair'], a['handoff']['details'], a['handoff']['rounds']),
                         (b['handoff']['pair'], b['handoff']['details'], b['handoff']['rounds']))

    def test_report_and_render(self):
        A, _ = self.run_side(label='a-prof')
        B, _ = self.run_side(label='n-prof')
        rep = pmc.build_report(A, B, args_ns(), [])
        hr = rep['handoff']
        self.assertAlmostEqual(hr['w_a'], 1.0)          # 1000 / (10 rounds * 100 fps)
        rows = {r['key']: r for r in hr['pair']}
        self.assertEqual(len(rows), 4)
        self.assertAlmostEqual(rows['main busy / render wait']['a'], 3.0)
        self.assertAlmostEqual(rows['main busy / render wait']['delta'], 0.0)
        self.assertAlmostEqual(hr['stats']['b']['expected']['main busy / render busy'], 4.2)
        crit = hr['details']['crit_main_bucket'][0]
        self.assertEqual((crit['key'], crit['a']), ('write-tracking fault (VEH)', 3.0))
        self.assertEqual(hr['joint']['a'], [])           # no gpu_cmd: no 3-role table
        text = pmc.render(rep)
        for s in ('== handoff: Main vs render', 'critical-path Main work',
                  'P(render wait | main busy) 42.9%', 'P(main wait | render busy) 33.3%',
                  'tracked main 100 Main XThread (F8000024), render 200', '4.200'):
            self.assertIn(s, text)

    def test_truncated_file_warns(self):
        with open(self.prof, 'r+b') as f:
            f.truncate(os.path.getsize(self.prof) - 3)
        out, warns = self.run_side()
        self.assertEqual(out['handoff']['samples'], 29)
        self.assertTrue(any('handoff scan stopped: truncated' in w for w in warns))

    def test_skipped_without_render(self):
        warns = []
        with fake_analysis(make_fake(Aggregation.A_MAIN, [0] * 8)):
            pmc.analyse(Aggregation.side(types.SimpleNamespace(prof=self.prof, tmp=self.tmp),
                                         'A', 100.0),
                        args_ns(handoff=True), re.compile(r'^Main XThread'), None, False, warns)
        self.assertTrue(any('--handoff skipped' in w for w in warns))


SMOKE = os.path.join(pmc.ROOT, 'build', 'agent8', 'runs', '2008-dry1prof')


@unittest.skipUnless(os.path.isdir(SMOKE), 'legacy profile run not present')
class Smoke(unittest.TestCase):
    def test_real_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, js = os.path.join(tmp, 'o.txt'), os.path.join(tmp, 'o.json')
            with contextlib.redirect_stderr(io.StringIO()):
                rc = pmc.main([SMOKE, SMOKE, '--fps-a', '100', '--fps-b', '100', '--no-undname',
                               '--handoff', '-o', out, '--json', js])
            self.assertEqual(rc, 0)
            with open(out, encoding='utf-8') as f:
                text = f.read()
        self.assertIn('== buckets', text)
        self.assertIn('--handoff skipped', text)         # legacy profile: no trailer names
        m = re.search(r'\+0\.000~ +[\d.]+ +(\d+) +(\d+) +total busy', text)
        self.assertIsNotNone(m, 'A == B must give a zero total delta')
        self.assertEqual(m.group(1), m.group(2))


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""Synthetic tests + 1M-sample timing for DimensionsRecomp/tools/native-cpu/analyze_profile.py.

Everything is generated: a fake lld-link /MAP (random names and addresses, in the
exact layout lld writes) and fake LSP1 profiles with and without an LSPX trailer.
No game data is read or written (except --real-map: parse timing only, counts printed).

usage: python synth_test.py [--big N] [--keep-big] [--skip-big] [--real-map PATH]
Writes data to build/agent8/profiler/synth/ and results to bench/agent8/profiler/synth-result.txt.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import random
import struct
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
TOOLS = os.path.join(ROOT, 'DimensionsRecomp', 'tools', 'native-cpu')
ANALYZER = os.path.join(TOOLS, 'analyze_profile.py')
OUT = os.path.join(ROOT, 'build', 'agent8', 'profiler', 'synth')
sys.path.insert(0, TOOLS)
import analyze_profile as ap  # noqa: E402

IMAGE_BASE = 0x140000000
TEXT_RVA = 0x1000
NTDLL_BASE = 0x7FFA10000000
DRV_BASE = 0x7FFA20000000
SYS32 = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32')
QPC_FREQ = 10_000_000


def align(x, a):
    return (x + a - 1) // a * a


def guest_addr(k):
    return 0x82000000 + 0x40 * k


# =============================================================================
# Synthetic image + lld-style map
# =============================================================================

class SynthMap:
    def __init__(self, n_guest=60000, n_cpp=12000, n_gpu=4000, n_data=8000, n_static=4000,
                 n_hooks=40, seed=1):
        rnd = random.Random(seed)
        self.code: list[tuple] = []        # (rva, size, names, obj, static)
        self.by_name: dict[str, tuple] = {}
        self.hooked: list[int] = []
        rva = TEXT_RVA

        def add(names, obj, size, static=False):
            nonlocal rva
            e = (rva, size, tuple(names), obj, static)
            self.code.append(e)
            for nm in names:
                self.by_name.setdefault(nm, e)
            rva += size
            return e

        add(['mainCRTStartup'], 'libcmt:exe_main.obj', 0x40)
        add(['?RunGuest@synth@@YAXXZ'], 'runtime.cpp.obj', 0x200)
        add(['?Dispatch@synth@@YAXXZ'], 'runtime.cpp.obj', 0x80)      # ends with a call ...
        add(['?NeverCalled@synth@@YAXXZ'], 'runtime.cpp.obj', 0x80)   # ... returning here
        add(['?Draw@Renderer@gpu_native@legodimensions@@QEAAXXZ'], 'renderer.cpp.obj', 0x300)
        add(['?Pump@synth@@YAXXZ'], 'runtime.cpp.obj', 0x100)
        for k in range(n_cpp):
            names = [f'?Fn{k}@Sys{k % 97}@synth@@QEAAXH@Z']
            if k == 0:
                names = ['?Same0@synth@@YAXXZ', '?Same0b@synth@@YAXXZ', '?Same0cc@synth@@YAXXZ']
            elif k % 50 == 0:   # identical-code-folded aliases
                names += [f'?Alias{k}@synth@@YAXXZ']
            add(names, f'sys{k % 97}.cpp.obj', 0x10 * rnd.randint(2, 64))
        for k in range(n_gpu):
            add([f'?Op{k}@Pass{k % 31}@gpu_native@legodimensions@@QEAAXXZ'],
                f'pass{k % 31}.cpp.obj', 0x10 * rnd.randint(2, 64))
        for k in range(n_static):
            add([f'?helper{k}@?A0x1a2b3c4d@synth@@YAXXZ'], f'sys{k % 97}.cpp.obj',
                0x10 * rnd.randint(1, 16), static=True)
        hooks = set(rnd.sample(range(100, n_guest), n_hooks))
        for k in range(n_guest):
            g = guest_addr(k)
            obj = f'synthgame_recomp.{k // 2000}.cpp.obj'
            if k in hooks:
                add([f'__imp__sub_{g:08X}'], obj, 0x10 * rnd.randint(4, 96))
                self.hooked.append(g)
            else:
                add([f'sub_{g:08X}', f'__imp__sub_{g:08X}'], obj, 0x10 * rnd.randint(4, 96))
        for g in self.hooked:
            add([f'sub_{g:08X}'], 'area_watch_synth.cpp.obj', 0x60)
        self.text_end = rva
        self.rdata_rva = align(rva, 0x1000)
        self.data = [(self.rdata_rva + 0x10 * k, f'?kTable{k}@synth@@3QBHB', 'tables.cpp.obj')
                     for k in range(n_data)]
        self.data.append((self.rdata_rva + 0x10 * n_data, '__imp_Sleep', 'kernel32:KERNEL32.dll'))
        self.rdata_len = 0x10 * (n_data + 1)
        self.data_rva = align(self.rdata_rva + self.rdata_len, 0x1000)
        self.pdata_rva = self.data_rva + 0x2000
        self.image_size = self.pdata_rva + 0x1000
        self.line_count = 0

    def write(self, path, image='synthgame'):
        def sym(sec, off, name, va, obj):
            return f' {sec:04x}:{off:08x}       {name:<26} {va:016x}     {obj}'
        L = [f' {image}', '', ' Timestamp is 00000000 (Thu Jan  1 00:00:00 1970)', '',
             f' Preferred load address is {IMAGE_BASE:016x}', '',
             ' Start         Length     Name                   Class',
             f' 0001:00000000 {0x100:08x}H .text                   CODE',
             f' 0001:00000100 {self.text_end - TEXT_RVA - 0x100:08x}H .text$mn                CODE',
             f' 0002:00000000 {self.rdata_len:08x}H .rdata                  DATA',
             f' 0003:00000000 {0x2000:08x}H .data                   DATA',
             f' 0004:00000000 {0x1000:08x}H .pdata                  DATA',
             '', '  Address         Publics by Value              Rva+Base               Lib:Object',
             '',
             sym(0, 0, '__AbsoluteZero', 0, '<absolute>'),
             sym(0, 0, '__ImageBase', IMAGE_BASE, '<linker-defined>')]
        pubs, stats = [], []
        for rva, _size, names, obj, static in self.code:
            for nm in names:
                (stats if static else pubs).append((rva, 1, rva - TEXT_RVA, nm, obj))
        for rva, nm, obj in self.data:
            pubs.append((rva, 2, rva - self.rdata_rva, nm, obj))
        pubs.sort(key=lambda s: (s[0], s[3]))
        L += [sym(s[1], s[2], s[3], IMAGE_BASE + s[0], s[4]) for s in pubs]
        L += ['', f' entry point at         0001:{self.by_name["mainCRTStartup"][0] - TEXT_RVA:08x}',
              '', ' Static symbols', '']
        L += [sym(s[1], s[2], s[3], IMAGE_BASE + s[0], s[4]) for s in stats]
        with open(path, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write('\n'.join(L) + '\n')
        self.line_count = len(pubs) + len(stats) + 2


# =============================================================================
# LSP1 / LSPX writers
# =============================================================================

def lsp1_header(mods):
    out = [b'LSP1', struct.pack('<I', len(mods))]
    for base, size, name in mods:
        nb = name.encode()
        out.append(struct.pack('<QII', base, size, len(nb)) + nb)
    return b''.join(out)


def write_lsp1(path, mods, samples, tail=b''):
    with open(path, 'wb') as f:
        f.write(lsp1_header(mods))
        f.write(struct.pack('<Q', len(samples)))
        for tid, frames in samples:
            f.write(struct.pack(f'<II{len(frames)}Q', tid, len(frames), *frames))
        f.write(tail)


def lspx(version, seconds, rounds, mode, names, extra=b'', qs=5_000_000_000):
    body = struct.pack('<QQQQII', QPC_FREQ, qs, qs + int(seconds * QPC_FREQ), rounds, mode,
                       len(names))
    for tid in sorted(names):
        nb = names[tid].encode('utf-8')
        body += struct.pack('<II', tid, len(nb)) + nb
    body += extra
    return b'LSPX' + struct.pack('<II', version, len(body)) + body


# =============================================================================
# Small deterministic profile
# =============================================================================

NAMES = {100: 'synth-main', 200: 'synth-render', 300: 'synth-waiter', 400: 'synth-driver',
         500: ''}


def small_samples(m: SynthMap, wait_leaf: int):
    rnd = random.Random(3)
    E = m.by_name

    def at(e):
        return IMAGE_BASE + e[0] + rnd.randrange(e[1])

    def ret(e):
        return IMAGE_BASE + e[0] + rnd.randrange(1, e[1])

    g = lambda k: E[f'sub_{guest_addr(k):08X}']
    run, never = E['?RunGuest@synth@@YAXXZ'], E['?NeverCalled@synth@@YAXXZ']
    crt, draw, pump = E['mainCRTStartup'], E['?Draw@Renderer@gpu_native@legodimensions@@QEAAXXZ'], \
        E['?Pump@synth@@YAXXZ']
    hx = m.hooked[0]
    hook, orig = E[f'sub_{hx:08X}'], E[f'__imp__sub_{hx:08X}']
    S = []
    for i in range(600):   # main: guest A (400) / guest B (200) <- guest 12 <- Dispatch <- RunGuest
        leaf = at(g(10)) if i < 400 else at(g(11))
        S.append((100, [leaf, ret(g(12)), IMAGE_BASE + never[0], ret(run), ret(crt)]))
    for i in range(50):    # hook (25 self) / hooked original (25 self, called by the hook)
        S.append((100, [at(hook), ret(run), ret(crt)] if i < 25 else
                  [at(orig), ret(hook), ret(run), ret(crt)]))
    for _ in range(300):   # render: gpu_native
        S.append((200, [at(draw), ret(pump), ret(crt)]))
    for _ in range(1000):  # waiter: ntdll!NtWaitForSingleObject
        S.append((300, [wait_leaf, ret(pump), ret(crt)]))
    for _ in range(100):   # driver dll without a file on disk
        S.append((400, [DRV_BASE + rnd.randrange(0x100000), ret(draw), ret(pump)]))
    for i in range(120):   # data address (50), no module (50), ICF-aliased function (20)
        leaf = (IMAGE_BASE + m.rdata_rva + 0x20 if i < 50 else 0x10 if i < 100 else
                at(E['?Same0@synth@@YAXXZ']))
        S.append((500, [leaf, ret(pump)]))
    return S


# =============================================================================
# Test runner
# =============================================================================

class Results:
    def __init__(self):
        self.rows = []

    def check(self, name, ok, detail=''):
        self.rows.append(('PASS' if ok else 'FAIL', name, detail))
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f': {detail}' if detail else ''), flush=True)


def run_json(argv, out):
    ap._warnings.clear()
    ap.main(argv + ['--json', '-o', out])
    with open(out, encoding='utf-8') as f:
        return json.load(f)


def run_text(argv, out):
    ap._warnings.clear()
    ap.main(argv + ['-o', out])
    with open(out, encoding='utf-8') as f:
        return f.read()


def by_tid(rep, tid):
    return next((t for t in rep['threads'] if t['tid'] == tid), None)


def find(rows, pred):
    return next((r for r in rows if pred(r)), None)


def any_warn(rep, text):
    return any(text in w for w in rep['warnings'])


def small_tests(R: Results, m: SynthMap, map_path: str, wait_leaf: int, nt_size: int):
    mods = [(IMAGE_BASE, m.image_size, 'synthgame.exe'), (NTDLL_BASE, nt_size, 'ntdll.dll'),
            (DRV_BASE, 0x200000, 'nvsynthumd64.dll')]
    S = small_samples(m, wait_leaf)
    n = len(S)
    files = {
        'a_notrailer': b'',
        'b_mode0': lspx(1, 2.0, 1000, 0, NAMES),
        'c_mode1': lspx(1, 2.0, 1000, 1, NAMES),
        'd_bigpayload': lspx(1, 2.0, 1000, 1, NAMES, extra=struct.pack('<QQQ', 7, 8, 9)),
        'e1_garbage': b'\xde\xad\xbe\xef' * 5,
        'e2_truncated': lspx(1, 2.0, 1000, 1, NAMES)[:30],
        'e3_version2': lspx(2, 2.0, 1000, 1, NAMES, extra=b'\x01' * 12),
        'e4_trailing_after_lspx': lspx(1, 2.0, 1000, 1, NAMES) + b'zz',
    }
    P = {}
    for k, tail in files.items():
        P[k] = os.path.join(OUT, f'{k}.bin')
        write_lsp1(P[k], mods, S, tail)
    J = lambda k, *extra: run_json([P[k], map_path, *extra], os.path.join(OUT, f'{k}.json'))
    hx = m.hooked[0]

    # --- (a) legacy file, no trailer --------------------------------------------------------
    a = J('a_notrailer')
    R.check('a: no trailer parses, samples', a['trailer'] is None and a['samples'] == n,
            f"samples {a['samples']}/{n}")
    R.check('a: observer effect true, duration estimated',
            a['timer_observer_effect'] is True and a['duration']['source'] == 'estimate'
            and a['rate_unit'] == '/1k rounds' and a['duration']['rounds_estimated'] == 1000
            and any_warn(a, 'no recording duration'),
            f"{a['timer_observer_effect']} {a['duration']}")
    cb = a['categories_busy']
    exp = {'guest': 625, 'rexlego': 45, 'native-gpu': 300, 'd3d12+driver': 100, 'unknown': 100}
    R.check('a: busy categories', all(cb[c] == v for c, v in exp.items())
            and a['totals'] == {'busy': 1170, 'waiting': 1000, 'io': 0}, f'{cb} {a["totals"]}')
    w = by_tid(a, 300)
    R.check('a: ntdll!NtWaitForSingleObject leaf = waiting (real System32 ntdll exports)',
            w and w['waiting'] == 1000 and w['busy'] == 0 and w['role'] == 'synth::Pump',
            f"wait {w and w['waiting']} role {w and w['role']!r}")
    t0 = a['top_self'][0]
    R.check('a: guest name / address / category',
            t0['name'] == f'sub_{guest_addr(10):08X} [guest 0x{guest_addr(10):08X}]'
            and t0['guest_addr'] == f'0x{guest_addr(10):08X}' and t0['category'] == 'guest'
            and t0['samples'] == 400 and t0['rate'] == 400.0,
            f"{t0['name']} {t0['category']} {t0['samples']} rate {t0.get('rate')}")
    hk = find(a['top_self'], lambda r: r['kind'] == 'hook')
    ho = find(a['top_self'], lambda r: r['kind'] == 'hooked original')
    R.check('a: hook (host category) and hooked original (guest)',
            hk and ho and hk['category'] == 'rexlego' and ho['category'] == 'guest'
            and hk['name'] == f'sub_{hx:08X} [hook of guest 0x{hx:08X}]'
            and ho['name'] == f'__imp__sub_{hx:08X} [guest 0x{hx:08X}, hooked original]'
            and hk['samples'] == 25 and ho['samples'] == 25,
            f"{hk and hk['name']} / {ho and ho['name']}")
    inc = {r['name']: r['samples'] for r in by_tid(a, 100)['top_inclusive']}
    R.check('a: return address at function end -> caller (addr-1)',
            inc.get('synth::Dispatch') == 600 and not any('NeverCalled' in x for x in inc),
            f"Dispatch {inc.get('synth::Dispatch')}, NeverCalled absent")
    sm = find(a['top_self'], lambda r: r['name'].startswith('synth::Same0'))
    R.check('a: ICF aliases counted', sm and sm['name'] == 'synth::Same0 {+2 aliases}',
            sm and sm['name'])
    dv = find(a['top_self'], lambda r: r['module'] == 'nvsynthumd64.dll')
    R.check('a: driver dll without file -> d3d12+driver', dv and dv['category'] == 'd3d12+driver',
            dv and f"{dv['name']} {dv['category']}")
    txt = run_text([P['a_notrailer'], map_path], os.path.join(OUT, 'a_notrailer.txt'))
    R.check('a: text header has the observer warning', 'WARNING: ' + ap.OBSERVER_WARNING in txt)

    # --- (b) v1 trailer timer_mode 0 -----------------------------------------------------------
    b = J('b_mode0')
    R.check('b: v1 trailer mode 0 -> observer true, duration 2.0 s from trailer',
            b['trailer'] and b['trailer']['timer_mode'] == 0 and b['timer_observer_effect'] is True
            and b['duration']['source'] == 'trailer' and abs(b['duration']['seconds'] - 2.0) < 1e-9
            and b['rate_unit'] == '/s',
            f"{b['timer_observer_effect']} {b['duration']}")

    # --- (c) v1 trailer timer_mode 1 -----------------------------------------------------------
    c = J('c_mode1')
    names_ok = all((by_tid(c, t) or {}).get('name') == nm for t, nm in NAMES.items())
    R.check('c: v1 trailer mode 1 -> observer false, names per tid',
            c['timer_observer_effect'] is False and names_ok and c['trailer']['rounds'] == 1000
            and c['trailer']['thread_count'] == 5 and c['trailer']['extra_payload_bytes'] == 0,
            f"{c['timer_observer_effect']} names_ok={names_ok}")
    txt = run_text([P['c_mode1'], map_path], os.path.join(OUT, 'c_mode1.txt'))
    R.check('c: text has no observer warning', ap.OBSERVER_WARNING not in txt
            and 'synth-waiter' in txt)
    fold = run_text([P['c_mode1'], map_path, '--folded', '--folded-thread'],
                    os.path.join(OUT, 'c_mode1.folded'))
    want = (f'thread 100 synth-main;mainCRTStartup;synth::RunGuest;synth::Dispatch;'
            f'sub_{guest_addr(12):08X} [guest 0x{guest_addr(12):08X}];'
            f'sub_{guest_addr(10):08X} [guest 0x{guest_addr(10):08X}] 400')
    R.check('c: --folded --folded-thread line', want in fold.splitlines(), want)

    # --- (d) payload larger than v1 ----------------------------------------------------------
    d = J('d_bigpayload')
    R.check('d: payload_bytes > v1 (24 extra bytes) parses',
            d['trailer'] and d['trailer']['extra_payload_bytes'] == 24
            and d['timer_observer_effect'] is False and by_tid(d, 300)['name'] == 'synth-waiter'
            and not d['warnings'], f"extra {d['trailer'] and d['trailer']['extra_payload_bytes']}"
            f" warnings {d['warnings']}")

    # --- (e) garbage / truncated / v2 / bytes after the block ------------------------------------
    e1 = J('e1_garbage')
    R.check('e1: garbage after samples -> warning, still reports',
            e1['trailer'] is None and e1['samples'] == n and any_warn(e1, 'unknown trailing bytes')
            and e1['timer_observer_effect'] is True, '; '.join(e1['warnings'][:1]))
    e2 = J('e2_truncated')
    R.check('e2: truncated LSPX -> ignored with warning',
            e2['trailer'] is None and e2['samples'] == n and any_warn(e2, 'truncated'),
            '; '.join(e2['warnings'][:1]))
    e3 = J('e3_version2')
    R.check('e3: LSPX version 2 -> v1 fields read, warning',
            e3['trailer'] and e3['trailer']['version'] == 2 and e3['trailer']['timer_mode'] == 1
            and e3['trailer']['extra_payload_bytes'] == 12 and any_warn(e3, 'version 2'),
            '; '.join(e3['warnings'][:1]))
    e4 = J('e4_trailing_after_lspx')
    R.check('e4: bytes after the LSPX block -> warning, trailer kept',
            e4['trailer'] and e4['timer_observer_effect'] is False
            and any_warn(e4, 'after the LSPX block'), '; '.join(e4['warnings'][:1]))

    # --- durations ------------------------------------------------------------------------------
    def meta(name, obj):
        p = os.path.join(OUT, name)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(obj, f)
        return p
    cases = [
        ('--duration-s 4', ['--duration-s', '4'], 4.0, '--duration'),
        ('--meta duration_s', ['--meta', meta('m1.json', {'duration_s': 3.0})], 3.0, 'meta'),
        ('--meta nested duration_s', ['--meta', meta('m2.json', {'run': {'duration_s': 5}})], 5.0,
         'meta'),
        ('--meta profile_trigger_start/end (epoch)',
         ['--meta', meta('m3.json', {'profile_trigger_start': 1000.0,
                                     'profile_trigger_end': 1002.175})], 2.0, 'meta'),
        ('--meta trigger_start/end (ISO-8601)',
         ['--meta', meta('m4.json', {'trigger_start': '2026-11-21T18:00:00Z',
                                     'trigger_end': '2026-11-21T18:00:02.175Z'})], 2.0, 'meta'),
    ]
    for label, extra, want_s, src in cases:
        r = J('a_notrailer', *extra)
        R.check(f'duration: {label} -> {want_s} s', abs(r['duration']['seconds'] - want_s) < 1e-6
                and r['duration']['source'].startswith(src) and r['rate_unit'] == '/s',
                f"{r['duration']['seconds']} [{r['duration']['source']}]")
    r = J('b_mode0', '--duration-s', '9')
    R.check('duration: trailer beats --duration-s', r['duration']['source'] == 'trailer'
            and abs(r['duration']['seconds'] - 2.0) < 1e-9, str(r['duration']))

    # --- options ----------------------------------------------------------------------------------
    r = J('c_mode1', '--thread', '200')
    R.check('--thread 200', [t['tid'] for t in r['threads']] == [200] and r['counted_samples'] == 300,
            f"{[t['tid'] for t in r['threads']]} counted {r['counted_samples']}")
    r = J('c_mode1', '--by', 'module')
    mods_self = {x['module']: x['samples'] for x in r['modules_self']}
    # busy leaves in synthgame.exe: guest 625 + hook 25 + gpu 300 + data address 50 + ICF 20
    R.check('--by module', mods_self.get('synthgame.exe') == 1020
            and mods_self.get('nvsynthumd64.dll') == 100 and mods_self.get('?') == 50, str(mods_self))
    r = J('c_mode1', '--focus', r'^synth::Dispatch$')
    fo = r['focus']
    R.check('--focus synth::Dispatch callers/callees',
            fo['inclusive'] == 600 and fo['callers'][0]['name'] == 'synth::RunGuest'
            and fo['callees'][0]['name'] == f'sub_{guest_addr(12):08X} [guest 0x{guest_addr(12):08X}]',
            f"incl {fo['inclusive']} callers {[x['name'] for x in fo['callers']]}")
    r = J('c_mode1', '--fold-guest')
    R.check('--fold-guest', r['top_self'][0]['name'] == 'guest [folded]'
            and r['top_self'][0]['samples'] == 625, str(r['top_self'][0]))
    r = J('c_mode1', '--include-waits')
    R.check('--include-waits counts waits', r['counted_samples'] == n
            and r['top_self'][0]['name'] == 'ntdll.dll!NtWaitForSingleObject',
            f"counted {r['counted_samples']} top {r['top_self'][0]['name']}")
    dj = os.path.join(OUT, 'diff_bc.json')
    r = run_json(['--diff', P['b_mode0'], map_path, P['c_mode1'], map_path], dj)
    R.check('--diff b vs c (same samples, both 2 s): zero deltas, /s',
            r['unit'] == '/s' and r['max_abs_delta_self'] == 0
            and r['a']['timer_observer_effect'] is True and r['b']['timer_observer_effect'] is False,
            f"unit {r['unit']} max {r['max_abs_delta_self']}")
    r = run_json(['--diff', P['a_notrailer'], map_path, P['a_notrailer'], map_path,
                  '--duration-a', '2', '--duration-b', '4'], dj)
    top = r['self'][0]
    R.check('--diff --duration-a 2 --duration-b 4: rates halve',
            r['unit'] == '/s' and top['a'] == 200.0 and top['b'] == 100.0 and top['delta'] == -100.0,
            f"{top['name']}: {top['a']} -> {top['b']}")
    r = run_json(['--diff', P['a_notrailer'], map_path, P['a_notrailer'], map_path,
                  '--meta-a', os.path.join(OUT, 'm1.json'), '--meta-b', os.path.join(OUT, 'm4.json')], dj)
    R.check('--diff --meta-a/--meta-b', r['unit'] == '/s' and r['a']['duration']['seconds'] == 3.0
            and abs(r['b']['duration']['seconds'] - 2.0) < 1e-6,
            f"{r['a']['duration']['seconds']} / {r['b']['duration']['seconds']}")
    r = run_json(['--diff', P['a_notrailer'], map_path, P['a_notrailer'], map_path], dj)
    R.check('--diff without durations -> /1k rounds + warning', r['unit'] == '/1k rounds'
            and any_warn(r, 'per 1000 sampler rounds'), r['unit'])


# =============================================================================
# 1M-sample timing
# =============================================================================

def gen_big(path, m: SynthMap, n, wait_leaf, nt_size, seed=7):
    rnd = random.Random(seed)
    funcs = [e for e in m.code if e[1] >= 0x20]
    paths = []
    for _ in range(4000):
        d = rnd.randint(4, 23)
        fr = [IMAGE_BASE + e[0] + rnd.randrange(1, e[1]) for e in (rnd.choice(funcs) for _ in range(d))]
        leafs = []
        for _ in range(rnd.randint(1, 4)):
            e = rnd.choice(funcs)
            leafs += [IMAGE_BASE + e[0] + rnd.randrange(e[1]) for _ in range(8)]
        paths.append((d + 1, struct.pack(f'<{d}Q', *fr), leafs))
    nthreads = 20
    tids = [0x2000 + 4 * k for k in range(nthreads)]
    mods = [(IMAGE_BASE, m.image_size, 'synthgame.exe'), (NTDLL_BASE, nt_size, 'ntdll.dll')]
    pk = struct.Struct('<IIQ').pack
    rr = rnd.random
    npaths, nfuncs = len(paths), len(funcs)
    with open(path, 'wb') as f:
        f.write(lsp1_header(mods))
        f.write(struct.pack('<Q', n))
        buf = []
        for i in range(n):
            tid = tids[i % nthreads]
            x = rr()
            if x < 0.3:
                d, pb, _ = paths[int(npaths * rr() ** 2)]
                buf.append(pk(tid, d, wait_leaf) + pb)
            elif x < 0.4:
                d, pb, _ = paths[int(npaths * rr())]
                e = funcs[int(nfuncs * rr())]
                buf.append(pk(tid, d, IMAGE_BASE + e[0] + int(e[1] * rr())) + pb)
            else:
                d, pb, leafs = paths[int(npaths * rr() ** 3)]
                buf.append(pk(tid, d, leafs[int(len(leafs) * rr())]) + pb)
            if len(buf) >= 65536:
                f.write(b''.join(buf))
                buf.clear()
        f.write(b''.join(buf))
        rounds = n // nthreads
        f.write(lspx(1, rounds / 1000.0, rounds, 1, {t: f'synth-{k}' for k, t in enumerate(tids)}))


def run_measured(argv):
    t0 = time.perf_counter()
    p = subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    _, err = p.communicate()
    wall = time.perf_counter() - t0
    cpu = peak = None
    if os.name == 'nt':
        try:
            class PMC(ctypes.Structure):
                _fields_ = [('cb', ctypes.c_uint32), ('PageFaultCount', ctypes.c_uint32)] + [
                    (k, ctypes.c_size_t) for k in (
                        'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
                        'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage',
                        'PagefileUsage', 'PeakPagefileUsage')]
            h = ctypes.c_void_p(int(p._handle))
            pmc = PMC()
            pmc.cb = ctypes.sizeof(PMC)
            if ctypes.windll.kernel32.K32GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb):
                peak = pmc.PeakWorkingSetSize
            ft = [ctypes.c_uint64() for _ in range(4)]
            if ctypes.windll.kernel32.GetProcessTimes(h, *[ctypes.byref(x) for x in ft]):
                cpu = (ft[2].value + ft[3].value) / 1e7
        except Exception:  # noqa: BLE001 - measurement is best effort
            pass
    return p.returncode, wall, cpu, peak, err.decode('utf-8', 'replace')


def main():
    apg = argparse.ArgumentParser()
    apg.add_argument('--big', type=int, default=1_000_000)
    apg.add_argument('--skip-big', action='store_true')
    apg.add_argument('--keep-big', action='store_true')
    apg.add_argument('--real-map', help='time MapTable() on a real map (prints counts/timing only)')
    a = apg.parse_args()
    os.makedirs(OUT, exist_ok=True)
    R = Results()
    t0 = time.perf_counter()
    m = SynthMap()
    map_path = os.path.join(OUT, 'synthgame.map')
    m.write(map_path)
    t1 = time.perf_counter()
    mt = ap.MapTable(map_path)
    t2 = time.perf_counter()
    print(f'synthetic map: {m.line_count} symbol lines, {os.path.getsize(map_path) >> 20} MB, '
          f'generated {t1 - t0:.1f} s, parsed {t2 - t1:.2f} s -> {len(mt.rvas)} code entries, '
          f'{len(mt.code_ranges)} code range(s)', flush=True)
    R.check('map: data/absolute symbols excluded, code range',
            len(mt.code_ranges) == 1 and mt.code_ranges[0] == (TEXT_RVA, m.text_end)
            and len(mt.rvas) == len(m.code), f'{len(mt.rvas)} entries vs {len(m.code)} functions')
    nt = ap.PEImage(os.path.join(SYS32, 'ntdll.dll'))
    wait_leaf = NTDLL_BASE + nt.exp_rvas[nt.exp_names.index('NtWaitForSingleObject')] + 0x14
    small_tests(R, m, map_path, wait_leaf, nt.size_of_image)

    extra = []
    if not a.skip_big:
        big = os.path.join(OUT, 'big.bin')
        t0 = time.perf_counter()
        gen_big(big, m, a.big, wait_leaf, nt.size_of_image)
        gen_s = time.perf_counter() - t0
        size_mb = os.path.getsize(big) / 1e6
        bj = os.path.join(OUT, 'big.json')
        rc, wall, cpu, peak, err = run_measured([sys.executable, ANALYZER, big, map_path,
                                                 '--json', '-o', bj])
        with open(bj, encoding='utf-8') as f:
            rep = json.load(f) if rc == 0 else {}
        tm = rep.get('timing', {})
        line = (f'{a.big} samples ({size_mb:.0f} MB, generated in {gen_s:.1f} s): analysis wall '
                f'{wall:.1f} s, cpu {cpu if cpu is None else round(cpu, 1)} s, peak working set '
                f'{peak if peak is None else round(peak / 2**20)} MB; read {tm.get("read_s")} s, '
                f'map {tm.get("map_s")} s, symbolize {tm.get("symbolize_s")} s, '
                f'{tm.get("unique_stacks")} unique stacks, {tm.get("unique_addresses")} addresses, '
                f'{tm.get("functions")} functions')
        print(line, flush=True)
        extra.append(line)
        R.check(f'1M: analysis exit 0, all samples read, < 60 s wall',
                rc == 0 and rep.get('samples') == a.big and wall < 60.0,
                f'rc {rc} samples {rep.get("samples")} wall {wall:.1f} s' + (f' {err[-300:]}' if rc else ''))
        if not a.keep_big:
            os.remove(big)
    if a.real_map:
        t0 = time.perf_counter()
        rm = ap.MapTable(a.real_map)
        line = (f'real map parse: {os.path.getsize(a.real_map) >> 20} MB, {rm.symbol_lines} code '
                f'symbol lines -> {len(rm.rvas)} entries in {time.perf_counter() - t0:.2f} s')
        print(line, flush=True)
        extra.append(line)
    npass = sum(1 for r in R.rows if r[0] == 'PASS')
    verdict = 'PASS' if npass == len(R.rows) else 'FAIL'
    res = os.path.join(HERE, 'synth-result.txt')
    with open(res, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'synth_test {time.strftime("%Y-%m-%d %H:%M:%S")}: {verdict} '
                f'({npass}/{len(R.rows)})\n')
        for r in R.rows:
            f.write(f'{r[0]}  {r[1]}' + (f': {r[2]}' if r[2] else '') + '\n')
        for x in extra:
            f.write(x + '\n')
    print(f'synth_test: {verdict} ({npass}/{len(R.rows)}) -> {res}')
    return 0 if verdict == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())

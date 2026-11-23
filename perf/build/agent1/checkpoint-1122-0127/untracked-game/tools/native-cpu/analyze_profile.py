#!/usr/bin/env python3
"""Offline analyser for rexlego/src/sample_profiler.cpp profiles ("LSP1" files).

Standard library only (Python 3.11+). See README.md in this directory.

  analyze_profile.py PROFILE.bin [MAP]                       summary (threads, categories, top N)
  analyze_profile.py PROFILE.bin MAP --by module             per-module self/inclusive
  analyze_profile.py PROFILE.bin MAP --focus REGEX           callers/callees of matching functions
  analyze_profile.py PROFILE.bin MAP --folded                Brendan Gregg folded stacks
  analyze_profile.py --diff A.bin A.map B.bin B.map          per-function delta, samples per second
Common: --thread TID (repeatable), --include-waits, --fold-guest, --top N, --json, -o FILE.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import datetime as _dt
import glob
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time

# =============================================================================
# Tables (edit here)
# =============================================================================

# Leaf-frame classification. Each sample's leaf frame (frames[0]) is resolved to
# module + raw symbol (export name for system DLLs). The first rule whose module
# regex and symbol regex both fullmatch (module case-insensitive) decides the
# class; everything else is "busy" (running on a CPU when sampled).
LEAF_CLASS_RULES = [
    (r'ntdll\.dll', r'(?:Nt|Zw)(?:WaitFor\w+|DelayExecution|RemoveIoCompletion\w*|'
                    r'SignalAndWaitForSingleObject|ReplyWaitReceivePort\w*|AlpcSendWaitReceivePort|'
                    r'Wait(?:Low|High)EventPair|WaitForAlertByThreadId|WaitForKeyedEvent|'
                    r'WaitForWorkViaWorkerFactory|WaitForMultipleObjects32)', 'wait'),
    (r'win32u\.dll', r'NtUser(?:GetMessage|RealInternalGetMessage|MsgWaitForMultipleObjectsEx|'
                     r'WaitMessage|RealWaitMessageEx|WaitForInputIdle|WaitForMsgAndEvent)', 'wait'),
    (r'win32u\.dll', r'NtGdiDdDDI(?:WaitForSynchronizationObject\w*|WaitForVerticalBlankEvent\w*|'
                     r'WaitForIdle)', 'wait'),
    # Synchronous I/O: reported as "io", never counted as busy CPU.
    (r'ntdll\.dll', r'(?:Nt|Zw)(?:ReadFile\w*|WriteFile\w*|DeviceIoControlFile|FsControlFile|'
                    r'QueryDirectoryFile\w*|FlushBuffersFile\w*)', 'io'),
]

# Module names (fullmatch, case-insensitive) that count as D3D12 runtime / GPU driver.
D3D_DRIVER_MODULES = (
    r'd3d12\w*\.dll|d3d12sdklayers\.dll|dxgi\.dll|dxcore\.dll|d3d11\.dll|d3d10warp\.dll|'
    r'dxilconv\.dll|dxcompiler\.dll|dxil\.dll|d3dcompiler_\d+\.dll|'
    r'nv\w*umd\w*\.dll|nvwgf2umx\w*\.dll|nvldumdx\.dll|nvgpucomp\w*\.dll|nvapi64\.dll|'
    r'igd\w*\.dll|igc\w*\.dll|igxelp\w*\.dll|amdxc\w*\.dll|atidxx\w*\.dll|amdxn\w*\.dll|amdihk64\.dll')

# Category rules, first match wins:
#   (category, scope, module_re, symbol_re, object_re)
# scope 'main' = the module symbolized by the main lld map (the game exe),
# 'module' = any other module. Regexes fullmatch; None = any. symbol_re sees the
# raw (decorated) name; object_re sees the map's Lib:Object column.
# '<GPU_NATIVE_OBJECTS>' = an object compiled from rexlego/src/gpu_native/*.cpp
# (the map only has object base names); '<SYSTEM32>' = module file found in System32.
# Fallbacks: 'other' (known module, no rule), 'unknown' (address in no module /
# no symbol in the exe's code ranges).
CATEGORY_RULES = [
    ('guest', 'main', None, r'(?:__imp__)?sub_[0-9A-Fa-f]{8}', None),
    ('guest', 'main', None, None, r'(?:.*:)?.*_recomp\.\d+\.cpp\.obj'),
    ('native-gpu', 'main', None, r'.*@gpu_native@.*', None),
    ('native-gpu', 'main', None, None, '<GPU_NATIVE_OBJECTS>'),
    ('rexlego', 'main', None, None, None),
    ('rexruntime', 'module', r'rexruntime\w*\.dll', None, None),
    ('d3d12+driver', 'module', D3D_DRIVER_MODULES, None, None),
    ('d3d12+driver', 'module', r'win32u\.dll', r'Nt(?:GdiDdDDI|Dxgk)\w*', None),
    ('d3d12+driver', 'module', r'gdi32(?:full)?\.dll', r'D3DKMT\w*', None),
    ('system', 'module', '<SYSTEM32>', None, None),
]
CATEGORY_ORDER = ['guest', 'rexruntime', 'native-gpu', 'rexlego', 'd3d12+driver', 'system',
                  'other', 'unknown']
# Runtime DLLs treated as "system" even when they sit next to the exe.
SYSTEM_EXTRA = r'ucrtbase\w*\.dll|msvcp\d+\w*\.dll|vcruntime\d+\w*\.dll|concrt\d+\.dll'

OBSERVER_WARNING = ('sampler held timeBeginPeriod(1): guest Sleep granularity differs from an '
                    'unprofiled run; use for attribution, not timing')
TRIGGER_LATENCY_S = 0.175   # 50 ms trigger poll (avg 25) + 150 ms Beep before recording starts
MAX_DEPTH = 64              # sanity bound; the producer writes at most 24 frames

GUEST_NAME_RE = re.compile(r'(__imp__)?sub_([0-9A-Fa-f]{8})')
GUEST_SEARCH_RE = re.compile(r'sub_([0-9A-Fa-f]{8})(?![0-9A-Fa-f])')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_warnings: list[str] = []


def warn(msg: str) -> None:
    if msg not in _warnings:
        _warnings.append(msg)
        print('warning: ' + msg, file=sys.stderr)


# =============================================================================
# LSP1 reader
# =============================================================================

class Profile:
    def __init__(self, path: str):
        self.path = path
        self.modules: list[tuple[int, int, str]] = []
        self.sample_count = 0
        self.counts: dict[int, int] = {}      # (sid << 32 | tid) -> samples
        self.stacks: list[bytes] = []         # sid -> raw little-endian u64 frames
        self.trailer: dict | None = None
        self.tid_counts: collections.Counter = collections.Counter()
        self._read()

    def _read(self) -> None:
        with open(self.path, 'rb') as f:
            data = f.read()
        end = len(data)
        if data[:4] != b'LSP1':
            raise SystemExit(f'{self.path}: not an LSP1 profile (magic {data[:4]!r})')
        (nmod,) = struct.unpack_from('<I', data, 4)
        off = 8
        for _ in range(nmod):
            base, size, nlen = struct.unpack_from('<QII', data, off)
            off += 16
            self.modules.append((base, size, data[off:off + nlen].decode('utf-8', 'replace')))
            off += nlen
        (nsamples,) = struct.unpack_from('<Q', data, off)
        off += 8
        hdr = struct.Struct('<II').unpack_from
        stack_ids: dict[bytes, int] = {}
        stacks = self.stacks
        counts = self.counts
        get = stack_ids.get
        read = 0
        for _ in range(nsamples):
            if off + 8 > end:
                warn(f'{self.path}: truncated after {read} of {nsamples} samples')
                break
            tid, depth = hdr(data, off)
            nb = depth << 3
            if depth > MAX_DEPTH or off + 8 + nb > end:
                warn(f'{self.path}: corrupt sample {read} (depth {depth}); stopping')
                break
            key = data[off + 8:off + 8 + nb]
            off += 8 + nb
            sid = get(key)
            if sid is None:
                sid = len(stacks)
                stack_ids[key] = sid
                stacks.append(key)
            k = (sid << 32) | tid
            counts[k] = counts.get(k, 0) + 1
            read += 1
        self.sample_count = read
        for k, n in counts.items():
            self.tid_counts[k & 0xFFFFFFFF] += n
        if off < end:
            self._read_trailer(data, off)

    def _read_trailer(self, data: bytes, off: int) -> None:
        end = len(data)
        if data[off:off + 4] != b'LSPX' or off + 12 > end:
            warn(f'{self.path}: {end - off} unknown trailing bytes after the samples (ignored)')
            return
        version, payload_bytes = struct.unpack_from('<II', data, off + 4)
        p0 = off + 12
        p_end = p0 + payload_bytes
        if p_end > end:
            warn(f'{self.path}: LSPX block truncated ({end - p0} of {payload_bytes} payload bytes); '
                 f'trailer ignored')
            return
        if payload_bytes < 40:
            warn(f'{self.path}: LSPX payload too small for v1 ({payload_bytes} bytes); trailer ignored')
            return
        t = {'version': version, 'payload_bytes': payload_bytes}
        freq, qs, qe, rounds, mode, nthreads = struct.unpack_from('<QQQQII', data, p0)
        if freq == 0 or qe < qs:
            warn(f'{self.path}: implausible LSPX timing (freq {freq}, start {qs}, end {qe}); '
                 f'trailer ignored')
            return
        t.update(qpc_frequency=freq, qpc_start=qs, qpc_end=qe, rounds=rounds,
                 timer_mode=mode, thread_count=nthreads)
        names = {}
        p = p0 + 40
        for _ in range(nthreads):
            if p + 8 > p_end:
                warn(f'{self.path}: LSPX thread table truncated; names after {len(names)} ignored')
                break
            tid, nlen = struct.unpack_from('<II', data, p)
            if p + 8 + nlen > p_end:
                warn(f'{self.path}: LSPX thread name truncated; names after {len(names)} ignored')
                break
            names[tid] = data[p + 8:p + 8 + nlen].decode('utf-8', 'replace')
            p += 8 + nlen
        t['thread_names'] = names
        t['extra_payload_bytes'] = max(0, p_end - p)
        if version != 1:
            warn(f'{self.path}: LSPX version {version}; read the v1 fields only')
        self.trailer = t
        rest = end - (p0 + payload_bytes)
        if rest > 0:
            warn(f'{self.path}: {rest} unknown bytes after the LSPX block (ignored)')

    @property
    def thread_names(self) -> dict[int, str]:
        return (self.trailer or {}).get('thread_names', {})

    def observer_effect(self):
        if not self.trailer or 'timer_mode' not in self.trailer:
            return True             # legacy sampler: always timeBeginPeriod(1) + Sleep(1)
        mode = self.trailer['timer_mode']
        return True if mode == 0 else False if mode == 1 else 'unknown'


# =============================================================================
# lld-link /MAP reader
# =============================================================================

_SEC_RE = re.compile(r'^\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]+)H\s+(\S+)\s+(CODE|DATA)\b')


class MapTable:
    """Code symbols of one image from an MSVC-style map written by lld-link /MAP."""

    def __init__(self, path: str):
        self.path = path
        self.image_name = ''
        self.image_base = None
        self.rvas: list[int] = []
        self.entries: list[tuple] = []     # (name, obj, alias_count, kind, guest_addr)
        self.code_ranges: list[tuple[int, int]] = []
        self.symbol_lines = 0
        self._parse()

    def _parse(self) -> None:
        sec_code: dict[int, bool] = {}
        sec_ext: dict[int, list[int]] = {}
        sec_rva: dict[int, int] = {}
        syms = []
        part = 0
        with open(self.path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                if part == 0:
                    if not self.image_name and line.strip():
                        self.image_name = line.strip()
                    if 'Preferred load address is' in line:
                        self.image_base = int(line.split()[-1], 16)
                        continue
                    m = _SEC_RE.match(line)
                    if m:
                        sec = int(m.group(1), 16)
                        start, length = int(m.group(2), 16), int(m.group(3), 16)
                        sec_code[sec] = sec_code.get(sec, False) or m.group(5) == 'CODE'
                        ext = sec_ext.setdefault(sec, [start, start + length])
                        ext[0] = min(ext[0], start)
                        ext[1] = max(ext[1], start + length)
                    elif 'Publics by Value' in line:
                        part = 1
                    continue
                parts = line.split()
                if len(parts) < 3:
                    if len(parts) == 2 and parts[0] == 'Static' and parts[1] == 'symbols':
                        part = 2
                    elif len(parts) == 1 and parts[0] == 'Exports':
                        break
                    continue
                ss = parts[0]
                if len(ss) != 13 or ss[4] != ':':
                    continue
                try:
                    sec = int(ss[:4], 16)
                    if not sec_code.get(sec):
                        continue
                    va = int(parts[2], 16)
                except ValueError:
                    continue
                rest = parts[3:]
                while rest and len(rest) > 1 and rest[0] in ('f', 'i'):
                    rest = rest[1:]
                rva = va - (self.image_base or 0)
                if sec not in sec_rva:
                    sec_rva[sec] = rva - int(ss[5:], 16)
                syms.append((rva, part == 2, parts[1], ' '.join(rest)))
        if self.image_base is None:
            raise SystemExit(f'{self.path}: no "Preferred load address" line; not an lld/MSVC map?')
        self.symbol_lines = len(syms)
        for sec, (s, e) in sec_ext.items():
            if sec_code.get(sec) and sec in sec_rva:
                self.code_ranges.append((sec_rva[sec] + s, sec_rva[sec] + e))
        self.code_ranges.sort()
        self._range_starts = [r[0] for r in self.code_ranges]
        syms.sort(key=lambda s: s[0])
        # Guest names: sub_X (codegen alias or a hook) vs __imp__sub_X (original body).
        plain_at: dict[int, set] = collections.defaultdict(set)
        imp_at: dict[int, set] = collections.defaultdict(set)
        for rva, _st, name, _obj in syms:
            m = GUEST_NAME_RE.fullmatch(name)
            if m:
                (imp_at if m.group(1) else plain_at)[int(m.group(2), 16)].add(rva)
        i, n = 0, len(syms)
        while i < n:
            j = i + 1
            rva = syms[i][0]
            while j < n and syms[j][0] == rva:
                j += 1
            best = min(syms[i:j], key=_alias_rank)
            name, obj = best[2], best[3]
            kind, guest = '', None
            m = GUEST_NAME_RE.fullmatch(name)
            if m:
                guest = int(m.group(2), 16)
                if m.group(1):   # __imp__sub_X: original body; hooked if sub_X lives elsewhere
                    if plain_at.get(guest, set()) - {rva}:
                        kind = 'hooked original'
                    else:
                        name = name[7:]
                elif imp_at.get(guest, set()) - {rva}:
                    kind = 'hook'
            else:
                m = GUEST_SEARCH_RE.search(name)
                if m and name.startswith('?'):
                    guest = int(m.group(1), 16)
            aliases = sum(1 for s in syms[i:j]
                          if s[2] != best[2] and not _is_guest_pair(s[2], best[2]))
            self.rvas.append(rva)
            self.entries.append((name, obj, aliases, kind, guest))
            i = j

    def lookup(self, rva: int):
        """-> entry index or None (address outside the code ranges / before any symbol)."""
        r = bisect.bisect_right(self._range_starts, rva) - 1
        if r < 0 or rva >= self.code_ranges[r][1]:
            return None
        i = bisect.bisect_right(self.rvas, rva) - 1
        if i < 0 or self.rvas[i] < self.code_ranges[r][0]:
            return None
        return i


def _is_guest_pair(a: str, b: str) -> bool:
    return a == '__imp__' + b or b == '__imp__' + a


def _alias_rank(sym):
    _rva, static, name, _obj = sym
    m = GUEST_NAME_RE.fullmatch(name)
    guest_rank = 0 if (m and not m.group(1)) else 1 if m else 2
    thunk = name.startswith('__imp_') or '$thunk' in name or name.startswith('__guard')
    return (guest_rank, static, thunk, len(name), name)


# =============================================================================
# PE reader (exports + .pdata) for modules without a map
# =============================================================================

class PEImage:
    def __init__(self, path: str):
        self.path = path
        with open(path, 'rb') as f:
            data = f.read()
        if data[:2] != b'MZ':
            raise ValueError('no MZ header')
        (pe,) = struct.unpack_from('<I', data, 0x3C)
        if data[pe:pe + 4] != b'PE\0\0':
            raise ValueError('no PE header')
        _machine, nsec, _, _, _, opt_size, _ = struct.unpack_from('<HHIIIHH', data, pe + 4)
        opt = pe + 24
        (magic,) = struct.unpack_from('<H', data, opt)
        (self.size_of_image,) = struct.unpack_from('<I', data, opt + 56)
        if magic == 0x20B:
            (ndirs,) = struct.unpack_from('<I', data, opt + 108)
            dirs = opt + 112
        elif magic == 0x10B:
            (ndirs,) = struct.unpack_from('<I', data, opt + 92)
            dirs = opt + 96
        else:
            raise ValueError(f'unknown optional header magic {magic:#x}')
        self.sections = []
        so = opt + opt_size
        for k in range(nsec):
            vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', data, so + 40 * k + 8)
            (chars,) = struct.unpack_from('<I', data, so + 40 * k + 36)
            self.sections.append((va, max(vsize, rawsize), rawptr, rawsize, chars))
        self.data = data

        def ddir(k):
            return struct.unpack_from('<II', data, dirs + 8 * k) if k < ndirs else (0, 0)

        exp_rva, exp_size = ddir(0)
        names_by_rva: dict[int, list[str]] = collections.defaultdict(list)
        if exp_rva and self.off(exp_rva) is not None:
            o = self.off(exp_rva)
            (_c, _t, _mj, _mn, _name, _base, nfunc, nname, afunc, aname,
             aord) = struct.unpack_from('<IIHHIIIIIII', data, o)
            funcs = struct.unpack_from(f'<{nfunc}I', data, self.off(afunc)) if nfunc else ()
            nrvas = struct.unpack_from(f'<{nname}I', data, self.off(aname)) if nname else ()
            ords = struct.unpack_from(f'<{nname}H', data, self.off(aord)) if nname else ()
            for nrva, ordinal in zip(nrvas, ords):
                if ordinal >= len(funcs):
                    continue
                frva = funcs[ordinal]
                if exp_rva <= frva < exp_rva + exp_size or not self.is_exec(frva):
                    continue   # forwarder or data export
                no = self.off(nrva)
                if no is None:
                    continue
                names_by_rva[frva].append(data[no:data.index(b'\0', no)].decode('ascii', 'replace'))
        self.exp_rvas = sorted(names_by_rva)
        self.exp_names = [min(names_by_rva[r], key=lambda s: (s.startswith('Zw'), len(s), s))
                          for r in self.exp_rvas]
        exc_rva, exc_size = ddir(3)
        self.pb = self.pe_ = self.pu = ()
        if exc_rva and exc_size >= 12 and self.off(exc_rva) is not None:
            nfn = exc_size // 12
            arr = struct.unpack_from(f'<{3 * nfn}I', data, self.off(exc_rva))
            self.pb, self.pe_, self.pu = arr[0::3], arr[1::3], arr[2::3]
        if not self.pb:
            self.data = b''   # only needed to follow chained unwind info

    def off(self, rva: int):
        for va, size, rawptr, rawsize, _ch in self.sections:
            if va <= rva < va + size:
                d = rva - va
                return rawptr + d if d < rawsize else None
        return None

    def is_exec(self, rva: int) -> bool:
        for va, size, _rp, _rs, ch in self.sections:
            if va <= rva < va + size:
                return bool(ch & 0x20000000)
        return False

    def _primary(self, idx: int) -> int:
        data = self.data
        for _ in range(32):
            u = self.pu[idx]
            if u & 1:      # RUNTIME_FUNCTION_INDIRECT
                o = self.off(u & ~1)
                if o is None:
                    break
                b = struct.unpack_from('<I', data, o)[0]
            else:
                o = self.off(u)
                if o is None or o + 4 > len(data):
                    break
                if not (data[o] >> 3) & 0x4:          # UNW_FLAG_CHAININFO
                    break
                co = o + 4 + ((data[o + 2] + 1) & ~1) * 2
                b = struct.unpack_from('<I', data, co)[0]
            j = bisect.bisect_left(self.pb, b)
            if j < len(self.pb) and self.pb[j] == b and j != idx:
                idx = j
                continue
            return b
        return self.pb[idx]

    def lookup(self, rva: int):
        """-> (function key rva, display name, raw export name or '') or None."""
        start = None
        if self.pb:
            i = bisect.bisect_right(self.pb, rva) - 1
            if i >= 0 and rva < self.pe_[i]:
                start = self._primary(i)
        if start is not None:
            j = bisect.bisect_right(self.exp_rvas, start) - 1
            if j >= 0 and self.exp_rvas[j] == start:
                return start, self.exp_names[j], self.exp_names[j]
            near = f' (near {self.exp_names[j]}+0x{start - self.exp_rvas[j]:X})' if j >= 0 else ''
            return start, f'fn_{start:X}{near}', ''
        j = bisect.bisect_right(self.exp_rvas, rva) - 1
        if j >= 0:
            return self.exp_rvas[j], self.exp_names[j], self.exp_names[j]
        return None


# =============================================================================
# Demangling
# =============================================================================

_SPECIAL_NAMES = {'0': None, '1': None, '2': 'operator new', '3': 'operator delete',
                  '4': 'operator=', 'R': 'operator()', 'A': 'operator[]', '8': 'operator==',
                  '9': 'operator!=', '_G': "`scalar deleting dtor'", '_E': "`vector deleting dtor'",
                  '_U': 'operator new[]', '_V': 'operator delete[]'}


def simplify_msvc(sym: str) -> str | None:
    """'?Name@Ns2@Ns1@@...' -> 'Ns1::Ns2::Name' (rough). None if too complex."""
    if not sym.startswith('?'):
        return sym
    s = sym[1:]
    special = None
    if s.startswith('?') and not s.startswith('?$'):
        code = s[1:3] if s[1:2] == '_' else s[1:2]
        if code not in _SPECIAL_NAMES:
            return None
        special, s = code, s[1 + len(code):]
    parts: list[str] = []
    i = 0
    while i < len(s) and s[i] != '@':
        c = s[i]
        if c.isdigit():
            k = int(c)
            if k >= len(parts):
                return None
            parts.append(parts[k])
            i += 1
            continue
        if s.startswith('?A0x', i):
            j = s.find('@', i)
            parts.append("`anonymous namespace'")
            i = j + 1
            continue
        if c == '?':
            return None          # templates, local scopes, ...: leave to llvm-undname
        j = s.find('@', i)
        if j < 0:
            return None
        parts.append(s[i:j])
        i = j + 1
    if not parts:
        return None
    q = list(reversed(parts))
    if special == '0':
        q.append(q[-1])
    elif special == '1':
        q.append('~' + q[-1])
    elif special:
        q.append(_SPECIAL_NAMES[special])
    return '::'.join(q)


def _strip_params(s: str) -> str:
    """Drop the trailing top-level '(...)' parameter list (+ cv qualifiers)."""
    t = re.sub(r'(\s+(const|volatile|__ptr64|&|&&))+$', '', s)
    if not t.endswith(')'):
        return s
    depth = 0
    for k in range(len(t) - 1, -1, -1):
        if t[k] == ')':
            depth += 1
        elif t[k] == '(':
            depth -= 1
            if depth == 0:
                head = t[:k].rstrip()
                return head if head and not head.endswith('operator') else s
    return s


class Demangler:
    def __init__(self, use_undname: bool, keep_params: bool):
        self.keep_params = keep_params
        self.cache: dict[str, str] = {}
        self.undname = None
        if use_undname:
            root = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
            cands = [shutil.which('llvm-undname')] + sorted(
                glob.glob(os.path.join(root, 'toolchain', 'llvm-*', 'bin', 'llvm-undname.exe')),
                reverse=True)
            self.undname = next((c for c in cands if c and os.path.isfile(c)), None)

    def prime(self, names) -> None:
        todo = sorted({n for n in names if n.startswith('?') and n not in self.cache})
        if not todo or not self.undname:
            return
        try:
            out = subprocess.run(
                [self.undname, '--no-calling-convention', '--no-return-type',
                 '--no-access-specifier', '--no-member-type', '--no-variable-type'],
                input='\n'.join(todo) + '\n', capture_output=True, text=True, timeout=120,
                errors='replace').stdout
        except (OSError, subprocess.SubprocessError) as e:
            warn(f'llvm-undname failed ({e}); using the built-in simplifier')
            self.undname = None
            return
        lines = [ln.rstrip('\r') for ln in out.split('\n')]
        pos = {}
        for k, ln in enumerate(lines):
            pos.setdefault(ln, k)
        for n in todo:
            k = pos.get(n)
            if k is not None and k + 1 < len(lines):
                r = lines[k + 1].strip()
                if r and not r.startswith('error:'):
                    self.cache[n] = r if self.keep_params else _strip_params(r)

    def __call__(self, name: str) -> str:
        r = self.cache.get(name)
        if r is None:
            r = simplify_msvc(name) or name if name.startswith('?') else name
            self.cache[name] = r
        return r


# =============================================================================
# Symbolization
# =============================================================================

class Func:
    __slots__ = ('name', 'raw', 'module', 'category', 'guest', 'kind', 'cls', 'aliases', 'obj')

    def __init__(self, name, raw, module, category, guest=None, kind='', cls='busy', aliases=0,
                 obj=''):
        self.name, self.raw, self.module, self.category = name, raw, module, category
        self.guest, self.kind, self.cls, self.aliases, self.obj = guest, kind, cls, aliases, obj


def _gpu_native_objects() -> set[str]:
    d = os.path.join(SCRIPT_DIR, '..', '..', 'rexlego', 'src', 'gpu_native')
    return {os.path.basename(p).lower() + '.obj' for p in glob.glob(os.path.join(d, '*.cpp'))}


class Symbolizer:
    def __init__(self, prof: Profile, map_path: str | None, args):
        self.prof = prof
        self.args = args
        self.mods = sorted(prof.modules)
        self.bases = [m[0] for m in self.mods]
        self.funcs: list[Func] = []
        self.index: dict = {}
        self.resolvers: dict[int, object] = {}
        self.demangle = Demangler(not args.no_undname, args.keep_params)
        self.gpu_objs = _gpu_native_objects()
        self.sys32 = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32')
        self.leaf_rules = [(re.compile(m, re.I), re.compile(s), c) for m, s, c in LEAF_CLASS_RULES]
        self.cat_rules = [(c, sc, re.compile(m, re.I) if m and not m.startswith('<') else m,
                           re.compile(s) if s else None,
                           re.compile(o, re.I) if o and not o.startswith('<') else o)
                          for c, sc, m, s, o in CATEGORY_RULES]
        self.sys_extra = re.compile(SYSTEM_EXTRA, re.I)
        self.search_dirs = [args.bin_dir or os.path.dirname(os.path.abspath(prof.path))]
        self.search_dirs += list(args.search or []) + [self.sys32]
        self._driverstore_index = None
        self.main_idx = None
        self.main_map = None
        self.maps: dict[str, MapTable] = {}
        self.map_info: dict[str, dict] = {}
        if map_path:
            t0 = time.perf_counter()
            self.main_map = MapTable(map_path)
            self.map_info[map_path] = {'symbols': len(self.main_map.rvas),
                                       'lines': self.main_map.symbol_lines,
                                       'image': self.main_map.image_name,
                                       'parse_s': round(time.perf_counter() - t0, 3)}
            stem = self.main_map.image_name.lower()
            for k, m in enumerate(self.mods):
                if os.path.splitext(m[2])[0].lower() == stem:
                    self.main_idx = k
            if self.main_idx is None:
                exe = [k for k, m in enumerate(self.mods) if m[2].lower().endswith('.exe')]
                if prof.modules:
                    first = self.bases.index(prof.modules[0][0])
                    self.main_idx = exe[0] if len(exe) == 1 else first
                warn(f'no module named like map image "{self.main_map.image_name}"; using '
                     f'{self.mods[self.main_idx][2] if self.main_idx is not None else "nothing"}')
        for spec in args.extra_map or []:
            mod, _, p = spec.partition('=')
            self.maps[mod.lower()] = MapTable(p)
        self.unknown = self._func(('?',), lambda: Func('[unknown]', '', '?', 'unknown'))
        self.empty = self._func(('-',), lambda: Func('[no frames]', '', '?', 'unknown'))

    # -- helpers --
    def _func(self, key, make) -> int:
        fid = self.index.get(key)
        if fid is None:
            fid = len(self.funcs)
            self.funcs.append(make())
            self.index[key] = fid
        return fid

    def _locate(self, name: str, size: int):
        for d in self.search_dirs:
            p = os.path.join(d, name)
            if os.path.isfile(p):
                return p
        if self.args.driverstore:
            if self._driverstore_index is None:
                self._driverstore_index = collections.defaultdict(list)
                wanted = {m[2].lower() for m in self.mods}
                root = os.path.join(self.sys32, 'DriverStore', 'FileRepository')
                for dp, _dn, fn in os.walk(root):
                    for f in fn:
                        if f.lower() in wanted:
                            self._driverstore_index[f.lower()].append(os.path.join(dp, f))
            cands = self._driverstore_index.get(name.lower(), [])
            best = None
            for p in sorted(cands, key=lambda q: -os.path.getmtime(q)):
                try:
                    with open(p, 'rb') as f:
                        head = f.read(4096)
                    (pe,) = struct.unpack_from('<I', head, 0x3C)
                    (soi,) = struct.unpack_from('<I', head, pe + 24 + 56)
                except (OSError, struct.error):
                    continue
                if soi == size:
                    return p
                best = best or p
            return best
        return None

    def _resolver(self, k: int):
        r = self.resolvers.get(k, False)
        if r is not False:
            return r
        base, size, name = self.mods[k]
        r = None
        if k == self.main_idx and self.main_map:
            r = self.main_map
        elif name.lower() in self.maps:
            r = self.maps[name.lower()]
        else:
            p = self._locate(name, size)
            if p:
                try:
                    r = PEImage(p)
                    if r.size_of_image != size:
                        warn(f'{name}: {p} SizeOfImage {r.size_of_image:#x} != loaded {size:#x}; '
                             f'export names may be wrong (file changed since capture?)')
                except (OSError, ValueError, struct.error) as e:
                    warn(f'{name}: cannot read {p}: {e}')
                    r = None
        self.resolvers[k] = r
        return r

    def _is_system(self, name: str) -> bool:
        return bool(self.sys_extra.fullmatch(name)) or os.path.isfile(os.path.join(self.sys32, name))

    def categorize(self, module: str, is_main: bool, raw: str, obj: str, kind: str) -> str:
        for cat, scope, mre, sre, ore in self.cat_rules:
            if (scope == 'main') != is_main:
                continue
            if cat == 'guest' and kind == 'hook':
                continue
            if mre == '<SYSTEM32>':
                if not self._is_system(module):
                    continue
            elif mre is not None and not mre.fullmatch(module):
                continue
            if sre is not None and not sre.fullmatch(raw):
                continue
            if ore == '<GPU_NATIVE_OBJECTS>':
                o = obj.lower()
                if not (('gpu_native' in o) or (':' not in o and o in self.gpu_objs)):
                    continue
            elif ore is not None and not ore.fullmatch(obj):
                continue
            return cat
        return 'other'

    def leaf_class(self, module: str, raw: str) -> str:
        for mre, sre, cls in self.leaf_rules:
            if mre.fullmatch(module) and sre.fullmatch(raw):
                return cls
        return 'busy'

    def resolve(self, addr: int) -> int:
        k = bisect.bisect_right(self.bases, addr) - 1
        if k < 0 or addr >= self.bases[k] + self.mods[k][1]:
            return self.unknown
        base, _size, mod = self.mods[k]
        r = self._resolver(k)
        rva = addr - base
        if isinstance(r, MapTable):
            i = r.lookup(rva)
            if i is None:
                return self._func((k, None), lambda: Func(f'{mod}!?', '', mod, 'unknown'))
            return self._func((k, i), lambda: self._map_func(k, r, i))
        if isinstance(r, PEImage):
            hit = r.lookup(rva)
            if hit is None:
                return self._func((k, None), lambda: self._mod_func(k, f'{mod}!?', ''))
            start, disp, raw = hit
            return self._func((k, start), lambda: self._mod_func(k, f'{mod}!{disp}', raw))
        return self._func((k, None), lambda: self._mod_func(k, f'{mod}!?', ''))

    def _mod_func(self, k: int, name: str, raw: str) -> Func:
        mod = self.mods[k][2]
        cat = self.categorize(mod, k == self.main_idx, raw, '', '')
        return Func(name, raw, mod, cat, cls=self.leaf_class(mod, raw))

    def _map_func(self, k: int, table: MapTable, i: int) -> Func:
        mod = self.mods[k][2]
        name, obj, aliases, kind, guest = table.entries[i]
        is_main = k == self.main_idx
        raw = name
        cat = self.categorize(mod, is_main, raw, obj, kind)
        if cat == 'other' and not is_main:
            cat = 'rexruntime' if mod.lower().startswith('rexruntime') else cat
        return Func(None, raw, mod, cat, guest, kind, self.leaf_class(mod, raw), aliases, obj)

    def finish_names(self) -> None:
        """Demangle (batch llvm-undname) and build display names for map symbols."""
        self.demangle.prime(f.raw for f in self.funcs if f.name is None)
        for f in self.funcs:
            if f.name is not None:
                continue
            n = self.demangle(f.raw)
            if f.guest is not None and GUEST_NAME_RE.fullmatch(f.raw):
                tag = {'hook': f'hook of guest 0x{f.guest:08X}',
                       'hooked original': f'guest 0x{f.guest:08X}, hooked original'}.get(
                           f.kind, f'guest 0x{f.guest:08X}')
                n = f'{n} [{tag}]'
            if f.aliases:
                n += f' {{+{f.aliases} alias{"es" if f.aliases > 1 else ""}}}'
            mi = self.main_idx
            if mi is None or f.module != self.mods[mi][2]:
                n = f'{f.module}!{n}'
            f.name = n.replace(';', ':')


# =============================================================================
# Aggregation
# =============================================================================

class Analysis:
    """Profile + symbols -> aggregated (tid, function-stack) counts."""

    def __init__(self, prof_path: str, map_path: str | None, args, duration_s=None, meta=None):
        t0 = time.perf_counter()
        self.prof = Profile(prof_path)
        t1 = time.perf_counter()
        if map_path is None:
            map_path = _default_map(self.prof)
        self.map_path = map_path
        self.sym = Symbolizer(self.prof, map_path, args)
        t2 = time.perf_counter()
        fstack_ids: dict[tuple, int] = {}
        self.fstacks: list[tuple] = []
        sid2f = []
        cache: dict[int, int] = {}
        resolve = self.sym.resolve
        structs: dict[int, struct.Struct] = {}
        for key in self.prof.stacks:
            n = len(key) >> 3
            st = structs.get(n)
            if st is None:
                st = structs[n] = struct.Struct(f'<{n}Q')
            addrs = st.unpack(key)
            fs = []
            for d, a in enumerate(addrs):
                if d:
                    a -= 1      # return address: attribute the call to its caller
                f = cache.get(a)
                if f is None:
                    f = cache[a] = resolve(a)
                fs.append(f)
            fsk = tuple(fs) if fs else (self.sym.empty,)
            fid = fstack_ids.get(fsk)
            if fid is None:
                fid = fstack_ids[fsk] = len(self.fstacks)
                self.fstacks.append(fsk)
            sid2f.append(fid)
        self.agg: dict[tuple[int, int], int] = collections.defaultdict(int)
        for k, cnt in self.prof.counts.items():
            self.agg[(k & 0xFFFFFFFF, sid2f[k >> 32])] += cnt
        self.sym.finish_names()
        t3 = time.perf_counter()
        self.timing = {'read_s': round(t1 - t0, 3), 'map_s': round(t2 - t1, 3),
                       'symbolize_s': round(t3 - t2, 3), 'unique_stacks': len(self.prof.stacks),
                       'unique_addresses': len(cache), 'functions': len(self.sym.funcs)}
        self.duration = _resolve_duration(self.prof, duration_s, meta, args.trigger_latency)

    def funcs(self):
        return self.sym.funcs


def _default_map(prof: Profile):
    d = os.path.dirname(os.path.abspath(prof.path))
    names = []
    if prof.modules:
        names.append(os.path.splitext(prof.modules[0][2])[0] + '.map')
    names.append('legodimensions.map')
    for n in names:
        p = os.path.join(d, n)
        if os.path.isfile(p):
            return p
    warn('no map given or found next to the profile; exe frames are attributed by .pdata only')
    return None


def _parse_time(v):
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            pass
        d = _dt.datetime.fromisoformat(v.strip().replace('Z', '+00:00'))
        if d.tzinfo is None:
            d = d.astimezone()
        return d.timestamp()
    raise ValueError(f'bad time value {v!r}')


def _meta_duration(path: str, latency: float):
    with open(path, 'r', encoding='utf-8-sig') as f:
        meta = json.load(f)
    scopes = [meta] + [v for v in meta.values() if isinstance(v, dict)]
    for sc in scopes:
        if isinstance(sc.get('duration_s'), (int, float)) and sc['duration_s'] > 0:
            return float(sc['duration_s']), f'meta {os.path.basename(path)}: duration_s'
    for sc in scopes:
        for a, b in (('profile_trigger_start', 'profile_trigger_end'), ('trigger_start', 'trigger_end')):
            if a in sc and b in sc:
                d = _parse_time(sc[b]) - _parse_time(sc[a])
                return max(d - latency, 1e-6), (f'meta {os.path.basename(path)}: {b}-{a} '
                                                f'({d:.3f} s) - {latency:.3f} s start latency')
    raise SystemExit(f'{path}: no duration_s / profile_trigger_start+end / trigger_start+end')


def _resolve_duration(prof: Profile, duration_s, meta, latency) -> dict:
    t = prof.trailer or {}
    rounds = t.get('rounds')
    est_rounds = max(prof.tid_counts.values()) if prof.tid_counts else 0
    out = {'rounds': rounds, 'rounds_estimated': est_rounds}
    if t.get('qpc_frequency') and t.get('qpc_end', 0) > t.get('qpc_start', 0):
        out.update(seconds=(t['qpc_end'] - t['qpc_start']) / t['qpc_frequency'], source='trailer')
    elif duration_s:
        out.update(seconds=float(duration_s), source='--duration')
    elif meta:
        s, src = _meta_duration(meta, latency)
        out.update(seconds=s, source=src)
    else:
        out.update(seconds=None, source='estimate')
        warn(f'{os.path.basename(prof.path)}: no recording duration (no LSPX trailer, --duration-s '
             f'or --meta): rates are per 1000 sampler rounds, rounds estimated as the max '
             f'per-thread sample count ({est_rounds}; nominal rate ~1 kHz, lower in practice)')
    r = rounds if rounds is not None else est_rounds
    if out['seconds'] and r:
        out['rounds_per_s'] = round(r / out['seconds'], 1)
        if out['rounds_per_s'] < 250:
            warn(f'{os.path.basename(prof.path)}: low sampling rate ({out["rounds_per_s"]:.0f} '
                 f'rounds/s, nominal ~1000): the machine was probably CPU-saturated (each '
                 f'SuspendThread/GetThreadContext waits until the target thread is scheduled); '
                 f'attribution is still usable but noisy')
    return out


# =============================================================================
# Reports
# =============================================================================

def _tid_filter(args):
    return {int(t, 0) for t in args.thread} if args.thread else None


def _fold_map(an: Analysis, fold_guest: bool):
    funcs = an.funcs()
    if not fold_guest:
        return None
    gid = len(funcs)
    return [gid if f.category == 'guest' else i for i, f in enumerate(funcs)], gid


def _apply_fold(fs, fmap):
    if fmap is None:
        return fs
    m = fmap[0]
    out = []
    for f in fs:
        g = m[f]
        if not out or out[-1] != g or g != fmap[1]:
            out.append(g)
    return tuple(out)


def _fname(an, f, fmap):
    if fmap is not None and f == fmap[1]:
        return 'guest [folded]'
    return an.funcs()[f].name


def _finfo(an, f, fmap, n, total, rate):
    if fmap is not None and f == fmap[1]:
        d = {'name': 'guest [folded]', 'category': 'guest', 'module': '', 'guest_addr': None,
             'kind': 'folded'}
    else:
        fn = an.funcs()[f]
        d = {'name': fn.name, 'category': fn.category, 'module': fn.module,
             'guest_addr': f'0x{fn.guest:08X}' if fn.guest is not None else None,
             'kind': fn.kind or None}
    d['samples'] = n
    d['pct'] = round(100.0 * n / total, 2) if total else 0.0
    if rate:
        d['rate'] = round(n / rate, 3)
    return d


def summarize(an: Analysis, args) -> dict:
    funcs = an.funcs()
    tids = _tid_filter(args)
    fmap = _fold_map(an, args.fold_guest)
    names = an.prof.thread_names
    top = args.top
    per_thread = collections.defaultdict(lambda: {'samples': 0, 'busy': 0, 'wait': 0, 'io': 0,
                                                  'self': collections.Counter(),
                                                  'incl': collections.Counter(),
                                                  'role': collections.Counter()})
    self_c, incl_c = collections.Counter(), collections.Counter()
    mod_self, mod_incl = collections.Counter(), collections.Counter()
    cat_busy = collections.Counter()
    totals = collections.Counter()
    focus_re = re.compile(args.focus) if args.focus else None
    foc = {'self': 0, 'incl': 0, 'callers': collections.Counter(), 'callees': collections.Counter(),
           'matched': set()}
    counted = 0
    for (tid, fsid), n in an.agg.items():
        if tids is not None and tid not in tids:
            continue
        fs = an.fstacks[fsid]
        leaf = funcs[fs[0]]
        cls = leaf.cls
        th = per_thread[tid]
        th['samples'] += n
        th[cls] += n
        totals[cls] += n
        role = next((f for f in fs if funcs[f].category in ('guest', 'rexlego', 'native-gpu',
                                                            'rexruntime')), None)
        if role is not None:
            th['role'][role] += n
        if cls == 'busy':
            cat_busy[leaf.category] += n
        if cls != 'busy' and not args.include_waits:
            continue
        counted += n
        ffs = _apply_fold(fs, fmap)
        self_c[ffs[0]] += n
        th['self'][ffs[0]] += n
        uniq = set(ffs)
        for f in uniq:
            incl_c[f] += n
            th['incl'][f] += n
        mod_self[leaf.module] += n
        for m in {funcs[f].module for f in fs}:
            mod_incl[m] += n
        if focus_re is not None:
            hit = [d for d, f in enumerate(ffs) if _focus_match(an, f, fmap, focus_re)]
            if hit:
                foc['incl'] += n
                if hit[0] == 0:
                    foc['self'] += n
                callers = {ffs[d + 1] for d in hit if d + 1 < len(ffs)}
                callees = {ffs[d - 1] for d in hit if d > 0}
                for f in callers:
                    foc['callers'][f] += n
                for f in callees:
                    foc['callees'][f] += n
                foc['matched'].update(ffs[d] for d in hit)
    dur = an.duration
    rate = dur['seconds']
    rate_unit = '/s' if rate else '/1k rounds'
    if not rate:
        r = dur['rounds'] or dur['rounds_estimated']
        rate = r / 1000.0 if r else None
    threads = []
    for tid, th in sorted(per_thread.items(), key=lambda kv: -kv[1]['samples']):
        busy = th['busy']
        role = th['role'].most_common(1)
        threads.append({
            'tid': tid, 'name': names.get(tid, ''), 'samples': th['samples'], 'busy': busy,
            'waiting': th['wait'], 'io': th['io'],
            'pct_running': round(100.0 * busy / th['samples'], 1) if th['samples'] else 0.0,
            'top_self': [_finfo(an, f, fmap, c, busy if not args.include_waits else th['samples'],
                                None) for f, c in th['self'].most_common(top)],
            'top_inclusive': [_finfo(an, f, fmap, c, busy if not args.include_waits
                                     else th['samples'], None)
                              for f, c in th['incl'].most_common(top)],
            'role': _fname(an, role[0][0], None) if role else '',
        })
    rep = {
        'tool': 'analyze_profile.py', 'schema': 1, 'mode': 'summary',
        'profile': an.prof.path, 'map': an.map_path, 'samples': an.prof.sample_count,
        'modules': len(an.prof.modules), 'threads_seen': len(an.prof.tid_counts),
        'trailer': _trailer_json(an.prof), 'duration': dur, 'rate_unit': rate_unit,
        'timer_observer_effect': an.prof.observer_effect(),
        'counting': 'all samples' if args.include_waits else 'busy samples',
        'counted_samples': counted, 'thread_filter': sorted(tids) if tids else None,
        'fold_guest': bool(args.fold_guest),
        'totals': {'busy': totals['busy'], 'waiting': totals['wait'], 'io': totals['io']},
        'categories_busy': {c: cat_busy.get(c, 0) for c in CATEGORY_ORDER},
        'threads': threads,
        'top_self': [_finfo(an, f, fmap, c, counted, rate) for f, c in self_c.most_common(top)],
        'top_inclusive': [_finfo(an, f, fmap, c, counted, rate) for f, c in incl_c.most_common(top)],
        'timing': an.timing, 'map_info': an.sym.map_info,
    }
    if args.by == 'module':
        rep['modules_self'] = [{'module': m, 'samples': c,
                                'pct': round(100.0 * c / counted, 2) if counted else 0.0}
                               for m, c in mod_self.most_common(top)]
        rep['modules_inclusive'] = [{'module': m, 'samples': c,
                                     'pct': round(100.0 * c / counted, 2) if counted else 0.0}
                                    for m, c in mod_incl.most_common(top)]
    if focus_re is not None:
        base = foc['incl'] or 1
        rep['focus'] = {
            'regex': args.focus, 'inclusive': foc['incl'], 'self': foc['self'],
            'matched': sorted(_fname(an, f, fmap) for f in foc['matched']),
            'callers': [dict(_finfo(an, f, fmap, c, base, None)) for f, c in
                        foc['callers'].most_common(top)],
            'callees': [dict(_finfo(an, f, fmap, c, base, None)) for f, c in
                        foc['callees'].most_common(top)],
        }
    rep['warnings'] = list(_warnings)
    return rep


def _focus_match(an, f, fmap, rx):
    if fmap is not None and f == fmap[1]:
        return bool(rx.search('guest [folded]'))
    fn = an.funcs()[f]
    return bool(rx.search(fn.name) or (fn.raw and rx.search(fn.raw)))


def _trailer_json(prof: Profile):
    t = prof.trailer
    if not t:
        return None
    d = {k: v for k, v in t.items() if k != 'thread_names'}
    d['thread_names'] = {str(k): v for k, v in t.get('thread_names', {}).items()}
    return d


def folded(an: Analysis, args) -> list[tuple[str, int]]:
    funcs = an.funcs()
    tids = _tid_filter(args)
    fmap = _fold_map(an, args.fold_guest)
    names = an.prof.thread_names
    out = collections.Counter()
    for (tid, fsid), n in an.agg.items():
        if tids is not None and tid not in tids:
            continue
        fs = an.fstacks[fsid]
        if funcs[fs[0]].cls != 'busy' and not args.include_waits:
            continue
        frames = [_fname(an, f, fmap) for f in reversed(_apply_fold(fs, fmap))]
        if args.folded_thread:
            frames.insert(0, f'thread {tid}' + (f' {names[tid]}' if names.get(tid) else ''))
        out[';'.join(fr.replace(';', ':') for fr in frames)] += n
    return sorted(out.items(), key=lambda kv: (-kv[1], kv[0]))


def diff(args) -> dict:
    a_bin, a_map, b_bin, b_map = args.diff
    a = Analysis(a_bin, a_map, args, args.duration_a, args.meta_a)
    b = Analysis(b_bin, b_map, args, args.duration_b, args.meta_b)
    if a.duration['seconds'] and b.duration['seconds']:
        unit, da, db = '/s', a.duration['seconds'], b.duration['seconds']
    else:
        unit = '/1k rounds'
        da = (a.duration['rounds'] or a.duration['rounds_estimated']) / 1000.0 or 1.0
        db = (b.duration['rounds'] or b.duration['rounds_estimated']) / 1000.0 or 1.0
        warn('no duration for one or both profiles (no LSPX trailer, --duration-a/b or '
             '--meta-a/b): normalising per 1000 sampler rounds, rounds estimated as the max '
             'per-thread sample count (nominal ~1 kHz); deltas are approximate')
    tids = _tid_filter(args)

    def collect(an):
        funcs = an.funcs()
        fmap = _fold_map(an, args.fold_guest)
        s, inc, cats = collections.Counter(), collections.Counter(), collections.Counter()
        for (tid, fsid), n in an.agg.items():
            if tids is not None and tid not in tids:
                continue
            fs = an.fstacks[fsid]
            leaf = funcs[fs[0]]
            if leaf.cls != 'busy' and not args.include_waits:
                cats['[' + leaf.cls + ']'] += n
                continue
            cats[leaf.category] += n
            ffs = _apply_fold(fs, fmap)
            s[_fname(an, ffs[0], fmap)] += n
            for nm in {_fname(an, f, fmap) for f in ffs}:
                inc[nm] += n
        return s, inc, cats

    sa, ia, ca = collect(a)
    sb, ib, cb = collect(b)

    def rows(ca_, cb_):
        out = []
        for k in set(ca_) | set(cb_):
            ra, rb = ca_.get(k, 0) / da, cb_.get(k, 0) / db
            out.append({'name': k, 'a': round(ra, 3), 'b': round(rb, 3), 'delta': round(rb - ra, 3),
                        'delta_pct': round(100.0 * (rb - ra) / ra, 1) if ra else None,
                        'a_samples': ca_.get(k, 0), 'b_samples': cb_.get(k, 0)})
        out.sort(key=lambda r: (-abs(r['delta']), -max(r['a'], r['b']), r['name']))
        return out

    return {
        'tool': 'analyze_profile.py', 'schema': 1, 'mode': 'diff', 'unit': unit,
        'a': {'profile': a_bin, 'map': a.map_path, 'samples': a.prof.sample_count,
              'duration': a.duration, 'timer_observer_effect': a.prof.observer_effect()},
        'b': {'profile': b_bin, 'map': b.map_path, 'samples': b.prof.sample_count,
              'duration': b.duration, 'timer_observer_effect': b.prof.observer_effect()},
        'counting': 'all samples' if args.include_waits else 'busy samples',
        'categories': rows(ca, cb),
        'self': rows(sa, sb)[:args.top], 'inclusive': rows(ia, ib)[:args.top],
        'max_abs_delta_self': max((abs(r['delta']) for r in rows(sa, sb)), default=0.0),
        'warnings': list(_warnings),
    }


# =============================================================================
# Text rendering
# =============================================================================

def _table(rows, headers, right=()):
    w = [len(h) for h in headers]
    for r in rows:
        for k, c in enumerate(r):
            w[k] = max(w[k], len(str(c)))
    fmt = lambda r: '  '.join(str(c).rjust(w[k]) if k in right else str(c).ljust(w[k])
                              for k, c in enumerate(r)).rstrip()
    return '\n'.join([fmt(headers), fmt(['-' * x for x in w])] + [fmt(r) for r in rows])


def _short(s, n=110):
    return s if len(s) <= n else s[:n - 3] + '...'


def _header_lines(rep_like, prof_label='profile') -> list[str]:
    out = []
    eff = rep_like['timer_observer_effect']
    if eff is True:
        out.append('WARNING: ' + OBSERVER_WARNING)
    elif eff == 'unknown':
        out.append('WARNING: unknown sampler timer_mode; ' + OBSERVER_WARNING)
    return out


def render_summary(rep: dict) -> str:
    L = []
    d = rep['duration']
    dur = f"{d['seconds']:.3f} s ({d['source']})" if d['seconds'] else 'unknown (estimate)'
    L.append(f"profile : {rep['profile']}")
    L.append(f"map     : {rep['map']}")
    L.append(f"samples : {rep['samples']}  threads: {rep['threads_seen']}  modules: {rep['modules']}"
             f"  duration: {dur}  rounds: {d['rounds'] if d['rounds'] is not None else '~%d (est)' % d['rounds_estimated']}")
    L.append(f"counting: {rep['counting']} ({rep['counted_samples']})"
             + (f"  threads: {rep['thread_filter']}" if rep['thread_filter'] else '')
             + ('  [guest folded]' if rep['fold_guest'] else ''))
    L += _header_lines(rep)
    for w in rep['warnings']:
        if OBSERVER_WARNING not in w:
            L.append('warning: ' + w)
    tot = rep['totals']
    allc = sum(tot.values()) or 1
    L.append('')
    L.append(f"busy {tot['busy']} ({100.0 * tot['busy'] / allc:.1f}%)  waiting {tot['waiting']} "
             f"({100.0 * tot['waiting'] / allc:.1f}%)  io {tot['io']} ({100.0 * tot['io'] / allc:.1f}%)")
    busy = tot['busy'] or 1
    L.append('busy samples by category (leaf): ' + '  '.join(
        f"{c} {n} ({100.0 * n / busy:.1f}%)" for c, n in rep['categories_busy'].items() if n))
    L.append('')
    L.append('== threads ==')
    rows = []
    for t in rep['threads']:
        if t['busy']:
            desc = '; '.join(f"{_short(x['name'], 50)} {x['pct']:.0f}%" for x in t['top_self'][:3])
        else:
            desc = f"(waiting) {_short(t['role'], 70)}" if t['role'] else '(waiting)'
        rows.append([t['tid'], _short(t['name'], 24), t['samples'], f"{t['pct_running']:.1f}",
                     t['busy'], t['waiting'], t['io'], desc])
    L.append(_table(rows, ['tid', 'name', 'samples', 'run%', 'busy', 'wait', 'io',
                           'top busy functions / role'], right=(0, 2, 3, 4, 5, 6)))
    unit = rep['rate_unit']
    for key, title in (('top_self', 'self'), ('top_inclusive', 'inclusive')):
        L.append('')
        L.append(f'== top {len(rep[key])} by {title} ({rep["counting"]}) ==')
        rows = [[x['samples'], f"{x['pct']:.2f}", f"{x.get('rate', 0):.1f}", x['category'],
                 _short(x['name'])] for x in rep[key]]
        L.append(_table(rows, ['samples', '%', unit, 'category', 'function'], right=(0, 1, 2)))
    if 'modules_self' in rep:
        for key, title in (('modules_self', 'self'), ('modules_inclusive', 'inclusive')):
            L.append('')
            L.append(f'== modules by {title} ==')
            L.append(_table([[x['samples'], f"{x['pct']:.2f}", x['module']] for x in rep[key]],
                            ['samples', '%', 'module'], right=(0, 1)))
    if 'focus' in rep:
        fo = rep['focus']
        L.append('')
        L.append(f"== focus /{fo['regex']}/: inclusive {fo['inclusive']}, self {fo['self']} ==")
        L.append('matched: ' + ', '.join(_short(m, 80) for m in fo['matched'][:10]))
        for key in ('callers', 'callees'):
            L.append(f'-- {key} --')
            L.append(_table([[x['samples'], f"{x['pct']:.1f}", _short(x['name'])] for x in fo[key]],
                            ['samples', '% of focus', 'function'], right=(0, 1)))
    tm = rep['timing']
    L.append('')
    L.append(f"(read {tm['read_s']} s, map {tm['map_s']} s, symbolize {tm['symbolize_s']} s; "
             f"{tm['unique_stacks']} unique stacks, {tm['unique_addresses']} addresses, "
             f"{tm['functions']} functions)")
    return '\n'.join(L) + '\n'


def render_diff(rep: dict) -> str:
    L = [f"A: {rep['a']['profile']} ({rep['a']['samples']} samples, duration "
         f"{rep['a']['duration']['seconds'] or 'n/a'} [{rep['a']['duration']['source']}])",
         f"B: {rep['b']['profile']} ({rep['b']['samples']} samples, duration "
         f"{rep['b']['duration']['seconds'] or 'n/a'} [{rep['b']['duration']['source']}])",
         f"unit: samples {rep['unit']}, {rep['counting']}"]
    for side in ('a', 'b'):
        if rep[side]['timer_observer_effect'] is not False:
            L.append(f'WARNING ({side.upper()}): ' + OBSERVER_WARNING)
    for w in rep['warnings']:
        L.append('warning: ' + w)

    def fmt(rows):
        return _table([[f"{r['a']:.1f}", f"{r['b']:.1f}", f"{r['delta']:+.1f}",
                        f"{r['delta_pct']:+.1f}%" if r['delta_pct'] is not None else 'new',
                        _short(r['name'])] for r in rows],
                      ['A', 'B', 'delta', 'delta%', 'name'], right=(0, 1, 2, 3))
    L += ['', '== categories ==', fmt(rep['categories']), '', '== self ==', fmt(rep['self']),
          '', '== inclusive ==', fmt(rep['inclusive'])]
    return '\n'.join(L) + '\n'


# =============================================================================
# main
# =============================================================================

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('profile', nargs='?', help='profile-<tick>.bin')
    ap.add_argument('map', nargs='?', help='lld-link /MAP file of the exe (default: <exe>.map or '
                    'legodimensions.map next to the profile)')
    ap.add_argument('--map', dest='extra_map', action='append', metavar='MODULE=PATH',
                    help='extra lld map for another module (repeatable)')
    ap.add_argument('--by', choices=('function', 'module'), default='function')
    ap.add_argument('--thread', action='append', metavar='TID', help='only these threads (repeatable)')
    ap.add_argument('--focus', metavar='REGEX', help='callers/callees of matching functions')
    ap.add_argument('--folded', action='store_true', help='folded stacks (root->leaf) for flamegraphs')
    ap.add_argument('--folded-thread', action='store_true', help='prefix folded stacks with the thread')
    ap.add_argument('--fold-guest', action='store_true', help='fold all guest functions into "guest"')
    ap.add_argument('--include-waits', action='store_true', help='count waiting/io samples too')
    ap.add_argument('--diff', nargs=4, metavar=('A.bin', 'A.map', 'B.bin', 'B.map'))
    ap.add_argument('--duration-s', type=float, help='recording length if the profile has no trailer')
    ap.add_argument('--meta', help='harness run-metadata JSON (duration_s or trigger start/end)')
    ap.add_argument('--duration-a', type=float)
    ap.add_argument('--duration-b', type=float)
    ap.add_argument('--meta-a')
    ap.add_argument('--meta-b')
    ap.add_argument('--trigger-latency', type=float, default=TRIGGER_LATENCY_S,
                    help='seconds subtracted from a meta trigger window (default %(default)s)')
    ap.add_argument('--top', type=int, default=25)
    ap.add_argument('--json', action='store_true')
    ap.add_argument('-o', '--output', help='write the report here instead of stdout')
    ap.add_argument('--bin-dir', help='where the exe/DLLs live (default: the profile directory)')
    ap.add_argument('--search', action='append', metavar='DIR', help='extra DLL search dir')
    ap.add_argument('--driverstore', action='store_true',
                    help='also search System32\\DriverStore\\FileRepository (GPU user-mode drivers)')
    ap.add_argument('--no-undname', action='store_true', help='do not use llvm-undname')
    ap.add_argument('--keep-params', action='store_true', help='keep C++ parameter lists')
    args = ap.parse_args(argv)

    if args.diff:
        rep = diff(args)
        text = json.dumps(rep, indent=1) if args.json else render_diff(rep)
    else:
        if not args.profile:
            ap.error('a profile is required (or --diff)')
        an = Analysis(args.profile, args.map, args, args.duration_s, args.meta)
        if args.folded:
            lines = folded(an, args)
            if args.json:
                text = json.dumps({'tool': 'analyze_profile.py', 'schema': 1, 'mode': 'folded',
                                   'timer_observer_effect': an.prof.observer_effect(),
                                   'stacks': [{'stack': s, 'count': c} for s, c in lines],
                                   'warnings': list(_warnings)}, indent=1)
            else:
                text = ''.join(f'{s} {c}\n' for s, c in lines)
                if an.prof.observer_effect() is not False:
                    print('warning: ' + OBSERVER_WARNING, file=sys.stderr)
        else:
            rep = summarize(an, args)
            text = json.dumps(rep, indent=1) if args.json else render_summary(rep)
    if args.output:
        with open(args.output, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text if text.endswith('\n') else text + '\n')
    else:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stdout.write(text if text.endswith('\n') else text + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())

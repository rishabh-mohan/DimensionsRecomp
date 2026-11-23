#!/usr/bin/env python3
"""Heuristic host call stacks from a Windows x64 minidump.

Python 3 stdlib only. Everything is opened READ-ONLY (dump, .map, PE files in the run dir).
Usage: python dumpstacks.py [dump] [out] [tid,tid,...]
Method: Rip, then scan 8-byte stack slots from Rsp upward (cap 96 KB); keep values inside a
loaded module's code. Candidates in modules whose code bytes are known (exe / rex DLLs from
the run dir, or code captured in the dump) must be preceded by a CALL instruction ('V');
otherwise they are kept unverified ('?'). Stale frames are possible: this is heuristic.
"""
import bisect
import mmap
import os
import re
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
RUN = os.path.join(WS, 'build', 'agent3', 'runs', '20261122-045945-bgate-long-native3d')
DUMP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RUN, 'hang-63248.dmp')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'dumpstacks-native3d.txt')
FOCUS = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else [74100, 31544]
RUNDIR = os.path.dirname(os.path.abspath(DUMP))
MAP = os.path.join(RUNDIR, 'legodimensions.map')
SCAN_CAP = 96 * 1024
MAX_HITS = 70

STREAM_NAMES = {0: 'Unused', 3: 'ThreadList', 4: 'ModuleList', 5: 'MemoryList', 6: 'Exception',
                7: 'SystemInfo', 8: 'ThreadExList', 9: 'Memory64List', 10: 'CommentA',
                11: 'CommentW', 12: 'HandleData', 13: 'FunctionTable', 14: 'UnloadedModuleList',
                15: 'MiscInfo', 16: 'MemoryInfoList', 17: 'ThreadInfoList',
                18: 'HandleOperationList', 19: 'Token', 20: 'JavaScriptData',
                21: 'SystemMemoryInfo', 22: 'ProcessVmCounters', 23: 'IptTrace', 24: 'ThreadNames'}

RELEVANT = re.compile(r'^(legodimensions\.exe|rex.*|d3d12.*|d3d12core\.dll|nv.*|dxgi\.dll|dbghelp\.dll|'
                      r'ntdll\.dll|kernelbase\.dll|kernel32\.dll|dxcore\.dll|d3d11\.dll|'
                      r'amd_fidelityfx_dx12\.dll|tracyclient\.dll|ucrtbase\.dll|msvcp140\.dll|'
                      r'vcruntime140.*)$', re.I)
INTEREST = re.compile(r'Native|Pipeline|Pso|PSO|Draw|Lock|Wait|Swap|Present|Shader|Compile|Mutex|'
                      r'Critical|Sleep|Fence|Event|Dump|Hang', re.I)


# ----------------------------------------------------------------------------- dump
class Dump:
    def __init__(self, path):
        self.f = open(path, 'rb')
        self.m = mmap.mmap(self.f.fileno(), 0, access=mmap.ACCESS_READ)
        sig, ver, n, dirrva, _ck, ts, flags = struct.unpack_from('<IIIIIIQ', self.m, 0)
        if sig != 0x504D444D:
            raise SystemExit('not a minidump')
        self.version, self.timestamp, self.flags = ver, ts, flags
        self.streams = [struct.unpack_from('<III', self.m, dirrva + 12 * i) for i in range(n)]
        self.ranges = []  # (start, size, fileoff)
        for st, size, rva in self.streams:
            if st == 5:
                cnt = struct.unpack_from('<I', self.m, rva)[0]
                for i in range(cnt):
                    s, sz, r = struct.unpack_from('<QII', self.m, rva + 4 + 16 * i)
                    self.ranges.append((s, sz, r))
            elif st == 9:
                cnt, base = struct.unpack_from('<QQ', self.m, rva)
                off = base
                for i in range(cnt):
                    s, sz = struct.unpack_from('<QQ', self.m, rva + 16 + 16 * i)
                    self.ranges.append((s, sz, off))
                    off += sz
        self.ranges.sort()
        self.starts = [r[0] for r in self.ranges]

    def stream(self, st):
        for t, size, rva in self.streams:
            if t == st:
                return size, rva
        return None

    def mstr(self, rva):
        ln = struct.unpack_from('<I', self.m, rva)[0]
        return self.m[rva + 4:rva + 4 + ln].decode('utf-16-le', 'replace')

    def read(self, addr, n):
        out = b''
        while n > 0:
            i = bisect.bisect_right(self.starts, addr) - 1
            if i < 0:
                return None
            s, sz, off = self.ranges[i]
            if not (s <= addr < s + sz):
                return None
            take = min(n, s + sz - addr)
            out += self.m[off + addr - s: off + addr - s + take]
            addr += take
            n -= take
        return out

    def captured_bytes(self):
        return sum(r[1] for r in self.ranges)


# ----------------------------------------------------------------------------- PE
class PE:
    """PE32+ image, either from a file on disk (read-only) or from dump memory (headers only)."""

    def __init__(self, data_reader, from_file):
        self.rd = data_reader  # rd(off, n) -> bytes|None ; offsets are file offsets or RVAs
        self.from_file = from_file
        e = struct.unpack('<I', self.rd(0x3C, 4))[0]
        if self.rd(e, 4) != b'PE\0\0':
            raise ValueError('no PE sig')
        _mach, nsec, self.ts, _p, _n, optsz, _ch = struct.unpack('<HHIIIHH', self.rd(e + 4, 20))
        opt = e + 24
        oh = self.rd(opt, optsz)
        if struct.unpack_from('<H', oh, 0)[0] != 0x20B:
            raise ValueError('not PE32+')
        self.image_base = struct.unpack_from('<Q', oh, 24)[0]
        self.size_of_image = struct.unpack_from('<I', oh, 56)[0]
        nd = struct.unpack_from('<I', oh, 108)[0]
        self.dirs = [struct.unpack_from('<II', oh, 112 + 8 * i) for i in range(min(nd, 16))]
        sh = self.rd(opt + optsz, 40 * nsec)
        self.sections = []
        for i in range(nsec):
            name = sh[40 * i:40 * i + 8].rstrip(b'\0').decode('latin1')
            vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', sh, 40 * i + 8)
            chars = struct.unpack_from('<I', sh, 40 * i + 36)[0]
            self.sections.append((va, vsize, rawsize, rawptr, chars, name))
        self._pdata = None
        self._exports = None

    def rva_to_off(self, rva):
        if not self.from_file:
            return rva
        for va, vsize, rawsize, rawptr, _c, _n in self.sections:
            if va <= rva < va + rawsize:
                return rawptr + rva - va
        return None

    def bytes_at(self, rva, n):
        off = self.rva_to_off(rva)
        if off is None:
            return None
        return self.rd(off, n)

    def is_code(self, rva):
        for va, vsize, _rs, _rp, chars, _n in self.sections:
            if va <= rva < va + max(vsize, 1) and (chars & 0x20000020):
                return True
        return False

    def section_name(self, rva):
        for va, vsize, _rs, _rp, _c, name in self.sections:
            if va <= rva < va + vsize:
                return name
        return '?'

    def func_of(self, rva):
        """RUNTIME_FUNCTION containing rva via binary search over .pdata (file only)."""
        if not self.from_file or len(self.dirs) < 4:
            return None
        prva, psz = self.dirs[3]
        if not prva:
            return None
        off = self.rva_to_off(prva)
        if off is None:
            return None
        lo, hi = 0, psz // 12
        while lo < hi:
            mid = (lo + hi) // 2
            b, e, u = struct.unpack('<III', self.rd(off + 12 * mid, 12))
            if rva < b:
                hi = mid
            elif rva >= e:
                lo = mid + 1
            else:
                return b, e, u
        return None

    def frame_size(self, rva):
        """Fixed stack allocation (pushes + allocs) of the function containing rva, from UNWIND_INFO
        (follows chained unwind info). Returns (bytes, uses_frame_pointer) or None."""
        f = self.func_of(rva)
        if not f:
            return None
        total, fp, u = 0, False, f[2]
        for _ in range(8):
            if u & 1:  # unwind data pointing at another RUNTIME_FUNCTION
                b, e, u = struct.unpack('<III', self.bytes_at(u & ~1, 12))
                continue
            hdr = self.bytes_at(u, 4)
            if hdr is None:
                return None
            flags, cnt = hdr[0] >> 3, hdr[2]
            codes = self.bytes_at(u + 4, 2 * cnt + 8) or b''
            i = 0
            while i < cnt:
                op, info = codes[2 * i + 1] & 0xF, codes[2 * i + 1] >> 4
                if op == 0:
                    total += 8; i += 1
                elif op == 1:
                    if info == 0:
                        total += struct.unpack_from('<H', codes, 2 * (i + 1))[0] * 8; i += 2
                    else:
                        total += struct.unpack_from('<I', codes, 2 * (i + 1))[0]; i += 3
                elif op == 2:
                    total += info * 8 + 8; i += 1
                elif op == 3:
                    fp = True; i += 1
                elif op in (4, 8):
                    i += 2
                elif op in (5, 9):
                    i += 3
                else:
                    i += 1
            if flags & 4:
                co = u + 4 + 2 * ((cnt + 1) & ~1)
                b, e, u = struct.unpack('<III', self.bytes_at(co, 12))
                continue
            break
        return total, fp

    def cstr(self, rva):
        off = self.rva_to_off(rva)
        out = bytearray()
        while True:
            c = self.rd(off, 64)
            if not c:
                break
            z = c.find(b'\0')
            if z >= 0:
                out += c[:z]
                break
            out += c
            off += 64
        return out.decode('latin1')

    def exports(self):
        if self._exports is not None:
            return self._exports
        res = {}
        erva, esz = self.dirs[0] if self.dirs else (0, 0)
        if erva and self.from_file:
            d = self.bytes_at(erva, 40)
            (_c, _t, _mj, _mn, _nm, base, nfun, nnames, aof, aon, aoo) = struct.unpack('<IIHHIIIIIII', d)
            funcs = struct.unpack('<%dI' % nfun, self.bytes_at(aof, 4 * nfun)) if nfun else ()
            names = struct.unpack('<%dI' % nnames, self.bytes_at(aon, 4 * nnames)) if nnames else ()
            ords = struct.unpack('<%dH' % nnames, self.bytes_at(aoo, 2 * nnames)) if nnames else ()
            for nrva, o in zip(names, ords):
                frva = funcs[o]
                if erva <= frva < erva + esz or not self.is_code(frva):
                    continue
                res.setdefault(frva, self.cstr(nrva))
            for i, frva in enumerate(funcs):
                if frva and frva not in res and not (erva <= frva < erva + esz) and self.is_code(frva):
                    res[frva] = '#%d' % (base + i)
        self._exports = sorted(res.items())
        self._exp_keys = [k for k, _ in self._exports]
        return self._exports

    def nearest_export(self, rva):
        ex = self.exports()
        if not ex:
            return None
        i = bisect.bisect_right(self._exp_keys, rva) - 1
        if i < 0:
            return None
        return ex[i][1], rva - ex[i][0]


def file_reader(path):
    f = open(path, 'rb')
    m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

    def rd(off, n):
        if off is None or off < 0 or off + n > len(m):
            return None
        return m[off:off + n]
    rd._keep = (f, m)
    return rd


# ----------------------------------------------------------------------------- map
def load_map(path):
    t0 = time.time()
    with open(path, 'rb') as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        pref = int(re.search(rb'Preferred load address is ([0-9a-fA-F]+)', mm[:4096]).group(1), 16)
        ts = re.search(rb'Timestamp is ([0-9a-fA-F]+)', mm[:4096])
        pat = re.compile(rb'^ 0001:[0-9a-fA-F]{8}\s+(\S+)\s+([0-9a-fA-F]{16})\s+(?:f\s+)?(?:i\s+)?(\S*)', re.M)
        d = {}
        for mt in pat.finditer(mm):
            a = int(mt.group(2), 16)
            if a not in d:
                d[a] = (mt.group(1).decode('latin1'), mt.group(3).decode('latin1'))
        mm.close()
    addrs = sorted(d)
    return {'pref': pref, 'ts': int(ts.group(1), 16) if ts else None, 'addrs': addrs,
            'syms': [d[a] for a in addrs], 'secs': time.time() - t0}


def pretty(name):
    """Very light MSVC undecoration: ?a@b@c@@... -> c::b::a (leaves special names alone)."""
    if name.startswith('?') and not name.startswith('??') and '@@' in name:
        parts = name[1:name.index('@@')].split('@')
        if all(p and not p.startswith('?') and not p.startswith('$') for p in parts):
            return '::'.join(reversed(parts))
    return name


# ----------------------------------------------------------------------------- call check
def call_before(get, R):
    """Is R plausibly a return address (preceded by a CALL)? True/False/None(unknown bytes)."""
    b = get(R - 8, 8)
    if b is None or len(b) != 8:
        return None

    def at(k):  # byte at R-k
        return b[8 - k]
    if at(5) == 0xE8:
        return 'rel32'
    for k in (2, 3, 4, 5, 6, 7):
        if at(k) != 0xFF:
            continue
        modrm = at(k - 1)
        if (modrm >> 3) & 7 != 2:
            continue
        mod, rm = modrm >> 6, modrm & 7
        L = 2
        if mod == 0:
            if rm == 4:
                if k < 3:
                    continue
                L += 1 + (4 if (at(k - 2) & 7) == 5 else 0)
            elif rm == 5:
                L += 4
        elif mod == 1:
            L += 1 + (1 if rm == 4 else 0)
        elif mod == 2:
            L += 4 + (1 if rm == 4 else 0)
        if L == k:
            return 'ff/2'
    return False


# ----------------------------------------------------------------------------- main
def main():
    t0 = time.time()
    D = Dump(DUMP)
    lines = []
    w = lines.append
    w('dumpstacks.py - heuristic host call stacks (stdlib-only, read-only)')
    w('dump: %s (%d bytes)  version=0x%08X  flags=0x%X  timestamp=%d (%s UTC)' % (
        DUMP, len(D.m), D.version, D.flags, D.timestamp,
        time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(D.timestamp))))
    w('streams:')
    for st, size, rva in D.streams:
        w('  type %2d %-20s size=%-10d rva=0x%X' % (st, STREAM_NAMES.get(st, '?'), size, rva))
    w('memory ranges: %d, captured bytes: %d' % (len(D.ranges), D.captured_bytes()))

    # misc info
    mi = D.stream(15)
    if mi:
        size, rva = mi
        sz, fl, pid, ctime, utime, ktime = struct.unpack_from('<IIIIII', D.m, rva)
        w('misc: pid=%d flags1=0x%X process_create=%d (%s UTC) user=%ds kernel=%ds  dump-create=%ds' % (
            pid, fl, ctime, time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ctime)), utime, ktime,
            D.timestamp - ctime))

    # modules
    mods = []
    ms = D.stream(4)
    size, rva = ms
    nmod = struct.unpack_from('<I', D.m, rva)[0]
    for i in range(nmod):
        o = rva + 4 + 108 * i
        base, isz, ck, ts, nrva = struct.unpack_from('<QIIII', D.m, o)
        name = D.mstr(nrva)
        short = name.replace('/', '\\').split('\\')[-1]
        mods.append({'base': base, 'size': isz, 'ts': ts, 'name': name, 'short': short, 'pe': None,
                     'pe_src': ''})
    mods.sort(key=lambda m: m['base'])
    mod_bases = [m['base'] for m in mods]

    def mod_of(a):
        i = bisect.bisect_right(mod_bases, a) - 1
        if i >= 0 and a < mods[i]['base'] + mods[i]['size']:
            return mods[i]
        return None

    # PE info: from run-dir files when timestamps match, else from dump memory headers if captured
    for m in mods:
        cand = os.path.join(RUNDIR, m['short'])
        if os.path.isfile(cand) and m['short'].lower().endswith(('.exe', '.dll')):
            try:
                pe = PE(file_reader(cand), True)
                if pe.ts == m['ts'] and pe.size_of_image == m['size']:
                    m['pe'], m['pe_src'] = pe, 'file'
                else:
                    m['pe_src'] = 'file-MISMATCH(ts %08X/%08X)' % (pe.ts, m['ts'])
            except Exception as ex:  # noqa
                m['pe_src'] = 'file-error %s' % ex
        if m['pe'] is None:
            base = m['base']
            try:
                if D.read(base, 0x400) is not None:
                    pe = PE(lambda off, n, b=base: D.read(b + off, n), False)
                    m['pe'], m['pe_src'] = pe, 'dump-hdr'
            except Exception:
                pass

    # map
    MP = load_map(MAP)
    exe = next((m for m in mods if m['short'].lower() == 'legodimensions.exe'), None)
    w('map: %s  preferred=0x%X  map-timestamp=%s  exe-ts=%s  code symbols=%d (parsed in %.1fs)' % (
        MAP, MP['pref'], '%08X' % MP['ts'] if MP['ts'] else '?', '%08X' % exe['ts'] if exe else '?',
        len(MP['addrs']), MP['secs']))
    if exe and MP['ts'] and exe['ts'] != MP['ts']:
        w('WARNING: map timestamp does not match exe module in dump; exe symbols unreliable')

    def code_get(a, n):
        m = mod_of(a)
        if m and m['pe'] is not None and m['pe'].from_file:
            return m['pe'].bytes_at(a - m['base'], n)
        return D.read(a, n)

    def symbolize(a):
        m = mod_of(a)
        if m is None:
            return '<no module>', ''
        off = a - m['base']
        loc = '%s+0x%X' % (m['short'], off)
        sym = ''
        if m is exe:
            pa = off + MP['pref']
            i = bisect.bisect_right(MP['addrs'], pa) - 1
            if i >= 0:
                nm, obj = MP['syms'][i]
                sym = '%s+0x%X  [%s]' % (nm, pa - MP['addrs'][i], obj)
                pn = pretty(nm)
                if pn != nm:
                    sym += '  {%s}' % pn
        elif m['pe'] is not None and m['pe'].from_file:
            f = m['pe'].func_of(off)
            ne = m['pe'].nearest_export(off)
            parts = []
            if f:
                parts.append('func@+0x%X+0x%X' % (f[0], off - f[0]))
            if ne:
                parts.append('nearest-export %s+0x%X' % (pretty(ne[0]), ne[1]))
            sym = '  '.join(parts)
        if m['pe'] is not None:
            sec = m['pe'].section_name(off)
            if sec not in ('.text', '?'):
                sym = ('(%s) ' % sec) + sym
        return loc, sym

    w('modules: %d' % len(mods))
    w('relevant modules (base, size, timestamp, pe-info source):')
    for m in mods:
        if RELEVANT.match(m['short']):
            w('  %016X %10X %08X %-28s %s' % (m['base'], m['size'], m['ts'], m['short'], m['pe_src']))

    # threads
    tl = D.stream(3)
    size, rva = tl
    nthr = struct.unpack_from('<I', D.m, rva)[0]
    threads = []
    for i in range(nthr):
        (tid, susp, pcls, prio, teb, sstart, ssize, srva, csize, crva) = struct.unpack_from(
            '<IIIIQQIIII', D.m, rva + 4 + 48 * i)
        ctx = D.m[crva:crva + csize]
        rsp, rbp = struct.unpack_from('<QQ', ctx, 0x98)
        rip = struct.unpack_from('<Q', ctx, 0xF8)[0]
        if srva and ssize:
            stack = D.m[srva:srva + ssize]
        else:
            stack = D.read(sstart, ssize) or b''
        threads.append({'tid': tid, 'susp': susp, 'pcls': pcls, 'prio': prio, 'teb': teb,
                        'sstart': sstart, 'ssize': ssize, 'stack': stack, 'rsp': rsp, 'rbp': rbp,
                        'rip': rip, 'ctx': ctx})
    w('threads: %d' % nthr)

    # memory info list: protection of pages (used to keep only executable values in modules
    # whose PE headers / code bytes are not available)
    minfo = []
    mis = D.stream(16)
    if mis:
        size, rva = mis
        hs, es, cnt = struct.unpack_from('<IIQ', D.m, rva)
        for i in range(cnt):
            b, ab, _ap, _a1, rs, state, prot, typ, _a2 = struct.unpack_from('<QQIIQIIII', D.m, rva + hs + es * i)
            minfo.append((b, rs, ab, state, prot, typ))
        minfo.sort()
    mi_bases = [x[0] for x in minfo]

    def meminfo(a):
        i = bisect.bisect_right(mi_bases, a) - 1
        if i >= 0 and a < minfo[i][0] + minfo[i][1]:
            return minfo[i]
        return None

    def executable(a):
        inf = meminfo(a)
        if inf is None:
            return None
        return inf[3] == 0x1000 and bool(inf[4] & 0xF0)

    allocs = {}
    for b, rs, ab, state, prot, typ in minfo:
        if state != 0x10000:
            allocs[ab] = allocs.get(ab, 0) + rs
    big = sorted(allocs.items(), key=lambda kv: -kv[1])[:4]
    w('largest allocations (memory-info): ' + ', '.join('0x%X:%.1fGB' % (ab, s / 2 ** 30) for ab, s in big))
    for ab in [0x100000000] + [ab for ab, s in big if s >= 0x100000000 and ab != 0x100000000]:
        if True:
            cs = D.read(ab + 0x84959EDC, 0x1C)
            if cs:
                lc, rc, own = struct.unpack_from('>iiI', cs, 0x10)
                w('  guest CS 0x84959EDC @ host 0x%X: %s  lock_count=%d recursion=%d owner=0x%08X' % (
                    ab + 0x84959EDC, cs.hex(), lc, rc, own))
            else:
                w('  guest CS 0x84959EDC @ host 0x%X: not captured in dump' % (ab + 0x84959EDC))

    names = {}
    tn = D.stream(24)
    if tn:
        size, rva = tn
        cnt = struct.unpack_from('<I', D.m, rva)[0]
        for i in range(cnt):
            tid, nrva = struct.unpack_from('<IQ', D.m, rva + 4 + 12 * i)
            try:
                names[tid] = D.mstr(nrva)
            except Exception:
                pass
    tinfo = {}
    ti = D.stream(17)
    if ti:
        size, rva = ti
        hs, es, cnt = struct.unpack_from('<III', D.m, rva)
        for i in range(cnt):
            (tid, dflags, derr, exitst, ct, et, kt, ut, sa, aff) = struct.unpack_from(
                '<IIIIQQQQQQ', D.m, rva + hs + es * i)
            tinfo[tid] = {'create': ct, 'kernel': kt, 'user': ut, 'start': sa, 'flags': dflags}

    def walk(t):
        """Heuristic frames: list of (stack_addr or None, value, flag)."""
        frames = [(None, t['rip'], 'ip')]
        st, data = t['sstart'], t['stack']
        begin = t['rsp'] if st <= t['rsp'] < st + len(data) else st
        begin = (begin + 7) & ~7
        end = min(st + len(data), begin + SCAN_CAP)
        rejected = 0
        fnptr = 0
        hits = 0
        last = t['rip']
        beyond = []  # verified frames after the cap (exe / rex only: code bytes known)
        for a in range(begin, end - 7, 8):
            v = struct.unpack_from('<Q', data, a - st)[0]
            m = mod_of(v)
            if m is None:
                continue
            pe = m['pe']
            off = v - m['base']
            if pe is not None:
                if not pe.is_code(off):
                    continue
                if pe.from_file and pe.dirs and len(pe.dirs) > 3 and pe.dirs[3][0] and pe.func_of(off) is None:
                    rejected += 1
                    continue
            elif executable(v) is False:
                continue
            cb = call_before(code_get, v)
            if cb is False:
                rejected += 1
                continue
            if cb == 'rel32':
                rel = struct.unpack('<i', code_get(v - 4, 4))[0]
                if mod_of((v + rel) & 0xFFFFFFFFFFFFFFFF) is None:
                    rejected += 1
                    continue
            if cb is None and (v & 0xF) == 0:
                fnptr += 1  # unverifiable and 16-byte aligned: most likely a function pointer
                continue
            flag = 'V' if cb else '?'
            if v == last:
                continue
            last = v
            if hits >= MAX_HITS:
                if flag == 'V':
                    beyond.append((a, v, flag))
                continue
            frames.append((a, v, flag))
            hits += 1
        return frames, rejected, begin, end, fnptr, beyond

    def tname(t):
        n = names.get(t['tid'], '')
        return n

    def syscall_hint(rip):
        m = mod_of(rip)
        if not m or m['short'].lower() != 'ntdll.dll':
            return ''
        b = D.read(rip - 0x14, 0x14)
        if b and b[0:4] == b'\x4C\x8B\xD1\xB8':
            return ' syscall#0x%X' % struct.unpack_from('<I', b, 4)[0]
        return ''

    def summ(t, frames):
        loc, sym = symbolize(t['rip'])
        picks = []
        for sa, v, fl in frames[1:]:
            m = mod_of(v)
            if m and re.match(r'(legodimensions\.exe|rex|d3d|nv|dxgi)', m['short'], re.I):
                l2, s2 = symbolize(v)
                s2 = s2.split('  [')[0].split('  nearest')[0]
                picks.append('%s%s%s' % (l2, (' ' + s2) if s2 else '', '' if fl == 'V' else '(?)'))
                if len(picks) >= 3:
                    break
        info = tinfo.get(t['tid'])
        cpu = ''
        if info:
            cpu = ' cpu u=%.2fs k=%.2fs start=%s' % (info['user'] / 1e7, info['kernel'] / 1e7,
                                                      symbolize(info['start'])[0])
        guest = [symbolize(v)[1].split('  [')[0] for sa, v, fl in frames[1:]
                 if fl == 'V' and mod_of(v) is exe and 'sub_' in symbolize(v)[1]][:3]
        return 'TID %6d (0x%05X) susp=%d prio=%d%s%s | rip %s %s%s | %s%s' % (
            t['tid'], t['tid'], t['susp'], t['prio'], (' name="%s"' % tname(t)) if tname(t) else '',
            cpu, loc, sym.split('  [')[0].split('  nearest')[0], syscall_hint(t['rip']),
            ' <- '.join(picks) if picks else '(no exe/rex/d3d/nv frames)',
            (' | guest: ' + ' <- '.join(guest)) if guest else '')

    results = {}
    for t in threads:
        results[t['tid']] = walk(t)

    for tid in FOCUS:
        t = next((x for x in threads if x['tid'] == tid), None)
        w('')
        w('=' * 100)
        if t is None:
            w('TID %d (0x%X): NOT FOUND in thread list' % (tid, tid))
            continue
        frames, rej, b, e, fnp, beyond = results[tid]
        info = tinfo.get(tid)
        w('TID %d (0x%X)%s  suspend=%d prio=%d teb=0x%X' % (tid, tid, (' name="%s"' % tname(t)) if tname(t) else '',
                                                        t['susp'], t['prio'], t['teb']))
        if info:
            w('  thread-info: start=%s %s  user=%.3fs kernel=%.3fs flags=0x%X' % (
                symbolize(info['start'])[0], symbolize(info['start'])[1].split('  [')[0],
                info['user'] / 1e7, info['kernel'] / 1e7, info['flags']))
        w('  rip=0x%X rsp=0x%X rbp=0x%X stack=[0x%X..0x%X) %d bytes; scanned [0x%X..0x%X); '
          'rejected (no CALL before / not in a function)=%d, dropped 16-aligned unverifiable=%d%s' % (
              t['rip'], t['rsp'], t['rbp'], t['sstart'], t['sstart'] + t['ssize'],
              t['ssize'], b, e, rej, fnp, syscall_hint(t['rip'])))
        regs = ['rax', 'rcx', 'rdx', 'rbx', 'rsp', 'rbp', 'rsi', 'rdi', 'r8', 'r9', 'r10', 'r11', 'r12',
                'r13', 'r14', 'r15']
        rv = struct.unpack_from('<16Q', t['ctx'], 0x78)
        w('  regs: ' + ' '.join('%s=%X' % (n, v) for n, v in zip(regs, rv)))
        w('  heuristic frames (V = preceded by CALL, ? = code bytes unavailable; stale frames possible):')
        for idx, (sa, v, fl) in enumerate(frames):
            loc, sym = symbolize(v)
            mark = ' <==' if INTEREST.search(sym or '') else ''
            w('  %2d %-3s %-18s %016X  %-34s %s%s' % (
                idx, fl, ('rsp+0x%X' % (sa - t['rsp'])) if sa is not None else 'RIP', v, loc, sym, mark))
        if beyond:
            w('  verified (V) exe/rex frames beyond the %d-hit cap:' % MAX_HITS)
            for sa, v, fl in beyond:
                loc, sym = symbolize(v)
                mark = ' <==' if INTEREST.search(sym or '') else ''
                w('     %-3s %-18s %016X  %-34s %s%s' % (fl, 'rsp+0x%X' % (sa - t['rsp']), v, loc, sym, mark))
        # unwound chain: start at the first verified exe/rex frame and follow UNWIND_INFO frame sizes
        # (caller's return slot = slot + 8 + fixed frame size of the function containing the address)
        first = None
        st, data = t['sstart'], t['stack']

        def chain_from(sa, v):
            out = []
            for _ in range(80):
                m = mod_of(v)
                fs = m['pe'].frame_size(v - m['base']) if (m and m['pe'] is not None and m['pe'].from_file) else None
                out.append((sa, v, fs))
                if fs is None:
                    break
                sa = sa + 8 + fs[0]
                if not (st <= sa < st + len(data) - 7):
                    out.append((sa, None, 'off'))
                    break
                v = struct.unpack_from('<Q', data, sa - st)[0]
                if mod_of(v) is None:
                    out.append((sa, v, 'broken'))
                    break
            return out
        skipped = []
        for sa0, v0, fl0 in frames[1:]:
            if fl0 != 'V' or sa0 is None:
                continue
            ch = chain_from(sa0, v0)
            if sum(1 for x in ch if x[1] is not None and mod_of(x[1]) is not None) >= 4:
                first = ch
                break
            skipped.append('rsp+0x%X' % (sa0 - t['rsp']))
        if first:
            w('  unwound exe/rex chain (pdata/UNWIND_INFO frame sizes; start candidates that did not chain: %s):' % (
                ', '.join(skipped) or 'none'))
            for sa, v, fs in first:
                if fs in ('off', 'broken'):
                    w('     %-18s %s' % ('rsp+0x%X' % (sa - t['rsp']), '(ran off the captured stack)' if fs == 'off'
                                         else '%016X (not a module address: chain broken)' % v))
                    continue
                loc, sym = symbolize(v)
                w('     %-18s %016X  %-34s %s%s' % ('rsp+0x%X' % (sa - t['rsp']), v, loc, sym.split('  [')[0],
                                                  '' if fs is None else '  (frame 0x%X%s)' % (fs[0], ' fp' if fs[1] else '')))
        st, data = t['sstart'], t['stack']
        raw = []
        for a in range(b, e - 7, 8):
            v = struct.unpack_from('<Q', data, a - st)[0]
            m = mod_of(v)
            if m is None or m['pe'] is None or not m['pe'].from_file or not m['pe'].is_code(v - m['base']):
                continue
            raw.append((a, v, call_before(code_get, v)))
        w('  unfiltered exe/rex code pointers on the scanned stack: %d (x = no CALL before it)' % len(raw))
        if len(raw) <= 120:
            for a, v, cb in raw:
                loc, sym = symbolize(v)
                w('     %-2s %-18s %016X  %-34s %s' % ('x' if cb is False else '', 'rsp+0x%X' % (a - t['rsp']),
                                                       v, loc, sym.split('  [')[0]))

    w('')
    w('=' * 100)
    w('per-thread summary (rip, then first 3 exe/rex/d3d/nv/dxgi heuristic frames):')
    for t in threads:
        w('  ' + summ(t, results[t['tid']][0]))
    w('')
    w('elapsed %.1fs' % (time.time() - t0))
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', OUT, '(%d lines, %.1fs)' % (len(lines), time.time() - t0))


if __name__ == '__main__':
    main()

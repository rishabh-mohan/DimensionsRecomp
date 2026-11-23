"""S6 clock / front-end scan of the A generated tree (read-only, 1 thread, ~1 min).

Goal (Agent 10's 1b exit split, option (b)): guest addresses to diff in snap1 vs snapB3.
  1. Time sources: functions with mftb/mftbu/mfspr TB, or calls to time imports (__imp__KeQuery...).
  2. Their direct callers (C1) and callers of those (C2).
  3. Writable data globals stored by time sources/C1/C2 (frame-clock candidates), with reader counts.
  4. Front-end-range functions that read those globals or call the time functions.
  5. Records of known front-end anchors (rexlego hooks): callees, data loads, callers.
Usage: python s6_clock_scan.py [tu files...]   (no args = whole A tree; report s6-clock-report.txt)
"""
import collections, glob, os, re, sys, time

GEN = (r'<workspace>'
       r'\baseline\DimensionsRecomp\rexlego\generated\default')
HERE = os.path.dirname(os.path.abspath(__file__))
M = 0xFFFFFFFF
DATA_LO, DATA_HI = 0x84113BAC, 0x84B80000      # writable data after code; image ends 0x84B80000
FE_RANGES = [(0x82EF0000, 0x83000000), (0x839C0000, 0x839E0000)]
ANCHORS = {
    0x82FEA350: 'FE manager per-frame (settings_native_hooks.cpp:186 BeforeFrame/AfterFrame)',
    0x82F0F8D0: 'page Input r3-r6 (settings_native_hooks.cpp:203)',
    0x82FD8C30: 'request_page (settings_native_hooks.cpp:116)',
    0x82F0FF38: 'page_event (settings_native_hooks.cpp:111)',
    0x82FCF858: 'FE manager init (settings_native_hooks.cpp:140)',
    0x82FE4A80: 'main menu A pressed (main_menu_extras.cpp:18)',
    0x82FBE7A8: 'main menu AboutToShow (main_menu_extras.cpp:6)',
    0x82EF9730: 'find_page', 0x82F0FAC0: 'load_layout', 0x82EFCB70: 'play UI sound',
}
TIME_IMP_RE = re.compile(r'__imp__(\w*(?:QueryPerformance|SystemTime|InterruptTime|DelayExecution|YieldExecution'
                         r'|TimeStamp|TickCount|Timer)\w*)')
CALL_RE = re.compile(r'\bsub_([0-9A-Fa-f]{8})\(')
MEM_RE = re.compile(r'^(-?(?:0x[0-9a-fA-F]+|\d+))\((r\d+)\)$')
GPR_RE = re.compile(r'^r\d+$')
VOLATILE = ['r0'] + ['r%d' % i for i in range(3, 13)]
NODEST = ('st', 'cmp', 'mt', 'tw', 'td', 'dcb', 'icb', 'b', 'fcmp', 'sync', 'lwsync', 'eieio',
          'isync', 'sc', 'db', 'cctp', 'nop', 'vcmp')


def toint(s):
    s = s.strip()
    try:
        return int(s, 0)
    except ValueError:
        return int(s, 10)


def in_fe(a):
    return any(lo <= a < hi for lo, hi in FE_RANGES)


def in_data(ea):
    return DATA_LO <= ea < DATA_HI


class Rec:
    __slots__ = ('tu', 'ln', 'mftb', 'imps', 'callees', 'loads', 'stores', 'fcmp', 'fadd')


class Scan:
    def __init__(self):
        self.funcs = {}
        self.lines = 0
        self.cur = None
        self.cur_addr = None

    def finalize(self, jumps, labels):
        r = self.cur
        if r is None:
            return
        for t in jumps:
            if t not in labels:
                r.callees.add(t)
        r.callees = tuple(sorted(r.callees))
        r.loads = tuple(sorted(r.loads))
        r.stores = tuple(sorted(r.stores))
        r.imps = tuple(r.imps)
        self.funcs[self.cur_addr] = r
        self.cur = None

    def scan_file(self, path):
        parts = os.path.basename(path).split('.')
        tu = parts[1] if len(parts) >= 3 else parts[0]
        vals, labels, jumps = {}, set(), set()
        cur = None
        ln = 0
        with open(path, encoding='utf-8', errors='replace') as f:
            for ln, line in enumerate(f, 1):
                if line.startswith('\t// '):
                    if cur is None:
                        continue
                    body = line[4:].strip()
                    if not body:
                        continue
                    mn, _, rest = body.partition(' ')
                    mn = mn.rstrip('.+-')
                    ops = [o.strip() for o in rest.split(',')] if rest.strip() else []
                    if mn in ('mftb', 'mftbu') or (mn == 'mfspr' and len(ops) == 2
                                                   and ops[1] in ('268', '269', 'tbl', 'tbu')):
                        cur.mftb += 1
                        continue
                    if mn.startswith('fcmp'):
                        cur.fcmp += 1
                        continue
                    if mn in ('fadd', 'fadds', 'fsub', 'fsubs'):
                        cur.fadd += 1
                    if mn.startswith('b'):
                        tgt = None
                        if ops:
                            o = ops[-1]
                            try:
                                if o.startswith('0x'):
                                    tgt = int(o, 16)
                                elif o.startswith('sub_'):
                                    tgt = int(o[4:], 16)
                            except ValueError:
                                tgt = None
                        if mn == 'bl':
                            if tgt is not None:
                                cur.callees.add(tgt)
                        elif mn == 'b' and tgt is not None:
                            jumps.add(tgt)
                        if mn.endswith('l'):
                            for r in VOLATILE:
                                vals.pop(r, None)
                        continue
                    if mn == 'la' and len(ops) == 2:
                        m = MEM_RE.match(ops[1])
                        if m and GPR_RE.match(ops[0]):
                            ra = m.group(2)
                            b0 = 0 if ra == 'r0' else vals.get(ra)
                            if b0 is None:
                                vals.pop(ops[0], None)
                            else:
                                vals[ops[0]] = (b0 + toint(m.group(1))) & M
                        continue
                    if len(ops) == 2 and '(' in ops[1]:
                        m = MEM_RE.match(ops[1])
                        if m:
                            ra = m.group(2)
                            b0 = 0 if ra == 'r0' else vals.get(ra)
                            ea = None if b0 is None else (b0 + toint(m.group(1))) & M
                            if mn.startswith('st'):
                                if ea is not None and in_data(ea):
                                    cur.stores.add(ea)
                            elif mn.startswith('l'):
                                if ea is not None and in_data(ea):
                                    cur.loads.add(ea)
                                if GPR_RE.match(ops[0]):
                                    vals.pop(ops[0], None)
                            if mn.endswith('u') and ra != 'r0':
                                if ea is None:
                                    vals.pop(ra, None)
                                else:
                                    vals[ra] = ea
                            continue
                    if not ops or not GPR_RE.match(ops[0]):
                        continue
                    d = ops[0]
                    v = None
                    try:
                        if mn == 'lis' and len(ops) == 2:
                            v = (toint(ops[1]) << 16) & M
                        elif mn == 'li' and len(ops) == 2:
                            v = toint(ops[1]) & M
                        elif mn in ('addi', 'subi', 'addis', 'subis') and len(ops) == 3:
                            if ops[1] in vals:
                                imm = toint(ops[2])
                                if mn.startswith('sub'):
                                    imm = -imm
                                if mn.endswith('s'):
                                    imm <<= 16
                                v = (vals[ops[1]] + imm) & M
                        elif mn in ('ori', 'oris') and len(ops) == 3:
                            if ops[1] in vals:
                                imm = toint(ops[2]) & 0xFFFF
                                if mn == 'oris':
                                    imm <<= 16
                                v = vals[ops[1]] | imm
                        elif mn == 'mr' and len(ops) == 2:
                            v = vals.get(ops[1])
                        elif mn.startswith(NODEST):
                            continue
                    except ValueError:
                        v = None
                    if v is None:
                        vals.pop(d, None)
                    else:
                        vals[d] = v
                elif line.startswith('DEFINE_REX_FUNC('):
                    self.cur = cur
                    self.finalize(jumps, labels)
                    name = line[16:line.index(')')]
                    if name.startswith('__imp__'):
                        name = name[7:]
                    cur = None
                    vals, labels, jumps = {}, set(), set()
                    if name.startswith('sub_'):
                        try:
                            self.cur_addr = int(name[4:], 16)
                        except ValueError:
                            continue
                        cur = Rec()
                        cur.tu, cur.ln, cur.mftb, cur.imps = tu, ln, 0, []
                        cur.callees, cur.loads, cur.stores, cur.fcmp, cur.fadd = set(), set(), set(), 0, 0
                elif cur is None:
                    continue
                elif line.startswith('loc_'):
                    s = line.strip()
                    if s.endswith(':'):
                        try:
                            labels.add(int(s[4:-1], 16))
                        except ValueError:
                            pass
                else:
                    if '__imp__' in line:
                        m = TIME_IMP_RE.search(line)
                        if m:
                            cur.imps.append(m.group(1))
                    if 'sub_' in line:
                        for h in CALL_RE.findall(line):
                            cur.callees.add(int(h, 16))
        self.cur = cur
        self.finalize(jumps, labels)
        self.lines += ln

    def report(self, nfiles, secs):
        F = self.funcs
        out = []
        P = out.append

        def loc(a):
            r = F.get(a)
            return 'TU%s:%d' % (r.tu, r.ln) if r else '(not in scanned files)'

        P('S6 clock/front-end scan (A tree): %d files, %d lines, %d functions, %.1f s'
          % (nfiles, self.lines, len(F), secs))
        P('')
        Mset = {a for a, r in F.items() if r.mftb or r.imps}
        P('## 1. Time sources: %d functions' % len(Mset))
        for a in sorted(Mset):
            r = F[a]
            P('  sub_%08X %s  mftb=%d  imports=%s  fcmp=%d fadd=%d  callees=%d'
              % (a, loc(a), r.mftb, ','.join(sorted(set(r.imps))) or '-', r.fcmp, r.fadd, len(r.callees)))
        callers = collections.defaultdict(set)
        for a, r in F.items():
            for c in r.callees:
                callers[c].add(a)
        C1 = set()
        for a in Mset:
            C1 |= callers.get(a, set())
        C1 -= Mset
        C2 = set()
        for a in C1:
            C2 |= callers.get(a, set())
        C2 -= Mset | C1
        P('')
        P('## 2. Callers: C1 (direct callers of time sources) %d, C2 (callers of C1) %d' % (len(C1), len(C2)))
        for a in sorted(C1):
            r = F[a]
            P('  C1 sub_%08X %s  calls %s  fcmp=%d fadd=%d  stores=%d  callers=%d%s'
              % (a, loc(a), ','.join('sub_%08X' % c for c in r.callees if c in Mset), r.fcmp, r.fadd,
                 len(r.stores), len(callers.get(a, ())), '  [FE]' if in_fe(a) else ''))
        for a in sorted(C2)[:400]:
            r = F[a]
            P('  C2 sub_%08X %s  calls %s%s'
              % (a, loc(a), ','.join('sub_%08X' % c for c in r.callees if c in C1)[:120],
                 '  [FE]' if in_fe(a) else ''))
        if len(C2) > 400:
            P('  ... %d more C2' % (len(C2) - 400))
        writers = collections.defaultdict(set)
        for a in Mset | C1:
            for ea in F[a].stores:
                writers[ea].add(a)
        readers = collections.defaultdict(set)
        for a, r in F.items():
            for ea in r.loads:
                if ea in writers:
                    readers[ea].add(a)
        P('')
        P('## 3. Writable globals stored by time sources / C1: %d' % len(writers))
        for ea in sorted(writers):
            rd = readers.get(ea, set())
            fe = sorted(x for x in rd if in_fe(x))
            P('  0x%08X  writers %s  readers %d  FE readers %s'
              % (ea, ','.join('sub_%08X' % w for w in sorted(writers[ea]))[:150], len(rd),
                 ','.join('sub_%08X' % x for x in fe[:12]) or '-'))
        P('')
        cand = []
        for a, r in F.items():
            if not in_fe(a):
                continue
            g = [ea for ea in r.loads if ea in writers]
            c = [x for x in r.callees if x in Mset or x in C1]
            if g or c:
                cand.append((a, g, c))
        P('## 4. Front-end-range functions that read those globals or call time sources/C1: %d' % len(cand))
        for a, g, c in sorted(cand):
            r = F[a]
            P('  sub_%08X %s  globals %s  calls %s  fcmp=%d fadd=%d  callers %s'
              % (a, loc(a), ','.join('0x%08X' % x for x in g) or '-', ','.join('sub_%08X' % x for x in c) or '-',
                 r.fcmp, r.fadd, ','.join('sub_%08X' % x for x in sorted(callers.get(a, ()))[:6])))
        P('')
        P('## 5. Front-end anchors (rexlego hooks)')
        for a in sorted(ANCHORS):
            r = F.get(a)
            P('  sub_%08X  %s  %s' % (a, ANCHORS[a], loc(a)))
            if not r:
                continue
            P('     mftb=%d imports=%s fcmp=%d fadd=%d' % (r.mftb, ','.join(r.imps) or '-', r.fcmp, r.fadd))
            P('     callees (%d): %s' % (len(r.callees), ' '.join('sub_%08X%s' % (c, '*' if c in Mset or c in C1
                                                                               else '') for c in r.callees)[:900]))
            P('     data loads (%d): %s' % (len(r.loads), ' '.join('0x%08X' % x for x in r.loads)[:600]))
            P('     data stores (%d): %s' % (len(r.stores), ' '.join('0x%08X' % x for x in r.stores)[:400]))
            P('     callers (%d): %s' % (len(callers.get(a, ())),
                                         ' '.join('sub_%08X' % x for x in sorted(callers.get(a, ())))[:400]))
        return out


def main():
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(GEN, 'legodimensions_recomp.*.cpp')),
                                   key=lambda p: int(os.path.basename(p).split('.')[1]))
    t0 = time.time()
    sc = Scan()
    for p in files:
        sc.scan_file(p)
    out = sc.report(len(files), time.time() - t0)
    name = 's6-clock-report.txt' if not sys.argv[1:] else 's6-clock-report-test.txt'
    with open(os.path.join(HERE, name), 'w', encoding='ascii', errors='replace', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print('report:', os.path.join(HERE, name))
    for line in out[:120]:
        print(line[:220])


if __name__ == '__main__':
    main()

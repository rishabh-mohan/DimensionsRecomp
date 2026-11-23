#!/usr/bin/env python3
"""Step 7 (read-only): who reads/writes the walk's gating globals.
Scans every generated TU for REX_STORE/REX_LOAD at the low half of each global and confirms the
base register was last loaded with the matching lis value. Writes step7.log. Run via cpu2.ps1."""
import bisect
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
GEN = os.path.join(ROOT, 'baseline', 'DimensionsRecomp', 'rexlego', 'generated', 'default')
OUT = os.path.join(HERE, 'step7.log')
# offset -> list of (name, lis value)
OFFS = {
    24304: [('0x849F5EF0 ui_skip_frames', -2069954560)],
    8656: [('0x849E21D0 layer2_skip_frames', -2070020096)],
    24340: [('0x849F5F14 two_layer_arg', -2069954560)],
    -24672: [('0x84959FA0 slot_mode1_enable', -2070544384)],
    212: [('0x848C00D4 skip_8268C580', -2071199744)],
    24260: [('0x849F5EC4 fcb308_arg0', -2069954560)],
}
pat = re.compile(r'REX_(STORE|LOAD)_U(8|16|32|64)\(ctx\.(r\d+)\.u32 \+ (24304|8656|24340|-24672|212|24260)(?=[,)])')
defpat = re.compile(r'^DEFINE_REX_FUNC\((sub_[0-9A-F]{8})\)', re.M)
out = open(OUT, 'w', encoding='ascii', errors='replace', newline='\n')
hits = []
for tu in range(0, 600):
    path = os.path.join(GEN, 'legodimensions_recomp.%d.cpp' % tu)
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='latin-1') as f:
        txt = f.read()
    defs = [(m.start(), m.group(1)) for m in defpat.finditer(txt)]
    starts = [d[0] for d in defs]
    for m in pat.finditer(txt):
        kind, width, reg, off = m.group(1), m.group(2), m.group(3), int(m.group(4))
        i = bisect.bisect_right(starts, m.start()) - 1
        fstart = starts[i] if i >= 0 else 0
        fname = defs[i][1] if i >= 0 else '?'
        window = txt[max(fstart, m.start() - 8000):m.start()]
        last = None
        for a in re.finditer(r'ctx\.' + reg + r'\.(?:s64|u64) = ([^;]+);', window):
            last = a
        val = None
        if last:
            try:
                val = int(last.group(1))
            except ValueError:
                val = None
        for name, hi in OFFS[off]:
            if val == hi:
                line = txt.count('\n', 0, m.start()) + 1
                hits.append((name, kind, width, tu, line, fname))
for name in sorted(set(h[0] for h in hits)):
    out.write('=== %s\n' % name)
    for h in hits:
        if h[0] == name and h[1] == 'STORE':
            out.write('STORE u%s TU%d:%d %s\n' % (h[2], h[3], h[4], h[5]))
    readers = {}
    for h in hits:
        if h[0] == name and h[1] == 'LOAD':
            readers.setdefault(h[5], []).append('TU%d:%d' % (h[3], h[4]))
    for fn, locs in sorted(readers.items()):
        out.write('LOAD %s %s\n' % (fn, ' '.join(locs[:4])))
out.write('done %d hits\n' % len(hits))
out.close()

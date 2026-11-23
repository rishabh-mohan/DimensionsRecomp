#!/usr/bin/env python3
"""flagw: functions in snapB3 that store to a global byte HI<<16 + LO (lis/stb or lis/addi/stb forms).
  flagw.py HI_S64 LO      e.g. flagw.py -2071068672 11938  (0x848E2EA2, read by sub_82A75FD8). Agent 10, read-only."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livein

hi, lo = sys.argv[1], sys.argv[2]
HI = re.compile(r'ctx\.r(\d+)\.s64 = %s;' % re.escape(hi))
w, r = [], []
for tu, name, lines in livein.funcs(livein.GEN['B']):
    body = '\n'.join(lines)
    if hi not in body:
        continue
    st = [i for i, l in enumerate(lines) if re.search(r'REX_STORE_U(?:8|16|32|64)\(ctx\.r\d+\.u32 \+ %s,' % lo, l)]
    ad = [i for i, l in enumerate(lines) if re.search(r'ctx\.r\d+\.s64 = ctx\.r\d+\.s64 \+ %s;' % lo, l)]
    ld = [i for i, l in enumerate(lines) if re.search(r'REX_LOAD_U(?:8|16|32|64)\(ctx\.r\d+\.u32 \+ %s\)' % lo, l)]
    if st or ad:
        w.append('%s TU %d: store lines %s; addi lines %s' % (name, tu, st, ad))
    if ld:
        r.append('%s TU %d: load lines %s' % (name, tu, ld))
print('candidate writers (function has %s and a store at +%s or an addi of %s): %d' % (hi, lo, lo, len(w)))
print('\n'.join(w))
print('\nreaders (function has %s and a load at +%s): %d' % (hi, lo, len(r)))
print('\n'.join(r))

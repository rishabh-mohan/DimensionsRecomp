#!/usr/bin/env python3
"""flag2288: who writes the byte at [app]+2288 (app = *(0x849F5E8C)), which gates the page-timeout
accumulator in sub_82FE70C0 (event 5 adds dt only while it is 0). Read-only lead for S4 (Agent 10)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livein

APP = re.compile(r'\+ 24204\)')
ST = re.compile(r'REX_STORE_U8\(ctx\.r\d+\.u32 \+ 2288, (.*)\);')
LD = re.compile(r'REX_LOAD_U8\(ctx\.r\d+\.u32 \+ 2288\)')
w, r = [], []
for tu, name, lines in livein.funcs(livein.GEN['B']):
    body = '\n'.join(lines)
    if not APP.search(body):
        continue
    sts = [(i, ST.search(l).group(1)) for i, l in enumerate(lines) if ST.search(l)]
    lds = [i for i, l in enumerate(lines) if LD.search(l)]
    if sts:
        w.append('%s TU %d: %s' % (name, tu, '; '.join('line +%d stores %s' % s for s in sts)))
    if lds:
        r.append('%s TU %d: loads at line +%s' % (name, tu, ','.join(str(i) for i in lds)))
print('functions that load the app pointer (0x849F5E8C) and store a byte at +2288: %d' % len(w))
print('\n'.join(w))
print('\nfunctions that load the app pointer and load a byte at +2288: %d' % len(r))
print('\n'.join(r))

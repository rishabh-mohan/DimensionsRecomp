#!/usr/bin/env python3
"""Check RATE-REQUEST.md against the staged files (Agent 7, task #17). Read-only, stdlib.

1. Every line of each ```cpp block appears, in order, as a whole line of after/native_worker.cpp or
   after/native_preparation.h (markdown list indentation removed).
2. Every 64-hex sha256 in RATE-REQUEST.md is listed in SHA256SUMS.txt, and every SHA256SUMS hash is in RATE-REQUEST.md.
3. Prints the after-file lines that RATE-REQUEST.md cites by number, for a by-eye check.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AFTER = os.path.join(HERE, 'after', 'src', 'gpu_native')
fails = 0


def read_lines(name):
    with open(os.path.join(AFTER, name), 'rb') as f:
        return f.read().decode('ascii').split('\r\n')


with open(os.path.join(HERE, 'RATE-REQUEST.md'), encoding='utf-8') as f:
    rr = f.read()
files = {n: read_lines(n) for n in ('native_worker.cpp', 'native_preparation.h', 'native_recording.cpp')}

blocks = re.findall(r'^( *)```cpp\n(.*?)^\1```', rr, flags=re.S | re.M)
for k, (indent, body) in enumerate(blocks, 1):
    lines = [l[len(indent):] if l.startswith(indent) else l for l in body.split('\n')]
    lines = [l for l in lines if l.strip()]
    ok_any = False
    for name in ('native_worker.cpp', 'native_preparation.h'):
        src, pos, ok = files[name], 0, True
        for l in lines:
            try:
                pos = src.index(l, pos) + 1
            except ValueError:
                ok = False
                break
        if ok:
            print(f'PASS cpp block {k}: {len(lines)} lines found in order in after/{name}')
            ok_any = True
            break
    if not ok_any:
        fails += 1
        print(f'FAIL cpp block {k}: not found in order in either file')

with open(os.path.join(HERE, 'SHA256SUMS.txt'), encoding='ascii') as f:
    sums = {l.split()[0] for l in f if l.strip() and not l.startswith('#')}
cited = set(re.findall(r'\b[0-9A-F]{64}\b', rr))
for h in sorted(cited - sums):
    fails += 1
    print(f'FAIL sha256 in RATE-REQUEST.md not in SHA256SUMS.txt: {h}')
for h in sorted(sums - cited):
    fails += 1
    print(f'FAIL SHA256SUMS.txt hash missing from RATE-REQUEST.md: {h}')
if cited == sums:
    print(f'PASS sha256: RATE-REQUEST.md cites exactly the {len(sums)} SHA256SUMS.txt hashes')

for name, nums in (('native_worker.cpp', (6, 156, 202, 265, 337, 366, 380, 387, 388, 390, 637, 638)),
                   ('native_preparation.h', (18, 19, 35)),
                   ('native_recording.cpp', (113, 139, 174, 179, 530, 533))):
    for n in nums:
        print(f'  after/{name}:{n}: {files[name][n - 1].strip()[:110]}')
print('RESULT: ' + ('PASS' if fails == 0 else f'{fails} FAILED'))
sys.exit(1 if fails else 0)

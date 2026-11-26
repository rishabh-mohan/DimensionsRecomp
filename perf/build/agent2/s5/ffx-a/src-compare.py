#!/usr/bin/env python3
# src-compare.py (M2, S5 item 2): is snap1's rexglue-sdk source == SDK a7e79c0 for everything the option-A
# rexui fsyntax reads (src/ui, include/rex, cmake, CMakeLists)? Compares LF-normalised snap1 files with the
# a7e79c0 blobs. Read-only; writes build/agent2/s5/ffx-a/src-compare.txt.
import hashlib, os, subprocess, sys

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
SDK = os.path.join(R, 'DimensionsRecomp', 'rexglue-sdk')
SNAP = os.path.join(R, 'build', 'agent2', 'snap1', 'DimensionsRecomp', 'rexglue-sdk')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src-compare.txt')
prefixes = sys.argv[1:] or ['src/', 'include/', 'cmake/', 'CMakeLists.txt', 'CMakePresets.json',
                            'thirdparty/CMakeLists.txt']
ls = subprocess.run(['git', '-C', SDK, 'ls-tree', '-r', 'a7e79c0'], capture_output=True, text=True).stdout
diff, missing, same = [], [], 0
for ln in ls.splitlines():
    meta, path = ln.split('\t', 1)
    mode, typ, oid = meta.split()
    if typ != 'blob' or not any(path == p or path.startswith(p) for p in prefixes):
        continue
    f = os.path.join(SNAP, *path.split('/'))
    if not os.path.isfile(f):
        missing.append(path)
        continue
    b = open(f, 'rb').read()
    for cand in (b, b.replace(b'\r\n', b'\n')):
        if hashlib.sha1(b'blob %d\0' % len(cand) + cand).hexdigest() == oid:
            same += 1
            break
    else:
        diff.append(path)
lines = ['snap1 vs a7e79c0, prefixes %s' % prefixes, 'same %d, differ %d, missing %d' % (same, len(diff), len(missing))]
lines += ['DIFF ' + p for p in diff] + ['MISSING ' + p for p in missing]
open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
print('\n'.join(lines[:60]))

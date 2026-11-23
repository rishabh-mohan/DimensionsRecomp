#!/usr/bin/env python3
"""Agent 9 (task #17 item 1a): recompute the native GPU fingerprint of two native game trees and list the inputs that
differ. The fingerprint (rexlego/CMakeLists.txt:766-780, the configured generate-native-gpu-fingerprint.cmake) is
sha256(concat(file-sha256 hex of each input))[:16] over LEGO_NATIVE_GPU_FINGERPRINT_INPUTS, in list order. Its inputs
include rexlego/legodimensions_config.toml and 12 generated files, so a codegen change alone changes it.
  python build/agent9/fpcheck.py [--a-game build/agent2/snap1-on] [--a-snap build/agent2/snap1/DimensionsRecomp]
                                 [--b-game build/agent2/snapB3-on] [--b-snap build/agent2/snapB3/DimensionsRecomp]
                                 [--out build/agent9/logs/fpcheck-native.txt]
Exit 0: both recomputed fingerprints equal the recorded native-gpu-build.txt, the two input lists are the same paths in
the same order (relative to their snapshot/game roots), and every input that differs is a codegen input (the config TOML
or rexlego/generated/). Exit 1 otherwise. Read-only.
"""
import argparse
import hashlib
import os
import re
import sys
import time

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def norm(p):
    return os.path.normcase(os.path.normpath(p)).replace('\\', '/')


def inputs_of(game):
    with open(os.path.join(game, 'generate-native-gpu-fingerprint.cmake'), encoding='utf-8') as f:
        s = f.read()
    m = re.search(r'set\(LEGO_NATIVE_GPU_FINGERPRINT_INPUTS "([^"]*)"\)', s)
    if not m:
        sys.exit(f'no LEGO_NATIVE_GPU_FINGERPRINT_INPUTS list in {game}')
    return [x for x in m.group(1).split(';') if x]


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def scan(game, snap):
    g, sn = norm(game) + '/', norm(snap) + '/'
    rows, material, missing = [], '', 0
    for p in inputs_of(game):
        n = norm(p)
        rel = '<snap>/' + n[len(sn):] if n.startswith(sn) else ('<game>/' + n[len(g):] if n.startswith(g) else n)
        try:
            h, size = sha_file(p), os.path.getsize(p)
        except OSError:
            h, size, missing = 'MISSING', -1, missing + 1
        material += h
        rows.append((rel, h, size))
    fp = hashlib.sha256(material.encode('ascii')).hexdigest()[:16]
    with open(os.path.join(game, 'native-gpu-build.txt'), encoding='utf-8') as f:
        recorded = f.read().strip()
    return rows, fp, recorded, missing


def is_codegen(rel):
    return rel == '<snap>/rexlego/legodimensions_config.toml' or rel.startswith('<snap>/rexlego/generated/')


def main():
    ap = argparse.ArgumentParser()
    a2 = os.path.join(R, 'build', 'agent2')
    ap.add_argument('--a-game', default=os.path.join(a2, 'snap1-on'))
    ap.add_argument('--a-snap', default=os.path.join(a2, 'snap1', 'DimensionsRecomp'))
    ap.add_argument('--b-game', default=os.path.join(a2, 'snapB3-on'))
    ap.add_argument('--b-snap', default=os.path.join(a2, 'snapB3', 'DimensionsRecomp'))
    ap.add_argument('--out', default=os.path.join(R, 'build', 'agent9', 'logs', 'fpcheck-native.txt'))
    o = ap.parse_args()
    t0 = time.time()
    out = []

    def say(s=''):
        out.append(s)
        print(s)

    ok = True
    res = {}
    for k, game, snap in (('A', o.a_game, o.a_snap), ('B', o.b_game, o.b_snap)):
        rows, fp, recorded, missing = scan(game, snap)
        res[k] = rows
        match = recorded.split()[-1] == fp
        ok &= match and missing == 0
        say(f'{k} {os.path.relpath(game, R)} (snapshot {os.path.relpath(snap, R)}): {len(rows)} inputs, '
            f'{sum(r[2] for r in rows if r[2] > 0):,} B, missing {missing}; recomputed {fp}; recorded "{recorded}": '
            f'{"MATCH" if match else "DIFFERENT"}')
    ra, rb = res['A'], res['B']
    same_order = [r[0] for r in ra] == [r[0] for r in rb]
    ok &= same_order
    say(f'input lists: same relative paths in the same order: {same_order}')
    da, db = {r[0]: r for r in ra}, {r[0]: r for r in rb}
    only_a = [p for p in da if p not in db]
    only_b = [p for p in db if p not in da]
    diff = [p for p in da if p in db and da[p][1] != db[p][1]]
    ok &= not only_a and not only_b
    say(f'only in A: {len(only_a)} {only_a[:10]}')
    say(f'only in B: {len(only_b)} {only_b[:10]}')
    codegen_inputs = [p for p in da if is_codegen(p)]
    say(f'codegen inputs in the list: {len(codegen_inputs)}; inputs with a different sha256: {len(diff)} '
        f'({sum(1 for p in diff if is_codegen(p))} codegen, {sum(1 for p in diff if not is_codegen(p))} other)')
    for p in diff:
        say(f'  {"codegen" if is_codegen(p) else "OTHER  "}  {p}  A {da[p][2]:,} B {da[p][1][:16]}  '
            f'B {db[p][2]:,} B {db[p][1][:16]}')
    other = [p for p in diff if not is_codegen(p)]
    ok &= not other
    same_codegen = [p for p in codegen_inputs if p in db and da[p][1] == db[p][1]]
    say(f'codegen inputs with the same sha256: {len(same_codegen)} {same_codegen}')
    say(f'non-codegen inputs: {len(da) - len(codegen_inputs)}, all equal: {not other}')
    say(f'RESULT: {"PASS" if ok else "FAIL"} ({time.time() - t0:.1f}s)')
    os.makedirs(os.path.dirname(o.out), exist_ok=True)
    with open(o.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

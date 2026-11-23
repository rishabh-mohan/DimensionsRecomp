"""hookset.py (Agent 10, task #17 item 1a): the host hook set of two native link maps (native3d-bin vs
nativeB-bin). Read-only; one thread; writes only the --out report.

  python hookset.py --a MAP --b MAP [--src REXLEGO_SRC_DIR] [--out report.txt]

REX_HOOK / REX_HOOK_RAW (rexglue-sdk/include/rex/hook.h) define a strong sub_XXXXXXXX in a host object, so a
hooked guest function has its public sub_ in a non-generated object while __imp__sub_ stays in a generated TU
(legodimensions_recomp.N.cpp.obj) at another address. Per map this lists the hooked set with the defining host
object (both criteria: sub_ outside the TU objects, and __imp__ not at its sub_), the mid-asm hook functions
(NativeCelShading*, MissingAdventureTimeLookupNode, RepairDialogueLockReleaseOperand) with their objects, and the
LR-gated hooks of the native gate.
PASS when both maps have the same hooked set (name -> object, both criteria agree), every LR-gated hook is hooked
in both, and the mid-asm hook functions are present in both with the same objects. --src cross-references the
REX_HOOK targets of a source tree (informational: a source hook absent from a map is compiled out there).
"""
import argparse
import collections
import os
import re
import sys

SUB = re.compile(r'^sub_[0-9A-F]{8}$')
TU = re.compile(r'^legodimensions_recomp\.\d+\.cpp\.obj$')
MID = re.compile(r'(NativeCelShading\w+?|MissingAdventureTimeLookupNode|RepairDialogueLockReleaseOperand)(?=@|$|\()')
LRHOOKS = {
    'sub_83FC49E8': 'placement relocation line + pool-copy drain (caller 83F9B660)',
    'sub_82BD2868': 'CPU pool copy (lr 82BD2B44 caller test)',
    'sub_839C4D08': 'pause-menu Options rows (lr 839D11B0)',
    'sub_836F9E48': 'slot heap Register',
    'sub_82A3B6D8': 'slot heap (native_slot_growth)',
    'sub_82A57FE0': 'slot heap (native_slot_growth)',
}
SRC_RE = re.compile(r'^\s*REX_HOOK(?:_RAW)?\(\s*(\w+)', re.M)


def parse(path):
    pubs, state = [], 0
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            s = line.strip()
            if state == 0:
                if s.startswith('Address') and 'Publics by Value' in s:
                    state = 1
                continue
            if s.startswith('entry point at'):
                break
            p = s.split()
            if len(p) < 4 or ':' not in p[0]:
                continue
            sec, off = p[0].split(':')
            pubs.append((int(sec, 16), int(off, 16), p[1], p[-1]))
    return pubs


def summarize(pubs):
    # guest functions = every X with an __imp__X alias in a generated TU object: sub_XXXXXXXX and the
    # __savegprlr_N / __restgprlr_N / __savefpr_N / __restfpr_N helpers (native_saverest.cpp hooks those).
    names, guest, mids = {}, {}, collections.defaultdict(set)
    for sec, off, name, obj in pubs:
        if name.startswith('__imp__') and TU.match(obj):
            guest[name[7:]] = (sec, off, obj)
        elif not name.startswith('__imp_'):
            names[name] = (sec, off, obj)
            m = MID.search(name)
            if m:
                mids[m.group(1)].add((name, obj))
    by_obj = {n: names[n][2] for n in guest if n in names and not TU.match(names[n][2])}
    by_imp = {n for n, g in guest.items() if n in names and names[n][:2] != g[:2]}
    no_alias = sorted(n for n in guest if n not in names)
    no_imp = sorted(n for n, v in names.items() if SUB.match(n) and n not in guest)
    subs = sum(1 for n in names if SUB.match(n))
    return {'pubs': len(pubs), 'subs': subs, 'imps': len(guest), 'hooked': by_obj, 'by_imp': by_imp,
            'no_imp': no_imp + [f'{n} (no public)' for n in no_alias],
            'mids': {k: sorted(v) for k, v in mids.items()}}


def src_targets(d):
    out = {}
    for root, _, files in os.walk(d):
        for f in files:
            if f.endswith(('.cpp', '.h', '.inl')):
                p = os.path.join(root, f)
                with open(p, encoding='utf-8', errors='replace') as fh:
                    for m in SRC_RE.finditer(fh.read()):
                        out.setdefault(m.group(1), os.path.relpath(p, d))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--a', required=True)
    ap.add_argument('--b', required=True)
    ap.add_argument('--src')
    ap.add_argument('--out')
    o = ap.parse_args()
    A, B = summarize(parse(o.a)), summarize(parse(o.b))
    W = []
    w = W.append
    ok = True
    for tag, path, S in (('A', o.a, A), ('B', o.b, B)):
        agree = set(S['hooked']) == S['by_imp']
        ok &= agree
        w(f"{tag} {path}: {S['pubs']:,} publics, {S['subs']:,} sub_, {S['imps']:,} guest __imp__ aliases in TU "
          f"objects; hooked {len(S['hooked'])} (public in a host object) / {len(S['by_imp'])} (__imp__ not at its "
          f"public), criteria {'agree' if agree else 'DISAGREE'}; unpaired: {S['no_imp'] or 'none'}")
    ha, hb = A['hooked'], B['hooked']
    only_a, only_b = sorted(set(ha) - set(hb)), sorted(set(hb) - set(ha))
    moved = sorted(n for n in set(ha) & set(hb) if ha[n] != hb[n])
    same = not only_a and not only_b and not moved
    ok &= same
    w('')
    w(f"hooked set: {len(set(ha) & set(hb))} common, only in A {only_a or 'none'}, only in B {only_b or 'none'}, "
      f"object differs {[(n, ha[n], hb[n]) for n in moved] or 'none'} -> {'SAME' if same else 'DIFFERENT'}")
    objs = collections.Counter(ha.values())
    w('  hooks per host object (A): ' + ', '.join(f'{k} {v}' for k, v in sorted(objs.items())))
    w('')
    w('LR-gated hooks (name: purpose -> A object / B object):')
    for n, why in LRHOOKS.items():
        good = n in ha and n in hb and ha[n] == hb[n]
        ok &= good
        w(f"  {n}: {why} -> {ha.get(n, 'NOT HOOKED')} / {hb.get(n, 'NOT HOOKED')}  {'ok' if good else 'FAIL'}")
    w('')
    w('Mid-asm hook functions (name -> A / B, symbol @ object):')
    for n in sorted(set(A['mids']) | set(B['mids'])):
        ma, mb = A['mids'].get(n, []), B['mids'].get(n, [])
        good = bool(ma) and ma == mb
        ok &= good
        w(f"  {n}: {'SAME' if good else 'DIFFERENT'}  A {ma or 'absent'}" + ('' if good else f"  B {mb or 'absent'}"))
    if not A['mids'] and not B['mids']:
        ok = False
        w('  none found in either map')
    if o.src:
        st = src_targets(o.src)
        w('')
        w(f'source cross-reference ({o.src}): {len(st)} REX_HOOK/REX_HOOK_RAW targets')
        def in_src(n):  # a target ending in '_' is a token-pasting prefix (SAVEREST_HOOKS(n): __savegprlr_##n)
            return n in st or any(p.endswith('_') and n.startswith(p) for p in st)
        miss = sorted((n, st[n]) for n in st
                      if n not in ha and not (n.endswith('_') and any(h.startswith(n) for h in ha)))
        extra = sorted(n for n in ha if not in_src(n))
        pre = {p: sum(1 for h in ha if h.startswith(p)) for p in st if p.endswith('_')}
        w('  token-pasted prefixes, hooked count in A: ' + (', '.join(f'{p}* {c}' for p, c in sorted(pre.items()))
                                                          or 'none'))
        w(f'  in source, not hooked in A (compiled out or not a sub_): {miss or "none"}')
        w(f'  hooked in A, not a REX_HOOK target in this source dir (SDK or other host code): {extra or "none"}')
    w('')
    w(f"RESULT {'PASS' if ok else 'DIFFERENT'}")
    text = '\n'.join(W) + '\n'
    if o.out:
        with open(o.out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
    print(text)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

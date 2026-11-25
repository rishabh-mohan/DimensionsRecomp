"""rule_d.py - M12 helper: check an s4b_check output against Overseer standing rule (d)
(build/agent4/session3/ruling-r19-d.md 39BC0929) and compare its marks with other check files.

usage: python -B rule_d.py <row.check.txt> [--cmp <other.check.txt> ...]

Prints one line per condition (ok / BAD / info). Read-only. Exit 0 = rule (d) holds (or no LOOK),
1 = a condition fails (HOLD for the Overseer), 2 = usage / parse error.
"""
import re
import sys


def read(p):
    with open(p, 'rb') as f:
        b = f.read()
    enc = 'utf-16' if b[:2] in (b'\xff\xfe', b'\xfe\xff') else 'utf-8-sig'
    return b.decode(enc, errors='replace').splitlines()


def marks(lines):
    for ln in lines:
        if ln.startswith('  cand marks:'):
            return [tuple(kv.split('=', 1)) for kv in ln.split(':', 1)[1].split()]
    return None


def main(argv):
    if not argv or argv[0].startswith('-'):
        print(__doc__)
        return 2
    path, cmps = argv[0], []
    if '--cmp' in argv:
        cmps = argv[argv.index('--cmp') + 1:]
    L = read(path)
    txt = '\n'.join(L)
    bad = 0

    def R(ok, msg):
        nonlocal bad
        if not ok:
            bad += 1
        print(('ok   ' if ok else 'BAD  ') + msg)

    verdict = next((l for l in L if l.startswith('VERDICT')), None)
    if verdict is None:
        print('BAD  no VERDICT line')
        return 2
    print('     ' + verdict)
    m = re.search(r'(\d+) BASE misses, (\d+) proof misses', verdict)
    base_miss, proof = (int(m.group(1)), int(m.group(2))) if m else (None, None)
    R(proof == 0, f'proof misses {proof}')
    bim = next((l for l in L if l.startswith('BASE items missed:')), '')
    only_marks = base_miss == 0 or (base_miss == 1 and bim.startswith('BASE items missed: marks differ'))
    R(only_marks, f'only BASE miss is mark scene ids: {bim[:160]}')
    # s4b_check does not judge scenes/marks/GONE when the base is another scenario (title vs menu)
    differs = 'base scenario differs' in bim
    rj = next((l for l in L if l.startswith('run.json:')), '')
    st = re.search(r'steps (\d+)/(\d+)', rj)
    unscripted = st is None and marks(L) is None  # title/idle routes: no steps, no marks
    if unscripted:
        print('n/a  route steps None (unscripted run: no steps, no marks)')
    else:
        R(bool(st) and st.group(1) == st.group(2), f'route steps {st.group(0) if st else None}')
    ld = next((l for l in L if l.startswith('logdiff vs')), '')
    g = lambda k: (re.search(k, ld) or [None, None])[1]
    new, more, flag = g(r'NEW (\d+) \('), g(r'MORE (\d+) \('), g(r'FLAG (\d+)')
    unexp = g(r'GONE \d+ \((\d+) unexpected\)')
    R(new == '0', f'NEW {new} beyond allow-new')
    # ruling (e): allow-new patterns are matched on normalised lines (digits -> #); quote allowed NEW verbatim
    allowed = g(r'NEW \d+ \(\+(\d+) allowed\)')
    info_allowed = g(r'NEW at info \d+ other, (\d+) allowed')
    print(f'     allowed NEW {allowed}, info allowed groups {info_allowed} (normalised match):')
    for l in L:
        if l.startswith('  allowed NEW') or l.startswith('  info allowed NEW'):
            print('       ' + l.strip())
    if new not in ('0', None) and any('d#d#_' in l for l in L if l.startswith('  ') and 'NEW' in l and 'allowed' not in l):
        print('NOTE NEW includes a d#d#_ line: check that the allow-new pattern was given in normalised form (ruling e)')
    R(more == '0', f'MORE {more}')
    R(flag == '0', f'FLAG {flag}')
    if differs:
        print(f'n/a  unexpected GONE {unexp} (not judged: base scenario differs)')
    else:
        R(unexp == '0', f'unexpected GONE {unexp}')
    sm = next((l for l in L if l.startswith('summary:')), '')
    er = re.search(r'errors (\d+)', sm)
    lv = re.search(r'levels (\{[^}]*\})', sm)
    crit = bool(lv) and ('"error"' in lv.group(1) or '"critical"' in lv.group(1))
    R(bool(er) and er.group(1) == '0' and not crit, f'errors {er.group(1) if er else None}; levels {lv.group(1) if lv else None}')
    rm = next((l for l in L if l.startswith('route marks')), '')
    print('     ' + rm[:300])
    cm = marks(L)
    for c in cmps:
        om = marks(read(c))
        if cm is None or om is None:
            if unscripted:
                print(f'n/a  no marks in row (unscripted), vs {c}')
                continue
            R(False, f'marks missing (row {cm is not None}, {c} {om is not None})')
            continue
        names_same = [k for k, _ in cm] == [k for k, _ in om]
        R(names_same, f'mark names/order identical vs {c}')
        diff = [f'{k} {v2}->{v}' for (k, v), (_, v2) in zip(cm, om) if v != v2]
        print(f'     vs {c}: {len(diff)} of {len(cm)} ids differ: ' + ' '.join(diff))
    print(f'RULE-D: {"HOLDS" if bad == 0 else f"FAILS ({bad})"}')
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

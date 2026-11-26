#!/usr/bin/env python3
# e6_roles.py - M16 (S5), build/agent16/cg7: INFORMATION-ONLY by-role report of the late missing draws for step E
# (cand6 zone). It is not a proof tool and gates nothing: E is judged by proof5_post v3 + M10's E-C2..E-C6
# (build\agent10\s5\cand6-kit-rating-E-go.md 07629957). Static and read-only on its inputs; writes ONLY <--out>
# (a NEW dir under build\agent16\cg7). Exit 0 = report written, 2 = refused.
#
#   python -B build\agent16\cg7\e6_roles.py --trace <trace dir\events.tsv> --log <run dir\game.log>
#          [--runlog <kit logs\gameplay-<stamp>.txt>] [--fp e5c874ca2b87a59d] [--label cand6]
#          --out build\agent16\cg7\roles-<stamp>
#
# Why by role: guest addresses move between runs (073150 VS AB64C0E0 = 082648 VS ABA99710), so a role is defined
# by stage + timing, not by address ("similar times, matched by shape not key").
#   red      : first game.log `Toypad: pad 1 mode 3 lit FF 00 00 (... speed 18)` line, converted to trace ms through
#              trace-start.json (same rule as dump6_post / proof5_post).
#   miss row : draw_missing_vertex_shader (guest_vs) or draw_missing_pixel_shader (guest_ps).
#   E-C4     : per-window miss rows (M10's windows): W1a red+40..59 s, W1b red+59..65 s, W2 red+65 s..stop.
#   role     : every (stage, guest) with a miss row at >= red + 40 s gets the role whose [lo, hi) range (seconds after
#              red) holds its FIRST such row. Roles are named by their 082648 (B) VS; ranges from the two reference
#              runs (073150 base, 082648 B):
#                A-AB7D1200 [43.0, 44.0)  073150 VS AB80F350 / PS AB77B580 +43.5; B VS AB7D1200 / PS AB854C80 +43.5
#                U-ABA99710 [44.0, 45.0)  073150 VS AB64C0E0 / PS ABB3F110 +44.5; B VS ABA99710 / PS ABB41A90 +44.5
#                C-A7F79FD0 [58.0, 77.0)  073150 VS A7F7A100 / PS A7F79ED0 +75.7; B VS A7F79FD0 / PS A7F79DA0 +59.0
#              No range -> OTHER (no role). Miss rows before red + 40 s are counted apart as PRE.
#   class    : per role and stage, from the B identities packed into native6pack (stage6 NEW set):
#                known uncovered VS, no identity in B = U-ABA99710 VS (E FAIL, expected risk);
#                covered role = A VS 56F18006 / PS E566393A, U PS 6EE915B0, C VS F976B389 / PS 4DB01A8D
#                (a miss here is an E FAIL with high priority: pack or lookup problem);
#                OTHER = no role (new).
#   checks   : (information) DUP = two guests of one stage in one role; backing (from game.log `placement ...
#              shader 0x<g> backing 0x<p> ... missing from AOT index` lines, capped at 16 in the game, and from
#              missing_placement_shader_identity events if any) vs the reference backings: AGREES / CONFLICT (another
#              role's reference) / unknown-ref.
#   hygiene  : (E-C6 part) game.log `shader miss cache ON|OFF` line; DIAGNOSTIC lines in --runlog (if given).
# The summary lines (E-C4 / ROLES / CLASS / HYGIENE / FLAGS) are information; no RESULT line, no PASS/FAIL.
import argparse, collections, ctypes, datetime, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CG7 = os.path.join(W, 'build', 'agent16', 'cg7')
ST = {6: 'VS', 7: 'PS'}
KV = re.compile(r'(\w+)=\s*(\d+)')
RED = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\].*Toypad: pad 1 mode 3 lit FF 00 00 \(.*speed 18\)')
BACK = re.compile(r'placement (vertex|pixel) shader 0x([0-9A-Fa-f]{8}) backing 0x([0-9A-Fa-f]{8})'
                  r'(?: prefix=0x([0-9A-Fa-f]{16}))?.*missing from AOT index')
MCACHE = re.compile(r'Native GPU: shader miss cache (ON|OFF)\b')
ROLES = [('A-AB7D1200', 43.0, 44.0), ('U-ABA99710', 44.0, 45.0), ('C-A7F79FD0', 58.0, 77.0)]
UNCOVERED = 'known uncovered VS, no identity in B'
COVER = {('A-AB7D1200', 6): 'covered (B container 56F18006)', ('A-AB7D1200', 7): 'covered (B container E566393A)',
         ('U-ABA99710', 6): UNCOVERED, ('U-ABA99710', 7): 'covered (B container 6EE915B0)',
         ('C-A7F79FD0', 6): 'covered (B container F976B389)', ('C-A7F79FD0', 7): 'covered (B container 4DB01A8D)'}
# reference backings: 082648 identity events + game.log lines of 073150 and 082648 (A VS/PS in both runs)
REFBACK = {(6, 0xED25B6A0): 'A-AB7D1200', (7, 0xED25B8E0): 'A-AB7D1200', (7, 0xED25BC80): 'U-ABA99710',
           (6, 0xED65D8C0): 'C-A7F79FD0', (7, 0xED65DAE0): 'C-A7F79FD0'}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def red_ms(log, trace):
    tsj = os.path.join(os.path.dirname(os.path.abspath(trace)), 'trace-start.json')
    unix_ms = json.load(open(tsj))['unix_ms']
    for l in open(log, encoding='utf-8', errors='replace'):
        m = RED.match(l)
        if m:
            t = datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f')
            return t.timestamp() * 1000.0 - unix_ms, m.group(1), unix_ms
    return None, None, unix_ms


def scan(path):
    """One streaming pass: frames, inserts, miss rows per (stage, guest), unrecognized counts, identity backings."""
    frames, last_ms, inserts = 0, None, 0
    miss = collections.defaultdict(list)     # (stage, guest) -> [ms of each miss row]
    unrec = collections.Counter()            # (stage, guest) -> unrecognized_shader rows
    idback = {}                              # (stage, guest) -> physical, from identity events
    with open(path, 'rb') as f:
        for l in f:
            p = l.rstrip(b'\r\n').split(b'\t', 4)
            if len(p) < 5:
                continue
            e = p[2]
            try:
                ts = float(p[0])
            except ValueError:
                continue
            if e == b'frame':
                frames += 1
                last_ms = ts
                continue
            if e == b'shader_miss_cache_insert':
                inserts += 1
                continue
            if e not in (b'unrecognized_shader', b'draw_missing_vertex_shader', b'draw_missing_pixel_shader',
                         b'missing_placement_shader_identity'):
                continue
            d = dict((k, int(v)) for k, v in KV.findall(p[4].decode('ascii', 'replace')))
            if e == b'missing_placement_shader_identity':
                if d.get('stage') in ST and 'guest' in d and 'physical' in d:
                    idback.setdefault((d['stage'], d['guest']), d['physical'])
            elif e == b'unrecognized_shader':
                if d.get('stage') in ST and 'guest' in d:
                    unrec[(d['stage'], d['guest'])] += 1
            else:
                st = 6 if e == b'draw_missing_vertex_shader' else 7
                g = d.get('guest_vs' if st == 6 else 'guest_ps')
                if g is not None:
                    miss[(st, g)].append(ts)
    return dict(frames=frames, last_ms=last_ms, inserts=inserts, miss=miss, unrec=unrec, idback=idback)


def main():
    if os.name == 'nt':
        k = ctypes.windll.kernel32
        k.SetPriorityClass(k.GetCurrentProcess(), 0x00100000)  # background mode (Idle + low I/O), as proof5
    ap = argparse.ArgumentParser()
    for n in ('--trace', '--log', '--out'):
        ap.add_argument(n, required=True)
    ap.add_argument('--runlog')
    ap.add_argument('--fp')
    ap.add_argument('--label', default='run')
    a = ap.parse_args()
    w1, w1b, w2 = 40.0, 59.0, 65.0
    out = os.path.abspath(a.out)
    if not os.path.normcase(out).startswith(os.path.normcase(CG7) + os.sep) or os.path.exists(out):
        print('REFUSED: --out must be a new dir under %s' % CG7)
        return 2
    if a.fp is not None and not re.fullmatch(r'[0-9a-f]{16}', a.fp):
        print('REFUSED: --fp must be 16 lowercase hex')
        return 2
    if not re.fullmatch(r'[\w.-]+', a.label):
        print('REFUSED: --label must be [A-Za-z0-9_.-]')
        return 2
    ts_json = os.path.join(os.path.dirname(os.path.abspath(a.trace)), 'trace-start.json')
    ins = [('trace', a.trace), ('trace-start', ts_json), ('game.log', a.log)]
    if a.runlog:
        ins.append(('runlog', a.runlog))
    miss_in = [p for _, p in ins if not os.path.isfile(p)]
    if miss_in:
        print('REFUSED: missing input(s): %s' % '; '.join(miss_in))
        return 2

    L = []
    w = L.append
    w('e6_roles.py sha256 %s  (INFORMATION ONLY: not a proof tool; E is judged by proof5_post v3 + E-C2..E-C6)'
      % sha(os.path.abspath(__file__)))
    w('label %s' % a.label)
    for tag, p in ins:
        w('%-11s %s %s' % (tag, sha(p), os.path.abspath(p)))
    logtxt = open(a.log, encoding='utf-8', errors='replace').read()
    flags = []
    if a.fp:
        fpok = ('Native GPU [%s]' % a.fp) in logtxt
        w('fingerprint %s in game.log: %s' % (a.fp, fpok))
        if not fpok:
            flags.append('FP-MISSING')
    mc = sorted(set(MCACHE.findall(logtxt)))
    mcs = '/'.join(mc) if mc else 'not found'
    if 'OFF' in mc:
        flags.append('MISS-CACHE-OFF')
    if a.runlog:
        diag = [l for l in open(a.runlog, encoding='utf-8', errors='replace') if 'DIAGNOSTIC' in l]
        ds = '%d' % len(diag)
        if diag:
            flags.append('DIAGNOSTIC')
    else:
        ds = 'runlog not given'
    hyg = 'HYGIENE (E-C6 part): game.log shader miss cache %s; runlog DIAGNOSTIC lines %s' % (mcs, ds)
    red, red_wall, unix_ms = red_ms(a.log, a.trace)
    w('trace start unix_ms %d (%s local)' % (unix_ms, datetime.datetime.fromtimestamp(unix_ms / 1000.0)))
    w('red start (game.log, first pad 1 FF 00 00 speed 18): %s -> trace %s ms' % (
        red_wall, '%.1f' % red if red is not None else 'NOT FOUND'))
    w('role rule (first miss row at >= red+40 s, seconds after red, [lo, hi)): %s' % ', '.join(
        '%s [%.1f, %.1f)' % r for r in ROLES))
    if red is None:
        lines = ['ROLES: NO-RED (no red-18 start in game.log; nothing assigned)', hyg,
                 'FLAGS: %s' % (', '.join(flags) if flags else 'none')]
        L.extend(lines)
        return finish(out, L, lines)

    R = scan(a.trace)
    stop = R['last_ms'] if R['last_ms'] is not None else red
    rel = lambda t: (t - red) / 1000.0
    w('trace: frames %d; stop (last frame) red%+.1f s; miss-cache inserts %d' % (R['frames'], rel(stop),
                                                                               R['inserts']))
    back = {}
    for mb in BACK.finditer(logtxt):
        back.setdefault((6 if mb.group(1) == 'vertex' else 7, int(mb.group(2), 16)), int(mb.group(3), 16))
    for k_, v in R['idback'].items():
        back.setdefault(k_, v)
    w('backings known (game.log lines + identity events): %d' % len(back))

    t1, tb, t2 = red + 1000.0 * w1, red + 1000.0 * w1b, red + 1000.0 * w2
    winof = lambda t: 'W1a' if t < tb else 'W1b' if t < t2 else 'W2'
    pre = sum(1 for v in R['miss'].values() for t in v if t < t1)
    w('PRE: miss rows before red+%.0f s: %d' % (w1, pre))
    win = collections.Counter()
    byrole = collections.OrderedDict((n, []) for n, _, _ in ROLES)
    byrole['OTHER'] = []
    for (st, g), ts in R['miss'].items():
        late = [t for t in ts if t >= t1]
        if not late:
            continue
        win.update(winof(t) for t in late)
        f0 = rel(late[0])
        role = next((n for n, lo, hi in ROLES if lo <= f0 < hi), 'OTHER')
        byrole[role].append((st, g, late))

    w('')
    w('per role (stage guest: miss rows at >= red+40 s [W1a / W1b / W2], unrecognized rows, first..last red+s, '
      'backing)')
    summ, cls = [], {'unc': 0, 'cov': 0, 'oth': 0}
    covlist = []
    for role, items in byrole.items():
        nv = sum(len(x[2]) for x in items if x[0] == 6)
        np_ = sum(len(x[2]) for x in items if x[0] == 7)
        w('  %s: VS misses %d, PS misses %d' % (role, nv, np_))
        for st, n_ in ((6, nv), (7, np_)):
            c = COVER.get((role, st), 'OTHER (no role)')
            w('    %s class: %s' % (ST[st], c))
            key = 'unc' if c == UNCOVERED else 'cov' if c.startswith('covered') else 'oth'
            cls[key] += n_
            if key == 'cov' and n_:
                covlist.append('%s %s %d' % (role, ST[st], n_))
        for st, g, late in sorted(items, key=lambda x: (x[0], x[2][0])):
            b = back.get((st, g))
            if b is None:
                bt = 'backing unknown'
            else:
                ref = REFBACK.get((st, b))
                bt = 'backing %08X %s' % (b, 'unknown-ref' if ref is None else
                                          'AGREES (%s ref)' % ref if ref == role else 'CONFLICT (%s ref)' % ref)
                if ref is not None and ref != role:
                    flags.append('BACKING-CONFLICT %s %s %08X' % (role, ST[st], g))
            wc = collections.Counter(winof(t) for t in late)
            w('    %s %08X: %d [%d / %d / %d], %d, %+.1f..%+.1f, %s' % (
                ST[st], g, len(late), wc['W1a'], wc['W1b'], wc['W2'], R['unrec'].get((st, g), 0), rel(late[0]),
                rel(late[-1]), bt))
        for s_ in (6, 7):
            if role != 'OTHER' and sum(1 for x in items if x[0] == s_) > 1:
                flags.append('DUP %s %s' % (role, ST[s_]))
        summ.append('%s %d (VS %d, PS %d)' % (role, nv + np_, nv, np_))
    total = sum(win.values())
    w('')
    lines = [
        'E-C4 windows: W1a red+40..59 s %d; W1b red+59..65 s %d; W2 red+65 s..stop %d; TOTAL at >= red+40 s %d; '
        'PRE %d; stop red%+.1f s' % (win['W1a'], win['W1b'], win['W2'], total, pre, rel(stop)),
        'ROLES: ' + '; '.join(summ),
        'CLASS: %s (U-ABA99710 VS) %d; covered-role misses (high priority) %d%s; OTHER (no role) %d' % (
            UNCOVERED, cls['unc'], cls['cov'], ' [%s]' % ', '.join(covlist) if covlist else '', cls['oth']),
        hyg,
        'FLAGS: %s' % (', '.join(flags) if flags else 'none'),
    ]
    L.extend(lines)
    return finish(out, L, lines)


def finish(out, L, lines):
    os.makedirs(out)
    rp = os.path.join(out, 'e6_roles.txt')
    with open(rp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    for l in lines:
        print(l)
    print('report %s %s' % (rp, sha(rp)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

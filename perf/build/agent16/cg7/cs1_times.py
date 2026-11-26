#!/usr/bin/env python3
# cs1_times.py - M16 (S5), build/agent16/cg7: INFORMATION-ONLY helper for M10's C-S1 (dump6-stepC-rating B0A9B0C6).
# Does not change dump6_post.py (7887B90A) or its RESULT. Read-only on its inputs; writes only --out (a new file
# under build\agent16\cg7).
#
#   python -B build\agent16\cg7\cs1_times.py --report <post dir\dump6_post.txt> --trace <events.tsv> --out <file>
#
# Per D3 target that dump6_post matched, it prints:
#   - the window first row (as dump6_post shows it: clipped at the window start) and the TRUE first row of that
#     (stage, guest) anywhere in the trace (one streaming pass, same row kinds as dump6_post: unrecognized_shader
#     stage/guest, draw_missing_vertex_shader guest_vs, draw_missing_pixel_shader guest_ps);
#   - every matching identity event and its time (red+s);
#   - C-S1 flag: a guest match counts only if some matching identity is at >= first row - 1 s; a backing match counts.
#     Judged both against the true first row (EARLY-TRUE) and the window first row (EARLY-WIN).
#   - CAP: identity events >= 256 (capture cap) -> every guest match flagged CAP.
# Summary: whether COVERED would stand under C-S1 (any EARLY or CAP on a needed match -> PARTIAL).
import argparse, ctypes, hashlib, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
KV = re.compile(r'(\w+)=\s*(\d+)')
RED = re.compile(r'-> trace ([\d.]+) ms')
IDN = re.compile(r'^\s+(VS|PS) guest ([0-9A-F]{8}) physical ([0-9A-F]{8}) vb \d+ pb \d+ container ([0-9A-F]{16}) '
                 r'physical_hash [0-9A-F]{16} at red([+-][\d.]+) s$')
WIN = re.compile(r'^D3 (W[12]) targets')
TGT = re.compile(r'^\s+(VS|PS) ([0-9A-F]{8}): (\d+), (\d+), ([+-][\d.]+)\.\.([+-][\d.]+)\s+(.*)$')
HOW = re.compile(r'^MATCHED by (guest|backing ([0-9A-F]{8})) -> container (.*)$')
CAPN = 256


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def main():
    k = ctypes.windll.kernel32
    k.SetPriorityClass(k.GetCurrentProcess(), 0x00100000)  # background mode, as dump6_post
    ap = argparse.ArgumentParser()
    for n in ('--report', '--trace', '--out'):
        ap.add_argument(n, required=True)
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    if not os.path.normcase(out).startswith(os.path.normcase(HERE) + os.sep) or os.path.exists(out):
        print('REFUSED: --out must be a new file under %s' % HERE)
        return 2
    rep = open(a.report, encoding='utf-8', errors='replace').read().splitlines()
    red = None
    ids, tg, win = [], [], None
    nid = None
    for l in rep:
        m = RED.search(l)
        if m and red is None and l.startswith('red start'):
            red = float(m.group(1))
        m = re.match(r'^identity events: (\d+)', l)
        if m:
            nid = int(m.group(1))
        m = IDN.match(l)
        if m:
            ids.append((m.group(1), int(m.group(2), 16), int(m.group(3), 16), m.group(4), float(m.group(5))))
        m = WIN.match(l)
        if m:
            win = m.group(1)
            continue
        if l.lstrip().startswith('pairs') or not l.strip():
            win = None  # target block ends at the pairs table or a blank line
        m = TGT.match(l) if win else None
        if m:
            tg.append((win, m.group(1), int(m.group(2), 16), float(m.group(5)), m.group(7)))
    if red is None:
        print('REFUSED: no red trace ms in the report')
        return 2
    want = {(6 if s == 'VS' else 7, g) for _, s, g, _, _ in tg}
    first = {}
    with open(a.trace, 'rb') as f:
        for l in f:
            p = l.rstrip(b'\r\n').split(b'\t', 4)
            if len(p) < 5 or p[2] not in (b'unrecognized_shader', b'draw_missing_vertex_shader',
                                          b'draw_missing_pixel_shader'):
                continue
            d = dict((kk, int(v)) for kk, v in KV.findall(p[4].decode('ascii', 'replace')))
            if p[2] == b'unrecognized_shader':
                key = (d.get('stage'), d.get('guest'))
            elif p[2] == b'draw_missing_vertex_shader':
                key = (6, d.get('guest_vs'))
            else:
                key = (7, d.get('guest_ps'))
            if key in want and key not in first:
                try:
                    first[key] = (float(p[0]) - red) / 1000.0
                except ValueError:
                    continue
                if len(first) == len(want):
                    break
    L = ['cs1_times.py sha256 %s (information only; dump6_post RESULT unchanged)' % sha(os.path.abspath(__file__)),
         'report %s %s' % (sha(a.report), os.path.abspath(a.report)),
         'trace  %s' % os.path.abspath(a.trace),
         'identity events %s (capture cap %d): %s' % (nid, CAPN, 'CAP' if nid is not None and nid >= CAPN else 'below cap'),
         '']
    cap = nid is not None and nid >= CAPN
    bad_t, bad_w, nm = [], [], 0
    for w_, s, g, wfirst, rest in tg:
        st = 6 if s == 'VS' else 7
        tf = first.get((st, g))
        m = HOW.match(rest)
        if not m:
            L.append('%s %s %08X: UNMATCHED; window first red%+.1f s, true first %s' % (
                w_, s, g, wfirst, 'red%+.1f s' % tf if tf is not None else '?'))
            continue
        nm += 1
        if m.group(1) == 'guest':
            hits = [x for x in ids if x[0] == s and x[1] == g]
            how = 'guest'
        else:
            ph = int(m.group(2), 16)
            hits = [x for x in ids if x[0] == s and x[2] == ph]
            how = 'backing %08X' % ph
        tl = ', '.join('%s@red%+.1f' % (x[3], x[4]) for x in hits) or 'none listed'
        if how == 'guest':
            ok_t = tf is not None and any(x[4] >= tf - 1.0 for x in hits)
            ok_w = any(x[4] >= wfirst - 1.0 for x in hits)
            flags = [f for f, c in (('EARLY-TRUE', not ok_t), ('EARLY-WIN', not ok_w), ('CAP', cap)) if c]
            if not ok_t or cap:
                bad_t.append('%s %s %08X' % (w_, s, g))
            if not ok_w or cap:
                bad_w.append('%s %s %08X' % (w_, s, g))
        else:
            flags = ['backing (counts)']
        L.append('%s %s %08X: window first red%+.1f s, true first %s; matched by %s; identities %s; %s' % (
            w_, s, g, wfirst, 'red%+.1f s' % tf if tf is not None else '?', how, tl, ' '.join(flags) or 'OK'))
    L.append('')
    L.append('C-S1 summary: %d target(s), %d matched; flagged vs true first row: %d%s; vs window first row: %d%s' % (
        len(tg), nm, len(bad_t), (' (' + ', '.join(bad_t) + ')') if bad_t else '', len(bad_w),
        (' (' + ', '.join(bad_w) + ')') if bad_w else ''))
    L.append('C-S1 reading: a COVERED/W-COVERED claim stands only for windows with no flagged match; otherwise PARTIAL.')
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L))
    print('out %s %s' % (out, sha(out)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

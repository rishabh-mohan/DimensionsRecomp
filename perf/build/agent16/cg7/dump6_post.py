#!/usr/bin/env python3
# dump6_post.py - M16 (S5), build/agent16/cg7: post for the dump6 capture run (PLAN-dump6 step C, M10 rating 5749F60E).
# Static and read-only on its inputs; writes ONLY <--out> (a NEW dir under build\agent16\cg7). Exit 2 = refused.
#
#   python -B build\agent16\cg7\dump6_post.py --trace <trace dir\events.tsv> --log <run dir\game.log>
#          --post <M3 post\gameplay-<stamp>.txt> --runlog <M3 logs\gameplay-<stamp>.txt>
#          --sidecar <M3 logs\<stamp>-native.sidecar.out.txt> [--dump-dir <kit\shader-dumps-native-<stamp>>]
#          [--fp a349d5292f67b127] [--root-vs <vs-A58EBA123EFB541C.bin>] [--noident <noident.txt>]
#          --out build\agent16\cg7\post-<stamp>
#
# D1 route   : the proof5 v3 anchors unchanged (clean exit 0, steps 302/302 + last: done, title gate = route L55
#              wait ok, prompts exactly 1/1 each, all kit exits 0) + zone=done in the sidecar result line + a red
#              start (game.log, first `Toypad: pad 1 mode 3 lit FF 00 00 (... speed 18)`). ctl is reported only.
# D2 reach   : stop (last trace frame) >= red + 80 s. W2 coverage seconds reported apart; < 80 s = W2 NOT-REACHED.
# D3 cover   : targets = VS and PS guests of unrecognized_shader / draw_missing_* rows at >= red + 40 s, by window
#              (W1 = red+40..red+65 s, W2 = red+65 s..stop). A target is matched by a missing_placement_shader_identity
#              event of the same stage with the same guest, or with physical == the target's backing address from a
#              game.log `placement ... shader 0x<guest> backing 0x<phys> ... missing from AOT index` line (capped at
#              16 lines). physical_hash only joins identity events to each other (listed); it NEVER covers a target.
#              v2 (B-N1 + C-S1, M10 dump6-stepC-rating B0A9B0C6 / dump6-B-review 2090CDB5): each target line also gives
#              its TRUE first row (any unrecognized_shader / draw_missing_* row of that stage+guest anywhere in the
#              trace, not clipped at the window start) and every matching identity time. A guest match is C-S1 OK
#              only if some matching identity is at >= true first row - 1 s (else EARLY); a backing match is OK at any
#              time. CAP: identity events >= 256 (the capture cap) flags EVERY match. A flagged match is still
#              listed as matched, but its window and the RESULT can be at most PARTIAL.
# D4 files   : per identity: placement-containers\{vs,ps}-<container_hash:016X>.bin exists, size == virtual_bytes +
#              4 + physical_bytes, the 4 marker bytes == virtual header bytes 8..11, sha256 listed. No xxhash module
#              is installed, so container_hash itself is NOT recomputed (name + size + marker + sha256 only).
# D5         : identity events before red + 40 s (expect 0); listed and flagged against the 22-noident list.
# D6 (info)  : each VS identity's physical section (container bytes [virtual_bytes+4:]) vs root vs-A58EBA12
#              physical bytes 304..703. Information only: the root is never packed (D-C2).
# D7 (info)  : placement-raw files are keyed by microcode prefix and never overwritten (snap1 9567FE3F L202-204,
#              L587-589): expect unique (stage, prefix) files, <= 1 per stage for the zero bucket, not 1 per
#              identity. Root files: expect the 2 boot files (ps-93B9F93B535E7CCA, vs-A58EBA123EFB541C); others listed.
# RESULT, first match wins: INVALID (--fp given and not in game.log) | INCONCLUSIVE (D1 failed, or no target rows
#              at >= red + 40 s) | NOT-REACHED (D2 failed) | COVERED (every VS and PS target matched, no C-S1 flag,
#              AND D4 passed) | PARTIAL (some targets matched, or all matched but D4 failed or a match is C-S1
#              flagged) | NOT-COVERED (no target matched).
#              Plus a W1/W2 split line. Exit 0 for COVERED, 1 otherwise, 2 = refused.
import argparse, collections, ctypes, datetime, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CG7 = os.path.join(W, 'build', 'agent16', 'cg7')
ROOT_VS = os.path.join(W, 'build', 'agent3', 'gameplay', 'shader-dumps-native-20261126-051154',
                       'vs-A58EBA123EFB541C.bin')
NOIDENT = os.path.join(CG7, 'data', 'noident.txt')
BOOT = {'ps-93B9F93B535E7CCA.bin', 'vs-A58EBA123EFB541C.bin'}
ST = {6: 'VS', 7: 'PS'}
KV = re.compile(r'(\w+)=\s*(\d+)')
RED = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\].*Toypad: pad 1 mode 3 lit FF 00 00 \(.*speed 18\)')
BACK = re.compile(r'placement (vertex|pixel) shader 0x([0-9A-Fa-f]{8}) backing 0x([0-9A-Fa-f]{8})'
                  r'(?: prefix=0x([0-9A-Fa-f]{16}))?.*missing from AOT index')
SIDE_RED = re.compile(r'^(\d\d:\d\d:\d\d\.\d{3}) alert pad 1 lit FF 00 00 speed 18')
CAPN = 256                                  # process-wide capture cap (snap1 shaders.cpp 9567FE3F L161, L192)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def txt(p):
    return open(p, encoding='utf-8', errors='replace').read()


def route_checks(post, runlog, sidecar):
    """proof5 v3 anchors (unchanged) + zone=done. Returns ([(name, ok)], sidecar result line)."""
    P, R = txt(post), txt(runlog)
    res = [l for l in txt(sidecar).splitlines() if re.match(r'^\S+ result ', l)]
    S = res[-1] if res else ''
    return [
        ('clean exit 0', 'PASS native clean exit: exit 0x00000000' in P),
        ('steps 302/302', 'steps 302/302 stopped_by_script True error None' in P),
        ('stop reached (last: done)', re.search(r'steps 302/302 \(last: done\)', R) is not None),
        ('title gate HIT', re.search(r'wait line 55 current=5 pending=0 \d+ +ok after', P) is not None),
        ('prompts 3/3', re.search(r'(?:^|\s)prompts=batman:1/1 gandalf:1/1 wyldstyle:1/1(?=\s|$)', S) is not None),
        ('kit exits 0', all(s in R for s in ('run-game (native) exit 0', 'sidecar exit 0', 'holdwatch exit 0',
                                             'watcher exit 0', 'GAMEPLAY DONE: run-game exit 0; post exit 0'))),
        ('zone=done', re.search(r'(?:^|\s)zone=done(?=\s|$)', S) is not None),
    ], S


def scan(path, red, w1lo, w2lo):
    """One streaming pass. Rows at >= red + w1lo s are assigned to W1 (< red + w2lo s) or W2."""
    t1, t2 = red + 1000.0 * w1lo, red + 1000.0 * w2lo
    frames, last_ms, last_fr, inserts, early_miss = 0, None, None, 0, 0
    targets = {'W1': {}, 'W2': {}}          # win -> (stage, guest) -> [unrec rows, draw_missing rows, first ms, last ms]
    pairs = {'W1': {}, 'W2': {}}            # win -> (last VS, last PS) -> [draws, VSmiss, PSmiss, first ms, last ms]
    last = {6: None, 7: None}
    idents = []
    allfirst = {}                           # (stage, guest) -> first row ms anywhere in the trace (B-N1)
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
                last_ms, last_fr = ts, p[1].decode('ascii', 'replace')
                continue
            if e == b'shader_miss_cache_insert':
                inserts += 1
                continue
            if e not in (b'unrecognized_shader', b'draw_missing_vertex_shader', b'draw_missing_pixel_shader',
                         b'missing_placement_shader_identity'):
                continue
            d = dict((k, int(v)) for k, v in KV.findall(p[4].decode('ascii', 'replace')))
            if e == b'missing_placement_shader_identity':
                d['ms'] = ts
                idents.append(d)
                continue
            if e == b'unrecognized_shader':
                st, g = d.get('stage'), d.get('guest')
                if st not in ST or g is None:
                    continue
                last[st] = g
            else:
                st = 6 if e == b'draw_missing_vertex_shader' else 7
                g = d.get('guest_vs' if st == 6 else 'guest_ps')
                if g is None:
                    continue
            allfirst.setdefault((st, g), ts)
            if ts < t1:
                if e != b'unrecognized_shader':
                    early_miss += 1
                continue
            win = 'W1' if ts < t2 else 'W2'
            r = targets[win].setdefault((st, g), [0, 0, ts, ts])
            r[0 if e == b'unrecognized_shader' else 1] += 1
            r[3] = ts
            if e != b'unrecognized_shader':
                q = pairs[win].setdefault((last[6], last[7]), [0, 0, 0, ts, ts])
                q[0] += 1
                q[1 if st == 6 else 2] += 1
                q[4] = ts
    return dict(frames=frames, last_ms=last_ms, last_fr=last_fr, inserts=inserts, early_miss=early_miss,
                targets=targets, pairs=pairs, idents=idents, allfirst=allfirst)


def red_ms(log, trace):
    tsj = os.path.join(os.path.dirname(os.path.abspath(trace)), 'trace-start.json')
    unix_ms = json.load(open(tsj))['unix_ms']
    for l in open(log, encoding='utf-8', errors='replace'):
        m = RED.match(l)
        if m:
            t = datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f')
            return t.timestamp() * 1000.0 - unix_ms, m.group(1), unix_ms, tsj
    return None, None, unix_ms, tsj


def noident_set(p):
    out = set()
    for l in open(p, encoding='utf-8', errors='replace'):
        m = re.match(r'^(VS|PS) ([0-9A-F]{8}) ', l)
        if m:
            out.add((6 if m.group(1) == 'VS' else 7, int(m.group(2), 16)))
    return out


def main():
    k = ctypes.windll.kernel32
    k.SetPriorityClass(k.GetCurrentProcess(), 0x00100000)  # background mode (Idle + low I/O), as proof5
    ap = argparse.ArgumentParser()
    for n in ('--trace', '--log', '--post', '--runlog', '--sidecar', '--out'):
        ap.add_argument(n, required=True)
    ap.add_argument('--dump-dir')
    ap.add_argument('--fp')
    ap.add_argument('--root-vs', default=ROOT_VS)
    ap.add_argument('--noident', default=NOIDENT)
    ap.add_argument('--w1-s', type=float, default=40.0)
    ap.add_argument('--w2-s', type=float, default=65.0)
    ap.add_argument('--reach-s', type=float, default=80.0)
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    if not os.path.normcase(out).startswith(os.path.normcase(CG7) + os.sep) or os.path.exists(out):
        print('REFUSED: --out must be a new dir under %s' % CG7)
        return 2
    ins = [('trace', a.trace), ('game.log', a.log), ('post', a.post), ('runlog', a.runlog), ('sidecar', a.sidecar),
           ('root-vs', a.root_vs), ('noident', a.noident)]
    ts_json = os.path.join(os.path.dirname(os.path.abspath(a.trace)), 'trace-start.json')
    ins.append(('trace-start', ts_json))
    miss = [p for _, p in ins if not os.path.isfile(p)]
    if a.dump_dir and not os.path.isdir(a.dump_dir):
        miss.append(a.dump_dir)
    if a.fp is not None and not re.fullmatch(r'[0-9a-f]{16}', a.fp):
        print('REFUSED: --fp must be 16 lowercase hex')
        return 2
    if miss:
        print('REFUSED: missing input(s): %s' % '; '.join(miss))
        return 2
    L = []
    w = L.append
    w('dump6_post.py sha256 %s' % sha(os.path.abspath(__file__)))
    for tag, p in ins:
        w('%-11s %s %s' % (tag, sha(p), os.path.abspath(p)))
    w('%-11s %s' % ('dump-dir', os.path.abspath(a.dump_dir) if a.dump_dir else 'NONE (not given: 0 identity files)'))
    bad_fp = False
    if a.fp:
        bad_fp = ('Native GPU [%s]' % a.fp) not in txt(a.log)
        w('fingerprint %s in game.log: %s' % (a.fp, not bad_fp))
    red, red_wall, unix_ms, _ = red_ms(a.log, a.trace)
    sred = [m.group(1) for m in map(SIDE_RED.match, txt(a.sidecar).splitlines()) if m]
    w('trace start unix_ms %d (%s local)' % (unix_ms, datetime.datetime.fromtimestamp(unix_ms / 1000.0)))
    w('red start (game.log, first pad 1 FF 00 00 speed 18): %s -> trace %s ms; sidecar alert %s' % (
        red_wall, '%.1f' % red if red is not None else 'NOT FOUND', sred[0] if sred else 'not found'))

    # ---- D1
    rc_, S = route_checks(a.post, a.runlog, a.sidecar)
    rc_.append(('red-18 start', red is not None))
    rbad = [n for n, ok in rc_ if not ok]
    w('D1 route: %s; %s' % ('PASS' if not rbad else 'FAIL', '; '.join('%s %s' % (n, 'yes' if ok else 'NO')
                                                                      for n, ok in rc_)))
    m = re.search(r'(?:^|\s)(ctl=\d+ done/\d+ err)', S)
    w('   ctl (reported only, not gated): %s' % (m.group(1) if m else 'not found'))
    if red is None:
        w('RESULT: INCONCLUSIVE (no red-18 start in game.log; nothing else judged)')
        return finish(out, L, 'INCONCLUSIVE (no red-18 start in game.log)')

    # ---- scan
    R = scan(a.trace, red, a.w1_s, a.w2_s)
    stop = R['last_ms'] if R['last_ms'] is not None else 0.0
    reach = (stop - red) / 1000.0
    w2cov = max(0.0, reach - a.w2_s)
    d2 = reach >= a.reach_s
    w('trace: frames %d; last frame %s at %.1f ms; miss-cache inserts %d (dump mode: miss cache off, expect 0); '
      'draw_missing rows before red+%.0f s: %d' % (R['frames'], R['last_fr'], stop, R['inserts'], a.w1_s,
                                                    R['early_miss']))
    w('D2 reach: stop = red + %.1f s (need >= red + %.0f s): %s; W1 = red+%.0f..%.0f s; W2 coverage %.1f s '
      '(red+%.0f s..stop)%s' % (reach, a.reach_s, 'PASS' if d2 else 'FAIL', a.w1_s, a.w2_s, w2cov, a.w2_s,
                                '' if d2 else '; W2 NOT-REACHED'))

    # ---- backing map + identities
    back = {}
    for l in open(a.log, encoding='utf-8', errors='replace'):
        mb = BACK.search(l)
        if mb:
            back.setdefault((6 if mb.group(1) == 'vertex' else 7, int(mb.group(2), 16)),
                            (int(mb.group(3), 16), mb.group(4)))
    w('game.log placement warnings (capped at 16 lines): %d distinct (stage, guest) with backing' % len(back))
    for (st, g), (ph, pf) in sorted(back.items()):
        w('   %s %08X backing %08X prefix %s' % (ST[st], g, ph, pf or '-'))
    ids = R['idents']
    t1 = red + 1000.0 * a.w1_s
    w('identity events: %d (VS %d, PS %d)' % (len(ids), sum(1 for d in ids if d.get('stage') == 6),
                                              sum(1 for d in ids if d.get('stage') == 7)))
    for d in ids:
        w('   %s guest %08X physical %08X vb %d pb %d container %016X physical_hash %016X at red%+.1f s' % (
            ST.get(d.get('stage'), '?'), d.get('guest', 0), d.get('physical', 0), d.get('virtual_bytes', 0),
            d.get('physical_bytes', 0), d.get('container_hash', 0), d.get('physical_hash', 0),
            (d['ms'] - red) / 1000.0))
    ph = collections.defaultdict(list)
    for d in ids:
        ph[d.get('physical_hash')].append(d)
    joins = [v for v in ph.values() if len(v) > 1]
    w('physical_hash joins between identity events (information; never used to cover a target): %d' % len(joins))
    for v in joins:
        w('   physical_hash %016X: %s' % (v[0].get('physical_hash', 0), ', '.join(
            '%s %08X' % (ST.get(d.get('stage'), '?'), d.get('guest', 0)) for d in v)))

    # ---- D3
    w('')
    cap = len(ids) >= CAPN
    split, matched_all, unmatched_all, flagged_all, used = {}, [], [], [], []
    for win in ('W1', 'W2'):
        T = R['targets'][win]
        w('D3 %s targets (stage guest: unrecognized rows, draw_missing rows, first..last red+s; match; true first row; '
          'identity times; C-S1)' % win)
        mt, nf = [], 0
        for (st, g), (nu, nd, f0, f1) in sorted(T.items(), key=lambda x: (x[0][0], x[1][2])):
            b = back.get((st, g))
            hit = [d for d in ids if d.get('stage') == st and d.get('guest') == g]
            how = 'guest'
            if not hit and b:
                hit = [d for d in ids if d.get('stage') == st and d.get('physical') == b[0]]
                how = 'backing %08X' % b[0]
            tf = R['allfirst'].get((st, g), f0)
            mt.append(bool(hit))
            (matched_all if hit else unmatched_all).append('%s %s %08X' % (win, ST[st], g))
            used += hit
            if hit:
                fl = []
                if how == 'guest' and not any(d['ms'] >= tf - 1000.0 for d in hit):
                    fl.append('EARLY')
                if cap:
                    fl.append('CAP')
                if fl:
                    nf += 1
                    flagged_all.append('%s %s %08X %s' % (win, ST[st], g, '+'.join(fl)))
                cs1 = '; true first red%+.1f s; identity at %s; C-S1 %s' % (
                    (tf - red) / 1000.0, ', '.join('red%+.1f s' % ((d['ms'] - red) / 1000.0) for d in hit),
                    ' '.join(fl) if fl else ('OK (backing)' if how != 'guest' else 'OK'))
            else:
                cs1 = '; true first red%+.1f s' % ((tf - red) / 1000.0)
            w('   %s %08X: %d, %d, %+.1f..%+.1f  %s%s' % (
                ST[st], g, nu, nd, (f0 - red) / 1000.0, (f1 - red) / 1000.0,
                'MATCHED by %s -> container %s' % (how, ','.join('%016X' % d.get('container_hash', 0) for d in hit))
                if hit else 'UNMATCHED%s' % (' (backing %08X known, no identity with it)' % b[0] if b else ''), cs1))
        w('   pairs at draw_missing rows (last unrecognized VS, PS): draws VSmiss PSmiss first..last red+s')
        for (v, p_), (c, x, y, f0, f1) in sorted(R['pairs'][win].items(), key=lambda x: -x[1][0]):
            fm = lambda z: '%08X' % z if z is not None else '-'
            w('     %-8s %-8s %6d %6d %6d  %+.1f..%+.1f' % (fm(v), fm(p_), c, x, y, (f0 - red) / 1000.0,
                                                           (f1 - red) / 1000.0))
        if win == 'W2' and not d2:
            split[win] = 'NOT-REACHED'
        elif not T:
            split[win] = 'NO-TARGETS'
        elif all(mt) and not nf:
            split[win] = 'COVERED'
        elif any(mt):
            split[win] = 'PARTIAL (%d/%d%s)' % (sum(mt), len(mt), '; C-S1 flagged %d' % nf if nf else '')
        else:
            split[win] = 'NOT-COVERED (0/%d)' % len(mt)

    # ---- D4
    w('')
    d4_bad = []
    cdir = os.path.join(a.dump_dir, 'placement-containers') if a.dump_dir else None
    w('D4 container files (check run: name + size == vb+4+pb + marker == vheader[8:12] + sha256; container_hash '
      'NOT recomputed, no xxhash module)')
    if not a.dump_dir:
        d4_bad.append('no dump dir')
        w('   no dump dir given: 0 container files')
    elif not ids:
        w('   0 identity events')
    d6 = []
    for d in ids:
        st, vb, pb = d.get('stage'), d.get('virtual_bytes', 0), d.get('physical_bytes', 0)
        name = '%s-%016X.bin' % ('vs' if st == 6 else 'ps', d.get('container_hash', 0))
        fpth = os.path.join(cdir, name) if cdir else None
        if not fpth or not os.path.isfile(fpth):
            d4_bad.append(name)
            w('   %s MISSING' % name)
            continue
        data = open(fpth, 'rb').read()
        ok_size = len(data) == vb + 4 + pb
        ok_mark = ok_size and vb >= 12 and data[vb:vb + 4] == data[8:12]
        if not (ok_size and ok_mark):
            d4_bad.append(name)
        w('   %s size %d (expect %d) %s marker %s sha256 %s' % (name, len(data), vb + 4 + pb,
                                                              'OK' if ok_size else 'BAD',
                                                              'OK' if ok_mark else 'BAD', sha(fpth)))
        if st == 6 and ok_size:
            d6.append((name, data[vb + 4:], d.get('guest', 0)))
    d4 = not d4_bad
    w('D4: %s%s' % ('PASS' if d4 else 'FAIL', '' if d4 else ' (%s)' % ', '.join(d4_bad)))

    # ---- D5
    ni = noident_set(a.noident)
    early = [d for d in ids if d['ms'] < t1]
    w('D5 identity events before red+%.0f s: %d (expect 0)' % (a.w1_s, len(early)))
    for d in early:
        key = (d.get('stage'), d.get('guest'))
        w('   %s %08X container %016X at red%+.1f s  %s' % (ST.get(key[0], '?'), key[1] or 0,
                                                          d.get('container_hash', 0), (d['ms'] - red) / 1000.0,
                                                          'IN noident (one of the 22)' if key in ni else
                                                          'not in noident'))

    # ---- D6
    root = open(a.root_vs, 'rb').read()
    rphys = root[304:704]
    w('D6 (information only; the root is never packed, D-C2): VS physical sections vs root vs-A58EBA12 bytes 304..703 '
      '(%d B)' % len(rphys))
    for name, phys, g in d6:
        w('   %s guest %08X physical %d B: %s' % (name, g, len(phys), 'MATCH' if phys == rphys else 'DIFF'))
    if not d6:
        w('   no VS container files')

    # ---- D7
    w('D7 (information): raw + root files')
    if a.dump_dir:
        rdir = os.path.join(a.dump_dir, 'placement-raw')
        raw = sorted(os.listdir(rdir)) if os.path.isdir(rdir) else []
        per = collections.Counter(n[:2] for n in raw if re.fullmatch(r'(vs|ps)-[0-9A-F]{16}\.bin', n))
        idc = collections.Counter('vs' if d.get('stage') == 6 else 'ps' for d in ids)
        for s_ in ('vs', 'ps'):
            w('   raw %s: %d file(s) = unique (stage, prefix) for %d identities (prefix-keyed, no overwrite: '
              'expect <= identities)%s' % (s_.upper(), per[s_], idc[s_], '' if per[s_] <= max(idc[s_], 0) or
                                           not idc[s_] else '  CHECK'))
        for n in raw:
            w('     %s %d B' % (n, os.path.getsize(os.path.join(rdir, n))))
        roots = sorted(n for n in os.listdir(a.dump_dir) if n.endswith('.bin'))
        w('   root files: %s; boot files present: %s; other: %s' % (len(roots), sorted(BOOT & set(roots)),
                                                                     sorted(set(roots) - BOOT) or 'none'))
        known = [(st, pf) for (st, _), (_, pf) in back.items() if pf]
        for st, pf in sorted(set(known)):
            n = '%s-%s.bin' % ('vs' if st == 6 else 'ps', pf.upper())
            w('   game.log prefix %s %s: raw file %s' % (ST[st], pf.upper(), 'present' if n in raw else 'absent'))
    else:
        w('   no dump dir')

    # ---- RESULT
    w('')
    w('C-S1: identity events %d (capture cap %d): %s; flagged matches: %s' % (
        len(ids), CAPN, 'CAP' if cap else 'below cap', ', '.join(flagged_all) if flagged_all else 'none'))
    w('W1/W2 split: W1 %s; W2 %s' % (split['W1'], split['W2']))
    ntg = len(matched_all) + len(unmatched_all)
    if bad_fp:
        res = 'INVALID (fingerprint %s not in game.log)' % a.fp
    elif rbad:
        res = 'INCONCLUSIVE (D1 route: %s)' % ', '.join(rbad)
    elif not ntg:
        res = 'INCONCLUSIVE (no target rows at >= red + %.0f s)' % a.w1_s
    elif not d2:
        res = 'NOT-REACHED (stop red + %.1f s < red + %.0f s)' % (reach, a.reach_s)
    elif not unmatched_all and d4 and not flagged_all:
        res = 'COVERED (%d/%d targets matched; D4 PASS; C-S1 0 flagged)' % (len(matched_all), ntg)
    elif matched_all:
        res = 'PARTIAL (%d/%d targets matched%s%s%s)' % (
            len(matched_all), ntg, '; unmatched: ' + ', '.join(unmatched_all) if unmatched_all else '',
            '' if d4 else '; D4 FAIL', '; C-S1 flagged: ' + ', '.join(flagged_all) if flagged_all else '')
    else:
        res = 'NOT-COVERED (0/%d targets matched; unmatched: %s)' % (ntg, ', '.join(unmatched_all))
    res += '; W1 %s, W2 %s' % (split['W1'], split['W2'])
    w('RESULT: ' + res)
    return finish(out, L, res)


def finish(out, L, res):
    os.makedirs(out)
    rp = os.path.join(out, 'dump6_post.txt')
    with open(rp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    print('RESULT: ' + res)
    print('report %s %s' % (rp, sha(rp)))
    return 0 if res.startswith('COVERED') else 1


if __name__ == '__main__':
    sys.exit(main())

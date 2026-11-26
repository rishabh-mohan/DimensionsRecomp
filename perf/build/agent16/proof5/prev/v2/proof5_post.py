#!/usr/bin/env python3
# proof5_post.py - M16 (S5), build/agent16/proof5: miss-count proof for the candidate bin native5pack-bin.
# Read-only on its inputs; writes ONLY <--out> (must be a NEW dir under build\agent16\proof5).
#
#   python build\agent16\proof5\proof5_post.py --base-trace <events.tsv> --base-log <game.log>
#          --cand-trace <events.tsv> --cand-log <game.log> --cand-fp <16 hex> [--base-fp 39129c4c059be5f0]
#          --cand-post <M3 post\gameplay-<stamp>.txt> --cand-runlog <M3 logs\gameplay-<stamp>.txt>
#          --cand-sidecar <M3 logs\<stamp>-native.sidecar.out.txt>
#          [--targets build\agent16\pack\DUMP-TARGETS-story.txt] --out build\agent16\proof5\post-<stamp>
#
# Both traces must come from miss-cache-ON runs (no dump) of the same scripted route. Per run it counts frames,
# draw_missing_{vertex,pixel}_shader per (stage, guest) and maps each guest to its microcode prefix
# (XXH3 of the first 8 bytes, from shader_miss_cache_insert; stage 6 = VS, 7 = PS). Heap guests move between
# runs, so keys are (stage, prefix); a guest without a unique prefix is keyed by address (@guest).
# STABLE targets (image-range 0xAC4/0xAC5 guests of DUMP-TARGETS-story) are also compared by address.
# A NEW key that is @-keyed may be a base guest that just had no insert event: listed apart as "possibly REMAIN".
# Route checks (M10 P5/P-S1): frames ratio cand/base within +-10%, and the cand route completed like 054546
# (clean exit 0, steps 302/302 last: done, title gate HIT, prompts 3/3, ctl=0, all kit exits 0).
# RESULT, first match wins: INVALID (fingerprint check failed) | INCONCLUSIVE (frames ratio or route check
# failed) | FAIL (missing draws per 1000 frames not lower) | PASS-WITH-CHECKS (rate lower, some STABLE remain)
# | PASS (rate lower AND every STABLE target that missed in base has 0 missing draws in cand).
# Exit 0 for PASS / PASS-WITH-CHECKS, 1 otherwise, 2 = refused.
import argparse, collections, ctypes, hashlib, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
PROOF = os.path.join(W, 'build', 'agent16', 'proof5')
GUEST = re.compile(r'guest(?:_vs|_ps)?=\s*(\d+)')
STAGE = re.compile(r'stage=\s*(\d+)')
PREFIX = re.compile(r'prefix=\s*(\d+)')
ST = {'6': 'VS', '7': 'PS'}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def scan(path):
    frames, draws, pref, inserts = 0, collections.Counter(), collections.defaultdict(set), 0
    with open(path, 'rb') as f:
        for l in f:
            p = l.split(b'\t', 5)
            if len(p) < 5:
                continue
            e = p[2]
            if e == b'frame':
                frames += 1
            elif e in (b'draw_missing_vertex_shader', b'draw_missing_pixel_shader'):
                m = GUEST.search(p[4].decode('ascii', 'replace'))
                if m:
                    draws[('VS' if e == b'draw_missing_vertex_shader' else 'PS', int(m.group(1)))] += 1
            elif e == b'shader_miss_cache_insert':
                d = p[4].decode('ascii', 'replace')
                g, s, x = GUEST.search(d), STAGE.search(d), PREFIX.search(d)
                if g and s and x and s.group(1) in ST:
                    pref[(ST[s.group(1)], int(g.group(1)))].add(int(x.group(1)))
                    inserts += 1
    keyed, gkeys = collections.Counter(), {}
    for (st, g), c in draws.items():
        ps = pref.get((st, g), set())
        k = (st, '%016X' % next(iter(ps))) if len(ps) == 1 else (st, '@%08X' % g)
        keyed[k] += c
        gkeys.setdefault(k, set()).add(g)
    return dict(frames=frames, draws=draws, keyed=keyed, gkeys=gkeys, inserts=inserts,
                total=sum(draws.values()))


def stable_targets(path):
    out = []
    for l in open(path, encoding='utf-8', errors='replace'):
        p = l.rstrip('\n').split('\t')
        if len(p) > 3 and p[3] == 'STABLE':
            out.append((p[0], int(p[2])))
    return out


def fp_in_log(path, fp):
    t = open(path, encoding='utf-8', errors='replace').read()
    return ('Native GPU [%s]' % fp) in t


def txt(path):
    return open(path, encoding='utf-8', errors='replace').read()


def route_checks(post, runlog, sidecar):
    """M3 post + gameplay run log + sidecar log of the cand run -> [(name, ok)] (054546 outcome = all True)."""
    P, R = txt(post), txt(runlog)
    res = [l for l in txt(sidecar).splitlines() if re.match(r'^\S+ result ', l)]
    S = res[-1] if res else ''
    return [
        ('clean exit 0', 'PASS native clean exit: exit 0x00000000' in P),
        ('steps 302/302', 'steps 302/302 stopped_by_script True error None' in P),
        ('stop reached (last: done)', re.search(r'steps 302/302 \(last: done\)', R) is not None),
        ('title gate HIT', re.search(r'wait line \d+ current=5 pending=0 \d+ +ok after', P) is not None),
        ('prompts 3/3', 'prompts=batman:1/1 gandalf:1/1 wyldstyle:1/1' in S),
        ('ctl 0', ' ctl=0 done/0 err' in S),
        ('kit exits 0', all(s in R for s in ('run-game (native) exit 0', 'sidecar exit 0', 'holdwatch exit 0',
                                             'watcher exit 0', 'GAMEPLAY DONE: run-game exit 0; post exit 0'))),
    ]


def main():
    k = ctypes.windll.kernel32
    k.SetPriorityClass(k.GetCurrentProcess(), 0x00100000)  # background mode (Idle + low I/O)
    ap = argparse.ArgumentParser()
    ap.add_argument('--base-trace', required=True)
    ap.add_argument('--cand-trace', required=True)
    ap.add_argument('--cand-fp', required=True)
    ap.add_argument('--base-fp', default='39129c4c059be5f0')
    ap.add_argument('--base-log', required=True)
    ap.add_argument('--cand-log', required=True)
    ap.add_argument('--cand-post', required=True)
    ap.add_argument('--cand-runlog', required=True)
    ap.add_argument('--cand-sidecar', required=True)
    ap.add_argument('--targets', default=os.path.join(W, 'build', 'agent16', 'pack', 'DUMP-TARGETS-story.txt'))
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    if not os.path.normcase(out).startswith(os.path.normcase(PROOF) + os.sep) or os.path.exists(out):
        print('REFUSED: --out must be a new dir under %s' % PROOF)
        return 2
    if not re.fullmatch(r'[0-9a-f]{16}', a.cand_fp) or a.cand_fp == a.base_fp:
        print('REFUSED: --cand-fp must be 16 lowercase hex and differ from --base-fp')
        return 2
    B, C = scan(a.base_trace), scan(a.cand_trace)
    L = []
    w = L.append
    w('proof5_post.py sha256 %s' % sha(os.path.abspath(__file__)))
    for tag, p in (('base trace', a.base_trace), ('cand trace', a.cand_trace), ('base log', a.base_log),
                   ('cand log', a.cand_log), ('cand post', a.cand_post), ('cand runlog', a.cand_runlog),
                   ('cand sidecar', a.cand_sidecar), ('targets', a.targets)):
        w('%-12s %s %s' % (tag, sha(p), os.path.abspath(p)))
    bad_fp = []
    for tag, p, fp in (('base', a.base_log, a.base_fp), ('cand', a.cand_log, a.cand_fp)):
        r = fp_in_log(p, fp)
        w('fingerprint %s %s in game.log: %s' % (tag, fp, r))
        if not r:
            bad_fp.append(tag)
    inconc = []
    ratio = C['frames'] / B['frames'] if B['frames'] else float('nan')
    fr_ok = 0.9 <= ratio <= 1.1
    w('frames ratio cand/base: %d / %d = %.3f (%s; must be within +-10%%)' % (
        C['frames'], B['frames'], ratio, 'OK' if fr_ok else 'OUT OF RANGE'))
    if not fr_ok:
        inconc.append('frames ratio %.3f' % ratio)
    rc_ = route_checks(a.cand_post, a.cand_runlog, a.cand_sidecar)
    rbad = [n for n, ok in rc_ if not ok]
    w('route completion (cand): %s; %s' % ('OK' if not rbad else 'FAILED',
                                           '; '.join('%s %s' % (n, 'yes' if ok else 'NO') for n, ok in rc_)))
    if rbad:
        inconc.append('route: ' + ', '.join(rbad))

    def rate(R):
        return 1000.0 * R['total'] / R['frames'] if R['frames'] else float('nan')

    for tag, R in (('base', B), ('cand', C)):
        w('%s: frames %d; missing draws %d (VS %d, PS %d); per 1000 frames %.1f; missed guests %d; keys %d; '
          'miss-cache inserts %d' % (tag, R['frames'], R['total'], sum(c for (s, _), c in R['draws'].items() if s == 'VS'),
                                     sum(c for (s, _), c in R['draws'].items() if s == 'PS'), rate(R),
                                     len(R['draws']), len(R['keyed']), R['inserts']))
    w('')
    w('STABLE targets (by address; base -> cand missing draws)')
    st_left = []
    for st, g in stable_targets(a.targets):
        b, c = B['draws'].get((st, g), 0), C['draws'].get((st, g), 0)
        verdict = 'not-in-base' if not b else ('FIXED' if not c else 'REMAINS')
        if b and c:
            st_left.append('%s %08X' % (st, g))
        w('  %s %08X %7d -> %7d  %s' % (st, g, b, c, verdict))
    w('')
    fixed = [k_ for k_ in B['keyed'] if k_ not in C['keyed']]
    remain = [k_ for k_ in B['keyed'] if k_ in C['keyed']]
    new = [k_ for k_ in C['keyed'] if k_ not in B['keyed'] and not k_[1].startswith('@')]
    new_at = [k_ for k_ in C['keyed'] if k_ not in B['keyed'] and k_[1].startswith('@')]
    for name, ks, src in (('FIXED (base keys gone in cand)', fixed, B), ('REMAIN (in both)', remain, C),
                          ('NEW (cand only, prefix-keyed)', new, C),
                          ('NEW @-keyed (cand only, no insert event: possibly REMAIN)', new_at, C)):
        w('%s: %d keys, %d cand-or-base draws' % (name, len(ks), sum(src['keyed'][x] for x in ks)))
        for x in sorted(ks, key=lambda x: -src['keyed'][x]):
            w('  %s %s base %7d cand %7d  guests base %s cand %s' % (
                x[0], x[1], B['keyed'].get(x, 0), C['keyed'].get(x, 0),
                ','.join('%08X' % g for g in sorted(B['gkeys'].get(x, ()))) or '-',
                ','.join('%08X' % g for g in sorted(C['gkeys'].get(x, ()))) or '-'))
    w('')
    rb, rc = rate(B), rate(C)
    if bad_fp:
        res = 'INVALID (fingerprint check failed: %s)' % ', '.join(bad_fp)
    elif inconc:
        res = 'INCONCLUSIVE (%s; per 1000 frames %.1f -> %.1f not judged)' % ('; '.join(inconc), rb, rc)
    elif not rc < rb:
        res = 'FAIL (missing draws per 1000 frames %.1f -> %.1f, not lower)' % (rb, rc)
    elif st_left:
        res = 'PASS-WITH-CHECKS (per 1000 frames %.1f -> %.1f; STABLE remaining: %s)' % (rb, rc, ', '.join(st_left))
    else:
        res = 'PASS (per 1000 frames %.1f -> %.1f; all base-missed STABLE targets fixed; keys fixed %d, remain %d, ' \
              'new %d, new @-keyed %d)' % (rb, rc, len(fixed), len(remain), len(new), len(new_at))
    w('RESULT: ' + res)
    os.makedirs(out)
    rp = os.path.join(out, 'proof5_post.txt')
    with open(rp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    print('RESULT: ' + res)
    print('report %s %s' % (rp, sha(rp)))
    return 0 if res.startswith('PASS') else 1


if __name__ == '__main__':
    sys.exit(main())

"""Agent 9, session 3: static A/B check of two MSVC-format link maps (default A = devoff2-bin, B = devoffB-bin).

Usage: python build/agent9/mapcmp.py [--a MAP] [--b MAP] [--out FILE] [--subs NAMES] [--subs-from FILE]
Read-only; one thread. Compares the guest function set (sub_XXXXXXXX publics and their __imp__ aliases), the other
publics from the recompiled TUs, the .text size, and per-function code size (address delta to the next public in
section 0001, so it includes alignment padding).
--subs / --subs-from (added 04:05 for Agent 7's a/b profile tables): also list the A and B code size of the named
functions: a comma list, and/or every sub_XXXXXXXX and __save*/__rest* name in a text file, in first-seen order.
A name not found as-is is looked up as the base of a mangled '?name@...' public. Default --out is
build/agent9/logs/mapcmp-AB.txt, or build/agent9/logs/mapcmp-subs.txt when --subs or --subs-from is given.
"""
import argparse, os, re, sys, time

R = r'<workspace>'
SUB = re.compile(r'^sub_[0-9A-F]{8}$')
TU = re.compile(r'^legodimensions_recomp\.\d+\.cpp\.obj$')
NAME_TOKEN = re.compile(r'(?<![\w?@])(sub_[0-9A-F]{8}|__(?:save|rest)[a-z]+_\d+)(?![\w@])')


def parse(path):
    sections, publics, state = {}, [], 0
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            s = line.strip()
            if state == 0:
                m = re.match(r'^(\d{4}):([0-9a-f]{8}) ([0-9a-f]{8})H (\S+)\s+(CODE|DATA)$', s)
                if m:
                    sections.setdefault(m[4], 0)
                    sections[m[4]] += int(m[3], 16)
                elif s.startswith('Address') and 'Publics by Value' in s:
                    state = 1
            elif state == 1:
                if s.startswith('entry point at'):
                    break
                p = s.split()
                if len(p) < 4 or ':' not in p[0]:
                    continue
                sec, off = p[0].split(':')
                publics.append((int(sec, 16), int(off, 16), p[1], p[-1]))
    return sections, publics


def summarize(publics):
    subs = {}   # name -> (sec, off, obj)
    imps = {}
    other_tu = set()
    for sec, off, name, obj in publics:
        if SUB.match(name):
            subs[name] = (sec, off, obj)
        elif name.startswith('__imp__') and SUB.match(name[7:]):
            imps[name[7:]] = (sec, off, obj)
        elif TU.match(obj):
            other_tu.add(name)
    # code size per sub_: delta to the next distinct address in the same section
    text = sorted({(sec, off) for sec, off, name, obj in publics if sec == 1})
    nxt = {text[i]: text[i + 1][1] for i in range(len(text) - 1)}
    size = {n: nxt.get((v[0], v[1]), v[1]) - v[1] for n, v in subs.items() if v[0] == 1}
    return subs, imps, other_tu, size


def sizes_all(publics):
    """Every public in section 0001: name -> (size, obj), plus base -> entry for mangled '?base@...' names."""
    text = sorted({(sec, off) for sec, off, name, obj in publics if sec == 1})
    nxt = {text[i]: text[i + 1][1] for i in range(len(text) - 1)}
    by_name, by_base = {}, {}
    for sec, off, name, obj in publics:
        if sec != 1 or name in by_name:
            continue
        e = (nxt.get((sec, off), off) - off, obj)
        by_name[name] = e
        if name.startswith('?') and '@' in name:
            by_base.setdefault(name[1:name.index('@')], e)
    return by_name, by_base


def lookup(tables, name):
    by_name, by_base = tables
    return by_name.get(name) or by_base.get(name)


def subs_names(names, path):
    out = [t.strip() for t in (names or '').split(',') if t.strip()]
    if path:
        with open(path, encoding='utf-8', errors='replace') as f:
            out += NAME_TOKEN.findall(f.read())
    seen = set()
    return [n for n in out if not (n in seen or seen.add(n))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--a', default=os.path.join(R, 'build', 'agent2', 'devoff2-bin', 'legodimensions.map'))
    ap.add_argument('--b', default=os.path.join(R, 'build', 'agent2', 'devoffB-bin', 'legodimensions.map'))
    ap.add_argument('--out', default=None)
    ap.add_argument('--subs', default=None, help='comma list of function names (sub_XXXXXXXX, __restgprlr_29, ...)')
    ap.add_argument('--subs-from', default=None, help='text file: every sub_XXXXXXXX and __save*/__rest* name in it')
    a = ap.parse_args()
    want = subs_names(a.subs, a.subs_from) if (a.subs or a.subs_from) else None
    if a.out is None:
        a.out = os.path.join(R, 'build', 'agent9', 'logs', 'mapcmp-subs.txt' if want is not None else 'mapcmp-AB.txt')
    t0 = time.time()
    out = []

    def say(s):
        out.append(s)
        print(s)

    res = {}
    for tag, path in (('A', a.a), ('B', a.b)):
        sections, publics = parse(path)
        subs, imps, other_tu, size = summarize(publics)
        bad_alias = [n for n, v in imps.items() if subs.get(n, (None, None))[:2] != v[:2]]
        allsz = sizes_all(publics) if want is not None else None
        res[tag] = (sections, publics, subs, imps, other_tu, size, set(bad_alias), allsz)
        say('%s %s: %d publics; .text %d B (0x%X); %d sub_ functions (%d in TU objects); %d __imp__ aliases, %d '
            'not at their sub_; %d other publics from recompiled TUs; sub_ code bytes %d'
            % (tag, os.path.relpath(path, R), len(publics), sections.get('.text', 0), sections.get('.text', 0),
               len(subs), sum(1 for v in subs.values() if TU.match(v[2])), len(imps), len(bad_alias), len(other_tu),
               sum(size.values())))
    xa, xb = res['A'][6], res['B'][6]
    say('__imp__ aliases not at their sub_ (hooked): A %d, B %d, same set: %s; objects in B: %s'
        % (len(xa), len(xb), xa == xb, sorted({res['B'][3][n][2] for n in xb})[:6]))
    sa, sb = res['A'][2], res['B'][2]
    only_a, only_b = sorted(set(sa) - set(sb)), sorted(set(sb) - set(sa))
    say('sub_ set: %d common, %d only in A %s, %d only in B %s'
        % (len(set(sa) & set(sb)), len(only_a), only_a[:5], len(only_b), only_b[:5]))
    ia, ib = set(res['A'][3]), set(res['B'][3])
    say('__imp__ alias set: %d only in A, %d only in B' % (len(ia - ib), len(ib - ia)))
    oa, ob = res['A'][4], res['B'][4]
    say('other recompiled-TU publics: %d only in A %s, %d only in B %s'
        % (len(oa - ob), sorted(oa - ob)[:8], len(ob - oa), sorted(ob - oa)[:8]))
    ta, tb = res['A'][0].get('.text', 0), res['B'][0].get('.text', 0)
    say('.text: A %d B, B %d B, delta %d B (%+.2f%%)' % (ta, tb, tb - ta, 100.0 * (tb - ta) / ta if ta else 0))
    za, zb = res['A'][5], res['B'][5]
    common = sorted(set(za) & set(zb))
    ca, cb = sum(za[n] for n in common), sum(zb[n] for n in common)
    grew = sum(1 for n in common if zb[n] > za[n])
    shrank = sum(1 for n in common if zb[n] < za[n])
    say('sub_ code bytes (common, incl. padding): A %d, B %d, delta %d (%+.2f%%); %d shrank, %d grew, %d same'
        % (ca, cb, cb - ca, 100.0 * (cb - ca) / ca if ca else 0, shrank, grew, len(common) - shrank - grew))
    big = sorted(common, key=lambda n: zb[n] - za[n])
    say('largest shrink: ' + ', '.join('%s %d->%d' % (n, za[n], zb[n]) for n in big[:8]))
    say('largest growth: ' + ', '.join('%s %d->%d' % (n, za[n], zb[n]) for n in reversed(big[-8:])))
    if want is not None:
        src = ', '.join(x for x in (a.subs and '--subs', a.subs_from and os.path.relpath(a.subs_from, R)) if x)
        say('')
        say('== code size of %d listed functions, A -> B (bytes incl. padding; names from %s) ==' % (len(want), src))
        say('%-40s %8s %8s %8s %8s  %s' % ('name', 'A', 'B', 'delta', 'pct', 'object (B)'))
        tot_a = tot_b = found = 0
        for n in want:
            ea, eb = lookup(res['A'][7], n), lookup(res['B'][7], n)
            if ea is None or eb is None:
                miss = ' and '.join(t for t, e in (('A', ea), ('B', eb)) if e is None)
                say('%-40s %8s %8s  not found in %s' % (n, ea[0] if ea else '-', eb[0] if eb else '-', miss))
                continue
            found += 1
            tot_a += ea[0]
            tot_b += eb[0]
            say('%-40s %8d %8d %+8d %+7.1f%%  %s' % (n, ea[0], eb[0], eb[0] - ea[0],
                                                     100.0 * (eb[0] - ea[0]) / ea[0] if ea[0] else 0.0, eb[1]))
        say('listed total (%d of %d found): A %d, B %d, delta %+d (%+.2f%%)'
            % (found, len(want), tot_a, tot_b, tot_b - tot_a, 100.0 * (tot_b - tot_a) / tot_a if tot_a else 0.0))
    with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print('wrote %s (%.1fs)' % (a.out, time.time() - t0))
    return 0 if not only_a and not only_b and xa == xb else 1


if __name__ == '__main__':
    sys.exit(main())

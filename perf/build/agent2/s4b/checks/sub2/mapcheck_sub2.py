#!/usr/bin/env python3
"""mapcheck_sub2.py - independent link-map check by NAME and OBJECT (Agent 2 / sub2).

Own parser for lld-link /MAP files.  Two maps (NEW, REF) are compared only by symbol
name and defining object; addresses are compared only inside ONE map:
  sub_X is "hooked" in a map when sub_X and __imp__sub_X are both publics there and
  __imp__sub_X is not at the address of sub_X (section:offset, cross-checked with Rva+Base).

Modes
  moved : --moved NAME=OBJ[@IMPOBJ] (repeatable and/or comma separated).  NAME must be
          unhooked in REF (sub_X and __imp__sub_X in one object, = IMPOBJ if given) and
          hooked in NEW with sub_X defined by OBJ and __imp__sub_X still in its REF object;
          OBJ must be absent from REF and define exactly its moved sub_ publics in NEW.
          Expected: NEW hooked = REF hooked + moved.
  same  : (no --moved) NEW hooked == REF hooked, every sub_/__imp__sub_ object unchanged.
Checks
  a) sub_ / __imp__sub_ counts (optionally == --expect-count) and identical name sets
  b) hooked sets (optionally == --expect-ref-hooked / --expect-new-hooked) and NEW == REF + moved
  c) the moved names (n/a in same mode)
  d) objects of hooked / unhooked names; per-object sub_ and __imp__sub_ name sets
  e) ALL publics as (name, object) pairs: names only in NEW / only in REF / object changed,
     classified (1) moved targets, (2) new names defined by a moved-to object,
     (3) COMDAT/constant re-attributions, (4) anything else (flagged).
"Static symbols" (internal-linkage symbols) are parsed separately, excluded from a-e and
compared as (name, object) multisets for information.
Name lists: a comma/space separated list, or @FILE[:A[-B]] = every sub_XXXXXXXX token
(not preceded by '_') on lines A..B of FILE.
Exit 0 = PASS, 1 = FAIL, 2 = usage/parse problem; the last stdout line is "RESULT: ...".
Read-only on the maps; writes only --out.
"""
import argparse
import hashlib
import os
import re
import sys
import time
from collections import Counter, defaultdict

# " ssss:oooooooo       NAME(left-justified 26)  VVVVVVVVVVVVVVVV     [f] [i] LIB:OBJECT"
SYM_RE = re.compile(r'^ ([0-9A-Fa-f]{4}):([0-9A-Fa-f]{8})\s+(\S.*?)\s+([0-9A-Fa-f]{16})(?:\s+(\S.*?))?\s*$')
FLAG_RE = re.compile(r'^([fi])\s+(\S.*)$')
SUB_RE = re.compile(r'^sub_[0-9A-F]{8}$')
IMP = '__imp__'
RECOMP_RE = re.compile(r'^legodimensions_recomp\.\d+\.cpp\.obj$')
TOKEN_RE = re.compile(r'(?<![0-9A-Za-z_])sub_[0-9A-F]{8}(?![0-9A-Za-z_])')


def lld_line(sec, off, name, va, obj):
    """Re-format a parsed symbol the way lld-link writes it (parser self-check)."""
    s = ' %s:%s       %s %s' % (sec, off, name.ljust(26), va)
    if obj:
        s += '     ' + obj
    return s


class MapInfo(object):
    pass


def parse_map(path, watch):
    t0 = time.time()
    with open(path, 'rb') as f:
        data = f.read()
    mi = MapInfo()
    mi.path = path
    mi.size = len(data)
    mi.sha256 = hashlib.sha256(data).hexdigest().upper()
    text = data.decode('utf-8', 'surrogateescape')
    del data
    mi.publics = []          # (name, sec, off, va, obj, flags, ln)
    mi.statics = []
    mi.marks = []            # (section, line number)
    mi.preamble = []         # non-blank preamble lines
    mi.sectable = 0
    mi.secnames = []         # section-table names (no addresses kept)
    mi.unparsed = []         # (ln, section, text)
    mi.other = []            # unexpected non-blank lines outside symbol sections
    mi.entry = ''
    mi.exports = 0
    mi.flagged = Counter()
    mi.noobj = Counter()
    mi.recon_bad = []        # lines whose lld re-format differs from the raw line
    mi.raw = {}              # watched public name -> raw line(s)
    section = 'preamble'
    ln = 0
    for line in text.split('\n'):
        ln += 1
        if line.endswith('\r'):
            line = line[:-1]
        s = line.strip()
        if not s:
            continue
        if section == 'publics' or section == 'statics':
            m = SYM_RE.match(line)
            if m:
                name = m.group(3)
                obj = m.group(5) or ''
                flags = ''
                while True:
                    fm = FLAG_RE.match(obj)
                    if not fm:
                        break
                    flags += fm.group(1)
                    obj = fm.group(2)
                rec = (name, m.group(1), m.group(2), m.group(4), obj, flags, ln)
                if section == 'publics':
                    mi.publics.append(rec)
                    if name in watch:
                        mi.raw.setdefault(name, []).append(line)
                else:
                    mi.statics.append(rec)
                if flags:
                    mi.flagged[(section, flags)] += 1
                elif lld_line(rec[1], rec[2], name, rec[3], obj) != line.rstrip():
                    mi.recon_bad.append((ln, line))
                if not obj:
                    mi.noobj[section] += 1
                continue
        if 'Publics by Value' in s:
            section = 'publics'
            mi.marks.append(('Publics by Value', ln))
            continue
        if s.startswith('entry point at'):
            section = 'entry'
            mi.entry = s
            mi.marks.append(('entry point', ln))
            continue
        if s == 'Static symbols':
            section = 'statics'
            mi.marks.append(('Static symbols', ln))
            continue
        if s == 'Exports':
            section = 'exports'
            mi.marks.append(('Exports', ln))
            continue
        if section == 'preamble' and s.startswith('Start') and 'Length' in s and 'Class' in s:
            section = 'sectable'
            mi.marks.append(('section table', ln))
            continue
        if section == 'preamble':
            mi.preamble.append(s)
            continue
        if section == 'sectable' and re.match(r'^ [0-9A-Fa-f]{4}:[0-9A-Fa-f]{8} [0-9A-Fa-f]{8}H ', line):
            mi.sectable += 1
            mi.secnames.append(line.split()[2])
            continue
        if section == 'exports':
            mi.exports += 1
            continue
        if section in ('publics', 'statics'):
            mi.unparsed.append((ln, section, line))
        else:
            mi.other.append((ln, section, line))
    mi.nlines = ln
    mi.secs = time.time() - t0
    return mi


class Derived(object):
    def __init__(self, mi):
        self.mi = mi
        by = {}
        dups = defaultdict(list)
        for rec in mi.publics:
            n = rec[0]
            if n in by:
                dups[n].append(rec)
            else:
                by[n] = rec
        for n in dups:
            dups[n].insert(0, by[n])
        self.by = by
        self.dups = dict(dups)
        self.subs = set()
        self.imps = set()          # stored as X (without the __imp__ prefix)
        self.sub_loose = 0
        self.imp_loose = 0
        self.prefix_odd = []
        for n in by:
            if n.startswith('sub_'):
                self.sub_loose += 1
                if SUB_RE.match(n):
                    self.subs.add(n)
                else:
                    self.prefix_odd.append(n)
            elif n.startswith('__imp__sub_'):
                self.imp_loose += 1
                x = n[len(IMP):]
                if SUB_RE.match(x):
                    self.imps.add(x)
                else:
                    self.prefix_odd.append(n)
        self.pairs = self.subs & self.imps
        self.orphan_sub = sorted(self.subs - self.imps)
        self.orphan_imp = sorted(self.imps - self.subs)
        self.sub_obj = dict((x, by[x][4]) for x in self.subs)
        self.imp_obj = dict((x, by[IMP + x][4]) for x in self.imps)
        self.hooked = set()
        self.addr_disagree = []
        self.hooked_same_obj = []
        self.unhooked_diff_obj = []
        for x in self.pairs:
            a = by[x]
            b = by[IMP + x]
            d_so = (a[1].lower(), a[2].lower()) != (b[1].lower(), b[2].lower())
            d_va = a[3].lower() != b[3].lower()
            if d_so != d_va:
                self.addr_disagree.append(x)
            if d_so or d_va:
                self.hooked.add(x)
                if a[4] == b[4]:
                    self.hooked_same_obj.append(x)
            elif a[4] != b[4]:
                self.unhooked_diff_obj.append(x)
        self.obj_subs = defaultdict(set)
        for x, o in self.sub_obj.items():
            self.obj_subs[o].add(x)
        self.obj_imps = defaultdict(set)
        for x, o in self.imp_obj.items():
            self.obj_imps[o].add(x)
        self.sub_in_recomp = sum(1 for o in self.sub_obj.values() if RECOMP_RE.match(o))
        self.obj_pub = Counter(r[4] for r in mi.publics)
        self.obj_stat = Counter(r[4] for r in mi.statics)
        self.stat_sub = [r for r in mi.statics if r[0].startswith('sub_') or r[0].startswith('__imp__sub_')]
        self.objs_of = dict((n, (rec[4],)) for n, rec in by.items())
        for n, recs in self.dups.items():
            self.objs_of[n] = tuple(sorted(r[4] for r in recs))


def load_names(spec):
    if spec is None:
        return None, None
    if spec.startswith('@'):
        p = spec[1:]
        a = b = None
        m = re.match(r'^(.*):(\d+)(?:-(\d+))?$', p)
        if m and not os.path.exists(p):
            p, a = m.group(1), int(m.group(2))
            b = int(m.group(3)) if m.group(3) else a
        with open(p, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.read().splitlines()
        sel = lines[a - 1:b] if a else lines
        names = []
        for l in sel:
            names.extend(TOKEN_RE.findall(l))
        return names, '%s lines %s' % (p, ('%d-%d' % (a, b)) if a else 'all')
    return [t for t in re.split(r'[\s,]+', spec) if t], 'command line'


def parse_moved(items):
    out = []
    for item in items:
        for part in item.split(','):
            part = part.strip()
            if not part:
                continue
            if '=' not in part:
                sys.exit('bad --moved item %r (want NAME=OBJ[@IMPOBJ])' % part)
            name, rhs = part.split('=', 1)
            imp = None
            if '@' in rhs:
                rhs, imp = rhs.split('@', 1)
            out.append((name.strip(), rhs.strip(), imp.strip() if imp else None))
    return out


def name_kind(n):
    if n.startswith('__real@'):
        return '__real@ constant'
    if n.startswith(('__xmm@', '__ymm@', '__zmm@')):
        return '__xmm@ constant'
    if n.startswith('??_C@'):
        return '??_C@ string'
    if n.startswith('??$'):
        return '??$ template'
    if n.startswith(('??_7', '??_R')):
        return 'vftable/RTTI'
    if n.startswith(('_TI', '_CTA', '_CT')) and '?' in n:
        return 'throw info'
    if n.startswith('?') and '?$' in n:
        return '?$ template member'
    if n.startswith('?'):
        return 'C++ name (inline/COMDAT)'
    return None


def obj_kind(o):
    if not o:
        return 'no-object'
    if o.startswith('<'):
        return 'linker'
    if RECOMP_RE.match(o):
        return 'recomp-TU'
    if ':' in o:
        lib, mem = o.split(':', 1)
        if mem.lower().endswith('.dll'):
            return 'import:' + lib
        return 'lib:' + lib
    return 'project-obj'


def short(lst, k=12):
    lst = list(lst)
    if len(lst) <= k:
        return ' '.join(lst)
    return ' '.join(lst[:k]) + ' ... (+%d)' % (len(lst) - k)


def fmt_objs(objs):
    """('<absolute>',)*49 -> '<absolute> x49'; single objects unchanged."""
    c = Counter(objs)
    return ' '.join(o if c[o] == 1 else '%s x%d' % (o, c[o]) for o in sorted(c))


def main():
    ap = argparse.ArgumentParser(description='independent lld-link map check by name and object')
    ap.add_argument('--new', required=True)
    ap.add_argument('--ref', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--moved', action='append', default=[], help='NAME=OBJ[@IMPOBJ]; repeatable / comma separated')
    ap.add_argument('--expect-count', type=int, default=None, help='expected sub_ and __imp__sub_ count in both maps')
    ap.add_argument('--expect-ref-hooked', default=None, help='names or @FILE[:A[-B]]')
    ap.add_argument('--expect-new-hooked', default=None, help='names or @FILE[:A[-B]]')
    ap.add_argument('--label', default='')
    ap.add_argument('--find', action='append', default=[], help='info: count publics/statics whose name or object matches REGEX')
    ap.add_argument('--max-list', type=int, default=3000)
    args = ap.parse_args()
    t0 = time.time()
    moved = parse_moved(args.moved)
    moved_names = set(m[0] for m in moved)
    moved_objs = set(m[1] for m in moved)
    mode = 'moved' if moved else 'same'
    exp_ref, exp_ref_src = load_names(args.expect_ref_hooked)
    exp_new, exp_new_src = load_names(args.expect_new_hooked)
    watch = set()
    for x in moved_names | set(exp_ref or []) | set(exp_new or []):
        watch.add(x)
        watch.add(IMP + x)

    rmi = parse_map(args.ref, watch)
    nmi = parse_map(args.new, watch)
    R = Derived(rmi)
    N = Derived(nmi)

    out = []
    w = out.append
    w('# mapcheck_sub2: independent map check by NAME and OBJECT (Agent 2 / sub2)  %s  %s'
      % (time.strftime('%Y-%m-%d %H:%M:%S'), args.label))
    w('# script: %s (own parser; no shared code with mapcheck-s4c.py / mapcmp.py / maplines.py)' % os.path.normpath(sys.argv[0]))
    w('mode: %s%s' % (mode, (' (%d moved: %s)' % (len(moved), ', '.join('%s=%s%s' % (a, b, ('@' + c) if c else '') for a, b, c in moved))) if moved else ' (NEW must equal REF in hooked set and objects)'))
    parse_ok = True
    for tag, mi in (('NEW', nmi), ('REF', rmi)):
        w('%s: %s  %d B  sha256 %s  lines %d  parse %.1fs' % (tag, mi.path, mi.size, mi.sha256[:16], mi.nlines, mi.secs))
        w('     %s | %s | section table rows %d' % ('; '.join(mi.preamble[1:3]), mi.entry, mi.sectable))
        w('     sections at lines: %s' % ', '.join('%s %d' % (a, b) for a, b in mi.marks))
        w('     publics %d, statics %d, unparsed lines in symbol sections %d, other unexpected lines %d, '
          'lines with f/i flags %d, symbols without object %d, lld re-format mismatches %d, exports lines %d'
          % (len(mi.publics), len(mi.statics), len(mi.unparsed), len(mi.other), sum(mi.flagged.values()),
             sum(mi.noobj.values()), len(mi.recon_bad), mi.exports))
        for ln, sec, line in (mi.unparsed[:5] + mi.other[:5]):
            w('       unexpected line %d (%s): %s' % (ln, sec, line[:160]))
        for ln, line in mi.recon_bad[:5]:
            w('       re-format mismatch line %d: %r' % (ln, line[:160]))
        if mi.unparsed or mi.other or mi.recon_bad or not mi.publics or not any(a == 'Publics by Value' for a, b in mi.marks):
            parse_ok = False
    w('section-table names (by name only) only in NEW: %s; only in REF: %s' % (
        ' '.join(sorted(set(nmi.secnames) - set(rmi.secnames))) or 'none',
        ' '.join(sorted(set(rmi.secnames) - set(nmi.secnames))) or 'none'))
    w('statics: the "Static symbols" section (internal-linkage symbols, listed after "entry point at") is parsed '
      'separately with the same line parser; it is NOT used for a-e (publics only); it is compared as (name, object) '
      'multisets for information at the end.')
    w('')
    w('counts            publics  statics     sub_  __imp__sub_   pairs  hooked  hooked-same-obj  unhooked-diff-obj  sub_-in-recomp-TU  objects(publics)')
    for tag, D in (('REF', R), ('NEW', N)):
        w('  %-3s          %9d %8d %8d %12d %7d %7d %16d %18d %18d %17d'
          % (tag, len(D.mi.publics), len(D.mi.statics), len(D.subs), len(D.imps), len(D.pairs), len(D.hooked),
             len(D.hooked_same_obj), len(D.unhooked_diff_obj), D.sub_in_recomp, len(D.obj_pub)))
    w('')
    results = {}

    # ---------------- a) counts and name sets
    w('a) sub_ / __imp__sub_ counts and name sets')
    ok = parse_ok
    for tag, D in (('REF', R), ('NEW', N)):
        sd = sorted(n for n in D.dups if n.startswith('sub_') or n.startswith('__imp__sub_'))
        w('  %s: sub_ %d, __imp__sub_ %d (names starting sub_ %d / __imp__sub_ %d), pairs %d, orphan sub_ %d, '
          'orphan __imp__sub_ %d, duplicate public names %d (of them sub_/__imp__sub_ %d), address forms disagree %d'
          % (tag, len(D.subs), len(D.imps), D.sub_loose, D.imp_loose, len(D.pairs), len(D.orphan_sub),
             len(D.orphan_imp), len(D.dups), len(sd), len(D.addr_disagree)))
        if args.expect_count is not None and (len(D.subs) != args.expect_count or len(D.imps) != args.expect_count):
            ok = False
            w('    FAIL: expected %d each' % args.expect_count)
        if D.orphan_sub or D.orphan_imp:
            ok = False
            w('    FAIL: orphan sub_: %s | orphan __imp__sub_: %s' % (short(D.orphan_sub), short(D.orphan_imp)))
        if sd:
            ok = False
            w('    FAIL: duplicate sub_/__imp__sub_ publics: %s' % short(sd))
        if D.addr_disagree:
            ok = False
            w('    FAIL: section:offset and Rva+Base disagree on hookedness: %s' % short(sorted(D.addr_disagree)))
        if D.dups:
            w('    note: duplicate public names: %s' % short(sorted(D.dups)))
        if D.prefix_odd:
            w('    note: names with the prefix but not the sub_XXXXXXXX form: %s' % short(sorted(D.prefix_odd)))
        w('    sub_/__imp__sub_ names in Static symbols: %d%s' % (len(D.stat_sub), (' e.g. ' + short([r[0] + '@' + r[4] for r in D.stat_sub], 6)) if D.stat_sub else ''))
    if args.expect_count is not None:
        w('  expected count %d in both maps: %s' % (args.expect_count, 'yes' if all(len(D.subs) == args.expect_count and len(D.imps) == args.expect_count for D in (R, N)) else 'NO'))
    if len(R.subs) != len(N.subs) or len(R.imps) != len(N.imps):
        ok = False
        w('  FAIL: counts differ between maps')
    s_new = sorted(N.subs - R.subs)
    s_ref = sorted(R.subs - N.subs)
    i_new = sorted(N.imps - R.imps)
    i_ref = sorted(R.imps - N.imps)
    w('  sub_ name set: only in NEW %d, only in REF %d -> %s' % (len(s_new), len(s_ref), 'identical' if not (s_new or s_ref) else 'DIFFERENT'))
    w('  __imp__sub_ name set: only in NEW %d, only in REF %d -> %s' % (len(i_new), len(i_ref), 'identical' if not (i_new or i_ref) else 'DIFFERENT'))
    for lab, lst in (('sub_ only NEW', s_new), ('sub_ only REF', s_ref), ('__imp__ only NEW', i_new), ('__imp__ only REF', i_ref)):
        if lst:
            ok = False
            w('    %s: %s' % (lab, short(lst, 30)))
    results['a'] = ok
    w('  => a) %s' % ('PASS' if ok else 'FAIL'))
    w('')

    # ---------------- b) hooked sets
    w('b) hooked sets (hooked = sub_X and __imp__sub_X both public, __imp__sub_X not at the address of sub_X, same map)')
    ok = True
    w('  REF hooked %d, NEW hooked %d' % (len(R.hooked), len(N.hooked)))
    for tag, D, exp, src in (('REF', R, exp_ref, exp_ref_src), ('NEW', N, exp_new, exp_new_src)):
        if exp is None:
            continue
        es = set(exp)
        miss = sorted(es - D.hooked)
        extra = sorted(D.hooked - es)
        w('  %s hooked vs expected list (%d names from %s): %s%s%s' % (
            tag, len(es), src, 'equal' if not (miss or extra) else 'DIFFERENT',
            ('; missing: ' + short(miss, 40)) if miss else '', ('; extra: ' + short(extra, 40)) if extra else ''))
        if len(es) != len(exp):
            w('    note: expected list repeats names (%d tokens, %d distinct)' % (len(exp), len(es)))
        if miss or extra:
            ok = False
    rel = R.hooked | moved_names
    miss = sorted(rel - N.hooked)
    extra = sorted(N.hooked - rel)
    w('  NEW hooked == REF hooked%s (%d): %s%s%s' % (
        (' + %d moved' % len(moved_names)) if moved_names else '', len(rel), 'yes' if not (miss or extra) else 'NO',
        ('; missing in NEW: ' + short(miss, 40)) if miss else '', ('; extra in NEW: ' + short(extra, 40)) if extra else ''))
    if miss or extra:
        ok = False
    pre = sorted(moved_names & R.hooked)
    if pre:
        ok = False
        w('  FAIL: moved names already hooked in REF: %s' % ' '.join(pre))
    for tag, D in (('REF', R), ('NEW', N)):
        groups = defaultdict(list)
        for x in sorted(D.hooked):
            groups[D.sub_obj[x]].append(x)
        w('  %s hooked, by the object that defines sub_X:' % tag)
        for o in sorted(groups):
            w('    %-36s %2d  %s' % (o, len(groups[o]), ' '.join(groups[o])))
    w('  NEW hooked, sorted: %s' % ' '.join(sorted(N.hooked)))
    results['b'] = ok
    w('  => b) %s' % ('PASS' if ok else 'FAIL'))
    w('')

    # ---------------- c) moved names
    w('c) moved names')
    ok = True
    if not moved:
        w('  n/a (same mode)')
        results['c'] = None
    else:
        for x, obj, impobj in moved:
            probs = []
            r_sub, r_imp = R.sub_obj.get(x), R.imp_obj.get(x)
            n_sub, n_imp = N.sub_obj.get(x), N.imp_obj.get(x)
            if x not in R.pairs:
                probs.append('REF: sub_/__imp__ pair missing')
            else:
                if x in R.hooked:
                    probs.append('REF: already hooked')
                if r_sub != r_imp:
                    probs.append('REF: sub_ and __imp__ in different objects')
                if impobj and r_imp != impobj:
                    probs.append('REF: __imp__ object %s != expected %s' % (r_imp, impobj))
            if x not in N.pairs:
                probs.append('NEW: sub_/__imp__ pair missing')
            else:
                if x not in N.hooked:
                    probs.append('NEW: not hooked')
                if n_sub != obj:
                    probs.append('NEW: sub_ object %s != %s' % (n_sub, obj))
                if n_imp != r_imp:
                    probs.append('NEW: __imp__ object %s != REF %s' % (n_imp, r_imp))
                if impobj and n_imp != impobj:
                    probs.append('NEW: __imp__ object %s != expected %s' % (n_imp, impobj))
            if probs:
                ok = False
            w('  %s: REF sub_ %s / __imp__ %s (%s) -> NEW sub_ %s / __imp__ %s (%s): %s' % (
                x, r_sub, r_imp, 'hooked' if x in R.hooked else 'unhooked', n_sub, n_imp,
                'hooked' if x in N.hooked else 'unhooked', 'OK' if not probs else 'FAIL: ' + '; '.join(probs)))
            for tag, mi in (('REF', rmi), ('NEW', nmi)):
                for nm in (x, IMP + x):
                    for line in mi.raw.get(nm, ['(missing)']):
                        w('      %s %s' % (tag, line))
        for obj in sorted(moved_objs):
            want = set(x for x, o, _ in moved if o == obj)
            r_like = sorted(o for o in set(R.obj_pub) | set(R.obj_stat) if o == obj or o.split(':')[-1] == obj)
            n_subs = N.obj_subs.get(obj, set())
            n_imps = N.obj_imps.get(obj, set())
            others = sorted(r[0] for r in nmi.publics if r[4] == obj and r[0] not in want)
            w('  %s: in REF publics %d, statics %d, same-named objects %s -> %s' % (
                obj, R.obj_pub.get(obj, 0), R.obj_stat.get(obj, 0), r_like or 'none', 'absent' if not r_like else 'PRESENT (FAIL)'))
            w('    in NEW: publics %d (sub_ %d: %s; __imp__sub_ %d; other publics %d), statics %d -> sub_ set %s' % (
                N.obj_pub.get(obj, 0), len(n_subs), ' '.join(sorted(n_subs)), len(n_imps), len(others),
                N.obj_stat.get(obj, 0), 'exactly the moved names' if n_subs == want else 'DIFFERS from the moved names'))
            w('    other publics of %s in NEW: %s' % (obj, ' '.join(others) if others else 'none'))
            if r_like or n_subs != want or n_imps:
                ok = False
        results['c'] = ok
    w('  => c) %s' % ('n/a' if results['c'] is None else ('PASS' if ok else 'FAIL')))
    w('')

    # ---------------- d) objects of hooked / unhooked names, per-object sets
    w('d) objects of hooked / unhooked names; per-object sub_ and __imp__sub_ sets')
    ok = True
    common = sorted((R.hooked & N.hooked) - moved_names)
    bad = [x for x in common if R.sub_obj[x] != N.sub_obj[x] or R.imp_obj[x] != N.imp_obj[x]]
    w('  hooked in both maps (moved excluded): %d; sub_ and __imp__ objects unchanged: %d; changed: %d' % (len(common), len(common) - len(bad), len(bad)))
    for x in bad:
        w('    CHANGED %s: REF %s / %s -> NEW %s / %s' % (x, R.sub_obj[x], R.imp_obj[x], N.sub_obj[x], N.imp_obj[x]))
    if bad:
        ok = False
    for tag, D in (('REF', R), ('NEW', N)):
        w('  %s: unhooked %d, of them sub_ and __imp__ in different objects: %d%s; hooked with both in one object: %d%s' % (
            tag, len(D.pairs) - len(D.hooked), len(D.unhooked_diff_obj),
            (' (' + short(sorted(D.unhooked_diff_obj)) + ')') if D.unhooked_diff_obj else '',
            len(D.hooked_same_obj), (' (' + short(sorted(D.hooked_same_obj)) + ')') if D.hooked_same_obj else ''))
        if D.unhooked_diff_obj:
            ok = False
    exp_obj = dict((o, set(s)) for o, s in R.obj_subs.items())
    for x, obj, _ in moved:
        o = R.sub_obj.get(x)
        if o is not None and o in exp_obj:
            exp_obj[o].discard(x)
        exp_obj.setdefault(obj, set()).add(x)
    objs = sorted(set(exp_obj) | set(N.obj_subs))
    diffs = []
    for o in objs:
        e = exp_obj.get(o, set())
        n = N.obj_subs.get(o, set())
        if e != n:
            diffs.append((o, sorted(n - e), sorted(e - n)))
    w('  per-object sub_ sets, REF with the %d moved names re-homed vs NEW: %d objects, %d differ' % (len(moved), len(objs), len(diffs)))
    for o, plus, minus in diffs:
        w('    DIFF %s: +%d %s  -%d %s' % (o, len(plus), short(plus), len(minus), short(minus)))
    if diffs:
        ok = False
    rawd = []
    for o in sorted(set(R.obj_subs) | set(N.obj_subs)):
        a = R.obj_subs.get(o, set())
        b = N.obj_subs.get(o, set())
        if a != b:
            rawd.append('%s(+%d -%d)' % (o, len(b - a), len(a - b)))
    w('  raw per-object sub_ changes REF -> NEW (no re-homing): %s' % (', '.join(rawd) if rawd else 'none'))
    objs2 = sorted(set(R.obj_imps) | set(N.obj_imps))
    diffs2 = []
    for o in objs2:
        a = R.obj_imps.get(o, set())
        b = N.obj_imps.get(o, set())
        if a != b:
            diffs2.append((o, sorted(b - a), sorted(a - b)))
    w('  per-object __imp__sub_ sets REF vs NEW: %d objects, %d differ' % (len(objs2), len(diffs2)))
    for o, plus, minus in diffs2:
        w('    DIFF %s: +%d %s  -%d %s' % (o, len(plus), short(plus), len(minus), short(minus)))
    if diffs2:
        ok = False
    results['d'] = ok
    w('  => d) %s' % ('PASS' if ok else 'FAIL'))
    w('')

    # ---------------- e) all publics as (name, object) pairs
    w('e) all publics as (name, object) pairs, REF -> NEW')
    rmap, nmap = R.objs_of, N.objs_of
    only_new = sorted(set(nmap) - set(rmap))
    only_ref = sorted(set(rmap) - set(nmap))
    changed = sorted(n for n in set(rmap) & set(nmap) if rmap[n] != nmap[n])
    same = len(set(rmap) & set(nmap)) - len(changed)
    w('  names: REF %d, NEW %d; in both with the same object(s) %d; only in NEW %d; only in REF %d; object changed %d' % (
        len(rmap), len(nmap), same, len(only_new), len(only_ref), len(changed)))
    items = []   # (cat, sub, group, name, ref_objs, new_objs, note)

    def is_subish(n):
        return n.startswith('sub_') or n.startswith('__imp__sub_')

    def sub4(objs_):
        kinds = set(obj_kind(o) for o in objs_)
        if any(k == 'recomp-TU' for k in kinds):
            return '4c recompiled TU'
        if any(k == 'project-obj' for k in kinds):
            return '4b project object'
        return '4a library/CRT/import/linker'

    for n in only_new:
        o = nmap[n]
        if all(x in moved_objs for x in o) and not is_subish(n):
            items.append((2, '2', fmt_objs(o), n, '-', fmt_objs(o), name_kind(n) or ''))
        else:
            items.append((4, sub4(o) + ', only in NEW', fmt_objs(o), n, '-', fmt_objs(o), name_kind(n) or ''))
    for n in only_ref:
        o = rmap[n]
        items.append((4, sub4(o) + ', only in REF', fmt_objs(o), n, fmt_objs(o), '-', name_kind(n) or ''))
    for n in changed:
        ro, no = rmap[n], nmap[n]
        grp = '%s -> %s' % (fmt_objs(ro), fmt_objs(no))
        if is_subish(n):
            mv = [m for m in moved if m[0] == n]
            if mv and no == (mv[0][1],) and ro == (R.imp_obj.get(n),):
                items.append((1, '1', grp, n, fmt_objs(ro), fmt_objs(no), 'moved target'))
            else:
                items.append((4, '4d sub_/__imp__sub_ object change', grp, n, fmt_objs(ro), fmt_objs(no), ''))
        elif all(x in moved_objs for x in no):
            items.append((3, '3a re-attributed to the new object', grp, n, fmt_objs(ro), fmt_objs(no), name_kind(n) or 'C-name COMDAT?'))
        elif name_kind(n) is not None:
            items.append((3, '3b re-attributed between existing objects', grp, n, fmt_objs(ro), fmt_objs(no), name_kind(n)))
        else:
            items.append((4, sub4(ro + no) + ', object changed', grp, n, fmt_objs(ro), fmt_objs(no), ''))
    catn = Counter(it[0] for it in items)
    subn = Counter(it[1] for it in items)
    w('  categories: (1) moved targets %d; (2) new names of the moved-to object %d; (3) COMDAT/constant re-attributions %d; (4) other %d'
      % (catn.get(1, 0), catn.get(2, 0), catn.get(3, 0), catn.get(4, 0)))
    w('  sub-categories: %s' % ', '.join('%s: %d' % (k, v) for k, v in sorted(subn.items())))
    for cat, title in ((1, '(1) the moved targets'), (2, '(2) new names defined by the moved-to object'),
                       (3, '(3) COMDAT/constant re-attributions'), (4, '(4) ANYTHING ELSE - flagged')):
        sel = [it for it in items if it[0] == cat]
        w('  %s: %d' % (title, len(sel)))
        groups = defaultdict(list)
        for it in sel:
            groups[(it[1], it[2])].append(it)
        k = 0
        for (sub, grp) in sorted(groups):
            g = groups[(sub, grp)]
            w('    [%s] %s: %d' % (sub, grp, len(g)))
            for it in g:
                k += 1
                if k > args.max_list:
                    break
                w('        %s%s' % (it[3], ('   (' + it[6] + ')') if it[6] else ''))
        if k > args.max_list:
            w('    ... list truncated at %d' % args.max_list)
    cat4 = [it for it in items if it[0] == 4]
    cat4_hard = [it for it in cat4 if not it[1].startswith('4a')]
    if not cat4:
        e_status = 'PASS'
    elif not cat4_hard:
        e_status = 'PASS*'
    else:
        e_status = 'FAIL'
    results['e'] = e_status
    w('  objects: only in NEW: %s; only in REF: %s' % (
        ', '.join(sorted(set(N.obj_pub) - set(R.obj_pub))) or 'none', ', '.join(sorted(set(R.obj_pub) - set(N.obj_pub))) or 'none'))
    dll_new = sorted(o for o in set(N.obj_pub) - set(R.obj_pub) if obj_kind(o).startswith('import:'))
    dll_ref = sorted(o for o in set(R.obj_pub) - set(N.obj_pub) if obj_kind(o).startswith('import:'))
    w('  import DLLs (by descriptor) only in NEW: %s; only in REF: %s' % (', '.join(dll_new) or 'none', ', '.join(dll_ref) or 'none'))
    chg = []
    for o in sorted(set(R.obj_pub) | set(N.obj_pub)):
        if R.obj_pub.get(o, 0) != N.obj_pub.get(o, 0):
            chg.append('%s %d->%d' % (o, R.obj_pub.get(o, 0), N.obj_pub.get(o, 0)))
    w('  public counts per object that changed: %s' % ('; '.join(chg) if chg else 'none'))
    w('  => e) %s  (PASS = no category 4; PASS* = category 4 only library/CRT/import/linker symbols (4a), flagged above; '
      'FAIL = category 4 in project objects, recompiled TUs or sub_ names)' % e_status)
    w('')

    # ---------------- statics (information)
    w('statics (information only, not part of a-e): (name, object) multisets REF -> NEW')
    rs = Counter((r[0], r[4]) for r in rmi.statics)
    ns = Counter((r[0], r[4]) for r in nmi.statics)
    plus = ns - rs
    minus = rs - ns
    w('  statics REF %d, NEW %d; added %d, removed %d' % (len(rmi.statics), len(nmi.statics), sum(plus.values()), sum(minus.values())))
    per = defaultdict(lambda: [[], []])
    for (n, o), c in plus.items():
        per[o][0].extend([n] * c)
    for (n, o), c in minus.items():
        per[o][1].extend([n] * c)
    for o in sorted(per, key=lambda z: (obj_kind(z), z)):
        a, b = per[o]
        w('    %-44s [%s] +%d -%d%s%s' % (o, obj_kind(o), len(a), len(b),
                                          ('  +: ' + short(sorted(a), 40)) if a else '', ('  -: ' + short(sorted(b), 40)) if b else ''))
    w('')

    if args.find:
        w('find (information): publics/statics whose name or object matches (case-insensitive)')
        for pat in args.find:
            rx = re.compile(pat, re.I)
            for tag, mi in (('REF', rmi), ('NEW', nmi)):
                hits = [(sec, r) for sec, lst in (('pub', mi.publics), ('stat', mi.statics)) for r in lst
                        if rx.search(r[0]) or rx.search(r[4])]
                w('  /%s/ %s: %d hits (publics %d, statics %d)%s' % (
                    pat, tag, len(hits), sum(1 for h in hits if h[0] == 'pub'), sum(1 for h in hits if h[0] == 'stat'),
                    (' e.g. ' + short(['%s@%s' % (h[1][0], h[1][4]) for h in hits], 5)) if hits else ''))
        w('')

    fails = [k for k in 'abcde' if results.get(k) is False or results.get(k) == 'FAIL']
    summ = ' '.join('%s=%s' % (k, ('n/a' if results[k] is None else (results[k] if isinstance(results[k], str) else ('PASS' if results[k] else 'FAIL')))) for k in 'abcde')
    final = 'RESULT: %s  (%s; hooked REF %d -> NEW %d; e: cat1 %d, cat2 %d, cat3 %d, cat4 %d; %.1fs)' % (
        'FAIL' if fails else 'PASS', summ, len(R.hooked), len(N.hooked), catn.get(1, 0), catn.get(2, 0),
        catn.get(3, 0), catn.get(4, 0), time.time() - t0)
    w(final)
    d = os.path.dirname(os.path.abspath(args.out))
    if not os.path.isdir(d):
        os.makedirs(d)
    with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print('report: %s' % args.out)
    print(final)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())

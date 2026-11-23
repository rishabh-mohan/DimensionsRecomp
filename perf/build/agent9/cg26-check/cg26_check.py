#!/usr/bin/env python3
# cg26_check.py -- Agent 9, run-2 task #18 (W10 readiness). An independent, read-only static check of the CG26 regen
# and its staged bin (#26: codegen option db16cyc_pause ON), for Agent 10's b2r row 37 (S36) static gates.
# Stdlib only, one thread. It reads the trees and writes only under --out.
#
# Run it from the workspace root at below-normal priority, one heavy script at a time (it reads both trees, ~1 GB).
# Put everything on one command line (README.md has the exact command):
#   cmd /c start "" /belownormal /wait /b python build\agent9\cg26-check\cg26_check.py --arm A
#       --gen build\agent2\cg26\DimensionsRecomp\rexlego\generated
#       --ref build\agent2\snap1\DimensionsRecomp\rexlego\generated
#       --config build\agent2\cg26\DimensionsRecomp\rexlego\legodimensions_config.toml
#       --tool build\agent2\cg26\tool\rexglue.exe --bin build\agent2\<CG26 bin dir> --out build\agent9\cg26-check\run-X
#
# Gates. Exit 0 = RESULT: PASS, 1 = RESULT: FAIL, 2 = RESULT: INCOMPLETE (no --tool or --bin, so a part was skipped)
# or a usage error, 3 = HELD: the stop file (--hold, default perf-notes/WINDOW-HOLD.txt in this workspace) exists or
# appeared during the run; nothing is written, so run it again after the window.
#  (a) Both changes are in one build:
#      - the config toml has exactly one root-level 'db16cyc_pause = true' and is otherwise the arm's base toml;
#      - codegen.d names that toml;
#      - the tool carries the option (strings 'db16cyc_pause' and '\tsimde_mm_pause();');
#      - the regen's stamps agree with each other, differ from the reference's, and are newer than the toml;
#      - the regen emitted the pauses;
#      - the staged exe is newer than the regen.
#  (b) There are exactly 20 '\tsimde_mm_pause();' lines, each directly after a '\t// db16cyc ' line, all in the arm's
#      10 TUs and functions (Agent 9 R2.17). There is no '_mm_pause' anywhere else, and each TU minus its pause lines
#      is byte-identical to the reference TU.
#  (c) codegen.partition.json is unchanged (it is the arm's sidecar). No file differs from the reference except the
#      10 TUs and the three stamp files (codegen.stamp, codegen.build.stamp, codegen.d).
#  (d) The staged bin's MANIFEST: every row's sha256 and size are recomputed from the staged file.
# Output under --out: report.txt (every PASS/FAIL/NOTE/SKIP line), diff-summary.md (per TU and per site), sites.tsv.
import argparse
import collections
import difflib
import hashlib
import json
import os
import posixpath
import re
import sys
import time

PAUSE = b'\tsimde_mm_pause();'      # what build_db16cyc prints when db16cyc_pause is set (staged system.cpp diff)
SITE = b'\t// db16cyc '              # the comment the codegen prints for each db16cyc instruction
ANY_PAUSE = b'_mm_pause'             # any spelling of a pause counts as a pause site
FUNC_RE = re.compile(rb'^DEFINE_REX_FUNC\((\w+)\)')
LABEL_RE = re.compile(rb'^(loc_[0-9A-Fa-f]{8}):')
TU_RE = re.compile(r'^legodimensions_recomp\.(\d+)\.cpp$')
HEX64_RE = re.compile(r'(?<![0-9A-Fa-f])[0-9A-Fa-f]{64}(?![0-9A-Fa-f])')
KEY_RE = re.compile(rb'^\s*db16cyc_pause\s*=')
ON_RE = re.compile(rb'^\s*db16cyc_pause\s*=\s*true\s*(#.*)?$')
TOOL_MARKS = (b'db16cyc_pause', b'\tsimde_mm_pause();')
STAMP_FILES = ('codegen.stamp', 'codegen.build.stamp', 'codegen.d')
WATCH = ('sources.cmake', 'legodimensions_funcs.h', 'legodimensions_init.cpp', 'legodimensions_init.h',
         'legodimensions_register.cpp', 'legodimensions_pch.h')
EXPECTED_TOTAL = 20

# Agent 9 R2.17 (perf-notes/agent9-codegen.md): the 20 db16cyc sites as function -> (TU, count), per arm and partition.
# Agent 9 R2.11.3/HASHES.txt: the base and the ON codegen config toml of each arm.
ARMS = {
    'A': {'partition': '22C9D89BEA8E8C6E',
          'toml_base': '7F775847DB9CC2DA89DC3EDE57A0AD5F30FDF58D98F5021A0E27A4E0E4DA95BF',
          'toml_new': '11707872E82D8B524D59B2E62DEABBABB90F10E2707CB2825338A920BD4D5FCF',
          'sites': {'sub_83FAF180': (107, 8), 'sub_83F99F80': (116, 2), 'sub_83F9A5B0': (321, 2),
                    'sub_83FCB608': (205, 2), 'sub_83E66CD8': (169, 1), 'sub_83EA90D0': (153, 1),
                    'sub_83E63F38': (432, 1), 'sub_83E96348': (304, 1), 'sub_83E70320': (284, 1),
                    'sub_83E64900': (125, 1)}},
    'B': {'partition': '9DADABCC6F543432',
          'toml_base': 'E60EAF1CEB575572BA0274AA5F52E97F25A35C01690B41E6A637739408E6A090',
          'toml_new': 'FFC119BFE2639E30E8CEC4E5258F1428DB06C62E0E880003DCF9EF1113B7B570',
          'sites': {'sub_83FAF180': (383, 8), 'sub_83F99F80': (107, 2), 'sub_83F9A5B0': (354, 2),
                    'sub_83FCB608': (389, 2), 'sub_83E66CD8': (162, 1), 'sub_83EA90D0': (265, 1),
                    'sub_83E63F38': (281, 1), 'sub_83E96348': (329, 1), 'sub_83E70320': (378, 1),
                    'sub_83E64900': (394, 1)}},
}


class Report:
    ORDER = ('a', 'b', 'c', 'd')
    TITLES = {'a': '(a) the toml line and the new codegen tool are in the same build',
              'b': '(b) the 20 pause sites',
              'c': '(c) codegen.partition.json and the rest of the tree unchanged',
              'd': '(d) the staged bin MANIFEST'}

    def __init__(self):
        self.rows = {k: [] for k in self.ORDER}
        self.fails, self.skips = [], []

    def check(self, gate, what, ok, detail=''):
        self.rows[gate].append('%s %s%s' % ('PASS' if ok else 'FAIL', what, (': ' + detail) if detail else ''))
        if not ok:
            self.fails.append('(%s) %s' % (gate, what))
        return ok

    def note(self, gate, what):
        self.rows[gate].append('NOTE ' + what)

    def skip(self, gate, what):
        self.rows[gate].append('SKIP ' + what)
        self.skips.append('(%s) %s' % (gate, what))


HOLD_PATH = None                      # set from --hold in main()
HELD_EXIT = 3


class Held(Exception):
    pass


def hold_check():
    if HOLD_PATH and os.path.exists(HOLD_PATH):
        raise Held()


def rd(path):
    hold_check()
    with open(path, 'rb') as f:
        return f.read()


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest().upper()


def sha_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            hold_check()
            h.update(blk)
    return h.hexdigest().upper()


def jn(root, rel):
    return os.path.join(root, *rel.split('/'))


def walk(root):
    out = []
    for dp, dns, fns in os.walk(root):
        dns.sort()
        for fn in fns:
            out.append(os.path.relpath(os.path.join(dp, fn), root).replace(os.sep, '/'))
    return sorted(out)


def codegen_dir(root):
    for cand in (root, os.path.join(root, 'default')):
        if os.path.isfile(os.path.join(cand, 'codegen.partition.json')):
            return cand
    for dp, _dns, fns in os.walk(root):
        if 'codegen.partition.json' in fns:
            return dp
    return None


def count_sites(data):
    return data.count(b'\n' + SITE) + (1 if data.startswith(SITE) else 0)


def norm(path):
    return os.path.normcase(os.path.abspath(path.replace('/', os.sep)))


def show(path):
    p = os.path.abspath(path)
    try:
        r = os.path.relpath(p, os.getcwd())
    except ValueError:
        return p
    return p if r.startswith('..') else r


def tstr(t):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))


def parse_depfile(data):
    text = data.decode('utf-8', 'replace').replace('\\\r\n', ' ').replace('\\\n', ' ')
    m = re.search(r':\s', text)
    if not m:
        return None, []
    return text[:m.start()].strip(), text[m.end():].split()


def load_json(path):
    try:
        return json.loads(rd(path).decode('utf-8'))
    except (OSError, ValueError):
        return None


def align(ref_lines, gen_lines):
    """Walk both line lists in lockstep. A gen line that is exactly PAUSE and does not match the reference is an
    insertion. Returns (insertions [(gen_idx, ref_idx)], clean, (i, j) = where the first other difference is)."""
    i = j = 0
    ins = []
    nr, ng = len(ref_lines), len(gen_lines)
    while True:
        if i < nr and j < ng and ref_lines[i] == gen_lines[j]:
            i += 1
            j += 1
            continue
        if j < ng and gen_lines[j].rstrip(b'\r') == PAUSE:
            ins.append((j, i))
            j += 1
            continue
        break
    return ins, (i == nr and j == ng), (i, j)


def dec(line):
    return line.decode('utf-8', 'replace').rstrip('\r')


def local_diff(ref_lines, gen_lines, i, j, name, span=12, limit=40):
    a0, b0 = max(0, i - 3), max(0, j - 3)
    a = [dec(x) for x in ref_lines[a0:i + span]]
    b = [dec(x) for x in gen_lines[b0:j + span]]
    d = list(difflib.unified_diff(a, b, 'ref/%s (from line %d)' % (name, a0 + 1), 'gen/%s (from line %d)' % (name, b0 + 1),
                                  lineterm='', n=2))
    return d[:limit]


def parse_manifest(text, bin_names):
    rows = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s.startswith('#'):
            continue
        f = [x.strip() for x in s.split('\t')]
        if len(f) >= 4 and re.fullmatch(r'[0-9A-Fa-f]{64}', f[3]):        # name size mtime sha256 [source]
            rows.append({'name': f[0], 'size': f[1], 'sha': f[3].upper(), 'src': f[4] if len(f) > 4 else ''})
            continue
        m = re.match(r'^([0-9A-Fa-f]{64})\s+\*?(.+)$', s)                  # sha256sum style
        if m:
            rows.append({'name': m.group(2).strip(), 'size': '', 'sha': m.group(1).upper(), 'src': ''})
            continue
        hx = HEX64_RE.findall(s)                                          # anything else: one hash + one staged name
        names = [t for t in re.split(r'[\s,;|]+', s) if t in bin_names]
        if len(hx) == 1 and len(names) == 1:
            rows.append({'name': names[0], 'size': '', 'sha': hx[0].upper(), 'src': ''})
    return rows


def main():
    ap = argparse.ArgumentParser(description='CG26 (#26 db16cyc_pause ON) static check kit (Agent 9, task #18)')
    ap.add_argument('--arm', required=True, choices=sorted(ARMS))
    ap.add_argument('--gen', required=True, help='the CG26 regen output (rexlego/generated)')
    ap.add_argument('--ref', required=True, help='the reference (pinned, OFF) output of the same arm')
    ap.add_argument('--config', required=True, help='the codegen config toml the regen used')
    ap.add_argument('--tool', help='the codegen tool (rexglue.exe) the regen used')
    ap.add_argument('--tool-sha', help='the expected sha256 (or a prefix) of --tool')
    ap.add_argument('--bin', help='the staged CG26 bin dir')
    ap.add_argument('--manifest', help='the MANIFEST file (default: MANIFEST* in --bin)')
    ap.add_argument('--out', required=True, help='the report dir (report.txt, diff-summary.md, sites.tsv)')
    ap.add_argument('--hold', default=os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                                                                     '..', '..', 'perf-notes', 'WINDOW-HOLD.txt')),
                    help='stop file: if it exists or appears, stop with exit 3 and no report ("none" = off)')
    a = ap.parse_args()
    global HOLD_PATH
    HOLD_PATH = None if a.hold.lower() == 'none' else a.hold
    hold_check()
    t0 = time.time()
    arm = ARMS[a.arm]
    rep = Report()
    for what, p, isdir in (('--gen', a.gen, True), ('--ref', a.ref, True), ('--config', a.config, False),
                           ('--tool', a.tool, False), ('--bin', a.bin, True), ('--manifest', a.manifest, False)):
        if p and not (os.path.isdir(p) if isdir else os.path.isfile(p)):
            print('ERROR: %s %s does not exist' % (what, p))
            return 2
    gcd, rcd = codegen_dir(a.gen), codegen_dir(a.ref)
    if not gcd or not rcd:
        print('ERROR: no codegen.partition.json under %s' % (a.ref if gcd else a.gen))
        return 2
    cg_rel = os.path.relpath(gcd, a.gen).replace(os.sep, '/')
    cg_dir = '' if cg_rel == '.' else cg_rel

    def crel(name):
        return name if not cg_dir else cg_dir + '/' + name

    head = ['# cg26_check.py (Agent 9, run-2 task #18)  %s  kit sha256 %s' % (
                time.strftime('%Y-%m-%d %H:%M:%S'), sha_file(os.path.abspath(__file__))[:16]),
            '# arm %s; R2.17 sites %s' % (a.arm, ', '.join('%s TU%d x%d' % (f, tu, n) for f, (tu, n) in
                                                         arm['sites'].items())),
            '# gen    %s  (codegen dir %s)' % (show(a.gen), cg_rel),
            '# ref    %s' % show(a.ref),
            '# config %s' % show(a.config),
            '# tool   %s' % (show(a.tool) if a.tool else '-'),
            '# bin    %s' % (show(a.bin) if a.bin else '-'),
            '# hold   %s' % (show(HOLD_PATH) if HOLD_PATH else 'off')]
    if os.path.relpath(rcd, a.ref).replace(os.sep, '/') != cg_rel:
        rep.note('c', 'the codegen dir is %s in gen but %s in ref' % (cg_rel, os.path.relpath(rcd, a.ref)))

    # ---- one pass over both trees: byte compare, pause text, db16cyc comment lines ----
    gfiles, rfiles = walk(a.gen), walk(a.ref)
    gset, rset = set(gfiles), set(rfiles)
    differ, gen_pause, ref_pause, gen_sites, ref_sites = [], {}, {}, {}, {}
    nbytes = 0
    for rel in sorted(gset | rset):
        g = rd(jn(a.gen, rel)) if rel in gset else None
        r = rd(jn(a.ref, rel)) if rel in rset else None
        for data, pauses, sites in ((g, gen_pause, gen_sites), (r, ref_pause, ref_sites)):
            if data is None:
                continue
            nbytes += len(data)
            n = data.count(ANY_PAUSE)
            if n:
                pauses[rel] = n
            if rel.endswith('.cpp'):
                s = count_sites(data)
                if s:
                    sites[rel] = s
        if g is not None and r is not None and g != r:
            differ.append(rel)
    scan_s = time.time() - t0

    exp_rel = {}                       # rel -> (function, count, TU)
    for func, (tu, n) in arm['sites'].items():
        exp_rel[crel('legodimensions_recomp.%d.cpp' % tu)] = (func, n, tu)
    stamp_rels = {crel(s) for s in STAMP_FILES}

    # ---- (c) the tree ----
    only_g, only_r = sorted(gset - rset), sorted(rset - gset)
    rep.check('c', 'same file list as the reference', not only_g and not only_r,
              '%d files' % len(gfiles) if not only_g and not only_r else 'only in gen %d %s; only in ref %d %s' % (
                  len(only_g), only_g[:5], len(only_r), only_r[:5]))
    other = [r for r in differ if r not in exp_rel and r not in stamp_rels]
    rep.check('c', 'no file differs except the 10 TUs and the 3 stamp files', not other,
              '%d differ: %s' % (len(differ), ' '.join(posixpath.basename(r) for r in differ)) if not other else
              'unexpected %d: %s' % (len(other), ' '.join(other[:12])))
    prel = crel('codegen.partition.json')
    gp = rp = ''
    if prel in gset and prel in rset:
        gp, rp = sha_file(jn(a.gen, prel)), sha_file(jn(a.ref, prel))
        rep.check('c', 'codegen.partition.json unchanged', gp == rp, 'gen %s, ref %s' % (gp[:16], rp[:16]))
        rep.check('c', 'codegen.partition.json is the arm-%s sidecar %s' % (a.arm, arm['partition']),
                  gp.startswith(arm['partition']), gp[:16])
    else:
        rep.check('c', 'codegen.partition.json present in both trees', False, prel)
    for name in WATCH:
        rel = crel(name)
        if rel in gset and rel in rset:
            rep.check('c', '%s unchanged' % name, rel not in differ, sha_file(jn(a.gen, rel))[:16])
    hdr = [r for r in gfiles if r.endswith('.h')]
    hdr_diff = [r for r in differ if r.endswith('.h')]
    rep.check('c', 'every header unchanged (%d .h files)' % len(hdr), not hdr_diff, ' '.join(hdr_diff[:10]))
    for s in STAMP_FILES:
        rel = crel(s)
        rep.note('c', '%s %s' % (s, 'differs from the reference (expected after a regen)' if rel in differ else
                                 'is identical to the reference' if rel in gset and rel in rset else 'missing'))

    # ---- (b) the sites ----
    want_sites = {rel: v[1] for rel, v in exp_rel.items()}

    def sites_detail(have):
        keys = sorted(set(have) | set(want_sites))
        bad = ['%s %d (want %d)' % (posixpath.basename(k), have.get(k, 0), want_sites.get(k, 0)) for k in keys
               if have.get(k, 0) != want_sites.get(k, 0)]
        return ('%d sites in %d TUs' % (sum(have.values()), len(have))) if not bad else '; '.join(bad[:10])

    rep.check('b', 'the reference has the 20 db16cyc sites in the arm-%s TUs' % a.arm, ref_sites == want_sites,
              sites_detail(ref_sites))
    rep.check('b', 'the reference has no _mm_pause text', not ref_pause,
              ' '.join('%s x%d' % (posixpath.basename(k), v) for k, v in sorted(ref_pause.items())[:10]))
    rep.check('b', 'gen has the same db16cyc comment lines per TU as the reference', gen_sites == ref_sites,
              sites_detail(gen_sites))
    sites = []
    for rel in sorted(gen_pause):
        lines = rd(jn(a.gen, rel)).split(b'\n')
        m = TU_RE.match(posixpath.basename(rel))
        tu = int(m.group(1)) if m and posixpath.dirname(rel) == cg_dir else None
        func = label = None
        for k, ln in enumerate(lines):
            fm = FUNC_RE.match(ln)
            if fm:
                func, label = fm.group(1).decode(), None
            lm = LABEL_RE.match(ln)
            if lm:
                label = lm.group(1).decode()
            if ANY_PAUSE in ln:
                exp = arm['sites'].get(func)
                sites.append({'rel': rel, 'tu': tu, 'line': k + 1, 'func': func or '?', 'label': label or '-',
                              'exact': ln.rstrip(b'\r') == PAUSE, 'n': ln.count(ANY_PAUSE),
                              'after_site': k > 0 and lines[k - 1].startswith(SITE),
                              'where_ok': bool(exp) and exp[0] == tu and rel in exp_rel})
    n_exact = sum(1 for s in sites if s['exact'])
    n_any = sum(gen_pause.values())
    rep.check('b', 'exactly %d pause lines (\\tsimde_mm_pause();)' % EXPECTED_TOTAL, n_exact == EXPECTED_TOTAL,
              '%d' % n_exact)
    rep.check('b', "no other '_mm_pause' text anywhere in gen (%d files scanned)" % len(gfiles),
              n_any == n_exact and all(s['exact'] and s['n'] == 1 for s in sites),
              '%d occurrence(s) in %d file(s)' % (n_any, len(gen_pause)))
    outside = sorted({s['rel'] for s in sites if s['rel'] not in exp_rel})
    rep.check('b', 'no pause outside the arm-%s 10 TUs' % a.arm, not outside, ' '.join(outside[:10]))
    bad_where = [s for s in sites if not s['where_ok']]
    rep.check('b', 'every pause is in its expected function and TU', not bad_where, '; '.join(
        '%s:%d in %s' % (posixpath.basename(s['rel']), s['line'], s['func']) for s in bad_where[:8]))
    orphans = [s for s in sites if not s['after_site']]
    rep.check('b', "every pause line directly follows a '\\t// db16cyc ' line", not orphans, '; '.join(
        '%s:%d' % (posixpath.basename(s['rel']), s['line']) for s in orphans[:8]))
    per_func = dict(collections.Counter(s['func'] for s in sites))
    want_func = {f: n for f, (tu, n) in arm['sites'].items()}
    rep.check('b', 'per-function pause counts == R2.17 (8, 2, 2, 2 and six 1s)', per_func == want_func, '; '.join(
        '%s %d (want %d)' % (f, per_func.get(f, 0), want_func.get(f, 0)) for f in sorted(set(per_func) | set(want_func))
        if per_func.get(f, 0) != want_func.get(f, 0)) or '10 functions')

    tu_rows, hunks, site_rows = [], [], []
    by_line = {(s['rel'], s['line']): s for s in sites}
    on_tu_sha = {}
    newest_tu = 0.0
    for rel in sorted(exp_rel, key=lambda r: exp_rel[r][2]):
        func, n, tu = exp_rel[rel]
        if rel not in gset or rel not in rset:
            rep.check('b', 'TU%d present in both trees' % tu, False, rel)
            continue
        rb_, gb_ = rd(jn(a.ref, rel)), rd(jn(a.gen, rel))
        on_tu_sha[rel] = sha_bytes(gb_)
        newest_tu = max(newest_tu, os.path.getmtime(jn(a.gen, rel)))
        rl, gl = rb_.split(b'\n'), gb_.split(b'\n')
        ins, clean, (i, j) = align(rl, gl)
        unfollowed = sum(1 for k, ln in enumerate(gl) if ln.startswith(SITE) and not (
            k + 1 < len(gl) and gl[k + 1].rstrip(b'\r') == PAUSE))
        rep.check('b', 'TU%d %s: %d pause line(s), one after each db16cyc site; minus them == the reference' % (
            tu, func, n), clean and len(ins) == n and unfollowed == 0,
            'inserted %d, db16cyc sites without a pause %d, rest identical %s' % (
                len(ins), unfollowed, 'yes' if clean else 'NO (first other difference at ref line %d / gen line %d)' % (
                    i + 1, j + 1)))
        tu_rows.append((tu, func, n, len(ins), unfollowed, clean, len(rl), len(gl), sha_bytes(rb_)[:16],
                        on_tu_sha[rel][:16]))
        for gj, ri in ins:
            s = by_line.get((rel, gj + 1), {})
            ctx = [dec(x) for x in gl[max(0, gj - 3):gj + 2]]
            site_rows.append({'tu': tu, 'rel': rel, 'func': s.get('func', '?'), 'label': s.get('label', '-'),
                              'gen_line': gj + 1, 'ref_line': ri, 'after_site': s.get('after_site', False),
                              'where_ok': s.get('where_ok', False), 'ctx': ctx})
        if not clean:
            hunks.append((rel, local_diff(rl, gl, i, j, posixpath.basename(rel))))
    for rel in [r for r in differ if r.endswith('.cpp') and r not in exp_rel][:3]:
        rb_, gb_ = rd(jn(a.ref, rel)), rd(jn(a.gen, rel))
        rl, gl = rb_.split(b'\n'), gb_.split(b'\n')
        ins, clean, (i, j) = align(rl, gl)
        if ins:
            rep.note('b', '%s (not an expected TU): %d pause line(s) inserted' % (posixpath.basename(rel), len(ins)))
        hunks.append((rel, local_diff(rl, gl, i, j, posixpath.basename(rel)) if not clean else
                      ['(only pause lines inserted, at gen lines %s)' % ', '.join(str(x[0] + 1) for x in ins)]))

    # ---- (a) one build has both ----
    cfg_b = rd(a.config)
    cfg_sha = sha_bytes(cfg_b)
    tl = cfg_b.split(b'\n')
    keys = [k for k, ln in enumerate(tl) if KEY_RE.match(ln)]
    first_table = next((k for k, ln in enumerate(tl) if ln.lstrip().startswith(b'[')), len(tl))
    line_ok = len(keys) == 1 and bool(ON_RE.match(tl[keys[0]].rstrip(b'\r'))) and keys[0] < first_table
    rep.check('a', "config toml has exactly one root-level 'db16cyc_pause = true' (before the first [table])", line_ok,
              ('line %d' % (keys[0] + 1)) if line_ok else '%d db16cyc_pause line(s)%s' % (
                  len(keys), (': line %d %r' % (keys[0] + 1, dec(tl[keys[0]]))) if keys else ''))
    if len(keys) == 1:
        base_sha = sha_bytes(b'\n'.join(tl[:keys[0]] + tl[keys[0] + 1:]))
        rep.check('a', 'config toml minus that line == the arm-%s base toml %s' % (a.arm, arm['toml_base'][:16]),
                  base_sha == arm['toml_base'], base_sha[:16])
    if cfg_sha == arm['toml_new']:
        rep.note('a', 'config toml sha256 %s == Agent 9 staged new-%s toml (HASHES.txt)' % (cfg_sha[:16], a.arm))
    else:
        rep.note('a', 'config toml sha256 %s != Agent 9 staged new-%s toml %s' % (cfg_sha[:16], a.arm,
                                                                                 arm['toml_new'][:16]))
    dpath = os.path.join(gcd, 'codegen.d')
    if os.path.isfile(dpath):
        target, deps = parse_depfile(rd(dpath))
        toms = [d for d in deps if d.lower().endswith('_config.toml')]
        if len(toms) == 1 and os.path.isfile(toms[0]):
            dsha = sha_file(toms[0])
            rep.check('a', 'codegen.d names a config toml with this content', dsha == cfg_sha, '%s %s%s' % (
                toms[0], dsha[:16], '' if norm(toms[0]) == norm(a.config) else ' (another path)'))
        else:
            rep.check('a', 'codegen.d names exactly one readable *_config.toml', False, ' '.join(toms) or 'none')
        if target and os.path.dirname(norm(target)) != norm(gcd):
            rep.note('a', 'codegen.d target is %s (this output was written elsewhere and copied)' % target)
    else:
        rep.check('a', 'codegen.d present', False, dpath)
    gs, rs = load_json(os.path.join(gcd, 'codegen.stamp')), load_json(os.path.join(rcd, 'codegen.stamp'))
    gfp = (gs or {}).get('fingerprint', '') if isinstance(gs, dict) else ''
    rfp = (rs or {}).get('fingerprint', '') if isinstance(rs, dict) else ''
    rep.check('a', 'codegen.stamp is a version-1 stamp with a fingerprint', isinstance(gs, dict) and
              gs.get('version') == 1 and bool(re.fullmatch(r'[0-9a-f]{32}', gfp)), gfp or 'unreadable')
    bpath = os.path.join(gcd, 'codegen.build.stamp')
    bfp = rd(bpath).decode('ascii', 'replace').strip() if os.path.isfile(bpath) else '<missing>'
    rep.check('a', 'codegen.build.stamp == the codegen.stamp fingerprint (one regen wrote both)', bfp == gfp,
              '%s vs %s' % (bfp, gfp))
    rep.check('a', 'the fingerprint differs from the reference (the inputs changed since the reference)',
              bool(gfp) and gfp != rfp, 'gen %s, ref %s' % (gfp, rfp))
    if isinstance(gs, dict) and isinstance(rs, dict):
        go, ro = gs.get('outputs') or [], rs.get('outputs') or []
        rep.check('a', 'the stamp lists the same outputs as the reference (%d)' % len(ro), sorted(go) == sorted(ro),
                  '' if sorted(go) == sorted(ro) else 'only gen %s; only ref %s' % (
                      sorted(set(go) - set(ro))[:5], sorted(set(ro) - set(go))[:5]))
        missing = [o for o in go if not os.path.isfile(os.path.join(gcd, o))]
        rep.check('a', 'every stamp output exists', not missing, ' '.join(missing[:5]))
    st = os.path.getmtime(os.path.join(gcd, 'codegen.stamp')) if os.path.isfile(os.path.join(gcd, 'codegen.stamp')) \
        else 0.0
    ct = os.path.getmtime(a.config)
    rep.check('a', 'the regen ran after the toml landed', st >= ct, 'codegen.stamp %s, toml %s' % (tstr(st), tstr(ct)))
    tsha = ''
    if a.tool:
        tb = rd(a.tool)
        tsha = sha_bytes(tb)
        marks = [(m, m in tb) for m in TOOL_MARKS]
        rep.check('a', 'the tool has the db16cyc_pause option (sha256 %s)' % tsha[:16], all(v for _m, v in marks),
                  ', '.join('%r %s' % (m.decode(), 'yes' if v else 'NO') for m, v in marks))
        if a.tool_sha:
            rep.check('a', 'tool sha256 == --tool-sha %s' % a.tool_sha, tsha.startswith(a.tool_sha.upper()), tsha[:16])
        tt = os.path.getmtime(a.tool)
        if st < tt:
            rep.note('a', 'the tool file (%s) is newer than codegen.stamp (%s): re-staged after the regen?' % (
                tstr(tt), tstr(st)))
    else:
        rep.skip('a', 'no --tool: the codegen tool was not inspected')
    rep.check('a', 'the regen emitted the pauses (both the toml line and the new tool were in effect)',
              n_exact == EXPECTED_TOTAL, '%d of %d' % (n_exact, EXPECTED_TOTAL))
    if n_exact == 0:
        rep.note('a', 'ADVICE: no pause lines, so no regen ran with both the line and the new tool. If codegen.stamp '
                      'is newer than the toml, an old tool took the stamp and a new-tool run will skip the regen: '
                      'delete codegen.stamp (or pass --ignore-stamp) and force one regen with the new tool. '
                      'Touching the toml does not force one: the fingerprint hashes input contents, not mtimes.')

    # ---- (d) the staged bin, and its link to this regen ----
    if a.bin:
        man = a.manifest
        if not man:
            cands = sorted(f for f in os.listdir(a.bin) if f.upper().startswith('MANIFEST') and
                           os.path.isfile(os.path.join(a.bin, f)))
            man = os.path.join(a.bin, cands[0]) if cands else None
        staged = sorted(f for f in os.listdir(a.bin) if os.path.isfile(os.path.join(a.bin, f)))
        if not man:
            rep.check('d', 'a MANIFEST file in the bin', False, show(a.bin))
        else:
            text = rd(man).decode('utf-8', 'replace')
            rows = parse_manifest(text, set(staged))
            rep.check('d', 'MANIFEST %s has hash rows' % show(man), bool(rows), '%d rows' % len(rows))
            for row in rows:
                p = os.path.join(a.bin, row['name'])
                if not os.path.isfile(p):
                    rep.check('d', '%s: the staged file exists' % row['name'], False, p)
                    continue
                h, sz = sha_file(p), os.path.getsize(p)
                ok = h == row['sha'] and (not row['size'] or row['size'] == str(sz))
                rep.check('d', '%s sha256 and size == MANIFEST' % row['name'], ok, '%s %d B' % (h[:16], sz) if ok else
                          'file %s %d B, MANIFEST %s %s B' % (h[:16], sz, row['sha'][:16], row['size'] or '?'))
                if row['src'] and row['name'].lower().endswith(('.exe', '.map')):
                    rep.note('d', '%s source in the MANIFEST: %s' % (row['name'], row['src']))
            listed = {row['name'] for row in rows} | {os.path.basename(man)}
            unlisted = [f for f in staged if f not in listed]
            if unlisted:
                rep.note('d', 'staged but not in the MANIFEST: %s' % ' '.join(unlisted))
            up = text.upper()
            hexes = {h.upper() for h in HEX64_RE.findall(text)}

            def named(h):
                return bool(h) and (h in hexes or h[:16] in up)

            rep.note('a', 'the bin MANIFEST names: the tool sha256 %s, the config toml sha256 %s, ON TU sha256s %d/10'
                     % ('yes' if named(tsha) else 'no', 'yes' if named(cfg_sha) else 'no',
                        sum(1 for v in on_tu_sha.values() if named(v))))
        exe = os.path.join(a.bin, 'legodimensions.exe')
        if os.path.isfile(exe) and newest_tu:
            et = os.path.getmtime(exe)
            rep.check('a', 'the staged exe is newer than the regen', et >= newest_tu,
                      'exe %s, newest of the 10 TUs %s' % (tstr(et), tstr(newest_tu)))
        else:
            rep.note('a', 'no legodimensions.exe in the bin: exe-vs-regen time not checked')
    else:
        rep.skip('d', 'no --bin: the MANIFEST was not checked')
        rep.skip('a', 'no --bin: the bin was not tied to the regen')

    # ---- result and outputs ----
    if rep.fails:
        res, code = 'FAIL (%d)' % len(rep.fails), 1
    elif rep.skips:
        res, code = 'INCOMPLETE (%d skipped)' % len(rep.skips), 2
    else:
        res, code = 'PASS', 0
    out = list(head)
    out.append('# scanned %d + %d files, %.1f MB, %.1f s' % (len(gfiles), len(rfiles), nbytes / 1e6, scan_s))
    for g in Report.ORDER:
        out.append('== ' + Report.TITLES[g])
        out.extend(rep.rows[g])
    if rep.fails:
        out.append('== failed: ' + ' | '.join(rep.fails))
    out.append('RESULT: %s  (%.1f s)' % (res, time.time() - t0))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, 'report.txt'), 'w', encoding='ascii', errors='replace', newline='\n') as f:
        f.write('\n'.join(out) + '\n')

    md = ['# CG26 generated-diff summary (Agent 9 cg26_check.py, task #18)', '',
          '%s, arm %s. gen `%s`, ref `%s`. **RESULT: %s**' % (time.strftime('%Y-%m-%d %H:%M:%S'), a.arm, show(a.gen),
                                                             show(a.ref), res), '',
          'Expected: each of the 10 TUs gains exactly one line, `\\tsimde_mm_pause();`, right after each '
          '`\\t// db16cyc ` line, and nothing else changes. Elsewhere only codegen.stamp, codegen.build.stamp and '
          'codegen.d may differ.', '',
          '## Per TU', '',
          '| TU | function | pauses expected | lines inserted | db16cyc sites without a pause | rest identical | '
          'ref lines | gen lines | ref sha256 | gen sha256 |',
          '|---|---|---|---|---|---|---|---|---|---|']
    for r in tu_rows:
        md.append('| %d | %s | %d | %d | %d | %s | %d | %d | %s | %s |' % (r[0], r[1], r[2], r[3], r[4],
                                                                         'yes' if r[5] else '**NO**', r[6], r[7], r[8],
                                                                         r[9]))
    md += ['', '## Per site (%d inserted pause lines in the 10 TUs; %d pause lines in the whole tree)' % (
        len(site_rows), n_exact), '',
           '| # | TU | function | label | gen line | ref line of the db16cyc comment | after a db16cyc line | '
           'expected place |', '|---|---|---|---|---|---|---|---|']
    for k, s in enumerate(site_rows, 1):
        md.append('| %d | %d | %s | %s | %d | %d | %s | %s |' % (k, s['tu'], s['func'], s['label'], s['gen_line'],
                                                                s['ref_line'], 'yes' if s['after_site'] else '**NO**',
                                                                'yes' if s['where_ok'] else '**NO**'))
    stray = [s for s in sites if s['rel'] not in exp_rel]
    if stray:
        md += ['', '**Pause text outside the 10 TUs:** ' + '; '.join('%s:%d (%s)' % (s['rel'], s['line'], s['func'])
                                                                     for s in stray[:20])]
    md += ['', '## Context (gen lines: 3 before each pause, the pause, 1 after)', '']
    for tu in sorted({s['tu'] for s in site_rows}):
        md.append('TU%d (%s):' % (tu, exp_rel[crel('legodimensions_recomp.%d.cpp' % tu)][0]))
        md.append('```')
        for s in [x for x in site_rows if x['tu'] == tu]:
            md.append('-- gen line %d, %s' % (s['gen_line'], s['label']))
            md.extend(s['ctx'])
        md.append('```')
    md += ['', '## Other differences', '']
    for sname in STAMP_FILES:
        rel = crel(sname)
        if rel in differ:
            if sname == 'codegen.d':
                md.append('- codegen.d differs (it names the regen tree and toml).')
            else:
                md.append('- %s differs: fingerprint %s -> %s.' % (sname, rfp or '?', gfp or '?'))
        elif rel in gset:
            md.append('- %s is identical to the reference.' % sname)
    if other:
        md.append('- **Unexpected differing files (%d):** %s' % (len(other), ' '.join(other[:30])))
    for rel, d in hunks:
        md += ['', 'Unexpected change in `%s` (first one; up to 40 diff lines):' % rel, '```diff'] + d + ['```']
    if not other and not hunks:
        md.append('- None.')
    with open(os.path.join(a.out, 'diff-summary.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(md) + '\n')
    with open(os.path.join(a.out, 'sites.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('n\tTU\tfunction\tlabel\tgen_line\tref_line_db16cyc\tafter_site\texpected_place\tfile\n')
        for k, s in enumerate(site_rows, 1):
            f.write('%d\t%d\t%s\t%s\t%d\t%d\t%s\t%s\t%s\n' % (k, s['tu'], s['func'], s['label'], s['gen_line'],
                                                              s['ref_line'], s['after_site'], s['where_ok'], s['rel']))
    print('\n'.join(out))
    print('-> %s (report.txt, diff-summary.md, sites.tsv)' % show(a.out))
    return code


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Held:
        print('HOLD: %s exists, so the check stopped without a result. Run it again after the window.' % HOLD_PATH)
        sys.exit(HELD_EXIT)

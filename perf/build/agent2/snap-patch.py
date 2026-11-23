"""Agent 2 - S2: selective, hash-logged patches onto build/agent2/snap1 (Agent 1 at 21:56; SESSION2.md line 760).

S2 = snap1 as it stands (S1 = MANIFEST-S1-*.tsv, plus the PATCHES-*.tsv rows and the NATIVE-INPUTS-*.tsv copies)
plus the LIVE versions of the files the rules select, i.e. the files of the owners Agent 10 has cleared. Every
other file keeps its S1 / S1+pN content: 'plan' and 'apply' stop if snap1 has drifted from that, and 'verify'
checks it afterwards. snap.py is not used for this. A refresh would re-copy every changed live file whatever its
owner, and would re-copy the p1/p2 files from live as 'snapshot tampered'.

Run from anywhere (all paths are absolute):
  python build\\agent2\\snap-patch.py plan   <TAG> <rules>                   report only -> snap1\\PLAN-<TAG>-<HHMM>.txt
  python build\\agent2\\snap-patch.py apply  <TAG> <rules> [--allow-delete]  re-plans, then backs up, copies, logs
  python build\\agent2\\snap-patch.py verify <TAG> [--full]                  snap1 == the latest STATE-<TAG>-*.tsv
  python build\\agent2\\snap-patch.py revert <TAG>                           undo PATCHES-<TAG>.tsv from the backups

Options of plan and apply: --note=TEXT (repeatable) and --note-file=F (one note per non-empty line). Each note is
written as a '# note: ...' line into PLAN-* and DIFF-*, and appended as '; note: ...' to the one '#' header line
of PATCHES-<TAG>.tsv (when apply creates it) and of STATE-<TAG>-*.tsv, so both keep a single header line (S3: Agent
1 asked for the S3 build inputs to be recorded there). Notes must not contain tabs.

What apply does for every selected file whose live content differs from snap1:
  - backs the snap1 version up to build\\agent2\\snap1-backup-<TAG>\\DimensionsRecomp\\<rel> and hash-checks it;
  - copies live -> snap1 and sets mtime = now, so ninja rebuilds everything that depends on it. CMake install keeps
    that mtime, so a changed SDK header also reaches the game trees;
  - checks the copy's sha256 against the planned live hash. If the live file changed after the plan, the run stops;
  - appends a row to snap1\\PATCHES-<TAG>.tsv (same columns as PATCHES-S1.tsv) as it goes.
  Then it writes snap1\\STATE-<TAG>-<HHMM>.tsv (for every file: live size/mtime/sha, snap1 size/mtime/sha, origin)
  and snap1\\DIFF-<TAG>-<HHMM>.txt. STATE-* is deliberately not named MANIFEST-*, so snap.py's load_prev still uses
  S1.
A selected file that is gone from live is deleted from snap1 only with --allow-delete. Two things are never
patched: rexlego/generated (the pinned 0.0.23.3 output) and rexlego/legodimensions_manifest.toml (its game_root is
rewritten in snap1).

Rules file: one rule per line, '#' starts a comment, fields are separated by '|':
  <glob>                              include (relative to DimensionsRecomp/; a leading 'DimensionsRecomp/' is dropped)
  <owner> | <glob>                    the owner label goes into the logs
  <owner> | <glob> | <sha256 prefix>  the live file must also have this hash (8-64 hex digits): the reviewed version
  !<glob>                             exclude (wins over every include)
  @owner <N> [<N> ...]                Agent N's DimensionsRecomp/ claims on .agy-grid/board.json (read only)
  ~<glob>                             accept snap1 drift on these paths (e.g. a file a build rewrote inside snap1):
                                      reported as a warning instead of an error; the file keeps its snap1 content
Globs: '**' spans directories, while '*' and '?' stay within one name. Matching ignores case. Files outside the
snap.py walk (rexlego/out/**, research/**) are matched only by explicit rules: an exact path, or a glob over the
files listed in NATIVE-INPUTS-*.tsv. @owner skips such claims and says so. An exact-path include that matches
nothing, or a file whose hash differs from the one the rule gives, is an error.
"""
import hashlib
import json
import os
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import snap as S  # noqa: E402  (R, LIVE, SNAP, SNAP_ROOT, walk rules, live_path/snap_path, sha, closure_set)

A = os.path.join(S.R, 'build', 'agent2')
BOARD = os.path.join(S.R, '.agy-grid', 'board.json')
LP = S.LP
OUTSIDE = ('rexglue-sdk/out/', 'rexlego/out/', 'rexlego/generated/')
NEVER = ('rexlego/generated/', S.MANIFEST_REL)
NATIVE_PREFIXES = ('rexlego/src/gpu_native/', 'thirdparty/plume/', 'tools/gpu-aot/', 'rexlego/out/', 'research/')


def ts(t, ns=True):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t / 1e9 if ns else t))


def snapfiles(prefix, suffix):
    c = [os.path.join(S.SNAP_ROOT, n) for n in os.listdir(S.SNAP_ROOT)
         if n.startswith(prefix) and n.endswith(suffix) and 'reverted' not in n]
    return sorted(c, key=os.path.getmtime)


def load_tsv_rows(path):
    # utf-8-sig: PATCHES-S1.tsv starts with a BOM, which hid its '#' header line (IndexError in make_plan, 23:13)
    with open(path, encoding='utf-8-sig') as f:
        return [ln.rstrip('\r\n').split('\t') for ln in f if ln.strip() and not ln.startswith('#')]


def stat2(p):
    try:
        st = os.stat(p)
    except OSError:
        return None
    return st.st_size, st.st_mtime_ns


def h16(h):
    return (h or 'ABSENT')[:16]


# ---------------------------------------------------------------- rules
def norm_pat(p):
    p = p.strip().replace('\\', '/')
    if p.lower().startswith('dimensionsrecomp/'):
        p = p[len('dimensionsrecomp/'):]
    return p.lstrip('/')


def wild(p):
    return '*' in p or '?' in p


def glob_re(p):
    out, i = [], 0
    while i < len(p):
        if p.startswith('**/', i):
            out.append('(?:.*/)?')
            i += 3
        elif p.startswith('**', i):
            out.append('.*')
            i += 2
        elif p[i] == '*':
            out.append('[^/]*')
            i += 1
        elif p[i] == '?':
            out.append('[^/]')
            i += 1
        else:
            out.append(re.escape(p[i]))
            i += 1
    return re.compile(''.join(out) + r'\Z', re.I)


def literal(p):
    return re.split(r'[*?]', p, 1)[0].lower()


def outside_walk(p):
    """True when the pattern can only name files that snap.py does not mirror (rexlego/out, research, ...)."""
    lit = literal(p)
    if '/' not in lit:
        return False  # a top-level file, or a top-level wildcard: matched against the walk only
    if lit.split('/', 1)[0] not in [t.lower() for t in S.TOP_DIRS]:
        return True
    return any(lit.startswith(x) or lit + '/' == x for x in OUTSIDE)


def pinned(rel):
    low = rel.lower()
    return any((low + '/').startswith(n.lower()) or low == n.lower() for n in NEVER)


def make_rule(owner, pat, expect, neg, src, explicit):
    pat = norm_pat(pat)
    if not neg and pinned(pat):
        raise SystemExit('%s: %s is pinned and never patched' % (src, pat))
    return {'owner': owner, 'pat': pat, 're': glob_re(pat), 'lit': literal(pat), 'expect': expect, 'neg': neg,
            'outside': outside_walk(pat), 'src': src, 'explicit': explicit, 'hits': 0, 'diff': 0}


def owner_rules(n_agent, src, notes):
    with open(BOARD, encoding='utf-8') as f:
        board = json.load(f)
    out = []
    for c in board.get('claims', []):
        p = str(c.get('pattern', '')).replace('\\', '/')
        if c.get('owner') != n_agent - 1 or not p.lower().startswith('dimensionsrecomp/'):
            continue
        pat = norm_pat(p)
        if outside_walk(pat) or pinned(pat):
            notes.append('%s: @owner %d claim %s is outside the snapshot walk or pinned; not used (name such files '
                         'explicitly)' % (src, n_agent, p))
            continue
        out.append(make_rule('Agent %d' % n_agent, pat, None, False,
                             '%s @owner %d (task %s)' % (src, n_agent, c.get('taskId')), False))
    if not out:
        notes.append('%s: @owner %d has no usable DimensionsRecomp/ claims on the board' % (src, n_agent))
    return out


def load_rules(path):
    rules, notes, accepts = [], [], []
    with open(path, encoding='utf-8-sig') as f:
        lines = f.read().splitlines()
    for n, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        src = 'line %d' % n
        if line.startswith('~'):
            pat = norm_pat(line[1:])
            if not pat:
                raise SystemExit('%s: empty glob' % src)
            accepts.append({'pat': pat, 're': glob_re(pat), 'lit': literal(pat), 'src': src, 'hits': 0})
            continue
        if line.lower().startswith('@owner'):
            for t in re.split(r'[\s,]+', line[6:].strip()):
                if t:
                    rules += owner_rules(int(re.sub(r'(?i)^(agent|a)', '', t)), src, notes)
            continue
        neg = line.startswith('!')
        parts = [x.strip() for x in (line[1:] if neg else line).split('|')]
        expect = None
        if len(parts) == 1:
            owner, pat = '-', parts[0]
        else:
            owner, pat = parts[0] or '-', parts[1]
            if len(parts) > 2 and parts[2]:
                expect = re.sub(r'(?i)^expect\s*=\s*', '', parts[2]).lower()
                if not re.fullmatch(r'[0-9a-f]{8,64}', expect):
                    raise SystemExit('%s: the hash must be 8-64 hex digits, got %r' % (src, parts[2]))
        if not pat:
            raise SystemExit('%s: empty glob' % src)
        rules.append(make_rule(owner, pat, expect, neg, src, True))
    return rules, notes, accepts


def claim_index():
    try:
        with open(BOARD, encoding='utf-8') as f:
            board = json.load(f)
    except (OSError, ValueError):
        return []
    idx = []
    for c in board.get('claims', []):
        p = str(c.get('pattern', '')).replace('\\', '/')
        if p.lower().startswith('dimensionsrecomp/') and isinstance(c.get('owner'), int):
            pat = norm_pat(p)
            idx.append((c['owner'] + 1, literal(pat), glob_re(pat)))
    return idx


def owners_of(rel, idx):
    low = rel.lower()
    s = sorted({n for n, lit, rx in idx if low.startswith(lit) and rx.match(rel)})
    return ','.join('A%d' % n for n in s) if s else 'unclaimed'


# ---------------------------------------------------------------- tree state
def walk_snap():
    """snap1 with snap.py's walk rules (TOP_DIRS + top-level files, minus EXCL_REL and .git/__pycache__ dirs)."""
    files = {}
    with os.scandir(LP + S.SNAP) as it:
        for e in it:
            if e.is_file(follow_symlinks=False) and e.name not in S.EXCL_NAMES:
                st = e.stat(follow_symlinks=False)
                files[e.name] = (st.st_size, st.st_mtime_ns)
    for top in S.TOP_DIRS:
        stack = [top]
        while stack:
            rel = stack.pop()
            try:
                it = os.scandir(S.snap_path(rel))
            except OSError:
                continue
            with it:
                for e in it:
                    r = rel + '/' + e.name
                    if r in S.EXCL_REL or (e.name in S.EXCL_NAMES and e.is_dir(follow_symlinks=False)):
                        continue
                    if e.is_dir(follow_symlinks=False):
                        stack.append(r)
                    else:
                        st = e.stat(follow_symlinks=False)
                        files[r] = (st.st_size, st.st_mtime_ns)
    return files


def native_inputs():
    nat = {}
    for p in snapfiles('NATIVE-INPUTS-', '.tsv'):
        tag = os.path.basename(p).split('-')[2]
        for c in load_tsv_rows(p):
            nat[c[0]] = (tag, c[3].lower())
    return nat


def hash_side(side, files, cache):
    """sha256 for every file; (size, mtime_ns) equal to a cached row means the cached hash (the toml: mtime only)."""
    out, need = {}, []
    for rel, (size, mt) in files.items():
        c = cache.get((side, rel))
        if c and c[1] == mt and (c[0] == size or (side == 'S' and rel == S.MANIFEST_REL)):
            out[rel] = c[2]
        else:
            need.append(rel)
    f = S.live_path if side == 'L' else S.snap_path
    with ThreadPoolExecutor(S.THREADS) as ex:
        for rel, h in zip(need, ex.map(lambda r: S.sha(f(r)), need)):
            out[rel] = h
    return out, need


def toml_logical(lh, sh, sneed):
    """snap1's toml has a rewritten game_root; when it had to be hashed, map it back to the live hash if it is
    exactly the rewrite of the live file (as snap.py's rewrite_game_root writes it)."""
    r = S.MANIFEST_REL
    if r not in sneed or r not in lh:
        return
    with open(S.live_path(r), encoding='utf-8') as f:
        txt = f.read()
    m = re.search(r'^(\s*game_root\s*=\s*")([^"]+)(")', txt, re.M)
    if m:
        target = os.path.normpath(os.path.join(S.LIVE, 'rexlego', m.group(2)))
        new = os.path.relpath(target, os.path.join(S.SNAP, 'rexlego')).replace('\\', '/')
        txt = txt[:m.start(2)] + new + txt[m.end(2):]
    if hashlib.sha256(txt.encode('utf-8')).hexdigest() == sh[r]:
        sh[r] = lh[r]


def is_cmake_input(rel):
    b = rel.rsplit('/', 1)[-1].lower()
    return b in ('cmakelists.txt', 'cmakepresets.json', 'cmakeuserpresets.json') or b.endswith(('.cmake', '.in'))


def build_tag(tag):
    return 'snap' + tag[1:].lower() if tag[:1].upper() == 'S' else 'snap-' + tag.lower()


def rebuild_plan(tag, changed):
    clo = S.closure_set()
    sdk = [r for r in changed if r.startswith('rexglue-sdk/')]
    sdk_cm = [r for r in sdk if is_cmake_input(r)]
    game_cm = [r for r in changed if not r.startswith('rexglue-sdk/') and is_cmake_input(r)]
    hit = [r for r in changed if r.lower() in clo]
    nat = [r for r in changed if r.startswith(NATIVE_PREFIXES)]
    out = ['## REBUILD PLAN (%d changed files)' % len(changed),
           '  rexglue-sdk files: %d (CMake inputs %d) -> %s' % (
               len(sdk), len(sdk_cm), 'SDK build + install into snap1-sdk/install' if sdk else
               'no SDK build; snap1-sdk/install stays'),
           '  closure headers (sdk-headers-dev.txt, %d loaded): %d -> %s' % (
               len(clo), len(hit), 'all 440 generated TUs rebuild in both game trees (OFF about 13 min at -j10)'
               if hit else 'the generated TUs stay'),
           '  game-side CMake inputs: %d -> %s' % (
               len(game_cm), 'reconfigure the game trees (no -SkipConfigure)' if game_cm or sdk_cm else
               '-SkipConfigure is fine'),
           '  native-only paths (gpu_native, plume, gpu-aot, native inputs): %d of %d%s' % (
               len(nat), len(changed), ' -> little or nothing to rebuild in the OFF tree'
               if changed and len(nat) == len(changed) else '')]
    for name, lst in (('SDK CMake inputs', sdk_cm), ('game CMake inputs', game_cm), ('closure headers', hit)):
        if lst:
            out.append('    %s: %s' % (name, ', '.join(lst)))
    cfg = '' if (sdk_cm or game_cm) else ' -SkipConfigure'
    base = 'powershell -NoProfile -ExecutionPolicy Bypass -File build\\agent2\\build-snap.ps1 '
    bt = build_tag(tag)
    if sdk:
        out.append('  1. ' + base + '-Phase sdk -Tag %s -Jobs 10 -KeepGoing%s' % (bt, '' if sdk_cm else ' -SkipConfigure'))
    out.append('  2. ' + base + '-Phase game -Tag %s -Jobs 10 -KeepGoing%s   (devoff)' % (bt, cfg))
    out.append('  3. ' + base + '-Phase game -Native -Tag %s -Jobs 10 -PrelinkJobs 10 -KeepGoing%s   (native)' % (bt, cfg))
    out.append('  then: stage-snap-bin.ps1 -Variant off / -Variant native -SnapTag %s' % tag)
    return out


# ---------------------------------------------------------------- plan
def make_plan(tag, rules_path, allow_delete=False):
    t0 = time.time()
    rules, notes, accepts = load_rules(rules_path) if rules_path else ([], [], [])
    s1_path = snapfiles('MANIFEST-S1-', '.tsv')[-1]
    cache, expected, origin = {}, {}, {}
    for rel, size, mt, h, smt in load_tsv_rows(s1_path):
        cache[('L', rel)] = (int(size), int(mt), h)
        cache[('S', rel)] = (int(size), int(smt), h)
        expected[rel], origin[rel] = h, 'S1'
    nat = native_inputs()
    for rel, (ntag, h) in nat.items():
        expected[rel], origin[rel] = h, ntag
    prow = []
    for p in snapfiles('PATCHES-', '.tsv'):
        prow += load_tsv_rows(p)
    prow.sort(key=lambda c: c[4])

    def patch_rows(rows):
        for c in rows:
            expected[c[0]] = None if c[2].upper() == 'DELETED' else c[2].lower()
            origin[c[0]] = c[5].split(':')[0]
    patch_rows(prow)
    states = snapfiles('STATE-', '.tsv')
    if states:
        for rel, ls, lm, lh, ss, sm, sh, org in load_tsv_rows(states[-1]):
            if lh != '-':
                cache[('L', rel)] = (int(ls), int(lm), lh)
            if sh != '-':
                cache[('S', rel)] = (int(ss), int(sm), sh)
            expected[rel], origin[rel] = (sh if sh != '-' else None), org
        st_time = ts(os.path.getmtime(states[-1]), ns=False)
        patch_rows([c for c in prow if c[4] > st_time])

    live, junctions = S.walk_live()
    snapf = walk_snap()
    outside = set(nat)
    for ru in rules:
        if ru['outside'] and not ru['neg'] and not wild(ru['pat']):
            outside.add(ru['pat'])
    for rel in outside:
        st = stat2(S.live_path(rel))
        if st:
            live[rel] = st
        st = stat2(S.snap_path(rel))
        if st:
            snapf[rel] = st
    t_walk = time.time() - t0
    lh, lneed = hash_side('L', live, cache)
    sh, sneed = hash_side('S', snapf, cache)
    toml_logical(lh, sh, sneed)
    t_hash = time.time() - t0 - t_walk

    idx = claim_index()
    errors, warnings = [], []
    copy, delete, held = [], [], []
    same = 0
    universe = sorted(set(live) | set(snapf))
    for rel in universe:
        low = rel.lower()
        is_out = outside_walk(rel)  # walk rules match walk files, outside rules match rexlego/out, research, ...
        inc, exc = [], False
        for ru in rules:
            if ru['outside'] != is_out or not low.startswith(ru['lit']) or not ru['re'].match(rel):
                continue
            ru['hits'] += 1
            if lh.get(rel) != sh.get(rel):
                ru['diff'] += 1
            if ru['neg']:
                exc = True
            else:
                inc.append(ru)
                if ru['expect'] and not (lh.get(rel) or '').startswith(ru['expect']):
                    errors.append('%s: live %s has sha256 %s, the rule expects %s (changed after the review?)'
                                  % (ru['src'], rel, h16(lh.get(rel)), ru['expect']))
        a, b = lh.get(rel), sh.get(rel)
        if a == b:
            same += 1
            continue
        item = {'rel': rel, 'cat': 'modified' if a and b else ('added' if a else 'removed'), 'lh': a, 'sh': b,
                'lst': live.get(rel), 'sst': snapf.get(rel), 'native': rel in outside}
        if inc and not exc and not pinned(rel):
            item['owner'] = ','.join(sorted({ru['owner'] for ru in inc}))
            item['rule'] = inc[0]
            (copy if a else delete).append(item)
        else:
            item['why'] = 'pinned' if (inc and pinned(rel)) else ('excluded' if exc else 'not selected')
            item['claims'] = owners_of(rel, idx)
            held.append(item)
    for ru in rules:
        if ru['explicit'] and not ru['neg'] and not wild(ru['pat']) and not ru['hits']:
            errors.append('%s: %s matches no file in live or snap1' % (ru['src'], ru['pat']))
        elif not ru['hits']:
            warnings.append('%s: %s%s matches nothing' % (ru['src'], '!' if ru['neg'] else '', ru['pat']))
    if delete and not allow_delete:
        errors.append('%d selected file(s) are gone from live; deleting them from snap1 needs --allow-delete'
                      % len(delete))

    # snapshot drift: snap1 must still hold exactly S1 + the patch rows + the native inputs (+ the last STATE)
    covered = {it['rel'] for it in copy + delete}
    drift = []
    for rel, h in sh.items():
        exp = expected.get(rel, 'MISSING')
        if exp == 'MISSING':
            drift.append((rel, 'extra', 'in snap1 but not in S1, a patch row, the native inputs or a STATE'))
        elif exp is None:
            drift.append((rel, 'changed', 'in snap1 although an earlier apply deleted it'))
        elif h != exp:
            drift.append((rel, 'changed', 'snap1 sha %s, expected %s (%s)' % (h16(h), h16(exp), origin.get(rel))))
    for rel, exp in expected.items():
        if exp is not None and rel not in snapf:
            drift.append((rel, 'missing', 'expected in snap1 (%s) but missing' % origin.get(rel)))
    for rel, kind, why in drift:
        acc = [x for x in accepts if rel.lower().startswith(x['lit']) and x['re'].match(rel)]
        for x in acc:
            x['hits'] += 1
        if kind == 'extra':
            warnings.append('snap1 extra file (left alone): %s' % rel)
        elif rel in covered:
            continue
        elif acc:
            warnings.append('snap1 drift accepted by %s ~%s: %s: %s' % (acc[0]['src'], acc[0]['pat'], rel, why))
            origin[rel] = 'drift accepted, was %s' % origin.get(rel, '?')
        else:
            errors.append('snap1 drift: %s: %s' % (rel, why))

    P = {'tag': tag, 'rules_path': rules_path, 'rules': rules, 'accepts': accepts, 'notes': notes, 'errors': errors,
         'warnings': warnings, 'copy': copy, 'delete': delete, 'held': held, 'same': same, 'drift': drift,
         'live': live, 'snapf': snapf, 'lh': lh, 'sh': sh, 'origin': origin, 'junctions': junctions,
         's1_path': s1_path, 'states': states, 'nat': nat, 'stamp': time.strftime('%H%M'), 'universe': universe}
    lines = ['# snap-patch %s plan %s; rules %s%s' % (
        tag, time.strftime('%Y-%m-%d %H:%M:%S'), rules_path or '(none)',
        ' (sha256 %s)' % S.sha(rules_path) if rules_path else ''),
        '# base: %s + %d PATCHES row(s) + %d native-input file(s)%s' % (
            os.path.basename(s1_path), len(prow), len(nat),
            (' + ' + os.path.basename(states[-1])) if states else ''),
        'files: live %d, snap1 %d; hashed live %d, snap1 %d; walk %.1fs, hash %.1fs' % (
            len(live), len(snapf), len(lneed), len(sneed), t_walk, t_hash),
        'same %d; differing %d: COPY %d (%d bytes), DELETE %d, HELD BACK %d; errors %d, warnings %d' % (
            same, len(copy) + len(delete) + len(held), len(copy), sum(it['lst'][0] for it in copy), len(delete),
            len(held), len(errors), len(warnings))]
    if errors:
        lines.append('## ERRORS (%d): apply refuses to run' % len(errors))
        lines += ['  ' + e for e in errors]
    lines.append('## COPY live -> snap1 (%d): category, owner, live sha/mtime, snap1 sha, path' % len(copy))
    for it in copy:
        lines.append('  %-8s %-12s live %s %s  snap1 %s  %s' % (
            it['cat'], it['owner'], h16(it['lh']), ts(it['lst'][1]), h16(it['sh']), it['rel']))
    if delete:
        lines.append('## DELETE from snap1 (%d, needs --allow-delete)' % len(delete))
        for it in delete:
            lines.append('  %-12s snap1 %s  %s' % (it['owner'], h16(it['sh']), it['rel']))
    lines.append('## HELD BACK (%d): differs from live but stays at its snap1 content; grouped by board claim' % len(held))
    groups = {}
    for it in held:
        groups.setdefault(('native input ' if it['native'] else '') + it['claims'], []).append(it)
    for k in sorted(groups):
        lines.append('  [%s] %d file(s)' % (k, len(groups[k])))
        for it in groups[k]:
            lines.append('    %-8s %-12s live %s %s  snap1 %s  %s' % (
                it['cat'], it['why'], h16(it['lh']), ts(it['lst'][1]) if it['lst'] else '-', h16(it['sh']),
                it['rel']))
    lines.append('## RULES (%d)' % len(rules))
    for ru in rules:
        lines.append('  %-26s %s%s  [%s]%s hits=%d differing=%d' % (
            ru['src'], '!' if ru['neg'] else '', ru['pat'], ru['owner'],
            ' expect=%s' % ru['expect'] if ru['expect'] else '', ru['hits'], ru['diff']))
    if accepts:
        lines.append('## ACCEPTED DRIFT RULES (%d)' % len(accepts))
        for x in accepts:
            lines.append('  %-26s ~%s  drift hits=%d' % (x['src'], x['pat'], x['hits']))
    if notes:
        lines.append('## NOTES (%d)' % len(notes))
        lines += ['  ' + x for x in notes]
    if warnings:
        lines.append('## WARNINGS (%d)' % len(warnings))
        lines += ['  ' + w for w in warnings[:200]]
        if len(warnings) > 200:
            lines.append('  ... %d more' % (len(warnings) - 200))
    lines += rebuild_plan(tag, [it['rel'] for it in copy + delete])
    P['text'] = lines
    return P


def write_text(path, lines):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')


def add_notes(P, notes):
    # --note / --note-file: '# note: ...' lines after the plan's two '#' header lines (PLAN-* and DIFF-*)
    P['text'][2:2] = ['# note: %s' % n for n in notes]


def note_suffix(notes):
    # the same notes for the one '#' header line of PATCHES-<TAG>.tsv and STATE-<TAG>-*.tsv
    return ''.join('; note: %s' % n for n in notes)


def patches_header(tag, notes=()):
    return ('# patches applied to build/agent2/snap1 for %s by snap-patch.py (relpath under DimensionsRecomp/, '
            'sha256 before, sha256 after, source, time, note)%s\n' % (tag, note_suffix(notes)))


def state_header(tag, nrows, notes=()):
    return ('# snap1 state after snap-patch %s apply %s: %d files (rel, live size, live mtime_ns, live sha256, '
            'snap1 size, snap1 mtime_ns, snap1 sha256, origin); generated/ not listed%s\n'
            % (tag, time.strftime('%Y-%m-%d %H:%M:%S'), nrows, note_suffix(notes)))


def cmd_plan(tag, rules_path, notes=()):
    P = make_plan(tag, rules_path)
    add_notes(P, notes)
    out = os.path.join(S.SNAP_ROOT, 'PLAN-%s-%s.txt' % (tag, P['stamp']))
    write_text(out, P['text'])
    print('\n'.join(P['text']))
    print('plan: %s' % out)
    return 1 if P['errors'] else 0


# ---------------------------------------------------------------- apply
def backup_root(tag):
    return os.path.join(A, 'snap1-backup-%s' % tag, 'DimensionsRecomp')


def find_backup(tag, rel, want):
    base = LP + os.path.join(backup_root(tag), rel.replace('/', os.sep))
    for b in (base, base + '.' + want[:8]):
        if os.path.isfile(b) and S.sha(b) == want:
            return b
    return None


def cmd_apply(tag, rules_path, allow_delete, notes=()):
    t0 = time.time()
    P = make_plan(tag, rules_path, allow_delete)
    add_notes(P, notes)
    stamp = P['stamp']
    write_text(os.path.join(S.SNAP_ROOT, 'PLAN-%s-%s.txt' % (tag, stamp)), P['text'])
    if P['errors']:
        print('\n'.join(P['text']))
        print('NOT APPLIED: %d error(s); nothing was copied' % len(P['errors']))
        return 2
    pt = os.path.join(S.SNAP_ROOT, 'PATCHES-%s.tsv' % tag)
    if not os.path.exists(pt):
        with open(pt, 'w', encoding='utf-8', newline='\n') as f:
            f.write(patches_header(tag, notes))
    elif notes:
        with open(pt, encoding='utf-8-sig') as f:
            head = f.readline()
        if note_suffix(notes) not in head:
            print('WARNING: %s exists and its header line lacks the --note text; left as is' % pt)
    now = time.time()
    done, gone, later = {}, set(), []
    for it in P['copy'] + (P['delete'] if allow_delete else []):
        rel, ru = it['rel'], it['rule']
        dst = S.snap_path(rel)
        bnote = 'none (new file)'
        if it['sh'] is not None:
            b = find_backup(tag, rel, it['sh'])
            if b is None:
                b = LP + os.path.join(backup_root(tag), rel.replace('/', os.sep))
                if os.path.exists(b):
                    b = b + '.' + it['sh'][:8]
                os.makedirs(os.path.dirname(b), exist_ok=True)
                shutil.copy2(dst, b)
                if S.sha(b) != it['sh']:
                    raise SystemExit('backup of %s does not hash to the planned snap1 sha %s; stopping' % (rel, h16(it['sh'])))
            bnote = b[len(LP) + len(S.R) + 1:]
        if it['lh'] is None:
            os.chmod(dst, 0o666)
            os.remove(dst)
            gone.add(rel)
            after, source = 'DELETED', 'deleted from snap1 (gone from live)'
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(dst):
                os.chmod(dst, 0o666)
            shutil.copy2(S.live_path(rel), dst)
            os.utime(dst, (now, now))
            got = S.sha(dst)
            if got != it['lh']:
                raise SystemExit('copy of %s has sha %s but the plan said %s: the live file changed after the plan. '
                                 'Rows so far are in %s; re-run apply.' % (rel, h16(got), h16(it['lh']), pt))
            if S.sha(S.live_path(rel)) != it['lh']:
                later.append(rel)
            done[rel] = stat2(dst)
            after = it['lh'].upper()
            source = 'live DimensionsRecomp/%s (mtime %s)' % (rel, ts(it['lst'][1]))
        note = '%s %s: %s; rule %s (%s); backup %s' % (tag, it['owner'], it['cat'], ru['pat'], ru['src'], bnote)
        with open(pt, 'a', encoding='utf-8', newline='\n') as f:
            f.write('\t'.join([rel, (it['sh'] or 'ABSENT').upper(), after, source,
                               time.strftime('%Y-%m-%d %H:%M:%S'), note]) + '\n')
    # STATE: every file, after the apply
    rows = []
    for rel in sorted(set(P['universe']) | gone):
        lst, lhv = P['live'].get(rel), P['lh'].get(rel)
        if rel in done:
            sst, shv, org = done[rel], lhv, tag
        elif rel in gone:
            sst, shv, org = None, None, tag + ' deleted'
        else:
            sst, shv, org = P['snapf'].get(rel), P['sh'].get(rel), P['origin'].get(rel, 'unrecorded')
        rows.append('\t'.join([rel, str(lst[0]) if lst else '-', str(lst[1]) if lst else '-', lhv or '-',
                               str(sst[0]) if sst else '-', str(sst[1]) if sst else '-', shv or '-', org]))
    sp = os.path.join(S.SNAP_ROOT, 'STATE-%s-%s.tsv' % (tag, stamp))
    with open(sp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(state_header(tag, len(rows), notes))
        f.write('\n'.join(rows) + '\n')
    lines = list(P['text'])
    lines.append('## APPLIED %s: copied %d, deleted %d; PATCHES %s (sha256 %s); STATE %s (sha256 %s); wall %.1fs' % (
        time.strftime('%H:%M:%S'), len(done), len(gone), os.path.basename(pt), S.sha(pt), os.path.basename(sp),
        S.sha(sp), time.time() - t0))
    for rel in later:
        lines.append('  NOTE: live %s changed again after its copy; %s holds the planned version' % (rel, tag))
    dp = os.path.join(S.SNAP_ROOT, 'DIFF-%s-%s.txt' % (tag, stamp))
    write_text(dp, lines)
    print('\n'.join(P['text'][:4 + len(notes)]))
    print(lines[-1 - len(later)])
    for x in lines[len(lines) - len(later):]:
        print(x)
    print('diff: %s' % dp)
    return 0


# ---------------------------------------------------------------- verify / revert
def cmd_verify(tag, full):
    t0 = time.time()
    sps = snapfiles('STATE-%s-' % tag, '.tsv')
    if not sps:
        raise SystemExit('no STATE-%s-*.tsv in %s' % (tag, S.SNAP_ROOT))
    sp = sps[-1]
    state = {c[0]: c[1:] for c in load_tsv_rows(sp)}
    snapf = walk_snap()
    for rel in state:
        if rel not in snapf:
            st = stat2(S.snap_path(rel))
            if st:
                snapf[rel] = st
    bad, check = [], []
    for rel, (ls, lm, lhv, ss, sm, shv, org) in state.items():
        cur = snapf.get(rel)
        if shv == '-':
            if cur:
                bad.append('%s: present in snap1 but deleted in %s' % (rel, os.path.basename(sp)))
            continue
        if cur is None:
            bad.append('%s: missing from snap1' % rel)
        elif rel == S.MANIFEST_REL:
            if cur[1] != int(sm):
                bad.append('%s: mtime changed (rewritten copy; compared by mtime only)' % rel)
        elif full or cur != (int(ss), int(sm)):
            check.append(rel)
    with ThreadPoolExecutor(S.THREADS) as ex:
        for rel, h in zip(check, ex.map(lambda r: S.sha(S.snap_path(r)), check)):
            if h != state[rel][5]:
                bad.append('%s: snap1 sha %s != recorded %s' % (rel, h16(h), h16(state[rel][5])))
    extra = sorted(r for r in snapf if r not in state)
    pt = os.path.join(S.SNAP_ROOT, 'PATCHES-%s.tsv' % tag)
    nb = 0
    if os.path.exists(pt):
        for c in load_tsv_rows(pt):
            if c[1].upper() != 'ABSENT':
                nb += 1
                if not find_backup(tag, c[0], c[1].lower()):
                    bad.append('%s: no backup hashing to %s' % (c[0], h16(c[1])))
    print('verify %s against %s: %d files, %d hashed (%s), %d backups checked, %d extra file(s) in snap1, %d problem(s), %.1fs'
          % (tag, os.path.basename(sp), len(state), len(check), 'full' if full else 'size/mtime changed', nb,
             len(extra), len(bad), time.time() - t0))
    for x in bad[:100]:
        print('  BAD ' + x)
    for x in extra[:50]:
        print('  extra ' + x)
    print('RESULT: %s' % ('PASS' if not bad else 'FAIL'))
    return 1 if bad else 0


def cmd_revert(tag):
    pt = os.path.join(S.SNAP_ROOT, 'PATCHES-%s.tsv' % tag)
    rows = load_tsv_rows(pt)
    now, stamp = time.time(), time.strftime('%H%M')
    for c in reversed(rows):
        rel, before, after = c[0], c[1].lower(), c[2].lower()
        dst = S.snap_path(rel)
        cur = S.sha(dst) if os.path.exists(dst) else None
        if (cur or 'deleted') != after:
            raise SystemExit('%s: snap1 holds %s, not the patched %s; stopping (nothing after this row reverted)'
                             % (rel, h16(cur), h16(after)))
        if before == 'absent':
            os.chmod(dst, 0o666)
            os.remove(dst)
        else:
            b = find_backup(tag, rel, before)
            if b is None:
                raise SystemExit('%s: no backup hashing to %s; stopping' % (rel, h16(before)))
            if os.path.exists(dst):
                os.chmod(dst, 0o666)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(b, dst)
            os.utime(dst, (now, now))
            if S.sha(dst) != before:
                raise SystemExit('%s: the restored file does not hash to %s' % (rel, h16(before)))
        print('reverted %s -> %s  %s' % (h16(after), h16(before), rel))
    os.replace(pt, pt[:-4] + '-reverted-%s.tsv' % stamp)
    for sp in snapfiles('STATE-%s-' % tag, '.tsv'):
        os.replace(sp, sp[:-4] + '.reverted')
    print('reverted %d row(s); PATCHES and STATE files renamed *-reverted*' % len(rows))
    return 0


def main(argv):
    if len(argv) < 3 or argv[1] not in ('plan', 'apply', 'verify', 'revert'):
        raise SystemExit(__doc__)
    cmd, tag = argv[1], argv[2]
    if not re.fullmatch(r'[A-Za-z0-9]+', tag) or tag.upper() == 'S1':
        raise SystemExit('TAG must be alphanumeric and not S1 (S1 is the base)')
    if cmd in ('plan', 'apply'):
        if len(argv) < 4:
            raise SystemExit('%s needs a rules file' % cmd)
        rp = os.path.abspath(argv[3])
        notes, bad = [], []
        for a in argv[4:]:
            if a.startswith('--note='):
                notes.append(a[len('--note='):])
            elif a.startswith('--note-file='):
                with open(a[len('--note-file='):], encoding='utf-8-sig') as f:
                    notes += f.read().splitlines()
            elif a != '--allow-delete':
                bad.append(a)
        if bad:
            raise SystemExit('unknown option(s): %s' % ' '.join(bad))
        notes = [n.strip() for n in notes if n.strip()]
        if any('\t' in n for n in notes):
            raise SystemExit('a note must not contain a tab (notes go into TSV header lines)')
        if cmd == 'plan':
            return cmd_plan(tag, rp, notes)
        return cmd_apply(tag, rp, '--allow-delete' in argv[4:], notes)
    if cmd == 'verify':
        return cmd_verify(tag, '--full' in argv[3:])
    return cmd_revert(tag)


if __name__ == '__main__':
    sys.exit(main(sys.argv))

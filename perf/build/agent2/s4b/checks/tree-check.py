#!/usr/bin/env python3
"""tree-check.py - read-only checker for Agent 2 (agy-grid): verify the composed snap1 tree (S4b) against
PATCHES-S4b.tsv, s4b/HASHES.txt, STATE-S4b-1950.tsv vs STATE-S4a-1325.tsv, the owners' staged after-files,
the compose check's o1-v3 results and the snap1-backup-S4b backups.
Reads only. Writes only build/agent2/s4b/checks/tree-check-<HHMM>.txt. No git, no builds, no runs.
Exits 9 at once if perf-notes/WINDOW-HOLD.txt exists (checked before each check too)."""
import hashlib
import os
import re
import sys
import time

sys.dont_write_bytecode = True

R = r'<workspace>'
HOLD = os.path.join(R, 'perf-notes', 'WINDOW-HOLD.txt')
A2 = os.path.join(R, 'build', 'agent2')
SNAP = os.path.join(A2, 'snap1', 'DimensionsRecomp')
BACK_ROOT = os.path.join(A2, 'snap1-backup-S4b')
BACK = os.path.join(BACK_ROOT, 'DimensionsRecomp')
O1 = os.path.join(A2, 's4b-check', 'o1-v3')
O2 = os.path.join(A2, 's4b-check', 'o2-v3')
OUTDIR = os.path.join(A2, 's4b', 'checks')
PATCHES = os.path.join(A2, 'snap1', 'PATCHES-S4b.tsv')
ST_B = os.path.join(A2, 'snap1', 'STATE-S4b-1950.tsv')
ST_A = os.path.join(A2, 'snap1', 'STATE-S4a-1325.tsv')
HASHES = os.path.join(A2, 's4b', 'HASHES.txt')
APPLY_LOG = os.path.join(A2, 'prep-s4b-apply-1950.txt')
COMPOSE = os.path.join(A2, 's4b-compose-check.py')

SDKP = 'rexglue-sdk/'
CP = SDKP + 'src/graphics/d3d12/command_processor.cpp'
XM = SDKP + 'src/system/xmemory.cpp'
MW = 'rexlego/src/gpu_native/memory_watch.cpp'
CML = 'rexlego/CMakeLists.txt'
TU = 'rexlego/src/gpu_wait_backoff.cpp'
TOML = 'rexlego/legodimensions_config.toml'
TASK_PREFIX = {CP: '027204B53A271D69', XM: 'BCA5E1CF63686E73', MW: '70829846C4F321A9',
               TU: '01D9F8F3464C8614', CML: '1BF46D7878BA9A25'}
TOML_PREFIX = '7F775847DB9CC2DA'
C1V3_ORDER = ['c1v3', 'm1', 'p2c', 'r1r2', 'n26']
COLS = ['rel', 'live size', 'live mtime_ns', 'live sha', 'snap size', 'snap mtime_ns', 'snap sha', 'origin']
G12 = r'build\agent12\s4-c1v3\new\sdk' + '\\'
G7 = r'build\agent7\s4-r1r2\new\sdk' + '\\'
G9 = r'build\agent9\s4\spin\db16cyc-pause\new' + '\\'
STAGED = {
    SDKP + 'include/rex/graphics/shared_memory.h': G12 + r'include\rex\graphics\shared_memory.h',
    SDKP + 'include/rex/system/xmemory.h': G12 + r'include\rex\system\xmemory.h',
    SDKP + 'src/graphics/primitive_processor.cpp': G12 + r'src\graphics\primitive_processor.cpp',
    SDKP + 'src/graphics/shared_memory.cpp': G12 + r'src\graphics\shared_memory.cpp',
    XM: G12 + r'src\system\xmemory.cpp',
    SDKP + 'src/graphics/d3d12/shared_memory.cpp': r'build\agent5\s4-m1\new\shared_memory.cpp',
    SDKP + 'include/rex/graphics/d3d12/command_processor.h': G7 + r'include\rex\graphics\d3d12\command_processor.h',
    SDKP + 'include/rex/graphics/d3d12/deferred_command_list.h': G7 + r'include\rex\graphics\d3d12\deferred_command_list.h',
    SDKP + 'src/graphics/d3d12/deferred_command_list.cpp': G7 + r'src\graphics\d3d12\deferred_command_list.cpp',
    SDKP + 'include/rex/codegen/config.h': G9 + r'include\rex\codegen\config.h',
    SDKP + 'src/codegen/config.cpp': G9 + r'src\codegen\config.cpp',
    SDKP + 'src/codegen/builders/system.cpp': G9 + r'src\codegen\builders\system.cpp',
    MW: r'build\agent12\s4-c1\new\game\rexlego\src\gpu_native\memory_watch.cpp',
    CML: r'build\agent9\s4\fence-wait\s4c\new\rexlego\CMakeLists.txt',
    TU: r'build\agent9\s4\fence-wait\s4c\new\rexlego\src\gpu_wait_backoff.cpp',
}
CP_SINGLE = [('p2c', r'build\agent12\s4-p2c\new\command_processor.cpp'),
             ('r1r2', G7 + r'src\graphics\d3d12\command_processor.cpp')]


def hold():
    if os.path.exists(HOLD):
        print('HOLD EXISTS - stopping')
        sys.exit(9)


def P(rel, root):
    return os.path.join(root, rel.replace('/', os.sep))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def sha_or(p):
    return sha(p) if os.path.isfile(p) else 'ABSENT'


def rp(p):
    return os.path.relpath(p, R).replace('\\', '/')


def compose_records():
    ns = {'__name__': 's4b_compose_check_records', '__file__': COMPOSE}
    with open(COMPOSE, 'r', encoding='utf-8') as f:
        src = f.read()
    exec(compile(src, COMPOSE, 'exec'), ns)
    ra, nst = {}, {}
    for k in C1V3_ORDER:
        for f, (b, a) in ns['STEPS'][k][3].items():
            ra[SDKP + f] = a
            nst[SDKP + f] = nst.get(SDKP + f, 0) + 1
    rf = {key: (ns['AGENT10_CP_COMPOSITE'] if nst[key] > 1 else ra[key]) for key in ra}
    rf[MW] = ns['MW_AFTER']
    rf[CML] = ns['S4C']['24-30'][2]
    rf[TU] = ns['TU_LF']
    single = {k: ns['STEPS'][k][3]['src/graphics/d3d12/command_processor.cpp'][1] for k in ('p2c', 'r1r2')}
    return rf, single, ns['C1_VARIANTS']['v3'][2]


def tsv_rows(path):
    with open(path, 'r', encoding='utf-8', errors='surrogateescape', newline='') as f:
        for ln in f:
            ln = ln.rstrip('\r\n')
            if ln:
                yield ln


def load_patches():
    rows = []
    for ln in tsv_rows(PATCHES):
        if ln.startswith('#'):
            continue
        c = ln.split('\t')
        rows.append({'rel': c[0].replace('\\', '/'), 'before': c[1].strip().upper(), 'after': c[2].strip().upper(),
                     'ncol': len(c)})
    return rows


def load_hashes():
    d = {}
    rx = re.compile(r'^([0-9A-Fa-f]{64}) \((\d+) B\)$')

    def parse(x):
        m = rx.match(x.strip())
        return (m.group(1).upper(), int(m.group(2))) if m else (x.strip(), None)

    for ln in tsv_rows(HASHES):
        if ln.startswith('#'):
            continue
        c = ln.split('\t')
        d[c[1].replace('\\', '/')] = {'before': parse(c[2]), 'after': parse(c[3])}
    return d


def load_state(path):
    rows, dups, bad, hdr = {}, [], [], []
    for ln in tsv_rows(path):
        if ln.startswith('#'):
            hdr.append(ln)
            continue
        c = ln.split('\t')
        if len(c) != 8:
            bad.append(ln[:120])
            continue
        rel = c[0].replace('\\', '/')
        if rel in rows:
            dups.append(rel)
        rows[rel] = c
    return rows, dups, bad, hdr


def le_counts(data):
    crlf = data.count(b'\r\n')
    return crlf, data.count(b'\n') - crlf, data.count(b'\r') - crlf


def read_text(path):
    # the prep logs are written by PowerShell: UTF-16 LE with a BOM (FF FE); others are UTF-8
    with open(path, 'rb') as f:
        data = f.read()
    if data.startswith(b'\xff\xfe') or data.startswith(b'\xfe\xff'):
        enc = 'utf-16'
    elif data.startswith(b'\xef\xbb\xbf'):
        enc = 'utf-8-sig'
    else:
        enc = 'utf-8'
    return data.decode(enc, 'replace').replace('\r\n', '\n'), enc


def check0():
    det, ok = [], True
    log, enc = read_text(APPLY_LOG)
    det.append('  NOTE apply log encoding: %s' % enc)
    want = {m.group(1): m.group(2) for m in re.finditer(r'wrote (\S+) \(sha256 ([0-9A-F]{16})\)', log)}
    for key, p in (('build/agent2/s4b/HASHES.txt', HASHES), ('build/agent2/snap1/PATCHES-S4b.tsv', PATCHES),
                   ('build/agent2/snap1/STATE-S4b-1950.tsv', ST_B)):
        h = sha_or(p)
        w = want.get(key)
        good = w is not None and h.startswith(w)
        ok = ok and good
        det.append('  %s %s sha256 %s; the apply log wrote it as %s' % ('ok  ' if good else 'FAIL', key, h, w))
    res = re.findall(r'^RESULT: (\w+)', log, re.M)
    ver = re.findall(r'^(verify S4b against .*)$', log, re.M)
    good = res[-1:] == ['PASS']
    ok = ok and good
    det.append('  %s apply log %s (sha256 %s): RESULT %s; %s' % ('ok  ' if good else 'FAIL', rp(APPLY_LOG),
               sha(APPLY_LOG)[:16], res[-1] if res else 'none', ver[-1] if ver else 'no verify line'))
    det.append('  NOTE records read from %s (sha256 %s)' % (rp(COMPOSE), sha(COMPOSE)[:16]))
    return ok, 'S4b records unchanged since the apply (HASHES.txt, PATCHES-S4b.tsv, STATE-S4b-1950.tsv == apply log)', det


def check1(prow, hashes, stb, rf, single):
    det = []
    rels = [r['rel'] for r in prow]
    ok = len(prow) == 16 and len(set(rels)) == 16 and all(r['ncol'] == 6 for r in prow)
    det.append('  PATCHES-S4b.tsv: %d rows (want 16), %d distinct rel(s), column counts %s' % (
        len(prow), len(set(rels)), sorted(set(r['ncol'] for r in prow))))
    nrow_ok = n_staged = n_o1 = 0
    for r in prow:
        rel = r['rel']
        p = P(rel, SNAP)
        h = sha_or(p)
        hs = hashes.get(rel)
        st = stb.get(rel)
        exp = [('PATCHES after', r['after']), ('HASHES.txt after', hs['after'][0] if hs else None),
               ('STATE-S4b snap sha', st[6] if st else None)]
        if rel in STAGED:
            exp.append(('staged ' + STAGED[rel].replace('\\', '/'), sha_or(os.path.join(R, STAGED[rel]))))
            n_staged += 1
        if rel.startswith(SDKP):
            exp.append(('o1-v3', sha_or(P(rel[len(SDKP):], O1))))
            n_o1 += 1
        exp.append(('compose-check record', rf.get(rel)))
        if rel in TASK_PREFIX:
            exp.append(('task', TASK_PREFIX[rel]))
        good = h != 'ABSENT'
        res = []
        for label, val in exp:
            if val is None or val == 'ABSENT':
                okv, vs = False, 'ABSENT/none'
            else:
                okv, vs = len(val) >= 8 and h.startswith(val.upper()), val.upper()[:16]
            good = good and okv
            res.append('%s %s %s%s' % ('==' if okv else '!=', label, vs, '' if okv else ' FAIL'))
        size = os.path.getsize(p) if h != 'ABSENT' else None
        mt = os.stat(p).st_mtime_ns if h != 'ABSENT' else None
        hs_size = hs['after'][1] if hs else None
        st_size = int(st[4]) if st and st[4].isdigit() else None
        st_mt = int(st[5]) if st and st[5].isdigit() else None
        sz_ok = size is not None and size == hs_size == st_size
        good = good and sz_ok
        nrow_ok += good
        det.append('  %s %s: snap1 %s (%s B)' % ('PASS' if good else 'FAIL', rel, h, size))
        det.append('       ' + ' | '.join(res))
        det.append('       size %s B vs HASHES.txt %s / STATE-S4b %s: %s; mtime_ns %s vs STATE-S4b %s: %s' % (
            size, hs_size, st_size, 'ok' if sz_ok else 'FAIL', mt, st_mt,
            'same' if mt == st_mt else 'DIFFERENT (note only)'))
        if rel == CP:
            for k, sp_rel in CP_SINGLE:
                sh = sha_or(os.path.join(R, sp_rel))
                det.append('       NOTE single-step after-file %s (%s alone) %s, == record %s after %s: %s; != snap1 '
                           'as expected (P2c then r1r2 both touch this file)' % (sp_rel.replace('\\', '/'), k, sh[:16],
                                                                                 k, single[k][:16],
                                                                                 'yes' if sh == single[k] else 'NO'))
            o2 = sha_or(P(rel[len(SDKP):], O2))
            det.append('       NOTE o2-v3 (r1r2 then P2c) result %s: %s' % (
                o2[:16], '== snap1 (both orders give the composite)' if o2 == h else '!= snap1'))
    ok = ok and nrow_ok == 16
    return ok, ('%d/16 rows: snap1 == PATCHES after == HASHES.txt after == STATE-S4b snap sha == staged after-file '
                '(%d files; command_processor.cpp = Agent 10 composite %s) == o1-v3 (%d SDK files) == compose-check '
                'record; xmemory.cpp %s' % (nrow_ok, n_staged, TASK_PREFIX[CP], n_o1, TASK_PREFIX[XM])), det


def check2():
    det, ok, parts = [], True, []
    for rel, want_le in ((MW, 'CRLF'), (TU, 'LF'), (CML, 'CRLF')):
        p = P(rel, SNAP)
        if not os.path.isfile(p):
            ok = False
            det.append('  FAIL %s: ABSENT in snap1' % rel)
            continue
        with open(p, 'rb') as f:
            data = f.read()
        h = hashlib.sha256(data).hexdigest().upper()
        crlf, lf, cr = le_counts(data)
        le_ok = (crlf > 0 and lf == 0 and cr == 0) if want_le == 'CRLF' else (crlf == 0 and cr == 0 and lf > 0)
        h_ok = h.startswith(TASK_PREFIX[rel])
        ok = ok and le_ok and h_ok
        det.append('  %s %s: sha256 %s (%s %s); %d CRLF, %d bare LF, %d bare CR -> %s; BOM %s; final newline %s' % (
            'PASS' if le_ok and h_ok else 'FAIL', rel, h, '==' if h_ok else '!=', TASK_PREFIX[rel], crlf, lf, cr,
            want_le if le_ok else 'NOT ' + want_le + ' (FAIL)', 'yes' if data.startswith(b'\xef\xbb\xbf') else 'no',
            'yes' if data.endswith(b'\n') else 'no'))
        parts.append('%s %s %s (%d CRLF/%d bare LF)' % (rel.rsplit('/', 1)[-1], want_le if le_ok else 'NOT-' + want_le,
                                                        h[:16], crlf, lf))
        bp = P(rel, BACK)
        if os.path.isfile(bp):
            with open(bp, 'rb') as f:
                bc, bl, bcr = le_counts(f.read())
            det.append('       NOTE S4a form (backup): %d CRLF, %d bare LF, %d bare CR' % (bc, bl, bcr))
    return ok, '; '.join(parts), det


def check3(sta, stb, prow):
    a, dupa, bada, hdra = sta
    b, dupb, badb, hdrb = stb
    pb = {r['rel']: r for r in prow}
    pset = set(pb)
    det = []
    sa, sb = set(a), set(b)
    added, removed = sorted(sb - sa), sorted(sa - sb)
    changed = sorted(x for x in (sa & sb) if a[x][6].upper() != b[x][6].upper())
    differ = set(changed) | set(added)
    not_in_p, p_not_d = sorted(differ - pset), sorted(pset - differ)

    def hdr_count(h):
        m = re.search(r'(\d+) files', h[0]) if h else None
        return int(m.group(1)) if m else None

    ca, cb = hdr_count(hdra), hdr_count(hdrb)
    det.append('  STATE-S4a-1325.tsv: %d rows (header says %s), %d duplicate rel(s), %d malformed line(s)' % (
        len(a), ca, len(dupa), len(bada)))
    det.append('  STATE-S4b-1950.tsv: %d rows (header says %s), %d duplicate rel(s), %d malformed line(s)' % (
        len(b), cb, len(dupb), len(badb)))
    det.append('  rel paths only in S4b: %s; only in S4a: %s' % (', '.join(added) or 'none', ', '.join(removed) or 'none'))
    det.append('  rows with a different snap sha: %d changed + %d new = %d; not PATCHES-S4b rows: %s; PATCHES-S4b rows '
               'without a difference: %s' % (len(changed), len(added), len(differ), ', '.join(not_in_p) or 'none',
                                             ', '.join(p_not_d) or 'none'))
    cons_ok = True
    for r in prow:
        x = r['rel']
        s_a = a[x][6].upper() if x in a else 'ABSENT'
        s_b = b[x][6].upper() if x in b else 'ABSENT'
        okb, oka = s_a == r['before'], s_b == r['after']
        cons_ok = cons_ok and okb and oka
        colsd = [COLS[i] for i in range(1, 8) if x in a and x in b and a[x][i] != b[x][i]]
        live_b = b[x][3].upper() if x in b else '?'
        det.append('    %s %s: S4a snap %s %s before; S4b snap %s %s after; changed columns: %s; S4b origin %s; '
                   'S4b live sha %s (%s)' % (
                       'ok  ' if okb and oka else 'FAIL', x, s_a[:16], '==' if okb else '!=', s_b[:16],
                       '==' if oka else '!=', ', '.join(colsd) if x in a else '(new row)', b[x][7] if x in b else '?',
                       live_b[:16], '== before, live untouched' if live_b == r['before'] else
                       ('not in live' if live_b == '-' else 'differs from before')))
    extra = [(x, [COLS[i] for i in range(1, 8) if a[x][i] != b[x][i]]) for x in sorted(sa & sb)
             if x not in pset and a[x][1:] != b[x][1:]]
    det.append('  extra differences (rows outside the 16 with any column changed): %d' % len(extra))
    for x, cols in extra[:40]:
        det.append('    EXTRA %s: %s' % (x, ', '.join(cols)))
    ok = (not dupa and not dupb and not bada and not badb and not removed and added == [TU] and len(changed) == 15
          and len(differ) == 16 and not not_in_p and not p_not_d and cons_ok and not extra
          and ca == len(a) and cb == len(b) and len(b) == len(a) + 1)
    return ok, ('STATE-S4b %d rows = STATE-S4a %d rows + %s; snap sha differs in %d rows (%d changed + %d new), %s; '
                'extra differences: %s' % (len(b), len(a), ', '.join(added) or 'nothing new', len(differ), len(changed),
                                           len(added), '== the 16 PATCHES-S4b rows' if differ == pset else
                                           'NOT the PATCHES-S4b set', len(extra) or 'none')), det


def check4(sta, stb, pset):
    a, b = sta[0], stb[0]
    p = P(TOML, SNAP)
    if not os.path.isfile(p):
        return False, 'snap1 %s ABSENT' % TOML, []
    with open(p, 'rb') as f:
        data = f.read()
    h = hashlib.sha256(data).hexdigest().upper()
    lines = data.decode('utf-8', 'replace').splitlines()
    hits = [(i + 1, l.strip()) for i, l in enumerate(lines) if 'db16cyc_pause' in l.lower()]
    hits2 = [i for i, l in enumerate(lines) if 'db16cyc' in l.lower()]
    s_b = b[TOML][6].upper() if TOML in b else 'NO ROW'
    s_a = a[TOML][6].upper() if TOML in a else 'NO ROW'
    h_ok = h.startswith(TOML_PREFIX)
    ok = h_ok and not hits and s_b == h and s_a == h and TOML not in pset
    det = ['  snap1 %s: sha256 %s (%d B, %d lines) %s %s' % (TOML, h, len(data), len(lines), '==' if h_ok else '!=',
                                                           TOML_PREFIX),
           '  STATE-S4b row %s, STATE-S4a row %s: %s; in PATCHES-S4b: %s' % (
               s_b[:16], s_a[:16], 'both == snap1' if s_b == h and s_a == h else 'MISMATCH',
               'YES (unexpected)' if TOML in pset else 'no (S4b does not touch it)'),
           '  lines containing db16cyc_pause: %d%s; lines mentioning db16cyc at all: %d' % (
               len(hits), (' -> ' + ' | '.join('L%d %s' % t for t in hits[:5])) if hits else '', len(hits2))]
    return ok, 'snap1 %s %s (%s %s), == STATE-S4b == STATE-S4a; db16cyc_pause lines: %d (#26 stays OFF)' % (
        TOML, h[:16], '==' if h_ok else '!=', TOML_PREFIX, len(hits)), det


def check5(prow, hashes):
    det, ok, n, n_ok = [], True, 0, 0
    for r in prow:
        rel = r['rel']
        bp = P(rel, BACK)
        if r['before'] == 'ABSENT':
            det.append('  NOTE %s: before ABSENT (new file, revert deletes it); backup %s' % (
                rel, 'absent (as expected)' if not os.path.exists(bp) else 'PRESENT (unexpected)'))
            continue
        n += 1
        h = sha_or(bp)
        hs = hashes.get(rel)
        hb, hbs = hs['before'] if hs else (None, None)
        size = os.path.getsize(bp) if h != 'ABSENT' else None
        good = h != 'ABSENT' and h == r['before'] and hb == r['before'] and size == hbs
        n_ok += good
        ok = ok and good
        det.append('  %s %s: backup %s (%s B) %s before %s; HASHES.txt before %s (%s B)' % (
            'PASS' if good else 'FAIL', rp(bp), h, size, '==' if h == r['before'] else '!=', r['before'][:16],
            (hb or 'none')[:16], hbs))
    found = [os.path.relpath(os.path.join(root, fn), BACK).replace('\\', '/')
             for root, _, fs in os.walk(BACK_ROOT) for fn in fs]
    extra = sorted(set(found) - set(r['rel'] for r in prow if r['before'] != 'ABSENT'))
    det.append('  files under %s: %d; not one of the 15 rows: %s' % (rp(BACK_ROOT), len(found), ', '.join(extra) or 'none'))
    ok = ok and n == 15 and n_ok == 15
    return ok, ('%d/%d backups present, sha256 == the row\'s before (== HASHES.txt before, sizes equal); extra backup '
                'files: %s' % (n_ok, n, len(extra) or 'none')), det


def main():
    hold()
    t0 = time.time()
    start = time.strftime('%Y-%m-%d %H:%M:%S')
    rf, single, xm_v3 = compose_records()
    prow = load_patches()
    hashes = load_hashes()
    pset = set(r['rel'] for r in prow)
    results = [('0 (extra)',) + check0()]
    hold()
    stb = load_state(ST_B)
    results.append(('1',) + check1(prow, hashes, stb[0], rf, single))
    hold()
    results.append(('2',) + check2())
    hold()
    sta = load_state(ST_A)
    results.append(('3',) + check3(sta, stb, prow))
    hold()
    results.append(('4',) + check4(sta, stb, pset))
    hold()
    results.append(('5',) + check5(prow, hashes))
    main_res = [x for x in results if not x[0].startswith('0')]
    npass = sum(1 for x in main_res if x[1])
    nfail = len(main_res) - npass
    extra_ok = results[0][1]
    out = ['tree-check report (read-only checker for Agent 2): composed snap1 tree S4b vs the staged after-files',
           'started %s; script %s; read-only (wrote only this report); no git, no builds' % (start, rp(__file__)),
           'tree build/agent2/snap1/DimensionsRecomp; records PATCHES-S4b.tsv, s4b/HASHES.txt, STATE-S4b-1950.tsv, '
           'STATE-S4a-1325.tsv, prep-s4b-apply-1950.txt, s4b-compose-check.py (o1-v3: %s; C1 v3 xmemory after %s)' % (
               ' -> '.join(C1V3_ORDER), xm_v3[:16])]
    older = sorted(fn for fn in (os.listdir(OUTDIR) if os.path.isdir(OUTDIR) else [])
                   if fn.startswith('tree-check-') and fn.endswith('.txt'))
    now15 = ['CHECK %s %s: %s' % (n, 'PASS' if k else 'FAIL', t) for n, k, t, _ in main_res]
    for fn in older:
        with open(os.path.join(OUTDIR, fn), 'r', encoding='utf-8', errors='replace') as f:
            old15 = [ln.rstrip('\n') for ln in f if re.match(r'^CHECK [1-5] ', ln)]
        out.append('supersedes build/agent2/s4b/checks/%s (its extra check 0 decoded the UTF-16 apply log as UTF-8 and '
                   'found no records: a checker bug); its CHECK 1-5 lines are %s' % (
                       fn, 'identical to this run' if old15 == now15 else 'DIFFERENT from this run'))
    out.append('')
    for name, ok, title, det in results:
        out.append('CHECK %s %s: %s' % (name, 'PASS' if ok else 'FAIL', title))
        out.extend(det)
        out.append('')
    fails = [x[0] for x in results if not x[1]]
    out.append('RESULT: %s (checks 1-5: %d PASS, %d FAIL; extra check 0 %s)%s; %.1f s' % (
        'PASS' if nfail == 0 and extra_ok else 'FAIL', npass, nfail, 'PASS' if extra_ok else 'FAIL',
        (' failing: ' + ', '.join(fails)) if fails else '', time.time() - t0))
    hold()
    os.makedirs(OUTDIR, exist_ok=True)
    stamp = time.strftime('%H%M')
    rep = os.path.join(OUTDIR, 'tree-check-%s.txt' % stamp)
    k = 2
    while os.path.exists(rep):
        rep = os.path.join(OUTDIR, 'tree-check-%s-%d.txt' % (stamp, k))
        k += 1
    with open(rep, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print('\n'.join(out))
    print('report: %s sha256 %s' % (rp(rep), sha(rep)))
    return 0 if nfail == 0 and extra_ok else 1


if __name__ == '__main__':
    sys.exit(main())

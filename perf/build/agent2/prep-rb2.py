"""Agent 2 - rollback build RB2 on an S3 base, at Agent 1's GO only (task #14): a clone of
build/agent9/repin/rb2-nomusttail/prep-b.py (Agent 9's re-pin of build/agent2/prep-b.py for recipe step 9.2), made by
build/agent2/make-rb-clones.py (diffs: build/agent2/RB-diffs). Agent 1, 03:11: the base is snap1's current tree (S3,
or S3d once applied; snap1-sdk/install is the S3 SDK and no S2 SDK install was kept) in the new copy
build/agent2/snapB3; snapB and snapB-off stay untouched; A = build/agent2/devoff3-bin. Changed from the re-pin: the
copy dir and the log and notes names (snapB -> snapB3), the snapshot tag (the newest PATCHES file, S3 or S3d, with its
STATE file; the PATCHES pattern now takes S3d, whose row then counts), --check-only, and the notes text. Step 1's text
below still names batch-nolr's pins; the code checks rb2-nomusttail's (VARIANT, SUMS_SHA, CFG_SHA, 870 entries).
Copies and hashing only.
  python build\\agent2\\prep-rb2.py [--resync] [--skip-copy] [--check-only] [--install DIR]
  --check-only: step 1 (the install tree, read only) and the snapshot tag, then stop before the copy.
1. Agent 9's install tree: ONLY build/agent9/install/batch-nolr (Agent 1, 02:05: --install exists for the negative test
   and refuses anything else; install/batch has skip_lr, which is unsafe for LEGO, Agent 10 Review 4 row 21). The last
   '[batch-nolr] END' line of build/agent9/logs/install-steps.txt (files, bytes, TUs, last TU, config sha);
   SHA256SUMS.txt sha256 == the pinned 24CE1493... (872 entries); every entry and no unlisted file;
   legodimensions_config.toml == build/agent9/configs/batch-nolr.toml == the pinned E60EAF1C...; generated/rexglue.cmake
   and generated/default/codegen.d == baseline's; sources.cmake lists the TUs + init + register, ending at the last TU.
2. Copy build/agent2/snap1/DimensionsRecomp -> build/agent2/snapB3/DimensionsRecomp with robocopy (/E, mtimes kept;
   --resync: /MIR after a new S-batch on snap1), except rexglue-sdk/out (snap1-sdk's output dir), rexlego/out
   (Agent 6's native banks; the OFF build never reads them: snap1-off/build.ninja names none), rexlego/generated and
   rexlego/legodimensions_config.toml (step 3 writes those). Then every copied file must match snap1 in size and mtime,
   and every patched file (snap1/PATCHES-S*.tsv, last row per file) its sha256.
3. Agent 9's step 4 into snapB3/DimensionsRecomp/rexlego: refuse unless rexlego and rexlego/generated are real
   directories that resolve under build/agent2/snapB3 (the live rexlego/generated is a junction to baseline/); the config
   first, then robocopy /MIR <install>/generated, then touch every generated file (mtime = now).
4. gen-check.py --base <install>/generated --snap <snapB3>/rexlego/generated must pass (it rewrites codegen.d once to
   snapB3 paths). Writes build/agent2/snapB3-manifest-notes.txt (ASCII) for stage-snap-bin.ps1 -ManifestNotesFile.
Log: build/agent2/snapB3-prep.txt (robocopy output: snapB3-robocopy.log). Exit 0 = ready for run-b.ps1.
"""
import argparse, hashlib, os, re, shutil, stat, subprocess, sys, time

R = r'<workspace>'
A = os.path.join(R, 'build', 'agent2')
SRC = os.path.join(A, 'snap1', 'DimensionsRecomp')
DST_ROOT = os.path.join(A, 'snapB3')
DST = os.path.join(DST_ROOT, 'DimensionsRecomp')
BASE_GEN = os.path.join(R, 'baseline', 'DimensionsRecomp', 'rexlego', 'generated')
STEPS = os.path.join(R, 'build', 'agent9', 'logs', 'install-steps.txt')
# Build B uses only install/batch-nolr (Agent 1, 02:05: never install/batch, whose skip_lr is unsafe for LEGO)
VARIANT = 'rb2-nomusttail'  # rollback re-pin (Agent 9, recipe step 9.2): was 'batch-nolr'
INSTALL = os.path.join(R, 'build', 'agent9', 'install', VARIANT)
BATCH_CFG = os.path.join(R, 'build', 'agent9', 'configs', VARIANT + '.toml')
SUMS_SHA = '8bde87171405ec9611b89cd75badc400dd93bc371cfba3634b7b446fcf9d7b14'  # install/rb2-nomusttail/SHA256SUMS.txt (02:10:49)
CFG_SHA = 'fc034d495dac395f45cdc0ac0dc7bfd88c8d2046a09590b88563b63be1c82924'  # configs/rb2-nomusttail.toml (S2.10 minus musttail_calls; no skip_lr)
TOOL = os.path.join(R, 'build', 'agent9', 'bin', 'rexglue.exe')
TOOL_SHA = '37b32713b7516402344bb4ddb402a3cd4131353adc1aef10e1602122e9b6036a'
LOG = os.path.join(A, 'snapB3-prep.txt')
RCLOG = os.path.join(A, 'snapB3-robocopy.log')
NOTES = os.path.join(A, 'snapB3-manifest-notes.txt')
EXCL_DIRS = [r'rexglue-sdk\out', r'rexlego\out', r'rexlego\generated']
EXCL_FILES = [r'rexlego\legodimensions_config.toml']


def log(m):
    line = time.strftime('%H:%M:%S ') + m
    print(line, flush=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def fail(m):
    log('FAIL ' + m)
    sys.exit(1)


def read_text(p):
    """A log file's text: PowerShell 5.1's Out-File writes UTF-16LE with a BOM (build/agent9/logs/install-steps.txt
    does), Python and Out-File -Encoding utf8 write UTF-8."""
    b = open(p, 'rb').read()
    if b[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return b.decode('utf-16', errors='replace')
    return b.decode('utf-8-sig', errors='replace')


def lp(p):
    if p.startswith('\\\\?\\'):
        return p
    return '\\\\?\\' + os.path.abspath(p)


def sha(p):
    h = hashlib.sha256()
    with open(lp(p), 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def is_link(p):
    st = os.lstat(lp(p))
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def excluded(rel, items):
    r = os.path.normcase(rel)
    return any(r == os.path.normcase(x) or r.startswith(os.path.normcase(x) + '\\') for x in items)


def walk(root, excl_dirs=(), excl_files=()):
    """{relative path: stat} of every file under root, minus the excluded relative dirs/files; plus the linked dirs."""
    root = lp(root)
    ed = {os.path.normcase(d) for d in excl_dirs}
    ef = {os.path.normcase(f) for f in excl_files}
    out, links = {}, []
    for dp, dn, fn in os.walk(root):
        reld = dp[len(root):].lstrip('\\')
        keep = []
        for d in dn:
            rd = os.path.join(reld, d) if reld else d
            if os.path.normcase(rd) in ed:
                continue
            if is_link(os.path.join(dp, d)):
                links.append(rd)
                continue
            keep.append(d)
        dn[:] = keep
        for n in fn:
            rf = os.path.join(reld, n) if reld else n
            if os.path.normcase(rf) in ef:
                continue
            out[rf] = os.stat(os.path.join(dp, n))
    return out, links


def robocopy(args, what):
    t = time.time()
    with open(RCLOG, 'ab') as f:
        f.write(('\r\n# %s %s: robocopy %s\r\n' % (time.strftime('%H:%M:%S'), what, ' '.join(args))).encode('utf-8'))
        f.flush()
        rc = subprocess.call(['robocopy'] + args, stdout=f, stderr=subprocess.STDOUT)
    if rc >= 8:
        fail('%s: robocopy exit %d (see %s)' % (what, rc, RCLOG))
    return rc, time.time() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resync', action='store_true', help='robocopy /MIR snap1 -> snapB3 again (after a new S-batch)')
    ap.add_argument('--skip-copy', action='store_true', help='keep the snapB3 copy; re-check it and redo steps 3-4')
    ap.add_argument('--install', default=INSTALL, help='only build/agent9/install/rb2-nomusttail is accepted')
    ap.add_argument('--check-only', action='store_true', help='step 1 and the snapshot tag only: nothing is copied')
    a = ap.parse_args()
    I = os.path.abspath(a.install)
    t0 = time.time()
    log('START prep-rb2: install tree %s, snapshot copy %s' % (I, DST))
    # refuse before anything is read or written: build B uses only install/batch-nolr (never install/batch)
    if os.path.normcase(os.path.realpath(I)) != os.path.normcase(os.path.realpath(INSTALL)):
        fail('refusing install tree %s: build B uses only %s (install/batch has skip_lr, unsafe for LEGO); nothing '
             'copied' % (I, INSTALL))
    if not os.path.isdir(INSTALL) or is_link(INSTALL):
        fail('%s is missing or a link: stop' % INSTALL)

    # 1. Agent 9's install tree
    tag = '[%s] END ' % VARIANT
    ends = [l.strip() for l in read_text(STEPS).splitlines() if tag in l]
    if not ends:
        fail('no %s line in %s' % (tag.strip(), STEPS))
    m = re.search(r'files=(\d+) bytes=(\d+) TUs=(\d+) last=(\S+) config_sha=([0-9A-Fa-f]+)', ends[-1])
    if not m:
        fail('unparsed END line: ' + ends[-1])
    e_files, e_bytes, e_tus, e_last, e_cfg = int(m[1]), int(m[2]), int(m[3]), m[4], m[5].lower()
    log('install END line: ' + ends[-1])
    sums_path = os.path.join(I, 'SHA256SUMS.txt')
    sums = {}
    for line in open(sums_path, encoding='utf-8-sig'):
        line = line.rstrip('\r\n')
        if not line.strip():
            continue
        mm = re.match(r'^([0-9a-fA-F]{64}) [ *](.+)$', line)
        if not mm:
            fail('bad SHA256SUMS.txt line: ' + line)
        sums[os.path.normcase(os.path.normpath(mm[2]))] = mm[1].lower()
    sums_sha = sha(sums_path)
    if sums_sha != SUMS_SHA or len(sums) != 870:
        fail('SHA256SUMS.txt sha256 %s with %d entries; build B expects the pinned %s (870 entries)'
             % (sums_sha, len(sums), SUMS_SHA))
    found, links = walk(I)
    if links:
        fail('links in the install tree: %s' % links[:5])
    files = {os.path.normcase(k): v for k, v in found.items() if os.path.normcase(k) != 'sha256sums.txt'}
    nbytes = sum(s.st_size for s in files.values())
    if len(files) != e_files or nbytes != e_bytes:
        fail('install tree has %d files / %d bytes, the END line says %d / %d' % (len(files), nbytes, e_files, e_bytes))
    extra, missing = sorted(set(files) - set(sums)), sorted(set(sums) - set(files))
    if extra or missing:
        fail('install tree vs SHA256SUMS.txt: %d unlisted %s, %d missing %s' % (len(extra), extra[:3], len(missing),
                                                                              missing[:3]))
    t = time.time()
    bad = [r for r in sorted(files) if sha(os.path.join(I, r)) != sums[r]]
    if bad:
        fail('%d install file(s) differ from SHA256SUMS.txt: %s' % (len(bad), bad[:5]))
    if sha(sums_path) != sums_sha:
        fail('SHA256SUMS.txt changed during the check')
    sums_time = time.strftime('%H:%M:%S')
    log('install tree: %d files, %d bytes, every file matches SHA256SUMS.txt (sha256 %s), %.1fs'
        % (len(files), nbytes, sums_sha, time.time() - t))
    cfg = sums.get('legodimensions_config.toml')
    bcfg = sha(BATCH_CFG)
    if cfg is None or cfg != bcfg or not cfg.startswith(e_cfg) or cfg != CFG_SHA:
        fail('config: install %s, configs/%s.toml %s, END line %s, pinned %s' % (cfg, VARIANT, bcfg, e_cfg, CFG_SHA))
    for rel in (r'rexglue.cmake', r'default\codegen.d'):
        if sums[os.path.normcase(os.path.join('generated', rel))] != sha(os.path.join(BASE_GEN, rel)):
            fail('install generated\\%s differs from baseline\'s (gen-check assumes the baseline layout)' % rel)
    src_text = open(os.path.join(I, 'generated', 'default', 'sources.cmake'), encoding='utf-8-sig').read()
    listed = re.findall(r'\$\{CMAKE_CURRENT_LIST_DIR\}/(\S+?\.cpp)', src_text)
    tus = [x for x in listed if re.fullmatch(r'legodimensions_recomp\.\d+\.cpp', x)]
    if (len(tus) != e_tus or len(listed) != e_tus + 2 or not tus or tus[-1] != e_last
            or 'legodimensions_init.cpp' not in listed or 'legodimensions_register.cpp' not in listed):
        fail('sources.cmake lists %d sources, %d TUs, last %s; the END line says %d TUs, last %s'
             % (len(listed), len(tus), tus[-1] if tus else None, e_tus, e_last))
    tool = sha(TOOL) if os.path.isfile(TOOL) else 'missing'
    log('config %s == configs/%s.toml == the END line == the pin; rexglue.cmake and codegen.d == baseline\'s; '
        'sources.cmake: %d sources (%d TUs, last %s); build/agent9/bin/rexglue.exe %s (%s the recipe\'s 37B32713)'
        % (cfg[:16], VARIANT, len(listed), len(tus), tus[-1], tool[:16],
           'matches' if tool == TOOL_SHA else 'DIFFERS FROM'))

    # snapshot tag (task #14): the newest PATCHES-S<N>[suffix].tsv in apply order (S1, S2, S3, S3d); the newest STATE
    # file must be that tag's (snap-patch.py apply writes both), and only an S3 or S3d base is accepted
    pfiles = sorted((f for f in os.listdir(os.path.join(A, 'snap1')) if re.fullmatch(r'PATCHES-S\d+[a-z]*\.tsv', f)),
                    key=lambda f: (int(re.match(r'PATCHES-S(\d+)', f)[1]), f))
    snap_tag = pfiles[-1][8:-4] if pfiles else '?'
    states = sorted((f for f in os.listdir(os.path.join(A, 'snap1')) if re.fullmatch(r'STATE-S\d+[a-z]*-\d{4}\.tsv', f)),
                    key=lambda f: os.stat(os.path.join(A, 'snap1', f)).st_mtime_ns)
    if snap_tag not in ('S3', 'S3d') or not states or not states[-1].startswith('STATE-%s-' % snap_tag):
        fail('snap1: newest PATCHES tag %s, newest STATE file %s: an S3 or S3d base with its STATE file is required'
             % (snap_tag, states[-1] if states else None))
    log('snapshot tag %s: PATCHES %s; newest STATE file %s' % (snap_tag, ', '.join(f[8:-4] for f in pfiles), states[-1]))
    if a.check_only:
        log('DONE --check-only: step 1 passed, snapshot tag %s; nothing copied (%s %s)'
            % (snap_tag, DST, 'exists' if os.path.exists(DST) else 'does not exist yet'))
        return 0
    # 2. snapB3 = snap1 (S3 or S3d) minus the excluded dirs and the config. Every write below goes under build/agent2/snapB3:
    #    stop if build/agent2, snapB3 or snapB3/DimensionsRecomp is a link or resolves elsewhere.
    for p in (A, DST_ROOT, DST):
        if os.path.lexists(p) and (is_link(p) or os.path.normcase(os.path.realpath(p)) != os.path.normcase(
                os.path.abspath(p))):
            fail('%s is a link or resolves elsewhere (%s): stop' % (p, os.path.realpath(p)))
    if not a.skip_copy:
        if os.path.exists(DST) and not a.resync:
            fail(DST + ' exists: use --resync (after a new S-batch) or --skip-copy')
        xd = [os.path.join(SRC, d) for d in EXCL_DIRS] + [os.path.join(DST, d) for d in EXCL_DIRS]
        xf = [os.path.join(SRC, f) for f in EXCL_FILES] + [os.path.join(DST, f) for f in EXCL_FILES]
        mode = '/MIR' if a.resync else '/E'
        rc, dt = robocopy([SRC, DST, mode, '/COPY:DAT', '/DCOPY:DAT', '/R:1', '/W:1', '/MT:8', '/XJ', '/NFL', '/NDL',
                           '/NP', '/XD'] + xd + ['/XF'] + xf, 'snap1 -> snapB3')
        log('robocopy snap1 -> snapB3 (%s): exit %d, %.1fs' % (mode, rc, dt))
    t = time.time()
    sf, sl = walk(SRC, EXCL_DIRS, EXCL_FILES)
    df, dl = walk(DST, EXCL_DIRS, EXCL_FILES)
    if sl or dl:
        fail('linked dirs: snap1 %s, snapB3 %s' % (sl[:3], dl[:3]))
    miss, extra = sorted(set(sf) - set(df)), sorted(set(df) - set(sf))
    diff = [r for r in sorted(set(sf) & set(df))
            if sf[r].st_size != df[r].st_size or sf[r].st_mtime_ns != df[r].st_mtime_ns]
    if miss or extra or diff:
        fail('snapB3 vs snap1: %d missing %s, %d extra %s, %d size/mtime differ %s'
             % (len(miss), miss[:3], len(extra), extra[:3], len(diff), diff[:3]))
    nb = sum(s.st_size for s in df.values())
    longest = max((len(DST) + 1 + len(r) for r in df), default=0)
    rows = {}
    for pf in pfiles:
        for line in open(os.path.join(A, 'snap1', pf), encoding='utf-8-sig'):
            line = line.rstrip('\r\n')
            if not line or line.startswith('#'):
                continue
            c = line.split('\t')
            rows[c[0]] = c[2].lower()
    bad, skipped = [], []
    for rel, after in sorted(rows.items()):
        rb = rel.replace('/', '\\')
        if excluded(rb, EXCL_DIRS + EXCL_FILES):
            skipped.append(rel)
            continue
        p = os.path.join(DST, rb)
        if after == 'deleted':
            if os.path.lexists(lp(p)):
                bad.append(rel + ' (deleted in snap1, present in snapB3)')
            continue
        if not os.path.isfile(lp(p)) or sha(p) != after:
            bad.append(rel)
    if bad:
        fail('%d patched file(s) in snapB3 differ from their PATCHES rows: %s' % (len(bad), bad[:5]))
    log('snapB3 copy verified: %d files, %d bytes, all equal to snap1 in size and mtime (longest path %d chars); %d '
        'patched files (%s) hash-equal their last PATCHES row%s; %.1fs'
        % (len(df), nb, longest, len(rows) - len(skipped), ', '.join(pfiles),
           ' (%d in excluded dirs skipped: %s)' % (len(skipped), skipped[:3]) if skipped else '', time.time() - t))

    # 3. Agent 9's step 4 (recipe lines 312-325), with the guards Agent 1 asked for (23:40)
    S = os.path.join(DST, 'rexlego')
    G = os.path.join(S, 'generated')
    if os.path.normcase(os.path.realpath(DST_ROOT)) != os.path.normcase(os.path.abspath(DST_ROOT)):
        fail('%s is not a real directory (resolves to %s)' % (DST_ROOT, os.path.realpath(DST_ROOT)))
    root_n = os.path.normcase(os.path.abspath(DST_ROOT)) + os.sep
    if not os.path.isdir(S) or is_link(S):
        fail(S + ' is not a real directory')
    existed = os.path.lexists(G)
    if existed and (is_link(G) or not os.path.isdir(G)):
        fail(G + ' is a link (or not a directory): stop')
    os.makedirs(G, exist_ok=True)
    for p in (S, G, os.path.join(S, 'legodimensions_config.toml')):
        rp = os.path.normcase(os.path.realpath(p))
        if not rp.startswith(root_n):
            fail('%s resolves to %s, outside build/agent2/snapB3' % (p, rp))
    log('guards: %s and %s are real directories (generated %s) and every target resolves under %s'
        % (S, G, 'existed' if existed else 'created', DST_ROOT))
    shutil.copy2(os.path.join(I, 'legodimensions_config.toml'), os.path.join(S, 'legodimensions_config.toml'))
    rc, dt = robocopy([os.path.join(I, 'generated'), G, '/MIR', '/COPY:DAT', '/R:1', '/W:1', '/MT:8', '/NFL', '/NDL',
                       '/NP'], 'install generated -> snapB3 generated')
    now = time.time()
    n = 0
    for dp, dn, fn in os.walk(G):
        for x in fn:
            os.utime(os.path.join(dp, x), (now, now))
            n += 1
    touched = time.strftime('%H:%M:%S', time.localtime(now))
    log('step 4: config copied first, robocopy /MIR install generated -> snapB3 generated exit %d (%.1fs), touched %d '
        'files at %s' % (rc, dt, n, touched))

    # 4. gen-check against the install tree (rewrites codegen.d to snapB3 paths once)
    gcl = os.path.join(A, 'snapB3-prep-gen-check.log')
    with open(gcl, 'wb') as f:
        rc = subprocess.call([sys.executable, os.path.join(A, 'gen-check.py'), '--base', os.path.join(I, 'generated'),
                              '--snap', G, '--snap-rex', S], stdout=f, stderr=subprocess.STDOUT)
    out = open(gcl, encoding='utf-8', errors='replace').read().splitlines()
    summ = next((l for l in out if l.startswith('# gen-check')), '?').lstrip('# ')
    if rc != 0 or not out or out[-1] != 'RESULT: PASS':
        fail('gen-check exit %d: %s' % (rc, ' | '.join(out[-4:])))
    if sha(os.path.join(S, 'legodimensions_config.toml')) != cfg:
        fail('the snapB3 config differs from the install tree\'s')
    log('gen-check PASS: ' + summ)
    s2cfg = sha(os.path.join(SRC, 'rexlego', 'legodimensions_config.toml'))
    notes = [
        "rollback build RB2 (recipe step 9.2) = codegen build B (Agent 9's codegen option; "
        "perf-notes/agent9-codegen.md 'Session 2: regen+build recipe'): "
        "generated by build/agent9/bin/rexglue.exe (sha256 %s) with build/agent9/configs/%s.toml (no skip_lr)."
        % (tool, VARIANT),
        'install tree build/agent9/install/%s, %s' % (VARIANT, ends[-1]),
        'install SHA256SUMS.txt sha256 %s: %d entries, every file verified at %s; legodimensions_config.toml sha256 %s '
        '(the %s snapshot config is %s).' % (sums_sha, len(sums), sums_time, cfg, snap_tag, s2cfg),
        'snapB3 = build/agent2/snap1/DimensionsRecomp at %s, copied by prep-rb2.py (robocopy, mtimes kept) without '
        'rexglue-sdk/out and rexlego/out: %d files, %d bytes, all equal to snap1 in size and mtime; the %d patched '
        'files hash-equal their last PATCHES row (%s).' % (snap_tag, len(df), nb, len(rows) - len(skipped),
                                                          ', '.join(f[8:-4] for f in pfiles)),
        'snapB3 rexlego/legodimensions_config.toml and rexlego/generated = the install tree (step 4: config first, '
        'robocopy /MIR, %d generated files touched at %s); gen-check.py rewrote codegen.d to snapB3 paths.' % (n, touched),
        'gen-check at prep: ' + summ,
        'A (the same snapshot and SDK, pinned 0.0.23.3 codegen): build/agent2/devoff3-bin (the S3 OFF build; S3d '
        'changes only rexlego/src/gpu_native/draw.cpp, which OFF builds do not compile).',
    ]
    with open(NOTES, 'w', encoding='ascii', errors='replace') as f:
        f.write('\n'.join(notes) + '\n')
    free = shutil.disk_usage(R).free / 2 ** 30
    log('DONE prep-b in %.1fs; notes %s; free C: %.1f GB' % (time.time() - t0, NOTES, free))
    return 0


if __name__ == '__main__':
    sys.exit(main())

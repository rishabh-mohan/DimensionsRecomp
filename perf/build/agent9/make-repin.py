"""Agent 9, session 3: re-pinned copies of Agent 2's build-B tools for a rollback build (recipe step 9).

Read-only on build/agent2 and the install trees; writes only build/agent9/repin/<tree>/ and build/agent9/repin/README.md.
For each rollback tree it
  1. re-runs prep-b.py's step-1 checks on the tree (END line, SHA256SUMS entries and every file hash, config ==
     configs/<tree>.toml == END line, rexglue.cmake / codegen.d == baseline's, sources.cmake TU count);
  2. writes prep-b.py and run-b.ps1 with the batch-nolr pins replaced (every replacement must match exactly once,
     so a changed tool stops this script instead of producing a half-pinned copy), plus unified diffs.
Agent 2 owns the tools: these copies are a proposal, used only after a B failure and Agent 1's GO.
Usage: python build/agent9/make-repin.py   (one thread; run it through bench/agent9/cpu2.ps1)
"""
import difflib, hashlib, os, re, stat, sys, time

R = r'<workspace>'
A = os.path.join(R, 'build', 'agent2')
N9 = os.path.join(R, 'build', 'agent9')
STEPS = os.path.join(N9, 'logs', 'install-steps.txt')
BASE_GEN = os.path.join(R, 'baseline', 'DimensionsRecomp', 'rexlego', 'generated')
OUT = os.path.join(N9, 'repin')
B_SUMS = '24ce1493fb8dae37e00b556eb8871d633921e44378d960de4359b104b16cdb8e'
B_CFG = 'e60eaf1ceb575572ba0274aa5f52e97f25a35c01690b41e6a637739408e6a090'
TREES = [  # tree, recipe step, what it drops
    ('rb1-nolocal', '9.1', 'ctr_as_local, xer_as_local, reserved_as_local, cr_as_local, cr_compare_so_zero'),
    ('rb2-nomusttail', '9.2', 'musttail_calls'),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def read_text(p):
    raw = open(p, 'rb').read()
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return raw.decode('utf-16')
    return raw.decode('utf-8-sig')


def fail(msg):
    print('FAIL: ' + msg)
    sys.exit(1)


def check_tree(t):
    """prep-b.py step 1 (lines 146-207 of C0067F18) for install/<t>; returns the values the pins need."""
    I = os.path.join(N9, 'install', t)
    tag = '[%s] END ' % t
    ends = [l.strip() for l in read_text(STEPS).splitlines() if tag in l]
    if not ends:
        fail('no %s line in %s' % (tag.strip(), STEPS))
    m = re.search(r'files=(\d+) bytes=(\d+) TUs=(\d+) last=(\S+) config_sha=([0-9A-Fa-f]+)', ends[-1])
    if not m:
        fail('unparsed END line: ' + ends[-1])
    e_files, e_bytes, e_tus, e_last, e_cfg = int(m[1]), int(m[2]), int(m[3]), m[4], m[5].lower()
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
    files, links = {}, []
    for dp, dn, fn in os.walk(I):
        for x in list(dn) + fn:
            p = os.path.join(dp, x)
            st = os.lstat(p)
            if stat.S_ISLNK(st.st_mode) or getattr(st, 'st_file_attributes', 0) & 0x400:
                links.append(p)
        for x in fn:
            rel = os.path.normcase(os.path.relpath(os.path.join(dp, x), I))
            if rel != 'sha256sums.txt':
                files[rel] = os.path.getsize(os.path.join(dp, x))
    if links:
        fail('%s: links %s' % (t, links[:3]))
    nbytes = sum(files.values())
    if len(files) != e_files or nbytes != e_bytes:
        fail('%s: %d files / %d bytes, END line %d / %d' % (t, len(files), nbytes, e_files, e_bytes))
    if set(files) != set(sums):
        fail('%s: tree vs SHA256SUMS.txt differ (%d unlisted, %d missing)'
             % (t, len(set(files) - set(sums)), len(set(sums) - set(files))))
    bad = [r for r in sorted(files) if sha(os.path.join(I, r)) != sums[r]]
    if bad:
        fail('%s: %d file(s) differ from SHA256SUMS.txt: %s' % (t, len(bad), bad[:5]))
    if sha(sums_path) != sums_sha:
        fail('%s: SHA256SUMS.txt changed during the check' % t)
    cfg = sums.get('legodimensions_config.toml')
    bcfg = sha(os.path.join(N9, 'configs', t + '.toml'))
    if cfg is None or cfg != bcfg or not cfg.startswith(e_cfg):
        fail('%s: config install %s, configs %s, END %s' % (t, cfg, bcfg, e_cfg))
    for rel in ('rexglue.cmake', r'default\codegen.d'):
        if sums[os.path.normcase(os.path.join('generated', rel))] != sha(os.path.join(BASE_GEN, rel)):
            fail('%s: generated\\%s differs from baseline\'s' % (t, rel))
    src = open(os.path.join(I, 'generated', 'default', 'sources.cmake'), encoding='utf-8-sig').read()
    listed = re.findall(r'\$\{CMAKE_CURRENT_LIST_DIR\}/(\S+?\.cpp)', src)
    tus = [x for x in listed if re.fullmatch(r'legodimensions_recomp\.\d+\.cpp', x)]
    if (len(tus) != e_tus or len(listed) != e_tus + 2 or not tus or tus[-1] != e_last
            or 'legodimensions_init.cpp' not in listed or 'legodimensions_register.cpp' not in listed):
        fail('%s: sources.cmake %d sources, %d TUs; END line %d TUs, last %s' % (t, len(listed), len(tus), e_tus, e_last))
    return dict(sums_sha=sums_sha, entries=len(sums), cfg=cfg, tus=len(tus), last=e_last, files=len(files),
                nbytes=nbytes, end=ends[-1])


def sub1(text, old, new, what):
    n = text.count(old)
    if n != 1:
        fail('%s: expected exactly 1 match of %r, found %d (the tool changed: redo the re-pin by hand)' % (what, old, n))
    return text.replace(old, new)


def repin(t, step, drops, v, prep, runb):
    p = prep
    p = sub1(p, "VARIANT = 'batch-nolr'",
             "VARIANT = '%s'  # rollback re-pin (Agent 9, recipe step %s): was 'batch-nolr'" % (t, step), 'prep-b VARIANT')
    p = sub1(p, "SUMS_SHA = '%s'  # install/batch-nolr/SHA256SUMS.txt (23:54)" % B_SUMS,
             "SUMS_SHA = '%s'  # install/%s/SHA256SUMS.txt (%s)" % (v['sums_sha'], t, v['end'][:8]), 'prep-b SUMS_SHA')
    p = sub1(p, "CFG_SHA = '%s'  # configs/batch-nolr.toml (S2.10, no skip_lr)" % B_CFG,
             "CFG_SHA = '%s'  # configs/%s.toml (S2.10 minus %s; no skip_lr)" % (v['cfg'], t, drops), 'prep-b CFG_SHA')
    p = sub1(p, "len(sums) != 872:", "len(sums) != %d:" % v['entries'], 'prep-b entry count')
    p = sub1(p, "(872 entries)'", "(%d entries)'" % v['entries'], 'prep-b entry-count message')
    p = sub1(p, "help='only build/agent9/install/batch-nolr is accepted'",
             "help='only build/agent9/install/%s is accepted'" % t, 'prep-b --install help')
    r = runb
    r = sub1(r, "[string]$Install = 'build\\agent9\\install\\batch-nolr'",
             "[string]$Install = 'build\\agent9\\install\\%s'" % t, 'run-b -Install default')
    r = sub1(r, '$nolr = "$R\\build\\agent9\\install\\batch-nolr"',
             '$nolr = "$R\\build\\agent9\\install\\%s"  # rollback re-pin (Agent 9, recipe step %s): was batch-nolr'
             % (t, step), 'run-b $nolr')
    r = sub1(r, "-ne '%s') { Log \"STOP: $nolr\\SHA256SUMS.txt is $sumsSha, not the pinned 24CE1493...\"" % B_SUMS.upper(),
             "-ne '%s') { Log \"STOP: $nolr\\SHA256SUMS.txt is $sumsSha, not the pinned %s...\""
             % (v['sums_sha'].upper(), v['sums_sha'][:8].upper()), 'run-b SHA256SUMS pin')
    r = sub1(r, "-ne '%s') { Log \"STOP: snapB legodimensions_config.toml is $cfgSha, not the pinned batch-nolr config "
                "E60EAF1C...\"" % B_CFG.upper(),
             "-ne '%s') { Log \"STOP: snapB legodimensions_config.toml is $cfgSha, not the pinned %s config %s...\""
             % (v['cfg'].upper(), t, v['cfg'][:8].upper()), 'run-b config pin')
    r = sub1(r, "with Agent 9's batch-nolr codegen options, NATIVE_GPU=OFF",
             "with Agent 9's %s codegen options (rollback step %s), NATIVE_GPU=OFF" % (t, step), 'run-b $what')
    r = sub1(r, "Agent 9's batch-nolr options (build/agent9/install/batch-nolr, 430 TUs, no skip_lr;",
             "Agent 9's %s options (build/agent9/install/%s, %d TUs, no skip_lr; rollback step %s: batch-nolr minus %s;"
             % (t, t, v['tus'], step, drops), 'run-b $cgNote')
    d = os.path.join(OUT, t)
    os.makedirs(d, exist_ok=True)
    for name, old, new in (('prep-b.py', prep, p), ('run-b.ps1', runb, r)):
        with open(os.path.join(d, name), 'w', encoding='utf-8', newline='') as f:
            f.write(new)
        diff = difflib.unified_diff(old.splitlines(True), new.splitlines(True), 'build/agent2/' + name,
                                    'build/agent9/repin/%s/%s' % (t, name))
        with open(os.path.join(d, name + '.diff'), 'w', encoding='utf-8', newline='') as f:
            f.writelines(diff)
    return p, r


def main():
    t0 = time.time()
    srcs = {}
    for name in ('prep-b.py', 'run-b.ps1'):
        raw = open(os.path.join(A, name), 'rb').read()
        srcs[name] = (raw.decode('utf-8-sig'), hashlib.sha256(raw).hexdigest(), raw[:3] == b'\xef\xbb\xbf',
                      b'\r\n' in raw)
    for name, (txt, h, bom, crlf) in srcs.items():
        print('source build/agent2/%s sha256 %s (bom %s, crlf %s)' % (name, h[:8].upper(), bom, crlf))
        if bom:
            fail('%s has a BOM: this script writes without one; redo by hand' % name)
    rows = []
    for t, step, drops in TREES:
        v = check_tree(t)
        print('%s: step-1 checks PASS: %d files, %d B, every file matches SHA256SUMS.txt (%s, %d entries); config %s '
              '== configs/%s.toml == END line; rexglue.cmake and codegen.d == baseline; %d TUs, last %s'
              % (t, v['files'], v['nbytes'], v['sums_sha'][:8].upper(), v['entries'], v['cfg'][:8].upper(), t,
                 v['tus'], v['last']))
        p, r = repin(t, step, drops, v, srcs['prep-b.py'][0], srcs['run-b.ps1'][0])
        rows.append((t, step, drops, v, hashlib.sha256(p.encode()).hexdigest(), hashlib.sha256(r.encode()).hexdigest()))
    L = ['# Re-pinned build-B tools for a rollback build (recipe step 9)', '',
         'Written by `build/agent9/make-repin.py` at %s. Agent 2 owns `prep-b.py` and `run-b.ps1`; these copies are a'
         % time.strftime('%H:%M:%S'),
         'proposal for after a B failure and Agent 1\'s GO. They were made from `build/agent2/prep-b.py` sha256 `%s` and'
         % srcs['prep-b.py'][1][:8].upper(),
         '`build/agent2/run-b.ps1` sha256 `%s`. If either has changed since, rerun the script (it stops on any pin it'
         % srcs['run-b.ps1'][1][:8].upper(),
         'cannot match exactly once).', '',
         '| Tree | Recipe step | Drops | `SHA256SUMS.txt` sha256 | Entries | Config sha256 | TUs (last) | Gate |',
         '|---|---|---|---|---|---|---|---|',
         '| `batch-nolr` (B, current) | - | - | `%s` | 872 | `%s` | 430 (`legodimensions_recomp.429.cpp`) | 432 |'
         % (B_SUMS.upper(), B_CFG.upper())]
    for t, step, drops, v, ph, rh in rows:
        L.append('| `%s` | %s | %s | `%s` | %d | `%s` | %d (`%s`) | %d |'
                 % (t, step, drops, v['sums_sha'].upper(), v['entries'], v['cfg'].upper(), v['tus'], v['last'],
                    v['tus'] + 2))
    L += ['', 'Each tree passed prep-b.py\'s step-1 checks again (this script): END line parsed, every file hash-matches',
          '`SHA256SUMS.txt`, config == `configs/<tree>.toml` == END line, `rexglue.cmake` and `codegen.d` == baseline\'s,',
          'and the `sources.cmake` TU count matches.', '',
          '## What changes', '',
          '- `prep-b.py`: `VARIANT`, `SUMS_SHA`, `CFG_SHA`, the entry count (2 places) and the `--install` help text.',
          '- `run-b.ps1`: the `-Install` default, `$nolr`, the two pins (and their STOP messages), `$what` and `$cgNote`.',
          '- Not changed: `-Out` (default `devoffB-bin`, the name in Agent 8\'s matrices). To keep the failed B, pass',
          '  another `-Out` and change `b-chain.ps1`\'s `devoffB-bin` hash lines to match.', '',
          '## Use (Agent 2, after Agent 1\'s GO)', '',
          '1. Review `build/agent9/repin/<tree>/prep-b.py.diff` and `run-b.ps1.diff`, then copy the two files over',
          '   `build/agent2/` (or apply the same edits by hand).',
          '2. `python build\\agent2\\prep-b.py --skip-copy`: keeps the snapB copy, re-checks it and redoes step 4.',
          '   Step 4\'s robocopy /MIR also deletes TUs the tree no longer has (rb2 has no `.429.cpp`).',
          '3. Run `run-b.ps1` as for B, with its fresh OFF configure: the TU count changes, and almost every TU',
          '   recompiles anyway. The gate is then TUs + 2 (table above).', '',
          '| Tree | `prep-b.py` copy sha256 | `run-b.ps1` copy sha256 |', '|---|---|---|']
    for t, step, drops, v, ph, rh in rows:
        L.append('| `%s` | `%s` | `%s` |' % (t, ph[:16].upper(), rh[:16].upper()))
    with open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    print('wrote %s and %d tree dirs in %.1fs' % (os.path.join(OUT, 'README.md'), len(rows), time.time() - t0))
    return 0


if __name__ == '__main__':
    sys.exit(main())

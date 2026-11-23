"""Stage a text-only export of the S4 perf workspace (notes, scripts, small results).

Writes build/agent1/perf-export/perf/<...> plus MANIFEST.tsv and EXCLUDED.tsv.
Nothing here touches git; Agent 1 decides where (and whether) the export is pushed.

  python export_perf.py            # dry run: summary + EXCLUDED/INCLUDED lists only
  python export_perf.py --copy     # also copy the files (the old export is replaced)
  python export_perf.py --copy --no-scrub   # keep absolute paths / the account name as they are

With --copy, every copied file is scrubbed: the workspace path (any separator style, also
JSON-escaped and file:/// forms) becomes <workspace>, other C:\\Users\\<name> paths become
C:\\Users\\<user>, a profile path cut off part-way through the account name (a truncated log or
grep line, e.g. C:/Users/ plus the first letters) also becomes C:\\Users\\<user>, and any remaining
account name becomes <user>. A final pass counts leftovers (full or cut-off).
"""
import fnmatch, hashlib, os, re, shutil, sys

WS = r'<workspace>'
USER = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(WS)))))  # '<user>'
_SEP = r'(?:\\\\|\\|/)'
WS_RE = re.compile(r'(?i)(?:file:///?)?[a-z]:' + _SEP + r'users' + _SEP + re.escape(USER) + _SEP + r'\.vscode'
                   + _SEP + r'projects' + _SEP + r'games' + _SEP + r'lego-dimensions-recomp')
PROFILE_RE = re.compile(r'(?i)([a-z]:' + _SEP + r'users' + _SEP + r')' + re.escape(USER))
USER_RE = re.compile(r'(?i)' + re.escape(USER))
# A profile path cut off part-way through the account name (a truncated log or grep line).
TRUNC_RE = re.compile(r'(?i)([a-z]:' + _SEP + r'users' + _SEP + r')(?:'
                      + '|'.join(re.escape(USER[:k]) for k in range(len(USER) - 1, 0, -1))
                      + r')(?=\.\.\.|\u2026|[^a-z0-9._\-]|$)')


def scrub_file(path):
    """Rewrite machine paths / the account name in a copied text file; returns the edit count."""
    with open(path, 'rb') as f:
        data = f.read()
    text = data.decode('utf-8', errors='surrogateescape')
    new, n1 = WS_RE.subn('<workspace>', text)
    new, n2 = PROFILE_RE.subn(lambda m: m.group(1) + '<user>', new)
    new, n4 = TRUNC_RE.subn(lambda m: m.group(1) + '<user>', new)
    new, n3 = USER_RE.subn('<user>', new)
    n = n1 + n2 + n3 + n4
    if n:
        st = os.stat(path)
        with open(path, 'wb') as f:
            f.write(new.encode('utf-8', errors='surrogateescape'))
        os.utime(path, (st.st_atime, st.st_mtime))
    return n
OUT = os.path.join(WS, 'build', 'agent1', 'perf-export')
DEST = os.path.join(OUT, 'perf')

# (source dir under WS, dest dir under perf/, per-file size cap in bytes)
ROOTS = [
    ('perf-notes', 'notes', 1_000_000),
    ('harness', 'harness', 512_000),
    ('env', 'env', 512_000),
    ('bench', 'bench', 512_000),
    ('build', 'build', 512_000),
]
TEXT_EXT = {'.md', '.txt', '.tsv', '.csv', '.json', '.py', '.ps1', '.psm1', '.psd1', '.cmd', '.bat',
            '.toml', '.ini', '.cfg', '.yaml', '.yml', '.diff', '.patch', '.cs', '.c', '.cpp', '.h',
            '.hpp', '.inc', '.def', '.sh', '.cmake'}
PRUNE_ANY = {'generated', 'out', '.git', '__pycache__', 'node_modules', '.vs', 'CMakeFiles', '.cache',
             'DimensionsRecomp', 'rexglue-sdk', 'rexlego', 'thirdparty', 'research', 'install',
             'recovered', 'codegen-frozen', 'codegen-tool', 'gen-noflag', 'compile-one-test',
             'scratch-inc', 'nmtest', 'ppcmap-test', 'probe-toggle', 'compat', 'link-dry', 'rbt-logs'}
PRUNE_GLOB = ['snap*', 'live-backup*', 'obj-*', 'log-*', 'perf-export', '*backup*', 'scratch', 'runs', 'logs']
VERSIONED = re.compile(r'\.\d{4}-[0-9A-F]{8}\.\w+$')
SRC_EXT = {'.cpp', '.c', '.h', '.hpp', '.inc'}
MATRIX_RUN = re.compile(r'^build\\agent8\\matrix\\\d{8}-\d{4}$', re.I)
GEN_LINE = re.compile(r'\bctx\.(?:r|f|v|cr)\d+\b|\bPPC_(?:FUNC|STORE|LOAD|CALL)\w*|__imp__sub_[0-9A-Fa-f]{8}\s*\(')
SECRET = re.compile(r'ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|'
                    r'AKIA[0-9A-Z]{16}|(?i:(?:api[_-]?key|secret|passw(?:or)?d|auth[_-]?token)\s*[:=]\s*["\']?[A-Za-z0-9/+_\-]{12,})')


def pruned(rel_dir, name):
    if name in PRUNE_ANY or any(fnmatch.fnmatch(name, g) for g in PRUNE_GLOB):
        return True
    full = os.path.join(WS, rel_dir, name)
    for marker in ('build.ninja', 'CMakeCache.txt'):
        if os.path.exists(os.path.join(full, marker)):
            return True
    return False


# Per-extension caps outside notes/: docs and scripts generous, data small (raw per-frame
# CSVs, thread dumps and logs stay local).
EXT_CAP = {'.md': 1_000_000, '.py': 256_000, '.ps1': 256_000, '.psm1': 256_000, '.cmd': 64_000,
           '.bat': 64_000, '.cs': 256_000, '.json': 128_000, '.toml': 64_000, '.diff': 512_000,
           '.patch': 512_000, '.tsv': 64_000, '.csv': 64_000, '.txt': 64_000, '.cpp': 128_000,
           '.c': 128_000, '.h': 128_000, '.hpp': 128_000, '.inc': 64_000}
DISASM = re.compile(r'^\s*(?:[0-9A-Fa-f]{8}[:\s]+(?:[0-9A-Fa-f]{8}\s+)?)?(?:lwz|stw|stwu|lis|addi|addis|ori|mflr|mtlr|bl|blr|lfs|stfs|lfd|stfd|rlwinm|cmpwi|cmplwi|bne|beq|lhz|sth|lbz|stb|mr|li|lvx|stvx|vaddfp|vmaddfp)\.?\s+[rfv]?\d', re.M)


def classify(path, rel, cap):
    ext = os.path.splitext(path)[1].lower()
    size = os.path.getsize(path)
    if ext not in TEXT_EXT:
        return 'ext', size
    if size > cap or (not rel.startswith('perf-notes') and size > EXT_CAP.get(ext, 64_000)):
        return 'size', size
    if rel.startswith('build') and ext in SRC_EXT:
        return 'src-copy', size  # S4 code is in git; pending work is kept as .diff/.patch
    if VERSIONED.search(rel):
        return 'versioned-backup', size
    if rel.startswith('build') and ext == '.txt' and size > 32_000:
        return 'size', size
    with open(path, 'rb') as f:
        data = f.read()
    if b'\x00' in data[:8192]:
        return 'binary', size
    text = data.decode('utf-8', errors='replace')
    if SECRET.search(text):
        return 'secret?', size
    if ext in {'.cpp', '.c', '.h', '.hpp', '.inc', '.diff', '.patch', '.txt', '.s'}:
        if len(GEN_LINE.findall(text)) > 20:
            return 'gencode', size
        if len(DISASM.findall(text)) > 30:
            return 'disasm', size
    return None, size


def main():
    copy = '--copy' in sys.argv
    inc, exc = [], []
    for src, dst, cap in ROOTS:
        base = os.path.join(WS, src)
        for dirpath, dirnames, filenames in os.walk(base):
            rel_dir = os.path.relpath(dirpath, WS)
            if MATRIX_RUN.match(rel_dir):
                dirnames[:] = []  # matrix run dirs: top-level files only (logs/ and runs/ stay local)
            else:
                keep = []
                for d in sorted(dirnames):
                    if d.endswith('-bin'):
                        for fn in sorted(os.listdir(os.path.join(dirpath, d))):
                            if fn.upper().startswith('MANIFEST') and fn.lower().endswith('.txt'):
                                p = os.path.join(dirpath, d, fn)
                                inc.append((p, os.path.join(dst, os.path.relpath(p, base)), os.path.getsize(p)))
                        continue
                    if pruned(rel_dir, d):
                        exc.append((os.path.join(dirpath, d), 'dir-pruned', 0))
                        continue
                    keep.append(d)
                dirnames[:] = keep
            for fn in sorted(filenames):
                p = os.path.join(dirpath, fn)
                why, size = classify(p, os.path.relpath(p, WS), cap)
                if why:
                    exc.append((p, why, size))
                else:
                    inc.append((p, os.path.join(dst, os.path.relpath(p, base)), size))

    total = sum(s for _, _, s in inc)
    groups = {}
    for p, d, s in inc:
        parts = d.split(os.sep)
        key = os.sep.join(parts[:2]) if parts[0] in ('build', 'bench') else parts[0]
        n, b = groups.get(key, (0, 0))
        groups[key] = (n + 1, b + s)
    print(f'included {len(inc)} files, {total / 1e6:.1f} MB')
    for k in sorted(groups):
        print(f'  {k:<28} {groups[k][0]:>5} files {groups[k][1] / 1e6:>7.2f} MB')
    reasons = {}
    for p, why, s in exc:
        n, b = reasons.get(why, (0, 0))
        reasons[why] = (n + 1, b + s)
    print('excluded:', ', '.join(f'{k} {v[0]} ({v[1] / 1e6:.1f} MB)' for k, v in sorted(reasons.items())))
    exts = {}
    for p, d, s in inc:
        e = os.path.splitext(p)[1].lower()
        n, b = exts.get(e, (0, 0))
        exts[e] = (n + 1, b + s)
    print('by ext:', ', '.join(f'{k} {v[0]}/{v[1] / 1e6:.1f}MB' for k, v in sorted(exts.items(), key=lambda kv: -kv[1][1])))
    print('largest included:')
    for p, d, s in sorted(inc, key=lambda t: -t[2])[:20]:
        print(f'  {s / 1e3:>8.0f} KB  {d}')
    flagged = [(p, why) for p, why, _ in exc if why in ('secret?', 'disasm')]
    print(f'flagged ({len(flagged)}):')
    for p, why in flagged[:60]:
        print(f'  {why:<8} {os.path.relpath(p, WS)}')

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'EXCLUDED.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        for p, why, s in exc:
            f.write(f'{os.path.relpath(p, WS)}\t{why}\t{s}\n')
    if not copy:
        with open(os.path.join(OUT, 'INCLUDED-dryrun.tsv'), 'w', encoding='utf-8', newline='\n') as f:
            for p, d, s in inc:
                f.write(f'{os.path.relpath(p, WS)}\tperf/{d.replace(os.sep, "/")}\t{s}\n')
        return
    scrub = '--no-scrub' not in sys.argv
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    edited_files, edits = 0, 0
    with open(os.path.join(OUT, 'MANIFEST.tsv'), 'w', encoding='utf-8', newline='\n') as m:
        m.write('# dest under perf/\tsource under the workspace\tbytes (exported)\tsha256 (exported)\tpath/name edits\n')
        for p, d, s in inc:
            t = os.path.join(DEST, d)
            os.makedirs(os.path.dirname(t), exist_ok=True)
            shutil.copy2(p, t)
            n = scrub_file(t) if scrub else 0
            if n:
                edited_files, edits = edited_files + 1, edits + n
            h = hashlib.sha256(open(t, 'rb').read()).hexdigest().upper()
            m.write(f'{d.replace(os.sep, "/")}\t{os.path.relpath(p, WS).replace(os.sep, "/")}\t'
                    f'{os.path.getsize(t)}\t{h}\t{n}\n')
    here = os.path.dirname(os.path.abspath(__file__))
    shutil.copy2(os.path.join(here, 'README-perf.md'), os.path.join(DEST, 'README.md'))
    shutil.copy2(os.path.join(OUT, 'MANIFEST.tsv'), os.path.join(DEST, 'MANIFEST.tsv'))
    print(f'copied to {DEST}')
    if scrub:
        left = []
        for dirpath, _, filenames in os.walk(DEST):
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                txt = open(fp, 'rb').read().decode('utf-8', 'replace')
                if USER_RE.search(fn) or USER_RE.search(txt) or TRUNC_RE.search(txt):
                    left.append(os.path.relpath(fp, DEST))
        # The count includes cut-off profile paths (TRUNC_RE), not only the full account name.
        print(f'scrub: {edits} edits in {edited_files} files; files still holding the account name: {len(left)}')
        for x in left[:20]:
            print(f'  LEFT {x}')


if __name__ == '__main__':
    main()

"""Agent 2 - dev snapshot for dev OFF build 1 and the ON build (task #1).
Usage:  python build\\agent2\\snap.py <TAG>        (e.g. S0 = preliminary pre-build, S1 = the 20:15 cut-off)

Mirrors the live DimensionsRecomp tree into build/agent2/snap1/DimensionsRecomp as REAL copies (no junctions):
  rexglue-sdk (no out/, no .git), rexlego (no out/, no generated junction), thirdparty, tools, and the top-level
  files (VERSION etc.). research/ is not copied: its only use in rexlego/CMakeLists.txt is a dxc HINT, and we pass
  LEGO_HOST_DXC_EXECUTABLE explicitly.
The pinned 0.0.23.3 generated output is copied ONCE from baseline/ (not refreshed; it is not part of the batch).
The snapshot manifest's game_root is re-pointed for the deeper path.
Writes snap1/MANIFEST-<TAG>-<HHMM>.tsv (rel, size, live mtime_ns, sha256, snapshot mtime_ns) and
snap1/DIFF-<TAG>-<HHMM>.txt against the previous manifest. On a refresh, every file whose CONTENT changed is
copied and touched (mtime = now) so ninja rebuilds whatever depends on it, even if the live file's mtime went
backwards. Files deleted from the live tree are deleted from the snapshot. A snapshot file that no longer matches
its recorded size/mtime (something wrote into the snapshot) is re-copied, touched and reported.
"""
import os, sys, hashlib, shutil, time, re
from concurrent.futures import ThreadPoolExecutor

R = r'<workspace>'
LIVE = os.path.join(R, 'DimensionsRecomp')
SNAP_ROOT = os.path.join(R, 'build', 'agent2', 'snap1')
SNAP = os.path.join(SNAP_ROOT, 'DimensionsRecomp')
GEN_SRC = os.path.join(R, 'baseline', 'DimensionsRecomp', 'rexlego', 'generated')
GEN_DST = os.path.join(SNAP, 'rexlego', 'generated')
TOP_DIRS = ['rexglue-sdk', 'rexlego', 'thirdparty', 'tools']
EXCL_REL = {'rexglue-sdk/out', 'rexlego/out', 'rexlego/generated'}
EXCL_NAMES = {'.git', '__pycache__'}
MANIFEST_REL = 'rexlego/legodimensions_manifest.toml'
HEADERS_LIST = os.path.join(R, 'build', 'agent2', 'sdk-headers-dev.txt')
REPARSE = 0x400
THREADS = 8
SYMLINKED = []


LP = '\\\\?\\'   # long-path prefix: the snapshot paths are 19 characters deeper than the live ones


def live_path(rel):
    return LP + os.path.join(LIVE, rel.replace('/', os.sep))


def snap_path(rel):
    return LP + os.path.join(SNAP, rel.replace('/', os.sep))


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def walk_live():
    files, junctions = {}, []
    for e in os.scandir(LIVE):
        if e.is_file(follow_symlinks=False) and e.name not in EXCL_NAMES:
            st = e.stat(follow_symlinks=False)
            files[e.name] = (st.st_size, st.st_mtime_ns)
    for top in TOP_DIRS:
        stack = [top]
        while stack:
            rel = stack.pop()
            with os.scandir(live_path(rel)) as it:
                for e in it:
                    r = rel + '/' + e.name
                    if r in EXCL_REL:
                        continue
                    # .git DIRECTORIES are skipped; submodule .git FILES (gitdir pointers) are kept because
                    # thirdparty/CMakeLists.txt checks EXISTS <submodule>/.git
                    if e.name in EXCL_NAMES and e.is_dir(follow_symlinks=False):
                        continue
                    st = e.stat(follow_symlinks=False)
                    if getattr(st, 'st_file_attributes', 0) & REPARSE:
                        # File symlinks are copied by content (as robocopy, and as the baseline snapshot, did);
                        # directory links and dangling links are skipped and reported.
                        try:
                            if e.is_file():
                                tst = e.stat()
                                files[r] = (tst.st_size, tst.st_mtime_ns)
                                SYMLINKED.append(r)
                                continue
                        except OSError:
                            pass
                        junctions.append(r)
                        continue
                    if e.is_dir(follow_symlinks=False):
                        stack.append(r)
                    else:
                        files[r] = (st.st_size, st.st_mtime_ns)
    return files, junctions


def load_prev():
    if not os.path.isdir(SNAP_ROOT):
        return None, {}
    ms = [os.path.join(SNAP_ROOT, n) for n in os.listdir(SNAP_ROOT) if n.startswith('MANIFEST-') and n.endswith('.tsv')]
    if not ms:
        return None, {}
    p = max(ms, key=os.path.getmtime)
    prev = {}
    with open(p, encoding='utf-8') as f:
        for line in f:
            if line.startswith('#'):
                continue
            rel, size, mt, h, smt = line.rstrip('\n').split('\t')
            prev[rel] = (int(size), int(mt), h, int(smt))
    return p, prev


def closure_set():
    """The 'dev-sdk' group of sdk-headers-dev.txt: paths relative to rexglue-sdk/, one per indented line."""
    s, on = set(), False
    try:
        for line in open(HEADERS_LIST, encoding='utf-8'):
            if line.startswith('#'):
                on = line.startswith('# dev-sdk')
                continue
            if on and line.strip():
                s.add(('rexglue-sdk/' + line.strip().replace('\\', '/')).lower())
    except OSError:
        pass
    return s


def rewrite_game_root():
    """Re-point game_root (relative to the manifest's directory) so it resolves to the same place as live."""
    live_dir, snap_dir = os.path.join(LIVE, 'rexlego'), os.path.join(SNAP, 'rexlego')
    txt = open(snap_path(MANIFEST_REL), encoding='utf-8').read()
    m = re.search(r'^(\s*game_root\s*=\s*")([^"]+)(")', txt, re.M)
    if not m:
        return 'game_root not found'
    target = os.path.normpath(os.path.join(live_dir, m.group(2)))
    new = os.path.relpath(target, snap_dir).replace('\\', '/')
    txt = txt[:m.start(2)] + new + txt[m.end(2):]
    with open(snap_path(MANIFEST_REL), 'w', encoding='utf-8', newline='') as f:
        f.write(txt)
    return '%s -> %s (%s, exists=%s)' % (m.group(2), new, target, os.path.isdir(target))


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else 'S'
    t0 = time.time()
    stamp = time.strftime('%H%M')
    os.makedirs(SNAP, exist_ok=True)
    prev_path, prev = load_prev()
    first = not prev
    live, junctions = walk_live()
    t_walk = time.time() - t0

    # 1. which live files need hashing (new, or size/mtime differ from the previous manifest)
    cand = [r for r, (s, m) in live.items() if not (r in prev and prev[r][0] == s and prev[r][1] == m)]
    with ThreadPoolExecutor(THREADS) as ex:
        pre = dict(zip(cand, ex.map(lambda r: sha(live_path(r)), cand)))
    added = sorted(r for r in cand if r not in prev)
    changed = sorted(r for r in cand if r in prev and prev[r][2] != pre[r])
    touched_only = sorted(r for r in cand if r in prev and prev[r][2] == pre[r])  # mtime-only change: no copy
    removed = sorted(r for r in prev if r not in live)
    # 2. snapshot files that were modified or deleted behind our back
    tampered = []
    for r in live:
        if r in prev and r not in pre or r in touched_only:
            sp = snap_path(r)
            try:
                st = os.stat(sp)
                if st.st_size != prev[r][0] and r != MANIFEST_REL or st.st_mtime_ns != prev[r][3]:
                    tampered.append(r)
            except OSError:
                tampered.append(r)
    tampered.sort()
    copy_list = added + changed + tampered
    now = time.time()

    def do_copy(r):
        d = snap_path(r)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        if os.path.exists(d):
            os.chmod(d, 0o666)
        shutil.copy2(live_path(r), d)
        if r == MANIFEST_REL:
            do_copy.game_root = rewrite_game_root()
        if not first:
            os.utime(d, (now, now))
        return sha(d) if r != MANIFEST_REL else None
    do_copy.game_root = '(manifest unchanged)'
    with ThreadPoolExecutor(THREADS) as ex:
        post = dict(zip(copy_list, ex.map(do_copy, copy_list)))
    raced = sorted(r for r, h in post.items() if h is not None and r in pre and h != pre[r])
    for r in removed:
        try:
            os.remove(snap_path(r))
        except OSError:
            pass
    t_copy = time.time() - t0

    # 3. pinned generated output, copied once
    gen_note = 'kept (copied earlier)'
    if not os.path.isdir(os.path.join(GEN_DST, 'default')):
        gfiles = []
        for dp, dn, fn in os.walk(GEN_SRC):
            for n in fn:
                gfiles.append(os.path.relpath(os.path.join(dp, n), GEN_SRC))

        def gcopy(rel):
            d = os.path.join(GEN_DST, rel)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(os.path.join(GEN_SRC, rel), d)
            return os.path.getsize(d)
        with ThreadPoolExecutor(THREADS) as ex:
            tot = sum(ex.map(gcopy, gfiles))
        gen_note = 'copied %d files, %.1f MB from baseline' % (len(gfiles), tot / 1e6)
    t_gen = time.time() - t0

    # 4. manifest + diff
    rows = []
    for r in sorted(live):
        s, m = live[r]
        if r in post and post[r] is not None:
            h = post[r]
        elif r in pre:
            h = pre[r]
        else:
            h = prev[r][2]
        smt = os.stat(snap_path(r)).st_mtime_ns
        rows.append('%s\t%d\t%d\t%s\t%d' % (r, s, m, h, smt))
    mpath = os.path.join(SNAP_ROOT, 'MANIFEST-%s-%s.tsv' % (tag, stamp))
    with open(mpath, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# snapshot %s %s: %d files (rel, size, live mtime_ns, sha256, snapshot mtime_ns); generated/ not listed\n'
                % (tag, time.strftime('%Y-%m-%d %H:%M:%S'), len(rows)))
        f.write('\n'.join(rows) + '\n')
    mhash = sha(mpath)
    clo = closure_set()
    hit = sorted(r for r in added + changed + removed if r.lower() in clo)
    sdk_inc = sorted(r for r in added + changed + removed if r.startswith('rexglue-sdk/include/'))
    lines = [
        '# snapshot diff %s %s vs %s' % (tag, time.strftime('%H:%M:%S'), os.path.basename(prev_path) if prev_path else '(none: first copy)'),
        'files=%d added=%d changed=%d removed=%d mtime-only=%d snapshot-tampered=%d raced=%d file-symlinks-copied=%d dir-links-skipped=%d'
        % (len(live), len(added), len(changed), len(removed), len(touched_only), len(tampered), len(raced), len(SYMLINKED), len(junctions)),
        'closure headers loaded=%d; closure headers changed=%d; rexglue-sdk/include changed=%d' % (len(clo), len(hit), len(sdk_inc)),
        'game_root: %s' % do_copy.game_root,
        'generated: %s' % gen_note,
        'manifest: %s sha256=%s' % (os.path.basename(mpath), mhash),
        'wall: walk %.1fs, copy %.1fs, generated %.1fs, total %.1fs; longest snapshot path %d chars'
        % (t_walk, t_copy, t_gen, time.time() - t0, max(len(os.path.join(SNAP, r)) for r in live)),
    ]
    def section(name, lst, limit=400):
        if lst:
            lines.append('## %s (%d)' % (name, len(lst)))
            lines.extend('  ' + r for r in lst[:limit])
            if len(lst) > limit:
                lines.append('  ... %d more' % (len(lst) - limit))
    section('CLOSURE HEADERS CHANGED (all 440 generated TUs rebuild)', hit)
    section('junctions skipped', junctions)
    if not first:
        section('changed', changed)
        section('added', added)
        section('removed', removed)
        section('snapshot tampered (re-copied)', tampered)
        section('changed during copy', raced)
    dpath = os.path.join(SNAP_ROOT, 'DIFF-%s-%s.txt' % (tag, stamp))
    with open(dpath, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    print('\n'.join(lines[:7]))
    print('diff: ' + dpath)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# commit-check.py (Agent 2, board task #28): check that the committed perf/opt trees equal the snap4b source.
# Main check, for every tracked file (git ls-files; submodule gitlinks and generated/ skipped) of the live
# DimensionsRecomp and rexglue-sdk repos:
#   (1) the working-tree file == build/agent2/snap1/DimensionsRecomp/<same path>, byte for byte;
#   (2) the HEAD blob == that snap1 file, byte-identical or identical after CRLF -> LF (what core.autocrlf=true commits);
#   (3) the index blob == the HEAD blob.
#   Tracked files under a top-level directory that snap1 never copied (snap1 holds only the build inputs) are listed
#   as out of scope; they must exist, be unchanged by the S4b/S4c commits and be clean in git status.
# Also: the HEADs and their parents, the parent's rexglue-sdk gitlink, git status (tracked files only),
# assume-unchanged/skip-worktree bits, each commit's changed files (diff-tree HEAD^ HEAD) against the 16 rows of
# build/agent2/s4b/HASHES.txt, and each row's before sha256 (HEAD^ blob) and after sha256 (HEAD blob, live, snap1).
# Extended (informational, own verdict): files in snap1 that live git does not track (ignored or not), and the
# content of the submodules (live checkout vs the snap1 copy; plume/simde, which the task ignores, are compared for
# information only, without a verdict). --sub stat compares size and mtime and byte-compares only files whose mtime
# differs; --sub bytes byte-compares every file; --sub skip skips it.
# Read-only: git runs only with --no-optional-locks (rev-parse, config --get, ls-files, ls-tree, diff-tree, status,
# cat-file --batch, check-ignore).
#   python build/agent2/commit-check.py --out build/agent2/COMMIT-CHECK.md [--sub stat|bytes|skip]
import argparse, hashlib, os, subprocess, sys, time
from collections import Counter

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
HOLD = os.path.join(R, 'perf-notes', 'WINDOW-HOLD.txt')
SNAP = os.path.join(R, 'build', 'agent2', 'snap1', 'DimensionsRecomp')
# name, live repo, snap1 copy, expected HEAD, expected HEAD^, path prefix under DimensionsRecomp/
REPOS = [('DimensionsRecomp', os.path.join(R, 'DimensionsRecomp'), SNAP, 'b0bd3b4', '1bd322e', ''),
         ('rexglue-sdk', os.path.join(R, 'DimensionsRecomp', 'rexglue-sdk'), os.path.join(SNAP, 'rexglue-sdk'),
          '5350b1d', '3bb65bb', 'rexglue-sdk/')]
IGNORED_SUBMODULES = {('DimensionsRecomp', 'thirdparty/plume'), ('rexglue-sdk', 'thirdparty/simde')}


def run_git(repo, args, inp=None, ok=(0,)):
    p = subprocess.run(['git', '--no-optional-locks', '-C', repo] + list(args), input=inp, capture_output=True)
    if p.returncode not in ok:
        raise RuntimeError('git %s (in %s): exit %d: %s' % (' '.join(args[:2]), relp(repo), p.returncode,
                                                           p.stderr.decode('utf-8', 'replace').strip()[:300]))
    return p.stdout


def git(repo, *args, inp=None):
    return run_git(repo, args, inp=inp)


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def rd(p):
    try:
        with open(p, 'rb') as f:
            return f.read()
    except OSError:
        return None


def relp(p):
    return os.path.relpath(p, R).replace('\\', '/')


def crlf(b):
    return b.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')


def ls_index(repo):
    idx = {}
    for ent in git(repo, 'ls-files', '-s', '-z').split(b'\0'):
        if not ent:
            continue
        meta, path = ent.split(b'\t', 1)
        mode, blob, stage = meta.decode().split()
        idx[path.decode('utf-8')] = (mode, blob, stage)
    return idx


def ls_tree(repo, rev):
    tree = {}
    for ent in git(repo, 'ls-tree', '-r', '-z', rev).split(b'\0'):
        if not ent:
            continue
        meta, path = ent.split(b'\t', 1)
        mode, typ, blob = meta.decode().split()
        tree[path.decode('utf-8')] = (mode, typ, blob)
    return tree


def cat_blobs(repo, ids):
    ids = list(ids)
    if not ids:
        return {}
    out = git(repo, 'cat-file', '--batch', inp=''.join(i + '\n' for i in ids).encode())
    res, pos = {}, 0
    for i in ids:
        nl = out.index(b'\n', pos)
        head = out[pos:nl].split()
        if len(head) < 3 or head[1] != b'blob':
            raise RuntimeError('cat-file: unexpected header %r' % out[pos:nl])
        n = int(head[2])
        res[i] = out[nl + 1:nl + 1 + n]
        pos = nl + 1 + n + 1
    return res


def diff_tree(repo):
    toks = git(repo, 'diff-tree', '-r', '-z', '--name-status', 'HEAD^', 'HEAD').split(b'\0')
    out, i = [], 0
    while i + 1 < len(toks) and toks[i]:
        out.append((toks[i].decode(), toks[i + 1].decode('utf-8')))
        i += 2
    return out


def status_lines(repo):
    rows = []
    for x in git(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=no').split(b'\0'):
        s = x.decode('utf-8', 'replace')
        if len(s) > 3 and s[2] == ' ' and s[:2].strip():
            rows.append((s[:2], s[3:]))
    return rows


def check_ignored(repo, paths):
    if not paths:
        return set()
    out = run_git(repo, ['check-ignore', '--stdin', '-z'], inp=b''.join(p.encode('utf-8') + b'\0' for p in paths),
                  ok=(0, 1))
    return {x.decode('utf-8') for x in out.split(b'\0') if x}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--sub', choices=('stat', 'bytes', 'skip'), default='stat')
    a = ap.parse_args()
    if os.path.exists(HOLD):
        print('HOLD file exists: not starting')
        return 9
    t0 = time.time()
    me = rd(os.path.abspath(__file__))
    fails, ext = [], []
    heads, parents, idx_by, tree_by, ptree_by, changed_by = {}, {}, {}, {}, {}, {}
    repo_of = {n: (r, s, pre) for n, r, s, _, _, pre in REPOS}

    # the 16 S4b input rows: owner, relpath under DimensionsRecomp/, before, after, item
    rows16 = []
    with open(os.path.join(R, 'build', 'agent2', 's4b', 'HASHES.txt'), encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or '\t' not in line:
                continue
            c = line.rstrip('\r\n').split('\t')
            if len(c) >= 6:
                rows16.append((c[0], c[1], c[2].split()[0].upper(), c[3].split()[0].upper(), c[4]))

    def split_rel(rel):
        return ('rexglue-sdk', rel[len('rexglue-sdk/'):]) if rel.startswith('rexglue-sdk/') else ('DimensionsRecomp',
                                                                                                    rel)

    expected = {'DimensionsRecomp': {'rexglue-sdk': 'M'}, 'rexglue-sdk': {}}
    for owner, rel, before, after, item in rows16:
        n, p = split_rel(rel)
        expected[n][p] = 'A' if before == 'ABSENT' else 'M'

    summary, details, scope, gitlinks, status_rows, commit_md = [], [], [], [], [], []
    main_links = {}
    for name, repo, snap, want, want_parent, pre in REPOS:
        head = git(repo, 'rev-parse', 'HEAD').decode().strip()
        parent = git(repo, 'rev-parse', 'HEAD^').decode().strip()
        heads[name], parents[name] = head, parent
        if not head.startswith(want):
            fails.append('%s HEAD %s is not %s' % (name, head[:12], want))
        if not parent.startswith(want_parent):
            fails.append('%s HEAD^ %s is not %s' % (name, parent[:12], want_parent))
        autocrlf = subprocess.run(['git', '--no-optional-locks', '-C', repo, 'config', '--get', 'core.autocrlf'],
                                  capture_output=True).stdout.decode().strip() or '(unset)'
        idx = idx_by[name] = ls_index(repo)
        tree = tree_by[name] = ls_tree(repo, 'HEAD')
        ptree_by[name] = ls_tree(repo, 'HEAD^')
        flags = [ln for ln in git(repo, 'ls-files', '-v', '-z').split(b'\0') if ln and (ln[:1].islower() or
                                                                                         ln[:1] == b'S')]
        st_rows = status_lines(repo)
        # the commit's changed files vs the HASHES.txt rows (+ the parent's rexglue-sdk gitlink)
        changes = diff_tree(repo)
        changed = changed_by[name] = {p: s for s, p in changes}
        exp = expected[name]
        for p, s in sorted(exp.items()):
            if p not in changed:
                fails.append('%s commit %s does not change %s (expected %s)' % (name, head[:7], p, s))
            elif changed[p] != s:
                fails.append('%s commit %s: %s is %s, expected %s' % (name, head[:7], p, changed[p], s))
        extra = sorted(p for p in changed if p not in exp)
        commit_md.append('- %s: HEAD `%s`, HEAD^ `%s`. `diff-tree HEAD^ HEAD` changes %d path(s): %s.' % (
            name, head[:12], parent[:12], len(changes),
            ', '.join('%s `%s%s`' % (s, pre, p) for s, p in changes) or 'none'))
        commit_md.append('  - Expected from HASHES.txt%s: %d path(s); missing: %s; extra: %s.' % (
            ' (+ the rexglue-sdk gitlink)' if name == 'DimensionsRecomp' else '', len(exp),
            ', '.join('`%s`' % p for p in sorted(set(exp) - set(changed))) or 'none',
            ', '.join('`%s`' % p for p in extra) or 'none'))
        n_gl = n_gen = n_cmp = n_scope = n_wt = n_exact = n_crlf = n_idx = n_prob = 0
        files = []
        for path, (mode, blob, stage) in sorted(idx.items()):
            if mode == '160000':
                n_gl += 1
                gitlinks.append((name, path, blob, (name, path) in IGNORED_SUBMODULES))
                continue
            if path.startswith('generated/') or '/generated/' in path:
                n_gen += 1
                continue
            if mode == '120000':
                main_links[name] = main_links.get(name, 0) + 1
            files.append((path, blob))
        blobs = cat_blobs(repo, sorted({tree[p][2] for p, _ in files if p in tree}))
        for path, blob in files:
            live = rd(os.path.join(repo, path))
            ref = rd(os.path.join(snap, path))
            tb = tree.get(path)
            hb = blobs.get(tb[2]) if tb else None
            prob = []
            out_of_scope = (ref is None and '/' in path and
                            not os.path.isdir(os.path.join(snap, path.split('/', 1)[0])))
            if out_of_scope:
                n_scope += 1
                scope.append((name, pre + path))
                if live is None:
                    prob.append('missing in the working tree')
                if path in changed:
                    prob.append('changed by commit %s (%s) but snap1 has no copy' % (head[:7], changed[path]))
            else:
                n_cmp += 1
                if live is None:
                    prob.append('missing in the working tree')
                if ref is None:
                    prob.append('missing in snap1')
                if live is not None and ref is not None:
                    if live == ref:
                        n_wt += 1
                    else:
                        eol = live.replace(b'\r\n', b'\n') == ref.replace(b'\r\n', b'\n')
                        prob.append('working tree != snap1%s (live %s %d B, snap1 %s %d B)' % (
                            ' (line endings only)' if eol else '', sha(live)[:16], len(live), sha(ref)[:16],
                            len(ref)))
                if tb is None:
                    prob.append('not in HEAD (staged add?)')
                elif ref is not None:
                    if hb == ref:
                        n_exact += 1
                    elif hb == ref.replace(b'\r\n', b'\n'):
                        n_crlf += 1
                    else:
                        prob.append('HEAD blob != snap1 (blob %s %d B, snap1 %s %d B)' % (
                            sha(hb)[:16], len(hb), sha(ref)[:16], len(ref)))
            if tb is not None and tb[2] == blob:
                n_idx += 1
            elif tb is not None:
                prob.append('index blob %s != HEAD blob %s' % (blob[:12], tb[2][:12]))
            if prob:
                n_prob += 1
                details.append('- `%s%s`: %s' % (pre, path, '; '.join(prob)))
        for xy, p in st_rows:
            gl = idx.get(p, ('',))[0] == '160000'
            status_rows.append((name, xy, p, gl, (name, p) in IGNORED_SUBMODULES))
            if not gl:
                fails.append('%s: git status %r %s' % (name, xy, p))
        for ln in flags:
            fails.append('%s: assume-unchanged/skip-worktree bit: %s' % (name, ln.decode('utf-8', 'replace')))
        if n_prob:
            fails.append('%s: %d file(s) with differences' % (name, n_prob))
        summary.append('| %s | `%s` | %s | %d | %d | %d | %d | %d | %d / %d | %d (%d exact + %d via CRLF->LF) | %d / %d '
                       '| %d | %s |' % (name, head[:12], autocrlf, len(idx), n_gl, n_gen, n_scope, n_cmp, n_wt, n_cmp,
                                        n_exact + n_crlf, n_exact, n_crlf, n_idx, len(files), len(st_rows),
                                        'PASS' if not n_prob else 'FAIL'))
    # the parent's gitlink for rexglue-sdk must pin the SDK HEAD
    pin = [g for g in gitlinks if g[0] == 'DimensionsRecomp' and g[1] == 'rexglue-sdk']
    pin_ok = bool(pin) and pin[0][2] == heads['rexglue-sdk']
    if not pin_ok:
        fails.append('DimensionsRecomp gitlink rexglue-sdk %s != SDK HEAD %s' % (pin[0][2][:12] if pin else 'none',
                                                                                  heads['rexglue-sdk'][:12]))

    # the 16 rows: before == HEAD^ blob, after == HEAD blob == live == snap1 (a blob matches a sha256 as is or LF->CRLF)
    need_p, need_h = {}, {}
    for owner, rel, before, after, item in rows16:
        n, p = split_rel(rel)
        if p in ptree_by[n]:
            need_p.setdefault(n, set()).add(ptree_by[n][p][2])
        if p in tree_by[n]:
            need_h.setdefault(n, set()).add(tree_by[n][p][2])
    pblobs = {n: cat_blobs(repo_of[n][0], sorted(v)) for n, v in need_p.items()}
    hblobs = {n: cat_blobs(repo_of[n][0], sorted(v)) for n, v in need_h.items()}

    def blob_is(b, want):
        return b is not None and want in (sha(b), sha(crlf(b)))

    rows_md, n16 = [], 0
    for owner, rel, before, after, item in rows16:
        n, p = split_rel(rel)
        pb = pblobs.get(n, {}).get(ptree_by[n][p][2]) if p in ptree_by[n] else None
        hb = hblobs.get(n, {}).get(tree_by[n][p][2]) if p in tree_by[n] else None
        lv = rd(os.path.join(R, 'DimensionsRecomp', rel))
        sv = rd(os.path.join(SNAP, rel))
        ok_b = (pb is None and p not in ptree_by[n]) if before == 'ABSENT' else blob_is(pb, before)
        ok_h = blob_is(hb, after)
        ok_l = lv is not None and sha(lv) == after
        ok_s = sv is not None and sha(sv) == after
        ok = ok_b and ok_h and ok_l and ok_s
        n16 += ok
        if not ok:
            fails.append('HASHES.txt row %s: before(HEAD^) %s, HEAD %s, live %s, snap1 %s' % (
                rel, 'ok' if ok_b else 'BAD', 'ok' if ok_h else 'BAD', 'ok' if ok_l else 'BAD', 'ok' if ok_s else 'BAD'))
        rows_md.append('| %s | `%s` | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            owner, rel, item, before[:16], 'absent' if before == 'ABSENT' and ok_b else ('==' if ok_b else 'DIFFERS'),
            after[:16], '==' if ok_h else 'DIFFERS', '==' if ok_l else 'DIFFERS', '==' if ok_s else 'DIFFERS',
            'PASS' if ok else 'FAIL'))

    # extended 1: files in snap1 that live git does not track
    tracked, prune_gl = set(), set()
    for name, repo, snap, want, want_parent, pre in REPOS:
        for p, (mode, blob, stage) in idx_by[name].items():
            if mode != '160000':
                tracked.add(pre + p)
            elif not (name == 'DimensionsRecomp' and p == 'rexglue-sdk'):
                prune_gl.add(pre + p)
    untracked, pruned = [], Counter()
    for dp, dns, fns in os.walk(SNAP):
        rdp = os.path.relpath(dp, SNAP).replace('\\', '/')
        rdp = '' if rdp == '.' else rdp + '/'
        keep = []
        for d in dns:
            if d == '.git':
                pruned['.git/'] += 1
            elif d == 'generated':
                pruned['generated/'] += 1
            elif rdp + d in prune_gl:
                pruned['submodule checkouts'] += 1
            else:
                keep.append(d)
        dns[:] = keep
        for fn in fns:
            if fn != '.git' and rdp + fn not in tracked:
                untracked.append(rdp + fn)
    sdk_u = [p[len('rexglue-sdk/'):] for p in untracked if p.startswith('rexglue-sdk/')]
    par_u = [p for p in untracked if not p.startswith('rexglue-sdk/')]
    ignored = ({'rexglue-sdk/' + p for p in check_ignored(repo_of['rexglue-sdk'][0], sdk_u)} |
               check_ignored(repo_of['DimensionsRecomp'][0], par_u))
    not_ign = sorted(p for p in untracked if p not in ignored)
    ign_dirs = Counter('/'.join(p.split('/')[:2]) if p.count('/') >= 2 else p.rsplit('/', 1)[0] if '/' in p else '.'
                       for p in untracked if p in ignored)
    if not_ign:
        ext.append('%d file(s) in snap1 are neither tracked nor ignored by live git' % len(not_ign))

    # extended 2: submodules (gitlinks); content compare for all but plume/simde
    sub_md, ext_notes = [], []
    sub_notes = {}
    for name, path, blob, ign in gitlinks:
        if name == 'DimensionsRecomp' and path == 'rexglue-sdk':
            continue
        repo, snaproot, pre = repo_of[name]
        live_sub, snap_sub = os.path.join(repo, path), os.path.join(snaproot, path)
        label = '%s:`%s`' % (name, path)
        if not os.path.exists(os.path.join(live_sub, '.git')):
            live_n = len(os.listdir(live_sub)) if os.path.isdir(live_sub) else -1
            snap_n = len(os.listdir(snap_sub)) if os.path.isdir(snap_sub) else -1
            sub_md.append('| %s | %s | not checked out in live (%s) | | snap1: %s | | | | %s |' % (
                label, blob[:12], 'empty directory' if live_n == 0 else 'absent' if live_n < 0 else
                '%d entries, no .git' % live_n, 'empty directory' if snap_n == 0 else 'absent' if snap_n < 0 else
                '%d entries' % snap_n, 'n/a' if snap_n <= 0 else 'WARN'))
            if snap_n > 0:
                ext.append('%s is not checked out in live, but snap1 has %d entries there' % (label, snap_n))
            continue
        shead = git(live_sub, 'rev-parse', 'HEAD').decode().strip()
        sst = status_lines(live_sub)
        sub_notes[(name, path)] = (shead == blob, sst)
        info = ign  # plume/simde: ignored per the task, so compared for information only (no verdict)
        hd = 'HEAD == gitlink' if shead == blob else 'HEAD %s' % shead[:12]
        bad = (shead != blob or bool(sst)) and not info
        if not os.path.isdir(snap_sub):
            sub_md.append('| %s | %s | %s | %d | snap1 has no copy | | | | %s |' % (
                label, blob[:12], hd, len(sst), 'ignored (info)' if info else 'WARN' if bad else 'n/a'))
            if bad:
                ext.append('%s: live checkout HEAD %s / %d tracked change(s)' % (label, shead[:12], len(sst)))
            continue
        nf = n_stat = n_bytes = n_diff = n_nest = 0
        nb, diffs = 0, []
        links = Counter()
        if a.sub != 'skip':
            for p, (mode, b, stg) in ls_index(live_sub).items():
                if mode == '160000':
                    n_nest += 1
                    continue
                nf += 1
                lp, sp = os.path.join(live_sub, p), os.path.join(snap_sub, p)
                if mode == '120000' and os.path.islink(lp):
                    # a real symlink in live (core.symlinks=true): compare link to link; a copy tool may instead have
                    # written the target's content as a plain file, or skipped the link
                    if os.path.islink(sp):
                        if os.readlink(sp) == os.readlink(lp):
                            links['same link'] += 1
                        else:
                            n_diff += 1
                            diffs.append('`%s` symlink target differs' % p)
                    elif not os.path.lexists(sp):
                        links['absent in snap1'] += 1
                    elif os.path.isfile(sp) and os.path.isfile(lp) and rd(sp) == rd(lp):
                        links['plain file with the target content in snap1'] += 1
                    else:
                        n_diff += 1
                        diffs.append('`%s` symlink in live, other content in snap1' % p)
                    continue
                try:
                    ls = os.stat(lp)
                except OSError:
                    ls = None
                try:
                    ss = os.stat(sp)
                except OSError:
                    ss = None
                if ls is None or ss is None:
                    n_diff += 1
                    diffs.append('`%s` missing in %s' % (p, 'live' if ls is None else 'snap1'))
                    continue
                nb += ls.st_size
                if ls.st_size != ss.st_size:
                    n_diff += 1
                    diffs.append('`%s` size %d vs snap1 %d' % (p, ls.st_size, ss.st_size))
                elif a.sub == 'stat' and abs(ls.st_mtime - ss.st_mtime) < 2.0:
                    n_stat += 1
                elif rd(lp) == rd(sp):
                    n_bytes += 1
                else:
                    n_diff += 1
                    diffs.append('`%s` content differs' % p)
        link_odd = links['absent in snap1'] + links['plain file with the target content in snap1']
        link_txt = ''
        if links:
            link_txt = ', %d symlink entries: %s' % (sum(links.values()), ', '.join(
                '%d %s' % (v, k) for k, v in sorted(links.items())))
        if info:
            ext_notes.append('%s, ignored per the task (compared for information only): %s (gitlink %s); %d tracked '
                             'change(s) in the live checkout%s; live vs snap1: %d of %d entries differ%s.' % (
                                 label, hd, blob[:12], len(sst),
                                 (' (%s)' % ', '.join('`%s` `%s`' % (x, q) for x, q in sst)) if sst else '',
                                 n_diff, nf, (' (%s)' % '; '.join(diffs[:5])) if diffs else ''))
        else:
            bad = bad or n_diff > 0
            if bad:
                ext.append('%s: HEAD %s, %d tracked change(s), %d file(s) differ from snap1%s' % (
                    label, 'ok' if shead == blob else shead[:12], len(sst), n_diff,
                    (': ' + '; '.join(diffs[:5])) if diffs else ''))
            if link_odd:
                ext_notes.append('%s has %d symlink entries (git mode 120000; real symlinks in live, core.symlinks=true): '
                                 '%s. The snap1 copy did not reproduce symlinks%s.' % (
                                     label, sum(links.values()),
                                     ', '.join('%d %s' % (v, k) for k, v in sorted(links.items())),
                                     '; no regular file differs' if not n_diff else ''))
        sub_md.append('| %s | %s | %s | %d | %s | %d | %d | %d | %s |' % (
            label, blob[:12], hd, len(sst),
            '%d entries, %.1f MB%s%s' % (nf, nb / 1048576.0, ', %d nested gitlinks skipped' % n_nest if n_nest else '',
                                        link_txt)
            if a.sub != 'skip' else 'skipped', n_stat, n_bytes, n_diff,
            'ignored (info)' if info else 'WARN' if bad else 'PASS (note)' if link_odd else 'PASS'))

    # ---- report
    res = 'PASS' if not fails else 'FAIL (%d)' % len(fails)
    eres = 'PASS' if not ext else 'WARN (%d)' % len(ext)
    md = []
    md.append('# COMMIT-CHECK: committed perf/opt trees vs the snap4b source (Agent 2, task #28)')
    md.append('')
    md.append('- Written %s by `build/agent2/commit-check.py` (sha256 %s, `--sub %s`), read-only: git only with '
              '`--no-optional-locks` (rev-parse, config --get, ls-files, ls-tree, diff-tree, status, cat-file --batch, '
              'check-ignore).' % (time.strftime('%Y-%m-%d %H:%M:%S'), sha(me)[:16], a.sub))
    md.append('- Reference: `build/agent2/snap1/DimensionsRecomp`, the S4b + S4c source with C1 v3 that devoff4b-bin '
              'and native4b-bin were built from. Live: `DimensionsRecomp` and `DimensionsRecomp/rexglue-sdk`.')
    md.append('- Per tracked file (`git ls-files`; submodule gitlinks and `generated/` skipped): (1) working tree == '
              'snap1, byte for byte; (2) HEAD blob == snap1 file (byte-identical, or after CRLF -> LF, which is what '
              '`core.autocrlf=true` commits); (3) index blob == HEAD blob.')
    md.append('- snap1 copied only the build inputs (top level: %s). Tracked files under top-level directories it never '
              'copied are out of scope: they must exist, be untouched by the S4b/S4c commits and be clean in git '
              'status.' % ', '.join('`%s`' % x for x in sorted(os.listdir(SNAP)) if x != '.git'))
    md.append('')
    md.append('**RESULT: %s** (main check). Extended checks: %s.' % (res, eres))
    md.append('')
    md.append('## Result per repo')
    md.append('')
    md.append('| repo | HEAD | core.autocrlf | ls-files entries | gitlinks skipped | generated/ skipped | out of scope '
              '(not in snap1) | files compared | working tree == snap1 | HEAD blob == snap1 | index == HEAD | git status '
              'lines (tracked) | result |')
    md.append('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    md.extend(summary)
    md.append('')
    md.append('- DimensionsRecomp pins rexglue-sdk at `%s` (gitlink) %s the SDK HEAD `%s`: %s.' % (
        pin[0][2][:12] if pin else 'none', '==' if pin_ok else '!=', heads['rexglue-sdk'][:12],
        'PASS' if pin_ok else 'FAIL'))
    md.append('- Symlink entries (git mode 120000) among the compared files: %s.' % (
        ', '.join('%s %d' % (n, main_links.get(n, 0)) for n, *_ in REPOS)))
    md.append('')
    md.append('## Differences (files in snap1 scope)')
    md.append('')
    md.extend(details or ['None: every compared file is identical in the working tree, HEAD and snap1.'])
    md.append('')
    md.append('## The S4b/S4c commits (`git diff-tree -r HEAD^ HEAD`)')
    md.append('')
    md.extend(commit_md)
    md.append('')
    md.append('## The 16 S4b input files (build/agent2/s4b/HASHES.txt, copied into live and committed at 05:40)')
    md.append('')
    md.append('A blob matches a sha256 as stored or after LF -> CRLF (the working-tree form under core.autocrlf=true).')
    md.append('')
    md.append('| owner | path under DimensionsRecomp/ | item | before sha256 | HEAD^ blob | after sha256 | HEAD blob | live '
              '| snap1 | result |')
    md.append('|---|---|---|---|---|---|---|---|---|---|')
    md.extend(rows_md)
    md.append('')
    md.append('%d of %d rows PASS.' % (n16, len(rows16)))
    md.append('')
    md.append('## Out of scope: tracked files under top-level directories snap1 never copied')
    md.append('')
    sc = Counter((n, p.split('/', 1)[0] if n == 'DimensionsRecomp' else '/'.join(p.split('/', 2)[:2]))
                 for n, p in scope)
    if sc:
        md.append('%d file(s), all present in the working tree, none changed by the S4b/S4c commits (see above), and '
                  'git status shows no tracked-file change: %s.' % (
                      len(scope), ', '.join('`%s/` %d' % (d, k) for (n, d), k in sorted(sc.items()))))
    else:
        md.append('None.')
    md.append('')
    md.append('## git status (tracked files only, `--untracked-files=no`)')
    md.append('')
    if status_rows:
        sdk_st = [r for r in status_rows if r[0] == 'rexglue-sdk']
        for name, xy, p, gl, ign in status_rows:
            if not gl:
                md.append('- %s: `%s` `%s` (TRACKED FILE)' % (name, xy, p))
            elif ign:
                hn = sub_notes.get((name, p))
                md.append('- %s: `%s` `%s`: submodule, ignored per the task%s.' % (
                    name, xy, p, '' if hn is None else ' (its HEAD %s the gitlink; %d tracked change(s) inside it)' % (
                        '==' if hn[0] else '!=', len(hn[1]))))
            elif name == 'DimensionsRecomp' and p == 'rexglue-sdk':
                md.append('- %s: `%s` `%s`: the SDK HEAD %s the gitlink, so this is "modified content" inside the SDK. '
                          'The SDK\'s own tracked status is %s. Porcelain v1 shows a submodule as ` M` for new commits, '
                          'modified content or (recursively) a dirty nested submodule.' % (
                              name, xy, p, '==' if pin_ok else '!=',
                              ', '.join('`%s` `%s`%s' % (x, q, ' (ignored per the task)' if i2 else '')
                                        for _, x, q, _, i2 in sdk_st) or 'clean'))
            else:
                hn = sub_notes.get((name, p))
                md.append('- %s: `%s` `%s`: submodule%s.' % (name, xy, p, '' if hn is None else
                                                             ' (HEAD %s gitlink; %d tracked change(s))' % (
                                                                 '==' if hn[0] else '!=', len(hn[1]))))
    else:
        md.append('- clean')
    md.append('')
    md.append('## Extended: submodules (live checkout vs the snap1 copy; plume/simde for information only)')
    md.append('')
    md.append('`--sub stat`: equal size and mtime (within 2 s) counts as same by stat; equal size with a different mtime '
              'is byte-compared. `--sub bytes` byte-compares every file.')
    md.append('')
    md.append('| submodule | gitlink | live HEAD | tracked changes | files | same (stat) | same (bytes) | differ | '
              'result |')
    md.append('|---|---|---|---|---|---|---|---|---|')
    md.extend(sub_md)
    md.append('')
    for x in ext_notes:
        md.append('- Note: ' + x)
    md.append('- Not checked out in live: %s. snap1 has no content there either (see the rows), so the S4b/S4c '
              'builds from snap1 did not use them.' % (', '.join(r.split(' | ')[0].lstrip('| ') for r in sub_md
                                                                 if 'not checked out in live' in r) or 'none'))
    md.append('')
    md.append('## Extended: files in snap1 that live git does not track')
    md.append('')
    md.append('Walk of snap1 (pruned: %s). %d file(s) are not tracked; %d of them are ignored by live `.gitignore` '
              'rules%s.' % (', '.join('%s %d' % (k, v) for k, v in sorted(pruned.items())) or 'nothing',
                            len(untracked), len(untracked) - len(not_ign),
                            (' (by directory: %s)' % ', '.join('`%s` %d' % (d, k) for d, k in ign_dirs.most_common(20)))
                            if ign_dirs else ''))
    md.append('')
    if not_ign:
        md.append('Neither tracked nor ignored (%d):' % len(not_ign))
        md.append('')
        for p in not_ign[:150]:
            b = rd(os.path.join(SNAP, p))
            md.append('- `%s` (%s B, %s)' % (p, len(b) if b is not None else '?', sha(b)[:16] if b is not None else '?'))
        if len(not_ign) > 150:
            md.append('- ... %d more' % (len(not_ign) - 150))
    else:
        md.append('None are neither tracked nor ignored.')
    md.append('')
    if fails:
        md.append('## Failures (main check)')
        md.append('')
        md.extend('- ' + x for x in fails)
        md.append('')
    if ext:
        md.append('## Warnings (extended checks)')
        md.append('')
        md.extend('- ' + x for x in ext)
        md.append('')
    md.append('RESULT: %s; EXTENDED: %s  (%.1f s)' % (res, eres, time.time() - t0))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(md) + '\n')
    print('\n'.join(summary))
    print('\n'.join(commit_md))
    print('16 rows: %d of %d PASS; out of scope: %d; snap1 untracked: %d (not ignored %d)' % (
        n16, len(rows16), len(scope), len(untracked), len(not_ign)))
    print('\n'.join(sub_md))
    print('\n'.join(fails[:40]))
    print('\n'.join(ext[:40]))
    print('RESULT: %s; EXTENDED: %s  (%.1f s) -> %s' % (res, eres, time.time() - t0, relp(os.path.abspath(a.out))))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())

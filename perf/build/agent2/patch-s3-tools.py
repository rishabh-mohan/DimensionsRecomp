"""Agent 2 - S3 tool edits, applied by exact search/replace (each search text must occur exactly once).
  python build\\agent2\\patch-s3-tools.py snap-patch   snap-patch.py: --note=TEXT / --note-file=F for plan and apply
                                                    (Agent 1, 02:22: record the S3 build inputs in PATCHES/STATE-S3)
  python build\\agent2\\patch-s3-tools.py stage        stage-snap-bin.ps1: S<N> lists the PATCHES rows of S1..S<N>, so
                                                    S3's MANIFEST and freshness checks also cover S2's rows. Run only
                                                    after devoffB-bin is staged (build B runs this script).
Backs the file up to <file>.pre-S3 first (refuses if that backup exists) and writes S3-diffs/<file>.S3.diff.
"""
import difflib
import hashlib
import os
import sys

A = os.path.dirname(os.path.abspath(__file__))

SNAP_PATCH = [
    ("What apply does for every selected file whose live content differs from snap1:\n",
     "Options of plan and apply: --note=TEXT (repeatable) and --note-file=F (one note per non-empty line). Each note is\n"
     "written as a '# note: ...' line into PLAN-* and DIFF-*, and appended as '; note: ...' to the one '#' header line\n"
     "of PATCHES-<TAG>.tsv (when apply creates it) and of STATE-<TAG>-*.tsv, so both keep a single header line (S3: Agent\n"
     "1 asked for the S3 build inputs to be recorded there). Notes must not contain tabs.\n"
     "\n"
     "What apply does for every selected file whose live content differs from snap1:\n"),
    (r"""def cmd_plan(tag, rules_path):
    P = make_plan(tag, rules_path)
    out = os.path.join(S.SNAP_ROOT, 'PLAN-%s-%s.txt' % (tag, P['stamp']))
""",
     r"""def add_notes(P, notes):
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
"""),
    (r"""def cmd_apply(tag, rules_path, allow_delete):
    t0 = time.time()
    P = make_plan(tag, rules_path, allow_delete)
    stamp = P['stamp']
""",
     r"""def cmd_apply(tag, rules_path, allow_delete, notes=()):
    t0 = time.time()
    P = make_plan(tag, rules_path, allow_delete)
    add_notes(P, notes)
    stamp = P['stamp']
"""),
    (r"""    if not os.path.exists(pt):
        with open(pt, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# patches applied to build/agent2/snap1 for %s by snap-patch.py (relpath under DimensionsRecomp/, '
                    'sha256 before, sha256 after, source, time, note)\n' % tag)
""",
     r"""    if not os.path.exists(pt):
        with open(pt, 'w', encoding='utf-8', newline='\n') as f:
            f.write(patches_header(tag, notes))
    elif notes:
        with open(pt, encoding='utf-8-sig') as f:
            head = f.readline()
        if note_suffix(notes) not in head:
            print('WARNING: %s exists and its header line lacks the --note text; left as is' % pt)
"""),
    (r"""        f.write('# snap1 state after snap-patch %s apply %s: %d files (rel, live size, live mtime_ns, live sha256, '
                'snap1 size, snap1 mtime_ns, snap1 sha256, origin); generated/ not listed\n'
                % (tag, time.strftime('%Y-%m-%d %H:%M:%S'), len(rows)))
""",
     r"""        f.write(state_header(tag, len(rows), notes))
"""),
    (r"""        lines.append('  NOTE: live %s changed again after its copy; S2 holds the planned version' % rel)
""",
     r"""        lines.append('  NOTE: live %s changed again after its copy; %s holds the planned version' % (rel, tag))
"""),
    (r"""    print('\n'.join(P['text'][:4]))
""",
     r"""    print('\n'.join(P['text'][:4 + len(notes)]))
"""),
    (r"""        rp = os.path.abspath(argv[3])
        if cmd == 'plan':
            return cmd_plan(tag, rp)
        return cmd_apply(tag, rp, '--allow-delete' in argv[4:])
""",
     r"""        rp = os.path.abspath(argv[3])
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
"""),
]

STAGE = [
    ("newest STATE-S<N>-*.tsv written by snap-patch.py apply (+ PATCHES-S1.tsv and PATCHES-S<N>.tsv)",
     "newest STATE-S<N>-*.tsv written by snap-patch.py apply (+ PATCHES-S1.tsv ... PATCHES-S<N>.tsv)"),
    (r"""# patches applied to snap1 since S1 (S1's rows, then this tag's)
$patchFiles = @(@('S1', $SnapTag) | Select-Object -Unique | ForEach-Object { "$A\snap1\PATCHES-$_.tsv" } | Where-Object { Test-Path $_ })
""",
     r"""# patches applied to snap1 since S1: S<N> (N >= 2) lists the rows of every tag S1..S<N> (S3 = S1 + S2 + S3, so S2's
# rows stay in S3's MANIFEST and freshness checks); any other tag lists S1's rows, then its own
$patchTags = $(if ($SnapN -ge 2) { @(1..$SnapN | ForEach-Object { "S$_" }) } else { @('S1', $SnapTag) })
$patchFiles = @($patchTags | Select-Object -Unique | ForEach-Object { "$A\snap1\PATCHES-$_.tsv" } | Where-Object { Test-Path $_ })
"""),
]

TARGETS = {'snap-patch': ('snap-patch.py', SNAP_PATCH), 'stage': ('stage-snap-bin.ps1', STAGE)}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in TARGETS:
        raise SystemExit(__doc__)
    name, edits = TARGETS[sys.argv[1]]
    path = os.path.join(A, name)
    backup = path + '.pre-S3'
    if os.path.exists(backup):
        raise SystemExit('%s exists: already patched? nothing written' % backup)
    raw = open(path, 'rb').read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    body = raw[3:] if bom else raw
    crlf = b'\r\n' in body
    if crlf and body.count(b'\r\n') != body.count(b'\n'):
        raise SystemExit('%s has mixed line endings; nothing written' % name)
    old = body.decode('utf-8').replace('\r\n', '\n')
    new = old
    for i, (s, r) in enumerate(edits):
        n = new.count(s)
        if n != 1:
            raise SystemExit('edit %d: search text found %d times in %s (want 1); nothing written' % (i, n, name))
        new = new.replace(s, r)
    out = new.replace('\n', '\r\n') if crlf else new
    out = (b'\xef\xbb\xbf' if bom else b'') + out.encode('utf-8')
    with open(backup, 'wb') as f:
        f.write(raw)
    if open(backup, 'rb').read() != raw:
        raise SystemExit('backup readback mismatch; %s left unchanged' % name)
    tmp = path + '.new'
    with open(tmp, 'wb') as f:
        f.write(out)
    os.replace(tmp, path)
    ddir = os.path.join(A, 'S3-diffs')
    os.makedirs(ddir, exist_ok=True)
    diff = ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), name + '.pre-S3', name, n=2))
    dpath = os.path.join(ddir, name + '.S3.diff')
    with open(dpath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(diff)
    sha = lambda b: hashlib.sha256(b).hexdigest().upper()[:16]
    print('patched %s: %d edits | %s -> %s | backup %s | diff %s (%d B, sha256 %s) | %s, %s' % (
        name, len(edits), sha(raw), sha(open(path, 'rb').read()), os.path.basename(backup), dpath, os.path.getsize(dpath),
        sha(open(dpath, 'rb').read()), 'CRLF' if crlf else 'LF', 'BOM' if bom else 'no BOM'))


if __name__ == '__main__':
    main()

"""Agent 2 - checks for the S3 snap-patch.py edits (no snapshot I/O): header helpers, note parsing, option errors.
Run: python build\\agent2\\s3-tools-test.py
"""
import importlib.util
import os
import re
import sys

A = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('snap_patch', os.path.join(A, 'snap-patch.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
fails = []


def check(ok, what):
    print('%s %s' % ('PASS' if ok else 'FAIL', what))
    if not ok:
        fails.append(what)


old_patches = ('# patches applied to build/agent2/snap1 for S3 by snap-patch.py (relpath under DimensionsRecomp/, '
               'sha256 before, sha256 after, source, time, note)\n')
check(m.patches_header('S3') == old_patches, 'patches_header without notes == the old header line')
h = m.patches_header('S3', ['a b', 'c'])
check(h == old_patches[:-1] + '; note: a b; note: c\n', 'patches_header with 2 notes: one line, notes appended')
s = m.state_header('S3', 123)
check(re.fullmatch(r'# snap1 state after snap-patch S3 apply \d{4}-\d\d-\d\d \d\d:\d\d:\d\d: 123 files \(rel, live size, '
                   r'live mtime_ns, live sha256, snap1 size, snap1 mtime_ns, snap1 sha256, origin\); generated/ not '
                   r'listed\n', s) is not None, 'state_header without notes == the old header format')
s2 = m.state_header('S3', 5, ['x'])
check(s2.endswith('generated/ not listed; note: x\n') and s2.count('\n') == 1, 'state_header with a note: one line')
P = {'text': ['h1', 'h2', 'l3', 'l4']}
m.add_notes(P, ['n1', 'n2'])
check(P['text'] == ['h1', 'h2', '# note: n1', '# note: n2', 'l3', 'l4'], 'add_notes inserts after the 2 header lines')
P = {'text': ['h1', 'h2', 'l3']}
m.add_notes(P, [])
check(P['text'] == ['h1', 'h2', 'l3'], 'add_notes with no notes changes nothing')
# readers skip the header line with notes
tmp = os.path.join(A, 's3-tools-test.tmp.tsv')
with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
    f.write(h + 'rel/a.cpp\tAAA\tBBB\tsrc\t2026-11-22 03:00:00\tS3 A6: cat; rule x (y); backup z\n')
rows = m.load_tsv_rows(tmp)
os.remove(tmp)
check(rows == [['rel/a.cpp', 'AAA', 'BBB', 'src', '2026-11-22 03:00:00', 'S3 A6: cat; rule x (y); backup z']],
      'load_tsv_rows skips the noted header line')


def exits(argv, want):
    try:
        m.main(argv)
    except SystemExit as e:
        return want in str(e)
    return False


check(exits(['snap-patch.py', 'plan', 'S3', 'r.txt', '--bogus'], 'unknown option(s): --bogus'), 'unknown option refused')
check(exits(['snap-patch.py', 'apply', 'S3', 'r.txt', '--note=a\tb'], 'must not contain a tab'), 'tab in a note refused')
check(exits(['snap-patch.py', 'apply', 'S1', 'r.txt'], 'not S1'), 'S1 still refused')
notes_file = os.path.join(A, 'S3-notes.txt')
lines = [x.strip() for x in open(notes_file, encoding='utf-8-sig').read().splitlines() if x.strip()]
check(len(lines) == 3 and all('\t' not in x for x in lines) and all(ord(c) < 128 for x in lines for c in x),
      'S3-notes.txt: 3 notes, ASCII, no tabs')
check('001336f' in lines[0] and 'c5fe668' in lines[0] and 'plume' in lines[0] and 'simde' in lines[0],
      'S3-notes.txt line 1 names both commits and the plume/simde edits')
print('RESULT: %s' % ('PASS' if not fails else 'FAIL (%d)' % len(fails)))
sys.exit(1 if fails else 0)

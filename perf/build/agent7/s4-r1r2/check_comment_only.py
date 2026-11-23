# check_comment_only.py (Agent 7, task #9): proves that a re-staged file differs from the copy the syntax check
# compiled only in whole-line // comments, with the same line count (so no token and no __LINE__ value changes).
# Usage: python -B build\agent7\s4-r1r2\check_comment_only.py <old file> <new file>
# Exit 0 = comment-only; 1 = a code line changed, the line count changed or a changed comment ends in a backslash.
import difflib
import sys


def lines(path):
    data = open(path, 'rb').read()
    if b'\r' in data:
        print('CR bytes in %s' % path)
        sys.exit(1)
    return data.decode('utf-8').split('\n')


old, new = lines(sys.argv[1]), lines(sys.argv[2])
bad = 0
changed = 0
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
    if tag == 'equal':
        continue
    for side, seg, start in (('old', old[i1:i2], i1), ('new', new[j1:j2], j1)):
        for k, line in enumerate(seg):
            changed += 1
            s = line.strip()
            ok = s.startswith('//') and not s.endswith('\\')
            print('%s L%d %s %s' % (side, start + k + 1, 'comment' if ok else 'NOT A PLAIN COMMENT', line))
            if not ok:
                bad += 1
if len(old) != len(new):
    print('line count differs: %d vs %d' % (len(old), len(new)))
    bad += 1
print('changed lines: %d; line count %d vs %d' % (changed, len(old), len(new)))
print('RESULT: %s' % ('COMMENT-ONLY' if not bad and changed else ('IDENTICAL' if not bad else 'CODE CHANGED')))
sys.exit(1 if bad else 0)

# Dump full lines (by number, plus table rows by item id) from S4-DRAFT and FINDINGS for pass B.
import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
def load(p):
    return re.split(r'\r\n|\n|\r', open(p, 'rb').read().decode('utf-8'))
S4 = load('perf-notes/S4-DRAFT.md')
FN = load('perf-notes/FINDINGS-AND-CHANGES.md')
s4_nums = [7, 12, 13, 16, 20, 21, 23, 25, 26, 163, 165, 166, 200, 412, 414, 416, 418, 421, 489, 491, 492, 493, 494, 495, 496, 504, 561]
fn_nums = [1, 6, 15, 16, 25, 34, 329, 402]
which = sys.argv[1]
if which == 'S4':
    rows = [i for i, l in enumerate(S4, 1) if re.match(r'\| (19|21|33|34) \|', l)]
    for i in sorted(set(s4_nums + rows)):
        print(f'@@ S4 L{i} [{len(S4[i-1])}]\n{S4[i-1]}\n')
else:
    for i in fn_nums:
        print(f'@@ FN L{i} [{len(FN[i-1])}]\n{FN[i-1]}\n')

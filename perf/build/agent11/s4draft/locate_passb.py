# Pass-B locator: headings + pattern hits (line, length, snippet) for S4-DRAFT and FINDINGS.
import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
FILES = {'S4': 'perf-notes/S4-DRAFT.md', 'FN': 'perf-notes/FINDINGS-AND-CHANGES.md'}
PATS = [
    ('pending', r'[Rr]ead-outs? (?:is |are )?(?:still )?pending|[Ff]ormal read-out pending|verdicts? (?:is |are )?pending|due ~10:00|[Pp]ending read-out'),
    ('runner', r'runner summar|runner\'s'),
    ('W9', r'\bW9\b'),
    ('W5b', r'\bW5b\b'),
    ('f10', r'\bf10|[Ff]inding 10|finding-10'),
    ('repin', r'rpm4|rpb0|re-pin|repin|native4b'),
    ('scrn', r'SCRNSAVE|scrnsave'),
    ('chain', r'CHAIN_PRIORITY|S4-T1|#21\b'),
    ('W8a', r'\bW8a'),
    ('struct', r'[Ll]eans now|[Ss]till open|[Aa]fter the break|LOCK'),
    ('d11p', r'\bd11p\b'),
]
which = sys.argv[1] if len(sys.argv) > 1 else 'S4'
path = FILES[which]
text = open(path, 'rb').read().decode('utf-8')
lines = re.split(r'\r\n|\n|\r', text)
print(f'== {path}: {len(lines)} lines')
print('-- headings:')
for i, l in enumerate(lines, 1):
    if re.match(r'#{1,4} ', l) or re.match(r'> \[!', l):
        print(f'{i}: {l[:160]}')
for name, pat in PATS:
    rx = re.compile(pat)
    hits = [(i, l) for i, l in enumerate(lines, 1) if rx.search(l)]
    print(f'-- {name}: {len(hits)} lines')
    for i, l in hits[:70]:
        m = rx.search(l)
        a = max(0, m.start() - 110); b = min(len(l), m.end() + 140)
        print(f'{i} [{len(l)}]: ...{l[a:b]}...')

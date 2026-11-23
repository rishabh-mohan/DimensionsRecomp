"""Agent 9, 04:04: independent check of Agent 2's rb-chain.ps1 -GuardOnly change (read-only, one thread)."""
import difflib, hashlib

A = r'<workspace>\build\agent2'
pre = open(A + r'\rb-chain.ps1.pre-GuardOnly', 'rb').read()
cur = open(A + r'\rb-chain.ps1', 'rb').read()
dif = open(A + r'\RB-diffs\rb-chain.ps1.GuardOnly.diff', 'rb').read()


def h(b):
    return hashlib.sha256(b).hexdigest().upper()[:16]


print('pre-GuardOnly', h(pre), len(pre), 'B | current', h(cur), len(cur), 'B | diff file', h(dif), len(dif), 'B')
print('CR: pre %d cur %d | non-ASCII bytes: cur %d | BOM cur %s'
      % (pre.count(b'\r'), cur.count(b'\r'), sum(1 for c in cur if c > 127), cur[:3] == b'\xef\xbb\xbf'))
d = ''.join(difflib.unified_diff(pre.decode('utf-8').splitlines(True), cur.decode('utf-8').splitlines(True),
                                 'build/agent2/rb-chain.ps1.pre-GuardOnly', 'build/agent2/rb-chain.ps1'))
d = d.replace('\r\n', '\n')
print('my diff == RB-diffs/rb-chain.ps1.GuardOnly.diff:', d.encode('utf-8') == dif)
lines = d.splitlines()
plus = [l for l in lines if l.startswith('+') and not l.startswith('+++')]
minus = [l for l in lines if l.startswith('-') and not l.startswith('---')]
print('changed lines: +%d -%d' % (len(plus), len(minus)))
for l in minus + plus:
    print('  ' + l[:200])
# where the new exit sits relative to the guard steps
cl = cur.decode('utf-8').splitlines()
for i, l in enumerate(cl, 1):
    s = l.strip()
    if ('GuardOnly' in s or s.startswith('$log =') or 'exit 4' in s or "08:30" in s or '07:00' in s
            or s.startswith('$v =') or 'Variant' in s and 'exit' in s or s.startswith('if ($Jobs')):
        print('%4d: %s' % (i, s[:170]))

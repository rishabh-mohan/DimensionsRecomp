"""Agent 2 (task #14, 03:53): rebuild rb-chain.ps1 as Agent 9 reviewed it (3660069E, before the -GuardOnly switch),
save it as build/agent2/rb-chain.ps1.pre-GuardOnly and write build/agent2/RB-diffs/rb-chain.ps1.GuardOnly.diff."""
import difflib, hashlib, os, sys
A = r'<workspace>\build\agent2'
cur_p = os.path.join(A, 'rb-chain.ps1')
cur = open(cur_p, 'rb').read()
edits = [
    (b"# -GuardOnly (for rb-tools-test.ps1): step 0 only, then exit 0; nothing is written or run.\r\n", b""),
    (b", [switch]$NoBuild, [switch]$GuardOnly)", b", [switch]$NoBuild)"),
    (b'if ($GuardOnly) { Write-Host "GUARD OK: -Variant $v -Jobs $Jobs, no other snapshot driver ($($mine.Count) own/ancestor processes skipped); nothing run"; exit 0 }\r\n', b""),
]
old = cur
for a, b in edits:
    if old.count(a) != 1:
        a2, b2 = a.replace(b'\r\n', b'\n'), b.replace(b'\r\n', b'\n')
        if old.count(a2) != 1:
            sys.exit('edit not found exactly once: %r' % a[:60])
        a, b = a2, b2
    old = old.replace(a, b)
h_old = hashlib.sha256(old).hexdigest().upper()
h_cur = hashlib.sha256(cur).hexdigest().upper()
print('reconstructed pre-GuardOnly sha256', h_old[:16], '(Agent 9 reviewed 3660069E...)', 'MATCH' if h_old.startswith('3660069E') else 'NO MATCH')
print('current rb-chain.ps1 sha256', h_cur[:16], len(cur), 'B')
if not h_old.startswith('3660069E'):
    sys.exit(1)
open(os.path.join(A, 'rb-chain.ps1.pre-GuardOnly'), 'wb').write(old)
d = ''.join(difflib.unified_diff(old.decode('utf-8').splitlines(True), cur.decode('utf-8').splitlines(True),
                                 'build/agent2/rb-chain.ps1.pre-GuardOnly', 'build/agent2/rb-chain.ps1'))
dp = os.path.join(A, 'RB-diffs', 'rb-chain.ps1.GuardOnly.diff')
open(dp, 'w', encoding='utf-8', newline='\n').write(d.replace('\r\n', '\n'))
print('diff', dp, hashlib.sha256(open(dp, 'rb').read()).hexdigest().upper()[:16], d.count('\n'), 'lines')
print(d)

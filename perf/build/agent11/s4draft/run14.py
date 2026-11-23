# -*- coding: utf-8 -*-
# run14.py - S4-DRAFT pass 3b for task #10 (Agent 11): SESSION2 22:55-22:57 (L3126-3152).
# Usage: python run14.py --dry | --apply. One-match edits, sha + line gates, hashed backup, LF, no BOM.
import datetime, difflib, hashlib, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'<workspace>'
P = lambda r: os.path.join(ROOT, *r.split('/'))
DRAFT, HOLD = P('perf-notes/S4-DRAFT.md'), P('perf-notes/WINDOW-HOLD.txt')
DRY, APPLY = '--dry' in sys.argv, '--apply' in sys.argv
if DRY == APPLY:
    sys.exit('usage: run14.py --dry | --apply')
sha = lambda b: hashlib.sha256(b).hexdigest().upper()
fails = []
def fail(m):
    fails.append(m); print('FAIL:', m)
if os.path.exists(HOLD):
    sys.exit('HOLD exists: stop')
raw = open(DRAFT, 'rb').read(); H0 = sha(raw)
print('draft %s %d B %d LF' % (H0[:8], len(raw), raw.count(b'\n')))
if not H0.startswith('F25F4E1E') or raw.count(b'\n') != 528 or b'\r' in raw or raw.startswith(b'\xef\xbb\xbf'):
    sys.exit('draft gate FAIL')
old = raw.decode('utf-8')
s2 = open(P('perf-notes/SESSION2.md'), 'rb').read().decode('utf-8').split('\n')
print('SESSION2 %d LF lines' % (len(s2) - 1))
def S(n, *subs):
    for s in subs:
        if s not in s2[n - 1]:
            fail('SESSION2 L%d lacks %r' % (n, s))
S(3127, 'STUCK-LOCK at 22:26:29', 'owner lr 83FAF200', 'The 22:25 waiver now covers it too', "Gate B isn't an input to the W6 read-out")
S(3128, 'for s4bLV and the two finding-10 rows: a STUCK-LOCK counts as "WARN, finding 10" only if all of these hold')
S(3129, 'same CS and owner lr'); S(3130, 'the render thread holds it'); S(3131, 'it recovers by itself, with no crash or WER')
S(3132, 'the run still reaches the level. For s4bLV that also means 3/3 LOADs and K 0 / F 0 over the whole run.'); S(3133, 'Anything else is FAIL.')
S(3134, 'under verify the CP is ~50% kernel-bound (row 7, gate A)', 'Without verify the median is 4-16%', 'one VirtualQuery per upload', 'Candidate for after S4')
S(3135, 'It holds no pinned files, so the freeze check covers only the 3 launcher files')
S(3137, "Agent 3's background scripts are still running"); S(3141, 'confirm all three are gone by 23:50')
S(3142, 'stage expect files for W9, W5b and W4c (paperwork only, by 23:45)')
S(3145, 'it agrees with Agent 2'); S(3146, '109 hooks, the same as native4-bin')
S(3147, "C1 v3's `BlockPhysicalProtectKeepWatch` import pair"); S(3148, 'The only other change is the GPU fingerprint string')
S(3149, "native4b's first start is PSO-cold", 'until it records them again'); S(3150, "don't read boot time or PSO/stall lines from the first native4b run")
S(3151, 'its warm-up run must be a native4b run'); S(3152, 'do the two files live next to each bin, or in one shared place', 'needs a warm-up after each bin switch')
T = datetime.datetime.now().strftime('%H:%M'); BK = 'S4-DRAFT.%s-%s.md' % (T.replace(':', ''), H0[:8])
RULES = "  - **Rules set before the post-window rows (22:55, L3127-3133):** for s4bLV and the two finding-10 rows, a STUCK-LOCK counts as \"WARN, finding 10\" only if it has the same CS and owner lr, the render thread holds it, it recovers by itself (no crash or WER) and the run still reaches the level; for s4bLV that also means 3/3 LOADs and K 0 / F 0 over the whole run. Anything else is a FAIL. Gate B's own finding-10 hang (22:26:29, owner lr 83FAF200) is under the 22:25 waiver, and gate B isn't an input to the W6 read-out."
NATIVE = "  - **native4b (22:57, L3145-3152):** Agent 2's subagent's map check agrees with Agent 2's: 109 hooks, as in native4-bin; the +2 publics are C1 v3's import pair; the only other change is the GPU fingerprint string. The new fingerprint makes native4b's first start PSO-cold (it rejects native4's PSO recipe and seed files until it records them again), so the re-pin rows don't read boot time or PSO/stall lines from the first native4b run, and Monday's W8a needs a native4b warm-up run. Open (Agent 2): whether those files live next to each bin or in one shared place; if shared, a window that mixes native bins needs a warm-up after each bin switch."
VQ = " Agent 12 (22:55): under verify the CP is ~50 % kernel-bound (row 7, gate A), against a 4-16 % median without verify; the suspected cause, one VirtualQuery per upload, is another candidate for after S4 (L3134)."
new = old
def sub(name, o, n):
    global new
    c = new.count(o)
    if c != 1:
        fail('sub %s matches %d' % (name, c)); return
    new = new.replace(o, n); print('sub', name)
def line(name, prefix, fn):
    global new
    L = new.split('\n'); ix = [i for i, l in enumerate(L) if l.startswith(prefix)]
    if len(ix) != 1:
        fail('line %s matches %d' % (name, len(ix))); return
    L[ix[0]] = fn(L[ix[0]]); new = '\n'.join(L); print('line', name, 'L%d' % (ix[0] + 1))
sub('D3', 'then at 19:37, 20:07, 21:47 and 22:55 under task #10', 'then at 19:37, 20:07, 21:47 and 22:55-@T@ under task #10')
sub('D7a', '19:37, 20:07, 21:47 and 22:55; the 15:54 version', '19:37, 20:07, 21:47 and 22:55-@T@; the 15:54 version')
sub('D7b', "the 20:07 one in `build/agent11/s4draft/S4-DRAFT.2147-0C93A609.md` and the 21:47 one in `build/agent11/s4draft/S4-DRAFT.2255-E496D3F6.md`):",
    "the 20:07 one in `build/agent11/s4draft/S4-DRAFT.2147-0C93A609.md`, the 21:47 one in `build/agent11/s4draft/S4-DRAFT.2255-E496D3F6.md` and the 22:55 one in `build/agent11/s4draft/@BK@`):")
sub('since', '- **Since 21:47** (SESSION2 L2921-3124, read at 22:55):', '- **Since 21:47** (SESSION2 L2921-3152, read at 22:55 and @T@):')
line('rules', '  - **C1 default-ON** still needs s4bLV', lambda l: l + '\n' + RULES)
line('native', '  - **The user (22:10):** daytime launcher sessions yes;', lambda l: l + '\n' + NATIVE)
sub('wait', "- **Waiting at 22:55:** the 23:30 launcher freeze;", "- **Waiting at @T@:** the 23:30 launcher freeze;")
sub('wait2', "Agent 8's final ordered GO lines (by 23:45); the user's double-click (~23:45);",
    "Agent 8's final ordered GO lines and Agent 6's expect files for W9, W5b and W4c (both by 23:45, L3142); Agent 3's background scripts gone by 23:50 (L3137-3141); the user's double-click (~23:45);")
sub('upd', '- Updated at 22:55: the header;', '- Updated at 22:55 and @T@ (SESSION2 to L3152): the header;')
sub('upd4b', '§4b (a 21:55-22:44 entry and Possible changes)', '§4b (a 21:55-22:57 entry and Possible changes)')
sub('4b head', '- **21:55-22:44 (L2921-3124):**', '- **21:55-22:57 (L2921-3152):**')
sub('4b tail', 'my GO-line check OK (Changed since 15:54).', "my GO-line check OK; the WARN rules for the post-window rows; native4b's map check and its PSO-cold first start (Changed since 15:54).")
sub('next', "finding 10's direct test, and the launcher's SAFE and freeze (Changed since 15:54).",
    "finding 10's direct test and its WARN rules, native4b's PSO-cold first start, and the launcher's SAFE and freeze (Changed since 15:54).")
line('f10', '- **The stuck game lock (finding 10):** v0.2.0 hits it too', lambda l: l + VQ)
for tok, val in (('@T@', T), ('@BK@', BK)):
    if tok in old:
        fail('token %s in draft' % tok)
    new = new.replace(tok, val)
def bad_rows(t):
    out, L, i = set(), t.split('\n'), 0
    while i < len(L):
        if L[i].startswith('|'):
            h, j = L[i].count('|'), i
            while j < len(L) and L[j].startswith('|'):
                if L[j].count('|') != h: out.add(L[j])
                j += 1
            i = j
        else:
            i += 1
    return out
if bad_rows(new) - bad_rows(old):
    fail('table pipe counts changed')
nb = new.encode('utf-8')
if b'\r' in nb or '@T@' in new or '@BK@' in new:
    fail('CR or token left')
print('new %d B, %d LF (+%d)' % (len(nb), nb.count(b'\n'), nb.count(b'\n') - raw.count(b'\n')))
if nb.count(b'\n') != 530:
    fail('expected 530 LF')
ol, nl = old.split('\n'), new.split('\n'); dry = []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=ol, b=nl, autojunk=False).get_opcodes():
    if tag != 'equal':
        dry.append('=== %s old L%d-%d -> new L%d-%d' % (tag, i1 + 1, i2, j1 + 1, j2))
        dry += ['--- %d: %s' % (i + 1, ol[i]) for i in range(i1, i2)] + ['+++ %d: %s' % (j + 1, nl[j]) for j in range(j1, j2)]
        print(dry[-1 - (i2 - i1) - (j2 - j1)])
if DRY:
    open(P('build/agent11/s4draft/run14-dry.txt'), 'wb').write(('\n'.join(dry) + '\n').encode('utf-8'))
    print('DRY: %d failures' % len(fails)); sys.exit(1 if fails else 0)
if fails or os.path.exists(HOLD):
    sys.exit('not written')
bk = P('build/agent11/s4draft/' + BK)
if os.path.exists(bk) or sha(open(DRAFT, 'rb').read()) != H0:
    sys.exit('backup exists or draft changed')
open(bk, 'wb').write(raw)
open(DRAFT, 'wb').write(nb); chk = open(DRAFT, 'rb').read()
print('WROTE sha256 %s %d B %d LF CR %d; backup %s' % (sha(chk), len(chk), chk.count(b'\n'), chk.count(b'\r'), BK))

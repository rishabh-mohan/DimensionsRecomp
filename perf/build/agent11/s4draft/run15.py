# -*- coding: utf-8 -*-
# run15.py - S4-DRAFT pass 3b for task #10 (Agent 11): SESSION2 22:55-23:01 (L3126-3169).
# Replaces run14.py (never applied): Agent 1 corrected L3129 at 23:00 (owner lr 83FAF188 or 83FAF200),
# settled the PSO question at 23:00 (L3153-3163, correcting the 22:57 morning note), and at 23:01
# recorded Agent 3's queue stopped at 22:56 and Agent 10's gate B PASS (L3169).
# Usage: python run15.py --dry | --apply. One-match edits, sha + line gates, hashed backup, LF, no BOM.
import datetime, difflib, hashlib, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'<workspace>'
P = lambda r: os.path.join(ROOT, *r.split('/'))
DRAFT, HOLD = P('perf-notes/S4-DRAFT.md'), P('perf-notes/WINDOW-HOLD.txt')
DRY, APPLY = '--dry' in sys.argv, '--apply' in sys.argv
if DRY == APPLY:
    sys.exit('usage: run15.py --dry | --apply')
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
print('SESSION2 %d split lines' % len(s2))
def S(n, *subs):
    for s in subs:
        if n > len(s2) or s not in s2[n - 1]:
            fail('SESSION2 L%d lacks %r' % (n, s))
S(3127, 'STUCK-LOCK at 22:26:29', 'owner lr 83FAF200', 'The 22:25 waiver now covers it too', "Gate B isn't an input to the W6 read-out")
S(3128, 'for s4bLV and the two finding-10 rows: a STUCK-LOCK counts as "WARN, finding 10" only if all of these hold')
S(3129, 'CS 0x84959EDC; the owner (render thread, tid 0x17) is parked in sub_83FAF180 at lr 83FAF188 or 83FAF200; the waiter is at lr 82A2A270',
  'Corrected at 23:00 per Agent 12', "gate A's owner was at 83FAF188", 'All 4 hangs share the waiter callers and the GPU thread on PM4 opcode 0x22')
S(3130, 'it recovers by itself, with no crash or WER')
S(3131, 'the run still reaches the level. For s4bLV that also means 3/3 LOADs and K 0 / F 0 over the whole run.'); S(3132, 'Anything else is FAIL.')
S(3133, 'Agent 12: under verify the CP is ~50% kernel-bound (row 7, gate A)', 'Without verify the median is 4-16%', 'one VirtualQuery per upload', 'Candidate for after S4')
S(3141, 'stage expect files for W9, W5b and W4c (paperwork only, by 23:45)')
S(3143, '### 22:57 - Agent 1: native4b map check AGREE')
S(3144, 'it agrees with Agent 2'); S(3145, '109 hooks, the same as native4-bin')
S(3146, "C1 v3's `BlockPhysicalProtectKeepWatch` import pair"); S(3147, 'The only other change is the GPU fingerprint string')
S(3153, '### 23:00 - Agent 1: PSO cache question settled (corrects the 22:57 morning note)')
S(3156, 'is checked against the fingerprint'); S(3157, 'are also checked against the fingerprint')
S(3158, 'The runner makes a fresh run folder for every run', 'only when the arm sets seed_cache')
S(3159, "The re-pin matrices and W8a4 don't set seed_cache", 'neither native4-bin nor native4b-bin has a seed file or a cache folder')
S(3160, '**every run starts PSO-cold on both bins**', 'the warm-up absorbs it', 'The new fingerprint changes nothing for the re-pin or for W8a as staged')
S(3161, '**No REPIN.md change is needed.**', 'This corrects my 22:57 note')
S(3162, 'any native4b arm with seed_cache must use a seed recorded by native4b')
S(3165, 'test-day.ps1 passed 25/25 at 22:54 on run-day.ps1 D86F6DE0 and launcher-ctl.ps1 43EC1AB7')
S(3166, 'The night launcher ignores new files under bench\\agent5\\', 'It pins only run-night.ps1, RUN-NIGHT.cmd and the bench\\agent8\\run files')
S(3167, 'The install folder will be bench\\agent5\\day\\', 'Day sessions write their status to bench\\agent5\\day\\status', "Agent 12's read-out must look there too")
S(3168, 'Hashes due by 23:35.')
S(3169, '23:01: Agent 3 stopped its s4b queue, postcheck and hostload at 22:56', 'no game or compiler is running',
  'Agent 10 rated gate B PASS for W6 (b2r row 43/§42)', 'Morning queue: f10a, then f10b, then rpb0/rpm4',
  'build\\agent3\\s4b\\ready-later + ready-quiet', 'Agent 3 creates them when I give the word after the windows')
T = datetime.datetime.now().strftime('%H:%M'); BK = 'S4-DRAFT.%s-%s.md' % (T.replace(':', ''), H0[:8])
RULES = ("  - **Rules set before the post-window rows (22:55, owner lr corrected at 23:00; L3127-3132):** for s4bLV and the two finding-10 rows, "
         "a STUCK-LOCK counts as \"WARN, finding 10\" only if all of these hold: CS 0x84959EDC, with the owner (render thread, tid 0x17) parked in "
         "sub_83FAF180 at lr 83FAF188 or 83FAF200 and the waiter at lr 82A2A270 (gate A's owner was at 83FAF188; all 4 hangs share the waiter callers "
         "and the GPU thread on PM4 opcode 0x22; Agent 12); it recovers by itself, with no crash or WER; and the run still reaches the level, which for "
         "s4bLV also means 3/3 LOADs and K 0 / F 0 over the whole run. Anything else is a FAIL. Gate B's own finding-10 hang (22:26:29, owner lr 83FAF200) "
         "is under the 22:25 waiver, and gate B isn't an input to the W6 read-out.")
NATIVE = ("  - **native4b (22:57-23:00, L3143-3163):** Agent 2's subagent's map check agrees with Agent 2's: 109 hooks, as in native4-bin; the +2 publics "
          "are C1 v3's import pair; the only other change is the GPU fingerprint string. The PSO question is settled from the code (Agent 1, 23:00, "
          "correcting the 22:57 morning note): the recipe and seed files are checked against the fingerprint, but every run gets a fresh folder and "
          "cache files are copied in only for arms that set seed_cache, which the re-pin matrices and W8a4 don't, and neither bin has a seed file or a "
          "cache folder. So every run starts PSO-cold on both bins, by design, the warm-up absorbs it, and nothing changes for the re-pin, for W8a as "
          "staged or for REPIN.md. A future native4b arm with seed_cache needs a seed recorded by native4b.")
DAY = (" At 23:00 (L3164-3168): test-day.ps1 passed 25/25 (22:54) on run-day.ps1 D86F6DE0 and launcher-ctl.ps1 43EC1AB7; the night launcher pins "
       "only run-night.ps1, RUN-NIGHT.cmd and the `bench/agent8/run` files and ignores new files under `bench/agent5/`; the day install folder will "
       "be `bench/agent5/day/`, with status in `bench/agent5/day/status`, which Agent 12's read-out must read too.")
GATEB = "; Agent 10 rated it PASS for W6 (b2r row 43/§42; L3169)"
AFTER = (" Agent 3 stopped its queue, postcheck and hostload at 22:56, so none of its runs is left tonight, and at 23:01 no game or compiler was running; its "
         "morning queue is f10a, then f10b, then rpb0/rpm4, gated by marker files (`build/agent3/s4b/ready-later` and `ready-quiet`) that Agent 3 "
         "creates on Agent 1's word after the windows (L3169).")
VQ = (" Agent 12 (22:55): under verify the CP is ~50 % kernel-bound (row 7, gate A), against a 4-16 % median without verify; the suspected cause, "
      "one VirtualQuery per upload, is another candidate for after S4 (L3133).")
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
sub('gateB', 'so none of its 3 tags was placed (L3001, L3074-3080, L3103-3107)', 'so none of its 3 tags was placed (L3001, L3074-3080, L3103-3107)' + GATEB)
sub('day', 'Agents 10 and 11 rate it after the windows (L3088-3092).', 'Agents 10 and 11 rate it after the windows (L3088-3092).' + DAY)
sub('since', '- **Since 21:47** (SESSION2 L2921-3124, read at 22:55):', '- **Since 21:47** (SESSION2 L2921-3169, read at 22:55 and @T@):')
line('rules', '  - **C1 default-ON** still needs s4bLV', lambda l: l + '\n' + RULES)
line('native', '  - **The user (22:10):** daytime launcher sessions yes;', lambda l: l + '\n' + NATIVE)
sub('wait', "- **Waiting at 22:55:** the 23:30 launcher freeze;", "- **Waiting at @T@:** the 23:30 launcher freeze;")
sub('wait2', "Agent 8's final ordered GO lines (by 23:45); the user's double-click (~23:45);",
    "Agent 8's final ordered GO lines and Agent 6's expect files for W9, W5b and W4c (both by 23:45, L3141); Agent 5's day-draft hashes (by 23:35, L3168); the user's double-click (~23:45);")
sub('after', 'the re-pin rows and the CG26/CTR builds (L3003-3007, L3033).', 'the re-pin rows and the CG26/CTR builds (L3003-3007, L3033).' + AFTER)
sub('upd', '- Updated at 22:55: the header;', '- Updated at 22:55 and @T@ (SESSION2 to L3169): the header;')
sub('upd4b', '§4b (a 21:55-22:44 entry and Possible changes)', '§4b (a 21:55-23:01 entry and Possible changes)')
sub('4b head', '- **21:55-22:44 (L2921-3124):**', '- **21:55-23:01 (L2921-3169):**')
sub('4b tail', 'my GO-line check OK (Changed since 15:54).',
    "my GO-line check OK; the WARN rules for the post-window rows (owner lr corrected at 23:00); native4b's map check and the settled PSO question (every run starts PSO-cold on both bins; no REPIN.md change); the day draft's 25/25; gate B PASS for W6 (Agent 10); Agent 3's queue stopped at 22:56, with its morning queue (Changed since 15:54).")
sub('next', "finding 10's direct test, and the launcher's SAFE and freeze (Changed since 15:54).",
    "finding 10's direct test and its WARN rules, native4b's map check and PSO cache, and the launcher's SAFE and freeze (Changed since 15:54).")
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
    open(P('build/agent11/s4draft/run15-dry.txt'), 'wb').write(('\n'.join(dry) + '\n').encode('utf-8'))
    print('DRY: %d failures' % len(fails)); sys.exit(1 if fails else 0)
if fails or os.path.exists(HOLD):
    sys.exit('not written')
bk = P('build/agent11/s4draft/' + BK)
if os.path.exists(bk) or sha(open(DRAFT, 'rb').read()) != H0:
    sys.exit('backup exists or draft changed')
open(bk, 'wb').write(raw)
open(DRAFT, 'wb').write(nb); chk = open(DRAFT, 'rb').read()
print('WROTE sha256 %s %d B %d LF CR %d; backup %s' % (sha(chk), len(chk), chk.count(b'\n'), chk.count(b'\r'), BK))

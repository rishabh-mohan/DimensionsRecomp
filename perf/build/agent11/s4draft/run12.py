# -*- coding: utf-8 -*-
# run12.py - S4-DRAFT pass 2 for task #10 (Agent 11): SESSION2 20:30-21:33 (L2779-2919).
# Usage: python run12.py --dry | --apply. One-match edits, sha + line gates, hashed backup, LF, no BOM.
import datetime, difflib, hashlib, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'<workspace>'
P = lambda r: os.path.join(ROOT, *r.split('/'))
DRAFT, HOLD = P('perf-notes/S4-DRAFT.md'), P('perf-notes/WINDOW-HOLD.txt')
DRY, APPLY = '--dry' in sys.argv, '--apply' in sys.argv
if DRY == APPLY:
    sys.exit('usage: run12.py --dry | --apply')
sha = lambda b: hashlib.sha256(b).hexdigest().upper()
fails = []
def fail(m):
    fails.append(m); print('FAIL:', m)
if os.path.exists(HOLD):
    sys.exit('HOLD exists: stop')
raw = open(DRAFT, 'rb').read(); H0 = sha(raw)
print('draft %s %d B %d LF' % (H0[:8], len(raw), raw.count(b'\n')))
if not H0.startswith('0C93A609') or raw.count(b'\n') != 509 or b'\r' in raw or raw.startswith(b'\xef\xbb\xbf'):
    sys.exit('draft gate FAIL')
old = raw.decode('utf-8')
s2 = open(P('perf-notes/SESSION2.md'), 'rb').read().decode('utf-8').split('\n')
print('SESSION2 %d LF lines' % (len(s2) - 1))
def S(n, *subs):
    for s in subs:
        if s not in s2[n - 1]:
            fail('SESSION2 L%d lacks %r' % (n, s))
S(2784, 'The read-out method for W5 and later is **T-std**'); S(2785, 'W4b 12.2 → 2.3 %', 'W5 6.5 → 2.1 %')
S(2787, 'd11t p99 is +8.8 % [+1.0, +17.2]*', 'a lead only'); S(2788, 'fps +6.0 % [+0.5, +11.8]*')
S(2789, 'W6 option for the user (ask at ~23:30)', 'Best performance'); S(2793, '9b40acbbef4c57b3')
S(2819, 'Pin freeze from 23:30'); S(2830, '6 arms × 3 repeats', 'The ref is s0'); S(2835, 'strict rules FAIL')
S(2837, 'd11t game CPU is -15.3 %'); S(2839, 'strict rules FAIL (R3 drops 15/15, R6 drops 1821)')
S(2840, '1 of 16 tests'); S(2841, 'd11t -13.7 %, d11p -12.2 %')
S(2843, 'the S4a arms equal S3d within about ±4 % (T-std)', 'cuts game CPU by 12-14 %')
S(2848, 'W6 bin = **devoff4b**'); S(2849, 'without the timer bundle', 'p99 lead'); S(2850, 'I write perf-notes/WINDOW-GO.txt')
S(2857, 'devoff4b-bin staged 20:49:07'); S(2858, 'MANIFEST DE11A914079D7DF7'); S(2865, 'Pending: the native re-pin on native4b.')
S(2868, '9b40acbbef4c57b3', 'ETA ~21:20'); S(2869, 'since 20:52')
S(2871, 'rows 7/20/23 ~22:10', 'W6 block ~22:38; re-pin ~23:02. Last launch 23:10')
S(2872, "Most W7+ functional rows won't run tonight"); S(2883, 'all finished by 23:40')
S(2885, 'up to 2 follow-up windows for 01:00-06:45 by 22:45'); S(2893, 'F1 approved as is')
S(2894, "W8b can't run tonight"); S(2895, 'W9 (devoff4b, #24, 16 runs, ~40 min)', 'W8a (native4b after the re-pin, 13 runs, ~33 min)', 'SPIN_US=30')
S(2896, 'Agent 1 writes the GO only after all of Agent 3', 'w6s3, ~22:38', 'Repeats are set after Agent 7')
S(2902, 'w6gA', 'RECOVERED HANG'); S(2904, 'sub_83FAF180'); S(2905, '9x slower')
S(2907, 'counts as a WARN (finding 10), not a W6 FAIL', 'G4, G5 and G8'); S(2908, 'E50D791B', '21:16-21:17')
S(2910, 'Stop-Tree must not use `taskkill /T`'); S(2911, 'restore the driver allowlist'); S(2913, 'the hard stop is 07:30, not 07:45')
S(2918, 'All 16 runs are clean')
T = datetime.datetime.now().strftime('%H:%M'); BK = 'S4-DRAFT.%s-%s.md' % (T.replace(':', ''), H0[:8])
NEW = '\n'.join([
 "- **Since 20:07** (SESSION2 L2779-2919, read at @T@):",
 "  - **Read-out method:** T-std, Agent 7's #6: frames are split at the runner's 4.5 ms threshold and re-mixed at the median heavy-time share; median-ms CV falls from 12.2 to 2.3 % on W4b and from 6.5 to 2.1 % on W5 (L2784-2788).",
 "  - **Agent 8's interim read-outs (20:45, L2835-2843):** W4b and W5 both FAIL the strict rules, so neither has a timing verdict. W4b: every arm overlaps d0, d11t uses 15.3 % less game CPU, and codegen B's fps +6.0 % [+0.5, +11.8]* (B-block T-std, n = 3) is a hint awaiting its check. W5: the S4a arms equal S3d within about ±4 % (T-std); the timer bundle cuts game CPU by 12-14 % (d11t −13.7 %, d11p −12.2 %); d11t's p99 +8.8 % [+1.0, +17.2]* is a lead only (1 of 16 tests). Agent 6's W5 logdiff is clean: all 16 runs (21:33, L2918).",
 "  - **W6:** bin devoff4b, without the timer bundle (d11t has the p99 lead, and s0 stays comparable to W5's s0). Agent 5's finalize, `build/agent5/w6-draft/matrix-window6.json` (E50D791B…, 21:16), has 6 arms × 3 repeats: s0; p2, p2f and p2fc; f and fc. Agent 8 promotes it once Agent 3's interim W6 rows pass; Agent 1 writes the GO only after all of Agent 3's W6 rows pass (w6s3 ~22:38) and the user has left; repeats follow Agent 7's 22:30 note (L2830, L2847-2850, L2896, L2908). Option for the user at ~23:30: Power mode Best performance before the double-click (L2789).",
 "  - **Gate A (w6gA, p2fc + verify, devoff4b): RECOVERED HANG**, one STUCK-LOCK whose owner sits in #24's L1 poll (sub_83FAF180), under verify mode's ~9x slowdown and the -j8 compile: finding 10 (§5). Agent 1's rule: such a STUCK-LOCK is a WARN, not a W6 FAIL; gate A passes on G4, G5 and G8, and the W6 read-out reports STUCK-LOCK counts per arm (L2902-2907).",
 "  - **Bins:** devoff4b-bin staged 20:49:07 (MANIFEST DE11A914079D7DF7…), with Agent 10's gates 1, 2, 3 and 5 PASS and gate 4, the native re-pin, pending (L2857-2867). native4b's fingerprint 9b40acbbef4c57b3 confirms Agent 4's; its rebuild ETA was ~21:20, then CTR and CG26 (L2793, L2868). Builds end by 23:40, and the pin freeze starts at 23:30 (L2819, L2883).",
 "  - **Agent 3's queue** (on devoff4b since 20:52; L2869-2872): rows 7/20/23 ~22:10, the W6 block ~22:38, the re-pin ~23:02, last launch 23:10. Most W7+ rows won't run tonight, so the night is W6 plus at most 2 follow-up windows from arms already checked, proposed by Agent 8 by 22:45 (L2885): W9 (devoff4b, 16 runs, ~40 min, SPIN_US=30) or W8a (native4b after the re-pin, 13 runs, ~33 min). W8b can't run: #21 isn't built (L2894-2895).",
 "  - **Agent 5's launcher:** F1's 11 env keys are approved (L2893). At 21:29 three MUSTs are open: no `taskkill /T` in Stop-Tree, the 3-name driver allowlist back, and the hard stop at 07:30 (L2910-2913). My review: `build/agent11/launcher-review/REVIEW.md`.",
])
WAIT = "- **Waiting at @T@:** Agent 3's W6 rows (w6s3 ~22:38) and rows 7/20/23 (~22:10); native4b, then Agent 4's re-pin (~23:02); Agent 8's W6 promotion and follow-up proposal (by 22:45); Agent 5's final launcher and my formal verdict (by 23:00); the user's double-click (~23:45)."
UPD = "- Updated at @T@: the header; Changed since 15:54 (the \"Since 20:07\" item and Waiting); Still open (W5's read-out, Agent 5's launcher); the W6 row; §4b (a 20:30-21:33 entry and Possible changes)."
E4B = "- **20:30-21:33 (L2779-2919):** T-std is the read-out method; Agent 8's interim read-outs (strict FAIL on W4b and W5; W5's S4a arms equal S3d within about ±4 %; the timer bundle cuts game CPU by 12-14 %); W6 on devoff4b without the timer bundle, GO by Agent 1; devoff4b staged, gates 1-3 and 5 PASS; gate A's STUCK-LOCK in the L1 poll is a WARN, not a W6 FAIL; F1's env keys approved; the launcher MUSTs of 21:29 (Changed since 15:54)."
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
sub('D3', 'then at 19:37 and 20:07 under task #10', 'then at 19:37, 20:07 and @T@ under task #10')
sub('D7', "19:37 and 20:07; the 15:54 version is kept in `build/agent11/s4draft/S4-DRAFT.1937-14C2A482.md` and the 19:37 one in `build/agent11/s4draft/S4-DRAFT.2007-0CB74A52.md`):",
    "19:37, 20:07 and @T@; the 15:54 version is kept in `build/agent11/s4draft/S4-DRAFT.1937-14C2A482.md`, the 19:37 one in `build/agent11/s4draft/S4-DRAFT.2007-0CB74A52.md` and the 20:07 one in `build/agent11/s4draft/@BK@`):")
line('wait', '- **Waiting at 20:07:** ', lambda l: NEW + '\n' + WAIT)
line('upd', '- Updated at 20:07: the header;', lambda l: UPD + '\n' + l)
line('D124', "- **W5's read-out:** W5 ran at 17:56-18:29", lambda l: l + " At 20:45, Agent 8's interim read-out (T-std): the S4a arms equal S3d within about ±4 %, the timer bundle cuts game CPU by 12-14 %, and d11t's p99 is a lead only; Agent 6's W5 logdiff is clean (SESSION2 L2839-2843, L2918).")
line('D125', "- **Agent 5's launcher** (`bench/agent5/launch/RUN-NIGHT.cmd`;", lambda l: l + " At @T@: run-night.ps1 3EFC5312 and README 581A03DB, with three MUSTs open (Stop-Tree without `taskkill /T`, the driver allowlist, the hard stop at 07:30; L2910-2913); my formal verdict by 23:00 (`build/agent11/launcher-review/REVIEW.md`).")
sub('W6 row', "started by Agent 5's launcher, not before 00:00 (SESSION2 L2702, L2714) | s0 / #8",
    "started by Agent 5's launcher, not before 00:00 (SESSION2 L2702, L2714). As finalized at 21:16: devoff4b, no timer bundle, 6 arms × 3 (s0; p2, p2f, p2fc; f, fc); the GO by Agent 1 after all of Agent 3's W6 rows pass and the user has left (L2830, L2847-2850, L2896, L2908) | s0 / #8")
line('4b', '- **19:42-19:49 (L2719-2761):**', lambda l: l + '\n' + E4B)
sub('D446', "Next: Agent 8's W5 read-out (with Agent 6's W5 logdiff; read with §2c's environment caveat, the Defender caveat and the 3-mode slow-state check), the S4b + S4c bins, Agent 3's queue, Agent 4's re-pin and Agent 5's launcher.",
    "Since 20:07: T-std, Agent 8's interim read-outs, the W6 decisions, devoff4b, gate A, the queue times, the follow-up windows and the launcher MUSTs (Changed since 15:54). Next: Agent 8's formal read-outs, Agent 3's W6 rows, native4b and Agent 4's re-pin, the W6 promotion and GO, and Agent 5's final launcher.")
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
ol, nl = old.split('\n'), new.split('\n'); dry = []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=ol, b=nl, autojunk=False).get_opcodes():
    if tag != 'equal':
        dry.append('=== %s old L%d-%d -> new L%d-%d' % (tag, i1 + 1, i2, j1 + 1, j2))
        dry += ['--- %d: %s' % (i + 1, ol[i]) for i in range(i1, i2)] + ['+++ %d: %s' % (j + 1, nl[j]) for j in range(j1, j2)]
        print(dry[-1 - (i2 - i1) - (j2 - j1)])
if DRY:
    open(P('build/agent11/s4draft/run12-dry.txt'), 'wb').write(('\n'.join(dry) + '\n').encode('utf-8'))
    print('DRY: %d failures' % len(fails)); sys.exit(1 if fails else 0)
if fails or os.path.exists(HOLD):
    sys.exit('not written')
bk = P('build/agent11/s4draft/' + BK)
if os.path.exists(bk) or sha(open(DRAFT, 'rb').read()) != H0:
    sys.exit('backup exists or draft changed')
open(bk, 'wb').write(raw)
open(DRAFT, 'wb').write(nb); chk = open(DRAFT, 'rb').read()
print('WROTE sha256 %s %d B %d LF CR %d; backup %s' % (sha(chk), len(chk), chk.count(b'\n'), chk.count(b'\r'), BK))

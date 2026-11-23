# One-match edits of REVIEW.md (Agent 11's own file). Gate: 4C14DBCD (20:58 pre-read).
# v2 of this script: records Agent 1's 21:01 classification (must/should/optional).
import hashlib, shutil, sys

P = 'build/agent11/launcher-review/REVIEW.md'
GATE = '4C14DBCDA47BCC6C180035F3F53F821AC7A690F5080E551A41BFD37B0F42DCB6'
b = open(P, 'rb').read()
h = hashlib.sha256(b).hexdigest().upper()
if h != GATE:
    sys.exit('GATE FAIL ' + h)
s = b.decode('utf-8')
assert '\r' not in s

L69 = ('- These pass as they are: W4, W5 (s3d), matrix-s3-functional, matrix-codegen, and the W6 check matrix '
       '(devoff4-bin, cvars only). W7 (#18-#20, cvars) and W10 (#26, a bin) need no env keys.\n')

SUBS = [
    ('Status: **PRE-READ (20:58)**, not yet the formal verdict. The formal verdict follows when Agent 5 asks, after the fix set due at 23:00.',
     'Status: **PRE-READ (20:58, updated 21:03)**, not yet the formal verdict. The formal verdict follows when Agent 5 asks (hard deadline 23:00, Agent 1 at 21:01).\n'
     'Agent 1\'s classification (21:01): **must-fix** F1, F3 and README L151; **should-fix** F5; **optional** F4 and F6, and no WINDOW-CANCEL.'),
    ('| (20:53:42) | README.md | 39ECF5C21234B500\u2026 | being edited; to be read in the formal pass |',
     '| (20:53:42) | README.md | 39ECF5C21234B500\u2026 | 16,507 B; only searched so far (L117, L163, L170, L202); full read in the formal pass |'),
    ('8. Rules from SESSION2.md (to L2853) and S4-DRAFT.md.',
     '8. Rules from SESSION2.md (to L2873) and S4-DRAFT.md.'),
    ('### F1 HIGH (time-critical): the env allowlist refuses every native window and W9',
     '### F1 HIGH, must-fix: the env allowlist refuses every native window and W9'),
    (L69,
     L69 + '- **Decision (Agent 1, 21:01): must-fix.** Agent 8 sends the exact key list to Agent 5 by 21:45. '
           'Context: SESSION2 L2872 (20:56) says most W7+ functional rows won\'t run tonight, so the plan is W6 plus windows built '
           'only from arms that have already passed their functional checks. W6 passes as it is.\n'),
    ('  - Update the README env rule and the runner-command text (v1 README L108, L125).',
     '  - Update the README env rule and the runner-command text (v1 README L108, L125; 39ECF5C2 L117, L163, L170).'),
    ('### F2 (v1 MEDIUM): a window could start without a HOLD. **Fixed in v2**; README to follow',
     '### F2 (v1 MEDIUM): a window could start without a HOLD. **Fixed in v2**; README L151 must-fix, looks done in 39ECF5C2'),
    ('- **Open:** README L151 (01C4D90F) still says "If it disappears during the gate wait, the launcher logs that and does not write it again." To be checked in 39ECF5C2 or later.',
     '- README: v1 (01C4D90F) L151 said "If it disappears during the gate wait, the launcher logs that and does not write it again." '
     '39ECF5C2 L202 now says "If its own HOLD has disappeared, it writes it again and logs that." That matches v2; to be confirmed in the full read.'),
    ('### F3 MEDIUM: the 06:45 latest start is not enforced',
     '### F3 MEDIUM, must-fix: the 06:45 latest start is not enforced'),
    ('### F4 LOW: the "not before 00:00" rule is not enforced',
     '### F4 LOW, optional: the "not before 00:00" rule is not enforced'),
    ('### F5 MEDIUM (quality, not safety): the close list misses the user\'s Copilot and Store Roblox',
     '### F5 MEDIUM (quality, not safety), should-fix: the close list misses the user\'s Copilot and Store Roblox'),
    ('### F6 LOW / optional',
     '### F6 LOW, optional'),
    ('Option: a `WINDOW-CANCEL.txt` honoured during the gate wait (drop this GO, keep waiting).',
     'Option: a `WINDOW-CANCEL.txt` honoured during the gate wait (drop this GO, keep waiting). Agent 1: not wanted.'),
    ('exits at 07:30 without clearing, so a window still running at 07:30 would leave a stale HOLD.',
     'exits at 07:30 without clearing, so a window still running at 07:30 would leave a stale HOLD. '
     'Agent 1 (21:01): in the morning he clears a stale HOLD, but only if no runner or game is running.'),
    ('3. Confirm each fix: Agent 10\'s 1-8, F1, F3-F5 and README L151.',
     '3. Confirm each fix: Agent 10\'s 1-8; must-fix F1, F3 and README L151; should-fix F5; optional F4 and F6.'),
]

for old, new in SUBS:
    n = s.count(old)
    if n != 1:
        sys.exit('MATCH FAIL n=%d: %s' % (n, old[:70]))
    s = s.replace(old, new)

if '--apply' in sys.argv:
    shutil.copyfile(P, 'build/agent11/launcher-review/REVIEW.2058-4C14DBCD.md')
    out = s.encode('utf-8')
    open(P, 'wb').write(out)
    print('APPLIED', hashlib.sha256(out).hexdigest().upper(), len(out), 'B', s.count('\n'), 'LF')
else:
    print('DRY OK', len(SUBS), 'subs', s.count('\n'), 'LF')

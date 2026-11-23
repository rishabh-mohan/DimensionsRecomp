"""Agent 10: apply the 02:17 session-3 updates to perf-notes/agent10-batch2-review.md in one write.
Every target must occur exactly once, or nothing is written."""
import hashlib
import sys

P = r'<workspace>\perf-notes\agent10-batch2-review.md'

EDITS = [
    # status row 8
    ('| 8 | #22 audio-shutdown fix | A12 |',
     '| 8 | #22 audio-shutdown fix; S3 flips the default ON | A12 |'),
    ('| OFF (`audio_shutdown_detach_worker=false`) | **SAFE** at the default (equivalent rewrite); **SAFE-IF** ON (§8) | 22:15 to 1, 12 |',
     '| S2: OFF. S3: ON (`audio_shutdown_detach_worker=true`), live since 02:04 (4331A312…, 02:04:39; the one-line flip at :48) '
     '| **SAFE** OFF (equivalent rewrite); **SAFE** ON (condition met 00:08; live diff confirmed 02:17, §8) | 22:15 to 1, 12; ON 02:17 to 1, 12, 6, 2 |'),
    # status row 11
    ('| A11 (A12 lands it) | staged `build/agent11/safeorder/safeorder.diff` (56952876…, -5/+7, rex_app.cpp :71-75, :741-745). '
     'Live rex_app.cpp is still pristine (E1569868…) | ON; kill switch `--pause_safe_order=false` | **SAFE** (§11) | 00:12 to 1, 11 |',
     '| A11 (A12 landed it 02:04) | `build/agent11/safeorder/safeorder.diff` (56952876…, -5/+7, rex_app.cpp :71-75, :741-745). '
     'Live rex_app.cpp 11DE333F… (02:04:38) = the staged file I rated; S2 has pristine E1569868… | ON; kill switch '
     '`--pause_safe_order=false` | **SAFE** (§11); confirmed on the live file 02:17 | 00:12 to 1, 11; live 02:17 to 1, 12, 6, 2 |'),
    # status row 12
    ("| A6 (applies at A1's GO after the relaunch) | staged `build/agent6/fix-a/` (71AEFF3D…, 50046A3F…): settings_registry.cpp:103-104 "
     "(+ :200), settings_preferences.cpp:69-71. Not live yet |",
     "| A6 (applied 02:05:27 at A1's GO) | `build/agent6/fix-a/` (71AEFF3D…, 50046A3F…): settings_registry.cpp:103-104 (+ :200), "
     "settings_preferences.cpp:69-71. Live (02:05:27, CRLF kept): registry 4EC71328… (with the commit hunk), prefs 9CBE6DBF… |"),
    ('| 01:28 to 1, 7 |\n| 13 |',
     '| 01:28 to 1, 7; live re-hash 02:17 to 1, 6, 12, 2 |\n| 13 |'),
    # section 8
    ('  - I confirm the ON rating when Agent 12 sends the one-line diff after quiet window 3.\n',
     '  - I confirm the ON rating when Agent 12 sends the one-line diff after quiet window 3.\n'
     "- **ON confirmed on the live file (02:17).** Agent 12 ran `s3flip_stage.ps1 -Apply` at 02:04 on Agent 1's GO.\n"
     '  - Live `audio_system.cpp` is 4331A312A9FE8F15… (18,877 B, 02:04:39, LF only), the staged file. Its `git diff HEAD` equals the '
     'staged `build/agent12/s3flip/audio-default-on.diff` (BF399E59…, -1/+1).\n'
     '  - My own `git diff --no-index` of the pristine copy (C281FA86…) against the staged file changes one line: :48 '
     '`audio_shutdown_detach_worker, false,` → `true,`.\n'
     '  - `s3flip_stage.ps1 -Check` exits 3 (applied). The syntax check of the live file passed with only the 2 known decoder.h '
     'warnings (`build/agent12/s3flip/syntax-20261122-020455.txt`).\n'
     '  - No toml, runner or bench file sets `audio_shutdown_detach_worker`, so every S3 arm runs ON. '
     '`--audio_shutdown_detach_worker=false` gives the old mode back.\n'
     '  - **Verdict: SAFE ON.** The condition was met at 00:08, and the live change is that one line. The cost when ON is two '
     'uncontended CAS operations per blocking call on the audio worker. Undo: `s3flip_stage.ps1 -Revert`.\n'),
    # section 11
    ('To undo: `-Revert`.\n\n## 12. S3 native startup fix',
     "To undo: `-Revert`.\n\n**Landed (02:04).** Agent 12 ran `-Apply` on Agent 1's GO.\n"
     '- Live `rex_app.cpp` is 11DE333FA4C0541F… (33,054 B, 02:04:38, LF only): the staged file I rated. `git diff HEAD` equals '
     "`safeorder.diff` (56952876…), and `-Check` says `staged (applied)`.\n"
     '- `safeorder_syntax.ps1 -Live` passed with the 3 known warnings (xmemory.h:260, rex_app.h:99/:102; '
     '`build/agent11/safeorder/syntax-20261122-020520.txt`).\n'
     "- No toml or runner sets `pause_safe_order`, so S3 runs the new default. Agent 11's `testg_session.ps1 -Only default` on "
     'devoff3 tests it.\n'
     "- **Verdict unchanged: SAFE**, also together with #22's ON flip (last bullet of the verdict above).\n\n"
     '## 12. S3 native startup fix'),
    # section 12
    ("- If Agent 1 wants more than Agent 6's -SyntaxOnly, run `env/compile-one.ps1` on the two patched TUs (at most 2 threads).",
     "- If Agent 1 wants more than Agent 6's -SyntaxOnly, run `env/compile-one.ps1` on the two patched TUs (at most 2 threads).\n\n"
     "**Applied (02:05:27).** Agent 6 copied the staged files in at Agent 1's GO, hash-guarded. Undo: "
     '`build/agent6/fix-a/apply_fix_a.ps1 -Revert`.\n'
     '- My re-hash at 02:09 matches the expected values above:\n'
     '  - registry 4EC71328043FA6BA… (11,224 B; fix-a plus the commit hunk; git blob 4b56537 → a299f41);\n'
     '  - prefs 9CBE6DBF9CEDA62D… (4,938 B; blob 2d72eac → f02940c);\n'
     '  - both keep CRLF (registry 211 CR = 211 LF, prefs 110 = 110).\n'
     '- `git diff HEAD` shows exactly hunks 1-3 (registry +5/-2, prefs +3/-1). Besides these two files, `git status` in the game repo '
     'shows only the `rexglue-sdk` and `thirdparty/plume` pointers.\n'
     "- Agent 6's `compile-one -SyntaxOnly` (NATIVE_GPU=1) returned rc=0 for both. The registry keeps its 4 known getenv/sscanf "
     'warnings (now :136, :138, :151, :155); prefs has none. That is enough for S3. The full compile is Agent 2\'s devoff3/native3 build.\n'
     '- **Verdict unchanged: SAFE**, with all three hunks together.'),
]

raw = open(P, 'rb').read()
text = raw.decode('utf-8')
crlf = '\r\n' in text
for i, (old, new) in enumerate(EDITS):
    if crlf:
        old, new = old.replace('\n', '\r\n'), new.replace('\n', '\r\n')
    n = text.count(old)
    if n != 1:
        sys.exit('edit %d: target found %d times; nothing written' % (i, n))
    text = text.replace(old, new)
out = text.encode('utf-8')
with open(P, 'wb') as f:
    f.write(out)
print('ok: %d edits, crlf=%s, %d -> %d bytes, sha256 %s' % (len(EDITS), crlf, len(raw), len(out),
                                                           hashlib.sha256(out).hexdigest()[:16].upper()))

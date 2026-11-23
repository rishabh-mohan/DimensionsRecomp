#!/usr/bin/env python3
"""Revise section 9 of perf-notes/agent6-hang-triage.md per Agent 1 (06:28).

- item 4: (e) is merged with Agent 9's (a1)/(a2) into one S4 item (same loop);
- item 2: the dump delay is staged only;
- item 5: Defender / PresentMon is user question 3, nobody touches either.
One-shot and guarded; keeps UTF-8 / LF / no BOM; backs up the note first.
"""
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
NOTE = HERE.parents[2] / 'perf-notes' / 'agent6-hang-triage.md'
BAK = HERE / 'agent6-hang-triage.md.bak-0630'

raw = NOTE.read_bytes()
t = raw.decode('utf-8')
if 'merged at Agent 1' in t:
    sys.exit('already patched')
if b'\r\n' in raw or raw.startswith(b'\xef\xbb\xbf') or not t.endswith('\n'):
    sys.exit('unexpected encoding or line endings')
if not BAK.exists():
    shutil.copyfile(NOTE, BAK)

OLD_STATUS = "Status: **written 2026-11-22 ~06:20.**"
NEW_STATUS = "Status: **written 2026-11-22 ~06:20; §9 revised ~06:35 at Agent 1's request.**"

OLD_2 = "2. **Stop the dump from freezing a game that recovers (SDK, diagnostics only).**"
NEW_2 = ("2. **Stop the dump from freezing a game that recovers (SDK, diagnostics only). "
         "Staged only, not an S4 item (Agent 1, 06:28).**")

OLD_45 = """4. **Xenos path: the lever is CPU time for the CP, not compile work.** The holds had pm 0 and a GPU that looked idle. A candidate S4 item for Agent 10:
   - **(e)** make the D3D ring-buffer wait yield on the host. Hook sub_83FAF180 to call `SwitchToThread()` (or pause, then yield) on each pass.
   - It changes timing only; the loop's exit conditions stay the same. So it is output-identical in the same sense as S8/S11. Ship it OFF behind a cvar.
   - A recompiler-wide `db16cyc` → pause mapping would also touch every guest spinlock, so it carries a much wider risk.
   - Test: devoffB-bin with attract-long on a loaded machine, off vs on. Count reports and frames ≥5 s, and check that the hook isn't hit when nothing is pending.
5. **Machine (the user's call; host state is not ours to change).** Exclude the run dirs from Defender and stop FrameView/PresentMon during timing windows. Both were consuming 2-5 cores during these runs.
"""

NEW_45 = """4. **Xenos path: one S4 item with Agent 9, the GPU-wait hook on sub_83FAF180** (merged at Agent 1's request, 06:28). The lever is CPU time for the CP, not compile work. The holds had pm 0 and a GPU that looked idle, and the owner's spin took one of the 1.3-1.8 cores the game got.
   - **Design: Agent 9's (a1)/(a2)** in `agent9-codegen.md` S4.1.3, items 2-3. Both hook the poll step with `REX_HOOK_RAW`, gated by an env var that is OFF by default, and then call the original unchanged.
     - (a1) sleeps on a CP sequence counter (`WaitOnAddress`, 1 ms timeout) that the SDK bumps after every guest-visible CP store. It needs rexlego plus an SDK change.
     - (a2) backs off in the hook alone: pause for ~20-50 us, then `SwitchToThread`, then a ~250 us sleep on a high-resolution timer. rexlego only.
   - My earlier (e), a pause plus `SwitchToThread` on each pass, is (a2) with a zero quantum. Agent 9's window-4 sweep (0/125/250/500 us) covers it, so it is no longer a separate item.
   - Output-identical by Agent 9's argument: the loop, its completion test and its exit conditions stay the same; only the poll timing changes. The only guest-visible differences are wall-clock values (dev+22008/22016 and the elapsed value), which already vary run to run.
   - What the hang triage adds to the test plan: a loaded-machine arm, devoffB-bin with attract-long, hook off vs on. Count STUCK-LOCK reports and frames ≥ 5 s, and check that waits whose fence has already passed go straight to the original. The 5 s STUCK-LOCK report stays on as the detector.
   - A recompiler-wide `db16cyc` → pause mapping (Agent 9's (b)/(c)) would also touch every guest spinlock. Agent 9 ranks both below the hook.
5. **Machine: user question 3 (Agent 1, 06:28).** Excluding the run dirs from Defender and stopping FrameView/PresentMon during timing windows is the user's call, and nobody touches either. Together they used about 2-6 cores during these runs.
"""

for old, new in ((OLD_STATUS, NEW_STATUS), (OLD_2, NEW_2), (OLD_45, NEW_45)):
    n = t.count(old)
    if n != 1:
        sys.exit(f'target found {n}x: {old[:60]!r}')
    t = t.replace(old, new)

out = t.encode('utf-8')
NOTE.write_bytes(out)

# Read-back checks.
b = NOTE.read_bytes()
s = b.decode('utf-8')
checks = {
    'no BOM': not b.startswith(b'\xef\xbb\xbf'),
    'no CRLF': b'\r\n' not in b,
    'ends with LF': b.endswith(b'\n'),
    'one alert': s.count('> [!') == 1,
    'no U+FFFD': '\ufffd' not in s,
    'old (e) bullet gone': '**(e)**' not in s,
    'merged item present': 'Design: Agent 9' in s and 'user question 3' in s and 'Staged only' in s,
}
for k, v in checks.items():
    print(('PASS ' if v else 'FAIL ') + k)
for i, line in enumerate(s.split('\n'), 1):
    if '(e)' in line:
        print(f'  (e) at L{i}: {line[:110]}')
print(f'{len(raw)} -> {len(b)} B, {s.count(chr(10))} lines, backup {BAK.name}')
sys.exit(0 if all(checks.values()) else 1)

"""One-off: replace lines 3-11 of perf-notes/agent10-helpers.md (task #17 RESUME, item 1) in place, LF kept."""
import sys

P = r'<workspace>\perf-notes\agent10-helpers.md'
NEW = """> **RESUME (03:58, updated 04:44; session 3, task #17: reviews part 2).** Read-only, at most 2 threads, no builds or game runs, notes only from 08:30. Summary to Agent 1 by ~07:30, then `@@done 17`.
> - **1. nativeB gate.** nativeB-bin staged 04:34 (exe 01C4D5A3…, MANIFEST E5CBF30A…, fingerprint 81d1c3a7…) against `build/agent2/native3d-bin` (exe B90DF683…, fingerprint 335ff2d4…). Write-up: codegen-review \"nativeB gate\".
>   - a. Static: **PASS** (04:43), with Agent 9.
>     - Inputs: `nb/statecmp.py` MATCH (`--full` MATCH too); `nb/sumscheck.py` MATCH.
>     - Generated code: `nb/lrsites.py` PASS.
>     - Binaries: `nb/hookset.py` PASS (181 hooks, same set and objects). Agent 9's mapcmp: same sub_ and alias sets, .text −10.38%. fpcheck PASS (only the 13 codegen inputs differ). warncmp CHECK (2 host-only signatures from identical sources). MANIFEST 149 PASS / 0 FAIL / 34 NOTE.
>     - The fingerprint keys only `<exe dir>/cache/native-pso-recipes.bin` and the trigger-loaded pack. The harness runs from a fresh run dir, so both runs of the pair start cold (`nb/fpscan.py`).
>   - b. Route pair: pending in Agent 8's slot (busy with Agent 5's s0/s1/s2 until ~04:51).
>     - Then run `python build\\agent10\\bgate\\logdiff.py --base <native3d run> --cand <nativeB run>` and `nb/nativelines.py --base … --cand … --out nb/nativelines-native3d-vs-nativeB.txt`, plus `nb/nrows.py` for draw_calls and scenes.
>     - Fail and must-match lists: codegen-review L354-367.
>     - Send the verdict with coverage to 1, 2, 8 and 9 **within 20 min of the logs landing**.
"""

with open(P, 'r', encoding='utf-8', newline='') as f:
    lines = f.read().split('\n')
if not lines[2].startswith('> **RESUME (03:58') or not lines[10].startswith('>   - b. Route pair'):
    print('anchor mismatch:', repr(lines[2][:40]), repr(lines[10][:40]))
    sys.exit(1)
lines[2:11] = NEW.rstrip('\n').split('\n')
with open(P, 'w', encoding='utf-8', newline='') as f:
    f.write('\n'.join(lines))
print('ok; CRLF present:', '\r' in '\n'.join(lines))

#!/usr/bin/env python3
"""Apply the ~05:05 additions to perf-notes/agent6-attract-stalls.md.

- cross-references in the status line, section 6 and section 7;
- the 'proposal for after window 4' note in section 7;
- appends note-s10-s11.md (section 10 S4 items, section 11 run spec).

Single-threaded, read-modify-write of one file. Refuses to run twice
(asserts '## 10.' is absent) and asserts every old string occurs exactly
once. Backs up the original next to this script first.
"""
import hashlib
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NOTE = ROOT / 'perf-notes' / 'agent6-attract-stalls.md'
ADD = HERE / 'note-s10-s11.md'
BAK = HERE / 'agent6-attract-stalls.md.bak-0500'

REPLACEMENTS = [
    # 1. status line
    (
        "Status: **analysis done, 2026-11-22 ~04:30.** No game runs, no builds, "
        "no git writes; all scripts are single-threaded and read-only.",
        "Status: **analysis done, 2026-11-22 ~04:30. §10 (S4 items table, for "
        "Agent 10) and §11 (diagnostic-run spec) added ~05:05 at Agent 1's "
        "request.** No game runs, no builds, no git writes; all scripts are "
        "single-threaded and read-only.",
    ),
    # 2. section 6 intro and item 1
    (
        """Follow-ups, smallest first. None of them is needed for task #16.
1. **Diagnostic run, cvars only.**""",
        """Follow-ups, smallest first. None of them is needed for task #16. §10 turns items 2-4 into an S4 table for Agent 10, and §11 is the run spec for item 1.
1. **Diagnostic run, cvars only** (spec in §11).""",
    ),
    # 3. section 6 item 2
    (
        "give each creation thread its own `DxbcShaderTranslator` (drop the "
        "shared lock at `pipeline_cache.cpp:3185`).",
        "give each creation thread its own `DxbcShaderTranslator` and replace "
        "the global lock at `pipeline_cache.cpp:3185` with a per-shader claim "
        "(§10.1).",
    ),
    # 4. section 6 item 3
    (
        "It only matters for warm boots, so it is minor here.",
        "It only matters for warm boots, so it is minor here (§10.2).",
    ),
    # 5. section 6 item 4
    (
        "4. Not for S4: a non-blocking async mode (don't await creation at "
        "EndSubmission; keep dropping draws until ready). It swaps stalls for "
        "multi-frame pop-in, so it is not output-identical, would have to be "
        "OFF by default, and needs review of how the deferred command list "
        "uses pipeline handles.",
        "4. Not for S4 by default: a non-blocking async mode (don't await "
        "creation at EndSubmission; keep dropping draws until ready). It swaps "
        "stalls for multi-frame pop-in, so it is not output-identical and can "
        "only be an opt-in cvar, OFF by default. In async mode the deferred "
        "command list never sees an unbuilt pipeline, so the change is small "
        "(§10.3).",
    ),
    # 6. section 7: proposal note
    (
        """## 7. What Agent 8's runner would need for a warm-cache arm

1. **Seed:**""",
        """## 7. What Agent 8's runner would need for a warm-cache arm

> [!NOTE]
> **Proposal for after window 4** (Agent 1, 04:36: no runner changes before window 4 has run); sent to Agent 8 as such at ~05:10. For the functional harness, Agent 3's `harness/run-game.ps1 -SeedXenos <dir>` (04:42) already does steps 2-3 for a given seed dir: it copies `*.xsh`/`*.xpso` into `<user>\\cache\\shaders\\shareable`, refuses to overwrite, records sha256 and sizes in run.json `seed_xenos`, captures the storage lines and prints the xpso pipeline count before and after. Seed dir: `build\\agent3\\seed\\devoff2-214` (xsh 160,232 B, xpso 15,420 B = 214 pipelines).

1. **Seed:**""",
    ),
    # 7. section 7 item 6: point at the spec
    (
        "6. Optional: a separate diagnostic arm with `slow_frame_log_ms=50` (§6.1).",
        "6. Optional: a separate diagnostic arm with `slow_frame_log_ms=50` "
        "(§6 item 1; spec in §11).",
    ),
]


def sha16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16].upper()


def main() -> int:
    raw = NOTE.read_bytes()
    add_raw = ADD.read_bytes()
    for name, b in (('note', raw), ('add', add_raw)):
        assert not b.startswith(b'\xef\xbb\xbf'), f'{name}: unexpected BOM'
        assert b'\r\n' not in b, f'{name}: CRLF found'
        assert b.endswith(b'\n'), f'{name}: no final newline'
    text = raw.decode('utf-8')
    add = add_raw.decode('utf-8')
    assert '\n## 10.' not in text, 'already patched (## 10. present)'
    assert add.startswith('## 10. S4 items (for Agent 10)\n'), 'add: bad head'
    assert '\n## 11. Diagnostic run spec' in add, 'add: no section 11'

    for i, (old, new) in enumerate(REPLACEMENTS, 1):
        n = text.count(old)
        assert n == 1, f'replacement {i}: old string found {n} times'
        assert old != new
        text = text.replace(old, new)

    text = text + '\n' + add

    shutil.copy2(NOTE, BAK)
    assert BAK.read_bytes() == raw, 'backup mismatch'
    with open(NOTE, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)

    out = NOTE.read_bytes()
    nl = out.count(b'\n')
    print(f'before: {len(raw)} B sha {sha16(raw)}')
    print(f'after:  {len(out)} B sha {sha16(out)} lines {nl}')
    print(f'backup: {BAK.name}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

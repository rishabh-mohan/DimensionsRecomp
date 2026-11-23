#!/usr/bin/env python3
"""Add the baseline-bin result (attract-base1) to perf-notes/agent6-hang-triage.md.

Fills §8, adds §3.4 (base1 owner loop and dump state), adds B1 to §1/§2/§4, updates the status
line, Bottom line points 1-5, §3.1, §3.3, §5 and §9 items 4 and 6. One-shot and guarded: every
target must occur exactly once; keeps UTF-8 / LF / no BOM / one alert; backs up the note first;
refuses to run while a placeholder is unset.
"""
import pathlib
import re
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
NOTE = HERE.parents[2] / 'perf-notes' / 'agent6-hang-triage.md'
BAK = HERE / 'agent6-hang-triage.md.bak-0720'

# ---- owner-site text (filled in from base1-owner.txt / dumpstacks-base1*.txt) -------------
B1_BOTTOM = (
    "the same render thread (tid 0x17) in a different loop: the game busy-waits on a GPU query, "
    "calling the D3D query GetData (sub_83FB09E8) from sub_82BDCFB8 until it stops returning S_FALSE. "
    "The query completes only when the CP gets past it, and in the dump the CP thread was compiling a "
    "shader in the NVIDIA driver (dxilconv.dll) rather than waiting (§3.4).")
B1_OWNER_HEAD = "a game-side query poll"
B1_OWNER_BULLET = (
    "lr 83FB09F0 is sub_83FB09E8+0x8, the return from the prologue's `bl __savegprlr_14`, like X3's "
    "83FAF188. sub_83FB09E8 is the D3D query GetData, and r3 1 is its S_FALSE (not ready). 82BDD028 is "
    "the polling call in sub_82BDCFB8, called from 82BDC918 (sub_82BDC8E8+0x30) ← 82BAEA7C "
    "(sub_82BAE968+0x114). 83FB0948 (sub_83FB0738+0x210, in the query-issue code) is a stale stack "
    "slot: the dump's host stack goes straight from sub_83FB09E8 to sub_82BDCFB8 (§3.4).")
B1_SITE = (
    "It is the game's busy-wait on a GPU query: sub_82BDCFB8 calls the D3D query GetData (sub_83FB09E8) "
    "until it stops returning S_FALSE, with no yield (§3.4).")
DUMP_NOTE = "read with dumpstacks.py"
DUMP_SENTENCE = (
    "dumpstacks shows the CS still held (lock_count 1, recursion 1, owner 0x30111018), the owner thread "
    "(host TID 4620, REX object F80001A8 as in devoffB) running GetData with 145.6 s of user CPU, and the "
    "CP thread compiling in dxilconv.dll rather than waiting (§3.4).")
B1_CONSEQUENCE = (
    "For §9 item 4: the merged hook on sub_83FAF180 alone would not have covered B1, so the S4 item now "
    "adds the same back-off for this query poll.\n"
    "  - In base1 the CP thread was compiling a shader in the NVIDIA driver at the snapshot, not waiting as "
    "in devoffB and devoff3-warm (§3.4). So on the Xenos path too, pipeline creation on the CP thread can "
    "hold up the render thread while it waits under kGraphicsLock. That links this hold to the #18 "
    "creation stalls (`agent6-attract-stalls.md`).")
S9_B1 = (
    "**Coverage gap found in base1 (§3.4).** The owner there spun in a second loop, the game's query poll "
    "(sub_82BDCFB8 → GetData, sub_83FB09E8), which never calls sub_83FAF180. So the S4 item also needs a "
    "back-off on that loop, under the same OFF-by-default env var. It is output-identical by the same "
    "argument (only the poll timing changes), and the test arm should count reports by owner site "
    "(83FAF188/83FAF200/83FBF868 vs 83FB09F0). Two ways to hook it:\n"
    "      - `REX_HOOK_RAW` on sub_83FB09E8, backing off only when it was called from the blocking site "
    "(lr 0x82BDD028) and the original returned 1 (S_FALSE);\n"
    "      - or a hook on sub_82BDCFB8 itself.")
SAT_TAIL = (
    ", and one of those went to the owner: PSO creation in native3d, the ring wait in devoffB and "
    "devoff3-warm, the query poll in base1.")
# -------------------------------------------------------------------------------------------

DRY = '--dry' in sys.argv  # check the targets only; writes nothing
for k in ('B1_BOTTOM', 'B1_OWNER_HEAD', 'B1_OWNER_BULLET', 'B1_SITE', 'DUMP_NOTE', 'DUMP_SENTENCE',
          'B1_CONSEQUENCE', 'S9_B1', 'SAT_TAIL'):
    v = globals()[k]
    if (not v.strip() or '@@' in v) and not DRY:
        sys.exit(f'placeholder {k} not filled in')

raw = NOTE.read_bytes()
t = raw.decode('utf-8')
if 'attract-base1' in t and 'Pending: Agent 8' not in t:
    sys.exit('already patched')
if b'\r\n' in raw or raw.startswith(b'\xef\xbb\xbf') or not t.endswith('\n'):
    sys.exit('unexpected encoding or line endings')
if not BAK.exists() and not DRY:
    shutil.copyfile(NOTE, BAK)

LINK = '<workspace>/build/agent6/hang/'
E = []  # (old, new)

# status line
E.append((
    "Status: **written 2026-11-22 ~06:20; §9 revised ~06:35 at Agent 1's request.** This covers Part A "
    "(native3d) and the re-scoped Q1-Q4; the reverse-order pair is in §7. The baseline-bin attract runs "
    "(Agent 8's 06:31-07:15 slot) are still pending, and §8 will get their result by ~07:30.",
    "Status: **written 2026-11-22 ~06:20; §9 revised ~06:35 at Agent 1's request; baseline result (§8, §3.4) "
    "added ~07:20.** This covers Part A (native3d) and the re-scoped Q1-Q4; the reverse-order pair is in §7 "
    "and the baseline-bin attract run in §8."))

# Bottom line 1
E.append((
    "1. **Not a deadlock.** All 6 reports in 3 runs are long holds",
    "1. **Not a deadlock.** All 7 reports in 4 runs, the baseline-bin run included (§8), are long holds"))

# Bottom line 2: baseline bullet after the Xenos bullet
XEN = ("   - **devoffB and devoff3-warm (Xenos path):** the guest D3D runtime busy-waits until the emulated "
       "CP's read pointer passes a target (sub_83FBF7D0 → sub_83FAF180). In both dumps, the CP thread is "
       "meanwhile blocked in a host wait inside rexgpu-xenos.\n")
E.append((XEN, XEN + "   - **baseline-bin (base1, Xenos path):** " + B1_BOTTOM + "\n"))

# Bottom line 3
TWO = "   - The function it calls on every pass (sub_83FA2698) is just two loads.\n"
E.append((TWO, TWO + "   - base1's owner (§3.4) polls the D3D query GetData back to back, with no hints at all.\n"))

# Bottom line 4
E.append((
    "4. **Q3: load makes it worse but doesn't cause it.** All 3 runs fall between 05:03 and 05:32.\n"
    "   - The CPU was 97-100% busy then: Defender used 1.2-4.8 cores, PresentMon 1 core and dwm about 1.1 cores.\n"
    "   - During the waits the game got only 1.3-1.8 cores, and the host GPU sat mostly idle (17-29% "
    "utilisation, idle throttle flag set).\n",
    "4. **Q3: load makes it worse but doesn't cause it.** All 4 runs with a report ran on a saturated "
    "machine: 3 between 05:03 and 05:32, and the baseline run at 06:39.\n"
    "   - The CPU was 97-100% busy: Defender used 1.2-4.8 cores, PresentMon 1 core and dwm about 1.1 cores "
    "(base1: 97.7% busy on average, Defender 1.35 cores, max 3.04).\n"
    "   - During the waits the game got only 1.3-1.8 cores (1.5-2.8 in base1), and the host GPU sat mostly "
    "idle (14-29% utilisation, idle throttle flag set).\n"))

# Bottom line 5
E.append((
    "5. **Q4: first seen tonight, but not ruled out earlier.** Only 3 of 89 game.logs contain a report, all "
    "from 05:03-05:32. No earlier run reached these scenes under load, so \"not seen\" doesn't mean \"not "
    "there\". The baseline-bin runs will decide (§8, pending).",
    "5. **Q4: pre-existing: yes.** baseline-bin (game 127e04b + SDK 2897c31, from before tonight's changes) "
    "hit the same STUCK-LOCK in attract-base1, 34.5 s into the attract (H0+34.45 s), with the CPU 97.7% busy "
    "(§8). It has the same CS, the same waiter chain and the same owner thread as devoffB. No run before "
    "05:03 had reached these scenes under load, which is why the 89-log history scan found nothing earlier."))

# §1 table
E.append((
    "and the reverse pair `…055041-bgate-rev-nativeB` and `…055439-bgate-rev-native3d` |",
    "the reverse pair `…055041-bgate-rev-nativeB` and `…055439-bgate-rev-native3d`, and the baseline run "
    "`…063542-attract-base1` (baseline-bin, exe FB922AC9) |"))
E.append((
    "hang-69196.dmp (devoff3-warm) |",
    "hang-69196.dmp (devoff3-warm), hang-60748.dmp (base1, " + DUMP_NOTE + ") |"))
E.append((
    "Output: `dumpstacks-native3d.txt`, `-devoffB.txt`, `-devoff3warm.txt`.",
    "Output: `dumpstacks-native3d.txt`, `-devoffB.txt`, `-devoff3warm.txt`, `-base1.txt`, `-base1-focus.txt`."))
REV = (f"| [revpair.py]({LINK}revpair.py) | For named native runs: totals and top frames. Output: "
       f"[revpair.txt]({LINK}revpair.txt) |\n")
E.append((REV, REV
          + f"| [base_check.py]({LINK}base_check.py) | One run dir: the STUCK lines, run.json, frames of "
            f"4.5 s or more with their H0 offset, and the sampler, samples.csv and gpu.csv rows around the "
            f"report. Used for base1 (§8) |\n"
          + f"| [base_owner.py]({LINK}base_owner.py) | Resolves report addresses to guest functions with one "
            f"map read and prints their generated code: call sites, backward branches. Output: "
            f"[base1-owner.txt]({LINK}base1-owner.txt) |\n"))

# §2
E.append(("## 2. The six reports (Q1)", "## 2. The seven reports (Q1)"))
W1 = ("| W1 | devoff3-warm | 05:32:12.361 | 0x17 / 0x30111018 | 83FBF868 | 1 | 0x22, 0x26d7 / 0x28a9 | "
      "05:32:14.077, hang-69196.dmp (+1.72 s) |\n")
E.append((W1, W1 + "| B1 | base1 (baseline-bin) | 06:39:22.996 | 0x17 / 0x30111018 | 83FB09F0 | 1 | "
                   "0x22, 0x27e / 0x30c | 06:39:26.534, hang-60748.dmp (+3.54 s) |\n"))
E.append((
    "W1's frame is devoff3-warm perf row 6707, 10.05 s.",
    "W1's frame is devoff3-warm perf row 6707, 10.05 s, and B1's is base1 perf row 9726, 8.58 s (H0+34.45 s, §8)."))
E.append((
    "**Waiter: the same functions in all 3 runs.** It is always the Main XThread: guest tid 0x4 in native3d, "
    "0x6 in both Xenos runs.",
    "**Waiter: the same functions in all 4 runs.** It is always the Main XThread: guest tid 0x4 in native3d, "
    "0x6 in the three Xenos-path runs."))
E.append((
    "**Owner: the same loop in both Xenos runs; a different path on native.**",
    "**Owner: the same loop in devoffB and devoff3-warm, " + B1_OWNER_HEAD
    + " in base1, and a different path on native.**"))
NAT = "- **Native.** lr 82BCE244 is the return from the `bl` at sub_82BCE1F8+0x48 (§3.2)."
E.append((NAT, "- **base1 (B1).** " + B1_OWNER_BULLET + "\n" + NAT))
E.append((
    "In all 6 reports the owner was making progress and later released the lock.",
    "In all 7 reports the owner was making progress and later released the lock."))

# §3.1: base1's CP differs
SETTLE = "- **To settle it:** resolve rexgpu-xenos+0xBF7F0 with the matching SDK PDB.\n"
E.append((SETTLE, SETTLE + "- **base1 differs (§3.4):** its CP thread was compiling a shader in the NVIDIA driver "
                           "(dxilconv.dll) at the snapshot, not waiting.\n"))

# §3.3 first bullet
E.append((
    "- The owner's top frames are the D3D draw/submit path on both GPU paths: the ring-buffer wait on Xenos, "
    "PSO creation on native.",
    "- The owner's top frames are the D3D draw/submit path on both GPU paths: the ring-buffer wait on Xenos, "
    "PSO creation on native. In base1 they are the D3D query GetData, polled by the game until the CP catches "
    "up (§3.4), which is a GPU wait too."))

# §3.4 (new), before §4
S34 = (
    "### 3.4 base1: a game-side poll on a GPU query\n"
    "\n"
    "Simplified from the generated code, found with [base_owner.py](" + LINK + "base_owner.py) on the base1 map, "
    "whose partition matches tonight's generated sources: sub_82BDCFB8 is at "
    "`legodimensions_recomp.429.cpp:7890` and sub_83FB09E8 at `.422.cpp:37230`. Output: "
    "[base1-owner.txt](" + LINK + "base1-owner.txt).\n"
    "\n"
    "```text\n"
    "sub_82BDCFB8(this, out, wait)                  // the game's \"get query result\"\n"
    "  q = this->query; if !q: *out = 0; return 1\n"
    "  if GetData(q, out, 4, 0) != 1: goto done     // lr 82BDD000: one non-blocking try\n"
    "  loop (loc_82BDD00C):\n"
    "    if !wait: return 0\n"
    "    if GetData(q, out, 4, 0) == 1: goto loop   // lr 82BDD028: the blocking poll\n"
    "  done: release q (sub_83FB05B0); this[0] = 0; this[1] = -1; return 1\n"
    "\n"
    "sub_83FB09E8(q, out, size, flags)              // D3D query GetData: EVENT, OCCLUSION, TIMESTAMP\n"
    "  if *(dev+11069) & 2: zero *out; return 0     // abort flag\n"
    "  if q was never issued (q+20 & 0x40 clear): return 0x8876086A   // D3DERR_NOTAVAILABLE\n"
    "  if the CP hasn't consumed the ring up to q+24:    // same ring-distance test as sub_83FBF7D0\n"
    "    if q+24 == dev+11036: sub_83FC0C10(dev)         // kick pending commands\n"
    "    return 1                                        // S_FALSE: not ready\n"
    "  OCCLUSION: if a tile slot still holds the -275 marker written at issue: return 1\n"
    "  sum the per-tile counts into *out; q+20 |= 0x80; return 0   // S_OK\n"
    "```\n"
    "\n"
    "- **The loop.** With the wait flag set, sub_82BDCFB8 calls GetData back to back, with no yield, sleep or "
    "SMT hint. Like the ring wait in §3.1, it burns a host core. GetData never calls sub_83FAF180 or "
    "sub_83FBF7D0, so the §9 item 4 hook on sub_83FAF180 would not touch this loop.\n"
    "- **Callers.** 82BDC918 is sub_82BDC8E8+0x30, a cached getter that passes the wait flag through and "
    "stores the result at +12. 82BAEA7C is sub_82BAE968+0x114 (`.300.cpp:7375`), which reads two queries per "
    "item (+16 and +32) and compares each result with -1. The 4-byte result and the per-item pairs point to "
    "occlusion queries. EVENT queries also return 4 bytes, so the type is inferred, not proven.\n"
    "- **83FB0948 is a stale slot.** It is sub_83FB0738+0x210, the return from `bl sub_83FCBF00`. "
    "sub_83FB0738 issues queries (PM4 packets, the -275 markers, q+24) and never calls GetData. The dump "
    "agrees: the owner's host stack goes straight from GetData to sub_82BDCFB8.\n"
    "- **Dump state** (`dumpstacks-base1.txt`, `dumpstacks-base1-focus.txt`):\n"
    "  - CS 0x84959edc **held**: lock_count 1, recursion 1, owner 0x30111018 (REX object 0xF8000270), the "
    "same values as in devoffB and devoff3-warm.\n"
    "  - Owner: host TID 4620 \"XThread120C (F80001A8)\", the same REX object as devoffB's owner. Its RIP is "
    "in sub_83FB09E8. Its host stack unwinds sub_82BDCFB8 ← sub_82BDC8E8 ← sub_82BAE968 ← sub_82BAF2B8 ← … ← "
    "sub_82B74258 ← sub_82A32950, the render-thread entry also seen in native3d (§3.2). User CPU 145.6 s in "
    "a 222 s process.\n"
    "  - CP thread \"GPU Commands\" (TID 96200, user CPU 43.5 s): **not waiting**, unlike devoffB and "
    "devoff3-warm. Its RIP is in dxilconv.dll, Microsoft's DXBC→DXIL converter, with unverified NVIDIA "
    "driver frames (nvwgf2umx.dll) between it and verified rexgpu-xenos frames. The run's toml sets no "
    "`d3d12_*` options, so the SDK's own dxilconv disassembly (`d3d12_dxbc_disasm_dxilconv`) is off: the "
    "driver was compiling a shader on the GPU thread. That fits `PipelineCache::EndSubmission`, which creates "
    "queued pipelines on the GPU thread before it waits, at every submission end, occlusion queries included "
    "(`agent6-attract-stalls.md` §2, read on SDK HEAD). With no rexgpu-xenos PDB, the calling SDK function "
    "can't be named.\n"
    "  - \"D3D12 Pipelines\": 9 threads; 8 idle, 1 in D3DSCache.dll.\n"
    "- **Reading.** The owner waits for the CP to pass the query while the CP compiles, on a saturated "
    "machine. So base1 sits between native3d and devoffB: pipeline creation behind kGraphicsLock as on "
    "native, but one step removed, because the CP thread compiles while the render thread polls.\n"
    "\n")
E.append(("## 4. Machine load (Q3)\n", S34 + "## 4. Machine load (Q3)\n"))

# §4
REVROW = ("| rev-native3d 05:54-05:58 | 0 | 93.4% | 1.60 (max 3.93) | 1.01 | 1.78 | – | cpu-sampler-0554.csv |\n")
E.append((REVROW, REVROW
          + "| base1 (baseline-bin) 06:35-06:43 | 1 | 97.7% avg, 96.4-99.8% around the report | 1.35 avg "
            "(max 3.04) | 1.01 | 2.21 avg, 1.53-2.78 in the hold | util 14-22%, throttle 0x1 (GPU idle), "
            "10.3-11.4 W; P0 with a P5 dip | cpu-sampler-0554.csv (Agent 8's summary), samples.csv, gpu.csv |\n"))
E.append((
    "- **Saturation is common to all three runs.** During the waits the game got 1.3-1.8 cores, and one of "
    "those went to the owner's spin.",
    "- **Saturation is common to all four runs with a report.** During the waits the game got 1.3-1.8 cores "
    "(1.5-2.8 in base1)" + SAT_TAIL))
E.append((
    "about 20-29% utilisation, the idle throttle reason set",
    "about 14-29% utilisation, the idle throttle reason set"))

# §5
E.append((
    "  - No report on a quiet machine means **not observed (load X)**, which is not proof.\n",
    "  - No report on a quiet machine means **not observed (load X)**, which is not proof.\n"
    "- **Result: pre-existing: yes (§8).** attract-base1 had one report, so attract-base2 was skipped by the "
    "rule above.\n"))

# §8
S8 = f"""## 8. Baseline-bin attract run (Q4 result)

**Result: pre-existing: yes.** baseline-bin is from before tonight's changes, and it hit the same STUCK-LOCK in the attract.

- **Run.** `build/agent3/runs/20261122-063542-attract-base1`, run by Agent 8 to the §5 spec at 06:35:44-06:43:48.
  - Bin: `build\\baseline-bin`, game 127e04b + SDK 2897c31 (exe FB922AC9, rexruntime E01D4618). Route attract-long.txt (4D35FAF4), 600 s cap, `-GpuLog`, cold, no args.
  - 91/91 steps with 0 timeouts. The game exited 0 via WM_CLOSE in 1.74 s, 478.9 s after launch.
  - The harness exit is 1 only because of the `[FATAL] Minidump` line. Since Agent 3's runstats.py change (07:02) the run reads RECOVERED HANG (STUCK-LOCK + dump) instead of CRASHED (§9 item 6).
  - attract-base2 was skipped by the §5 rule, because base1 had a report.
- **The report (B1 in §2).** game.log L209-214, at 06:39:22.996 (launch+219.03 s):
  - CS 0x84959edc after 5 s. The owner is guest thread object 0x30111018, tid 0x17, with lock_count 1 and recursion 1: the same object and tid as in devoffB and devoff3-warm. The waiter is 0x6, the Main XThread.
  - The waiter's chain is identical to devoffB's and devoff3-warm's, frame for frame: `82A2A270 ← 82AED6BC ← 82B7132C ← 82FB01A0 ← 82B7995C ← 82AB2108 ← 82FEBDE0`.
  - The owner is at lr 83FB09F0 with r3 1. Its callers are `83FB0948 ← 82BDD028 ← 82BDC918 ← 82BAEA7C`, a different site from X1-X4 and W1. {B1_SITE}
  - SDK GPU line: PM4 0x22 (DRAW_INDX), rptr 0x27e < wptr 0x30c, so commands were queued.
  - `[FATAL] Minidump written to hang-60748.dmp` followed at 06:39:26.534, 3.54 s later. The dump (49,377,574 B) is kept. {DUMP_SENTENCE}
- **Where it falls.** perf.csv has 13,321 rows. H0, the first 2823-draw / 366,575-vertex frame, is row 9371 at perf 165.66 s.
  - The report falls in row 9726, an 8.58 s frame at perf 200.11-208.69 s (H0+34.45 s): the 5 s hold plus the 3.54 s dump.
  - Row 9718 (4.78 s, H0+25.60 s) had no report. Agent 3 counts 18 frames of 1 s or more, and Agent 8's 10 s fps buckets drop to 0.8 at the report.
  - For comparison, devoffB reported at H0+16.4, +63.6, +69.5 and +128.9 s.
- **Load: the same saturated machine as in §4.**
  - The CPU was 96.4-99.8% busy around the report (cpu-sampler-0554.csv, 06:39:12-06:39:32). Over the whole run: 97.7% on average, MsMpEng 1.35 cores (max 3.04), PresentMon 1.01, dwm 1.09 and the game 2.21 (Agent 8).
  - In the hold the game got 1.53-2.78 cores (samples.csv, t 214-219 s), then 0.48-0.53 during the dump.
- **GPU: mostly idle in the hold.** gpu.csv at t 214-219 s: utilisation 14-22%, throttle 0x1 (GPU idle), 10.3-11.4 W, P0 with a P5 dip at 219.1 s. Over the whole run: median utilisation 38%, max 86 °C, power cap in 5.3% of samples, no thermal or hardware slowdown (Agent 8).
- **What it settles.**
  - Q4: the hold predates tonight's changes. Reaching the attract scenes on a saturated machine is enough to get it.
  - The 89-log history scan (§5) found no earlier report because no earlier run reached these scenes under load.
  - {B1_CONSEQUENCE}
"""
E.append((
    "## 8. Baseline-bin attract runs\n\nPending: Agent 8's 06:31-07:15 slot. Results will be appended here by "
    "~07:30, using the reading rule in §5.\n",
    S8))

# §9 item 4 and item 6
TP = ("   - What the hang triage adds to the test plan: a loaded-machine arm, devoffB-bin with attract-long, hook "
      "off vs on. Count STUCK-LOCK reports and frames ≥ 5 s, and check that waits whose fence has already passed "
      "go straight to the original. The 5 s STUCK-LOCK report stays on as the detector.\n")
E.append((TP, TP + "   - " + S9_B1 + "\n"))
E.append((
    "   - Label \"STUCK-LOCK + dump + exit 0\" as RECOVERED HANG. Agent 3 will relabel the runs after the slot, "
    "with Agent 1's OK.\n",
    "   - Label \"STUCK-LOCK + dump + exit 0\" as RECOVERED HANG. **Done by Agent 3 at 07:02** (runstats.py, "
    "`agent3-run-harness.md` §7.4): native3d, devoffB, devoff3-warm and base1 now read \"RECOVERED HANG "
    "(STUCK-LOCK + dump)\", with a \"STUCK-LOCK episodes: N; first at T s\" line. Exit codes are unchanged: "
    "run-game still exits 1 for a dump, and route-report still fails \"no crash\".\n"))

for old, new in E:
    n = t.count(old)
    if n != 1:
        sys.exit(f'target found {n}x: {old[:70]!r}')
    t = t.replace(old, new)
if DRY:
    print(f'dry run: all {len(E)} targets found exactly once; nothing written')
    sys.exit(0)

NOTE.write_bytes(t.encode('utf-8'))

# Read-back checks.
b = NOTE.read_bytes()
s = b.decode('utf-8')
lines = s.split('\n')


def table_ok(text):
    bad = []
    cur = None
    for i, ln in enumerate(text.split('\n'), 1):
        if ln.startswith('|'):
            c = ln.count('|')
            if cur is None:
                cur = c
            elif c != cur:
                bad.append(i)
        else:
            cur = None
    return bad


bad_rows = table_ok(s)
checks = {
    'no BOM': not b.startswith(b'\xef\xbb\xbf'),
    'no CRLF': b'\r\n' not in b,
    'ends with LF': b.endswith(b'\n'),
    'one alert': s.count('> [!') == 1,
    'no U+FFFD': '\ufffd' not in s,
    'no placeholder': '@@' not in s,
    'pending gone': 'Pending: Agent 8' not in s and 'still pending' not in s and '§8, pending' not in s,
    'B1 row once': s.count('| B1 | base1') == 1,
    'base1 row in §4': '| base1 (baseline-bin) 06:35-06:43 |' in s,
    '§8 heading once': s.count('## 8. ') == 1,
    '§3.4 once, before §4': s.count('### 3.4 ') == 1 and s.index('### 3.4 ') < s.index('## 4. '),
    'relabel noted': 'Done by Agent 3 at 07:02' in s,
    'code fences paired': s.count('```') % 2 == 0,
    'section order': [m.group(1) for m in re.finditer(r'^## (\d+)\.', s, re.M)] == [str(i) for i in range(1, 10)],
    'table column counts': not bad_rows,
    'no "6 reports"': 'All 6 reports' not in s and 'six reports' not in s and 'all 6 reports' not in s,
}
for k, v in checks.items():
    print(('PASS ' if v else 'FAIL ') + k + ('' if v or k != 'table column counts' else f' at L{bad_rows}'))
print(f'{len(raw)} -> {len(b)} B, {s.count(chr(10))} lines, backup {BAK.name}')
sys.exit(0 if all(checks.values()) else 1)

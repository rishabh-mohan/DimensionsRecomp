# Applies the S4.2/S4.3 write-up, the RESUME refresh and 3 small S4.1 fixes to perf-notes/agent9-codegen.md.
# All-or-nothing: every anchor must match exactly once, every new line must be ASCII, else nothing is written.
# Writes a backup to build/agent9/s4/notes-backup-<HHMM>.md first. LF only, no BOM. Then runs the byte check.
import datetime
import pathlib
import sys

ROOT = pathlib.Path(r'<workspace>')
NOTES = ROOT / 'perf-notes' / 'agent9-codegen.md'
T = datetime.datetime.now().strftime('%H:%M')

RESUME_TOP = r'''> **RESUME (session 3: task #23 = S4 analysis, done; task #8 done; this block updated {T}).** Task #23's notes (S4.x)
> come right after the run spec, then session 3 (S3.x), session 2 and the recipe; session 1 is archived at the end.
> - **Task #23, session 3 part 3 (Agent 1, about 04:55): S4 analysis. Done: S4.0-S4.3 are written; the summary to
>   Agent 1 and `@@done 23` were sent at about {T}.** Read-only on the trees, <= 2 threads, no builds, no game runs;
>   notes only from 08:30. Mine: `build/agent9/**`, `bench/agent9/**`, this file; up to 1 subagent (1 used: D
>   `4b8ebd88-9a37-497b-b3e5-c7f72eaea7f7`, step 2, finished; report `build/agent9/s4/scene-walk/REPORT.md`).
>   Steps: 0 review Agent 2's S3e clones (OK sent about 05:05, then moot: S3e is off; S4.0); 1 render-thread GPU-wait
>   spin (S4.1); 2 main scene walk (S4.2); 3 the S4 codegen ranking, marking the items that only save CPU while the
>   render thread is GPU-bound (S4.3).
> - **Scan ban (Agent 1, 05:31):** while Agent 8's game queue runs (until about 07:15), no recursive searches or
>   multi-file scans over the SDK, DimensionsRecomp (including `baseline/DimensionsRecomp`) or build trees; only single
>   files, line ranges, or a grep of one named file. After 07:15, only if Agent 1 asks: the S4.2.5 scans,
>   `HighResolutionTimer` users in `include/`, the `db16cyc` site count, and where `host_timer_resolution_ms` is defined.'''

WATCHING = r'''> - **Watching:** nothing (subagent D has finished; no background tasks). `build/agent9/watch-nb.ps1` exited 0 at
>   04:34:06 (nb chain DONE, 0 `FAILED:`; log `build/agent9/logs/watch-nb.txt`); `watch-b.ps1` exited 0 at 02:40.'''

CORRECTION = r'''  - **Correction to S3.8 (its "GPU-wait spin" bullet): this is a fence wait, not a wait for ring-buffer space.** The
    S3.8 conclusion stands: the render thread waits for the command processor, so faster guest code only spins faster.'''

CVAR = r'''  - Agent 11's R3 bundle sets it through the cvar `host_timer_resolution_ms` (S4.1.3 (d)). Where that cvar is defined
    was not looked up (no tree scans before 07:15).'''

S42_S43 = r'''## S4.2 Main scene walk (step 2): done {T}

Subagent D's static analysis, read-only, no runs: `build/agent9/s4/scene-walk/REPORT.md` (sections 0-5; its helper
scripts and `step1.log`-`step7.log` are in the same folder). `TUn:L` refs are A-tree files
(`baseline/DimensionsRecomp/rexlego/generated/default/legodimensions_recomp.n.cpp`); the walk's guest code is the same
in devoff2, native2 and native3d. The question is Agent 7's n-prof vs a-prof result: Main busy +2.40 ms/f, of which
+1.99 is the sub_82AFAB68 -> sub_82AF9BC0 subtree, 1.006 (13 samples) -> 2.992 (54) ms/f
(`perf-notes/agent7-present.md:413-436` at 05:35; D's `:219-223` refs went stale when Agent 7 edited the file).

### S4.2.1 What the walk is, and what sets its per-frame work

- **It is the UI/HUD layer render, not a 3D scene graph.** The main-loop body sub_82FEB7B8 calls sub_82AFAB68 once per
  iteration (lr 0x82FEBCC0, TU59:14407-14409), and sub_82AFAB68 keeps its own nesting counter (0x8491D674). So one
  depth-0 call is one Main frame.
- **The chain:**
  1. sub_82AFAB68: two loops over the 15 slot pointers at 0x8491D6E0 (TU210:6949-7110, :7224-7336), so at most about
     30 calls of sub_82AF9BC0. They are gated by each slot's active byte p+4040, its mode p+120 and the mode-1 enable
     0x84959FA0.
  2. sub_82AF9BC0, per slot, reaches sub_82FCC500 through an indirect call (hyp, from the profile tree).
  3. sub_82FCC500: while the UI skip counter 0x849F5EF0 is > 0, it decrements it and returns 7 without drawing
     (TU173:11095-11110).
  4. sub_82FCB308: the scene list. Each scene that passes the filters gets scene->vtbl[56] (TU220:13370-13588). The
     loop runs under the lock sub_82A2A260 (lr 0x82FCB474).
  5. sub_82F050B0, per scene: an early exit (sub_82EF4338) and an empty-lists skip, then either two-layer mode (when
     sub_82FBC4D8(*(0x849F5F14)) != 0) or 7 layers, with layer 2 skipped while 0x849E21D0 > 0 (TU340:12582-12840).
  6. sub_82EF8C18, per layer list: a linked list accessed by index, so about n^2/2 hops, and element->vtbl[324] per
     element (TU230:12578-12630).
  7. sub_82F0CCD8, recursive, per element: the only prune is node->vtbl[336] (TU41:10872-10890). Then come a matrix
     compose, 4 more virtual calls, and the children from the iterator that sub_82F0B200 builds (lr 0x82F0CDEC).
- **Text is laid out again on every draw.** sub_82EFE948 calls sub_82EF3B38 -> sub_82EF3180 with no condition
  (TU45:12697-12699): there is no cached layout and no dirty flag. Each call opens a 15,152-byte frame
  (TU34:12285-12294), memsets 13,199 bytes through the memset hook (TU34:12430-12451), measures the string (a
  binary-tree search per glyph pair in sub_82B61580, probably kerning; TU391:7223-7309), and emits the glyphs.
- **Only guest UI state sets the work:** the active slots and their modes, the scenes that pass the filters, the layer
  mode, the list lengths, the visible elements, and the text elements and their lengths. The skip counters 0x849F5EF0
  and 0x849E21D0 and the two-layer switch 0x849F5F14 turn large parts on or off.
- **Nothing on the chain reads a timer, fence, query, vblank or frame delta.** The event object the main loop passes
  down has no time field (TU59:14367-14397). Timing could get in only indirectly: through vtbl[336] or animation state
  in the element classes, or through whatever arms the skip counters.
- **Who writes the switches:**
  - 0x849E21D0: sub_82EFC738 copies *(0x849D36F8) into it when its r27 == 2 (TU129:12296-12307); the walk decrements
    it (TU340:12815).
  - 0x849F5F14: only sub_82FD7DA8 (TU240:14069). About 70 functions read it.
  - 0x849F5EF0: the only lis-addressed store is the decrement (TU173:11106). The arming store uses a computed address,
    so finding it needs a scan (S4.2.5).

### S4.2.2 Native vs Xenos: nothing different reaches the walk

- No query, fence, ring, vblank, resolve or device-state hook is reachable by direct calls within depth 5
  (step6.log:60-82).
  - Native GetData returns real counts (`rexlego/src/gpu_native/queries.cpp:172-194`), but the walk can't reach it;
    it reaches only ReleaseQuery, rarely.
  - It does reach InvalidateGpuCache, which native makes an empty function (`hooks_device.cpp:171-175`). So native is
    cheaper there, not dearer.
  - Limit: the search doesn't follow the 159 (UI/text subtree) / 333 (whole walk) indirect call sites. The native
    profile shows no gpu_native frame under the walk (`build/agent7/prof/an-main-tree-afab.txt:65-114`).
- **Host code inside the walk costs about 0.28 ms/f:** 5 of n-prof's 54 samples are hook leaves (memset 3, memcpy 1,
  the native-only heap-journal free hook 1). memset and memcpy are hooked in both builds and scale with the call count.
  The journal hooks run while `native_scene_diagnostics` is true, its default (kInitOnly,
  `rexlego/src/native_skin_diagnostics.cpp:14-16`). The other ~49 samples (~2.7 ms/f) are guest code.
- **Frontend confound: nil.** D left this to Agent 7; I checked it at 05:45-05:49.
  - `settings_native_hooks.cpp` is compiled only with LEGODIMENSIONS_NATIVE_GPU (:1, :240), and the cvar
    `native_settings_frontend` is defined inside it (:16). So devoff2 has no native-frontend code, and "frontend on in
    a-prof" (agent7-present.md:372) is only a runner toml value that nothing reads.
  - n-prof (`build/agent8/matrix/20261122-0357/runs/0405-n-prof-r1`, native2-bin) ran with
    `--native_settings_frontend=false` (run.json:68). With that, GetBridge returns null (:84), and the hooks call
    `__imp__` and return (for example :140-147).
  - So both runs drew the guest's own frontend.

### S4.2.3 H1 / H2 / H3

- **H1, more work per frame: favoured.**
  - The walk grew x3.0 and its text part about x3.6, while the rest of Main grew only x1.16
    (agent7-present.md:418-432). A uniform slowdown would hit all of Main's guest code alike.
  - sub_82B61580 is a pure guest leaf with no calls, and it went from 0 to 5 samples. No hook can change its cost per
    call.
  - The same subtree is 1.006 vs 0.314 ms/f in two devoff captures (agent7-present.md:433), so UI state alone moves
    it 3x.
- **H2, the same calls but slower:** about 0.3 ms/f of direct host time. A uniform effect (cache, clock) is bounded at
  about 16% by the rest of Main.
  - In a-prof, Main waits 10.37 ms/f in a guest critical section entered through sub_82A2A260
    (agent7-present.md:456), the walk's lock function. The busy-only tree can't tell whether the walk's call site
    (lr 0x82FCB474) is the one; the probe's lock_ns column can.
- **H3, a native-only branch:** the candidates are the skip counters, the two-layer switch, the sub_82EF4338 early
  exit, the empty-lists skip and the slot modes. None reads a GPU value, so H3 needs UI state that depends on timing.
  n-prof and a-prof ran at about the same fps (70.8 vs 67.7), so the frame rate alone can't be that timing.
- **Verdict:** H1 is most likely, with about 0.3 ms/f of H2 on top. Static reads can't exclude H3. The probe settles
  it with one count-only run per build.

### S4.2.4 Call-count probe (REPORT section 3; spec only, nothing built)

- **Files:**
  - a new `rexlego/src/scene_walk_probe.cpp` (+ .h);
  - a CMake option `LEGODIMENSIONS_SCENE_WALK_PROBE`, default OFF, in a block after `CMakeLists.txt:154` (the
    pattern at :143-154);
  - one `#ifdef`'d Add() line in each of the memset and memcpy hooks (`native_memops.cpp:166-185`) and the native
    alloc/free hooks (`native_skin_diagnostics.cpp:176-217`), instead of second hooks (those would be duplicate
    symbols). devoff2 doesn't build that file, so there the probe hooks alloc/free itself, under
    `#ifndef LEGODIMENSIONS_NATIVE_GPU`.
- **Gates:** with the option OFF there are no hook symbols. At run time `LEGO_SCENE_WALK_PROBE=<csv path>` turns it
  on; unset or 0, every wrapper just calls `__imp__`. `LEGO_SCENE_WALK_PROBE_TIMING=0` and `_LEAVES=0` drop the QPC
  columns and the leaf counters.
- **Hooks:** pass-through `REX_HOOK_RAW` wrappers in the style of `tt_lock_trace.cpp:12-14, 105-122`, on 18 targets
  that are unhooked in both builds (step6.log:24-54). The counters are thread_local and count only while the walk
  runs.
- **Frame boundary:** one depth-0 call of sub_82AFAB68 on Main. Swap can't be used: in native it is a hook on the
  render thread, and in devoff it is guest code.
- **Columns** (REPORT 3.3): slot modes; ui_calls and ui_skip; screens; scenes; scene_early; two_layer; layer2_skip;
  lists, list_n and list_hops; nodes and max_depth; visible; text_elems; text_calls and text_chars; measure_calls;
  glyph_calls; 4 leaf counts; memset, memcpy, alloc and free counts; walk_ns, tree_ns, text_ns and lock_ns; and the 4
  switch globals at frame end.
- **Output:** one CSV row per frame (CREATE_NEW; a 64 KB thread_local buffer, so no syscall per frame) and one log line
  every 600 frames. Cost < 0.1 ms/f. The count-only run (TIMING=0) is the clean H1 test.
- **Builds and runs:** Agent 2 builds devoff2-probe (NATIVE_GPU=OFF) and native3d-probe (ON); guest codegen doesn't
  change. Same route and capture window (frames N..N+1800 after the route marker); native with
  `--native_settings_frontend=false`; one count-only and one timed run per build; then capped vs uncapped, to see
  whether the counts follow the frame rate. How to read the result: REPORT 3.8.
- **Needs:** Agent 1's grant for rexlego (written by me or Agent 2), Agent 2's build, Agent 10's review, slot runs.

### S4.2.5 Zero-build A/Bs, items not proposed, scans after 07:15

- **Zero-build A/Bs on native3d** (profile runs in Agent 8's slot, only if Agent 1 wants them):
  - n0: `--native_scene_diagnostics=false`. If the walk drops by more than 0.2 ms/f, default it to false in perf
    builds.
  - n1: `LEGO_NATIVE_MEMOPS=0` (`native_memops.cpp:19-22`), in both builds.
  - Optional: `LEGO_NATIVE_LIGHT_MARKERS=0`.
  - **Limit:** at the slot's 1.3-1.7 sampler rounds/s the walk gets about 54 samples per run (0.055 ms/f each), so
    2se on a run-vs-run difference is about 1.1 ms/f. These runs can catch only a large effect; the probe's walk_ns
    is the real test.
- **Not proposed now:** caching the text layout, or an O(n) replacement for sub_82EF8C18. Both change how guest code
  runs; the O(n) walk is output-identical only if no vtbl[324] callback edits the list. Revisit only if list_hops or
  text_calls turn out large, and after the vtable dump.
- **Scans for after 07:15** (REPORT section 4):
  - who arms 0x849F5EF0 (`lis -31585` + `addi 24304`, or stores through a base near 0x849F5EC0);
  - the callers of sub_82EFC738 and sub_82FD7DA8;
  - a vtable dump for vtbl[336], [324] and [56] (does the visibility test read timers or animation state?);
  - the 159/333 indirect call sites (or rely on the probe).
- **My spot-checks of D's claims (A tree), all confirmed:**
  - TU173:11095-11110: 0x849F5EF0 > 0 -> decrement, return 7;
  - TU34:12285-12294 and :12430-12451: the 15,152-byte frame; r5 = 13199, then sub_83E46040 at lr 0x82EF32B8;
  - TU41:10872-10890: vtbl[336] at lr 0x82F0CCFC; low byte 0 -> return;
  - TU230:12578-12630: walk i steps from the head, then element->vtbl[324](element, 0x847BC800) at lr 0x82EF8C84;
  - TU45:12697-12699: `bl 0x82EF3B38` right after the argument stores.

## S4.3 S4 codegen ranking (step 3): done {T}

S3.8's list, re-ranked with S4.1 and S4.2. Every codegen item needs my SDK codegen grant back, a regen, Agent 2's full
rebuild, Agent 10's review and a game gate. Stage B/C also waits until Stage A passes the full game gate (B passed only
the front-end gate, S3.6).

**Who can gain what:**
- **devoff/PM4 builds (devoff2, devoffB):** GPU Commands / the CP sets the frame (S3.8, S4.1). In a-prof, Main waits
  10.37 ms/f in a guest critical section while the render thread is busy, and the render thread spends 13.0 ms/f in
  the fence spin (agent7-present.md:442-456; S4.1.1). So guest codegen saves CPU and power only; fps can move only
  through power headroom.
- **native builds (native3d, nativeB):** there is no fence spin. BlockOnFence becomes `HostDevice::Synchronize`
  (`rexlego/src/gpu_native/hooks_device.cpp:196-200`) and KickOff returns a scratch marker (:277-287). n-prof's render
  thread waits in a kernel wait (sub_83FA6020) and otherwise runs SwapHook, BindShader and DrawVertices
  (agent7-present.md:457-459). Main is busy in 42.7% of rounds (a-prof 24.6%), render waits on Main 1.05 ms/f
  (:443, :458), and Main is the busier thread in timing (5.31 vs 4.94 ms/f, :504). So Main savings can move native
  fps, once Agent 7's render-thread items land (:492-509).
- **A saving inside the render spin is worth nothing in either regime.** While the thread spins, it only polls
  faster. After (a1)/(a2) it polls a few times per wait, so the per-poll cost stops mattering.

**Marks:** [spin] = the measured saving is inside the devoff render spin: no CPU, no fps. [main] = Main-thread guest
code: real CPU, and fps is possible on native. [all] = every guest thread: real CPU.

1. **Stage B/C** (`non_argument_as_local` + `non_volatile_as_local`, together; S2.1; risk high: the setjmp/longjmp and
   SEH review comes first). [main] [all], but its only profile evidence is [spin].
   - S3.8 based it on about 2 ms/f of `__savegprlr_29`/`__restgprlr_29` on the render thread. All of that is spin
     time. `__savegprlr_29` (self 1.16) sits inside sub_83FAF180 (inclusive 9.98 = self 7.97 + sub_83FA2698 0.85 +
     1.16). `__restgprlr_29` (inclusive 1.08, `__chkstk` 0.23 of it) sits inside sub_83FBF7D0 (13.00 = self 1.94 +
     9.98 + 1.08). Source: `build/agent9/prof/ab-render-a9.txt:75-81, 100, 115-117`. So those 2.2 ms/f are worth 0.
   - Main has almost no save/rest samples: one each of `__savegprlr_27` and `__restgprlr_14`, 0.08 ms/f each
     (`ab-main-a9.txt:78, 169`). Main would gain only from fewer ctx loads and stores of r0/r2/r11/r12/f0/v32-v63 and
     the non-volatiles, for example in tight loops like the walk's hop loop (TU230:12592-12613).
   - Size: unmeasured. B's Stage A set moved Main's guest leaves by -0.51 ms/f (2se 1.28, S3.8); Stage B/C adds the
     rest of S2's -6.47% (all 6 localization keys).
   - It stays first because it is the only item that touches every function on Main.
2. **Flush-mode dataflow across labels** [all]. Unchanged (S3.8 item 4).
3. **PGO devirtualization of `bctrl` sites** [main] [all]. The walk makes 6 virtual calls per drawn element
   (vtbl[336], [340], [332], [344], [348], and [56] per child) and one per list element (vtbl[324]). But indirect
   dispatch is already lean (session 1 notes), so each call saves only a few ns. Sizing it needs an indirect-target
   profile, the probe's nodes/list_n counts and the vtable dump.
4. **Guest memory macro experiments** [all] (`volatile` and the phys-offset compare on every access; session 1, item
   8; `pch_h.inja:128,135-145`). Every hop of the walk's list loop is a guest load. Measured experiment only (risk
   high for volatile, medium for the offset).
5. **`[[unlikely]]` on divide guards** [all]. Unchanged.
6. **The redundant mfmsr/mtmsrd fence** [all]. Unchanged.
7. **musttail for indirect tail calls** [all]. Unchanged.
8. **(b) `db16cyc` -> `_mm_pause`** [spin] (S4.1.3 item 4; half of S3.8 item 2). devoff/PM4 only. It saves no
   OS-visible CPU, only power and HT-sibling time, and it is moot once (a1)/(a2) land.
9. **(c) a codegen spin policy** [spin] (S4.1.3 item 5; the other half of S3.8 item 2). devoff/PM4 only. (a1)/(a2) do
   the same job better, because the hook knows the wake condition.
- **Never for LEGO now: skip_lr** (host code reads `ctx.lr`, S2.2). Unchanged (S3.8 item 3).

**Not codegen, but this is where the real savings are:**
- devoff/PM4: (d) Agent 11's timer change (W4b arm d11t, about -0.85 core), then (a1) or (a2) (about -0.85 or -0.7 to
  -0.8 core); see S4.1.3.
- native: Agent 7's render-thread items (agent7-present.md:492-509), and the scene-walk probe (S4.2.4) before any
  Main fix.
- **Measuring codegen items:** on devoff fps can't move, so the metric is CPU per frame from window-4 timing. The
  slot's profiler (1.3-1.7 rounds/s) can't resolve effects under about 10% (S3.8).'''


def main():
    raw = NOTES.read_bytes()
    if raw.startswith(b'\xef\xbb\xbf'):
        sys.exit('FAIL: BOM present before edit')
    text = raw.decode('utf-8')
    if '\r' in text:
        sys.exit('FAIL: CR present before edit')
    lines = text.split('\n')

    def idx_eq(s):
        hits = [i for i, l in enumerate(lines) if l == s]
        if len(hits) != 1:
            sys.exit('FAIL: %d exact hits for %r' % (len(hits), s[:80]))
        return hits[0]

    def idx_start(s):
        hits = [i for i, l in enumerate(lines) if l.startswith(s)]
        if len(hits) != 1:
            sys.exit('FAIL: %d prefix hits for %r' % (len(hits), s[:80]))
        return hits[0]

    def new(block):
        out = block.replace('{T}', T).split('\n')
        for l in out:
            if any(ord(c) > 127 for c in l):
                sys.exit('FAIL: non-ASCII in new line %r' % l[:80])
        return out

    # Collect (start, end_inclusive, new_lines); apply bottom-up.
    edits = []
    a = idx_eq('## S4.2 Main scene walk (step 2): subagent D, report due 06:20')
    b = idx_eq('## S4.3 S4 codegen ranking (step 3): pending')
    if b != a + 2 or lines[a + 1] != '':
        sys.exit('FAIL: stub layout')
    edits.append((a, b, new(S42_S43)))
    c = idx_eq('  - The name of the cvar that feeds it: to look up after 07:15.')
    edits.append((c, c, new(CVAR)))
    d = idx_start('  - **Correction to S3.8 (lines 396-397): this is a fence wait, not a wait for ring-buffer space.**')
    if not lines[d + 1].startswith('    stands: the render thread waits for the command processor'):
        sys.exit('FAIL: correction layout')
    edits.append((d, d + 1, new(CORRECTION)))
    e = idx_eq('## S4.1 Render-thread GPU-wait spin (step 1): done 05:50')
    edits.append((e, e, ['## S4.1 Render-thread GPU-wait spin (step 1): done 05:40']))
    f = idx_start('> - **Watching:** subagent D (task #23 step 2, report due 06:20)')
    if not lines[f + 1].startswith('>   log `build/agent9/logs/watch-nb.txt`)'):
        sys.exit('FAIL: watching layout')
    edits.append((f, f + 1, new(WATCHING)))
    g = idx_start('> - **State (05:05): task #23 step 0 done, steps 1-3 open; task #8 complete (`@@done 8` 04:46).**')
    old_g = lines[g]
    new_g = old_g.replace('> - **State (05:05): task #23 step 0 done, steps 1-3 open; task #8 complete',
                          '> - **State (%s): task #23 done (S4.0-S4.3); task #8 complete' % T, 1)
    edits.append((g, g, [new_g]))
    h0 = idx_start('> **RESUME (session 3: task #23 = S4 analysis, in progress;')
    h1 = idx_eq('>   07:00, then `@@done 23: ...`.')
    if h0 != 0 or h1 != 10:
        sys.exit('FAIL: RESUME top layout %d..%d' % (h0, h1))
    edits.append((h0, h1, new(RESUME_TOP)))

    edits.sort(key=lambda x: x[0])
    for i in range(1, len(edits)):
        if edits[i][0] <= edits[i - 1][1]:
            sys.exit('FAIL: overlapping edits')
    backup = ROOT / 'build' / 'agent9' / 's4' / ('notes-backup-%s.md' % T.replace(':', ''))
    backup.write_bytes(raw)
    for s, e2, nl in sorted(edits, key=lambda x: -x[0]):
        lines[s:e2 + 1] = nl
    out = '\n'.join(lines)
    NOTES.write_bytes(out.encode('utf-8'))
    print('WROTE %s (%d edits, T=%s); backup %s' % (NOTES, len(edits), T, backup))

    # Byte check.
    raw2 = NOTES.read_bytes()
    t2 = raw2.decode('utf-8')
    L = t2.split('\n')
    print('bytes %d lines %d CR %d BOM %s' % (len(raw2), len(L), raw2.count(b'\r'), raw2.startswith(b'\xef\xbb\xbf')))
    sess3 = [i for i, l in enumerate(L) if l.startswith('# Session 3: build B support')]
    cut = sess3[0]
    head_non = sum(1 for l in L[:cut] for ch in l if ord(ch) > 127)
    tail_non_bytes = sum(len(l.encode('utf-8')) - len(l) for l in L[cut:])
    print('non-ASCII chars before line %d: %d; non-ASCII extra bytes from there on: %d' % (cut + 1, head_non,
                                                                                        tail_non_bytes))
    long_lines = [(i + 1, len(l)) for i, l in enumerate(L[:cut]) if len(l) > 120]
    print('lines > 120 chars before line %d: %s' % (cut + 1, long_lines[:40]))
    for i, l in enumerate(L[:cut + 1]):
        if l.startswith('## S4') or l.startswith('### S4') or l.startswith('# Session'):
            print('%d: %s' % (i + 1, l))


if __name__ == '__main__':
    main()

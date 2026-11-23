# Scene-walk (sub_82AFAB68 subtree): static analysis, native-vs-Xenos check, probe spec

Agent 9 helper, session S4, 2026-11-22 ~06:00. Static and read-only: no builds, no runs.

Notation:
- `TUn:L` means `baseline/DimensionsRecomp/rexlego/generated/default/legodimensions_recomp.n.cpp`, line L. The guest code is identical in devoff2 and native3d.
- `src/X` means `DimensionsRecomp/rexlego/src/X`.
- `stepN.log` files are in this folder (`build/agent9/s4/scene-walk/`).
- "lr 0x..." is the return address the generated code stores in `ctx.lr` just before a call. It identifies the call site, so a hook can test it.
- `vtbl[N]` is the function pointer at byte offset N in the object's vtable (the generated code loads `*(*(obj)+N)`).
- "(hyp)" marks a hypothesis.
- Profile numbers come from Agent 7: `perf-notes/agent7-present.md` and `build/agent7/prof/an-main-tree-afab.txt`.

## 0. Summary

1. **The walk is the UI/HUD layer render, not a 3D scene graph.**
   - The recursive sub_82F0CCD8 draws a UI element tree. It gets each node's children from an iterator built by sub_82F0B200 (TU41:11016-11018).
   - The only per-node prune is one virtual call, `node->vtbl[336](node)` (TU41:10872-10890).
   - Nowhere on either chain is there a frustum, distance/LOD, occlusion-query, fence, timer or frame-delta test.
2. **Text is laid out again on every draw.**
   - sub_82EFE948 calls sub_82EF3B38, which forwards to sub_82EF3180, with no condition (TU45:12697-12699, TU266:12394).
   - Each sub_82EF3180 call:
     - opens a 15152-byte stack frame (TU34:12291);
     - memsets 13199 bytes through the memset hook (TU34:12430-12451);
     - measures the string, with a per-glyph binary-tree search in sub_82B61580;
     - emits the glyphs.
3. **Guest UI state alone sets the per-frame work.** The factors are:
   - active slots (p+4040, p+120);
   - scenes that pass the filters;
   - non-empty layers (7, or 2 in two-layer mode);
   - list length n (each layer list is walked in O(n^2));
   - visible elements, text elements, and string lengths.

   Three globals switch big parts on or off:
   - the frame-skip counters 0x849F5EF0 and 0x849E21D0;
   - the two-layer switch 0x849F5F14.
4. **The native renderer hands this code nothing that differs from Xenos.**
   - No query, fence, ring, vblank, resolve or device-state read is reachable from the walk by direct calls (step6.log:60-82).
   - Native query GetData returns real results, not a constant (src/gpu_native/queries.cpp:172-194).
5. **Host code inside the walk is small.**
   - Some hooks run in both builds: memset, memcpy, markers, atomics, lock_elide.
   - Native only: the skin-diagnostics heap-journal free/alloc hooks. Their cvar defaults to true.
   - In the native profile, ~5 of 54 samples (~0.28 ms/f) are host hook leaves. The rest of the +1.99 ms is guest code.
6. **Verdict on the hypotheses.**
   - H1 (more work per frame) is favoured.
   - H2 (same calls, slower) directly explains about 0.3 ms/f at most, plus unknown cache effects.
   - H3 (a native-only branch) has concrete candidates: the skip counters, the two-layer switch, and an early exit.
   - Static analysis cannot settle which. The probe in section 3 can.

## 1. What decides the walk's per-frame work

### 1.1 Entry: once per main-loop iteration

- The main loop body is sub_82FEB7B8 (TU59:13665-14665). Each iteration it:
  1. builds an event object on its stack at r31+160 (TU59:14367-14397):
     - word 0x823B6FC4 at +0 (TU59:14367-14380);
     - r28 at +4 (TU59:14370);
     - the boolean (u8 r23+952 != 0) at +20 (TU59:14383-14397). The addic/subfe pair there is the "!= 0" idiom, not a time delta.
  2. calls sub_82FCB148 (lr 0x82FEBCB0, TU59:14398-14400);
  3. stores &event to 0x849F5EC8 (TU59:14401-14406);
  4. calls sub_82AFAB68 exactly once (lr 0x82FEBCC0, TU59:14407-14409).
- sub_82AFAB68 keeps its own nesting counter at 0x8491D674 (TU210:6886-6891, TU210:7346-7353).
- So one depth-0 call of sub_82AFAB68 is one game frame on the Main thread. That is the probe's frame boundary.

### 1.2 Chain (a): sub_82AFAB68 -> sub_82AF9BC0 -> sub_82FCC500 -> sub_82FCB308 -> sub_82F050B0 -> sub_82EF8C18 -> sub_82F0CCD8

**(a1) sub_82AFAB68 (TU210:6855-7451): the two slot loops**
- Loop 1 (TU210:6949-7110) walks 15 slot pointers from the array at 0x8491D6E0 (r28). For each non-null slot p:
  - it calls `p->vtbl[8]` (TU210:6958-6968);
  - it calls `sub_82AF9BC0(p)` (lr 0x82AFAC50, TU210:6986-6990) only if u8 p+4040 != 0 and u32 p+120 == 0 (TU210:6970-6985).
- Loop 2 (TU210:7224-7336), for slots with u8 p+4040 != 0 (TU210:7250-7254):
  - It writes p+4016 (TU210:7255-7256).
  - If p+120 == 2: it calls `sub_82AF9BC0` (lr 0x82AFAE40, TU210:7265-7269), then sets p+4036 = *(r23+27368) (TU210:7270-7273).
  - If p+120 == 1 and *(0x84959FA0) != 0: it calls `sub_82AF9BC0` (lr 0x82AFAE6C, TU210:7283-7293), then `sub_82B6FBB8` (TU210:7298-7300).
  - If p+120 == 1 and *(0x84959FA0) == 0: it branches to loc_82AFAE84 instead (TU210:7287-7288).
- Bound: 15 slots per loop, so at most ~30 calls of sub_82AF9BC0 per frame. No time limit.
- Inputs:
  - the slot mode p+120 (0/1/2);
  - the active byte p+4040;
  - the mode-1 enable 0x84959FA0. It is written by sub_82B76398 (TU27:7451), sub_82B784A0 (TU109:7519), sub_82B76958 (TU223:7254) and sub_82B77A28 (TU423:8885). The walk reads it only at TU210:7284 (step7.log:15-23).

**(a2) sub_82AF9BC0 (TU216:6784-8970): per-slot update and draw**
- It calls engine profiler section markers sub_82A3E238/sub_82A3E2B8 (TU216:8750-8770, TU216:8951-8955). Both builds hook those markers (src/native_markers.cpp:63-71).
- It makes indirect calls:
  - through the slot function pointers p+84 (TU216:8644, TU216:8678) and p+88 (TU216:8765);
  - through `vtbl[28]` (TU216:8749).
- It calls sub_82AF52B0 when p+120 == 0 (TU216:8777).
- There is no direct `bl` to sub_82FCC500. It is reached through one of these indirect calls (hyp; the profile tree shows sub_82FCC500 below sub_82AF9BC0).

**(a3) sub_82FCC500 (TU173:11070-11155): UI frame-skip counter**
- It first calls the marker sub_82A3E238 (TU173:11092-11094).
- It reads 0x849F5EF0 (TU173:11095-11098). If the value is > 0, it decrements it and returns 7 without drawing (TU173:11099-11110).
- Otherwise:
  - it stores r30 into *(0x849F5EC8)+24 (TU173:11122-11125);
  - it calls `sub_82FCB308(r3 = *(0x849F5EC4), r4 = &{5}, r5 = *(0x849F5EC8))` (lr 0x82FCC56C, TU173:11112-11132);
  - it then calls `sub_82FBBF10` (TU173:11133-11135).
- Writers of 0x849F5EF0: the only lis-addressed store in the whole image is that decrement (TU173:11106; step7.log:55-57). Whatever arms the counter uses a computed address. That search is a multi-TU scan, listed in section 4 to run after 07:15.
- Writers of 0x849F5EC4: sub_82FD7128 (TU37:13339) and sub_82FD6FA0 (TU416:13567) (step7.log:28-30).

**(a4) sub_82FCB308 (TU220:13119-13627): the screen/scene list**
- It selects the viewport and mode (TU220:13152-13259), then may skip early based on a table entry (TU220:13261-13288).
- It locks `sub_82A2A260` on an element of an array based at r24 (TU220:13305-13321), and unlocks at TU220:13600.
  - The lock call site is lr 0x82FCB474.
  - native_lock_elide does not hook sub_82A2A260 (its hooks are at src/native_lock_elide.cpp:322-2326; step6.log:19).
- Its scene loop is TU220:13370-13588. A scene is filtered out by any of:
  - sub_82FBC588, or bit 31 of *(r30+16) (TU220:13419-13435);
  - a null scene (r29);
  - r29+1776 or sub_82FBBB50 (TU220:13441-13473);
  - `vtbl[72]` (TU220:13475-13491);
  - sub_8302A790, sub_8302A7A8, sub_8302A7D0 or sub_8302A7E8 (TU220:13492-13543).
- For each scene that survives, it stores the scene in 0x849F5EC0 and calls `scene->vtbl[56]` (TU220:13572). On the profiled path that target is sub_82F050B0 (hyp, from the profile tree).
- Bound: the length of the scene list. No counter, no time limit.

**(a5) sub_82F050B0 (TU340:12556-12900): per-scene layers**
- **Early exit:** when `sub_82EF4338(*(r4+24))` returns nonzero (lr 0x82F050E4, TU340:12582-12598).
- **Empty-lists skip:** if `sub_82EFB260(this)` returns 0 (lr 0x82F050F8, TU340:12601-12609), it checks the counts at +8 of the 6 lists at *(this+84)+{0,12,...,60} (TU340:12610-12628). If all are empty, it skips the layer walks (to loc_82F052B0, TU340:12629-12637).
- **Two-layer mode:** it loads r3 = *(0x849F5F14) and calls `sub_82FBC4D8(r3)` (lr 0x82F05218, TU340:12767-12779). If the result is nonzero:
  - it walks only the lists at +12 and +60 with `sub_82EF8C18` (lr 0x82F05230 and lr 0x82F0523C; TU340:12780-12793);
  - it skips sub_82F02A80 (TU340:12794-12795).
- **Normal mode:** 7 layers, r30 = 0..6, list = *(this+84) + 12*r30 (TU340:12796-12840).
  - While 0x849E21D0 > 0, layer 2 is skipped and the counter is decremented (TU340:12804-12817).
  - Each list goes to `sub_82EF8C18` at lr 0x82F05280 (TU340:12829-12831).
  - Then it calls `sub_82F02A80` (lr 0x82F05298, TU340:12843-12845).
- **Tail:**
  - sub_82AEA3E0, sub_82B5A108 and sub_82AEA438 (TU340:12847-12861).
  - `sub_8268C580` runs only while *(0x848C00D4) == 0 (TU340:12862-12873). sub_8268C580 allocates an object, constructs it, and stores the pointer there (TU15:588-633). So this is a one-time lazy init, not per-frame work.
  - `sub_82EFCEF0` runs if byte *(*(0x849E2420)+12) != 0 (TU340:12874-12887).
- Writers of 0x849E21D0: sub_82EFC738 copies *(0x849D36F8) into it when its r27 == 2 (TU129:12296-12307); the decrement at TU340:12815 is the other writer (step7.log:24-27). Hyp: "hold layer 2 for N frames after a transition".
- Writer of 0x849F5F14: only sub_82FD7DA8 (TU240:14069). About 70 functions read it (step7.log:58-128).

**(a6) sub_82EF8C18 (TU230:12566-12646): one layer list**
- n = *(list+8) (TU230:12578-12587).
- For i = 0..n-1:
  - it walks i steps from the head *(list+0) along next = *(node+4) (TU230:12592-12613);
  - it takes element = *(node+8);
  - it calls `element->vtbl[324](element, 0x847BC800)` (TU230:12618-12630).
- So each layer costs about n^2/2 pointer hops, because a linked list is accessed by index.
- 0x847BC800 is the same default transform that sub_82F0CCD8 uses when a node has no parent (TU41:10901-10905).

**(a7) sub_82F0CCD8 (TU41:10860-11212): the recursive element draw**
- **Visibility gate:** `node->vtbl[336](node)` (lr 0x82F0CCFC, TU41:10872-10884). If the low byte is 0, the function returns (TU41:10885-10890). This is the only prune in the walk.
- **Parent transform:** the parent comes in r4. If it is null, or u8 node+460 == 0, the default 0x847BC800 is used (TU41:10891-10905).
- **Matrix and per-node work:** matrix compose (TU41:10907-10939); `vtbl[340]`, `vtbl[332]`, `vtbl[344]` and `vtbl[348]` (TU41:10952-10993).
- **Children:**
  - `sub_82F0B200(&it)` builds a child iterator (lr 0x82F0CDEC, TU41:11016-11018).
  - `it->vtbl[0]` steps the iterator (TU41:11019-11033, TU41:11039-11049).
  - Each child gets `child->vtbl[56]` (TU41:11050-11060). The loop runs over TU41:11038-11139.
  - Then come: a deferred child looked up by the name at 0x821A5440 (TU41:11140-11156); `sub_82EF9350` (TU41:11162-11188); `vtbl[332](7)` (TU41:11204).
- **Recursion:** child draws re-enter sub_82F0CCD8 through virtual calls. The profile shows sub_82F0DD60 -> sub_82F0CCD8, and the nested sub_82F0CCD8 level holds 32 of the 54 native samples. Recursion ends when the iterator is exhausted, so its depth is the depth of the tree.
- **What a probe can count:**
  - calls of sub_82F0B200 at lr 0x82F0CDEC = nodes that passed the gate;
  - calls of sub_82F0CCD8 minus that = nodes rejected.

### 1.3 Chain (b): sub_82EFE948 -> sub_82EF3B38 -> sub_82EF3180

**(b1) sub_82EFE948 (TU45:12186-12913): text element draw**
- layer = `sub_82B6FC70(...)` (TU45:12229). It returns early if the layer is null (TU45:12233-12235).
- It sets the text globals 0x849D8CF3, 0x849D8CC8 and 0x849D8D80 (TU45:12319-12376).
- It gets alpha from sub_82EFB870 and clamps it (TU45:12577-12606). There is no early-out at alpha 0.
- The string is this+488 if set, else this+476 (TU45:12610-12626).
- It calls `sub_82EF3B38` unconditionally (TU45:12697-12699). There is no cached layout and no dirty flag.
- It writes the measured bounds back (TU45:12825-12856).

**(b2) sub_82EF3B38 (TU266:12336-12401):** forwards to sub_82EF3180 (TU266:12394).

**(b3) sub_82EF3180 (TU34:12271-12913): text layout and draw**
- It opens a 15152-byte stack frame with page probes (TU34:12285-12294).
- Early exits:
  - string r3 == null (TU34:12320-12323);
  - stack argument r1+15300 == 0 (TU34:12335-12340);
  - *(0x849C8CC8) and *(0x849C7EB4) both null (TU34:12341-12356);
  - empty string (TU34:12357-12363).
- A leading 0xBF byte swaps in the string at 0x82036348 (TU34:12324-12333).
- strlen loop (TU34:12366-12378). A length >= 600 is cut to 450 (TU34:12381-12395).
- Fixed cost on every call, whatever the string length:
  - memset of 13199 bytes through sub_83E46040 (TU34:12430-12451);
  - memset of 84 bytes (TU34:12544-12559).
- **Measure:** `sub_82EF0918` (TU34:12491) -> sub_82EF0638 -> sub_82EEFA18 -> sub_82B62528 -> sub_82B61580. This is the profile path.
  - sub_82B61580 (TU391:7223-7309) is a binary-tree search keyed by a (u16,u16) pair (TU391:7226-7307). It makes no calls.
  - Hyp: it is a kerning-pair lookup, done once per adjacent glyph pair.
- **Scale-to-fit:** TU34:12501-12517.
- **Glyph emission:** `sub_82EF2FE0` runs when the stack flag r1+15284 == 0 (TU34:12838-12891). The chain is sub_82EF2FE0 -> sub_82EF2E28 -> sub_82EF2368 -> sub_82EEF4D8 -> sub_82EEEE18 -> sub_82B629F8 -> sub_82B62C1C. The profile has 7 samples on this path.
- Bound: strlen <= 600 (450 after the cut). Work per call = a fixed ~13 KB memset, plus O(chars) measuring, plus O(chars) emission.

### 1.4 Inputs that set the size of the walk

| input | read at | written by | role |
|---|---|---|---|
| slot array 0x8491D6E0 (15 pointers) | TU210:6950-6951 | not traced | which slots exist |
| u8 p+4040, u32 p+120 | TU210:6974-6985, TU210:7250-7259 | not traced (slot object) | slot active / mode 0,1,2 |
| 0x84959FA0 | TU210:7283-7284 | sub_82B76398 TU27:7451, sub_82B784A0 TU109:7519, sub_82B76958 TU223:7254, sub_82B77A28 TU423:8885 | mode-1 slots enabled |
| 0x849F5EF0 | TU173:11097-11098 | only its own decrement, TU173:11106 (lis-addressed) | UI frames to skip |
| 0x849F5EC4 | TU173:11126-11127 | sub_82FD7128 TU37:13339, sub_82FD6FA0 TU416:13567 | UI root (hyp) |
| 0x849F5EC8 | TU173:11122-11129 | main loop TU59:14406 | event object |
| scene list and filters | TU220:13370-13543 | not traced | screens drawn |
| 0x849F5F14 | TU340:12767-12770 | sub_82FD7DA8 TU240:14069 | two-layer switch argument |
| 0x849E21D0 | TU340:12801-12833 | sub_82EFC738 TU129:12307 (copies 0x849D36F8), decrement TU340:12815 | layer-2 skip frames |
| *(this+84) layer lists, count at +8 | TU340:12610-12628, TU230:12578 | not traced | n per layer |
| vtbl[336] of each element | TU41:10878-10890 | element class (indirect) | visibility |
| text this+476 / this+488 | TU45:12610-12626 | not traced | string and its length |
| 0x848C00D4 | TU340:12865-12866 | sub_8268C580 TU15:633 (once) | lazy init only |

### 1.5 What the walk does not read

- None of the bodies above read:
  - a D3D query, a fence or the ring read pointer;
  - vblank, a swap counter, the timebase or a frame delta.
- The event object handed down from the main loop carries no time value either (TU59:14367-14397).
- In the static code, then, the size of the walk depends only on guest UI state.
- A timing dependence could still enter indirectly, in two ways (hyp):
  - through `vtbl[336]` or animation state inside the element classes (indirect, not resolvable statically);
  - through whatever arms the skip counters.

## 2. What native returns to the guest differently from Xenos

### 2.1 Interfaces checked

| interface | native3d behaviour | reachable from the walk? |
|---|---|---|
| Occlusion queries | queries.cpp hooks Create sub_83FB2360, Issue sub_83FB0738, GetData sub_83FB09E8 and Release sub_83FB05B0 (src/gpu_native/queries.cpp:318-321). GetData returns "not ready" while a query is pending and the real sample count afterwards (queries.cpp:172-194). No constant is fabricated. | Only Release, at depth 5 via sub_82B6FC48 <- sub_82AFAB68 (step6.log:81). GetData is not reachable. |
| Fences / ring | BlockOnFence does a full Synchronize (src/gpu_native/hooks_device.cpp:196-200). KickOff returns a scratch marker at device+0x6000 (hooks_device.cpp:277-287). InsertCallback is deferred (hooks_device.cpp:289-324). | No, not within depth 5 (step6.log:60-82). |
| GPU cache | InvalidateGpuCache sub_83FC5A58 is an empty function (hooks_device.cpp:171-175). | Yes, via sub_82B62C1C -> sub_82AFC280 -> sub_82CBDD98 -> sub_82CBCED8 (step6.log:69), and via sub_82AFBF90 (step6.log:82). In devoff the generated version writes PM4, so native is cheaper here, not dearer. |
| vblank / pacing | SyncToPresentationInterval sub_83FB2F20 is empty (hooks_device.cpp:182-185). Swap sub_83FB33E0 is hooked; the queued swap runs on the render thread with throttle 1 (src/gpu_native/draw.cpp:5440-5467). | No. The walk reads no timer (1.5). |
| Resolve / readback | - | No resolve or readback hook within depth 5 (step6.log:60-82). |
| Device-state reads | hooks_state (16), hooks_shader (8), hooks_texture (5) and hooks_buffer (8) (step6.log:4-9) | No, not within depth 5 (step6.log:60-82). |

Limits of this check:
- The BFS follows direct `bl` calls only. It leaves 159 indirect call sites unfollowed in the UI/text subtree, and 333 in the whole walk (step6.log:60, step6.log:71).
- The profile covers most of that gap: no gpu_native draw, state, shader or query frame appears among the native samples under the walk (an-main-tree-afab.txt:65-114).

### 2.2 Inventory of hooked guest functions

The link maps show 27 hooked guest functions in devoff2 and 109 in native3d (step6.log:1-22).

Hooked in both builds:
- crash_guards (2);
- main_menu_extras (3);
- name_trace (5);
- native_atomics (3): sub_82A2A0E8, sub_82A2A138, sub_82A2A160;
- native_constants (1);
- native_lock_elide (7): sub_82A2CAB0, sub_82A2CC20, sub_82A34E28, sub_82A34FE8, sub_82A35D28, sub_82A4CA18, sub_83F99CB8;
- native_markers (2): sub_82A3E238, sub_82A3E2B8;
- native_memops (2): sub_83E46040 (memset), sub_83E45090 (memcpy);
- scene_distance (2): sub_82C6F428, sub_83A11F50.

Hooked in native3d only:
- draw.cpp (7): sub_83FB33E0 (Swap), sub_83FBC9D8, sub_83FBCD28, sub_83FBD098, sub_83FBF0D8, sub_83FC6640, sub_83FC6A58;
- hooks_buffer (8), hooks_device (11), hooks_portrait (2), hooks_shader (8), hooks_state (16), hooks_texture (5). The full symbol lists are at step6.log:4-9;
- queries (4);
- settings_native_hooks (12) (step6.log:13);
- native_skin_diagnostics (6): sub_82A2AA28, sub_82A33D28, sub_82A34208, sub_82C9A000, sub_82DD3220, sub_82E0F480;
- native_slot_growth (3): sub_82A3B6D8, sub_82A57FE0, sub_836F9E48.

Every probe target in section 3 is unhooked ("generated") in both builds (step6.log:24-54). The one exception is sub_83FB33E0, which is not a probe target.

### 2.3 Host code that runs inside the walk on Main

| hook | build | reached via (step6.log) | per frame? | native profile samples |
|---|---|---|---|---|
| memset sub_83E46040 (src/native_memops.cpp:166-173) | both | sub_82EF3180, 13199 B per text call (:64); sub_82B541D8 (:78) | yes, once per text call | 3 (devoff a-prof: 0) |
| memcpy sub_83E45090 (native_memops.cpp:175-185) | both | sub_82B53308 (:63), sub_82AF9BC0 (:74) | yes | 1 |
| markers (src/native_markers.cpp:63-71) | both | sub_82FCC500 (:61-62), sub_82AF9BC0 (:72-73) | yes, a few | 0 |
| atomics / lock_elide | both | sub_82AED880 (:65, :75), sub_82A58570 (:68), sub_82AF66A8 (:80) | yes | 0 |
| free sub_82A34208 (src/native_skin_diagnostics.cpp:176-201) | native only | sub_82F02A80 -> sub_82A58570 (:67); sub_82B26B58 -> sub_83DD0530 (:76) | yes (hyp) | 1 |
| alloc sub_82A33D28 (native_skin_diagnostics.cpp:210-217) | native only | sub_8268C580 (:66, one-shot, TU15:588-633); sub_82AED880 -> sub_82AED7A0 (:77) | maybe | 0 |
| heap assert sub_82A2AA28 (native_skin_diagnostics.cpp:203-208) | native only | glyph path sub_82EF2368 -> sub_82EE12A0 -> sub_82A4BBE0 (:70); sub_82AF11D0 (:79) | (hyp) failure path only | 0 |
| InvalidateGpuCache sub_83FC5A58 (empty) | native only | sub_82B62C1C chain (:69), sub_82AFBF90 (:82) | yes | 0 |
| ReleaseQuery sub_83FB05B0 | native only | sub_82B6FC48 (:81) | rare | 0 |

- The cvar native_scene_diagnostics defaults to true and is kInitOnly (native_skin_diagnostics.cpp:14-16). While it is true:
  - every free makes two `heap_journal.Record` calls (:196-200);
  - every alloc makes one (:215-216).
- Each Record does a hash, a CAS on a bucket word, a fetch_add on a process-wide atomic, and a 32-byte write into a ~2 MB ring (src/native_heap_journal.h:75-86).
  - Estimated cost: ~50-200 ns each (hyp).
  - The ring may evict cache lines the walk uses (hyp).
- Profile total: ~5 of the 54 native samples under sub_82AF9BC0 are host hook leaves (memset 3, memcpy 1, hook:sub_82A34208 1; an-main-tree-afab.txt:65-114).
  - At 2.992/54 = 0.055 ms/f per sample, that is ~0.28 ms/f.
  - The other ~49 samples (~2.7 ms/f) are guest code. Devoff has 13 samples (1.0 ms/f) in total.

### 2.4 Frontend confound

- devoff2 is built with NATIVE_GPU=OFF: it has no settings_native_hooks object and no gpu_native objects (step5.log:97). So the devoff profile (a-prof) ran the stock frontend.
- In native3d with `--native_settings_frontend=false`, the frontend hooks pass straight through to the guest (src/settings_native_hooks.cpp:84, 140-238; the whole file is #ifdef'd, :1 and :240).
- main_menu_extras differs only on the A-press path (src/main_menu_extras.cpp:161-170).
- So the frontend difference is nil, provided n-prof used that flag. Agent 7 should confirm (agent7-present.md:222-223).

### 2.5 Weighing H1 / H2 / H3

**H1: more nodes or calls per frame (favoured)**
- The walk grew x3.0 (1.006 -> 2.992 ms/f), and text under it ~x3.6 (about 7 of 13 samples vs ~35 of 54). The rest of Main grew only x1.16 (agent7-present.md:219). A uniform per-call slowdown (clock, cache, SMT) would hit all of Main's guest code alike.
- sub_82B61580 is a pure guest leaf: a binary search with no calls (TU391:7226-7307). It went from 0 to 5 samples (an-main-tree-afab.txt:65-114). No hook can change its per-call cost, so more calls is the simplest explanation.
- The same subtree measures 1.006 vs 0.314 ms/f between two devoff captures, a and b (agent7-present.md:220). It varies 3x with UI state alone, so a UI-state difference between the captures would be enough.
- If H1 holds, the extra work comes from UI state, since the walk reads no GPU-returned value (2.1). Possible sources: more slots in mode 1/2, more scenes passing the filters, 7 layers instead of 2, longer lists, more visible elements, or more/longer strings. Which one cannot be told statically.

**H2: same calls, each slower**
- Direct host time inside the walk is ~0.28 ms/f (2.3).
  - Only the free-journal hook (1 sample) is native-only.
  - memset and memcpy are hooked in both builds and scale with the number of calls, so they amplify H1 rather than explain it.
- Indirect effects (hyp): the journal ring and the native renderer's working set competing with Main for L2/L3; a different core or clock. The rest of Main grew x1.16, which bounds any uniform effect at ~16%.
- The walk's lock, sub_82A2A260 at lr 0x82FCB474 (TU220:13319-13321), is not a hot leaf in the profile (an-main-tree-afab.txt:65-114). That argues against lock waits. The probe column lock_ns checks it.

**H3: a different path only in native**
- Branches on the chain:
  - UI skip counter 0x849F5EF0 (TU173:11097-11110);
  - two-layer switch (TU340:12767-12795);
  - sub_82EF4338 early exit (TU340:12590-12598);
  - empty-lists skip (TU340:12610-12637);
  - layer-2 skip 0x849E21D0 (TU340:12804-12817);
  - slot modes and 0x84959FA0 (TU210:7257-7293);
  - glyph-emission flag r1+15284 (TU34:12838-12891).
- None of these reads a GPU value directly. A native-only branch would need UI state that differs because of timing, for example a counter armed per transition while frames are paced differently (hyp).

**Verdict:** H1 is most likely, with H2 adding ~0.3 ms/f. H3 cannot be excluded statically. The counters in section 3 settle it in one run per build.

## 3. Probe spec (to build and run later)

### 3.1 Placement and gating

- **New file:** `src/scene_walk_probe.cpp`, optionally with `scene_walk_probe.h` exporting `void scene_walk_probe::Add(Counter, uint64_t)`.
- **Compile gate:** only with `-DLEGODIMENSIONS_SCENE_WALK_PROBE=ON`. Copy the CMake pattern at CMakeLists.txt:143-154 into a block placed after line 154:
  ```
  option(LEGODIMENSIONS_SCENE_WALK_PROBE "Build per-frame UI walk call counters" OFF)
  if(LEGODIMENSIONS_SCENE_WALK_PROBE)
      list(APPEND LEGODIMENSIONS_SOURCES src/scene_walk_probe.cpp)
      add_compile_definitions(LEGODIMENSIONS_SCENE_WALK_PROBE=1)
  endif()
  ```
- **Hook pattern:** copy src/tt_lock_trace.cpp:
  - declare each target as `extern "C" REX_FUNC(__imp__sub_X);` (tt_lock_trace.cpp:12-14);
  - wrap it as `REX_HOOK_RAW(sub_X) { pre; __imp__sub_X(ctx, base); post; }` (tt_lock_trace.cpp:105-122).

  With the option OFF there are no hook symbols, so the cost is zero.
- **Runtime gate:** `LEGO_SCENE_WALK_PROBE=<csv path>`, using the Config pattern at tt_lock_trace.cpp:19-26. When it is unset or "0", each wrapper just tail-calls `__imp__`. Two optional switches:
  - `LEGO_SCENE_WALK_PROBE_TIMING=0` turns off the QPC columns;
  - `LEGO_SCENE_WALK_PROBE_LEAVES=0` turns off the leaf counters.
- **Counters:** a thread_local struct of plain uint64. A counter is bumped only while `t_in_walk` is set. The sub_82AFAB68 wrapper sets it, so other threads and other callers of shared helpers don't pollute the counts.
- **Functions that are already hooked:** do NOT add a second REX_HOOK for these; it would be a duplicate symbol.
  - memset/memcpy (both builds: src/native_memops.cpp:166-185): add one `#ifdef LEGODIMENSIONS_SCENE_WALK_PROBE` Add() line to each hook body.
  - free/alloc in native3d (src/native_skin_diagnostics.cpp:176-217): same approach.
  - free/alloc in devoff2: that file is compiled only with LEGODIMENSIONS_NATIVE_GPU (#ifdef at :1/:240), so scene_walk_probe.cpp hooks sub_82A33D28 and sub_82A34208 itself, under `#ifndef LEGODIMENSIONS_NATIVE_GPU`.

### 3.2 Frame boundary

- The frame boundary is the sub_82AFAB68 wrapper, at depth 0 only (the function keeps its own nesting counter, 0x8491D674, TU210:6886-6891). On entry the wrapper:
  1. zeroes the counters;
  2. sets t_in_walk;
  3. reads qpc0.
- After `__imp__` returns, it:
  1. reads qpc1;
  2. snapshots the globals;
  3. appends one row.
- sub_82AFAB68 is called once per main-loop iteration (TU59:14409, lr 0x82FEBCC0), so one row is one game frame on Main. The qpc0 deltas also give the frame rate.
- Swap (sub_83FB33E0) is not a usable boundary:
  - in native it is a hook that runs on the render thread (draw.cpp:5440-5467);
  - in devoff it is a guest function.

### 3.3 Counters (CSV columns)

| column | hook | condition / computation | separates |
|---|---|---|---|
| frame, qpc0, walk_ns | sub_82AFAB68 | depth 0 | should reproduce 1.0 vs 3.0 ms |
| slot_m0, slot_m1, slot_m2 | sub_82AF9BC0 | histogram of u32 at r3+120 on entry | H1 (slots) |
| ui_calls, ui_skip | sub_82FCC500 | ui_skip when *(0x849F5EF0) > 0 on entry (read before `__imp__`) | H3 (skip counter) |
| screens | sub_82FCB308 | count | H1 |
| scenes | sub_82F050B0 | count | H1 |
| scene_early | sub_82EF4338 | lr == 0x82F050E4 and (r3 & 0xFF) != 0 after | H3 |
| layer_section | sub_82FBC4D8 | lr == 0x82F05218 (layer code reached) | H3 (empty skip = scenes - early - this) |
| two_layer | sub_82FBC4D8 | lr == 0x82F05218 and (r3 & 0xFF) != 0 after | H3 |
| layer2_skip | sub_82F050B0 | *(0x849E21D0) lower after the call than before | H3 |
| lists, list_n, list_hops | sub_82EF8C18 | n = *(r3+8); list_n += n; list_hops += n*(n-1)/2 | H1 (n) |
| nodes, max_depth | sub_82F0CCD8 | count, plus thread_local recursion depth | H1 |
| visible | sub_82F0B200 | lr == 0x82F0CDEC | H1 (visibility gate) |
| tree_ns | sub_82F0CCD8 | QPC around depth-1 calls only | H2 |
| text_elems | sub_82EFE948 | count | H1 |
| text_calls, text_chars, text_ns | sub_82EF3180 | chars = strnlen(guest r3, 600) (r3 is the string, TU34:12299-12323); inclusive QPC | H1 vs H2 |
| measure_calls | sub_82EF0918 | count; more than one per text call means re-measuring | H1/H3 |
| glyph_calls | sub_82EF2FE0 | count | H3 (r1+15284 flag) |
| k_61580, k_62528, k_62c1c, k_53308 | the four leaves below | count inside the walk | H1 vs H2 |
| memset_n, memset_bytes, memcpy_n | native_memops.cpp hook bodies | inside the walk | H1 amplifier |
| free_n, alloc_n | alloc/free hooks (3.1) | inside the walk | H2 (journal) |
| lock_ns | sub_82A2A260 | lr == 0x82FCB474; QPC | H2 (lock wait) |
| g_5ef0, g_21d0, g_9fa0, g_5f14 | at frame end | REX_LOAD_U32 of 0x849F5EF0, 0x849E21D0, 0x84959FA0, 0x849F5F14 | H3 state |

**Leaves to count:** these four are the only leaves under the walk with 2 or more native samples (an-main-tree-afab.txt:65-114):
- sub_82B61580 (TU391; measure leaf, 5 samples);
- sub_82B62528 (TU135; measure, 3);
- sub_82B62C1C (TU137; glyph emission, 3);
- sub_82B53308 (TU259; 2).

The other ~40 sub_82B6xxxx leaves have 1 sample each and need no counter. Their cost moves with text_calls and nodes anyway.

### 3.4 Output

- **CSV:** opened with CreateFileW(CREATE_NEW), as in tt_lock_trace.cpp:54-56.
  - The first line is `#scene_walk_probe_v1,qpc_frequency=<f>,build=<devoff2|native3d>,timing=<0|1>`.
  - Then the header, then one row per frame.
  - Rows go into a thread_local 64 KB buffer, written to the file when it fills and at exit. There is no syscall per frame.
- **Summary line:** every 600 frames, one REXLOG_INFO line in the game log, for example:
  `scene_walk_probe: frames=600 walk_ms=mean/p50/p95 nodes=.. visible=.. text_calls=.. chars=.. ui_skip=.. two_layer=..`
  So the game log alone answers the question, even without the CSV.

### 3.5 Cost

- **Count-only wrapper:** one extra call, a thread_local increment and a branch, ~2-5 ns.
- **Expected calls per frame** (hyp; the probe will measure them):
  - nodes: 100-1000;
  - leaves: 1000-5000, mostly sub_82B61580;
  - text calls: 10-200.

  That is about 6000 x 4 ns, ~25 us/frame.
- **QPC:** ~20-30 ns per read, two reads per timed call. The timed calls are sub_82AFAB68 (1), depth-1 sub_82F0CCD8 (tens), sub_82EF3180 (10-200) and the lock (a few). Total < 15 us/frame.
- **strnlen:** at most 600 byte reads per text call, ~100-300 ns. Total < 60 us/frame.
- **Total:** < 0.1 ms/frame. That is < 5% of the 1.99 ms delta, and the same in both builds.
- The count-only run (TIMING=0) is the clean H1 test, because it does not touch the timing it measures.

### 3.6 Files that change, and owners

| file | change | owner / who builds |
|---|---|---|
| DimensionsRecomp/rexlego/CMakeLists.txt | option block after :154 | rexlego; Agent 2 builds |
| src/scene_walk_probe.cpp (+ .h) | new | rexlego (written by Agent 9 or Agent 2) |
| src/native_memops.cpp:166-185 | 2 #ifdef'd Add() lines | rexlego |
| src/native_skin_diagnostics.cpp:176-217 | 2 #ifdef'd Add() lines (native3d only) | rexlego |
| src/gpu_native/* (Agent 4) | none | - |

- Agent 2 builds two flavours, both with LEGODIMENSIONS_SCENE_WALK_PROBE=ON:
  - devoff2-probe (NATIVE_GPU=OFF);
  - native3d-probe (NATIVE_GPU=ON).
- Guest codegen does not change; the hooks only replace symbols.

### 3.7 Runs to compare

1. **Zero-build A/Bs.** These can run now, on the existing native3d build, using Agent 7's profile route. Compare the sub_82AFAB68 subtree ms/f against the existing a/n profiles.
   - n0: `--native_scene_diagnostics=false` (native_skin_diagnostics.cpp:14-16).
   - n1: `LEGO_NATIVE_MEMOPS=0` (native_memops.cpp:19-22), in both builds.
   - Optional: `LEGO_NATIVE_LIGHT_MARKERS=0` (native_markers.cpp:1, :15-21).
2. **devoff2-probe vs native3d-probe.**
   - Same harness route and scene.
   - Same capture window: frames N..N+1800 after the route marker.
   - Native runs with `--native_settings_frontend=false`.
   - Each build runs once count-only (TIMING=0) and once timed (TIMING=1).
3. **Frame-rate check:** repeat step 2 both 60-capped and uncapped. If per-frame counts change with frame rate, the size of the walk depends on pacing (H1 or H3 through timing).
4. **Optional:** set `LEGO_SAMPLE_PROFILE` in the same run (src/sample_profiler.cpp:1-7) to tie the counts to profile samples.

### 3.8 How to read the result

| result | meaning | next step |
|---|---|---|
| nodes, visible, text_calls or chars ~3x higher in native; ns per call equal | H1. Going down the chain (slots -> screens -> scenes -> two_layer/layers -> list_n -> visible -> text), the first column that diverges names the cause. | trace who writes that state |
| ui_skip or layer2_skip often > 0 in devoff and ~0 in native (or g_5ef0/g_21d0 armed differently) | H3, frame-skip counter | find who arms 0x849F5EF0 (section 4) and why it depends on timing |
| two_layer or scene_early differ | H3, branch | follow 0x849F5F14 (sub_82FD7DA8, TU240:14069) or sub_82EF4338 |
| counts equal; text_ns, tree_ns and walk_ns ~3x higher | H2 | check the n0/n1 A/Bs. If they don't recover the time, suspect cache or clock (pin Main; idle-renderer test) |
| n0 (diagnostics off) recovers > 0.2 ms/f | H2, journal | default native_scene_diagnostics to false in perf builds |
| lock_ns large in native | H2, lock contention with the render thread | use the tt_lock_trace build |
| counts follow the fps cap | UI state coupled to timing | compare at equal fps before blaming native |

## 4. To run after 07:15 (multi-TU scans are not allowed while Agent 8's queue runs)

- Who arms 0x849F5EF0: scan the TUs for `addi rX,rY,24304` after `lis rY,-31585`, and for stores through a base near 0x849F5EC0 (e.g. +48).
- Callers of sub_82EFC738 (arms the layer-2 skip) and sub_82FD7DA8 (sets the two-layer argument).
- Vtable dump: find which functions sit in vtbl[336], vtbl[324] and vtbl[56] of the element and scene classes. This shows whether the visibility test reads timers or animation state.
- Indirect-call coverage: resolve the 159 / 333 indirect sites (step6.log:60, :71), or rely on the probe and profile instead.

## 5. Files in this folder

- `find.py` and `mapscan.py`: map and TU lookup helpers.
- `step1.ps1` to `step7.ps1`, `step6.py`, `step7.py`, and logs `step1.log` to `step7.log`.
  - step6.log: hook inventory, probe-target providers, and the direct-call BFS for hooks.
  - step7.log: readers and writers of the gating globals.
- `map-hits.txt`: map symbol hits.

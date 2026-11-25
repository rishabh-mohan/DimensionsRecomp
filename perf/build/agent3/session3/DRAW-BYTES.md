# DRAW-BYTES: deferred-command bytes per draw and per frame (sets N for `d3d12_submit_split_kb`)

Paper estimate only. Nothing was compiled or run. Abbreviations:
- **CP** = `build/agent7/s4-r1r2/new/sdk/src/graphics/d3d12/command_processor.cpp` (staged copy, same as the live SDK).
- **DCL.h** = `build/agent7/s4-r1r2/new/sdk/include/rex/graphics/d3d12/deferred_command_list.h`. It is byte-identical to `DimensionsRecomp/rexglue-sdk/include/rex/graphics/d3d12/deferred_command_list.h`.
- **SDK/** = `DimensionsRecomp/rexglue-sdk/src/graphics/d3d12/`. Read-only helpers.

## 1. How a command is encoded

- `GetSizeBytes() = command_stream_.size() * sizeof(uintmax_t)`. See DCL.h L39. `command_stream_` is a `std::vector<uintmax_t>` (DCL.h L649).
- `WriteCommand` (SDK/deferred_command_list.cpp L684-693) appends one 8 B `CommandHeader` (DCL.h L502-507). It then adds the argument bytes, rounded up to a multiple of 8. So **bytes = 8 + roundup8(args)**.
- The split check runs at the end of IssueDraw (CP L3107-3111) and of IssueCopy (CP L3713-3716). The threshold is `kb*1024` (CP L1191). The default is 0, which means off (CP L109).

## 2. Size of each command (x64)

| Command | args (B) | **bytes** | DCL.h |
|---|---|---|---|
| D3DDrawIndexedInstanced | 20 → 24 | **32** | L151-161 |
| D3DDrawInstanced | 16 | **24** | L163-171 |
| D3DIASetIndexBuffer (IBV 16) | 16 | **24** | L202-214 |
| D3DIASetPrimitiveTopology | 4 → 8 | **16** | L216-220 |
| SetPipelineStateHandle / D3DSetPipelineState / D3DSetGraphicsRootSignature | 8 | **16** | L396-422 |
| D3DSetGraphicsRootConstantBufferView {UINT, GPU VA} | 16 | **24** | L335-339 |
| D3DSetGraphicsRootDescriptorTable {UINT, handle} | 16 | **24** | L352-356 |
| SetDescriptorHeaps (2 heaps) | 16 | **24** | L407-410 |
| D3DRSSetViewports (1) | 24 | **32** | L292-296 |
| D3DRSSetScissorRects (1) | 16 | **24** | L286-290 |
| D3DOMSetBlendFactor | 16 | **24** | L239-246 |
| D3DOMSetStencilRef | 4 → 8 | **16** | L269-272 |
| D3DOMSetRenderTargets (8 RTV + DSV + flags) | 80 | **88** | L248-267, struct L603-610 |
| D3DResourceBarrier, n barriers × 32 B | 8 + 32n | **16 + 32n** (1→48, 2→80, 4→144) | L274-284 |
| D3DCopyBufferRegion | 40 | **48** | — |
| D3DCopyResource | 16 | **24** | — |
| Begin/EndQuery | 16 | **24** | — |
| ResolveQueryData | 40 | **48** | — |
| D3DDispatch | 12 → 16 | **24** | — |
| Set{Graphics,Compute}Root32BitConstants (n dwords) | 12 + 4n → ×8 | **8 + roundup8(12+4n)** | — |

Confidence: **HIGH**. These sizes follow directly from the struct layouts.

## 3. Commands written per draw (IssueDraw, CP L2590-3115)

The last column is my assumed share of title-screen draws that write the command. The title screen is UI-like: same render target, shared bindless root signature, small vertex counts.

| Command | B | Cite | Condition | Title weight | B/draw |
|---|---|---|---|---|---|
| DrawIndexedInstanced (or DrawInstanced, 24) | 32 | CP L3059 (L3000) | **always** | 1.0 | 32 |
| IASetIndexBuffer | 24 | CP L3050 | **always** for indexed draws, not cached | 1.0 | 24 |
| SetPipelineStateHandle | 16 | CP L2770-2774 | the pipeline changed | 0.5 | 8 |
| IASetPrimitiveTopology | 16 | CP L1090-1095, L2986 | the topology changed | 0.1 | 1.6 |
| RSSetViewports | 32 | CP L4428+, L1055-1067 | the viewport changed | 0.05 | 1.6 |
| RSSetScissorRects | 24 | CP L1069-1079 | the scissor changed | 0.1 | 2.4 |
| OMSetBlendFactor / StencilRef | 24 / 16 | CP L4453-4490 | host-RT path only, and the value changed | 0.02 | 0.8 |
| SetGraphicsRootSignature | 16 | CP L4931-4940 | the root signature changed. This also invalidates every root parameter (≈+240 B) | ~0 | ~0 |
| Root CBV: float consts VS | 24 | CP L5559 | the guest wrote a register in the shader's used bitmap (WriteRegister L2086-2101, WriteRegistersFromMem L2149-2173) | 1.0 | 24 |
| Root CBV: float consts PS | 24 | CP L5564 | same as above, PS bitmap | 0.75 | 18 |
| Root CBV: fetch consts | 24 | CP L5554 | any write to a fetch register (L2105-2113, L2182-2193) | 0.9 | 21.6 |
| Root CBV: system consts | 24 | CP L5569 | the compare-based `dirty |=` (L4559-4915) found a change | 0.5 | 12 |
| Root CBV: bool/loop | 24 | CP L5574 | any bool/loop write (L2102-2104) | 0.1 | 2.4 |
| Root table: shared memory | 24 | CP L5579-5597 | UAV/SRV toggle (memexport) | ~0 | ~0 |
| Root CBV: bindless descriptor indices P/V | 24 | CP L5598-5612 | texture SRV or sampler keys changed (L5116-5197) | 0.6 | 14.4 |
| Root tables: bindless sampler/view heaps | 24 | CP L5613-5622 | only after a root-signature change or heap overflow | ~0 | ~0 |
| Render-target barriers + OMSetRenderTargets | 48-144 + 88 | SDK/render_target_cache.cpp L1059-1090, L4692-4749 | the RT set changed | ~0 on title | ~0 |
| Texture barriers | 48+ | SDK/texture_cache.cpp L760-789 | texture state transition | ~0.05 | 2.4 |
| Shared-memory upload: barrier→COPY_DEST 48 + CopyBufferRegion 48 per range + barrier back 48 | ~144 | SDK/shared_memory.cpp L497-538; CP L2834-2881 | vertex/index pages are CPU-dirty (UI draws often have fresh vertices) | 0.25 | 36 |
| **Typical total** | | | | | **≈200 B** (≈165 B without uploads) |

**Per-draw summary**
- **Min = 56 B**: an indexed draw where nothing changed (draw 32 + IB 24). The absolute floor is 24 B, a non-indexed draw with nothing changed.
- **Typical (title) ≈ 200 B**. The plausible band is 130-280 B. The weights are my assumptions (about ±50%).
- **Max ≈ 0.8 KB (768-816 B)**: root-signature change with full re-bind 256 + fixed-function state 128 + OMSetRenderTargets 88 + 4-barrier 144 + 1-2 copies 48-96 + barrier back 48 + IB/draw 56. This excludes RT transfers, texture loads and memexport.

## 4. Fixed overhead per submission and per frame

| Item | B | Cite |
|---|---|---|
| BeginSubmission: SetDescriptorHeaps | 24 | CP L4177. All caches reset at L4164-4183 |
| First draw after BeginSubmission re-binds: root sig 16 + 10 bindless root params × 24 = 240 + pipeline 16 + topology 16 + viewport 32 + scissor 24 + blend 24 + stencil 16 + OMSetRenderTargets 88 | ≈496 | CP L4931-4940, L5554-5622, L4428-4491; SDK/render_target_cache.cpp L4692-4749 |
| ⇒ cost of each extra submission (split or natural) | **≈0.35 KB** above a typical draw | |
| Swap (IssueSwap CP L2206-2576): compute root sig 16, root consts ~32, 3 descriptor tables 72, pipeline 16, barriers 80-130, dispatch 24, optional gamma ramp copy 96 | 0.4-0.6 KB | CP L2206-2576 |
| Each resolve (IssueCopy CP L3692-3719 → Resolve SDK/render_target_cache.cpp L1183-1410, DumpRenderTargets L5583-5800, plus the clear) | 0.6-1.0 KB | |
| EndQuery when a query is active | 24 | CP L4266-4270 |
| **Assumed fixed bytes per frame** | **min 1 KB / typical 3 KB / max 6 KB** | |

The `primitive_processor` BeginSubmission copy (SDK/primitive_processor.cpp L61-73) runs only once, so it is not counted.

## 5. KiB per frame (draws × B/draw + fixed)

| draws/frame | min (56 B + 1 KB) | typical (200 B + 3 KB) | max (816 B + 6 KB) |
|---|---|---|---|
| **226** (title median; p10 218, max 228) | **13.4** | **47.1** (39.4 at 165 B; band 31.7-64.8 for 130-280 B) | **186** |
| 785 (in-level static) | 43.9 | 156.3 | 631.5 |
| 6,000 (levels/cinematics 5k-16k) | 329 | 1,175 (≈970 at 165 B) | ≈4,787 |

**One list = one submission, not one frame.** If K natural submissions already happen per frame, the KiB per list is about (KiB/frame)/K.

| Title, typical | K=1 | K=2 | K=4 |
|---|---|---|---|
| KiB per submission | 47.1 | 23.6 | 11.8 |

## 6. Where submissions already end without the split

- IssueSwap → `EndSubmission(true)`: CP L2569 and L2575. This happens once per frame.
- `OnPrimaryBufferEnd`: CP L2578-2583. It is gated by `d3d12_submit_on_primary_buffer_end=true` (default, CP L98) and `CanEndSubmissionImmediately` (CP L4360-4362, which blocks it during pipeline creation). It is called at the end of every `ExecutePrimaryBuffer` (base `src/graphics/command_processor.cpp` L683-702, called from L310), i.e. **each time the CP catches up to the guest write pointer**. That can happen several times per frame, so K may well be > 1.
- `EndGuestOcclusionQuery`: CP L5834-5856. Ends the submission for each guest query.
- Memexport readback (`d3d12_readback_memexport=true` in the game tomls): FullPath CP L3551-3595 → `AwaitAllQueueOperationsCompletion` (command_processor.h L356-359) → `CheckSubmissionFence(submission_current_)` → `EndSubmission(false)` (CP L3959-3963). **Every memexport readback ends the submission.**
- `PublishOnDemandMemexport`: CP L3207-3208. `DisableHostOcclusionQueries`: CP L5798.
- `MaybeSplitSubmission` (CP L4364-4409) itself holds the split while an occlusion query, a scratch buffer or a pipeline creation is active.

**K is not known from any existing data.** Earlier notes only plan to measure it (`build/agent7/s4-r1s2/FUNCTIONAL-ROWS.md` L65-66; `notes/agent7-present.md` L23 "fallback K ~2-4").

## 7. Answers

1. **Does N=64 split on the title screen? Effectively no.** The typical estimate is 47 KiB/frame, which is below 64 even if one submission spans the whole frame (K=1). The split would only fire if a draw averaged **≥ ~276 B** (= (64−3)·1024/226) **and** K=1. With K ≥ 2 it is even further away. Treat N=64 on the title as a **control (≈no split)**, not as a treatment.
2. **N for about 2 submissions/frame on the title: N ≈ 24** (half of 47 KiB), assuming K=1.
   - Across the band (31.7-64.8 KiB/frame), N=24 always splits at least once: 2 submissions for 32-48 KiB and 3 for 48-65 KiB.
   - If K > 1 natural submissions already exist, use about (47/K)/2: K=2 → N≈12, K=4 → N≈6.
   - The extra cost of each split is ≈0.35 KB of re-binds plus one ExecuteCommandLists. This is negligible.
3. **Level scenes:**
   - In-level static (785 draws, ≈156 KiB): N ≈ **80** for about 2 per frame. The documented fallback N=64 gives about 3 per frame.
   - Heavy levels (6,000 draws, ≈1.2 MiB): about 2 per frame needs **N ≈ 512-600**. N=64 there means ~18 submissions per frame.
   - Natural boundaries (occlusion queries, memexport readbacks) are probably more frequent in levels, which lowers the bytes per list.
4. **Verification:** a split=0 run prints nothing. The `d3d12_submit_split:` counter line is logged only inside `MaybeSplitSubmission` (CP L4364-4409, at most every 10 s). That function is reached only when `d3d12_submit_split_kb != 0` (CP L1191-1196), and only once the list reaches N (CP L3107-3111).
   - So run once with a **small N that does split**, e.g. **N=16** (row s4b11/s4b25 style).
   - Take two counter lines and compute the deltas of `frame`, `submission` and `splits`.
   - Natural submissions per frame: **K = (Δsubmission − Δsplits) / Δframe**.
   - Bytes per frame: **KiB/frame ≈ N · (Δsplits/Δframe) + K · (leftover, < N KiB)**. This bounds the real KiB/frame between N·splits/frame and N·(splits/frame + K).
   - With K and KiB/frame measured, the §5/§7 arithmetic gives the real N for ~2 submissions per frame. Also check that `failed` and the `held_*` counters stay near 0, otherwise the split count undercounts what was due.

## 8. Assumptions

- Defaults: `d3d12_bindless=true` (CP L47, L1186), host render targets (`render_target_path_d3d12=""`), `occlusion_query_enable=true`, `async_shader_compilation=true`, `swap_post_effect=none`, `d3d12_readback_resolve=false` (CP L54).
- Title draws are mostly indexed. The weights for each command are listed in the §3 table.
- Float constants count as dirty only when the guest writes registers in the shader's used bitmap. Xenia-style titles rewrite VS constants on almost every draw, so the weight is 1.0 for VS and 0.75 for PS.
- RT transfers, texture uploads and memexport copies are left out of the per-draw max.

## 9. Confidence

| Item | Confidence |
|---|---|
| Command byte sizes (§2) | **HIGH** |
| Min bytes per draw (56 B) | **HIGH** |
| Typical bytes per draw (≈200 B, band 130-280) | **MEDIUM-LOW** (weights assumed, ±50%) |
| Max bytes per draw (≈0.8 KB) | MEDIUM |
| Fixed bytes per frame (1/3/6 KB) | MEDIUM-LOW |
| K (natural submissions/frame) | **UNKNOWN**. This is the biggest uncertainty and it scales the answer by 1/K |
| "N=64 does not split the title" | **MEDIUM-HIGH** (needs ≥276 B/draw and K=1) |
| "N≈24 gives ~2/frame on the title" | MEDIUM-LOW (true only if K=1) |

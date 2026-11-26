# NOTE: combined pack plan, attract + story (M16, static, 2026-11-26 05:35)

The plan step only. No pack, no bin, no repin; those stay the user's Phase 4 call.

## Inputs
| item | path | sha256 |
|---|---|---|
| attract input (79 placement + 2 root) | build\agent16\dump\pack-input-20261125-172422 | SHA256SUMS (existing) |
| story input (60 placement) | build\agent16\dump\pack-input-story-20261126-053310 | SHA256SUMS 757379E231D9E09A91AF8197B1F7C6841A15A2FE0860A625E470372BD5D4D014 |
| combined input (141 files, copies, sha re-verified) | build\agent16\dump\pack-input-combined-20261126-053440 | SHA256SUMS FA99EB7D2EAF7B65D12816DD9DD796FDDA42C65A1F662E8E90E388224B57CE0B |
| post report of the dump session | build\agent16\dump\post-story-20261126-053310\dump_post_story.txt | F1DDEBD0D899AC93838F16D037F3AE6DC05CF5443F50517AC77CBEA1F40F08A0 |

The merge script is scratch\combine_inputs.py. It checks for:
- name collisions with different bytes: 0;
- same-name/same-bytes duplicates: 0;
- same-content duplicates: 0.

## Plan
`native4bp.ps1 plan --input build\agent16\dump\pack-input-combined-20261126-053440` (native4bp.py 37FD3989, Idle, affinity 0x3)
- Output: build\agent16\pack\plan-20261126-053448.txt, sha256 0D10FF3617697AB121EACE5EA6B71F36A60C1986241E051452CB9A8BB5F3B2CC.
- **PLAN OK**: 0 bad pins, 0 input failures, clang++ found.
- 143 candidates selected: 4 s35 pinned + 79 attract + 60 story.
- 2 excluded by default: the root dumps ps-93B9F93B535E7CCA (create-path) and vs-A58EBA123EFB541C (memexport VS).
- The current pack (native4bp, run-20261125-173813) has 83 containers. This candidate list adds 60.
- The plan wrote only the plan file; LATEST-pack.txt is unchanged.

## OPEN ITEM: 22 missed stage+guests with no identity event (dump session 051154)
82 stage+guests missed in the dump-session trace, but only 60 have a `missing_placement_shader_identity` event (= dumped).
The remaining 22 account for 15910 of 300793 missing draws (5.3%).
Source: scratch\noident.txt 552EE07E (script noident.py 966888BB).

| stage | guest | missing draws |
|---|---|---|
| VS | A7FA6EA0 | 7458 |
| PS | A81DF240 | 6379 |
| VS | A7B66500 | 629 |
| VS | A791C1B0 | 552 |
| PS | AB625D70 | 290 |
| PS | A86EC990 | 290 |
| VS | A7B98960 | 146 |
| VS | A7B5F240 | 73 |
| VS | A7B52390 | 45 |
| VS | A7B64000 | 34 |
| VS | A7B774F0 | 8 |
| VS | A7B5E310 | 4 |
| VS | A7B55170 | 2 |
| PS | A7B09700, A7B61510, A7B61C10, A7B5EB40, A7B52C10, A7B566C0, A7B51D20, A7B5DD00, A7B54C20 | 0 (unrecognized only) |

Cause, not decidable statically. The hook (shaders.cpp CaptureMissingPlacementShader):
- emits the identity event only for a new full-container XXH3 per stage;
- returns silently on validation failure (flags, sizes, readable range).

So each of the 22 is either (a) the same container already captured under another guest, which is fine, or (b) refused by validation, in which case it is not in the dump.
Proof: a miss count on the rebuilt bin. If it is a rebuilt pack, run the same scene and check that these draws are gone.

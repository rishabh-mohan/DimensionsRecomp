# musttail - STATUS (restart notes)

## State (22:39)
- Part A (musttail_calls) DONE and reported 20:42: SDK edits in context.cpp / control_flow.cpp,
  tests/ppc/asm/seq_tailcall_musttail.s, proofs in README.md (emit_test 480/0, acceptance 5/5,
  proof_counts, real_tu TU 61).
- Batch 2 (Agent 10's ask C, from Agent 9 21:01):
  1. musttail regen DONE 21:05-21:22 -> build/agent9/generated/musttail/default (888 files,
     468.4 MB, gen_musttail.log; ran with the 21:08 rexglue.exe A8036AC8947D70BA).
  2. chain depth test DONE 21:56 (chain.txt; README "Batch 2" table), reported 21:59.
  3. vpkuhus/vpkuwus alias fix: CANCELLED by Agent 9 (22:01). Do NOT edit vector.cpp.
  4. Plan changed by Agent 9 at 22:26: NO alltu and NO heavy (musttail vs baseline) on the musttail
     variant; batch2.ps1 and heavy.ps1 are superseded, do not run them.
     a. textcheck (one step, in ONE slot): killed by the quiet windows at 21:57 and 22:29, not done.
     b. heavy_batch.ps1 (NEW): once Agent 9 says build/agent9/generated/batch/default exists (ETA ~22:45):
        baseline TUs 304/233/52/61 (build/agent2/gen-noflag/default) vs gen_out/batch_tuN.cpp
        (the same functions copied from the batch variant), real game Release flags, per-variant PCH.
        -> heavy_batch.txt, then a README table, then message Agent 9 the table.
     c. lowest priority, only if slots are free: alltu.ps1 -Variant batch (syntax-only, pausable, -Resume).
- QUIET WINDOW 2 since 22:28 (bench/agent9/QUIET): start nothing until Agent 9 says it is over.

## Next commands (each after Agent 9's go)
- `powershell -NoProfile -ExecutionPolicy Bypass -Command ". .\bench\agent9\musttail\slot1.ps1; Invoke-InSlot { powershell -NoProfile -ExecutionPolicy Bypass -File bench/agent9/musttail/textcheck.ps1 *> bench/agent9/musttail/textcheck.log }"`
- `powershell -NoProfile -File bench/agent9/musttail/heavy_batch.ps1 *> bench/agent9/musttail/heavy_batch.log`
  (holds no slot itself; scan + 2 PCH + 8 -O3 compiles, one slot each; progress in heavy_batch.txt)
- only if slots are free: `powershell -NoProfile -File bench/agent9/musttail/alltu.ps1 -Variant batch *> bench/agent9/musttail/alltu_batch.log`
  (resume with `-Resume`)
- Then: README "Batch 2" heavy_batch table + textcheck numbers, message Agent 9.

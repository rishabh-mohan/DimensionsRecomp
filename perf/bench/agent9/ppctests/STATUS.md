# T8 status (ppc asm tests: default vs opt vs crso, plus test F)

State (23:30): DONE. The rerun is complete, with tool sha256 37B32713B7516402 (23:16:17). Nothing is running.

Session 3 (02:21, Agent 9): opt9 (opt_config.toml without skip_lr = build B's 9 keys) ran on the same tool, in one slot.
- opt9: 1513 pass, 1 FAIL (vupkd3d128.test_short2_3), 1 excluded (cr_so_fold.test_call), 0 CRASH. This is the same as opt.
- Its ppc_test_functions.cpp differs from opt's only in 9 ctx.lr lines (build/agent9/ppctests/opt9_lrdiff.py).
- default and crso were rerun alongside: unchanged.
- Fix: link.ps1's fallback loop variable $o overwrote $O. PowerShell names are case-insensitive. It is now $ov.

Results, 1515 tests per variant:
- default: 1514 pass, 1 FAIL.
- opt (tests/ppc/opt_config.toml, incl. flush_mode_elision): 1513 pass, 1 FAIL, 1 excluded.
  - The excluded test is cr_so_fold.test_call. Run on its own it fails with r3 = 0x48000020, as predicted.
- crso (cr_compare_so_zero only): 1514 pass, 1 FAIL.
- The one FAIL is the same test in all three variants: vupkd3d128.test_short2_3.
  - The parser fix generated it for the first time.
  - The SHORT2 unpack of -32768 gives 0x403F8000; the test expects the QNaN 0x7FC00000.
  - The generated code is identical in all variants. This is an emitter gap, not an option bug.
- Test F: test_same and test_clear pass in every variant. test_call passes in default and crso.
- seq tail-call tests: all 4 pass in every variant (opt uses the musttail form). No crashes.
- The 6 opt failures on REGISTER_OUT cr are gone. The tool drops those expectations and logs a warning.

Outputs:
- bench/agent9/ppctests/README.md: full write-up, with the rerun and test F sections and the CMake proposal.
- build/agent9/ppctests/: compare.md, failures.md, instr_cr_so_fold.md.
- build/agent9/ppctests/<variant>/: gen.log, results.xml, isolated.txt, excluded.txt.
- build/agent9/ppctests/logs/compile.log.

Re-run recipe: README.md "Pipeline". The rerun's compiles went through two parallel chains, build/agent9/ppctests/chainA.ps1 and chainB.ps1, with one cpu2 call per compile.

Remaining (not mine):
- vupkd3d128 SHORT2: map -32768 to QNaN in the emitter, or exclude the test.
- Applying the ppc_tests_opt CMake proposal (README section (c)).
- opt_local.toml is obsolete. It is left in place.

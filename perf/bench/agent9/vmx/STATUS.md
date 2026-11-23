# VMX fallback subtask: STATUS

Owner: subagent of Agent 9 (conversation 7b9b6ed5-c2cb-49ac-8eda-faf8db962f21). Parent: 2bec8ced-e7bc-4b37-bc42-ca8e3f8ef8c3.
Flag: ctx.config().vmxVectorFallbacks (TOML vmx_vector_fallbacks), in config.h/config.cpp (added by the parent).

## State: DONE (reported to the parent)
- [x] Candidate survey: vsubsws, vsrb, vsrab, vrlw, vsraw, vsrw, vpkuhus, vpkuwus. Left alone: vlogefp, vexptefp, vpkd3d128, vupkd3d128.
- [x] vector.cpp: 8 emitters, each `if (ctx.config().vmxVectorFallbacks ...) { SSE text; return true; }` followed by the old code verbatim. vpkuhus/vpkuwus use the SSE form only when vD != vA and vD != vB.
- [x] syntax-check of vector.cpp: exit=0, errors=0. The tool built at 19:15 by Agent 9 compiled the live file.
- [x] run.ps1: 148,555,140 cases × 3 configs. 0 lane mismatches, 0 SAT mismatches. Flag-off text 0/40 different.
- [x] verify_unchanged (re-run 20:37): only the 8 emitters differ from the pre-edit file.
- [x] asm_count.ps1 counts recorded.
- [x] README.md written with all numbers.

## Next command (only if something changes)
powershell -NoProfile -File bench/agent9/cpu2.ps1 -File bench/agent9/vmx/run.ps1 *> bench/agent9/vmx/run.log

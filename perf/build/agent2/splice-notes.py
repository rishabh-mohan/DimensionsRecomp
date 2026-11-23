"""Splice build/agent2/notes-top.md (with the probe result) over the top block of perf-notes/agent2-baseline.md,
keep everything from 'Problems and fixes (session 3):' on, and append problems 11-14. Line endings are preserved."""
R = r'<workspace>'
p = R + r'\perf-notes\agent2-baseline.md'
top_p = R + r'\build\agent2\notes-top.md'

PROBE = """- **Probe result (19:07, `build/agent2/probe-toggle.log`):** one find_package tree (dev rexlego against
  build/sdk/install) configured OFF (9.8 s) and then ON with Agent 6's stub flags (10.5 s), both exit 0. Compile
  DB diff OFF -> ON: **generated 440/440 identical, PCH identical**; rexlego/src 33 changed + 38 ON-only; other 3
  changed (`share/rexglue/rex_app.cpp`, `share/rexglue/windowed_app_main_sdl.cpp`, `res/legodimensions.rc`) + 18
  ON-only (SDK `texture/{util,info}.cpp`, plume_d3d12 + D3D12MA, miniz, zstd, `gpu-aot/generate_microcode_index.cpp`
  and `prelink_shader_cache.cpp`, and the 4 `rexlego/out/native-gpu` cache/index TUs). `compile-one -SyntaxOnly` of
  SDK `texture/util.cpp` and `info.cpp` with that DB: exit 0 (6-7 s each). So toggling ON in the OFF tree recompiles
  no generated TU. Unknown until Agent 6's real inputs land: the compile time of the real bank TUs (embedded caches)."""

ITEMS = """11. **Correction (Tracy):** my 18:5x note that the baseline SDK libraries were compiled with Tracy on was wrong. The
    639 `TRACY_ENABLE` hits were the Debug and RelWithDebInfo entries of build/sdk's multi-config compile DB; in
    Release only TracyClient.cpp has it. See (a) above.
12. PowerShell 5.1: `Tee-Object -Append` writes UTF-16LE into an existing UTF-8 log, and pipeline output inside a
    function leaks into its return value (the probe's `$c1 -ne 0` became an array test and printed a bogus
    "configure failed"). Fix: `filter Log { $_ | Out-File -Append -Encoding utf8 $log; Write-Host $_ }`.
13. agy-grid delivers only the text on the `@@to` line itself; every message is one line and details live here.
14. Agent 8 (19:0x) fixed the dev tree's `native_lock_elide.cpp`: it declares its 21 callees with
    `DECLARE_REX_FUNC` and compiles with or without the shim. The shim is now only needed for build/baseline
    (snapshot 127e04b). build/dev still carries it (harmless); it goes at the next build/dev reconfigure. New trees
    (snap1-*) are configured without it.
"""

raw = open(p, 'rb').read()
crlf = b'\r\n' in raw
t = raw.decode('utf-8').replace('\r\n', '\n')
top = open(top_p, 'rb').read().decode('utf-8').replace('\r\n', '\n')
if '- PROBE_RESULT_PLACEHOLDER' in top:
    top = top.replace('- PROBE_RESULT_PLACEHOLDER', PROBE)
    open(top_p, 'w', encoding='utf-8', newline='\n').write(top)
marker = 'Problems and fixes (session 3):'
i = t.index(marker)
t = top.rstrip('\n') + '\n\n' + t[i:]
anchor = "10. x86: SDK x86-64-v2 + game x86-64-v3 kept (README-dev's documented pair; build/dev gives the same pair).\n"
j = t.index(anchor) + len(anchor)
if not t[j:].startswith('11. '):
    t = t[:j] + ITEMS + t[j:]
out = t.replace('\n', '\r\n') if crlf else t
open(p, 'wb').write(out.encode('utf-8'))
print('ok crlf=%s chars=%d lines=%d placeholder_left=%s' % (crlf, len(out), out.count('\n'), 'PROBE_RESULT_PLACEHOLDER' in out))

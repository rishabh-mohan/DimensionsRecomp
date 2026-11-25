# FINAL bins: pins (M2, staged 07:32 2026-11-25)

Built from FINAL-DEFAULTS.diff 955543F5 (sha256 955543F5E2E5F4F44A57CD380FF8D8AC6828E1C0C1372612441AB2AA4E88C657).
Rating: final-defaults-rating C20B6FDB, final-build-rating DF596C16, later 94CC9FA7 (build-final/fsyntax edits CONFORM).
Tools that ran (sha256/16): build-final.py 5BE1F221800137BD, recompile.py 855BCC79148E2DA8, relink.py F3C6EEAF332AB213,
stage-variant.py D2BD1C6358FC19C1, verify-bins.py 80FF4C5F581C4B1B, prep-final.py 83F732CA9CEB301F,
fsyntax.py 66C7D74022A068DA, pe-check.py F4368C32076AAA3E, mapcheck-s4c.py F8CB7B495F74D978.

Pin a bin by its **MANIFEST.txt sha256** (`session3\verify-bins.py <bin>` re-checks every file against it).

| bin id | dir (build/agent2/) | MANIFEST.txt sha256 | role | default arm | off arm |
|---|---|---|---|---|---|
| devfinal | devfinal-bin | F9C2BE722E5B3517D1CA7AB1A0F79BA9B7AADF59D4EF0E43384CE307C7084621 | Xenos ship (= win3 by default) | plain: cvars `framerate_limit=0` only, env none | 12 old values + `LEGO_GPU_WAIT_BACKOFF_US=off` |
| devfinal-off | devfinal-off-bin | 3F4B7BEBD887319A80CB4E689007D227176AA6586112242C0AA357D3AF9FE09D | Xenos, built with `-DLEGO_GPU_WAIT_BACKOFF_DEFAULT_US=-1` (F3) | n/a (OFF bin) | per D7: still set `off` |
| nativefinal | nativefinal-bin | D7C7B7060519A4950EE794FB5FF51D1E1BFB62394DBBF132D1AA99FFE7A6EE79 | native N-A (miss cache default ON) | plain launch | `LEGO_NATIVE_SHADER_MISS_CACHE=0` (F6) |
| nativefinal-off | nativefinal-off-bin | 0C67CBD6918822EC986DF06C141BAD74F47F5C07E40F443AFF1B6898A756C51D | native, built with `-DLEGO_NATIVE_SHADER_MISS_CACHE_DEFAULT=0` | n/a (OFF bin) | - |

## File hashes (sha256/16)

| file | devfinal | devfinal-off | nativefinal | nativefinal-off |
|---|---|---|---|---|
| legodimensions.exe | 545D28B9DDEAD51E | DB263913A67710B6 | 5C21941DAF9DF36B | 4ADF630E6899C407 |
| legodimensions.map | 6DA167C77804F7CD | A7891CD914648898 | B1CB53486742AB2B | 2375AA1259077A5A |
| rexruntime.dll | C5BC627BB2E83CF2 (new) | C5BC627BB2E83CF2 (new) | A33801D1538D6175 (native4b) | A33801D1538D6175 (native4b) |
| rexgpu-xenos.dll | CB3A2CC967A9BE81 (new) | CB3A2CC967A9BE81 (new) | E3CB99CFDEA95E66 (native4b) | E3CB99CFDEA95E66 (native4b) |
| TracyClient.dll | 85044850B6C663B5 | 85044850B6C663B5 | 85044850B6C663B5 | 85044850B6C663B5 |
| amd_fidelityfx_dx12.dll | - | - | 12A5081257EC95B0 | 12A5081257EC95B0 |
| FiraSans-Regular.ttf | C29556A2719BF613 | C29556A2719BF613 | C29556A2719BF613 | C29556A2719BF613 |
| achievement_unlocked.wav | A707019154484B9D | A707019154484B9D | A707019154484B9D | A707019154484B9D |

native-gpu-build.txt is not staged (native4b-bin has none). The fingerprint is `LEGO Dimensions native GPU 1616ce65e973c583`, in the exe and in final/b/nat/gen-on.

## Shared bins re-verified after each of the 4 stagings (D6): 0 FAIL every time

| bin | MANIFEST.txt sha256 |
|---|---|
| devoff4b-bin | DE11A914079D7DF7080CAA86B05DAE151CEFA017FDE15713CB85FA79F86339FA |
| devoff4b-cg26-bin | 917AE86E6C0CC9B370901397EF8FD72F65449E5EC9594D14D9902215BBBC1D5C |
| native4b-bin | B63769FE46CC04592F2BEDAF04A51C362000325D3291BC4D7489369C2160B817 |

snap1-sdk/install/bin/rexgpu-xenos.dll == E3CB99CF before and after.

## D7 harness rules (for M3/M8; not written by M2)

- New-bin off/ref arms set `LEGO_GPU_WAIT_BACKOFF_US=off` (lowercase) + the 12 old cvar values (DEFAULTS-TABLE.md). This includes STATS-only probe arms. Old-bin arms keep `env {}`.
- Each new-bin matrix names its default arm. Proof of the arm = run.json `env_set` + the bin id/MANIFEST sha above + `final\check-defaults.py <game.log> --mode xenos|native-old|off`.
- check-defaults works from a game.log only (no static mode). The static proof is the needle gates in final/b/<leg>/build-final.txt.
- Install before the first run on any new bin (no cache/ in any staged bin).

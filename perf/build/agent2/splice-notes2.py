"""Splice build/agent2/notes-top.md over the top block of perf-notes/agent2-baseline.md (everything before
'Problems and fixes (session 3):'), keep the rest, and append problems 15-20 after item 14 (once).
Line endings are preserved."""
R = r'<workspace>'
p = R + r'\perf-notes\agent2-baseline.md'
top_p = R + r'\build\agent2\notes-top.md'

ITEMS = """15. Snapshot copies: the libmspack sources the SDK compiles are file symlinks, and moltenvk has 8 directory links.
    S0 skipped all 27 reparse points. snap.py now copies file symlinks by content (19) and skips the directory links
    (moltenvk is macOS-only).
16. The SDK configure needs each submodule's `.git` FILE: `thirdparty/CMakeLists.txt:72` checks
    `EXISTS <submodule>/.git` and fails with "Git submodule 'cli11' is not initialized". snap.py keeps the `.git`
    files (31) and skips `.git` directories. git itself is not needed: the version falls back to
    0.10.0.0-dev.unknown, as in the baseline.
17. The first snapshot copy took 269.5 s (23.7k files, about 1.5 GB, through `\\\\?\\` paths). Refreshes take 6-9 s.
18. Processes started under a run_command task die with it. At 19:40 I killed only the build-snap.ps1 PowerShell, so
    that the slow SDK configure could finish without a -j10 build following it. That ended task-398, and its
    process tree took the configure with it. CMake writes CMakeCache.txt only at the end of a configure, so every
    check result was lost and attempt 3 started from scratch. To stop a build, kill its task or run
    `build/agent2/stop-snap.ps1`; to keep a child alive, don't end its task.
19. Step 6: CMake `file(WRITE)` writes in text mode on Windows, so LF becomes CRLF. Use
    `file(CONFIGURE ... NEWLINE_STYLE LF)` (binary mode) when the bytes matter. `execute_process` drops NUL bytes and
    the CR of CR-LF pairs from captured output.
20. PowerShell: `[IO.File]` methods resolve relative paths against the process cwd, not the `Set-Location`
    directory, so use full paths.
"""

raw = open(p, 'rb').read()
crlf = b'\r\n' in raw
t = raw.decode('utf-8').replace('\r\n', '\n')
top = open(top_p, 'rb').read().decode('utf-8').replace('\r\n', '\n')
marker = 'Problems and fixes (session 3):'
i = t.index(marker)
t = top.rstrip('\n') + '\n\n' + t[i:]
anchor = "    (snap1-*) are configured without it.\n"
j = t.index(anchor) + len(anchor)
if not t[j:].startswith('15. '):
    t = t[:j] + ITEMS + t[j:]
out = t.replace('\n', '\r\n') if crlf else t
open(p, 'wb').write(out.encode('utf-8'))
print('ok crlf=%s chars=%d lines=%d items15=%d' % (crlf, len(out), out.count('\n'), out.count('\n15. Snapshot copies')))

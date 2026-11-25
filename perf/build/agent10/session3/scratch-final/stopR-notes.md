# STOPR pre-notes (M10, 10:26) - rating held until M3 re-issues

- Draft 7F03C6E3 / queue B90266D4 vs live 69C77DA7: git diff = exactly lines 93-97, only -Seconds/est/note. Every other line is byte-identical.
- (c) s4b-queue.ps1 CCA391CA runs under Windows PowerShell 5.1 (powershell.exe, pids 40712/44632), with $ErrorActionPreference='Stop' (L35).
  - The main loop L113-172 has no try/catch around Get-Content queue (L129) or ConvertFrom-Json (L131).
  - Each loop re-reads queue.jsonl (5 s when idle), but only after the Held() check (L115). A PAUSE file next to the script makes it skip the read entirely.
  - PS 5.1 Move-Item -Force over an existing file is delete-then-move (not atomic). There is a window where Test-Path is true and Get-Content throws, and with 'Stop' that terminates the queue script.
  - Fix: create build\agent3\s4b\PAUSE at a row boundary (no game running), wait >= 10 s, swap via [IO.File]::Replace(tmp, queue, bak) or Copy+verify, run check --installed, then remove PAUSE.
  - holdwatch/holdwatch-m react only to perf-notes\WINDOW-HOLD.txt, not to PAUSE, so PAUSE cannot abort a running game.
  - go-s33stop3..7 absent means those rows can't be selected before the swap anyway.
- (d) Met: M12 agrees with the H0 lock (s33-h0 B5DA7B49, s33-ssim 18364E5D). Correction: ~121-131 s is also H0-locked.
- (e) Base comparison at 230 s vs offsf/basesf (540 s): s4b_check short mode. The 'GONE' after-close lines (Toypad) grow in number with later S, but they are out-of-window by design. Check N5 wording.
- (e) stop1 check.txt: short handling makes logdiff GONE (124, 0 unexpected), attract steps 37/91 and 'all marks 12 differ' non-BASE. Judged route marks first-frame..after-a2 (5) are within the first ~30 s, so they don't depend on S. The verdict needs no change for 191/192 or 229-231.
  - N5 wording: compare against the run's own close (seconds_requested + ~0.1), not 203. Under the H0 lock, read 'first appears in base after the close' H0-relative if the cand's b > base offsf b (148.94): allow base keys up to (b_cand - b_base) earlier.

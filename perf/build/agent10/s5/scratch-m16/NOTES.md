# E10.2 re-check of M16 2.3 r2 + psobin (for M10)

Hashes: 2.3 r2 diff 52341EDF, README 4C4F33C0, both-file (scratch/both, also applytest/t_both and
t_both_rev) 4247ECB9, psobin.ps1 3B3DC537, psobin.py A4AE67DD (psobin lives in build/agent16/psobin/, not
pso/), 2.2 36ED6E02, rating E22DE772: all match. Old 2.3 5CFD12E8 / old both 486D82D0: no copy left
anywhere under build/ or bench/ (searched by hash), so no byte interdiff possible.

git -C DimensionsRecomp apply --check: 2.3 r2 exit 0, 2.2 exit 0 (HEAD a8e8dc8, blob 4484038,
gpu_native worktree clean). Scratch both-order apply NOT re-run (permission prompt timed out);
M16's applytest.log shows both orders exit 0, same file, == hand-edited files; blobs 6b22f81 / b555dce /
8583c5c.

See the send_message report for the tagged findings.

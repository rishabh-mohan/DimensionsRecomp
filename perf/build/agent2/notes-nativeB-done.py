"""Update the RESUME block of perf-notes/agent2-baseline.md with the nativeB result (task #14 done).
Each anchor must match exactly once, otherwise nothing is written. Backs up the notes first. LF only."""
import datetime
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(r"<workspace>")
NOTES = ROOT / "perf-notes" / "agent2-baseline.md"
A2 = ROOT / "build" / "agent2"

raw = NOTES.read_bytes()
if b"\r" in raw:
    sys.exit("STOP: notes contain CR bytes")
t = raw.decode("utf-8")
now = datetime.datetime.now().strftime("%H:%M")

steps = (A2 / "snapB3n-steps.txt").read_text(encoding="utf-8", errors="replace")
m = re.search(r"^(\d\d:\d\d:\d\d) END\s+native-build exit=(\d+) wall=([\d.,]+s)", steps, re.M)
nb_end = f"{m.group(1)}, exit {m.group(2)}, {m.group(3)}" if m else "see snapB3n-steps.txt"


def once(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit(f"STOP: anchor '{what}' matched {n} times; nothing written")
    return text.replace(old, new)


# 1. header time
t = re.sub(r"task #14 from Agent 1; updated \d\d:\d\d\)", f"task #14 from Agent 1; updated {now})", t, count=1)

# 2. status paragraph
pat = re.compile(r"Step 3, nativeB: Agent 1's conditional\n.*?nativeB is my only running job\.\*\*", re.S)
hits = pat.findall(t)
if len(hits) != 1:
    sys.exit(f"STOP: status span matched {len(hits)} times; nothing written")
status = (
    "Step 3, nativeB: DONE,\n"
    "staged 04:34:06 as `nativeB-bin` (`rb-chain.ps1 -Variant nb -Jobs 10` from 04:12:09, once Agent 9 had acked the\n"
    "-GuardOnly diff (04:06) and Agent 8's last -Profile run had ended (04:09:51)); 149 PASS / 0 FAIL / 34 NOTE; hashes\n"
    f"posted to Agents 1, 8, 9 and 10. Task #14 is DONE (`@@done 14` at {now}). Agent 8 profiles on an idle machine from\n"
    "about 04:41 to 05:42 (s0-s2, native3d, the nativeB pair, attract): tell Agent 8 before any build of mine. No builds\n"
    "or game runs from 08:30 (window 4 waits for the user, asleep until about 10:00; questions go to Agent 1). Only\n"
    "Agent 2 builds (<= -j10). Nothing of mine is running.**"
)
t = pat.sub(lambda _m: status, t, count=1)

# 3. staged-bins row after native3d-bin
lines = t.split("\n")
idx = [i for i, l in enumerate(lines) if l.startswith("| `native3d-bin` | 03:46:18 |")]
if len(idx) != 1:
    sys.exit(f"STOP: native3d-bin row matched {len(idx)} times; nothing written")
row = ("| `nativeB-bin` | 04:34:06 | 8, 364.6 MB | 149/0/34, E5CBF30A6132B00E... | 01C4D5A3E36FAC50... | "
       "nativeB = S3d + batch-nolr, native (snapB3), vs native3d-bin; fingerprint `81d1c3a71be3c096`; "
       "map C9259B05689E3AA5... |")
if any(l.startswith("| `nativeB-bin` |") for l in lines):
    sys.exit("STOP: nativeB-bin row already present; nothing written")
lines.insert(idx[0] + 1, row)
t = "\n".join(lines)

# 4. rexruntime bullet
t = once(t, "S3 and S3d D1D66AC3716835AC", "S3, S3d and nativeB D1D66AC3716835AC", "rexruntime bullet")

# 5. step 3 heading in the task #14 section
t = once(t, "- Step 3, nativeB (Agent 1's GO with 4 conditions):",
         "- Step 3, nativeB: DONE 04:34:06, staged as `nativeB-bin` (RESULT at the end of this list). Agent 1's GO\n"
         "  conditions:", "step 3 heading")

# 6. result block
anchor6 = ("    fingerprint to Agents 1, 8, 9 and 10, then `@@done 14`.\n")
result = (
    "  - RESULT (DONE): `rb-chain-nb.txt` 04:12:09-04:34:06, 1316.9 s, exit 0. verify S3d PASS (1.0 s). prep-nb 93.4 s:\n"
    "    install pins 24CE1493 / E60EAF1C, robocopy snap1 -> snapB3 45.2 s, gen-check 870/870. run-nb 1221.4 s:\n"
    f"    configure, gen-check, gate PASS, native build (END {nb_end}), stage. Stage: 149 PASS / 0 FAIL /\n"
    "    34 NOTE; MANIFEST patch rows S1 0 (labelled S1+p1/S1+p2) / S2 18 / S3 28 / S3d 1. Against native3d-bin: exe\n"
    "    differs (PASS), map NOTE; rexruntime, rexgpu-xenos, TracyClient, the wav, the ttf and amd_fidelityfx are\n"
    "    identical.\n"
    "  - Hashes: exe 01C4D5A3E36FAC50C16B6CF8C0B6ACA6FC7D285BE67D66B30B229B7E2FEF5C5C (299,045,376 B); map\n"
    "    C9259B05689E3AA5... (43,689,378 B); rexruntime D1D66AC3716835AC...; rexgpu-xenos EE0A661FB0C30FCB...; MANIFEST\n"
    "    E5CBF30A6132B00E8D8F67E1C7C0B748AED6E486C0B61DDC2BBE06F110F2A966.\n"
    "  - Native GPU fingerprint 81d1c3a71be3c096 (native3d: 335ff2d47268f3a1). Expected: of the fingerprint's inputs, 13\n"
    "    differ from snap1: 12 batch-nolr files in rexlego/generated/default/ and rexlego/legodimensions_config.toml. No\n"
    "    hand-written source differs.\n"
    "  - Disk: snapB3 2.10 GB (24,987 files), snapB3-on 0.92 GB (588 files), nativeB-bin 0.34 GB: 3.36 GB in total (the\n"
    "    estimate was ~3.5). Free C 247.5 GB at 04:35.\n"
)
t = once(t, anchor6, anchor6 + result, "result anchor")

# 7. keep line
t = once(t, "  snapB3 and snapB3-on once made) until Agent 1 says otherwise. Free C: 251.2 GB at 03:46.",
         "  snapB3, snapB3-on and nativeB-bin) until Agent 1 says otherwise. Free C: 247.5 GB at 04:35.", "keep line")

bk_dir = A2 / "notes-backup"
bk_dir.mkdir(exist_ok=True)
bk = bk_dir / ("agent2-baseline.md." + datetime.datetime.now().strftime("%H%M%S"))
shutil.copy2(NOTES, bk)
NOTES.write_bytes(t.encode("utf-8"))
print(f"updated {NOTES} (LF, {len(raw)} -> {len(t.encode('utf-8'))} bytes); backup {bk}; native build END {nb_end}")

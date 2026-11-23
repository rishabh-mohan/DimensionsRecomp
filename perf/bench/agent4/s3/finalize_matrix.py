"""Promote the native3d draft matrix to bench/agent4/matrix-native-threaded.json (task #12, th3 back).

Text replacements only (keeps the draft's formatting and line endings), then a JSON parse check.
"""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
DRAFT = ROOT / "bench/agent4/s3/matrix-native-threaded.native3d-draft.json"
LIVE = ROOT / "bench/agent4/matrix-native-threaded.json"
EXPECT_LIVE = "1F8BC5DD4C82C3E44CFE5F4902E786E21EE7938072C9661F"  # prefix of the 02:20 file

REPLACEMENTS = [
    (
        "the recorder drops them at draw.cpp:2713 as before, so the image does not change. "
        "PENDING: native3d functional n0/n2/n3 checked with check_n_rows.py.",
        "the recorder drops them at draw.cpp:2718-2725 as before, so the image does not change. "
        "native3d functional n0/n2/n3 (Agent 8, build/agent8/matrix/20261122-0452, 04:52-04:59, idle machine) "
        "PASS check_n_rows.py for n2 and n3 with 0 hash=0 lines in all three (native2: 0 / 67,220 / 44,968) "
        "and no new warning type (checked separately by Agent 4, bench/agent4/s3/check-native3d.json, "
        "and Agent 10, build/agent10/nb/).",
    ),
    (
        "All four arms run the same exe and cvars; only the environment differs.",
        "All four arms run the same exe and cvars; only the environment differs. If a later native bin "
        "(an AOT pack for placement VS 0xAC449538 / PS 0xAC448F28, or a shader miss-cache bin) is staged "
        "before this matrix runs, move every arm to it together, after its own functional n-rows pass.",
    ),
]


def main() -> int:
    live_hash = hashlib.sha256(LIVE.read_bytes()).hexdigest().upper()
    if not live_hash.startswith(EXPECT_LIVE):
        print(f"live matrix changed under me: {live_hash}")
        return 2
    raw = DRAFT.read_bytes()
    text = raw.decode("utf-8")
    for old, new in REPLACEMENTS:
        if text.count(old) != 1:
            print(f"replacement target not found exactly once: {old[:60]}...")
            return 3
        text = text.replace(old, new)
    data = json.loads(text)
    arms = data["arms"]
    bins = {a["bin"] for a in arms}
    frames = {a["frames"] for a in arms}
    print("arms", [a["id"] for a in arms], "bins", bins, "frames", frames,
          "repeats", [a.get("repeats", data["repeats"]) for a in arms])
    if bins != {"build/agent2/native3d-bin"} or frames != {"perf"}:
        print("bin/frame source check failed")
        return 4
    if "PENDING" in text:
        print("PENDING still in text")
        return 5
    out = text.encode("utf-8")
    LIVE.write_bytes(out)
    print("crlf", out.count(b"\r\n"), "lf", out.count(b"\n"), "bom", out[:3] == b"\xef\xbb\xbf")
    print("sha256", hashlib.sha256(out).hexdigest().upper(), len(out), "B")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Batch-2 edits for task #20 (Agent 7). Run only after Agent 2 announces S1 is done.

(h)  device.h:93: inline CurrentDrawPreparation (extern thread_local + inline accessor);
     device.cpp:756: delete the out-of-line definition (line 755, the definition of the
     thread_local, stays: it is outside the anonymous namespace).
(p)  device.cpp after ResetFrameCounters(): write the --perf_log_csv row (same 2 lines as
     build/agent7/batch1/perf-csv-rows.patch).
(c') device.cpp:1902-1903: state the rule (c) relies on (Agent 10's #18 review).

Refuses to run unless both files still match the batch-1 copies. CRLF preserved.
Usage: python batch2_edits.py [gpu_native dir]   (default: the live tree)
"""
import hashlib
import os
import sys

LIVE = r"<workspace>\DimensionsRecomp\rexlego\src\gpu_native"
SRC = sys.argv[1] if len(sys.argv) > 1 else LIVE
H = os.path.join(SRC, "device.h")
C = os.path.join(SRC, "device.cpp")
BATCH1 = {H: "12391F5CE364E280", C: "4C15043E486A6225"}


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def replace_once(data, old, new, what):
    n = data.count(old)
    if n != 1:
        sys.exit("%s: expected 1 match, found %d" % (what, n))
    return data.replace(old, new, 1)


def main():
    blobs = {p: open(p, "rb").read() for p in (H, C)}
    for p, prefix in BATCH1.items():
        if not sha(blobs[p]).startswith(prefix):
            sys.exit("%s changed since batch 1 (%s); not editing" % (p, sha(blobs[p])[:16]))

    h = blobs[H]
    h = replace_once(
        h,
        b"\r\nDrawPreparationContext* CurrentDrawPreparation();\r\n",
        b"\r\n// Defined in device.cpp. Inline: draws and texture lookups call this per use.\r\n"
        b"extern thread_local DrawPreparationContext* t_draw_preparation;\r\n"
        b"inline DrawPreparationContext* CurrentDrawPreparation() { return t_draw_preparation; }\r\n",
        "device.h CurrentDrawPreparation declaration")

    c = blobs[C]
    c = replace_once(
        c,
        b"thread_local DrawPreparationContext* t_draw_preparation = nullptr;\r\n"
        b"DrawPreparationContext* CurrentDrawPreparation() { return t_draw_preparation; }\r\n",
        b"thread_local DrawPreparationContext* t_draw_preparation = nullptr;\r\n",
        "device.cpp CurrentDrawPreparation definition")
    c = replace_once(
        c,
        b"    rex::perf::ResetFrameCounters();\r\n  }\r\n",
        b"    rex::perf::ResetFrameCounters();\r\n"
        b"    // Profiler::Flip() also writes the --perf_log_csv row (no-op without it).\r\n"
        b"    rex::perf::WriteCsvFrame();\r\n  }\r\n",
        "device.cpp ResetFrameCounters call")
    c = replace_once(
        c,
        b"  // Window queries enter win32k; make them before g_mutex. g_state and its\r\n"
        b"  // swap chain change only under the recording gate held above.\r\n",
        b"  // Window queries enter win32k; make them before g_mutex. This relies on\r\n"
        b"  // g_state and its swap chain being replaced only under the full recording\r\n"
        b"  // gate (Create, Shutdown), which is held above. Replacing them under\r\n"
        b"  // g_mutex alone (e.g. device-lost recovery) would make these reads race.\r\n",
        "device.cpp window-query comment")

    open(H, "wb").write(h)
    open(C, "wb").write(c)
    print("device.h  ", sha(blobs[H])[:16], "->", sha(h)[:16])
    print("device.cpp", sha(blobs[C])[:16], "->", sha(c)[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())

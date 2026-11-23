# Read-only helper (Agent 6 subagent, W6 expected lines): grep the S4b SDK
# sources for the log statements tied to the W6 switches, and hash-check the
# snap1 copies against the after-hashes in build/agent2/devoff4b-bin/MANIFEST.txt.
import hashlib, os, re, sys

ROOTS = [
    r"build/agent2/snap1/DimensionsRecomp/rexglue-sdk/src",
]
PATTERNS = [
    "C1 keep-watch", "C1 verify", "keep_watch", "Recovered stale physical",
    "Unhandled guest physical", "PhysicalHeap::Protect failed", "Protect failed",
    "S4 upload hash", "upload_hash_log", "slow_frame_log_ms", "slow frame",
    "single_hold_rearm", "full-buffer", "full buffer", "STUCK-LOCK", "STUCK",
    "hold_global_lock",
]
EXTS = (".cpp", ".h", ".hpp", ".cc", ".inl", ".c")

HASHES = {
    "include/rex/graphics/shared_memory.h": "82A66445ED98B091",
    "include/rex/system/xmemory.h": "5A70782EF00F0FB6",
    "src/graphics/primitive_processor.cpp": "470BA4BED73B2ABF",
    "src/graphics/shared_memory.cpp": "A4A31038ABDFF94A",
    "src/system/xmemory.cpp": "BCA5E1CF63686E73",
    "src/graphics/d3d12/shared_memory.cpp": "2A5ADF13B5E433F1",
    "src/graphics/d3d12/command_processor.cpp": "027204B53A271D69",
    "include/rex/graphics/d3d12/command_processor.h": "67F4E8380C879377",
    "include/rex/graphics/d3d12/deferred_command_list.h": "9F6CC70A6922232D",
    "src/graphics/d3d12/deferred_command_list.cpp": "30FF57446EFB5D76",
    "src/core/timer_queue.cpp": "015C04A22DACC592",
    "src/graphics/d3d12/pipeline_cache.cpp": "DA77744302CFC149",
}

def main():
    sdk = "build/agent2/snap1/DimensionsRecomp/rexglue-sdk"
    print("=== hash check (snap1 vs MANIFEST S4b after-hash prefixes)")
    for rel, want in HASHES.items():
        p = os.path.join(sdk, rel)
        if not os.path.exists(p):
            print("MISSING", rel)
            continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest().upper()
        print(("OK  " if h.startswith(want) else "DIFF"), rel, h[:16], "want", want,
              "mtime", __import__("time").strftime("%Y-%m-%d %H:%M:%S", __import__("time").localtime(os.path.getmtime(p))))
    rx = re.compile("|".join(re.escape(x) for x in PATTERNS))
    for root in ROOTS:
        print("=== ROOT", root)
        for dp, dn, fn in os.walk(root):
            for f in fn:
                if not f.endswith(EXTS):
                    continue
                p = os.path.join(dp, f)
                try:
                    lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
                except OSError:
                    continue
                for i, ln in enumerate(lines, 1):
                    if rx.search(ln):
                        print("%s:%d: %s" % (os.path.relpath(p, root), i, ln.strip()[:220]))

if __name__ == "__main__":
    main()

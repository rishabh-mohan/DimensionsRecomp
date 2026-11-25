"""Stage diagnostic (d) for #33 (Agent 10 S2) as paper patches (M6, session 3, S3T-6).

Diagnostic (d): count and log resolves issued after draws were skipped for a pipeline in creation,
and whether each such resolve target is later resolved again with no skipped draws ("healed").
Cvar d3d12_resolve_after_drop_log (bool, default false, kRequiresRestart). With it false the only
change is one cvar read per skipped draw and per resolve.

Never touches the live SDK: blobs come from `git show 5350b1d:<path>`; work happens in
build/agent6/s33-popin/scratch/diagd*/ with GIT_CEILING_DIRECTORIES set.
Writes:
  s33-diagd-on-nohunk5.patch    stacked: apply after s33-popin-nohunk5.patch (1 file)
  s33-popin-nohunk5-diagd.patch combined: nohunk5 + (d) against 5350b1d (4 files)
Then verifies both apply (check, apply, reverse check, no "Skipped patch") on fresh scratch copies
and give byte-identical results. Exit 0 = all good.
"""
import difflib
import hashlib
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
WS = HERE.parents[2]
SDK = WS / "DimensionsRecomp" / "rexglue-sdk"
BASE = "5350b1de99276b7a7be701bf00914f1ee58ce9bc"
FILES = [
    "include/rex/graphics/d3d12/pipeline_cache.h",
    "src/graphics/d3d12/command_processor.cpp",
    "src/graphics/d3d12/pipeline_cache.cpp",
    "src/graphics/frame_stats.h",
]
CP = "src/graphics/d3d12/command_processor.cpp"
NOHUNK5 = HERE / "s33-popin-nohunk5.patch"
NOHUNK5_SHA = "57CFA8ADF1E90079"
STACKED = HERE / "s33-diagd-on-nohunk5.patch"
COMBINED = HERE / "s33-popin-nohunk5-diagd.patch"
SCRATCH = HERE / "scratch"
fails = []

# (anchor, text inserted after the anchor). Each anchor must occur exactly once.
EDITS = [
    (
        '                    "readback_resolve_max_kb value for a title)")\n'
        "    .lifecycle(rex::cvar::Lifecycle::kHotReload);\n",
        "\n"
        "// #33 diagnostic (d) (Agent 10 S2): log resolves that follow draws skipped while\n"
        "// their pipeline was in creation. A render-to-texture pass that loses draws and\n"
        "// is resolved only once stays wrong until it's drawn again; these lines measure\n"
        "// how often that can happen, with d3d12_pipeline_creation_no_wait on or off.\n"
        'REXCVAR_DEFINE_BOOL(d3d12_resolve_after_drop_log, false, "GPU/D3D12",\n'
        '                    "Log resolves issued after draws were skipped for a pipeline in "\n'
        '                    "creation, and when each such resolve target is next resolved with "\n'
        '                    "no skipped draws (diagnostic for d3d12_pipeline_creation_no_wait)")\n'
        "    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);\n",
    ),
    (
        "std::atomic<uint64_t> memexport_full_buffer_draws{0};\n",
        "\n"
        "// Diagnostic (d) state. Only touched on the command thread (IssueDraw,\n"
        "// IssueCopy), and only while d3d12_resolve_after_drop_log is set. Skipped draws\n"
        "// aren't matched to render targets: every skipped draw since the last resolve\n"
        "// counts against the next one (an upper bound on the exposure).\n"
        "struct ResolveAfterDrop {\n"
        "  uint64_t drops_since_resolve = 0;\n"
        "  uint64_t resolves = 0;\n"
        "  uint64_t after_drop = 0;\n"
        "  uint64_t healed = 0;\n"
        "  uint64_t lines = 0;\n"
        "  // Resolve destination base -> the resolve ordinal that last followed drops.\n"
        "  std::unordered_map<uint32_t, uint64_t> tainted;\n"
        "};\n"
        "ResolveAfterDrop resolve_after_drop;\n"
        "constexpr uint64_t kResolveAfterDropMaxLines = 4096;\n"
        "\n"
        "// A resolve to dest_base was just recorded. copies: it writes memory (it isn't\n"
        "// clear-only).\n"
        "void NoteResolveAfterDrop(uint32_t dest_base, bool copies) {\n"
        "  ResolveAfterDrop& d = resolve_after_drop;\n"
        "  ++d.resolves;\n"
        "  const uint64_t drops = d.drops_since_resolve;\n"
        "  d.drops_since_resolve = 0;\n"
        "  if (!copies) {\n"
        "    return;\n"
        "  }\n"
        "  if (drops) {\n"
        "    ++d.after_drop;\n"
        "    const bool first = d.tainted.insert_or_assign(dest_base, d.resolves).second;\n"
        "    if (d.lines < kResolveAfterDropMaxLines) {\n"
        "      ++d.lines;\n"
        "      REXGPU_INFO(\n"
        '          "resolve after drop: dest {:08X} after {} skipped draws ({}) | resolves {}, "\n'
        '          "after drops {}, healed {}, tainted {}",\n'
        '          dest_base, drops, first ? "new" : "again", d.resolves, d.after_drop, d.healed,\n'
        "          d.tainted.size());\n"
        "    }\n"
        "  } else if (d.tainted.erase(dest_base)) {\n"
        "    ++d.healed;\n"
        "    if (d.lines < kResolveAfterDropMaxLines) {\n"
        "      ++d.lines;\n"
        "      REXGPU_INFO(\n"
        '          "resolve after drop: dest {:08X} resolved clean again | resolves {}, "\n'
        '          "after drops {}, healed {}, tainted {}",\n'
        "          dest_base, d.resolves, d.after_drop, d.healed, d.tainted.size());\n"
        "    }\n"
        "  }\n"
        "  if (d.lines == kResolveAfterDropMaxLines) {\n"
        "    ++d.lines;\n"
        '    REXGPU_INFO("resolve after drop: {} lines logged, no more from here on",\n'
        "                kResolveAfterDropMaxLines);\n"
        "  }\n"
        "}\n",
    ),
    (
        "    if (skip_draw) {\n"
        "      frame_stats::Add(frame_stats::kDroppedDraw, 0);\n",
        "      if (REXCVAR_GET(d3d12_resolve_after_drop_log)) {\n"
        "        ++resolve_after_drop.drops_since_resolve;\n"
        "      }\n",
    ),
    (
        "    resolved = IssueCopy_ReadbackResolvePath();\n"
        "  }\n",
        "  if (resolved && REXCVAR_GET(d3d12_resolve_after_drop_log)) {\n"
        "    NoteResolveAfterDrop(register_file_->values[XE_GPU_REG_RB_COPY_DEST_BASE],\n"
        "                         register_file_->Get<reg::RB_COPY_CONTROL>().copy_command !=\n"
        "                             xenos::CopyCommand::kNull);\n"
        "  }\n",
    ),
]


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        fails.append(msg)


def git(args, cwd, env=None):
    # core.autocrlf=false: the system gitconfig sets autocrlf=true, and outside the SDK repo
    # (no .gitattributes `eol=lf`) git apply would write CRLF files.
    p = subprocess.run(["git", "-c", "core.autocrlf=false"] + args, cwd=cwd, env=env,
                       capture_output=True)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace").strip()


def fresh(name, blobs):
    d = SCRATCH / name
    if d.exists():
        shutil.rmtree(d)
    for f in FILES:
        (d / f).parent.mkdir(parents=True, exist_ok=True)
        (d / f).write_bytes(blobs[f])
    return d


def apply(d, patch, label):
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(SCRATCH))
    rc, _ = git(["rev-parse", "--show-toplevel"], d, env)
    check(rc != 0, "%s: no git repo above %s" % (label, d.name))
    for args in (["apply", "--check", "--verbose"], ["apply", "--verbose"],
                 ["apply", "-R", "--check", "--verbose"]):
        rc, text = git(args + [str(patch)], d, env)
        ok = rc == 0 and "Skipped patch" not in text and "offset" not in text
        check(ok, "%s: git %s %s -> exit %d%s" % (
            label, " ".join(args), patch.name, rc, "" if ok else "\n" + text))


def udiff(f, a, b):
    out = list(difflib.unified_diff(a.decode().splitlines(keepends=True),
                                    b.decode().splitlines(keepends=True),
                                    "a/" + f, "b/" + f, n=3))
    if not out:
        return ""
    return "diff --git a/%s b/%s\n" % (f, f) + "".join(out)


nb = NOHUNK5.read_bytes()
check(sha(nb).startswith(NOHUNK5_SHA), "nohunk5 patch sha256 %s" % sha(nb)[:16])
blobs = {}
for f in FILES:
    p = subprocess.run(["git", "show", "%s:%s" % (BASE, f)], cwd=SDK, capture_output=True)
    check(p.returncode == 0, "blob %s read from 5350b1d" % f)
    blobs[f] = p.stdout

d1 = fresh("diagd-build", blobs)
apply(d1, NOHUNK5, "nohunk5 on 5350b1d")
mid = {f: (d1 / f).read_bytes() for f in FILES}
text = mid[CP].decode()
for anchor, add in EDITS:
    n = text.count(anchor)
    check(n == 1, "anchor found once (%d): %r" % (n, anchor.splitlines()[0][:60]))
    text = text.replace(anchor, anchor + add, 1)
check("\r" not in text, "nohunk5 result is LF only")
for _, add in EDITS:
    for line in add.splitlines():
        if len(line) > 100:
            check(False, "added line over 100 columns: %r" % line)
final = dict(mid)
final[CP] = text.encode()

STACKED.write_bytes(udiff(CP, mid[CP], final[CP]).encode())
COMBINED.write_bytes("".join(udiff(f, blobs[f], final[f]) for f in FILES).encode())
for p in (STACKED, COMBINED):
    b = p.read_bytes()
    print("wrote %s: %d bytes, %d lines, sha256 %s" % (p.name, len(b), b.count(b"\n"), sha(b)))

d2 = fresh("diagd-stacked", blobs)
apply(d2, NOHUNK5, "stacked step 1 (nohunk5)")
apply(d2, STACKED, "stacked step 2 (diag d)")
d3 = fresh("diagd-combined", blobs)
apply(d3, COMBINED, "combined")
for f in FILES:
    a, b = (d2 / f).read_bytes(), (d3 / f).read_bytes()
    check(a == b == final[f], "%s: stacked = combined = generated (sha256 %s)" % (f, sha(b)[:16]))
rc, st = git(["status", "--porcelain", "--", "src", "include"], SDK)
check(rc == 0 and st == "", "live SDK src/include still clean")
print("result: %s" % ("PASS" if not fails else "FAIL (%d)" % len(fails)))
sys.exit(1 if fails else 0)

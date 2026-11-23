#!/usr/bin/env python3
"""Check a LEGO_DUMP_MISSING_SHADERS run (Agent 7, task #22 step 1).

Usage:
  python bench\\agent7\\shader_dump_check.py <run dir> [--bin build\\agent2\\native3d-bin] [--dumps DIR] [-o OUT]

Reads <run>\\shader-dumps\\{placement-raw,placement-containers}\\{vs,ps}-<16 hex>.bin. These are written by
DumpMissingShader (gpu_native/shaders.cpp:355-391), called from CaptureMissingPlacementShader (:146-207).
It also reads <run>\\game.log.

For every dump it reports the size, sha256, the count of non-zero bytes and the first words (big-endian u32).

Container dumps are parsed with the layout that CaptureMissingPlacementShader writes:
  - the virtual section: virtual_size bytes, starting with ShaderContainer (d3d.h:116, big-endian:
    flags, virtual_size, physical_size, field_0c, constant_table_offset, definition_table_offset,
    shader_offset, field_1c, field_20);
  - 4 bytes: a copy of header bytes 8..11 (physical_size), the archive marker;
  - the physical microcode: physical_size bytes.
It checks that flags & ~1 == 0x102A1100, the stage bit (1 = vertex), the sizes and the marker.

A raw dump holds the first min(2048, 4096 - (backing & 4095), readable) bytes of the physical microcode.
The file is named by XXH3-64 of the first 8 bytes, which is the "prefix=" in the "missing from AOT index"
warnings. That links each raw file to a warned shader address. The raw dumps are also cross-checked against
the containers' physical sections.

game.log lines checked:
  - dumped / failed to dump / cannot create shader dump directory;
  - "missing from AOT index" (address, backing, prefix, words);
  - "pool copy byte verification failed" (the XXH3 pool-copy check that the same env var enables,
    hooks_buffer.cpp:331-347).
With --bin it also runs bin_manifest_check on the bin dir, because nothing may be written there.

Exit code 0: the dump dir has at least one file, and the bin check passes when one is asked for.
The PS zero check is reported, not judged.
Stdlib only, one thread.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NAME_RE = re.compile(r"^(vs|ps)-([0-9A-Fa-f]{16})\.bin$")
WARN_RE = re.compile(r"placement (vertex|pixel) shader 0x([0-9A-Fa-f]{8}) backing 0x([0-9A-Fa-f]{8}) "
                     r"prefix=0x([0-9A-Fa-f]{16}) words=([0-9A-Fa-f]{8}(?: [0-9A-Fa-f]{8}){3}) missing from AOT index")
LOG_PATTERNS = (
    ("dumped", "dumped missing shader"),
    ("dump_failed", "failed to dump missing shader"),
    ("dir_failed", "cannot create shader dump directory"),
    ("missing_aot", "missing from AOT index"),
    ("pool_verify_failed", "pool copy byte verification failed"),
    ("hash0", "shader cache miss: hash=0x0"),
)
CONTAINER_FLAGS = 0x102A1100
HEADER_FIELDS = ("flags", "virtual_size", "physical_size", "field_0c", "constant_table_offset",
                 "definition_table_offset", "shader_offset", "field_1c", "field_20")


def words_be(data: bytes, count: int = 8) -> list[int]:
    n = min(count, len(data) // 4)
    return list(struct.unpack(f">{n}I", data[:4 * n])) if n else []


def fmt_words(ws: list[int]) -> str:
    return " ".join(f"{w:08X}" for w in ws)


def parse_container(data: bytes, stage: str) -> dict:
    """Parse one placement-containers dump. Returns a dict with 'ok', 'problems', 'header', 'physical'."""
    res: dict = {"ok": False, "problems": [], "header": {}, "physical": b""}
    if len(data) < 0x24:
        res["problems"].append(f"short file ({len(data)} bytes < 0x24 header)")
        return res
    hdr = dict(zip(HEADER_FIELDS, struct.unpack(">9I", data[:0x24])))
    res["header"] = hdr
    flags, vsz, psz = hdr["flags"], hdr["virtual_size"], hdr["physical_size"]
    if (flags & 0xFFFFFFFE) != CONTAINER_FLAGS:
        res["problems"].append(f"flags {flags:08X} & ~1 != {CONTAINER_FLAGS:08X}")
    want_bit = 1 if stage == "vs" else 0
    if (flags & 1) != want_bit:
        res["problems"].append(f"stage bit {flags & 1} != {want_bit} for {stage}")
    if not (0x24 <= vsz <= 65536):
        res["problems"].append(f"virtual_size {vsz} out of range")
    if not (8 <= psz <= 65536):
        res["problems"].append(f"physical_size {psz} out of range")
    if len(data) != vsz + 4 + psz:
        res["problems"].append(f"file size {len(data)} != virtual {vsz} + 4 + physical {psz}")
    if vsz + 4 <= len(data):
        if data[vsz:vsz + 4] != data[8:12]:
            res["problems"].append(f"marker {data[vsz:vsz + 4].hex()} != header bytes 8..11 {data[8:12].hex()}")
        res["physical"] = data[vsz + 4:vsz + 4 + psz]
    res["ok"] = not res["problems"]
    return res


def scan_dumps(root: str) -> list[dict]:
    out = []
    if not os.path.isdir(root):
        return out
    for dirpath, _dirs, files in os.walk(root):
        for fn in sorted(files):
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root)
            category = os.path.relpath(dirpath, root)
            with open(path, "rb") as fh:
                data = fh.read()
            m = NAME_RE.match(fn)
            item = {
                "rel": rel, "category": category, "name": fn, "stage": m.group(1).lower() if m else "?",
                "hash": m.group(2).upper() if m else "", "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest().upper()[:16],
                "nonzero": sum(1 for b in data if b), "words": words_be(data), "data": data,
            }
            if category == "placement-containers" and m:
                item["container"] = parse_container(data, item["stage"])
            out.append(item)
    out.sort(key=lambda d: (d["category"], d["stage"], d["name"]))
    return out


def scan_log(path: str) -> tuple[dict, list[str], dict]:
    counts = {k: 0 for k, _ in LOG_PATTERNS}
    keep: list[str] = []
    warned: dict = {}
    if not os.path.exists(path):
        return counts, keep, warned
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n")
            for key, pat in LOG_PATTERNS:
                if pat in line:
                    counts[key] += 1
                    if key in ("dumped", "dump_failed", "dir_failed", "pool_verify_failed") and len(keep) < 40:
                        keep.append(line)
            m = WARN_RE.search(line)
            if m:
                stage = "vs" if m.group(1) == "vertex" else "ps"
                key = (stage, m.group(2).upper())
                w = warned.setdefault(key, {"backing": m.group(3).upper(), "prefix": m.group(4).upper(),
                                            "words": m.group(5).upper(), "count": 0})
                w["count"] += 1
    return counts, keep, warned


def report(run: str, dumps_root: str, bin_dir: str | None) -> tuple[list[str], int]:
    lines: list[str] = []
    problems = 0
    dumps = scan_dumps(dumps_root)
    counts, keep, warned = scan_log(os.path.join(run, "game.log"))
    lines.append(f"shader_dump_check: run {run}")
    lines.append(f"  dumps root {dumps_root}: {'present' if os.path.isdir(dumps_root) else 'MISSING'}, {len(dumps)} file(s)")
    if not dumps:
        problems += 1
    lines.append("  game.log: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    for line in keep:
        lines.append("    " + line[line.find("Native GPU"):] if "Native GPU" in line else "    " + line)
    lines.append("")
    lines.append("== dump files (category, file, bytes, sha256, non-zero bytes, first words)")
    for d in dumps:
        lines.append(f"  {d['category']:22s} {d['name']:24s} {d['size']:6d} {d['sha256']} nz={d['nonzero']:5d}  {fmt_words(d['words'])}")
        c = d.get("container")
        if c is not None:
            h = c["header"]
            phys = c["physical"]
            hdr_txt = " ".join(f"{k}={v:#x}" for k, v in h.items()) if h else "-"
            lines.append(f"      container {'OK' if c['ok'] else 'BAD: ' + '; '.join(c['problems'])}; {hdr_txt}")
            lines.append(f"      physical {len(phys)} B, non-zero {sum(1 for b in phys if b)}, first words {fmt_words(words_be(phys))}")
    lines.append("")
    lines.append("== warned shaders (game.log) vs raw dumps (raw name = XXH3 of the first 8 bytes = prefix)")
    raw = {(d["stage"], d["hash"]): d for d in dumps if d["category"] == "placement-raw"}
    for (stage, addr), w in sorted(warned.items()):
        r = raw.get((stage, w["prefix"]))
        lines.append(f"  {stage} 0x{addr} backing 0x{w['backing']} prefix {w['prefix']} words {w['words']} x{w['count']}: "
                     + (f"raw {r['name']} ({r['size']} B, non-zero {r['nonzero']})" if r else "NO raw dump"))
    lines.append("")
    lines.append("== raw vs container physical sections (same stage; compared over the shorter length)")
    conts = [d for d in dumps if d.get("container") and d["container"]["physical"]]
    for (stage, h), r in sorted(raw.items()):
        hits = []
        for c in conts:
            if c["stage"] != stage:
                continue
            phys = c["container"]["physical"]
            n = min(len(phys), len(r["data"]))
            if n and phys[:n] == r["data"][:n]:
                hits.append(f"{c['name']} ({n} B)")
        lines.append(f"  raw {r['name']}: " + (", ".join(hits) if hits else "no container matches"))
    lines.append("")
    lines.append("== per stage")
    for stage in ("vs", "ps"):
        sr = [d for d in dumps if d["stage"] == stage and d["category"] == "placement-raw"]
        sc = [d for d in dumps if d["stage"] == stage and d["category"] == "placement-containers"]
        zero_c = [d for d in sc if d["container"]["physical"] and not any(d["container"]["physical"])]
        nz_c = [d for d in sc if d["container"]["physical"] and any(d["container"]["physical"])]
        lines.append(f"  {stage}: raw {len(sr)} (all-zero {sum(1 for d in sr if d['nonzero'] == 0)}), "
                     f"containers {len(sc)} (physical all-zero {len(zero_c)}, non-zero {len(nz_c)})")
        for d in nz_c[:4]:
            lines.append(f"      non-zero container {d['name']}: physical {len(d['container']['physical'])} B, "
                         f"first words {fmt_words(words_be(d['container']['physical']))}")
    if bin_dir:
        import bin_manifest_check as bmc
        out, bad = bmc.check(bin_dir, os.path.join(bin_dir, "MANIFEST.txt"), True)
        lines.append("")
        lines.append(f"== bin dir check: {bin_dir}: {'PASS' if bad == 0 else 'FAIL'} ({bad} problem(s))")
        lines.extend("  " + x for x in out if not x.startswith("ok "))
        problems += bad
    lines.append("")
    lines.append(f"RESULT: {'PASS' if problems == 0 else 'FAIL'} ({problems} problem(s))")
    return lines, problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--dumps", default=None, help="default: <run>/shader-dumps")
    ap.add_argument("--bin", default=None, help="bin dir to check against its MANIFEST.txt")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args(argv)
    dumps_root = args.dumps or os.path.join(args.run_dir, "shader-dumps")
    lines, problems = report(args.run_dir, dumps_root, args.bin)
    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

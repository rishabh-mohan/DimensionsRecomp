#!/usr/bin/env python3
"""Placement shader dumps: is the physical section real Xenos microcode or a capture artifact?

Usage (repo root):
  python bench\\agent7\\sd\\ps_words_check.py [<shader-dumps dir>] [-o build\\agent7\\sd\\ps-words-check.txt]

Container dump layout (shaders.cpp CaptureMissingPlacementShader, :146-206):
  virtual section (virtual_size bytes, ShaderContainer at 0, d3d.h:116), a 4-byte marker
  (copy of header bytes 8..11), then the physical section (physical_size bytes).

For every container it prints:
  - the header and the words at constant_table_offset, definition_table_offset and shader_offset;
  - the physical section as big-endian words, with a float reading where it looks like one;
  - every word offset in the physical section where a well-formed control-flow program starts.
Xenos CF instructions are 48 bits, packed two per 3 dwords; opcode = bits 44-47 (Xenia ucode.h).
A program counts as well-formed if it reaches an *_END exec within 32 CF instructions, has at
least one exec with count > 0, every exec slot range lies inside the section, and the first
exec's address equals the CF block length (the XDK compiler puts ALU/fetch slots right after it).
Raw dumps (placement-raw) are compared against the container physical sections.
"""
from __future__ import annotations

import argparse
import math
import os
import struct
import sys

DEFAULT = r"build\agent8\matrix\20261122-0509\runs\0509-sd-r1\shader-dumps"
HEADER = ("flags", "virtual_size", "physical_size", "field_0c", "constant_table_offset",
          "definition_table_offset", "shader_offset", "field_1c", "field_20")
CF = {0: "NOP", 1: "EXEC", 2: "EXEC_END", 3: "COND_EXEC", 4: "COND_EXEC_END", 5: "COND_PRED_EXEC",
      6: "COND_PRED_EXEC_END", 7: "LOOP_START", 8: "LOOP_END", 9: "COND_CALL", 10: "RETURN",
      11: "COND_JMP", 12: "ALLOC", 13: "COND_EXEC_PRED_CLEAN", 14: "COND_EXEC_PRED_CLEAN_END",
      15: "MARK_VS_FETCH_DONE"}
EXECS = {1, 2, 3, 4, 5, 6, 13, 14}
ENDS = {2, 4, 6, 14}
ALLOC_TYPES = {0: "none", 1: "position", 2: "interpolators/colors", 3: "memory"}


def be_words(data: bytes) -> list[int]:
    n = len(data) // 4
    return list(struct.unpack(f">{n}I", data[:4 * n]))


def f32(w: int) -> float:
    return struct.unpack(">f", struct.pack(">I", w))[0]


def floatish(w: int) -> str:
    if w == 0:
        return "0"
    v = f32(w)
    if math.isfinite(v) and 1e-4 <= abs(v) <= 1e5:
        return f"{v:.6g}"
    return "-"


def cf_list(words: list[int], start: int, limit: int = 32) -> list[tuple[int, int]]:
    out = []
    i = start
    while i + 3 <= len(words) and len(out) < limit:
        d0, d1, d2 = words[i], words[i + 1], words[i + 2]
        out.append((d0, d1 & 0xFFFF))
        out.append((((d1 >> 16) | (d2 << 16)) & 0xFFFFFFFF, d2 >> 16))
        i += 3
    return out


def describe(d0: int, d1: int) -> str:
    op = (d1 >> 12) & 0xF
    name = CF[op]
    if op in EXECS:
        return f"{name} addr={d0 & 0xFFF} count={(d0 >> 12) & 7} seq={(d0 >> 16) & 0xFFF:03X}"
    if op == 12:
        return f"{name} size={d0 & 7} type={ALLOC_TYPES[(d1 >> 9) & 3]}"
    if op in (7, 8, 9, 11):
        return f"{name} addr={d0 & 0x3FF} d0={d0:08X} d1={d1:04X}"
    return f"{name} d0={d0:08X} d1={d1:04X}"


def program_at(words: list[int], start: int) -> tuple[bool, list[str], str]:
    """Decode a CF program at word offset start. Returns (well_formed, lines, reason)."""
    lines, n_cf, execs, end_seen, allocs = [], 0, [], False, []
    for d0, d1 in cf_list(words, start):
        op = (d1 >> 12) & 0xF
        n_cf += 1
        lines.append(describe(d0, d1))
        if op in EXECS:
            execs.append((d0 & 0xFFF, (d0 >> 12) & 7))
        if op == 12:
            allocs.append((d1 >> 9) & 3)
        if op in ENDS:
            end_seen = True
            break
    if not end_seen:
        return False, lines, "no *_END within 32 CF instructions"
    slots_total = (len(words) - start) // 3
    cf_slots = (n_cf + 1) // 2
    used = [(a, c) for a, c in execs if c > 0]
    if not used:
        return False, lines, "no exec with count > 0"
    for a, c in used:
        if a < cf_slots or a + c > slots_total:
            return False, lines, f"exec slots {a}+{c} outside [{cf_slots}, {slots_total}]"
    if used[0][0] != cf_slots:
        return False, lines, f"first exec addr {used[0][0]} != CF block length {cf_slots}"
    last = max(a + c for a, c in used)
    reason = (f"well-formed: {n_cf} CF in {cf_slots} slots, instruction slots {cf_slots}..{last - 1}, "
              f"code {3 * 4 * last} B of {4 * (len(words) - start)} B from here, allocs "
              f"{[ALLOC_TYPES[t] for t in allocs]}")
    return True, lines, reason


def parse_container(data: bytes) -> dict:
    hdr = dict(zip(HEADER, struct.unpack_from(">9I", data, 0)))
    vsz, psz = hdr["virtual_size"], hdr["physical_size"]
    ok = len(data) == vsz + 4 + psz
    return {"hdr": hdr, "ok": ok, "virtual": data[:vsz], "marker": data[vsz:vsz + 4],
            "physical": data[vsz + 4:vsz + 4 + psz]}


def dump_words(lines: list[str], ws: list[int], base: int, label: str, per: int = 4) -> None:
    for i in range(0, len(ws), per):
        chunk = ws[i:i + per]
        hexs = " ".join(f"{w:08X}" for w in chunk)
        fl = " ".join(f"{floatish(w):>9}" for w in chunk)
        lines.append(f"    {label}+{base + 4 * i:04X}  {hexs:<36}  {fl}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=DEFAULT)
    ap.add_argument("-o", "--out")
    args = ap.parse_args()
    lines: list[str] = [f"ps_words_check.py: {args.root}", ""]
    conts: dict[str, dict] = {}
    cdir = os.path.join(args.root, "placement-containers")
    for name in sorted(os.listdir(cdir)):
        data = open(os.path.join(cdir, name), "rb").read()
        c = parse_container(data)
        conts[name] = c
        h = c["hdr"]
        lines.append("=" * 100)
        lines.append(f"{name}: {len(data)} B; " + ", ".join(
            f"{k}={v:08X}" if k == "flags" else f"{k}={v}" for k, v in h.items()))
        lines.append(f"  size check {'OK' if c['ok'] else 'BAD'}; marker {c['marker'].hex().upper()}")
        v = c["virtual"]
        for key in ("constant_table_offset", "definition_table_offset", "shader_offset"):
            off = h[key]
            if 0 < off < len(v):
                ws = be_words(v[off:off + 64])
                lines.append(f"  virtual @ {key} (0x{off:X}):")
                dump_words(lines, ws, off, "v")
        ws = be_words(c["physical"])
        lines.append(f"  physical section: {len(ws)} words, {sum(1 for w in ws if w)} non-zero")
        dump_words(lines, ws, 0, "p")
        found = []
        for s in range(0, len(ws) - 2):
            okp, plines, reason = program_at(ws, s)
            if okp:
                found.append((s, plines, reason))
        lines.append(f"  well-formed CF programs in the physical section: {len(found)}")
        for s, plines, reason in found:
            lines.append(f"    at word {s} (byte 0x{4 * s:X}): {reason}")
            for pl in plines:
                lines.append(f"      {pl}")
        okp, plines, reason = program_at(ws, 0)
        if not okp:
            lines.append(f"  at word 0: NOT a program ({reason}); first CF: {plines[:4]}")
        lines.append("")
    rdir = os.path.join(args.root, "placement-raw")
    lines.append("=" * 100)
    lines.append("raw dumps vs container physical sections (exact prefix match over the shorter length)")
    for name in sorted(os.listdir(rdir)):
        raw = open(os.path.join(rdir, name), "rb").read()
        hits = []
        for cname, c in conts.items():
            p = c["physical"]
            n = min(len(p), len(raw))
            if n and raw[:n] == p[:n]:
                hits.append(f"{cname} ({n} B)")
        rw = be_words(raw[:64])
        lines.append(f"  {name} ({len(raw)} B): first words {' '.join(f'{w:08X}' for w in rw[:8])}; "
                     f"matches: {', '.join(hits) if hits else 'none'}")
    text = "\n".join(lines) + "\n"
    if args.out:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

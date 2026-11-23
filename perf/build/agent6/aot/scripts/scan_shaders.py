#!/usr/bin/env python3
"""Scan extracted shader assets exactly like gradient_compiler's directory mode (main.cpp lines 96-158).

Reproduces the container detection loop (ShaderContainer = 9 big-endian u32 = 36 bytes, flags & 0xFFFFFF00 ==
0x102A1100, optional 4-byte physicalSize marker after the virtual section, field1C == field20 == 0, byte-wise
scan, skip dataSize after a hit), the first-wins de-duplication (blake2b-128 of the container bytes stands in
for XXH3-64; identical equivalence classes barring collisions), and sourceName = file stem (+ ".<containerIndex>"
for the container index within the file when > 0).

Subcommands:
  scan   <assets-dir> <out-json>                      corpus statistics + per-unique-shader table (TSV)
  sample <assets-dir> <out-dir> --count N [--seed S]  write N unique containers as standalone files (systematic
                                                      sample over the size-sorted corpus); gradient_compiler finds
                                                      exactly one container per file with the same hash/size.
  shard  <assets-dir> <out-dir> --shards K            write every unique container as a standalone file named
                                                      "<sourceName>.bin" into K size-balanced shard dirs (only if
                                                      a sharded compile is approved).
"""
import argparse
import hashlib
import json
import os
import random
import struct
import sys
import time

MAGIC = b"\x10\x2a\x11"
HDR = 36


def iter_files(root):
    """Mimic std::filesystem::recursive_directory_iterator order on Windows (native FindNextFile order,
    descend into a directory right after it is listed)."""
    with os.scandir(root) as it:
        entries = list(it)
    for e in entries:
        if e.is_dir(follow_symlinks=False):
            yield from iter_files(e.path)
        else:
            yield e.path


def be32(b, o):
    return struct.unpack_from(">I", b, o)[0]


def scan_file(data):
    """Yield (offset, dataSize, flags) for every container the C++ loop accepts, in order."""
    n = len(data)
    if n <= HDR:
        return
    limit = n - HDR - 1  # loop runs while i < limit
    i = 0
    while True:
        j = data.find(MAGIC, i)
        if j < 0 or j >= limit:
            return
        v = be32(data, j + 4)
        p = be32(data, j + 8)
        pad = 0
        if v + 4 <= n - j and be32(data, j + v) == p:
            pad = 4
        size = v + p + pad
        if size <= n - j and be32(data, j + 28) == 0 and be32(data, j + 32) == 0:
            if size == 0:
                raise RuntimeError("zero-size container would loop forever in gradient_compiler")
            yield j, size, be32(data, j)
            i = j + size
        else:
            i = j + 1


def scan(root):
    shaders = {}  # digest -> record (first wins)
    order = []
    files = 0
    files_with = 0
    containers = 0
    total_bytes = 0
    per_archive = {}
    for path in iter_files(root):
        files += 1
        with open(path, "rb") as fh:
            data = fh.read()
        total_bytes += len(data)
        rel = os.path.relpath(path, root)
        archive = rel.split(os.sep, 1)[0]
        stem = os.path.splitext(os.path.basename(path))[0]
        idx = 0
        found = False
        for off, size, flags in scan_file(data):
            containers += 1
            d = hashlib.blake2b(data[off:off + size], digest_size=16).hexdigest()
            a = per_archive.setdefault(archive, {"containers": 0, "new_unique": 0})
            a["containers"] += 1
            if d not in shaders:
                name = stem if idx == 0 else f"{stem}.{idx}"
                shaders[d] = {"digest": d, "path": rel, "offset": off, "size": size,
                              "flags": flags, "sourceName": name}
                order.append(d)
                a["new_unique"] += 1
                found = True
            idx += 1
        files_with += 1 if idx else 0
    return shaders, order, {"files": files, "files_with_containers": files_with, "containers": containers,
                            "unique": len(shaders), "asset_bytes": total_bytes, "per_archive": per_archive}


def read_container(root, rec):
    with open(os.path.join(root, rec["path"]), "rb") as fh:
        fh.seek(rec["offset"])
        return fh.read(rec["size"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["scan", "sample", "shard"])
    ap.add_argument("assets")
    ap.add_argument("out")
    ap.add_argument("--count", type=int, default=50)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--shards", type=int, default=8)
    a = ap.parse_args()
    t0 = time.time()
    shaders, order, stats = scan(a.assets)
    recs = [shaders[d] for d in order]
    sizes = [r["size"] for r in recs]
    flag_lo = {}
    for r in recs:
        k = f"0x{r['flags'] & 0xFF:02X}"
        flag_lo[k] = flag_lo.get(k, 0) + 1
    names = {}
    for r in recs:
        names[r["sourceName"]] = names.get(r["sourceName"], 0) + 1
    stats.update({
        "unique_container_bytes": sum(sizes),
        "mean_container_bytes": (sum(sizes) / len(sizes)) if sizes else 0,
        "flags_low_byte": flag_lo,
        "distinct_sourceNames": len(names),
        "unique_shaders_sharing_a_sourceName": sum(c for c in names.values() if c > 1),
        "scan_seconds": round(time.time() - t0, 1),
    })
    if a.cmd == "scan":
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(stats, fh, indent=2)
        with open(os.path.splitext(a.out)[0] + ".tsv", "w", encoding="utf-8") as fh:
            fh.write("digest\tsize\tflags\tsourceName\tpath\toffset\n")
            for r in recs:
                fh.write(f"{r['digest']}\t{r['size']}\t0x{r['flags']:08X}\t{r['sourceName']}\t{r['path']}\t{r['offset']}\n")
        print(json.dumps(stats, indent=2))
        return 0
    if a.cmd == "sample":
        os.makedirs(a.out, exist_ok=False)
        by_size = sorted(recs, key=lambda r: (r["size"], r["digest"]))
        step = len(by_size) / a.count
        start = random.Random(a.seed).random() * step
        pick = [by_size[int(start + k * step)] for k in range(a.count)]
        for k, r in enumerate(pick):
            with open(os.path.join(a.out, f"sample{k:03d}.bin"), "wb") as fh:
                fh.write(read_container(a.assets, r))
        ps = [r["size"] for r in pick]
        print(json.dumps({"sample_count": len(pick), "sample_bytes": sum(ps), "sample_mean": sum(ps) / len(ps),
                          "corpus_unique": len(recs), "corpus_bytes": sum(sizes),
                          "corpus_mean": sum(sizes) / len(sizes)}, indent=2))
        return 0
    # shard: size-balanced greedy assignment, file names keep gradient_compiler's sourceName
    os.makedirs(a.out, exist_ok=False)
    loads = [0] * a.shards
    counts = [0] * a.shards
    for k in range(a.shards):
        os.makedirs(os.path.join(a.out, f"shard{k:02d}"))
    manifest = []
    for r in sorted(recs, key=lambda r: (-r["size"], r["digest"])):
        k = loads.index(min(loads))
        loads[k] += r["size"]
        counts[k] += 1
        name = r["sourceName"] + ".bin"
        dst = os.path.join(a.out, f"shard{k:02d}", name)
        n = 1
        while os.path.exists(dst):  # same sourceName twice: keep both (dump name collision handled at merge)
            dst = os.path.join(a.out, f"shard{k:02d}", f"{r['sourceName']}~{n}.bin")
            n += 1
        with open(dst, "wb") as fh:
            fh.write(read_container(a.assets, r))
        manifest.append((f"shard{k:02d}", os.path.basename(dst), r["sourceName"], r["size"], r["digest"],
                         r["path"], r["offset"]))
    with open(os.path.join(a.out, "manifest.tsv"), "w", encoding="utf-8") as fh:
        fh.write("shard\tfile\tsourceName\tsize\tdigest\tpath\toffset\n")
        for row in manifest:
            fh.write("\t".join(str(x) for x in row) + "\n")
    print(json.dumps({"shards": a.shards, "counts": counts, "bytes": loads}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

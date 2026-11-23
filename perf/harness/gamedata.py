#!/usr/bin/env python3
"""Game-data tools for the Dimensions Recompiled run harness. Holds no game data itself.

  xiso-list    ISO                       every file on an Xbox 360 disc image (XDVDFS, XGD1/2/3)
  xiso-extract ISO OUT [PATH...]         extract files (root-relative, case-insensitive; default: all)
                                         --exclude PATH (repeatable), --manifest FILE (name size sha1)
  stfs-info    PKG                       header fields and file table of a CON/LIVE/PIRS package
  stfs-extract PKG OUT [PATH...]         extract files; every data block is checked against its
                                         SHA-1 in the level-0 hash table, and every hash table is
                                         checked up the tree to the header's top hash
  xex-info     FILE...                   XEX2 execution info (title / media / version)
  sha256       FILE...
  verify       [--iso ISO] [--tu PKG] [--rehash]
                                         re-runs the installer's checks (rexlego-installer/InstallJob.cs
                                         KnownGame + Validation) on game/disc and game/tu23; with --iso /
                                         --tu also checks every extracted file's size against its
                                         directory entry; --rehash re-reads every file and compares it
                                         with game/manifest-*.tsv (the hashes taken while extracting)

The STFS reader is a port of rexlego-installer/StfsPackage.cs, which mirrors the SDK's
StfsContainerDevice (block -> offset mapping, hash-table walk, secondary tables).
"""
import argparse
import hashlib
import os
import struct
import sys
import time

CHUNK = 8 << 20


def be32(b, at):
    return struct.unpack_from(">I", b, at)[0]


def le24(b, at):
    return b[at] | (b[at + 1] << 8) | (b[at + 2] << 16)


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024.0


# ---------------------------------------------------------------- XDVDFS (disc image)

class XIso:
    SECTOR = 2048
    MAGIC = b"MICROSOFT*XBOX*MEDIA"
    BASES = (("XGD3", 0x2080000), ("XGD2", 0xFD90000), ("XGD1", 0x18300000), ("plain", 0))

    def __init__(self, path):
        self.f = open(path, "rb")
        self.size = os.path.getsize(path)
        for kind, base in self.BASES:
            if base + 33 * self.SECTOR > self.size:
                continue
            self.f.seek(base + 32 * self.SECTOR)
            hdr = self.f.read(self.SECTOR)
            if hdr[:20] == self.MAGIC:
                self.kind, self.base = kind, base
                self.root_sector, self.root_size = struct.unpack_from("<II", hdr, 20)
                return
        raise ValueError(f"{path}: no XDVDFS volume descriptor found")

    def _read_dir(self, sector, size):
        if size == 0:
            return []
        self.f.seek(self.base + sector * self.SECTOR)
        data = self.f.read(size)
        out, stack, seen = [], [0], set()
        while stack:
            off = stack.pop()
            if off in seen or off == 0xFFFF:
                continue
            seen.add(off)
            p = off * 4
            if p + 14 > len(data):
                continue
            left, right, sec, sz, attr, nlen = struct.unpack_from("<HHIIBB", data, p)
            if left == 0xFFFF and right == 0xFFFF and sec == 0xFFFFFFFF:
                continue  # padding / empty directory
            out.append((data[p + 14:p + 14 + nlen].decode("ascii"), sec, sz, attr))
            if left:
                stack.append(left)
            if right:
                stack.append(right)
        return out

    def walk(self, sector=None, size=None, prefix=""):
        """Yields (path, is_dir, sector, size); paths use '/'."""
        if sector is None:
            sector, size = self.root_sector, self.root_size
        for name, sec, sz, attr in sorted(self._read_dir(sector, size), key=lambda e: e[0].lower()):
            path = prefix + name
            if attr & 0x10:
                yield path, True, sec, sz
                yield from self.walk(sec, sz, path + "/")
            else:
                yield path, False, sec, sz

    def extract(self, sector, size, dest, digests=()):
        hs = [hashlib.new(d) for d in digests]
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        start = self.base + sector * self.SECTOR
        if start + size > self.size:
            raise IOError(f"{dest}: extent {start:#x}+{size:#x} runs past the end of the image")
        self.f.seek(start)
        left = size
        with open(dest, "wb") as out:
            while left:
                buf = self.f.read(min(CHUNK, left))
                if not buf:
                    raise IOError(f"{dest}: short read, {left} bytes missing")
                out.write(buf)
                for h in hs:
                    h.update(buf)
                left -= len(buf)
        got = os.path.getsize(dest)
        if got != size:
            raise IOError(f"{dest}: wrote {got} bytes, directory entry says {size}")
        return [h.hexdigest() for h in hs]


# ---------------------------------------------------------------- STFS (CON / LIVE / PIRS)

class Stfs:
    BLOCK = 0x1000
    EOC = 0xFFFFFF
    LEVEL = (170, 28900, 4913000)

    def __init__(self, path):
        self.f = open(path, "rb")
        self.size = os.path.getsize(path)
        h = self.f.read(0x971A)
        self.h = h
        self.magic = h[:4].decode("ascii", "replace")
        if self.magic not in ("CON ", "LIVE", "PIRS"):
            raise ValueError(f"{path}: not an STFS package (magic {self.magic!r})")
        self.header_size = be32(h, 0x340)
        self.content_type = be32(h, 0x344)
        self.metadata_version = be32(h, 0x348)
        self.content_size = struct.unpack_from(">Q", h, 0x34C)[0]
        self.media_id, self.version, self.base_version, self.title_id = struct.unpack_from(">IIII", h, 0x354)
        self.volume_type = be32(h, 0x3A9)
        if self.volume_type != 0:
            raise ValueError("SVOD packages are not supported")
        if h[0x379] != 0x24:
            raise ValueError("bad STFS volume descriptor")
        flags = h[0x37B]
        self.read_only = bool(flags & 1)
        self.root_active = bool(flags & 2)
        self.ft_block_count = struct.unpack_from("<H", h, 0x37C)[0]
        self.ft_block = le24(h, 0x37E)
        self.top_hash = h[0x381:0x395]
        self.total_blocks = be32(h, 0x395)
        self.free_blocks = be32(h, 0x399)
        self.bpht = 1 if self.read_only else 2
        self.step = (self.LEVEL[0] + self.bpht, self.LEVEL[1] + (self.LEVEL[0] + 1) * self.bpht)
        self.display_name = self._utf16be(0x411, 128)
        self.title_name = self._utf16be(0x1691, 64)
        self.data_start = (self.header_size + 0xFFF) & ~0xFFF
        self.tables = {}          # primary offset -> table bytes
        self.verified = set()     # primary offsets of tables verified up to the header
        self.entries = self._read_directory()

    def _utf16be(self, at, chars):
        raw = self.h[at:at + chars * 2]
        s = raw.decode("utf-16-be", "replace")
        return s.split("\x00", 1)[0]

    def header_hash_ok(self):
        """Content ID (0x32C) is the SHA-1 of the header from 0x344 up to the first block
        (header_size rounded up to 0x1000)."""
        self.f.seek(0x344)
        body = self.f.read(self.data_start - 0x344)
        return hashlib.sha1(body).digest() == self.h[0x32C:0x340]

    # block index -> file offset (StfsPackage.BlockToOffset)
    def block_offset(self, n):
        base, block = self.LEVEL[0], n
        for _ in range(3):
            block += ((n + base) // base) * self.bpht
            if n < base:
                break
            base *= self.LEVEL[0]
        return self.data_start + (block << 12)

    def _hash_block_number(self, n, level):
        L0, L1, _ = self.LEVEL
        if level == 0:
            if n < L0:
                return 0
            b = (n // L0) * self.step[0] + ((n // L1) + 1) * self.bpht
            return b if n < L1 else b + self.bpht
        if level == 1:
            if n < L1:
                return self.step[0]
            return (n // L1) * self.step[1] + self.bpht
        return self.step[1]

    def _hash_offset(self, n, level):
        return self.data_start + (self._hash_block_number(n, level) << 12)

    def _read_table(self, key, actual):
        self.f.seek(actual)
        t = self.f.read(self.BLOCK)
        if len(t) != self.BLOCK:
            raise IOError(f"short hash table read at {actual:#x}")
        self.tables[key] = t
        return t

    @staticmethod
    def _active(table, rec):
        return (table[rec * 0x18 + 0x14] & 0x40) != 0

    def _levels(self):
        if self.total_blocks > self.LEVEL[1]:
            return 3
        if self.total_blocks > self.LEVEL[0]:
            return 2
        return 1

    def l0_table(self, n):
        """Level-0 table covering data block n (same table choice as the SDK)."""
        L0, L1, _ = self.LEVEL
        lv0 = self._hash_offset(n, 0)
        if lv0 in self.tables:
            return self.tables[lv0]
        secondary = self.BLOCK if self.root_active else 0
        if self.read_only:
            secondary = 0
        elif self.total_blocks > L0:
            lv1 = self._hash_offset(n, 1)
            if lv1 not in self.tables:
                if self.total_blocks > L1:
                    lv2 = self._hash_offset(n, 2)
                    if lv2 not in self.tables:
                        self._read_table(lv2, lv2 + secondary)
                    rec2 = (n // L1) % L0
                    secondary = self.BLOCK if self._active(self.tables[lv2], rec2) else 0
                self._read_table(lv1, lv1 + secondary)
            rec1 = (n // L0) % L0
            secondary = self.BLOCK if self._active(self.tables[lv1], rec1) else 0
        return self._read_table(lv0, lv0 + secondary)

    def next_block(self, n):
        t = self.l0_table(n)
        return be32(t, (n % self.LEVEL[0]) * 0x18 + 0x14) & 0xFFFFFF

    def block_hash(self, n):
        t = self.l0_table(n)
        rec = n % self.LEVEL[0]
        return t[rec * 0x18:rec * 0x18 + 20]

    def verify_chain(self, n):
        """Checks the level-0 table for block n, and every table above it, up to the header's
        top hash. Read-only (single-table) packages only; returns None when not applicable."""
        if not self.read_only:
            return None
        L0, L1, _ = self.LEVEL
        levels = self._levels()
        offs = [self._hash_offset(n, lv) for lv in range(levels)]
        if offs[0] in self.verified:
            return True
        tabs = []
        for lv, off in enumerate(offs):
            if off not in self.tables:
                self._read_table(off, off)
            tabs.append(self.tables[off])
        recs = [(n // L0) % L0, (n // L1) % L0]
        for lv in range(levels - 1):
            want = tabs[lv + 1][recs[lv] * 0x18:recs[lv] * 0x18 + 20]
            if hashlib.sha1(tabs[lv]).digest() != want:
                raise IOError(f"hash table level {lv} for block {n} does not match level {lv + 1}")
        if hashlib.sha1(tabs[-1]).digest() != self.top_hash:
            raise IOError("top hash table does not match the header's top hash")
        self.verified.add(offs[0])
        return True

    def _read_directory(self):
        names, entries = [], []
        block = self.ft_block
        for _ in range(self.ft_block_count):
            self.f.seek(self.block_offset(block))
            data = self.f.read(self.BLOCK)
            for m in range(0x40):
                e = data[m * 0x40:(m + 1) * 0x40]
                if e[0] == 0:
                    break
                fl = e[0x28]
                name = e[:min(fl & 0x3F, 40)].decode("ascii", "replace")
                parent = struct.unpack_from(">H", e, 0x32)[0]
                path = name if parent == 0xFFFF else names[parent] + "/" + name
                names.append(path)
                entries.append(dict(path=path, is_dir=bool(fl & 0x80), contiguous=bool(fl & 0x40),
                                    valid_blocks=le24(e, 0x29), alloc_blocks=le24(e, 0x2C),
                                    start=le24(e, 0x2F), length=be32(e, 0x34)))
            nxt = self.next_block(block)
            if nxt == self.EOC:
                break
            block = nxt
        return entries

    def extract(self, entry, dest, verify=True, digests=("sha256",)):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        hs = [hashlib.new(d) for d in digests]
        block, left, nblocks = entry["start"], entry["length"], 0
        with open(dest, "wb") as out:
            while left > 0 and block != self.EOC:
                self.f.seek(self.block_offset(block))
                buf = self.f.read(self.BLOCK)
                if len(buf) != self.BLOCK:
                    raise IOError(f"{entry['path']}: short read at block {block}")
                if verify:
                    if hashlib.sha1(buf).digest() != self.block_hash(block):
                        raise IOError(f"{entry['path']}: block {block} fails its SHA-1 check")
                    self.verify_chain(block)
                part = buf[:min(self.BLOCK, left)]
                out.write(part)
                for h in hs:
                    h.update(part)
                left -= len(part)
                nblocks += 1
                block = self.next_block(block)
        if left > 0:
            raise IOError(f"{entry['path']}: block chain ended {left} bytes early")
        if os.path.getsize(dest) != entry["length"]:
            raise IOError(f"{entry['path']}: size mismatch after extract")
        return nblocks, [h.hexdigest() for h in hs]


# ---------------------------------------------------------------- XEX2

def xex_info(path):
    with open(path, "rb") as f:
        head = f.read(0x18)
        if len(head) < 0x18 or be32(head, 0) != 0x58455832:
            return None
        header_size, count = be32(head, 8), be32(head, 0x14)
        f.seek(0)
        hdr = f.read(header_size)
    for i in range(count):
        at = 0x18 + i * 8
        if at + 8 > len(hdr):
            break
        key, value = struct.unpack_from(">II", hdr, at)
        if key == 0x00040006:
            media, ver, base, title = struct.unpack_from(">IIII", hdr, value)
            return dict(media_id=media, version=ver, base_version=base, title_id=title)
    return None


def fmt_ver(v):
    return f"{v >> 28}.{(v >> 24) & 0xF}.{(v >> 8) & 0xFFFF}.{v & 0xFF}"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- commands

def _select(paths, wanted, excluded):
    wl = {w.replace("\\", "/").lower() for w in wanted}
    xl = {x.replace("\\", "/").lower() for x in excluded}
    for p in paths:
        lp = p.lower()
        if any(lp == x or lp.startswith(x + "/") for x in xl):
            continue
        if wl and lp not in wl:
            continue
        yield p


def cmd_xiso_list(a):
    iso = XIso(a.iso)
    print(f"{iso.kind}: partition {iso.base:#x}, descriptor {iso.base + 32 * iso.SECTOR:#x}, "
          f"root sector {iso.root_sector}, root size {iso.root_size}")
    total = files = 0
    for path, is_dir, sec, sz in iso.walk():
        print(f"  {'DIR ' if is_dir else 'FILE'} {sz:>14,}  sector {sec:>9}  {path}")
        if not is_dir:
            total += sz
            files += 1
    print(f"{files} files, {total:,} bytes ({human(total)})")


def cmd_xiso_extract(a):
    iso = XIso(a.iso)
    entries = {p: (sec, sz) for p, d, sec, sz in iso.walk() if not d}
    chosen = list(_select(entries, a.paths, a.exclude))
    missing = [w for w in a.paths if w.replace("\\", "/").lower() not in {c.lower() for c in chosen}]
    if missing:
        sys.exit(f"not on the disc: {missing}")
    total = sum(entries[p][1] for p in chosen)
    print(f"{iso.kind} image; extracting {len(chosen)} files, {human(total)} -> {a.out}", flush=True)
    t0, done, lines = time.time(), 0, []
    for p in chosen:
        sec, sz = entries[p]
        dest = os.path.join(a.out, *p.split("/"))
        if a.skip_existing and os.path.exists(dest) and os.path.getsize(dest) == sz:
            print(f"  skip {p} (exists, {sz:,} bytes)", flush=True)
            if a.manifest:
                lines.append(f"{p}\t{sz}\t-")
            continue
        t1 = time.time()
        digs = iso.extract(sec, sz, dest, ("sha1",) if a.manifest else ())
        done += sz
        dt = time.time() - t1
        print(f"  ok   {p}  {sz:,} bytes  {dt:.1f}s"
              + (f"  sha1 {digs[0]}" if digs else ""), flush=True)
        if a.manifest:
            lines.append(f"{p}\t{sz}\t{digs[0]}")
    if a.manifest:
        with open(a.manifest, "w", newline="\n") as m:
            m.write("# path\tsize\tsha1 (size checked against the XDVDFS directory entry)\n")
            m.write("\n".join(lines) + "\n")
    dt = time.time() - t0
    print(f"done: {human(done)} in {dt:.1f}s ({human(done / max(dt, 1e-6))}/s)")


def cmd_stfs_info(a):
    p = Stfs(a.pkg)
    print(f"magic={p.magic} content_type={p.content_type:08X} title={p.title_id:08X} media={p.media_id:08X} "
          f"version={fmt_ver(p.version)} base={fmt_ver(p.base_version)}")
    print(f"name='{p.display_name}' game='{p.title_name}' header_size={p.header_size:#x} "
          f"data_start={p.data_start:#x} read_only={p.read_only} root_active={p.root_active}")
    print(f"total_blocks={p.total_blocks} free_blocks={p.free_blocks} file_table=block {p.ft_block} x{p.ft_block_count} "
          f"levels={p._levels()} header_hash_ok={p.header_hash_ok()} file_size={p.size:,}")
    for e in p.entries:
        kind = "<dir>" if e["is_dir"] else ("contig" if e["contiguous"] else "chain ")
        print(f"  {kind} {e['length']:>14,}  start {e['start']:>7}  blocks {e['valid_blocks']:>7}  {e['path']}")


def cmd_stfs_extract(a):
    p = Stfs(a.pkg)
    if not p.header_hash_ok():
        print("WARNING: header SHA-1 (content ID) does not match", flush=True)
    files = {e["path"]: e for e in p.entries if not e["is_dir"]}
    chosen = list(_select(files, a.paths, a.exclude))
    missing = [w for w in a.paths if w.replace("\\", "/").lower() not in {c.lower() for c in chosen}]
    if missing:
        sys.exit(f"not in the package: {missing}")
    total = sum(files[c]["length"] for c in chosen)
    print(f"{p.magic} {p.content_type:08X} title {p.title_id:08X}; extracting {len(chosen)} files, "
          f"{human(total)} -> {a.out} (block SHA-1 verify: {not a.no_verify})", flush=True)
    t0, lines = time.time(), []
    for c in chosen:
        e = files[c]
        dest = os.path.join(a.out, *c.split("/"))
        t1 = time.time()
        nblocks, digs = p.extract(e, dest, verify=not a.no_verify)
        print(f"  ok   {c}  {e['length']:,} bytes  {nblocks} blocks  {time.time() - t1:.1f}s  sha256 {digs[0]}",
              flush=True)
        lines.append(f"{c}\t{e['length']}\t{digs[0]}")
    if a.manifest:
        with open(a.manifest, "w", newline="\n") as m:
            m.write("# path\tsize\tsha256 (every block SHA-1 checked against the STFS hash tree)\n")
            m.write("\n".join(lines) + "\n")
    dt = time.time() - t0
    print(f"done: {human(total)} in {dt:.1f}s; hash tables verified to the header: {len(p.verified)}")


def cmd_xex_info(a):
    for path in a.files:
        i = xex_info(path)
        if not i:
            print(f"{path}: not a XEX2 (or no execution info)")
            continue
        print(f"{path}: title={i['title_id']:08X} media={i['media_id']:08X} version={fmt_ver(i['version'])} "
              f"base={fmt_ver(i['base_version'])} size={os.path.getsize(path):,}")


def cmd_sha256(a):
    for path in a.files:
        print(f"{sha256_file(path)}  {os.path.getsize(path):>14,}  {path}")


# ---------------------------------------------------------------- verify

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # games/lego-dimensions-recomp

# Copied from rexlego-installer/InstallJob.cs (KnownGame). Keep in sync if the installer changes.
KNOWN = dict(
    title_id=0x5752084B,
    media_id=0x72B1DD2A,
    xexp_sha256="a5169f508036d024312537d3ce64c07bf0680a87d9e0a282ff80461cf4a646a9",
    xexp_size=11114496,
    xexp24_sha256="272f465c020017917168d6fc4a0cf5b7a6e71c591ff77d7af207561913719a34",
    tu23_package_size=2069790720,
    update_required=("Default.xexp", "PATCH.DAT", "PATCH.HDR"),
    game_required=("Default.xex", "GAME.DAT", "GAME.HDR"),
    disc_archives=(
        ("GAME0.DAT", 2138287423), ("GAME0.HDR", 1294147),
        ("GAME1.DAT", 278177176), ("GAME1.HDR", 1880732),
        ("GAME2.DAT", 1311977060), ("GAME2.HDR", 1543784),
        ("GAME3.DAT", 2137634708), ("GAME3.HDR", 707992),
        ("GAME4.DAT", 1074093029), ("GAME4.HDR", 411881),
        ("INSTALL0_.DAT", 47503585), ("INSTALL0_.HDR", 1980144),
        ("INSTALL0_0.DAT", 64558277), ("INSTALL0_0.HDR", 2009913),
        ("INSTALL0_1.DAT", 46544891), ("INSTALL0_1.HDR", 807873),
    ),
)


class Checks:
    def __init__(self):
        self.passed = self.failed = 0

    def __call__(self, ok, what, detail=""):
        print(f"  {'PASS' if ok else 'FAIL'}  {what}" + (f"  [{detail}]" if detail else ""), flush=True)
        if ok:
            self.passed += 1
        else:
            self.failed += 1
        return ok


def _tree(root):
    """Relative '/' paths of every file under root."""
    out = {}
    for d, _, files in os.walk(root):
        for f in files:
            full = os.path.join(d, f)
            out[os.path.relpath(full, root).replace(os.sep, "/")] = full
    return out


def _read_manifest(path):
    rows = {}
    with open(path, encoding="utf-8") as m:
        for line in m:
            if line.startswith("#") or not line.strip():
                continue
            rel, size, dig = line.rstrip("\n").split("\t")
            rows[rel] = (int(size), dig)
    return rows


def _hash_file(path, algo):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _compare_sizes(check, label, root, expected):
    """expected: rel path -> size. Case-insensitive lookup, exact-size compare."""
    have = {k.lower(): v for k, v in _tree(root).items()}
    bad = []
    for rel, size in expected.items():
        full = have.get(rel.lower())
        got = os.path.getsize(full) if full else None
        if got != size:
            bad.append(f"{rel}: {'missing' if got is None else f'{got:,}'} vs {size:,}")
    check(not bad, f"all {len(expected)} {label} files present, each size equal to its directory entry",
          "; ".join(bad[:6]))
    return {k for k in have if k not in {r.lower() for r in expected}}


def cmd_verify(a):
    check, g, u = Checks(), a.game, a.update
    print(f"game dir   {g}\nupdate dir {u}")
    print("installer identity checks (rexlego-installer/InstallJob.cs, Validation.CheckGameDir/CheckUpdate):")
    for f in KNOWN["game_required"]:
        check(os.path.isfile(os.path.join(g, f)), f"game: {f} present")
    xi = xex_info(os.path.join(g, "Default.xex")) if os.path.isfile(os.path.join(g, "Default.xex")) else None
    check(bool(xi) and xi["title_id"] == KNOWN["title_id"], "Default.xex title ID = 5752084B",
          f"{xi['title_id']:08X}" if xi else "unreadable")
    check(bool(xi) and xi["media_id"] == KNOWN["media_id"], "Default.xex media ID = 72B1DD2A",
          f"{xi['media_id']:08X}, version {fmt_ver(xi['version'])}" if xi else "unreadable")
    bad = []
    for name, size in KNOWN["disc_archives"]:
        p = os.path.join(g, name)
        got = os.path.getsize(p) if os.path.isfile(p) else None
        if got != size:
            bad.append(f"{name}: {'missing' if got is None else f'{got:,}'} vs {size:,}")
    check(not bad, f"all {len(KNOWN['disc_archives'])} KnownGame.DiscArchives sizes match", "; ".join(bad))
    for f in KNOWN["update_required"]:
        check(os.path.isfile(os.path.join(u, f)), f"update: {f} present")
    for where, label in ((u, "update"), (g, "game")):
        p = os.path.join(where, "Default.xexp")
        if not os.path.isfile(p):
            check(False, f"{label}: Default.xexp present")
            continue
        sha, size = sha256_file(p), os.path.getsize(p)
        hint = " (this is TU24's)" if sha == KNOWN["xexp24_sha256"] else ""
        check(sha == KNOWN["xexp_sha256"] and size == KNOWN["xexp_size"],
              f"{label}: Default.xexp is TU23's (KnownGame.UpdateXexpSha256/Size)", f"sha256 {sha[:16]}..., {size:,} B{hint}")
    names = os.listdir(g)
    check("Default.xexp" in names and "Default.xex" in names,
          "game: exact-case names Default.xex + Default.xexp (README-dev step 3)",
          ", ".join(n for n in names if n.lower().startswith("default.")))

    if a.iso:
        print(f"disc image cross-check ({a.iso}):")
        iso = XIso(a.iso)
        excl = [x.replace("\\", "/").lower() for x in a.exclude]
        expected = {p: sz for p, d, sec, sz in iso.walk() if not d
                    and not any(p.lower() == x or p.lower().startswith(x + "/") for x in excl)}
        check(iso.kind == "XGD3", f"image is XGD3 (descriptor at {iso.base + 32 * iso.SECTOR:#x})", iso.kind)
        extra = _compare_sizes(check, "disc", g, expected) - {"default.xexp"}
        check(not extra, "game dir holds nothing else except the copied Default.xexp", ", ".join(sorted(extra)))
    if a.tu:
        print(f"title update cross-check ({a.tu}):")
        p = Stfs(a.tu)
        check(p.size == KNOWN["tu23_package_size"], "package size = KnownGame.Tu23PackageSize", f"{p.size:,}")
        check(p.magic == "LIVE" and p.content_type == 0x000B0000, "LIVE package, content type 000B0000 (title update)",
              f"{p.magic} {p.content_type:08X}")
        check(p.title_id == KNOWN["title_id"] and p.media_id == KNOWN["media_id"],
              "package execution info: title 5752084B, media 72B1DD2A", f"{p.title_id:08X} / {p.media_id:08X}")
        check(p.header_hash_ok(), "header SHA-1 equals the content ID")
        files = {e["path"]: e["length"] for e in p.entries if not e["is_dir"]}
        extra = _compare_sizes(check, "TU", u, files)
        check(not extra, "update dir holds nothing else", ", ".join(sorted(extra)))
    if a.rehash:
        print("re-hash against the extraction manifests:")
        for root, man, algo in ((g, a.disc_manifest, "sha1"), (u, a.tu_manifest, "sha256")):
            rows, bad, total, t0 = _read_manifest(man), [], 0, time.time()
            for rel, (size, dig) in rows.items():
                full = os.path.join(root, *rel.split("/"))
                if not os.path.isfile(full) or os.path.getsize(full) != size:
                    bad.append(f"{rel}: size")
                    continue
                if dig != "-" and _hash_file(full, algo) != dig:
                    bad.append(f"{rel}: {algo}")
                total += size
            check(not bad, f"{len(rows)} files re-read, {algo} equal to {os.path.basename(man)}",
                  f"{human(total)} in {time.time() - t0:.0f}s" if not bad else "; ".join(bad))
    print(f"RESULT: {check.passed} passed, {check.failed} failed")
    sys.exit(1 if check.failed else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("xiso-list"); s.add_argument("iso"); s.set_defaults(fn=cmd_xiso_list)
    s = sub.add_parser("xiso-extract"); s.add_argument("iso"); s.add_argument("out"); s.add_argument("paths", nargs="*")
    s.add_argument("--exclude", action="append", default=[]); s.add_argument("--manifest")
    s.add_argument("--skip-existing", action="store_true"); s.set_defaults(fn=cmd_xiso_extract)
    s = sub.add_parser("stfs-info"); s.add_argument("pkg"); s.set_defaults(fn=cmd_stfs_info)
    s = sub.add_parser("stfs-extract"); s.add_argument("pkg"); s.add_argument("out"); s.add_argument("paths", nargs="*")
    s.add_argument("--exclude", action="append", default=[]); s.add_argument("--manifest")
    s.add_argument("--no-verify", action="store_true"); s.set_defaults(fn=cmd_stfs_extract)
    s = sub.add_parser("xex-info"); s.add_argument("files", nargs="+"); s.set_defaults(fn=cmd_xex_info)
    s = sub.add_parser("sha256"); s.add_argument("files", nargs="+"); s.set_defaults(fn=cmd_sha256)
    s = sub.add_parser("verify")
    s.add_argument("--game", default=os.path.join(ROOT, "game", "disc"))
    s.add_argument("--update", default=os.path.join(ROOT, "game", "tu23"))
    s.add_argument("--iso"); s.add_argument("--tu")
    s.add_argument("--exclude", action="append", default=["$SystemUpdate"])
    s.add_argument("--rehash", action="store_true")
    s.add_argument("--disc-manifest", default=os.path.join(ROOT, "game", "manifest-disc.tsv"))
    s.add_argument("--tu-manifest", default=os.path.join(ROOT, "game", "manifest-tu23.tsv"))
    s.set_defaults(fn=cmd_verify)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""ldtag.py - LEGO Dimensions NTAG213 tag dumps (180 bytes) for the emulated Toy Pad.

Exact Python port of the tag crypto in
  DimensionsRecomp/rexglue-sdk/src/input/portal/emulated_toypad.cpp
  (ReadLE32/ReadBE32/WriteLE32/WriteBE32 L96-113, Decrypt L550, Encrypt L575,
   GenerateFigureKey L600, Scramble L611, Randomize L620, GetFigureId L632),
which is itself a port of RPCS3's dimensions_toypad. selftest_toypad.py --cpp
cross-checks this file against the C++ compiled straight from those source lines.

Agent 3, run-2 task 2 (decision 1 = YES, user 17:27): generated virtual Batman /
Gandalf / Wyldstyle tags, placed through the game's TCP listener (127.0.0.1:9191).
Harness-only and user-mode. The tags live in build/agent3/toypad/tags/ and are sent
with path length 0, so the game keeps them in memory and never writes a tag file
(ToypadFigure::Save writes only when the figure has a file path).

  python ldtag.py make --starter [--out-dir build/agent3/toypad/tags]
  python ldtag.py make --name batman --out x.bin        (or --name custom --id 17)
  python ldtag.py id   tags/batman.bin ...
  python ldtag.py dump tags/batman.bin
"""
import argparse
import hashlib
import json
import os
import struct
import sys

TAG_SIZE = 0x2D * 4  # kToypadTagSize = 180 bytes (45 NTAG213 pages of 4 bytes)
COMMAND_KEY = bytes([0x55, 0xFE, 0xF6, 0xB0, 0x62, 0xBF, 0x0B, 0x41,
                     0xC9, 0xB3, 0x7C, 0xB4, 0x97, 0x3E, 0x29, 0x7B])
CHAR_CONSTANT = bytes([0xB7, 0xD5, 0xD7, 0xE6, 0xE7, 0xBA, 0x3C, 0xA8, 0xD8,
                       0x75, 0x47, 0x68, 0xCF, 0x23, 0xE9, 0xFE, 0xAA])
M32 = 0xFFFFFFFF
DELTA = 0x9E3779B9

# Starter Pack characters: LEGO Dimensions figure ids 1-3 (RPCS3 / Dolphin figure lists).
CHARACTERS = {"batman": 1, "gandalf": 2, "wyldstyle": 3}
# Starter placement: pad 1 = centre, 2 = left, 3 = right; index = figure slot 0..6.
STARTER = (("batman", 2, 0), ("gandalf", 1, 1), ("wyldstyle", 3, 2))
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TAGS_DIR = os.path.join(HERE, "tags")


def rotr(v, n):
    return ((v >> n) | (v << (32 - n))) & M32


def le32(b, off=0):
    return struct.unpack_from("<I", b, off)[0]


def be32(b, off=0):
    return struct.unpack_from(">I", b, off)[0]


def randomize(key, count):
    """EmulatedToypad::Randomize -> 4 little-endian bytes."""
    s = 0
    for i in range(count):
        v4 = rotr(s, 25)
        v5 = rotr(s, 10)
        b = le32(key, i * 4)
        s = (b + v4 + v5 - s) & M32
    return struct.pack("<I", s)


def scramble(uid7, count):
    """EmulatedToypad::Scramble: uid + kCharConstant, byte count*4-1 = 0xAA, BE32 of Randomize."""
    buf = bytearray(uid7) + bytearray(CHAR_CONSTANT)
    buf[count * 4 - 1] = 0xAA
    return be32(randomize(bytes(buf), count))


def tag_uid(tag):
    """NTAG213 UID = bytes 0, 1, 2, 4, 5, 6, 7 (bytes 3 and 8 are the BCCs)."""
    return bytes((tag[0], tag[1], tag[2], tag[4], tag[5], tag[6], tag[7]))


def figure_key(tag):
    """EmulatedToypad::GenerateFigureKey: BE32 of Scramble(uid, 3..6)."""
    uid = tag_uid(tag)
    return b"".join(struct.pack(">I", scramble(uid, c)) for c in (3, 4, 5, 6))


def _key_words(key16):
    k = COMMAND_KEY if key16 is None else key16
    return [le32(k, o) for o in (0, 4, 8, 12)]


def tea_encrypt(block8, key16=None):
    """EmulatedToypad::Encrypt (TEA, LE words, 32 rounds; key None = kCommandKey)."""
    d1, d2 = le32(block8, 0), le32(block8, 4)
    k1, k2, k3, k4 = _key_words(key16)
    s = 0
    for _ in range(32):
        s = (s + DELTA) & M32
        d1 = (d1 + ((((d2 << 4) + k1) ^ (d2 + s) ^ ((d2 >> 5) + k2)) & M32)) & M32
        d2 = (d2 + ((((d1 << 4) + k3) ^ (d1 + s) ^ ((d1 >> 5) + k4)) & M32)) & M32
    return struct.pack("<II", d1, d2)


def tea_decrypt(block8, key16=None):
    """EmulatedToypad::Decrypt (sum starts at 0xC6EF3720)."""
    d1, d2 = le32(block8, 0), le32(block8, 4)
    k1, k2, k3, k4 = _key_words(key16)
    s = 0xC6EF3720
    for _ in range(32):
        d2 = (d2 - ((((d1 << 4) + k3) ^ (d1 + s) ^ ((d1 >> 5) + k4)) & M32)) & M32
        d1 = (d1 - ((((d2 << 4) + k1) ^ (d2 + s) ^ ((d2 >> 5) + k2)) & M32)) & M32
        s = (s - DELTA) & M32
    return struct.pack("<II", d1, d2)


def figure_id(tag):
    """EmulatedToypad::GetFigureId: decrypted page 36 if < 1000 (character), else plain LE32 page 36."""
    dec = tea_decrypt(bytes(tag[144:152]), figure_key(tag))
    n = le32(dec)
    if n < 1000:
        return n
    return le32(tag, 144)


def make_uid(name):
    """Deterministic 7-byte UID: 0x04 (NXP) + 6 bytes of sha256('agent3-ldtag:' + name)."""
    h = hashlib.sha256(("agent3-ldtag:" + name.lower()).encode("utf-8")).digest()
    return bytes([0x04]) + h[:6]


def make_tag(fig_id, uid7):
    if len(uid7) != 7:
        raise ValueError("uid must be 7 bytes")
    if not 0 < fig_id <= M32:
        raise ValueError("bad figure id")
    t = bytearray(TAG_SIZE)
    t[0:3] = uid7[0:3]
    t[3] = 0x88 ^ uid7[0] ^ uid7[1] ^ uid7[2]          # BCC0 (cascade tag 0x88)
    t[4:8] = uid7[3:7]
    t[8] = uid7[3] ^ uid7[4] ^ uid7[5] ^ uid7[6]       # BCC1
    t[9] = 0x48                                        # NTAG internal byte
    t[12:16] = b"\xE1\x10\x12\x00"                     # page 3: NTAG213 capability container
    t[16:19] = b"\x01\x00\x0F"                         # page 4, as RPCS3 create_blank_character
    if fig_id < 1000:
        # Characters: LE32(id) twice, TEA-encrypted with the figure key, in pages 36-37.
        t[144:152] = tea_encrypt(struct.pack("<II", fig_id, fig_id), figure_key(t))
    else:
        # Vehicles / gadgets: plain LE32 id in page 36 (GetFigureId's second branch).
        struct.pack_into("<I", t, 144, fig_id)
    return bytes(t)


def tag_info(tag):
    return {
        "uid": tag_uid(tag).hex().upper(),
        "bcc0_ok": tag[3] == (0x88 ^ tag[0] ^ tag[1] ^ tag[2]),
        "bcc1_ok": tag[8] == (tag[4] ^ tag[5] ^ tag[6] ^ tag[7]),
        "key": figure_key(tag).hex().upper(),
        "page36_37": bytes(tag[144:152]).hex().upper(),
        "id": figure_id(tag),
        "sha256": hashlib.sha256(bytes(tag)).hexdigest(),
    }


def read_tag(path):
    with open(path, "rb") as f:
        data = f.read()
    if len(data) != TAG_SIZE:
        raise ValueError("%s: %d bytes, expected %d" % (path, len(data), TAG_SIZE))
    return data


def write_starter(out_dir=DEFAULT_TAGS_DIR):
    os.makedirs(out_dir, exist_ok=True)
    manifest = []
    for name, pad, index in STARTER:
        tag = make_tag(CHARACTERS[name], make_uid(name))
        path = os.path.join(out_dir, name + ".bin")
        with open(path, "wb") as f:
            f.write(tag)
        info = tag_info(tag)
        info.update({"name": name, "file": name + ".bin", "pad": pad, "index": index})
        manifest.append(info)
    with open(os.path.join(out_dir, "tags.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--starter", action="store_true", help="write batman/gandalf/wyldstyle .bin + tags.json")
    m.add_argument("--out-dir", default=DEFAULT_TAGS_DIR)
    m.add_argument("--name")
    m.add_argument("--id", type=int)
    m.add_argument("--out")
    i = sub.add_parser("id")
    i.add_argument("files", nargs="+")
    d = sub.add_parser("dump")
    d.add_argument("file")
    a = ap.parse_args(argv)

    if a.cmd == "make":
        if a.starter:
            for e in write_starter(a.out_dir):
                print("%-10s id=%d pad=%d index=%d uid=%s sha256=%s" % (e["name"], e["id"], e["pad"], e["index"], e["uid"], e["sha256"][:16]))
            return 0
        if not a.name:
            ap.error("make needs --starter or --name")
        fid = a.id if a.id is not None else CHARACTERS.get(a.name.lower())
        if fid is None:
            ap.error("unknown name %r: give --id" % a.name)
        tag = make_tag(fid, make_uid(a.name))
        out = a.out or os.path.join(a.out_dir, a.name.lower() + ".bin")
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "wb") as f:
            f.write(tag)
        print(json.dumps(dict(tag_info(tag), file=out)))
        return 0
    if a.cmd == "id":
        for p in a.files:
            print("%s id=%d" % (p, figure_id(read_tag(p))))
        return 0
    if a.cmd == "dump":
        tag = read_tag(a.file)
        for k, v in tag_info(tag).items():
            print("%-10s %s" % (k, v))
        for page in range(TAG_SIZE // 4):
            print("page %2d: %s" % (page, tag[page * 4:page * 4 + 4].hex(" ").upper()))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())

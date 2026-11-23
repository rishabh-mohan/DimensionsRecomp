#!/usr/bin/env python3
"""selftest_toypad.py - self-test of the Toy Pad tag tool WITHOUT the game (Agent 3, run-2 task 2).

 1. ldtag: Batman/Gandalf/Wyldstyle decode to ids 1/2/3, BCC bytes, 180 bytes, determinism,
    pages 36-37 = TEA(LE32 id, LE32 id), distinct UIDs, TEA inverse x300, vehicle branch.
 2. toypad_client against fake_listener (random port): starter loads (pad/index/id/path len 0),
    GET_LED 40 bytes and the connection stays open, reject (pad 0) = hang-up with no reply,
    REMOVE, MOVE.
 3. --cpp: cross-check against the C++ itself. The crypto lines are cut from
    DimensionsRecomp/rexglue-sdk/src/input/portal/emulated_toypad.cpp at run time (kCommandKey ..
    WriteBE32, Decrypt .. GetFigureId, "EmulatedToypad::" stripped), compiled with the repo's
    clang-cl (/MT, lld-link /threads:1) into build/agent3/toypad/selftest/, and run on the tags:
    the figure keys, ids, encrypted pages and a command-key vector must equal the Python ones.
Report: build/agent3/toypad/selftest/selftest-<HHMMSS>.txt. Exit 0 = PASS.
"""
import argparse
import datetime
import os
import random
import struct
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ldtag  # noqa: E402
import toypad_client as tc  # noqa: E402
from fake_listener import FakeListener  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC = os.path.join(REPO, "DimensionsRecomp", "rexglue-sdk", "src", "input", "portal", "emulated_toypad.cpp")
CLANG = os.path.join(REPO, "toolchain", "llvm-23.1.6", "bin", "clang-cl.exe")
OUTDIR = os.path.join(HERE, "selftest")
RESULTS = []
LINES = []


def say(msg):
    LINES.append(msg)
    print(msg, flush=True)


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    say("%s %s%s" % ("PASS" if ok else "FAIL", name, (" - " + detail) if detail else ""))


def test_crypto(tags_dir):
    man = ldtag.write_starter(tags_dir)
    for e in man:
        tag = ldtag.read_tag(os.path.join(tags_dir, e["file"]))
        fid = ldtag.figure_id(tag)
        check("id %s" % e["name"], fid == ldtag.CHARACTERS[e["name"]], "id=%d uid=%s" % (fid, e["uid"]))
        check("bcc %s" % e["name"], e["bcc0_ok"] and e["bcc1_ok"])
        check("size %s" % e["name"], len(tag) == ldtag.TAG_SIZE)
        check("deterministic %s" % e["name"], ldtag.make_tag(ldtag.CHARACTERS[e["name"]], ldtag.make_uid(e["name"])) == tag)
        dec = ldtag.tea_decrypt(tag[144:152], ldtag.figure_key(tag))
        check("pages 36-37 %s" % e["name"], struct.unpack("<II", dec) == (fid, fid), dec.hex().upper())
    check("distinct uids", len({e["uid"] for e in man}) == 3)
    rnd = random.Random(1234)
    ok = True
    for _ in range(300):
        blk = bytes(rnd.getrandbits(8) for _ in range(8))
        key = bytes(rnd.getrandbits(8) for _ in range(16)) if rnd.random() < 0.8 else None
        if ldtag.tea_decrypt(ldtag.tea_encrypt(blk, key), key) != blk:
            ok = False
            break
    check("tea inverse x300", ok)
    veh = ldtag.make_tag(1000, ldtag.make_uid("batmobile"))
    check("vehicle branch id 1000", ldtag.figure_id(veh) == 1000)
    return veh


def recv_n(s, n):
    b = b""
    while len(b) < n:
        d = s.recv(n - len(b))
        if not d:
            break
        b += d
    return b


def test_client(tags_dir):
    fl = FakeListener(0)
    try:
        port = fl.port
        say("fake listener on 127.0.0.1:%d" % port)
        res = tc.place_starter(port, tags_dir, gap_s=0.1, wait_s=2.0, log=lambda m: say("  " + m))
        check("starter: 3 loads, server hung up", len(res) == 3 and all(r[3] for r in res))
        time.sleep(0.3)
        got = [(e[1], e[2], e[3], e[4]) for e in fl.events if e[0] == "load"]
        exp = [(pad, index, ldtag.CHARACTERS[n], 0) for n, pad, index in ldtag.STARTER]
        check("listener saw pad/index/id/path_len", got == exp, str(got))
        fl.set_led(1, 1, 0xFF, 0xFF, 0xFF)
        buf = tc.get_leds(port)
        p = tc.parse_leds(buf)
        check("GET_LED 40 bytes", len(buf) == 40 and p is not None and p["regions"][0]["rgb"] == "FFFFFF", tc.leds_text(p))
        with tc.connect(port) as s:
            s.sendall(tc.header(0x04, 1, 0))
            a = recv_n(s, 40)
            s.sendall(tc.header(0x04, 1, 0))
            b = recv_n(s, 40)
        check("GET_LED keeps the connection open", len(a) == 40 and len(b) == 40)
        with tc.connect(port) as s:
            s.sendall(tc.header(0x01, 0, 0) + bytes(ldtag.TAG_SIZE) + b"\x00\x00")
            ok, extra = tc.wait_hangup(s, 3.0)
        time.sleep(0.2)
        check("reject pad 0: hang-up, no reply", ok and extra == b"" and any(e[0] == "rejected" for e in fl.events))
        check("REMOVE 2/0", tc.remove(port, 2, 0))
        check("MOVE 1/1 -> 2/0", tc.move(port, 1, 1, 2, 0))
        time.sleep(0.3)
        check("slots after REMOVE/MOVE", fl.slots == {0: (2, 2), 2: (3, 3)}, str(fl.slots))
    finally:
        fl.close()


def extract_cpp():
    with open(SRC, encoding="utf-8") as f:
        lines = f.read().splitlines()

    def find(pred, start=0):
        for i in range(start, len(lines)):
            if pred(lines[i]):
                return i
        raise ValueError("pattern not found in %s" % SRC)

    a0 = find(lambda l: l.startswith("constexpr std::array<uint8_t, 16> kCommandKey"))
    a1 = find(lambda l: l == "}", find(lambda l: l.startswith("void WriteBE32("), a0))
    b0 = find(lambda l: l.startswith("std::array<uint8_t, 8> EmulatedToypad::Decrypt("))
    b1 = find(lambda l: l == "}", find(lambda l: l.startswith("uint32_t EmulatedToypad::GetFigureId("), b0))
    p1 = lines[a0:a1 + 1]
    p2 = [l.replace("EmulatedToypad::", "") for l in lines[b0:b1 + 1]]
    return (a0 + 1, a1 + 1, p1), (b0 + 1, b1 + 1, p2)


CPP_HEAD = """// xcheck.cpp - GENERATED by build/agent3/toypad/selftest_toypad.py from emulated_toypad.cpp. Do not edit.
#include <array>
#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <optional>
#include <string>
#include <vector>

namespace xcheck {
constexpr size_t kToypadTagSize = 0x2D * 0x04;
std::array<uint8_t, 8> Decrypt(const uint8_t* buf, std::optional<std::array<uint8_t, 16>> key);
std::array<uint8_t, 8> Encrypt(const uint8_t* buf, std::optional<std::array<uint8_t, 16>> key);
std::array<uint8_t, 16> GenerateFigureKey(const std::array<uint8_t, kToypadTagSize>& buf);
uint32_t Scramble(const std::array<uint8_t, 7>& uid, uint8_t count);
std::array<uint8_t, 4> Randomize(const std::vector<uint8_t>& key, uint8_t count);
uint32_t GetFigureId(const std::array<uint8_t, kToypadTagSize>& buf);
"""

CPP_MAIN = """}  // namespace xcheck
using namespace xcheck;

static void hex(const uint8_t* p, size_t n) {
  for (size_t i = 0; i < n; ++i) std::printf("%02X", p[i]);
}

int main(int argc, char** argv) {
  for (int a = 1; a < argc; ++a) {
    std::FILE* f = std::fopen(argv[a], "rb");
    if (!f) { std::printf("ERR open %s\\n", argv[a]); return 2; }
    std::array<uint8_t, kToypadTagSize> t{};
    const size_t n = std::fread(t.data(), 1, t.size(), f);
    std::fclose(f);
    if (n != t.size()) { std::printf("ERR size %s\\n", argv[a]); return 2; }
    const auto key = GenerateFigureKey(t);
    const uint32_t id = GetFigureId(t);
    uint8_t blk[8];
    WriteLE32(blk, id);
    WriteLE32(blk + 4, id);
    const auto enc = Encrypt(blk, key);
    std::printf("TAG %s id=%u key=", argv[a], id);
    hex(key.data(), 16);
    std::printf(" enc=");
    hex(enc.data(), 8);
    std::printf("\\n");
  }
  const uint8_t v[8] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF};
  const auto ce = Encrypt(v, std::nullopt);
  const auto cd = Decrypt(ce.data(), std::nullopt);
  std::printf("CMD enc=");
  hex(ce.data(), 8);
  std::printf(" dec=");
  hex(cd.data(), 8);
  std::printf("\\n");
  return 0;
}
"""


def test_cpp(tags_dir, veh):
    os.makedirs(OUTDIR, exist_ok=True)
    (l1a, l1b, p1), (l2a, l2b, p2) = extract_cpp()
    cpp = os.path.join(OUTDIR, "xcheck.cpp")
    exe = os.path.join(OUTDIR, "xcheck.exe")
    obj = os.path.join(OUTDIR, "xcheck.obj")
    with open(cpp, "w", encoding="utf-8", newline="\n") as f:
        f.write(CPP_HEAD)
        f.write("// ---- emulated_toypad.cpp L%d-%d (verbatim) ----\n" % (l1a, l1b))
        f.write("\n".join(p1) + "\n")
        f.write("// ---- emulated_toypad.cpp L%d-%d (EmulatedToypad:: stripped) ----\n" % (l2a, l2b))
        f.write("\n".join(p2) + "\n")
        f.write(CPP_MAIN)
    say("C++ source lines: L%d-%d and L%d-%d of %s" % (l1a, l1b, l2a, l2b, os.path.relpath(SRC, REPO)))
    for p in (exe, obj):
        if os.path.exists(p):
            os.remove(p)
    cmd = [CLANG, "/nologo", "/std:c++20", "/O2", "/EHsc", "/MT", cpp, "/Fe" + exe, "/Fo" + obj,
           "-fuse-ld=lld", "/link", "/threads:1"]
    r = subprocess.run(cmd, cwd=OUTDIR, capture_output=True, text=True, timeout=300)
    if r.stdout.strip() or r.stderr.strip():
        say("clang-cl output:\n" + (r.stdout + r.stderr).strip()[:3000])
    check("C++ cross-check compiles (clang-cl, lld-link /threads:1)", r.returncode == 0 and os.path.exists(exe), "exit %d" % r.returncode)
    if r.returncode != 0:
        return
    vpath = os.path.join(OUTDIR, "batmobile-1000.bin")
    with open(vpath, "wb") as f:
        f.write(veh)
    files = [os.path.join(tags_dir, n + ".bin") for n, _, _ in ldtag.STARTER] + [vpath]
    r = subprocess.run([exe] + files, cwd=OUTDIR, capture_output=True, text=True, timeout=60)
    say("xcheck.exe:\n" + r.stdout.strip())
    check("xcheck.exe runs", r.returncode == 0, "exit %d" % r.returncode)
    out = {}
    cmdline = None
    for line in r.stdout.splitlines():
        if line.startswith("TAG "):
            path, rest = line[4:].split(" id=", 1)
            kv = dict(x.split("=", 1) for x in ("id=" + rest).split())
            out[os.path.normcase(os.path.abspath(path))] = kv
        elif line.startswith("CMD "):
            cmdline = dict(x.split("=", 1) for x in line[4:].split())
    for p in files:
        tag = ldtag.read_tag(p)
        kv = out.get(os.path.normcase(os.path.abspath(p)), {})
        fid = ldtag.figure_id(tag)
        key = ldtag.figure_key(tag)
        enc = ldtag.tea_encrypt(struct.pack("<II", fid, fid), key)
        name = os.path.basename(p)
        check("C++ == Python id %s" % name, kv.get("id") == str(fid), "c++ %s py %d" % (kv.get("id"), fid))
        check("C++ == Python figure key %s" % name, kv.get("key") == key.hex().upper())
        check("C++ == Python Encrypt(id,id) %s" % name, kv.get("enc") == enc.hex().upper())
        if fid < 1000:
            check("C++ Encrypt(id,id) == tag pages 36-37 %s" % name, kv.get("enc") == tag[144:152].hex().upper())
    v = bytes([0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF])
    check("C++ == Python command-key Encrypt", cmdline is not None and cmdline.get("enc") == ldtag.tea_encrypt(v).hex().upper())
    check("C++ command-key Decrypt round trip", cmdline is not None and cmdline.get("dec") == v.hex().upper())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tags-dir", default=ldtag.DEFAULT_TAGS_DIR)
    ap.add_argument("--cpp", action="store_true", help="also compile and run the C++ cross-check")
    a = ap.parse_args()
    say("selftest_toypad %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    veh = test_crypto(a.tags_dir)
    test_client(a.tags_dir)
    if a.cpp:
        test_cpp(a.tags_dir, veh)
    fails = [n for n, ok in RESULTS if not ok]
    say("RESULT: %s (%d/%d checks passed)%s" % ("PASS" if not fails else "FAIL", len(RESULTS) - len(fails), len(RESULTS),
                                                ("; failed: " + ", ".join(fails)) if fails else ""))
    os.makedirs(OUTDIR, exist_ok=True)
    rep = os.path.join(OUTDIR, "selftest-%s.txt" % datetime.datetime.now().strftime("%H%M%S"))
    with open(rep, "w", encoding="utf-8") as f:
        f.write("\n".join(LINES) + "\n")
    print("report: " + rep)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())

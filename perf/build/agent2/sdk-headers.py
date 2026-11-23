"""Agent 2: list the SDK headers that the generated recomp TUs include (task #1 step 2).

Takes the real compile commands of generated TUs from a compile_commands.json, drops the
object/PCH-use/depfile flags, adds -M -MF (preprocess-only dependency scan; the PCH header is
included textually through cmake_pch.hxx so its whole header chain is listed) and classifies
every dependency. Run from a devshell so clang sees the same INCLUDE/LIB as the build.

usage: python sdk-headers.py <compile_commands.json> <out-prefix> [tu-substring ...]
"""
import json, os, re, shlex, subprocess, sys
from collections import defaultdict

R = r"<workspace>"
DEV_SDK = os.path.join(R, "DimensionsRecomp", "rexglue-sdk")
BASE_SDK = os.path.join(R, "baseline", "DimensionsRecomp", "rexglue-sdk")


def norm(p):
    return os.path.normcase(os.path.normpath(p))


def parse_depfile(text):
    text = text.replace("\\\r\n", " ").replace("\\\n", " ")
    _, _, deps = text.partition(": ")
    out, cur, i = [], "", 0
    while i < len(deps):
        c = deps[i]
        if c == "\\" and i + 1 < len(deps) and deps[i + 1] == " ":
            cur += " "; i += 2; continue
        if c in " \t\r\n":
            if cur: out.append(cur); cur = ""
        else:
            cur += c
        i += 1
    if cur: out.append(cur)
    return out


def scan_cmd(entry, dfile):
    args = entry.get("arguments") or shlex.split(entry["command"], posix=False)
    args = [a[1:-1] if len(a) > 1 and a[0] == a[-1] == '"' else a for a in args]
    res, i = [], 0
    while i < len(args):
        a = args[i]
        if a in ("-o", "-MT", "-MF", "-MQ"): i += 2; continue
        if a in ("-c", "-MD", "-MMD"): i += 1; continue
        if a == "-Xclang" and i + 3 < len(args) and args[i + 1] == "-include-pch":
            i += 4; continue
        res.append(a); i += 1
    return res[:1] + ["-M", "-MF", dfile] + res[1:]


def classify(p, roots):
    n = norm(p)
    for name, root in roots:
        r = norm(root) + os.sep
        if n.startswith(r):
            return name, os.path.relpath(n, norm(root)).replace("\\", "/")
    return "other", p.replace("\\", "/")


def dev_source_for(rel_install):
    """map an installed include path (relative to install/include) to the dev SDK source file."""
    cand = os.path.join(DEV_SDK, "include", rel_install)
    if os.path.isfile(cand):
        return os.path.relpath(cand, R).replace("\\", "/")
    return None


def main():
    db, prefix = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    subs = sys.argv[3:] or ["legodimensions_recomp.0.cpp"]
    entries = json.load(open(db))
    gen = [e for e in entries if re.search(r"[\\/]generated[\\/]default[\\/][^\\/]+\.cpp$", e["file"])]
    print(f"{len(gen)} generated TUs in {db}")
    install_inc = os.path.join(R, "build", "sdk", "install", "include")
    roots = [("sdk-install", install_inc), ("dev-sdk", DEV_SDK), ("baseline-sdk", BASE_SDK),
             ("generated", os.path.join(R, "baseline", "DimensionsRecomp", "rexlego", "generated")),
             ("baseline-game", os.path.join(R, "baseline", "DimensionsRecomp", "rexlego")),
             ("dev-game", os.path.join(R, "DimensionsRecomp", "rexlego")),
             ("llvm", os.path.join(R, "toolchain")),
             ("msvc", r"C:\Program Files\Microsoft Visual Studio"),
             ("winsdk", r"C:\Program Files (x86)\Windows Kits")]
    per_tu = {}
    for s in subs:
        e = next((x for x in gen if os.path.basename(x["file"]) == s), None)
        if e is None:
            print("no TU named", s); continue
        dfile = f"{prefix}-{s}.d"
        cmd = scan_cmd(e, dfile)
        r = subprocess.run(cmd, cwd=e["directory"], capture_output=True, text=True)
        if r.returncode != 0:
            print("FAILED", s, r.returncode, r.stderr[-2000:]); continue
        deps = parse_depfile(open(dfile, encoding="utf-8", errors="replace").read())
        per_tu[s] = deps[1:] if deps and norm(deps[0]) == norm(e["file"]) else deps
        print(f"{s}: {len(per_tu[s])} deps")
    groups = defaultdict(set)
    for s, deps in per_tu.items():
        for d in deps:
            k, rel = classify(d, roots)
            groups[k].add(rel)
    lines = []
    sdk = sorted(groups.get("sdk-install", set()))
    lines.append(f"# SDK headers included by generated TUs ({', '.join(per_tu)}): {len(sdk)} files")
    lines.append("# columns: installed path (build/sdk/install/include/...) -> dev source file (edit this one)")
    unmapped = []
    for rel in sdk:
        src = dev_source_for(rel)
        if src is None: unmapped.append(rel)
        lines.append(f"{rel}\t{src or '?'}")
    for k in sorted(groups):
        if k == "sdk-install": continue
        lines.append(f"# {k}: {len(groups[k])} files")
        lines += [f"  {x}" for x in sorted(groups[k])]
    # same deps for every scanned TU?
    sets = {s: frozenset(norm(d) for d in deps if classify(d, roots)[0] == 'sdk-install') for s, deps in per_tu.items()}
    if len(set(sets.values())) > 1:
        base = next(iter(sets.values()))
        for s, v in sets.items():
            lines.append(f"# {s}: +{len(v - base)} -{len(base - v)} SDK headers vs first TU")
    else:
        lines.append("# all scanned TUs include the identical SDK header set")
    lines.append(f"# unmapped to DimensionsRecomp/rexglue-sdk/include: {len(unmapped)}")
    open(prefix + ".txt", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines[:3])); print(f"... written {prefix}.txt; unmapped={len(unmapped)}")


if __name__ == "__main__":
    main()

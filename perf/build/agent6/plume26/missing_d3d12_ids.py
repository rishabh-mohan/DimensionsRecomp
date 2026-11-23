"""List D3D12 identifiers used by Plume or gpu_native that Windows SDK 10.0.22621 lacks.

Read-only and single-threaded: tokenises the FidelityFX-bundled Agility headers and
the installed Windows SDK 10.0.22621 headers, takes the Agility-only identifiers,
then scans Plume and rexlego/src/gpu_native for them. Each hit is tagged as code or
comment/string, with its enclosing preprocessor conditions.
"""
import os
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
DR = ROOT / "DimensionsRecomp"
AGILITY = DR / "rexglue-sdk/thirdparty/FidelityFX-SDK/framework/cauldron/framework/libs/agilitysdk/include"
WINSDK = pathlib.Path(r"C:\Program Files (x86)\Windows Kits\10\Include\10.0.22621.0")
OUT = pathlib.Path(__file__).resolve().parent / "missing_d3d12_ids.txt"
TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
DIRECTIVE = re.compile(r"\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)")
EXTS = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".inl", ".inc", ".ipp", ".hlsl", ".hlsli"}
SCAN = [DR / "thirdparty/plume", DR / "rexlego/src/gpu_native"]


def tokens(paths):
    found = set()
    for path in paths:
        found.update(TOKEN.findall(path.read_text(encoding="latin-1")))
    return found


def strip_line(line, in_block):
    """Blank comments and string/char literals; return (code, still_in_block_comment)."""
    out = []
    i, n = 0, len(line)
    while i < n:
        if in_block:
            end = line.find("*/", i)
            if end < 0:
                out.append(" " * (n - i))
                return "".join(out), True
            out.append(" " * (end + 2 - i))
            i = end + 2
            in_block = False
            continue
        c = line[i]
        if line.startswith("//", i):
            out.append(" " * (n - i))
            break
        if line.startswith("/*", i):
            in_block = True
            out.append("  ")
            i += 2
            continue
        if c in "\"'":
            j = i + 1
            while j < n and line[j] != c:
                j += 2 if line[j] == "\\" else 1
            j = min(j + 1, n)
            out.append(" " * (j - i))
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out), in_block


def main():
    agility_files = sorted(p for p in AGILITY.glob("*.h")
                           if re.match(r"(d3d12|d3dcommon|dxgiformat)", p.name, re.I))
    winsdk_files = sorted(set((WINSDK / "um").glob("d3d12*.h")) | set((WINSDK / "um").glob("d3dcommon.h"))
                          | set((WINSDK / "shared").glob("dxgi*.h")) | set((WINSDK / "um").glob("dxgi*.h")))
    agility = tokens(agility_files)
    winsdk = tokens(winsdk_files)
    missing = agility - winsdk
    hits = {}
    files = 0
    for base in SCAN:
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d != ".git")
            for name in sorted(filenames):
                path = pathlib.Path(dirpath, name)
                if path.suffix.lower() not in EXTS:
                    continue
                files += 1
                stack = []
                in_block = False
                for number, line in enumerate(path.read_text(encoding="latin-1").splitlines(), 1):
                    code, in_block = strip_line(line, in_block)
                    directive = DIRECTIVE.match(code)
                    if directive:
                        kind, rest = directive.group(1), directive.group(2).strip()
                        if kind in ("if", "ifdef", "ifndef"):
                            stack.append(f"#{kind} {rest}")
                        elif kind == "elif" and stack:
                            stack[-1] = f"{stack[-1]} ... #elif {rest}"
                        elif kind == "else" and stack:
                            stack[-1] = f"{stack[-1]} ... #else"
                        elif kind == "endif" and stack:
                            stack.pop()
                    found = set(TOKEN.findall(line)) & missing
                    if not found:
                        continue
                    code_tokens = set(TOKEN.findall(code))
                    for token in found:
                        where = "code" if token in code_tokens else "comment/string"
                        hits.setdefault(token, []).append(
                            (path.relative_to(ROOT), number, where, list(stack), line.strip()))
    report = [
        f"Agility headers ({len(agility_files)}): " + ", ".join(p.name for p in agility_files),
        f"WinSDK headers ({len(winsdk_files)}): " + ", ".join(str(p.relative_to(WINSDK)) for p in winsdk_files),
        f"tokens: agility={len(agility)} winsdk={len(winsdk)} agility-only={len(missing)}; files scanned={files}",
    ]
    for header in (AGILITY / "d3d12.h", WINSDK / "um/d3d12.h"):
        for line in header.read_text(encoding="latin-1").splitlines():
            if re.search(r"#\s*define\s+D3D12_(PREVIEW_)?SDK_VERSION\b", line):
                report.append(f"{header}: {line.strip()}")
    for token in sorted(hits):
        rows = hits[token]
        in_code = sum(1 for row in rows if row[2] == "code")
        report.append(f"\n{token}: {len(rows)} hit(s), {in_code} in code")
        for rel, number, where, stack, text in rows:
            guard = " | ".join(stack) if stack else "-"
            report.append(f"  {rel}:{number} [{where}] guard: {guard}")
            report.append(f"      {text[:220]}")
    OUT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report[:3]))
    print(f"{len(hits)} agility-only identifier(s) referenced; full listing in {OUT}")
    for token in sorted(hits):
        rows = hits[token]
        in_code = sum(1 for row in rows if row[2] == "code")
        print(f"  {token}: {len(rows)} hit(s), {in_code} in code")


if __name__ == "__main__":
    main()

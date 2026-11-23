"""Agent 6: build fix A (unregistered native settings read as catalog defaults) as patched copies.

Read-only on the live tree. Writes only under build/agent6/fix-a/{orig,new,new-commit}/rexlego/src/.
  new/        = fix A (hunks 1 + 2, the requested smallest fix)
  new-commit/ = fix A + optional hunk 3 (commit path skips unregistered keys)
"""
import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
LIVE = ROOT / "DimensionsRecomp"
OUT = pathlib.Path(__file__).resolve().parent

EXPECT = {
    "rexlego/src/settings_registry.cpp": "A37337001EBDC277B2B94D783939A47096423F0AE8962C8B879A6A60B4F8BA4B",
    "rexlego/src/settings_preferences.cpp": "C78112AA6E50F79D8E6154A37E47CC129C43EAD2E39EC066927374EFBF34B5F0",
}


def crlf(text):
    return text.replace("\n", "\r\n").encode("utf-8")


HUNK1_OLD = crlf(
    "  for (const auto& spec : catalog) {\n"
    "    const auto raw = rex::cvar::GetFlagByName(spec.key);\n"
    "    if (raw.empty()) throw std::runtime_error(\"Native setting is not registered: \" + std::string(spec.key));\n"
)
HUNK1_NEW = crlf(
    "  for (const auto& spec : catalog) {\n"
    "    auto raw = rex::cvar::GetFlagByName(spec.key);\n"
    "    // A cvar this build does not register (the FSR 1 presenter settings exist\n"
    "    // only in REX_HAS_FIDELITYFX_SDK builds) reads as its catalog default.\n"
    "    if (raw.empty() && !rex::cvar::GetFlagInfo(spec.key)) raw = spec.default_value;\n"
    "    if (raw.empty()) throw std::runtime_error(\"Native setting is not registered: \" + std::string(spec.key));\n"
)
HUNK2_OLD = crlf(
    "      const auto source = rex::cvar::GetFlagSource(key);\n"
    "      if (source == rex::cvar::Source::kEnvironment || source == rex::cvar::Source::kCommandLine ||\n"
    "          !NativeSettingOverrideReason(key).empty()) {\n"
)
HUNK2_NEW = crlf(
    "      const auto source = rex::cvar::GetFlagSource(key);\n"
    "      // A cvar this build does not register cannot take a saved value; it keeps\n"
    "      // its catalog default (see ReadRegistryValues), so skip it like an override.\n"
    "      if (source == rex::cvar::Source::kEnvironment || source == rex::cvar::Source::kCommandLine ||\n"
    "          !NativeSettingOverrideReason(key).empty() || !rex::cvar::GetFlagInfo(key)) {\n"
)
HUNK3_OLD = crlf(
    "        for (const auto& spec : catalog) {\n"
    "          if (!NativeSettingOverrideReason(spec.key).empty()) continue;\n"
)
HUNK3_NEW = crlf(
    "        for (const auto& spec : catalog) {\n"
    "          if (!NativeSettingOverrideReason(spec.key).empty() || !rex::cvar::GetFlagInfo(spec.key)) continue;\n"
)


def replace_once(data, old, new, label):
    count = data.count(old)
    if count != 1:
        sys.exit("FAIL: %s target found %d times" % (label, count))
    return data.replace(old, new)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def write(tree, rel, data):
    path = OUT / tree / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    print("%-11s %-38s %s %d" % (tree, rel, sha(data), len(data)))


src = {}
for rel, want in EXPECT.items():
    data = (LIVE / rel).read_bytes()
    if sha(data) != want:
        sys.exit("FAIL: live %s is %s, expected %s" % (rel, sha(data), want))
    src[rel] = data
    write("orig", rel, data)

reg = replace_once(src["rexlego/src/settings_registry.cpp"], HUNK1_OLD, HUNK1_NEW, "hunk 1")
pref = replace_once(src["rexlego/src/settings_preferences.cpp"], HUNK2_OLD, HUNK2_NEW, "hunk 2")
write("new", "rexlego/src/settings_registry.cpp", reg)
write("new", "rexlego/src/settings_preferences.cpp", pref)
reg3 = replace_once(reg, HUNK3_OLD, HUNK3_NEW, "hunk 3")
write("new-commit", "rexlego/src/settings_registry.cpp", reg3)
print("OK")

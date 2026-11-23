"""S3.4 (task #12 (c)): LEGO_NATIVE_SHADER_MISS_CACHE stopgap, default OFF, on scratch copies only.

    python build/agent4/s34/make_patch_s34.py

Reads the live shaders.cpp, which must still hash to E87A2DEE... (913 CRLF lines). Writes, next to this script:
  shaders.before.cpp  exact copy of the live bytes
  shaders.cpp         the patched file (CRLF kept)
  shaders-s34.patch   git-style unified diff, paths relative to DimensionsRecomp/, CRLF content kept
and the two scratch trees used by compile_copy_shaders.ps1:
  build/agent4/s34tree/DimensionsRecomp/rexlego/src/gpu_native/shaders.cpp  (patched)
  build/agent4/s34base/DimensionsRecomp/rexlego/src/gpu_native/shaders.cpp  (control, live bytes)
It never writes the live file (Agent 1: S4 review only, no live apply and no build tonight).
Every edit is anchored on exact live line numbers and asserted text; edits are applied bottom-up.
"""
import difflib
import hashlib
from pathlib import Path

here = Path(__file__).resolve().parent
workspace = here.parents[2]
live = workspace / 'DimensionsRecomp/rexlego/src/gpu_native/shaders.cpp'
LIVE_SHA = 'E87A2DEE43D38D8EBBEE8EFD663DE70A293F7826B5AC0231B8B8A08E6A7E916D'
LIVE_LINES = 913
REL = b'rexlego/src/gpu_native/shaders.cpp'
CRLF = b'\r\n'


def block(text: str) -> list:
    lines = text.strip('\n').split('\n')
    for line in lines:
        assert '\t' not in line and line == line.rstrip(), repr(line)
    return [line.encode('ascii') for line in lines]


# E1: after line 208 (blank line after CaptureMissingPlacementShader), before PlacementShaderUnchanged.
HELPERS = block(r'''
// LEGO_NATIVE_SHADER_MISS_CACHE=1 (default OFF): remember a placement shader that missed the AOT index, so its
// later binds skip ReadableGuestSpan and FindShaderByMicrocode. An entry replays the miss (warning counter and
// line included) only while the pack generation is unchanged and a CPU write stamp, armed before the lookup,
// proves unchanged every byte the lookup could read. Capture runs (LEGO_DUMP_MISSING_SHADERS) keep the full path.
bool ShaderMissEnvironmentSet(const char* name, bool zero_disables) {
  char* value = nullptr;
  size_t length = 0;
  _dupenv_s(&value, &length, name);
  const bool result = value && length > 1 && !(zero_disables && std::strcmp(value, "0") == 0);
  std::free(value);
  return result;
}

bool ShaderMissCacheEnabled() {
  static const bool enabled = ShaderMissEnvironmentSet("LEGO_NATIVE_SHADER_MISS_CACHE", true) &&
                              !ShaderMissEnvironmentSet("LEGO_DUMP_MISSING_SHADERS", false);
  return enabled;
}

// FindShaderByMicrocode hashes the 8 prefix bytes, then each index entry of the same stage and prefix whose
// microcode size fits readable_size. With readable_size >= this span no candidate is skipped, so while these
// bytes and the static index (pack generation 0) are unchanged the lookup misses again. 16 covers the logged words.
u32 ShaderMissSpan(u64 prefix, ShaderStage stage) {
  static const auto spans = [] {
    std::array<std::unordered_map<u64, u32>, 2> result;
    for (size_t i = 0; i < ::g_shaderMicrocodeEntryCount; ++i) {
      const ::ShaderMicrocodeEntry& entry = ::g_shaderMicrocodeEntries[i];
      if (!entry.microcodeSize || entry.stage > 1) continue;
      u32& span = result[entry.stage][entry.prefixHash];
      span = std::max<u32>(span, entry.microcodeSize);
    }
    return result;
  }();
  const auto& table = spans[StageIndex(stage)];
  const auto it = table.find(prefix);
  return std::max<u32>(16, it == table.end() ? 0 : it->second);
}

struct ShaderMissEntry {
  ShaderStage stage = ShaderStage::kVertex;
  u32 guest_address = 0;
  u32 container_address = 0;
  u32 span = 0;
  u64 pack_generation = 0;
  u64 prefix = 0;
  std::array<u32, 4> words{};
  CpuMemoryStamp stamp;
};

// Taken before the lookup; the stamp covers [container_address, container_address + span).
struct ShaderMissArm {
  ShaderStage stage = ShaderStage::kVertex;
  u32 container_address = 0;
  u32 span = 0;
  u64 pack_generation = 0;
  u64 prefix = 0;
  CpuMemoryStamp stamp;
  bool armed() const { return !stamp.pages.empty(); }
};

constexpr size_t kShaderMissCacheCapacity = 256;
// Leaf lock: held only for map operations and lock-free validity checks, never across a guest query or lock.
std::mutex g_miss_cache_mutex;
std::array<std::unordered_map<u64, std::shared_ptr<const ShaderMissEntry>>, 2> g_miss_cache;
// Moves on every insert, so PoolCopyMayTouchShaders marks the new span. OFF: stays 0.
std::atomic<u64> g_miss_cache_generation{0};

u64 ShaderMissKey(u32 guest_address, u32 container_address) {
  return (u64(guest_address) << 32) | container_address;
}

bool ShaderMissValid(const ShaderMissEntry& entry) {
  return entry.pack_generation == PrecompiledShaderPackGeneration() && CpuMemoryUnchanged(entry.stamp);
}

void LogMissingPlacementShader(ShaderStage stage, u32 guest_address, u32 container_address, u64 prefix,
                               const std::array<u32, 4>& words) {
  REXLOG_WARN("Native GPU: placement {} shader 0x{:08X} backing "
              "0x{:08X} prefix=0x{:016X} words={:08X} {:08X} "
              "{:08X} {:08X} missing from AOT index",
              stage == ShaderStage::kVertex ? "vertex" : "pixel",
              guest_address, container_address, prefix,
              words[0], words[1], words[2], words[3]);
}

ShaderMissArm ArmShaderMiss(u32 container_address, const uint8_t* microcode, size_t readable_size,
                            ShaderStage stage) {
  ShaderMissArm arm;
  // Pack microcode entries are outside the span table.
  arm.pack_generation = PrecompiledShaderPackGeneration();
  if (arm.pack_generation) return arm;
  arm.prefix = XXH3_64bits(microcode, 8);
  arm.span = ShaderMissSpan(arm.prefix, stage);
  if (readable_size < arm.span) return arm;
  arm.stage = stage;
  arm.container_address = container_address;
  const CpuMemorySpan span{container_address, arm.span};
  // Empty when the memory watch is off or the span has no physical backing: then nothing is remembered.
  arm.stamp = WatchCpuMemory({&span, 1});
  return arm;
}

// g_miss_cache_mutex held.
void SweepShaderMisses() {
  for (auto& map : g_miss_cache)
    std::erase_if(map, [](const auto& item) { return !ShaderMissValid(*item.second); });
}

void RememberShaderMiss(ShaderMissArm arm, u32 guest_address, const uint8_t* microcode) {
  // A different prefix means the bytes changed before the stamp was armed: the span was measured for another bucket.
  if (XXH3_64bits(microcode, 8) != arm.prefix) return;
  auto entry = std::make_shared<ShaderMissEntry>();
  entry->stage = arm.stage;
  entry->guest_address = guest_address;
  entry->container_address = arm.container_address;
  entry->span = arm.span;
  entry->pack_generation = arm.pack_generation;
  entry->prefix = arm.prefix;
  const auto* words = reinterpret_cast<const be_u32*>(microcode);
  for (size_t i = 0; i < entry->words.size(); ++i) entry->words[i] = static_cast<u32>(words[i]);
  entry->stamp = std::move(arm.stamp);
  // Still clean after the lookup and these reads: the entry describes exactly the bytes the lookup hashed.
  if (!ShaderMissValid(*entry)) return;
  const u64 key = ShaderMissKey(guest_address, entry->container_address);
  bool inserted = false;
  {
    std::lock_guard lock(g_miss_cache_mutex);
    auto& map = g_miss_cache[StageIndex(entry->stage)];
    const auto full = [] { return g_miss_cache[0].size() + g_miss_cache[1].size() >= kShaderMissCacheCapacity; };
    if (!map.contains(key) && full()) SweepShaderMisses();
    if (map.contains(key) || !full()) {
      map.insert_or_assign(key, entry);
      g_miss_cache_generation.fetch_add(1, std::memory_order_release);
      inserted = true;
    }
  }
  static std::atomic<u32> events{0};
  if (inserted && events.fetch_add(1, std::memory_order_relaxed) < 64)
    LongProbeEvent("shader_miss_cache_insert", false, "stage=", static_cast<u32>(entry->stage),
        "guest=", guest_address, "physical=", entry->container_address, "span=", entry->span,
        "prefix=", entry->prefix);
}

// True when a remembered miss still holds; it is counted and logged exactly as the full path would.
bool ReplayShaderMiss(u32 guest_address, u32 container_address, ShaderStage stage) {
  const u64 key = ShaderMissKey(guest_address, container_address);
  auto& map = g_miss_cache[StageIndex(stage)];
  std::shared_ptr<const ShaderMissEntry> entry;
  {
    std::lock_guard lock(g_miss_cache_mutex);
    const auto it = map.find(key);
    if (it == map.end()) return false;
    entry = it->second;
  }
  if (!ShaderMissValid(*entry)) {
    std::lock_guard lock(g_miss_cache_mutex);
    const auto it = map.find(key);
    if (it != map.end() && it->second == entry) map.erase(it);
    return false;
  }
  if (g_shader_warning_count.fetch_add(1, std::memory_order_relaxed) < 16)
    LogMissingPlacementShader(stage, guest_address, container_address, entry->prefix, entry->words);
  return true;
}

std::vector<std::shared_ptr<const ShaderMissEntry>> ShaderMissEntries() {
  std::vector<std::shared_ptr<const ShaderMissEntry>> entries;
  if (!ShaderMissCacheEnabled()) return entries;
  std::lock_guard lock(g_miss_cache_mutex);
  for (const auto& map : g_miss_cache)
    for (const auto& item : map) entries.push_back(item.second);
  return entries;
}

void ForgetShaderMisses(u32 guest_address) {
  if (!ShaderMissCacheEnabled()) return;
  std::lock_guard lock(g_miss_cache_mutex);
  for (auto& map : g_miss_cache)
    std::erase_if(map, [&](const auto& item) { return item.second->guest_address == guest_address; });
}

// Pool copies write through host pointers; drop the overlapping misses as the registry drops resources.
void ForgetShaderMissesOverlapping(PhysicalCopyRange destination) {
  std::vector<std::shared_ptr<const ShaderMissEntry>> overlapping;
  for (auto& entry : ShaderMissEntries())
    if (GuestRangeOverlapsPoolCopy(entry->container_address, entry->span, destination))
      overlapping.push_back(std::move(entry));
  if (overlapping.empty()) return;
  std::lock_guard lock(g_miss_cache_mutex);
  for (const auto& entry : overlapping) {
    auto& map = g_miss_cache[StageIndex(entry->stage)];
    const auto it = map.find(ShaderMissKey(entry->guest_address, entry->container_address));
    if (it != map.end() && it->second == entry) map.erase(it);
  }
}

void ClearShaderMisses() {
  if (!ShaderMissCacheEnabled()) return;
  std::lock_guard lock(g_miss_cache_mutex);
  for (auto& map : g_miss_cache) map.clear();
}
''') + [b'']

# E2: AdoptShader, live lines 285-308 (after the container_address null check, through the miss return).
ADOPT_OLD = block(r'''
  // XDK placement objects retain the copied physical microcode, not the
  // original ShaderContainer. Associate it with the independently indexed
  // AOT entry before creating any host object.
  const size_t readable_size = ReadableGuestSpan(container_address);
  if (readable_size < 8) return nullptr;
  const auto* microcode =
      memory->TranslateVirtual<const uint8_t*>(container_address);
  const ShaderCacheEntry* cache_entry = FindShaderByMicrocode(
      microcode, expected_stage == ShaderStage::kPixel ? 1u : 0u, readable_size);
  if (!cache_entry) {
    CaptureMissingPlacementShader(guest_address, container_address, microcode,
                                  readable_size, expected_stage);
    if (g_shader_warning_count.fetch_add(1, std::memory_order_relaxed) < 16) {
      const auto* words = reinterpret_cast<const be_u32*>(microcode);
      REXLOG_WARN("Native GPU: placement {} shader 0x{:08X} backing "
                  "0x{:08X} prefix=0x{:016X} words={:08X} {:08X} "
                  "{:08X} {:08X} missing from AOT index",
                  expected_stage == ShaderStage::kVertex ? "vertex" : "pixel",
                  guest_address, container_address, XXH3_64bits(microcode, 8),
                  static_cast<u32>(words[0]), static_cast<u32>(words[1]),
                  readable_size >= 12 ? static_cast<u32>(words[2]) : 0u,
                  readable_size >= 16 ? static_cast<u32>(words[3]) : 0u);
    }
    return nullptr;
''')
ADOPT_NEW = block(r'''
  // A remembered miss whose bytes and pack generation are unchanged skips the span query and the lookup.
  if (ShaderMissCacheEnabled() && ReplayShaderMiss(guest_address, container_address, expected_stage))
    return nullptr;
  // XDK placement objects retain the copied physical microcode, not the
  // original ShaderContainer. Associate it with the independently indexed
  // AOT entry before creating any host object.
  const size_t readable_size = ReadableGuestSpan(container_address);
  if (readable_size < 8) return nullptr;
  const auto* microcode =
      memory->TranslateVirtual<const uint8_t*>(container_address);
  // Armed before the lookup, so a write during it dirties the stamp instead of remembering a stale miss.
  ShaderMissArm miss_arm;
  if (ShaderMissCacheEnabled())
    miss_arm = ArmShaderMiss(container_address, microcode, readable_size, expected_stage);
  const ShaderCacheEntry* cache_entry = FindShaderByMicrocode(
      microcode, expected_stage == ShaderStage::kPixel ? 1u : 0u, readable_size);
  if (!cache_entry) {
    CaptureMissingPlacementShader(guest_address, container_address, microcode,
                                  readable_size, expected_stage);
    if (g_shader_warning_count.fetch_add(1, std::memory_order_relaxed) < 16) {
      const auto* words = reinterpret_cast<const be_u32*>(microcode);
      LogMissingPlacementShader(expected_stage, guest_address, container_address,
                                XXH3_64bits(microcode, 8),
                                {static_cast<u32>(words[0]), static_cast<u32>(words[1]),
                                 readable_size >= 12 ? static_cast<u32>(words[2]) : 0u,
                                 readable_size >= 16 ? static_cast<u32>(words[3]) : 0u});
    }
    if (miss_arm.armed()) RememberShaderMiss(std::move(miss_arm), guest_address, microcode);
    return nullptr;
''')

FORGET_GUEST = block(r'''
  // Before the registry lookup: a failed bind never registered, but it may be remembered as a miss.
  ForgetShaderMisses(guest_address);
''')

POOL_KEY_OLD = block(r'''
  const u64 generation = g_shader_registry_generation.load(std::memory_order_acquire);
  if (!index.Current(generation, 0)) {
''')
POOL_KEY_NEW = block(r'''
  const u64 generation = g_shader_registry_generation.load(std::memory_order_acquire);
  // OFF: stays 0, so the key is the registry generation alone, as before.
  const u64 miss_generation = g_miss_cache_generation.load(std::memory_order_acquire);
  if (!index.Current(generation, miss_generation)) {
''')
POOL_MARK_OLD = block(r'''
    }
    index.key[0] = generation;
    index.key[1] = 0;
''')
POOL_MARK_NEW = block(r'''
    }
    // Remembered misses: a pool copy over their code must reach InvalidatePoolCopyShaders as well.
    for (const auto& entry : ShaderMissEntries()) {
      PhysicalCopyRange physical;
      if (PoolCopyPhysicalRange(entry->container_address, entry->span, physical)) index.pages.Mark(physical);
    }
    index.key[0] = generation;
    index.key[1] = miss_generation;
''')


def main():
    data = live.read_bytes()
    sha = hashlib.sha256(data).hexdigest().upper()
    assert sha == LIVE_SHA, f'live shaders.cpp changed: {sha}'
    parts = data.split(CRLF)
    assert parts[-1] == b'', 'live file does not end with CRLF'
    lines = parts[:-1]
    assert not any(b'\r' in line or b'\n' in line for line in lines), 'bare CR or LF in the live file'
    assert len(lines) == LIVE_LINES, len(lines)
    for name in (b'ShaderMiss', b'g_miss_cache', b'LogMissingPlacementShader', b'LEGO_NATIVE_SHADER_MISS_CACHE'):
        assert name not in data, name

    def at(number):  # 1-based live line
        return lines[number - 1]

    def expect(number, text):
        assert at(number) == text, (number, at(number), text)

    # Anchors (1-based live line numbers).
    expect(207, b'}')
    expect(208, b'')
    expect(209, b'bool PlacementShaderUnchanged(ShaderResource& resource) {')
    expect(243, b'std::shared_ptr<ShaderResource> AdoptShader(u32 guest_address,')
    expect(282, b'  if (!container_address) {')
    expect(283, b'    return nullptr;')
    expect(284, b'  }')
    assert lines[284:308] == ADOPT_OLD, 'AdoptShader 285-308 changed'
    expect(309, b'  }')
    expect(718, b'void InvalidatePlacementShader(u32 guest_address) {')
    expect(719, b'  RegistryOnlyScope registry_only;')
    expect(720, b'  auto recording = HostDevice::LockRecording();')
    expect(725, b'    if (it == g_registry.end() || it->second->owns_guest_memory) return;')
    expect(750, b'bool PoolCopyMayTouchShaders(PhysicalCopyRange range) {')
    assert lines[751:753] == POOL_KEY_OLD, 'PoolCopyMayTouchShaders 752-753 changed'
    assert lines[768:771] == POOL_MARK_OLD, 'PoolCopyMayTouchShaders 769-771 changed'
    expect(776, b'u32 InvalidatePoolCopyShaders(PhysicalCopyRange destination) {')
    expect(795, b'  }')
    expect(796, b'  const u32 count = u32(retired.size());')
    expect(889, b'void ResetShaderResources() {')
    expect(904, b'    g_registry.clear();')
    expect(905, b'  }')
    expect(906, b'  for (const u32 guest_address : guest_addresses) {')

    out = list(lines)
    # Bottom-up, so the earlier live line numbers stay valid.
    out[905:905] = [b'  ClearShaderMisses();']                       # E6 after 905
    out[795:795] = [b'  ForgetShaderMissesOverlapping(destination);']  # E5 after 795
    out[768:771] = POOL_MARK_NEW                                      # E4b 769-771
    out[751:753] = POOL_KEY_NEW                                       # E4a 752-753
    out[720:720] = FORGET_GUEST                                       # E3 after 720
    out[284:308] = ADOPT_NEW                                          # E2 285-308
    out[208:208] = HELPERS                                            # E1 after 208

    patched = CRLF.join(out) + CRLF
    old = data.splitlines(keepends=True)
    new = patched.splitlines(keepends=True)
    diff = difflib.diff_bytes(difflib.unified_diff, old, new, fromfile=b'a/' + REL, tofile=b'b/' + REL, n=3)
    patch = b'diff --git a/' + REL + b' b/' + REL + b'\n' + b''.join(diff)

    (here / 'shaders.before.cpp').write_bytes(data)
    (here / 'shaders.cpp').write_bytes(patched)
    (here / 'shaders-s34.patch').write_bytes(patch)
    for tree, payload in (('s34tree', patched), ('s34base', data)):
        target = here.parent / tree / 'DimensionsRecomp/rexlego/src/gpu_native/shaders.cpp'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)

    added = sum(1 for line in patch.split(b'\n') if line.startswith(b'+') and not line.startswith(b'+++'))
    removed = sum(1 for line in patch.split(b'\n') if line.startswith(b'-') and not line.startswith(b'---'))
    hunks = patch.count(b'\n@@ ')
    for name, payload in (('before', data), ('after ', patched)):
        print(f'{name}: sha256 {hashlib.sha256(payload).hexdigest().upper()} bytes {len(payload):,} '
              f'lines {payload.count(CRLF):,}')
    print(f'patch : sha256 {hashlib.sha256(patch).hexdigest().upper()} bytes {len(patch):,} '
          f'+{added}/-{removed} hunks {hunks}')
    assert b'\r' not in patched.replace(CRLF, b'') and patched.count(b'\n') == patched.count(CRLF)


if __name__ == '__main__':
    main()

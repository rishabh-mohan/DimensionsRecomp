#include "gpu_native/pipeline_library.h"

#include <windows.h>
#include <d3d12.h>
#include <wrl/client.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <thread>
#include <unordered_set>
#include <vector>

#include <rex/logging.h>
#include <plume_d3d12.h>

#define XXH_INLINE_ALL
#include <xxhash.h>
#include "gpu_native/pipeline_parallel.h"
#include "gpu_native/pipeline_recipes.h"
#include "gpu_native/pipeline_snapshot.h"
#include "gpu_native/pipeline_stats.h"

namespace legodimensions::gpu_native {
namespace {

using Clock = std::chrono::steady_clock;
// A library past this size is dropped and rebuilt rather than grown forever
// across shader-bank changes (old entries never match new bytecode).
constexpr uint64_t kMaxLibraryBytes = 512ull << 20;
constexpr auto kQuietBeforeSave = std::chrono::seconds(3);

void HashBytecode(XXH3_state_t* state, const D3D12_SHADER_BYTECODE& code) {
  const uint64_t size = code.pShaderBytecode ? code.BytecodeLength : 0;
  XXH3_128bits_update(state, &size, sizeof(size));
  if (size) XXH3_128bits_update(state, code.pShaderBytecode, size);
}

template <typename T>
void HashValue(XXH3_state_t* state, const T& value) {
  XXH3_128bits_update(state, &value, sizeof(value));
}

// Every field Plume fills in, by value. Pointers are followed (bytecode,
// semantic names) and never hashed themselves, so the name is stable across runs.
std::wstring PipelineName(const D3D12_GRAPHICS_PIPELINE_STATE_DESC& desc,
                          const void* root_data, std::size_t root_size) {
  XXH3_state_t state;
  XXH3_128bits_reset(&state);
  constexpr uint32_t kVersion = 2;
  HashValue(&state, kVersion);
  HashBytecode(&state, desc.VS);
  HashBytecode(&state, desc.PS);
  HashBytecode(&state, desc.GS);
  HashBytecode(&state, desc.HS);
  HashBytecode(&state, desc.DS);
  HashValue(&state, desc.BlendState);
  HashValue(&state, desc.SampleMask);
  HashValue(&state, desc.RasterizerState);
  HashValue(&state, desc.DepthStencilState);
  HashValue(&state, desc.IBStripCutValue);
  HashValue(&state, desc.PrimitiveTopologyType);
  HashValue(&state, desc.NumRenderTargets);
  HashValue(&state, desc.RTVFormats);
  HashValue(&state, desc.DSVFormat);
  HashValue(&state, desc.SampleDesc);
  HashValue(&state, desc.NodeMask);
  HashValue(&state, desc.Flags);
  HashValue(&state, desc.InputLayout.NumElements);
  for (UINT i = 0; i < desc.InputLayout.NumElements; ++i) {
    const auto& element = desc.InputLayout.pInputElementDescs[i];
    const char* name = element.SemanticName ? element.SemanticName : "";
    XXH3_128bits_update(&state, name, std::strlen(name) + 1);
    HashValue(&state, element.SemanticIndex);
    HashValue(&state, element.Format);
    HashValue(&state, element.InputSlot);
    HashValue(&state, element.AlignedByteOffset);
    HashValue(&state, element.InputSlotClass);
    HashValue(&state, element.InstanceDataStepRate);
  }
  if (root_size) XXH3_128bits_update(&state, root_data, root_size);
  const XXH128_hash_t hash = XXH3_128bits_digest(&state);
  wchar_t text[40];
  std::swprintf(text, 40, L"%016llx%016llx", static_cast<unsigned long long>(hash.high64),
                static_cast<unsigned long long>(hash.low64));
  return text;
}

std::wstring PipelineName(const D3D12_GRAPHICS_PIPELINE_STATE_DESC& desc) {
  return PipelineName(desc, nullptr, 0);
}

std::filesystem::path CachePath() {
  wchar_t module[MAX_PATH]{};
  const DWORD length = GetModuleFileNameW(nullptr, module, MAX_PATH);
  std::filesystem::path base = length ? std::filesystem::path(module).parent_path()
                                      : std::filesystem::current_path();
  return base / "cache" / "native-pso.bin";
}

// LEGO_NATIVE_PSO_PREPARE_THREADS=<n> spreads startup preparation over n
// threads, at most 8 and at most the core count. Unset, 0 or 1: the serial loop.
unsigned PreparationThreads() {
  const char* value = std::getenv("LEGO_NATIVE_PSO_PREPARE_THREADS");
  if (!value || !*value) return 1;
  const unsigned long requested = std::strtoul(value, nullptr, 10);
  const unsigned limit = std::clamp(std::thread::hardware_concurrency(), 1u, 8u);
  return unsigned(std::clamp<unsigned long>(requested, 1, limit));
}

// Preparation workers run at most this many recipes ahead of the in-order commit.
constexpr std::size_t kPrepareWindow = 64;

enum class PrepareResult : uint8_t { kLoaded, kCompiled, kFailed, kRemoved };

struct PreparedPipeline {
  PrepareResult result = PrepareResult::kFailed;
  Microsoft::WRL::ComPtr<ID3D12PipelineState> pipeline;
  uint64_t load_ns = 0, compile_ns = 0;  // measured only while PSO stats are on
};

struct PrepareTotals {
  uint64_t loaded = 0, compiled = 0, failed = 0;
  uint64_t load_ns = 0, compile_ns = 0, max_compile_ns = 0;
};

// CreateGraphicsPipelineState for an auxiliary pipeline the library does not cover.
bool CreateUncached(ID3D12Device* device, const D3D12_GRAPHICS_PIPELINE_STATE_DESC& desc,
                    ID3D12PipelineState** pipeline) {
  if (!pso_stats::Enabled())
    return SUCCEEDED(device->CreateGraphicsPipelineState(&desc, IID_PPV_ARGS(pipeline)));
  const uint64_t start = pso_stats::Nanos();
  const bool compiled = SUCCEEDED(device->CreateGraphicsPipelineState(&desc, IID_PPV_ARGS(pipeline)));
  pso_stats::OnAuxiliary(false, compiled, pso_stats::Nanos() - start);
  return compiled;
}

class PipelineLibrary final : public plume::D3D12GraphicsPipelineCache {
 public:
  bool Open(ID3D12Device8* device) {
    const bool stats = pso_stats::Enabled();
    const uint64_t read_start = stats ? pso_stats::Nanos() : 0;
    device_ = device;
    path_ = CachePath();
    recipe_path_ = path_.parent_path() / "native-pso-recipes.bin";
    seed_path_ = path_.parent_path().parent_path() / "native-pso-seed.bin";
    std::error_code error;
    const auto size = std::filesystem::file_size(path_, error);
    if (!error && size && size <= kMaxLibraryBytes) {
      blob_.resize(size_t(size));
      std::ifstream file(path_, std::ios::binary);
      if (!file.read(reinterpret_cast<char*>(blob_.data()), std::streamsize(size))) blob_.clear();
    }
    const uint64_t file_bytes = blob_.size();
    const uint64_t create_start = stats ? pso_stats::Nanos() : 0;
    // The driver rejects a blob from another driver version or adapter;
    // start empty then, and the next save replaces the stale file.
    HRESULT result = E_FAIL;
    if (!blob_.empty())
      result = device->CreatePipelineLibrary(blob_.data(), blob_.size(), IID_PPV_ARGS(&library_));
    const bool accepted = SUCCEEDED(result);
    if (FAILED(result)) {
      if (!blob_.empty())
        REXLOG_INFO("Native GPU: pipeline cache {} rejected by the driver (0x{:08X}); rebuilding",
                    path_.string(), static_cast<uint32_t>(result));
      blob_.clear();
      library_ = nullptr;
      result = device->CreatePipelineLibrary(nullptr, 0, IID_PPV_ARGS(&library_));
    }
    const auto opened = [&](pso_stats::CacheState state) {
      if (stats)
        pso_stats::OnOpen(state, file_bytes, create_start - read_start, pso_stats::Nanos() - create_start);
    };
    if (FAILED(result) || !library_) {
      REXLOG_WARN("Native GPU: pipeline cache unavailable (0x{:08X})", static_cast<uint32_t>(result));
      opened(pso_stats::CacheState::kUnavailable);
      return false;
    }
    REXLOG_INFO("Native GPU: pipeline cache {} opened ({} bytes)", path_.string(), blob_.size());
    opened(accepted     ? pso_stats::CacheState::kLoaded
           : file_bytes ? pso_stats::CacheState::kRejected
                        : pso_stats::CacheState::kNoFile);
    return true;
  }

  ~PipelineLibrary() override {
    if (library_) library_->Release();
  }

  void Prepare(ID3D12RootSignature* root) {
    root_ = root;
    if (!StartupPipelinePreparationEnabled()) {
      root_ = nullptr;
      REXLOG_INFO("Native GPU: startup pipeline preparation disabled by LEGO_NATIVE_PSO_PRECOMPILE=0");
      return;
    }
    const auto start = Clock::now();
    ReadRecipes(recipe_path_, recipes_);
    const bool stats = pso_stats::Enabled();
    const unsigned threads = PreparationThreads();
    if (threads > 1)
      REXLOG_INFO("Native GPU: startup pipeline preparation uses {} threads (LEGO_NATIVE_PSO_PREPARE_THREADS)",
                  threads);
    PrepareTotals totals;
    auto next_progress = Clock::now() + std::chrono::seconds(2);
    std::vector<D3D12_INPUT_ELEMENT_DESC> inputs;
    std::unordered_set<std::wstring> prepared;
    const auto progress = [&] {
      if (Clock::now() >= next_progress) {
        REXLOG_INFO("Native GPU: startup pipeline preparation processed {} recipes",
                    totals.loaded + totals.compiled + totals.failed);
        next_progress = Clock::now() + std::chrono::seconds(2);
      }
    };
    // Applies one recipe's result on this thread, in recipe order, exactly as
    // the serial loop always has. Returns false once the device is removed.
    const auto commit = [&](const std::wstring& name, PreparedPipeline&& item) {
      totals.load_ns += item.load_ns;
      totals.compile_ns += item.compile_ns;
      totals.max_compile_ns = std::max(totals.max_compile_ns, item.compile_ns);
      switch (item.result) {
        case PrepareResult::kLoaded:
          ++totals.loaded;
          break;
        case PrepareResult::kCompiled:
          ++totals.compiled;
          Store(name, item.pipeline.Get());
          break;
        case PrepareResult::kFailed:
          ++totals.failed;
          return true;
        case PrepareResult::kRemoved:
          ++totals.failed;
          return false;
      }
      prepared.insert(name);
      // Keep the first pipelines resident. Later ones use the driver library.
      constexpr size_t kMaxResident = 512;
      if (warmed_.size() < kMaxResident) warmed_.emplace(name, std::move(item.pipeline));
      return true;
    };
    const auto prepare = [&](const PipelineRecipes& source) {
      if (threads > 1) return PrepareParallel(source, threads, stats, prepared, progress, commit);
      for (const auto& recipe : source.Entries()) {
        const std::wstring name(recipe->name.begin(), recipe->name.end());
        if (prepared.contains(name)) continue;
        progress();
        const auto desc = source.Describe(*recipe, root_, inputs);
        if (!commit(name, stats ? PrepareOne<true>(name, desc) : PrepareOne<false>(name, desc))) return false;
      }
      return true;
    };
    // Seed files are read one at a time. The portable seed does not use the
    // capacity reserved for recipes learned and saved by this installation.
    if (prepare(recipes_)) {
      for (const auto& path : SeedPaths()) {
        PipelineRecipes seed;
        if (!ReadRecipes(path, seed)) continue;
        REXLOG_INFO("Native GPU: using startup pipeline seed {} with {} recipes",
                    path.string(), seed.Entries().size());
        const bool complete = prepare(seed);
        for (const auto& recipe : seed.Entries()) {
          std::wstring name(recipe->name.begin(), recipe->name.end());
          if (prepared.contains(name)) seed_names_.insert(std::move(name));
        }
        if (!complete) break;
      }
    }
    const auto old_count = recipes_.Entries().size();
    if (std::any_of(recipes_.Entries().begin(), recipes_.Entries().end(), [&](const auto& recipe) {
          return seed_names_.contains(std::wstring(recipe->name.begin(), recipe->name.end()));
        })) {
      PipelineRecipes novel;
      bool retained = true;
      for (const auto& recipe : recipes_.Entries()) {
        const std::wstring name(recipe->name.begin(), recipe->name.end());
        if (!seed_names_.contains(name))
          retained &= novel.Record(name, recipes_.Describe(*recipe, root_, inputs));
      }
      if (retained) {
        recipes_ = std::move(novel);
        recipes_dirty_ = true;
        REXLOG_INFO("Native GPU: removed {} seeded pipelines from local recording",
                    old_count - recipes_.Entries().size());
      }
    }
    if (stats)
      pso_stats::OnPrepare({totals.loaded, totals.compiled, totals.failed, warmed_.size(), threads,
                            uint64_t(std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now() - start).count()),
                            totals.load_ns, totals.compile_ns, totals.max_compile_ns});
    if (!totals.loaded && !totals.compiled && !totals.failed) {
      REXLOG_INFO("Native GPU: no startup pipeline recipes yet; recording during gameplay");
      return;
    }
    REXLOG_INFO("Native GPU: startup pipelines loaded={} compiled={} failed={} resident={} elapsed_ms={}",
                totals.loaded, totals.compiled, totals.failed, warmed_.size(),
                std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - start).count());
  }

  ID3D12PipelineState* load(const D3D12_GRAPHICS_PIPELINE_STATE_DESC& desc) override {
    return pso_stats::Enabled() ? Load<true>(desc) : Load<false>(desc);
  }

  void store(const D3D12_GRAPHICS_PIPELINE_STATE_DESC& desc, ID3D12PipelineState* pipeline) override {
    if (pso_stats::Enabled())
      StoreCompiled<true>(desc, pipeline);
    else
      StoreCompiled<false>(desc, pipeline);
  }

  bool CreateAuxiliary(ID3D12Device* device, const D3D12_GRAPHICS_PIPELINE_STATE_DESC& desc,
                       const void* root_data, std::size_t root_size,
                       ID3D12PipelineState** pipeline) {
    if (device != device_ || !root_data || !root_size) return CreateUncached(device, desc, pipeline);
    return pso_stats::Enabled() ? Auxiliary<true>(device, desc, root_data, root_size, pipeline)
                                : Auxiliary<false>(device, desc, root_data, root_size, pipeline);
  }

  void Frame() {
    {
      // This is an opportunistic save check on the present thread. Serialize
      // holds the same mutex on a background thread; never wait for it here.
      std::unique_lock lock(mutex_, std::try_to_lock);
      if (!lock.owns_lock() || (!unsaved_ && !recipes_dirty_) ||
          Clock::now() - last_store_ < kQuietBeforeSave) return;
    }
    bool expected = false;
    if (!saving_.compare_exchange_strong(expected, true)) return;
    std::thread([this] {
      Save();
      saving_.store(false);
    }).detach();
  }

  void Stop() {
    while (saving_.load()) std::this_thread::sleep_for(std::chrono::milliseconds(5));
    Save();
    std::lock_guard lock(mutex_);
    warmed_.clear();
    seed_names_.clear();
    root_ = nullptr;
    recipes_ = {};
    REXLOG_INFO("Native GPU: pipeline cache hits={} misses={} stored={} saves={}",
                stats_.hits, stats_.misses, stats_.stored, stats_.saves);
  }

  PipelineLibraryStats Stats() {
    std::lock_guard lock(mutex_);
    return stats_;
  }

 private:
  // load(), store() and CreateAuxiliary() with the PSO stats compiled in or
  // out. The <false> versions are the code these functions had before.
  template <bool kStats>
  ID3D12PipelineState* Load(const D3D12_GRAPHICS_PIPELINE_STATE_DESC& desc) {
    pso_stats::LookupTimes times;
    if constexpr (kStats) times.start = pso_stats::Nanos();
    const auto name = PipelineName(desc);
    ID3D12PipelineState* pipeline = nullptr;
    if constexpr (kStats) times.lock_begin = pso_stats::Nanos();
    std::lock_guard lock(mutex_);
    if constexpr (kStats) times.locked = pso_stats::Nanos();
    if (root_ && desc.pRootSignature == root_) {
      auto entry = warmed_.find(name);
      if (entry != warmed_.end()) {
        pipeline = entry->second.Detach();
        warmed_.erase(entry);
        ++stats_.hits;
        if constexpr (kStats) pso_stats::OnLookup(pso_stats::Lookup::kWarm, times);
        return pipeline;
      }
    }
    if constexpr (kStats) times.load_begin = pso_stats::Nanos();
    const HRESULT loaded = library_->LoadGraphicsPipeline(name.c_str(), &desc, IID_PPV_ARGS(&pipeline));
    if constexpr (kStats) times.load_end = pso_stats::Nanos();
    if (SUCCEEDED(loaded)) {
      Record(name, desc);
      ++stats_.hits;
      if constexpr (kStats) pso_stats::OnLookup(pso_stats::Lookup::kLibrary, times);
      return pipeline;
    }
    ++stats_.misses;
    if constexpr (kStats) pso_stats::OnLookup(pso_stats::Lookup::kMiss, times);
    return nullptr;
  }

  // Plume calls store() on the thread that missed, right after it compiled.
  template <bool kStats>
  void StoreCompiled(const D3D12_GRAPHICS_PIPELINE_STATE_DESC& desc, ID3D12PipelineState* pipeline) {
    const uint64_t begin = kStats ? pso_stats::OnStore() : 0;
    const auto name = PipelineName(desc);
    {
      std::lock_guard lock(mutex_);
      Store(name, pipeline);
      Record(name, desc);
    }
    if constexpr (kStats) pso_stats::OnStored(begin);
  }

  template <bool kStats>
  bool Auxiliary(ID3D12Device* device, const D3D12_GRAPHICS_PIPELINE_STATE_DESC& desc,
                 const void* root_data, std::size_t root_size, ID3D12PipelineState** pipeline) {
    const auto name = L"aux-" + PipelineName(desc, root_data, root_size);
    std::lock_guard lock(mutex_);
    if (SUCCEEDED(library_->LoadGraphicsPipeline(name.c_str(), &desc, IID_PPV_ARGS(pipeline)))) {
      ++stats_.hits;
      if constexpr (kStats) pso_stats::OnAuxiliary(true, true, 0);
      return true;
    }
    ++stats_.misses;
    const uint64_t start = kStats ? pso_stats::Nanos() : 0;
    const bool compiled = SUCCEEDED(device->CreateGraphicsPipelineState(&desc, IID_PPV_ARGS(pipeline)));
    if constexpr (kStats) pso_stats::OnAuxiliary(false, compiled, pso_stats::Nanos() - start);
    if (!compiled) return false;
    Store(name, *pipeline);
    return true;
  }

  // One startup recipe: the driver library first, then a compile. Several may
  // run at once: the library and the device are free-threaded, and no two
  // concurrent calls share a name (ID3D12PipelineLibrary's one restriction).
  template <bool kStats>
  PreparedPipeline PrepareOne(const std::wstring& name, const D3D12_GRAPHICS_PIPELINE_STATE_DESC& desc) const {
    PreparedPipeline item;
    const uint64_t load_start = kStats ? pso_stats::Nanos() : 0;
    const HRESULT loaded = library_->LoadGraphicsPipeline(name.c_str(), &desc, IID_PPV_ARGS(&item.pipeline));
    if constexpr (kStats) item.load_ns = pso_stats::Nanos() - load_start;
    if (SUCCEEDED(loaded)) {
      item.result = PrepareResult::kLoaded;
      return item;
    }
    const uint64_t compile_start = kStats ? pso_stats::Nanos() : 0;
    const HRESULT compiled = device_->CreateGraphicsPipelineState(&desc, IID_PPV_ARGS(&item.pipeline));
    if constexpr (kStats) item.compile_ns = pso_stats::Nanos() - compile_start;
    if (SUCCEEDED(compiled))
      item.result = PrepareResult::kCompiled;
    else
      item.result = FAILED(device_->GetDeviceRemovedReason()) ? PrepareResult::kRemoved : PrepareResult::kFailed;
    return item;
  }

  // Prepare()'s loop over one source on `threads` threads
  // (LEGO_NATIVE_PSO_PREPARE_THREADS). Loads and compiles run on worker
  // threads; commit() runs on this thread in recipe order, so the library, the
  // resident set and the counts end up as the serial loop leaves them.
  template <class Progress, class Commit>
  bool PrepareParallel(const PipelineRecipes& source, unsigned threads, bool stats,
                       const std::unordered_set<std::wstring>& prepared, const Progress& progress,
                       const Commit& commit) const {
    const auto& entries = source.Entries();
    std::vector<std::size_t> pending;
    std::vector<std::wstring> names;
    std::unordered_set<std::wstring> seen;
    pending.reserve(entries.size());
    names.reserve(entries.size());
    for (std::size_t i = 0; i < entries.size(); ++i) {
      std::wstring name(entries[i]->name.begin(), entries[i]->name.end());
      // Names are unique within a source; never let two workers load one name.
      if (prepared.contains(name) || !seen.insert(name).second) continue;
      pending.push_back(i);
      names.push_back(std::move(name));
    }
    return RunOrdered<PreparedPipeline>(
        pending.size(), threads, kPrepareWindow,
        [&](std::size_t index) {
          std::vector<D3D12_INPUT_ELEMENT_DESC> inputs;
          const auto desc = source.Describe(*entries[pending[index]], root_, inputs);
          return stats ? PrepareOne<true>(names[index], desc) : PrepareOne<false>(names[index], desc);
        },
        [&](std::size_t index, PreparedPipeline&& item) {
          progress();
          return commit(names[index], std::move(item));
        });
  }

  std::vector<std::filesystem::path> SeedPaths() const {
    std::vector<std::filesystem::path> paths{seed_path_};
    auto directory = seed_path_;
    directory.replace_extension();
    std::error_code error;
    std::filesystem::directory_iterator iterator(directory, error);
    const std::filesystem::directory_iterator end;
    for (; !error && iterator != end; iterator.increment(error)) {
      std::error_code status_error;
      if (iterator->path().extension() == L".bin" && iterator->is_regular_file(status_error))
        paths.push_back(iterator->path());
    }
    if (error && error != std::errc::no_such_file_or_directory)
      REXLOG_WARN("Native GPU: could not enumerate startup seed directory {}: {}",
                  directory.string(), error.message());
    std::sort(paths.begin() + 1, paths.end());
    return paths;
  }

  bool ReadRecipes(const std::filesystem::path& path, PipelineRecipes& destination) {
    std::error_code error;
    const auto size = std::filesystem::file_size(path, error);
    if (error) return false;
    std::ifstream file(path, std::ios::binary);
    if (destination.Read(file, size)) return true;
    REXLOG_WARN("Native GPU: ignoring invalid or incompatible pipeline recipes {}", path.string());
    return false;
  }

  void Store(const std::wstring& name, ID3D12PipelineState* pipeline) {
    // The library may already have the name even when its load failed.
    if (SUCCEEDED(library_->StorePipeline(name.c_str(), pipeline))) {
      ++stats_.stored;
      ++unsaved_;
      last_store_ = Clock::now();
    }
  }

  void Record(const std::wstring& name, const D3D12_GRAPHICS_PIPELINE_STATE_DESC& desc) {
    if (root_ && desc.pRootSignature == root_ && !seed_names_.contains(name) &&
        recipes_.Record(name, desc)) {
      recipes_dirty_ = true;
      last_store_ = Clock::now();
    }
  }

  void SaveRecipes() {
    PipelineRecipes::Snapshot snapshot;
    {
      std::lock_guard lock(mutex_);
      if (!recipes_dirty_) return;
      snapshot = recipes_.TakeSnapshot();
      recipes_dirty_ = false;
    }
    std::error_code error;
    std::filesystem::create_directories(recipe_path_.parent_path(), error);
    auto temporary = recipe_path_;
    temporary += L"." + std::to_wstring(GetCurrentProcessId()) + L".tmp";
    std::ofstream file(temporary, std::ios::binary | std::ios::trunc);
    const bool written = snapshot.Write(file);
    file.close();
    if (written && file && MoveFileExW(temporary.c_str(), recipe_path_.c_str(),
                                       MOVEFILE_REPLACE_EXISTING)) {
      REXLOG_INFO("Native GPU: saved {} startup pipeline recipes", snapshot.recipes.size());
      return;
    }
    std::filesystem::remove(temporary, error);
    REXLOG_WARN("Native GPU: could not save startup pipeline recipes {}", recipe_path_.string());
    std::lock_guard lock(mutex_);
    recipes_dirty_ = true;
    last_store_ = Clock::now();
  }

  void Save() {
    SaveRecipes();
    const bool stats = pso_stats::Enabled();
    uint64_t saved = 0;
    // The buffer is allocated outside mutex_; only the size query and Serialize
    // run under it (see pipeline_snapshot.h). Same bytes, same file.
    auto snapshot = SnapshotPipelineLibrary(
        mutex_,
        [&]() -> std::size_t {
          if (!unsaved_) return 0;
          const SIZE_T size = library_->GetSerializedSize();
          // A library holding real pipelines is never this small; refuse to
          // overwrite a good file with one that did not actually keep them.
          if (size <= 1024 || size > kMaxLibraryBytes) {
            unsaved_ = 0;
            return 0;
          }
          return size;
        },
        [&](uint8_t* data, std::size_t size) {
          if (FAILED(library_->Serialize(data, size))) return false;
          saved = unsaved_;
          unsaved_ = 0;
          ++stats_.saves;
          return true;
        });
    if (stats)
      pso_stats::OnSaveSnapshot({uint64_t(snapshot.lock_us) * 1000, uint64_t(snapshot.max_lock_us) * 1000,
                                 uint64_t(snapshot.copy_us) * 1000, uint64_t(snapshot.alloc_us) * 1000,
                                 snapshot.retries, snapshot.allocated_under_lock});
    if (snapshot.status == PipelineSnapshot::Status::kNoMemory) {
      // The old resize threw std::bad_alloc on this detached thread. Retry
      // after the next quiet period instead.
      REXLOG_WARN("Native GPU: pipeline cache save postponed; {} bytes unavailable", snapshot.wanted);
      if (stats) pso_stats::OnSavePostponed();
      std::lock_guard lock(mutex_);
      last_store_ = Clock::now();
      return;
    }
    if (snapshot.status != PipelineSnapshot::Status::kCopied) return;
    const uint64_t write_start = stats ? pso_stats::Nanos() : 0;
    std::error_code error;
    std::filesystem::create_directories(path_.parent_path(), error);
    auto temporary = path_;
    temporary += L".tmp";
    {
      std::ofstream file(temporary, std::ios::binary | std::ios::trunc);
      if (!file.write(reinterpret_cast<const char*>(snapshot.data.get()), std::streamsize(snapshot.size))) {
        REXLOG_WARN("Native GPU: could not write pipeline cache {}", temporary.string());
        if (stats) pso_stats::OnSaveWritten(false, 0, pso_stats::Nanos() - write_start);
        return;
      }
    }
    std::filesystem::rename(temporary, path_, error);
    if (stats) pso_stats::OnSaveWritten(!error, snapshot.size, pso_stats::Nanos() - write_start);
    if (error)
      REXLOG_WARN("Native GPU: could not replace pipeline cache {}: {}", path_.string(), error.message());
    else
      REXLOG_INFO("Native GPU: pipeline cache saved, {} new pipelines, {} bytes", saved, snapshot.size);
  }

  std::filesystem::path path_;
  std::filesystem::path recipe_path_;
  std::filesystem::path seed_path_;
  ID3D12Device8* device_ = nullptr;
  ID3D12RootSignature* root_ = nullptr;
  PipelineRecipes recipes_;
  std::unordered_set<std::wstring> seed_names_;
  std::unordered_map<std::wstring, Microsoft::WRL::ComPtr<ID3D12PipelineState>> warmed_;
  bool recipes_dirty_ = false;
  std::vector<uint8_t> blob_;  // must outlive library_
  ID3D12PipelineLibrary* library_ = nullptr;
  std::mutex mutex_;
  PipelineLibraryStats stats_;
  uint64_t unsaved_ = 0;
  Clock::time_point last_store_{};
  std::atomic<bool> saving_{false};
};

PipelineLibrary* g_library = nullptr;

// Stands in for the library while PSO stats are on and there is none
// (LEGO_NATIVE_PSO_CACHE=0, a capture layer, or CreatePipelineLibrary failed),
// so lookups and compiles are still counted for cache on/off comparisons.
// Plume reads the registered pointer without a lock, so it is never deleted.
class CountingPipelineCache final : public plume::D3D12GraphicsPipelineCache {
 public:
  ID3D12PipelineState* load(const D3D12_GRAPHICS_PIPELINE_STATE_DESC&) override {
    pso_stats::OnUncachedLookup();
    return nullptr;
  }
  void store(const D3D12_GRAPHICS_PIPELINE_STATE_DESC&, ID3D12PipelineState*) override {
    pso_stats::OnStored(pso_stats::OnStore());
  }
};

std::atomic<bool> g_counting_cache{false};

void StartCountingCache(pso_stats::CacheState state) {
  pso_stats::OnCacheState(state);
  static auto* const cache = new CountingPipelineCache();
  g_counting_cache.store(true);
  plume::SetD3D12GraphicsPipelineCache(cache);
}

}  // namespace

void StartPipelineLibrary(plume::RenderDevice* render_device) {
  // LEGO_NATIVE_PSO_STATS; nothing else changes while it is off.
  const bool stats = pso_stats::ReadEnvironment();
  if (stats) pso_stats::Configure(CachePath().parent_path());
  const char* value = std::getenv("LEGO_NATIVE_PSO_CACHE");
  if (value && std::strcmp(value, "0") == 0) {
    REXLOG_INFO("Native GPU: pipeline cache disabled by LEGO_NATIVE_PSO_CACHE=0");
    if (stats) StartCountingCache(pso_stats::CacheState::kDisabled);
    return;
  }
  // Capture layers (RenderDoc) wrap the device and do not persist pipeline
  // libraries: stores "succeed" but serialize to an empty blob, which would
  // replace the real cache on disk. Leave the cache untouched in those runs.
  if (GetModuleHandleW(L"renderdoc.dll") || std::getenv("LEGO_NATIVE_RENDERDOC_DLL")) {
    REXLOG_INFO("Native GPU: pipeline cache skipped while a capture layer is active");
    if (stats) StartCountingCache(pso_stats::CacheState::kCaptureLayer);
    return;
  }
  if (!render_device || g_library) return;
  auto* device = static_cast<plume::D3D12Device*>(render_device)->d3d;
  if (!device) return;
  auto* library = new PipelineLibrary();
  if (!library->Open(device)) {
    delete library;
    if (stats) StartCountingCache(pso_stats::CacheState::kUnavailable);
    return;
  }
  g_library = library;
  plume::SetD3D12GraphicsPipelineCache(library);
}

void PipelineLibraryFrame() {
  if (pso_stats::Enabled()) pso_stats::OnFrame();
  if (g_library) g_library->Frame();
}

void PreparePipelineLibrary(plume::RenderPipelineLayout* layout) {
  if (g_library && layout)
    g_library->Prepare(static_cast<plume::D3D12PipelineLayout*>(layout)->rootSignature);
}

bool StartupPipelinePreparationEnabled() {
  const char* enabled = std::getenv("LEGO_NATIVE_PSO_PRECOMPILE");
  return !enabled || std::strcmp(enabled, "0") != 0;
}

bool CreateAuxiliaryPipeline(ID3D12Device* device,
    const D3D12_GRAPHICS_PIPELINE_STATE_DESC& desc, const void* root_data,
    std::size_t root_size, ID3D12PipelineState** pipeline) {
  if (g_library) return g_library->CreateAuxiliary(device, desc, root_data, root_size, pipeline);
  return CreateUncached(device, desc, pipeline);
}

void StopPipelineLibrary() {
  if (!g_library) {
    // The counting stand-in is unregistered but, like the library, never deleted.
    if (g_counting_cache.exchange(false)) plume::SetD3D12GraphicsPipelineCache(nullptr);
    if (pso_stats::Enabled()) pso_stats::LogExitSummary();
    return;
  }
  plume::SetD3D12GraphicsPipelineCache(nullptr);
  g_library->Stop();
  g_library = nullptr;
  // Intentionally leaked: a detached save thread can no longer start, but
  // keeping the object avoids any use-after-free during hard exits.
  if (pso_stats::Enabled()) pso_stats::LogExitSummary();
}

PipelineLibraryStats GetPipelineLibraryStats() {
  return g_library ? g_library->Stats() : PipelineLibraryStats{};
}

void LogPipelineStats() {
  if (pso_stats::Enabled()) pso_stats::LogSummary("request");
}

}  // namespace legodimensions::gpu_native

# Line-citation check for build/agent9/s4-t1-preread.md (Agent 9, #18). Read-only.
# Run from the workspace root: powershell -NoProfile -File build\agent9\s4-t1-preread-cites.ps1
if (Test-Path perf-notes\WINDOW-HOLD.txt) { 'HOLD PRESENT - STOP'; exit 3 }
$F = @{
  nw = 'build\agent7\s4-t1\after\src\gpu_native\native_worker.cpp'
  nr = 'build\agent7\s4-t1\after\src\gpu_native\native_recording.cpp'
  np = 'build\agent7\s4-t1\after\src\gpu_native\native_preparation.h'
  dev = 'DimensionsRecomp\rexlego\src\gpu_native\device.cpp'
  rec = 'DimensionsRecomp\rexlego\src\gpu_native\pipeline_recipes.h'
  lib = 'DimensionsRecomp\rexlego\src\gpu_native\pipeline_library.cpp'
  arc = 'DimensionsRecomp\rexlego\src\gpu_native\shader_archive.cpp'
  sha = 'DimensionsRecomp\rexlego\src\gpu_native\shaders.cpp'
  ld = 'build\agent10\bgate\logdiff.py'
  cms = 'build\agent2\snap1\DimensionsRecomp\rexlego\CMakeLists.txt'
  cml = 'DimensionsRecomp\rexlego\CMakeLists.txt'
  rr = 'build\agent7\s4-t1\RATE-REQUEST.md'
  dr = 'build\agent7\s4-t1\check\DIFF-REVIEW.md'
  fr = 'build\agent7\s4-t1\FUNCTIONAL-ROWS.md'
  mx = 'build\agent7\s4-t1\matrix-s4t1-f1.json'
}
$C = @(
  'nw|6|native_preparation.h', 'nw|155|SetThreadDescription', 'nw|156|ApplyNativeChainPriority("recorder")',
  'nw|160|g_queue_mutex', 'nw|161|g_record_ready.wait', 'nw|201|SetThreadDescription',
  'nw|202|ApplyNativeChainPriority("coordinator")', 'nw|205|g_queue_mutex', 'nw|206|g_queue_ready.wait',
  'nw|263|CoordinatorMain(); return;', 'nw|264|SetThreadDescription', 'nw|265|ApplyNativeChainPriority("worker")',
  'nw|268|g_queue_mutex', 'nw|269|g_queue_ready.wait', 'nw|274|NativeRecordingMutex',
  'nw|324|static const bool enabled', 'nw|329|}();', 'nw|335|Any other value', 'nw|337|ApplyNativeChainPriorityImpl',
  'nw|338|static const unsigned mode', 'nw|339|getenv("LEGO_NATIVE_CHAIN_PRIORITY")', 'nw|340|if (!value) return 0u;',
  'nw|343|REXLOG_INFO', 'nw|345|}();', 'nw|346|if (mode == 0) return;', 'nw|347|GetCurrentThread()',
  'nw|348|SetThreadPriority(self', 'nw|350|if (mode & 2u)', 'nw|355|SetThreadInformation', 'nw|357|std::atomic<unsigned> logged',
  'nw|358|fetch_add', 'nw|360|GetThreadPriority', 'nw|365|g_native_chain_priority_installed', 'nw|368|}();',
  'nw|380|if (!NativeWorkerEnabled()) return;', 'nw|381|std::once_flag once', 'nw|384|std::lock_guard lock(g_queue_mutex)',
  'nw|386|}', 'nw|387|std::thread(RecorderMain)', 'nw|388|std::thread(WorkerMain)',
  'nw|390|SetThreadPriority(g_thread.native_handle()', 'nw|392|});', 'nw|417|g_queue_progress.wait',
  'nw|637|g_thread.join()', 'nw|638|g_recorder_thread.join()', 'nw|639|StopNativePreparation()',
  'nr|2|native_preparation.h', 'nr|112|SetThreadDescription', 'nr|113|ApplyNativeChainPriority("recording queue")',
  'nr|117|std::unique_lock lock(mutex_)', 'nr|118|ready_.wait', 'nr|140|~RecordingQueue()', 'nr|143|worker_.join()',
  'nr|144|}', 'nr|152|progress_.wait', 'nr|169|progress_.wait', 'nr|174|RecordingQueueInstance()', 'nr|181|}',
  'nr|257|RecordingQueueInstance()', 'nr|498|NativeFullDrawPreparationEnabled', 'nr|504|}', 'nr|510|PreparationQueueInstance',
  'nr|511|static NativePreparationQueue queue', 'nr|513|}', 'nr|514|StopNativePreparation', 'nr|522|NativePreparationWorkerCount',
  'nr|528|}', 'nr|531|NativeFullDrawPreparationEnabled()) return commands;',
  'np|15|S4-T1 (#21)', 'np|18|inline void (*g_native_chain_priority)', 'np|19|inline void ApplyNativeChainPriority',
  'np|21|}', 'np|22|', 'np|33|Native GPU prepare', 'np|34|SetThreadDescription', 'np|35|ApplyNativeChainPriority("prepare")',
  'np|36|for (;;)', 'np|39|std::unique_lock lock(mutex_)', 'np|40|ready_.wait', 'np|46|}', 'np|48|void Stop()',
  'np|51|worker.join()', 'np|52|}', 'np|58|~NativePreparationQueue()', 'np|59|void Shutdown()',
  'np|60|Runs inline when the queue is full',
  'dev|903|Native GPU [{}]', 'dev|906|getTextureCount', 'rec|247|PipelineRecipes::Read', 'rec|254|memcmp(fingerprint',
  'rec|256|return false;', 'lib|99|CachePath()', 'lib|104|"native-pso.bin"', 'lib|105|}', 'lib|150|CachePath()',
  'lib|151|native-pso-recipes.bin', 'lib|152|native-pso-seed.bin', 'lib|502|ReadRecipes', 'lib|508|ignoring invalid or incompatible pipeline recipes',
  'lib|510|}', 'arc|152|string_view', 'arc|158|provenance mismatch', 'sha|601|PollPrecompiledShaders',
  'sha|604|LEGO_NATIVE_SHADER_PACK', 'sha|605|LEGO_NATIVE_SHADER_PACK_TRIGGER', 'sha|608|paths.second.empty()',
  'ld|38|[0-9A-Fa-f]{8,}',
  'cms|61|if(LEGODIMENSIONS_NATIVE_GPU)', 'cms|62|if(NOT WIN32)', 'cms|63|D3D12', 'cms|108|native_worker.cpp',
  'cms|109|native_recording.cpp', 'cms|753|GLOB_RECURSE', 'cms|754|gpu_native/*.h', 'cms|780|native_worker.cpp',
  'cms|781|native_recording.cpp', 'cms|798|SUBSTRING', 'cms|802|LEGO Dimensions native GPU',
  'cml|108|native_worker.cpp', 'cml|109|native_recording.cpp', 'cml|731|GLOB_RECURSE', 'cml|758|native_worker.cpp',
  'cml|759|native_recording.cpp', 'cml|776|SUBSTRING', 'cml|780|LEGO Dimensions native GPU',
  'rr|86|native_preparation.h:14-21', 'rr|147|Runtime proof', 'rr|209|PROOF 6', 'rr|216|Fingerprint', 'rr|217|re-pinned',
  'rr|236|EcoQoS opt-out', 'rr|237|host_execution_throttling_optout', 'rr|238|default (false)',
  'dr|79|after :383', 'dr|83|:383', 'dr|135|Check 2', 'dr|139|magic-static',
  'fr|40|:260', 'fr|42|173-178', 'fr|100|thread lines are exactly', 'fr|103|at most 16 thread lines', 'fr|160|(:596)',
  'mx|27|native_worker.cpp:349', 'mx|108|:260'
)
$cache = @{}; $bad = 0; $n = 0
foreach ($c in $C) {
  $alias, $line, $want = $c.Split('|', 3); $n++
  if (-not $cache.ContainsKey($alias)) { $cache[$alias] = @(Get-Content -LiteralPath $F[$alias]) }
  $text = if ([int]$line -le $cache[$alias].Count) { $cache[$alias][[int]$line - 1] } else { $null }
  $ok = if ($want -eq '') { $text -ne $null -and $text.Trim() -eq '' } else { $text -ne $null -and $text.Contains($want) }
  if (-not $ok) { $bad++; 'BAD  {0}:{1} want [{2}] got [{3}]' -f $alias, $line, $want, $text }
}
'{0} citations checked, {1} bad' -f $n, $bad
if ($bad) { exit 1 } else { exit 0 }

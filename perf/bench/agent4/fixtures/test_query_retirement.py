"""Execute native query generation/release/readback bodies with fake GPU fences."""
import argparse
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('output', type=Path)
p.add_argument('--compiler', default='clang++')
# Patched copy: the DimensionsRecomp tree is an argument so baseline and dev run the same fixture.
p.add_argument('--tree', type=Path, default=Path(__file__).resolve().parents[3] / 'DimensionsRecomp')
a = p.parse_args()
root = a.tree.resolve()
a.output.mkdir(parents=True, exist_ok=True)

def body(path, signature):
    text = (root / path).read_text()
    start = text.index(signature)
    end = text.index('{', start) + 1
    depth = 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]

query_path = 'rexlego/src/gpu_native/queries.cpp'
functions = '\n'.join(body(query_path, sig) for sig in
                      ['u32 IssueQuery(', 'u32 IssueQueryQueued(', 'u32 GetQueryData(', 'u32 ReleaseQuery(',
                       'void ResetQueryResources('])
assert 'Synchronize' not in functions
# Trees with the active-entry counter (dev) also check it after every step.
counts_active = 'active_queries' in functions
retire = body('rexlego/src/gpu_native/device.cpp', 'void HostDevice::RetireResource(')
harness = r'''
#include <algorithm>
#include <array>
#include <atomic>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <functional>
#include <memory>
#include <mutex>
#include <unordered_map>
#include <utility>
#include <vector>
using u32=uint32_t;using u64=uint64_t;using be_u32=u32;
#define REXLOG_INFO(...) ((void)0)
#define FAILED(x) ((x)!=0)
#define SUCCEEDED(x) ((x)==0)
#define IID_PPV_ARGS(x) (x)
constexpr int D3D12_FENCE_FLAG_NONE=0;
constexpr u32 kInvalid=0x8876086C,kUnsupported=0x80004001,kFailure=0x80004005;
template<class T>struct ComPtr {
 std::shared_ptr<T> p;
 T* Get()const{return p.get();} T* operator->()const{return p.get();}
 ComPtr* operator&(){return this;}
 void Reset(){p.reset();}
};
struct ID3D12Fence {u64 completed=0;u64 GetCompletedValue(){return completed;}};
struct D3D12_RANGE {size_t Begin,End;};
struct Readback {
 u64 value=0;bool fail=false;
 int Map(int,const D3D12_RANGE* r,void** out){assert(r->End==8);*out=&value;return fail?1:0;}
 void Unmap(int,const D3D12_RANGE* r){assert(r->End==0);}
};
struct Samples {std::shared_ptr<Readback> readback=std::make_shared<Readback>();};
// As queries.cpp: cached sum, and each draw's samples with its guest-resolution scale.
struct Query {
 bool active=false,ended=false,failed=false;
 bool summed=false;u32 sum=0;
 std::vector<std::pair<std::shared_ptr<Samples>,double>> draws;
 ComPtr<ID3D12Fence> completion;
 u64 completion_value=0;
};
// std::mutex with a one-shot step run before a chosen acquisition: interleaves another thread's call.
struct QueryMutex {
 std::mutex m;std::function<void()> before;unsigned skip=0;
 void lock(){if(before&&!skip--){auto step=std::move(before);before=nullptr;step();}m.lock();}
 void unlock(){m.unlock();}
};
QueryMutex mutex;std::mutex g_mutex;
std::unordered_map<u32,std::shared_ptr<Query>> queries;
// Real (dev tree): entries of `queries` with `active` set.
std::atomic<size_t> active_queries{0};constexpr bool kCountsActive=COUNTS_ACTIVE;
std::unordered_map<u32,unsigned> pending_issues;
std::vector<std::shared_ptr<Samples>> sample_pool;ComPtr<ID3D12Fence> query_completion;
bool full_mode=true, queue_mode=false;
bool NativeFullDrawPreparationEnabled(){return full_mode;}
bool NativeWorkerShouldQueue(){return queue_mode;}
// Queued tasks run inline here, as on the recorder thread: retires take the direct path.
bool NativeWorkerStarted(){return false;}
enum class NativeTaskStage : unsigned char { kDeferred, kRecorder, kRecorderBarrier };
std::vector<std::function<void()>> queued;std::vector<NativeTaskStage> stages;
void NativeWorkerSubmit(std::function<void()> task,bool=false,bool=false,bool=false,
                        NativeTaskStage stage=NativeTaskStage::kDeferred){queued.push_back(std::move(task));stages.push_back(stage);}
struct Preparation { std::vector<std::shared_ptr<void>> retired; };
Preparation* t_draw_preparation=nullptr;
std::atomic<u32> diagnostics{100};
u64 query_completion_value=0;
std::array<u32,256> header{};
be_u32* Header(u32 a){return header.data()+a;}
u32 Unsupported(const char*,u32){return kUnsupported;}
void TraceQueryValue(u32,size_t,u64){}
struct Memory {int frees=0;void SystemHeapFree(u32 a){assert(a==1);++frees;}} memory;
#define REX_KERNEL_MEMORY() (&memory)
struct DeviceImpl {
 bool fail=false;
 int CreateFence(int,int,ComPtr<ID3D12Fence>* out){if(fail)return 1;out->p=std::make_shared<ID3D12Fence>();return 0;}
};
struct QueueImpl {bool fail=false;u64 last=0;int Signal(ID3D12Fence* f,u64 value){assert(f&&value>last);last=value;return fail?1:0;}};
namespace plume {struct D3D12Device {DeviceImpl* d3d;};struct D3D12CommandQueue {QueueImpl* d3d;};}
DeviceImpl device_impl;QueueImpl queue_impl;
plume::D3D12Device device{&device_impl};plume::D3D12CommandQueue queue{&queue_impl};
struct State {
 static constexpr u32 kFramesInFlight=3;u32 command_slot_count=kFramesInFlight;
 std::array<bool,3> frame_submitted{true,false,false};
 bool command_list_open=true;u32 frame_slot=1;
 std::array<std::vector<std::shared_ptr<void>>,3> retired_resources;
};
std::unique_ptr<State> g_state=std::make_unique<State>();
using NativeRecordingGate=std::recursive_mutex;  // Recursive like the real gate.
struct HostDevice {
 static inline NativeRecordingGate recording;
 static inline bool submit_ok=true;
 static auto LockRecording(){return std::unique_lock(recording);}
 static auto Device(){return &device;} static auto Queue(){return &queue;}
 static bool SubmitRecordedWork(){return submit_ok;}
 static void RetireResource(std::shared_ptr<void>);
};
auto& NativeRecordingMutex(){return HostDevice::recording;}
'''.replace('COUNTS_ACTIVE', 'true' if counts_active else 'false')
tests = r'''
std::shared_ptr<Samples> sample(u64 value){auto s=std::make_shared<Samples>();s->readback->value=value;return s;}
std::pair<std::shared_ptr<Samples>,double> drawn(u64 value){return {sample(value),1.0};}
void empty_slots(){for(auto& s:g_state->retired_resources)s.clear();}
void check_active(){if(!kCountsActive)return;size_t n=0;for(const auto& [address,query]:queries)n+=query->active;assert(active_queries==n);}
int main(){
 auto initial=std::make_shared<Query>();initial->completion.p=std::make_shared<ID3D12Fence>();
 initial->draws.push_back(drawn(999));initial->ended=true;
 std::weak_ptr<Query> old=initial;queries[1]=initial;initial.reset();Header(1)[3]=1;
 assert(IssueQuery(1,2)==0);auto current=queries[1];check_active();
 assert(current->active&&current->draws.empty()&&!current->ended&&!current->failed);
 assert(!old.expired()); // Previous submission and open list each hold it.
 g_state->retired_resources[0].clear();assert(!old.expired());
 g_state->retired_resources[1].clear();assert(old.expired());
 assert(IssueQuery(1,2)==kInvalid);check_active(); // Active generation cannot be restarted.
 current->draws={drawn(7),drawn(5)};
 assert(IssueQuery(1,1)==0);assert(!current->active&&current->ended);check_active();
 assert(GetQueryData(1,100,4,0)==1); // Never invent a ready result.
 current->completion->completed=1;assert(GetQueryData(1,100,4,0)==0&&*Header(100)==12);
 current->completion->completed=UINT64_MAX;assert(GetQueryData(1,100,4,0)==kFailure);
 current->completion->completed=1;
 assert(GetQueryData(1,100,8,0)==kUnsupported);
 // The sum is cached once read; clear the cache to make the failing readback a first read.
 current->draws[0].first->readback->fail=true;assert(GetQueryData(1,100,4,0)==0&&*Header(100)==12);
 current->summed=false;assert(GetQueryData(1,100,4,0)==kFailure);
 current->draws[0].first->readback->fail=false;
 current->draws={drawn(UINT32_MAX),drawn(5)};
 assert(GetQueryData(1,100,4,0)==0&&*Header(100)==UINT32_MAX);
 assert(current->completion_value==1);
 std::weak_ptr<Query> ended=current;current.reset();
 assert(IssueQuery(1,2)==0);check_active();assert(!ended.expired());empty_slots();assert(ended.expired());
 // A new generation shares the fence but cannot inherit an old ready value.
 current=queries[1];assert(current->completion->completed==1);
 assert(IssueQuery(1,1)==0&&current->completion_value==2);check_active();
 assert(GetQueryData(1,100,4,0)==1);
 current->completion->completed=2;assert(GetQueryData(1,100,4,0)==0);
 current.reset();assert(IssueQuery(1,2)==0);check_active();empty_slots();
 auto active=queries[1];active->draws={drawn(19)};std::weak_ptr<Query> releasing=active;
 Header(1)[3]=2;assert(ReleaseQuery(1)==1&&queries.contains(1)&&active->active&&memory.frees==0);check_active();
 active.reset();assert(ReleaseQuery(1)==0);check_active(); // Release before END is safe.
 assert(!queries.contains(1)&&memory.frees==1&&!releasing.expired());
 assert(GetQueryData(1,100,4,0)==kInvalid&&ReleaseQuery(1)==0&&memory.frees==1);
 g_state->retired_resources[0].clear();assert(!releasing.expired());
 g_state->retired_resources[1].clear();assert(releasing.expired());
 // No pending work needs retention. Same guest address may be reused.
 g_state->frame_submitted.fill(false);g_state->command_list_open=false;
 auto next=std::make_shared<Query>();queries[1]=next;Header(1)[3]=1;
 next->active=true;++active_queries;next->completion.p=std::make_shared<ID3D12Fence>(); // Counted as BEGIN does.
 queue_impl.fail=true;assert(IssueQuery(1,1)==kFailure&&next->failed);check_active();
 assert(GetQueryData(1,100,4,0)==kFailure);
 std::weak_ptr<Query> done=next;next.reset();assert(ReleaseQuery(1)==0&&done.expired());check_active();
 queue_impl.fail=false;queue_mode=true;
 auto ready=std::make_shared<Query>();ready->completion.p=std::make_shared<ID3D12Fence>();
 ready->completion->completed=query_completion_value;ready->completion_value=query_completion_value;
 ready->ended=true;ready->draws={drawn(123)};queries[1]=ready;
 *Header(100)=456;
 assert(IssueQueryQueued(1,2)==0 && pending_issues[1]==1);
 assert(GetQueryData(1,100,4,0)==1 && *Header(100)==456);
 assert(IssueQueryQueued(1,1)==0 && pending_issues[1]==2);
 // Full preparation: queued BEGIN and END each hold later batches until applied.
 assert((stages==std::vector{NativeTaskStage::kRecorderBarrier,NativeTaskStage::kRecorderBarrier}));
 queued[0]();assert(pending_issues[1]==1);check_active();
 assert(GetQueryData(1,100,4,0)==1);
 queued[1]();assert(!pending_issues.contains(1));check_active();
 assert(GetQueryData(1,100,4,0)==1);
 queries[1]->completion->completed=queries[1]->completion_value;
 assert(GetQueryData(1,100,4,0)==0 && *Header(100)==0);
 // END racing the final Release (full preparation + queue: Release skips the recording lock).
 assert(IssueQuery(1,2)==0);auto racing=queries[1];check_active();
 const int frees=memory.frees;Header(1)[3]=1;
 mutex.skip=1;mutex.before=[]{assert(ReleaseQuery(1)==0);check_active();};
 assert(IssueQuery(1,1)==kInvalid&&!racing->active&&!racing->ended&&!queries.contains(1));
 assert(memory.frees==frees+1);check_active();
 // END racing ResetQueryResources: the dropped generation is not uncounted again.
 auto created=std::make_shared<Query>();created->completion.p=std::make_shared<ID3D12Fence>();
 queries[1]=created;created.reset();
 assert(IssueQuery(1,2)==0);racing=queries[1];check_active();
 // Reset restarts fence numbering.
 mutex.skip=1;mutex.before=[]{ResetQueryResources();queue_impl.last=0;check_active();};
 assert(IssueQuery(1,1)==0&&!racing->active&&racing->ended&&racing->completion_value==1);
 assert(queries.empty()&&memory.frees==frees+2);check_active();
 if(kCountsActive)assert(active_queries==0);
}
'''
source = a.output / 'query-retirement.cpp'
source.write_text(harness + retire + '\n' + functions + '\n' + tests)
exe = a.output / 'query-retirement-test.exe'
subprocess.run([a.compiler, '-std=c++20', '-DNOMINMAX', str(source), '-o', str(exe)], check=True, timeout=45)
subprocess.run([str(exe.resolve())], check=True, timeout=45)
report = {'passed': True, 'tree': str(root), 'counts_active': counts_active,
          'actual_native_functions': ['IssueQuery','IssueQueryQueued','GetQueryData','ReleaseQuery',
                                      'ResetQueryResources','HostDevice::RetireResource'],
          'checks': ['no query drain', 'fresh generations', 'retain at every submitted/open slot',
                     'release before END', 'guest header reuse', 'nonfinal refcount', 'fence readiness',
                     'no fabricated result', 'removal failure', 'readback failure', 'cached sum', 'saturating sum',
                     'shared monotonic fence generations', 'signal failures', 'queued BEGIN/END recorder barriers',
                     'END racing final release', 'END racing reset'] +
                    (['active entry count after every BEGIN/END/release/reset'] if counts_active else []),
          'real_GPU_gameplay_not_proven': True}
(a.output / 'verification.json').write_text(json.dumps(report, indent=2))
print('PASS: native query generations, fence-gated results and all-live-slot retirement.')

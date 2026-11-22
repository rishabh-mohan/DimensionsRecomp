#pragma once

// Ordered parallel map for startup pipeline preparation (task #5, item 3).
//
// RunOrdered<Result>(count, threads, window, work, commit) calls work(i) for
// every i in [0, count) on up to `threads` worker threads, and commit(i,
// Result&&) on the calling thread in index order. Everything commit() touches
// therefore sees exactly the serial sequence. Workers run at most `window`
// indices ahead of the last commit, which bounds the results held at once.
// When commit() returns false, no new work starts, results still in flight are
// discarded, and RunOrdered returns false after joining the workers.
// With threads <= 1, count <= 1, or no thread able to start, it is the plain
// serial loop: work(0), commit(0), work(1), commit(1), ...
//
// work() runs concurrently with itself and with commit(), so it may only touch
// thread-safe state. If work() throws, no new work starts and the exception is
// rethrown on the calling thread once the workers have joined. Results already
// committed stay committed.

#include <algorithm>
#include <condition_variable>
#include <cstddef>
#include <exception>
#include <mutex>
#include <optional>
#include <system_error>
#include <thread>
#include <utility>
#include <vector>

namespace legodimensions::gpu_native {

template <class Result, class Work, class Commit>
bool RunOrdered(std::size_t count, unsigned threads, std::size_t window, Work&& work, Commit&& commit) {
  const auto serial = [&] {
    for (std::size_t i = 0; i < count; ++i)
      if (!commit(i, work(i))) return false;
    return true;
  };
  if (threads <= 1 || count <= 1) return serial();
  threads = unsigned(std::min<std::size_t>(threads, count));
  window = std::max<std::size_t>(window, threads);

  std::mutex mutex;
  std::condition_variable ready;  // a result arrived, or a worker failed
  std::condition_variable room;   // the window moved, or the run stopped
  std::vector<std::optional<Result>> results(count);
  std::size_t next = 0, committed = 0;
  bool stop = false;
  std::exception_ptr error;

  const auto worker = [&] {
    for (;;) {
      std::size_t index;
      {
        std::unique_lock lock(mutex);
        room.wait(lock, [&] { return stop || next >= count || next < committed + window; });
        if (stop || next >= count) return;
        index = next++;
      }
      std::optional<Result> result;
      std::exception_ptr failure;
      try {
        result.emplace(work(index));
      } catch (...) {
        failure = std::current_exception();
      }
      {
        std::lock_guard lock(mutex);
        if (failure) {
          if (!error) error = failure;
          stop = true;
        } else if (!stop) {
          results[index] = std::move(result);
        }
      }
      ready.notify_one();
      if (failure) {
        room.notify_all();
        return;
      }
    }
  };

  std::vector<std::thread> pool;
  pool.reserve(threads);
  try {
    for (unsigned i = 0; i < threads; ++i) pool.emplace_back(worker);
  } catch (const std::system_error&) {
    // Fewer workers than asked for; the ones running still cover every index.
  }
  if (pool.empty()) return serial();

  const auto finish = [&] {
    {
      std::lock_guard lock(mutex);
      stop = true;
    }
    room.notify_all();
    for (auto& thread : pool)
      if (thread.joinable()) thread.join();
  };
  // Joins the workers if commit() throws.
  struct Finisher {
    const decltype(finish)& run;
    ~Finisher() { run(); }
  } finisher{finish};

  bool complete = true;
  for (std::size_t i = 0; i < count; ++i) {
    std::optional<Result> result;
    {
      std::unique_lock lock(mutex);
      ready.wait(lock, [&] { return results[i].has_value() || error != nullptr; });
      if (!results[i]) break;  // a worker failed before producing index i
      result = std::move(results[i]);
      results[i].reset();
    }
    if (!commit(i, std::move(*result))) {
      complete = false;
      break;
    }
    {
      std::lock_guard lock(mutex);
      committed = i + 1;
    }
    room.notify_all();
  }
  finish();
  if (error) std::rethrow_exception(error);
  return complete;
}

}  // namespace legodimensions::gpu_native

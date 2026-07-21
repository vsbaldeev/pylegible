---
name: python-concurrency
description: >
  Use when writing concurrent or parallel Python — choosing between threads, asyncio, and
  processes, using concurrent.futures executors, offloading blocking I/O, guarding shared
  state against races, cancelling or timing out work, or reasoning about the GIL and
  free-threaded builds. For async dunder protocols use python-data-model; for testing async
  code use python-testing.
---

# Python Concurrency

## Overview

Concurrency buys throughput, not a faster single operation — and it buys it with races,
deadlocks, and harder debugging. Reach for it only when a profiler shows a bottleneck you
can actually overlap. Then pick the model that fits the workload, prefer high-level
executors over hand-rolled threads and processes, and never share mutable state without
protecting it. Depth in `reference.md`.

## When to use

- Overlapping I/O-bound work (network, disk) to cut total wall-clock time.
- Spreading CPU-bound work across cores.
- Deciding between `asyncio`, threads, and processes for a bottleneck you have measured.

## Pick a model

| Workload | Use | Why |
|---|---|---|
| I/O-bound, many waits | `asyncio` (`async`/`await`) | one thread parks thousands of waits, no lock overhead |
| I/O-bound, blocking libraries | `ThreadPoolExecutor` | threads release the GIL while blocked on I/O |
| CPU-bound | `ProcessPoolExecutor` | sidesteps the GIL — real parallelism across cores |

The GIL lets only one thread run Python bytecode at a time, so threads speed up *waiting*,
not *computing*. For computing, use processes (or a free-threaded build — see `reference.md`).

## Core rules

- **Profile first.** Concurrency adds bugs and complexity; add it only for a measured win.
- Prefer `concurrent.futures` executors over raw `threading.Thread` / `multiprocessing.Process` —
  they handle pooling, results, and exception propagation for you.
- Never share mutable state across threads without a `Lock`; better, pass immutable inputs
  and return results instead of mutating shared objects.
- Bound every wait: pass `timeout=`, make work cancellable — one hung task must not hang the
  program.
- asyncio: one `asyncio.run()` entry point; group concurrent work with `asyncio.TaskGroup`
  (3.11+); never call blocking code in a coroutine — offload it with `asyncio.to_thread`.
- Processes: keep worker entry points import-safe (guard with `if __name__ == "__main__":`);
  on 3.14 the default start method is `forkserver`, so module import must have no side effects.

## Example

```python
logger = logging.getLogger(__name__)

def fetch_all(urls: list[str], client: HttpClient) -> dict[str, bytes]:
    """Fetch every URL concurrently, returning {url: body} for the ones that succeed."""
    results: dict[str, bytes] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        future_to_url = {pool.submit(client.get, url): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results[url] = future.result(timeout=30)
            except HttpError:
                logger.exception("fetch failed for %s", url)   # one failure, not all
    return results
```

## Common mistakes

- Adding concurrency before profiling — more complexity, no measured gain.
- Blocking the event loop: calling `requests.get` or `time.sleep` inside a coroutine. Use the
  async client, or `asyncio.to_thread` for unavoidable blocking calls.
- Sharing a mutable `dict`/`list` across threads with no lock — races and lost updates.
- Fire-and-forget tasks: creating a task and never awaiting it, so its exception vanishes.
  Use `TaskGroup`, which awaits and surfaces failures.
- Using processes for I/O-bound work — pickling and process startup cost for no benefit.
- Never calling `future.result()`, silently swallowing every worker exception.

## Boundary

This skill owns choosing and using a concurrency model — threads, asyncio, processes,
executors, and the GIL. Writing async **protocol** methods (`__aiter__`, `__anext__`,
`__aenter__`, `__aexit__`) → **python-data-model**. Testing async or concurrent code
(`pytest.mark.asyncio`, `AsyncMock`) → **python-testing**. Exception handling and general
idioms → **python-patterns**. See `reference.md` for threads/processes/asyncio depth,
shared-state discipline, and the free-threading (PEP 779) & subinterpreters (PEP 734) sidebar.

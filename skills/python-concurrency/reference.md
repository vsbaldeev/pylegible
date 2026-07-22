# Python Concurrency — Reference

The catalog behind `SKILL.md`: how each model works, how to keep shared state safe, and
where the language is heading (free threading, subinterpreters). All examples obey the
project `CLAUDE.md` — specific exceptions, `logging` over `print`, no single-letter names.

## Choosing a model

| Signal | Model | Notes |
|---|---|---|
| Mostly waiting on network/disk, and you control the code as `async` | `asyncio` | Highest concurrency per thread; needs async-aware libraries end to end. |
| Waiting on blocking libraries you cannot make async | `ThreadPoolExecutor` | Threads release the GIL during I/O; simplest retrofit. |
| Heavy computation | `ProcessPoolExecutor` | True parallelism; pays pickling + process-startup cost. |
| Heavy computation, in-process isolation | `InterpreterPoolExecutor` (3.14+) | Subinterpreters — cheaper to start than processes; still serializes what crosses between them. |

Rule of thumb: **threads and asyncio for waiting, processes for computing.** Don't mix
models without a reason — one executor type per bottleneck keeps the failure modes small.

## Threads and `ThreadPoolExecutor`

Prefer the executor to raw `Thread`: it pools workers, returns `Future`s, and re-raises
worker exceptions when you call `result()`.

```python
def totals_by_report(report_ids: list[int], store: ReportStore) -> dict[int, int]:
    """Compute each report's total concurrently (each call is I/O-bound on the store)."""
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {report_id: pool.submit(store.total_for, report_id) for report_id in report_ids}
        return {report_id: future.result() for report_id, future in futures.items()}
```

The pool also bounds fan-out: submit N items to a fixed `max_workers` and the executor
queues the rest. Never spawn a fresh `Thread` per item for on-demand fan-out — a burst of
work then creates a burst of threads, exhausting memory and starving the scheduler. A bounded
executor (or a worker pool draining a `queue.Queue`) keeps the thread count flat under load.

Guard shared mutable state with a `Lock`, or avoid it entirely by returning values:

```python
counter_lock = Lock()

def record(counter: Counter, key: str) -> None:
    """Increment a shared counter safely from multiple threads."""
    with counter_lock:
        counter[key] += 1
```

For producer/consumer flows use `queue.Queue` — it is thread-safe and blocks correctly,
so you never hand-roll waiting with `Lock` + `sleep`.

## Processes and `ProcessPoolExecutor`

Processes sidestep the GIL, at the cost of pickling arguments and results and starting
interpreters. Keep worker functions top-level (lambdas and closures cannot be pickled) and
make the module import-safe.

```python
def render_all(pages: list[Page]) -> list[bytes]:
    """Render pages in parallel across CPU cores."""
    with ProcessPoolExecutor() as pool:
        return list(pool.map(render_page, pages))   # render_page must be importable, side-effect-free at import

if __name__ == "__main__":          # required: the default start method re-imports this module
    render_all(load_pages())
```

Start methods: `spawn` (Windows/macOS default) and `forkserver` (Linux default from 3.14)
re-import your module in each worker, so **any import-time side effect runs again per
worker**. Keep top-level code to definitions; put actions under `if __name__ == "__main__":`.

Workers must not each open the same log file — that is shared mutable state. Route worker
logs through a `QueueHandler` to one listener that owns the file; see **python-logging**.

## asyncio

One `asyncio.run()` at the top; everything below is `async def`. Group concurrent tasks with
`TaskGroup` (3.11+), which awaits them all and propagates the first exception:

```python
async def fetch_all(urls: list[str], client: AsyncHttpClient) -> list[bytes]:
    """Fetch every URL concurrently and return the bodies in order."""
    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(client.get(url)) for url in urls]
    return [task.result() for task in tasks]        # group exit awaited them all
```

- **Never block the loop.** A synchronous `time.sleep`, `requests.get`, or heavy CPU call
  freezes every task. Use `await asyncio.sleep(...)`, an async client, or push the blocking
  call to a thread with `await asyncio.to_thread(blocking_call, arg)`.
- **Time-box** with `async with asyncio.timeout(seconds):` (3.11+) instead of unbounded awaits.
- Prefer `TaskGroup` to bare `asyncio.gather` — a stray task's exception can be lost with
  fire-and-forget `create_task`; the group cancels siblings and re-raises.

## Shared state, races, and deadlocks

- A **race** is any unsynchronized read-modify-write of shared state (`counter += 1` across
  threads). Fix by holding a `Lock`, or by not sharing — pass copies in, return results out.
- A **deadlock** is two threads each holding a lock the other wants. Avoid nested locks; if
  unavoidable, always acquire them in the same global order.
- The safest concurrent code shares **nothing mutable**: workers take immutable inputs and
  return new values, and the caller merges results single-threaded.

## Free threading and subinterpreters (know these exist)

Python 3.13/3.14 add two ways past the GIL. Treat them as "know it exists, detect it, weigh
the caveats" — not yet the portable default.

- **Free-threaded build (PEP 779, officially supported in 3.14).** A separate build with the
  GIL disabled, so threads run CPU-bound Python in true parallel. Opt-in and roughly 5–10%
  slower single-threaded; not every C extension is compatible yet.

  ```python
  # sys._is_gil_enabled() exists on every 3.13+ build — it returns True on a normal build
  # and False on a free-threaded one. It is absent on 3.12 and older, so guard the lookup.
  gil_enabled = sys._is_gil_enabled() if hasattr(sys, "_is_gil_enabled") else True
  if not gil_enabled:
      logger.info("running without the GIL")
  ```

  Also detectable via `python -VV` ("free-threading build") and
  `sysconfig.get_config_var("Py_GIL_DISABLED")`.

- **Subinterpreters (PEP 734).** Multiple isolated interpreters in one process, each with its
  own GIL. The low-level API is `concurrent.interpreters` (3.14+); the executor is
  `concurrent.futures.InterpreterPoolExecutor`. Cheaper to start than processes for CPU-bound
  isolation, but arguments and results still have to cross the interpreter boundary — only a
  narrow set of types passes cheaply, and the rest is serialized like it would be for a process.

Until these settle, processes remain the portable choice for CPU parallelism.

## Official HOWTOs worth linking

- **A Conceptual Overview of asyncio** — the event loop, coroutines, tasks, and why awaiting
  a bare coroutine does *not* cede control: `docs.python.org/3/howto/a-conceptual-overview-of-asyncio.html`
- **Python support for free threading** — building/detecting the no-GIL interpreter and its
  current caveats: `docs.python.org/3/howto/free-threading-python.html`

## Further reading

The judgment defaults here are distilled from a few standard references — reach for these
when a bottleneck needs more than this catalog gives:

- **Effective Python**, 3rd ed. (Brett Slatkin, 2024) — items 67–79 on concurrency, in the
  same best-practice format as these rules; the closest match to how this skill thinks.
- **Python Concurrency with asyncio** (Matthew Fowler, Manning, 2022) — a full book on the
  asyncio model: event loop internals, `aiohttp`, non-blocking drivers, CPU-bound offload.
- **Python Cookbook**, 3rd ed. (David Beazley & Brian K. Jones, 2013) — chapter 12's classic
  threads/queues/pools recipes (pre-asyncio, but the primitives are unchanged).

# Python Logging — reference catalog

Depth for `python-logging`. Load when configuring logging or going beyond the basics.

## The logger hierarchy

Loggers form a tree by dotted name. `getLogger("shop.orders")` is a child of
`getLogger("shop")`, which is a child of the root. A record travels up to ancestor
handlers, so you configure handlers once (usually at the root, in the app entry point)
and every module's `getLogger(__name__)` inherits them.

```python
# every module, at the top — cheap, no configuration
import logging
logger = logging.getLogger(__name__)
```

## Configuring logging (application entry point ONLY)

Do this once, where the program starts (a `main()`), never in importable library code.

```python
import logging

def configure_logging(level: int = logging.INFO) -> None:
    """Set up root logging for the application. Call once at startup."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
        # basicConfig writes to stderr by default, which is what we want for logs.
    )
```

For anything beyond one handler, build handlers explicitly:

```python
def configure_logging(level: int = logging.INFO) -> None:
    """Send INFO+ to stderr with a readable format."""
    handler = logging.StreamHandler()  # defaults to sys.stderr
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-8s %(name)s %(message)s")
    )
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
```

Two gotchas with `basicConfig`:

- Call it **before** any logging call. It configures the root logger only if the root has
  no handlers yet, so the first `logger.info(...)` that fires before it can lock in the
  bare "last resort" handler and your config becomes a silent no-op.
- It configures the **root** logger. The module-level convenience functions
  (`logging.info(...)`) call it implicitly; prefer explicit `getLogger(__name__)` loggers.

## Library logging: NullHandler and warnings

A library must not configure logging for its host application. It should attach a
`NullHandler` to its top-level logger so that, if the application never configures
logging, the library's records are dropped silently instead of triggering the "last
resort" stderr handler.

```python
# mylib/__init__.py
import logging
logging.getLogger("mylib").addHandler(logging.NullHandler())
```

Choosing how a library reports a problem:

- The **caller can fix it** (deprecated argument, misuse) → `warnings.warn(...)`, so it
  surfaces at the call site and can be filtered by the application.
- **Nothing the caller can do** (a transient downstream hiccup you recovered from) →
  `logger.warning(...)`.

## Handlers, formatters, filters

- **Handler** — where records go: `StreamHandler` (stderr/stdout), `FileHandler`,
  `RotatingFileHandler`, `SysLogHandler`, `QueueHandler`.
- **Formatter** — how a record is rendered (timestamp, level, name, message).
- **Filter** — drop or annotate records (e.g. attach a request id).

Set the level in two places if needed: the logger's level gates what it emits; a
handler's level gates what that destination accepts.

A record propagates up to every ancestor's handlers. If you attach a handler to a
non-root logger *and* the root also has one, each record is emitted twice — set
`logger.propagate = False` on that logger to stop the duplicate.

Rotate files instead of letting them grow without bound:

```python
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

by_size = RotatingFileHandler("app.log", maxBytes=10_000_000, backupCount=5)
by_day = TimedRotatingFileHandler("app.log", when="midnight", backupCount=7)
```

To keep logging off the hot path, hand records to a `QueueHandler` and drain them in a
background `QueueListener`. On Python 3.14+ the listener is a context manager, so you no
longer pair `start()`/`stop()` by hand:

```python
with QueueListener(queue, file_handler):   # 3.14+: starts and stops automatically
    run_application()
```

## Logging from multiple processes

A `FileHandler` (or `RotatingFileHandler`) is **not** safe for several processes writing the
same file at once — records interleave and rotation races lose data. Let exactly one process
own the file: each worker's root logger gets a single `QueueHandler` on a shared cross-process
queue, and one `QueueListener` in the main process owns the real handler and is the only
writer. On `spawn`/`forkserver` (the 3.14 default) workers do not inherit handlers, so
configure each one in a pool `initializer`.

```python
def configure_worker_logging(log_queue) -> None:
    """Point this worker's root logger at the shared queue (runs once per worker)."""
    handler = QueueHandler(log_queue)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def main(jobs: list[Job]) -> None:
    """Run jobs across processes; one listener owns the log file."""
    log_queue = Manager().Queue(-1)                    # cross-process, not queue.Queue
    file_handler = RotatingFileHandler("app.log", maxBytes=10_000_000, backupCount=5)
    with QueueListener(log_queue, file_handler):       # 3.14+: starts/stops automatically
        with ProcessPoolExecutor(initializer=configure_worker_logging, initargs=(log_queue,)) as pool:
            list(pool.map(handle_job, jobs))
```

Use `%(processName)s` in the formatter so each line names the worker that emitted it. Choosing
and running the process pool itself → **python-concurrency**.

## Lazy formatting and why it matters

```python
logger.debug("processing %s items for %s", count, user_id)
```

The `%s` arguments are only interpolated if `DEBUG` is enabled, so disabled debug logs
cost almost nothing. An f-string (`logger.debug(f"... {count} ...")`) formats
unconditionally — wasted work in the common case where debug is off.

Lazy `%`-args only defer the *formatting*. If computing an argument is itself expensive,
guard the whole call:

```python
if logger.isEnabledFor(logging.DEBUG):
    logger.debug("state dump: %s", expensive_snapshot())  # not called unless DEBUG is on
```

## Logging exceptions

Inside an `except` block that handles a failure:

```python
try:
    charge(order)
except PaymentError:
    logger.exception("charge failed for order %s", order.id)  # == error(..., exc_info=True)
    raise
```

`logger.exception` records the traceback. Outside an active exception, pass
`exc_info=error` explicitly if you hold the exception object.

## What is safe to log

| Log freely | Never log |
|---|---|
| Ids, order numbers, request ids | Passwords, API keys, tokens, secrets |
| Counts, durations, status codes | Full card numbers, CVV |
| Error type and message | Personal data (names, emails, addresses) beyond policy |
| High-level decisions taken | Whole request/response bodies |

When in doubt, log an identifier, not the value. Redact before logging if you must
reference a sensitive field.

## Structured logging

On Python 3.14+, template strings (`t"..."`, PEP 750) keep the static text and the
interpolated values as separate parts, which is a useful building block for redacting or
structuring fields safely instead of pre-formatting a message. Integration into logging
tooling is still emerging — for now keep passing variables as `%`-args or `extra` fields.

For machine-parsed logs (shipped to a log aggregator), attach fields via `extra` or use a
structured logging library. Keep the message stable and put variables in fields:

```python
logger.info("order charged", extra={"order_id": order.id, "amount_cents": order.amount})
```

## Choosing the level — worked judgments

- A retry that eventually succeeded → `WARNING` (degraded, recovered).
- A cache miss on a normal request → `DEBUG` (routine detail).
- A failed external call that aborts the request → `ERROR` + `logger.exception`.
- The database is unreachable at startup and the service exits → `CRITICAL`.
- "Handled 200 requests in 1.2s" summary → `INFO`.

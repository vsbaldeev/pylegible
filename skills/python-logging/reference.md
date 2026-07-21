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

## Handlers, formatters, filters

- **Handler** — where records go: `StreamHandler` (stderr/stdout), `FileHandler`,
  `RotatingFileHandler`, `SysLogHandler`, `QueueHandler`.
- **Formatter** — how a record is rendered (timestamp, level, name, message).
- **Filter** — drop or annotate records (e.g. attach a request id).

Set the level in two places if needed: the logger's level gates what it emits; a
handler's level gates what that destination accepts.

## Lazy formatting and why it matters

```python
logger.debug("processing %s items for %s", count, user_id)
```

The `%s` arguments are only interpolated if `DEBUG` is enabled, so disabled debug logs
cost almost nothing. An f-string (`logger.debug(f"... {count} ...")`) formats
unconditionally — wasted work in the common case where debug is off.

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

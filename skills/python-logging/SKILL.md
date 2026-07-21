---
name: python-logging
description: >
  Use when adding logging to Python code, choosing a log level (debug/info/warning/
  error/critical), deciding what to send to stdout vs stderr, replacing print statements
  with the logging module, configuring loggers/handlers/formatters, or judging what is
  safe to log. For exception handling itself use python-patterns.
---

# Python Logging

## Overview

Logs are messages to a future operator — often you, at 3am, with only the log to go on.
Log the events and context that make a failure diagnosable, at a level that matches how
much someone should care, and never log a secret. Use the `logging` module, never
`print`, for diagnostics. Depth in `reference.md`.

## Levels — pick by "who needs to care, and when"

| Level | Use for | Seen by default? |
|---|---|---|
| `DEBUG` | Developer detail: values, per-item progress | No |
| `INFO` | Normal milestones: started, finished, request handled | Yes |
| `WARNING` | Something recovered or degraded but continued | Yes |
| `ERROR` | An operation failed; a human should look | Yes |
| `CRITICAL` | The program cannot continue | Yes |

Per-item work goes at `DEBUG` so it does not flood high-volume runs; batch start/end and
failures stay at `INFO`/`ERROR` where operators actually look.

## Core rules

- One logger per module: `logger = logging.getLogger(__name__)` at module top.
- Lazy formatting: `logger.info("charged %s", order_id)` — not f-strings in the call.
- In an `except` block that handles a failure, use `logger.exception(...)` — it attaches
  the traceback. Use it only where you actually catch.
- **Never log** passwords, API keys, tokens, full card numbers, or personal data.
- Libraries never call `basicConfig` or add real handlers; only the application entry
  point configures logging. A library gets its logger, logs, and attaches a
  `logging.NullHandler()` to its top-level logger so it stays silent until the app
  configures logging.

## stdout vs stderr

- **stderr** is for logs and diagnostics. The `logging` module's default handler already
  writes there — good.
- **stdout** is for the program's actual output — the data a caller pipes to another
  command (e.g. the JSON result of a CLI). Keep it clean so `| jq` works.

Mixing them breaks pipelines: never `print()` progress messages onto stdout next to real
output. Progress and status are logs → stderr.

## Example

```python
logger = logging.getLogger(__name__)

def charge_order(order: Order, payments: PaymentClient) -> str:
    """Charge one order and return the charge id."""
    logger.debug("charging order %s amount=%s", order.id, order.amount)
    try:
        charge = payments.charge(order.amount)
    except PaymentError:
        logger.exception("charge failed for order %s", order.id)  # traceback, no card data
        raise
    logger.info("charged order %s -> %s", order.id, charge.id)
    return charge.id
```

## Common mistakes

- `print()` for diagnostics, or progress printed to stdout beside real output.
- f-strings inside logging calls (formats even when the level is disabled).
- Logging secrets, tokens, or whole request/response bodies.
- Calling `logging.basicConfig` from library code.
- `logger.error(str(error))` in an `except` — loses the traceback; use `logger.exception`.

## Boundary

This skill owns logging: levels, what/where to log, configuration. How to *catch and
raise* exceptions → **python-patterns**. See `reference.md` for handlers, formatters,
structured logging, and application setup.

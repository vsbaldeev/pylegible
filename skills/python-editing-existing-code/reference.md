# Editing Existing Code — reference catalog

Depth for `python-editing-existing-code`. Load when you need the details. The moves here
come from Michael Feathers, *Working Effectively with Legacy Code*, adapted to Python.
Examples obey the project `CLAUDE.md` conventions. How to write the tests themselves —
fixtures, mocks, markers — is **python-testing**; this catalog covers *when* and *what to
pin*, not pytest mechanics.

## The core loop

Feathers' definition: legacy code is code without tests. You cannot safely change what you
cannot pin. So every risky edit follows the same loop:

```
1. Find a seam            — a place to observe or replace behavior without editing it
2. Characterize          — write tests that capture what the code does now, bugs included
3. Change                — make the edit; the characterization tests catch what you moved
4. Update the pins       — flip only the assertions the intended change moved
5. Refactor (optional)   — now that behavior is pinned, improve — as its own change
```

Steps 4 and 5 are where discipline leaks: the moment behavior is pinned it is tempting to
"clean up while I'm here." Keep the behavior change and the cleanup in separate commits so a
reviewer can trust each independently.

## Finding seams

A **seam** is a place where you can alter behavior without editing the code at that place.
Every seam has an **enabling point** — where you choose which behavior runs. Prefer seams in
this order; the higher ones need no production change at all.

### Object seam (parameter / dependency injection)

The behavior arrives as an argument, so a test passes a fake. Best seam there is — if it
already exists, use it.

```python
def render_report(orders: list[Order], clock: Clock) -> str:
    """Render the report as of clock.now()."""
    ...

def test_render_report_stamps_current_time():
    frozen = FrozenClock(datetime(2026, 1, 1))
    assert "2026-01-01" in render_report(sample_orders, frozen)
```

### Import seam (monkeypatch)

The dependency is looked up by name at call time, so a test replaces the name. Patch where
the object is *used*, not where it is defined.

```python
def test_sync_retries_on_timeout(monkeypatch):
    calls = []
    def fake_fetch(url):
        calls.append(url)
        if len(calls) < 3:
            raise TimeoutError
        return "ok"
    monkeypatch.setattr("myapp.sync.fetch", fake_fetch)
    assert sync("https://example.test") == "ok"
    assert len(calls) == 3
```

### Subclass-and-override seam

When a method reaches out to something untestable, subclass in the test and override just
that method. A crude, temporary seam — use it to get the first test green, then refactor
toward an object seam.

```python
class TestableUploader(Uploader):
    def transmit(self, payload: bytes) -> None:  # override the network call only
        self.sent = payload

def test_uploader_compresses_before_transmit():
    uploader = TestableUploader()
    uploader.upload(b"x" * 1000)
    assert len(uploader.sent) < 1000
```

If no seam exists and you cannot add one cheaply, that is the signal in the SKILL rule:
**stop and surface it**, or introduce the smallest seam via sprout/wrap below — do not edit
blind.

## Characterization-test recipes

A characterization test asks the code what it does and records the answer. You are not
asserting correctness — you are building a net.

**Let the failure tell you the value.** Assert a guess, run, copy the actual value from the
failure into the assertion. The test now documents reality.

```python
def test_legacy_price_characterization():
    assert legacy_price(quantity=7, tier="gold") == 0  # placeholder; run, then paste actual
```

**Approval / golden-file testing** for wide output (rendered HTML, a report, a big dict).
Snapshot the current output; the test fails when any byte changes, which is exactly what you
want around code you are about to touch.

```python
def test_invoice_html_matches_snapshot(snapshot):   # e.g. the syrupy plugin
    assert render_invoice(sample_order) == snapshot
```

Review the first snapshot by eye — it is a photograph of current behavior, warts and all.
After an intended change, re-approve it deliberately; never auto-accept a diff you did not
read.

**Pin exceptions and side effects, not just return values.** If the code writes a file,
mutates an argument, or logs at a level, pin that too — it is behavior a consumer may depend
on.

```python
def test_import_rows_skips_and_logs_bad_line(caplog, tmp_path):
    target = tmp_path / "out.csv"
    import_rows(["good", "BAD", "good"], target)
    assert target.read_text().count("\n") == 2      # the bad line was dropped
    assert "skipped line 2" in caplog.text          # and it was reported
```

## Adding to untestable code

When you cannot pin the existing behavior cheaply, do not edit inside it. Add new, tested
code beside it.

**Sprout** — write the new logic as a fresh, fully tested function or class, then call it
from the old code in one line. The new behavior is clean; the old mess is untouched.

```python
def compute_late_fee(balance: float, days_overdue: int) -> float:
    """Late fee: 1.5% per 30-day period, capped at 10% of balance."""
    periods = days_overdue // 30
    return min(balance * 0.015 * periods, balance * 0.10)

# inside the legacy routine, the only edit is one call:
#     total = subtotal + tax + compute_late_fee(subtotal, days_overdue)
```

**Wrap** — rename the old function and give the new name a thin wrapper that adds the
behavior around it. Nothing inside the old body changes.

```python
def send_invoice(order: Order) -> None:
    """Send the invoice, recording an audit entry around the existing send."""
    record_audit("invoice.send.start", order.id)
    send_invoice_unaudited(order)   # the original body, renamed verbatim
    record_audit("invoice.send.done", order.id)
```

Sprout and wrap trade a little duplication now for a tested seam you can refactor through
later. That trade is usually right under deadline.

## Strangler-fig — replacing a subsystem

For a replacement too large for one diff, grow the new implementation around the old and
route traffic across incrementally, behind one stable interface.

```
1. Put the old subsystem behind an interface (a Protocol) if it isn't already.
2. Build the new implementation behind the same interface, tested in isolation.
3. Route a slice of calls to the new path (a flag, a key range, a percentage).
4. Widen the slice as evidence accrues; keep both paths reconcilable.
5. Delete the old implementation and the switch once nothing routes to it.
```

Each step is its own change with its own tests. The old code keeps working the whole way —
there is never a "big bang" cutover to get wrong. Contrast with a rewrite-in-place, which is
un-shippable until the last line lands.

## When to stop — the leash

Restraint needs a definition of "done with this change," or every edit metastasizes.

- **The footprint** is the code the task requires you to change, plus the lines a reader
  must touch to follow it. Nothing else — however tempting.
- **A spotted violation you are leaving alone** gets *recorded*, not fixed: a tracked issue,
  or a comment at the site. A record is a decision; a drive-by edit is noise.

```python
# TODO(#412): this module mixes pricing rules with CSV parsing — split when next
# touched for a pricing change. Left as-is here; this diff only fixes the rounding bug.
```

- **A refactor large enough to need its own tests and its own review** is large enough to
  need its own change. If it would double the diff of a bugfix, it is a separate piece of
  work — and, past a certain size, its own spec.

The test for "is this in scope?": could you write the commit message as one sentence with no
"and"? If not, you are shipping two changes as one. The project `CLAUDE.md` lists the full
design-principle set that the cleanup, when you do schedule it, should aim for.

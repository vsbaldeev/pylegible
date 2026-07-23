# Python Testing — reference catalog

Depth for `python-testing`. Load when you need the details. Examples obey the project
`CLAUDE.md` conventions.

## TDD cycle (double loop)

The outer loop is the feature; the inner loop is the design. Start outside.

```
OUTER   write the failing e2e test — the feature is not done
  INNER   RED       failing unit test for the next piece
          GREEN     minimum code to pass
          REFACTOR  improve names/structure, tests green
          repeat while the e2e test is still red
OUTER   e2e test green — the feature is done. Stop.
```

The outer test is what tells you when to stop, which is the half of TDD that usually goes
missing. Without it there is no completion signal, and tests accumulate until someone gets
bored. Write unit tests for the pieces you actually design on the way to green — not for
every line that ends up existing.

Keep the outer loop thin: a handful of e2e tests over the real entrypoint, many units
beneath them. Inverting that ratio buys slow, flaky runs that report "something broke"
without saying what.

## Coverage

Coverage is a diagnostic, never a target. Read it backwards — an uncovered line is a
question, not a ticket to write a test:

1. **Is the branch reachable?** No → delete it.
2. **Would its failure matter?** No → leave it uncovered, deliberately.
3. **Yes to both** → write the test, and take the failure signature from evidence
   (see *Unreproducible conditions* below).

Setting a percentage in CI collapses all three questions into "generate something that
executes the line", which is satisfied perfectly by tests that assert nothing. Measure
when you want the diagnostic, not on every run:

```bash
pytest --cov=mypackage --cov-report=term-missing   # requires the pytest-cov plugin
```

An untested `except` branch nobody has ever seen fire is not a safety net — it is
unexercised code that will run for the first time during an incident.

## Fixtures

A fixture provides a ready-to-use object and (optionally) tears it down after `yield`.

```python
@pytest.fixture
def database() -> Iterator[Database]:
    connection = Database(":memory:")
    connection.create_tables()
    yield connection
    connection.close()
```

Scopes: `function` (default), `class`, `module`, `session` — widen only when setup is
expensive and safely shared. Put fixtures used across files in `tests/conftest.py`.

Use `autouse=True` sparingly, for cross-cutting setup like resetting global config.

## Parametrization

Collapse same-shape cases; name them with `ids` so failures read clearly.

```python
@pytest.mark.parametrize(
    "raw, expected",
    [("valid@example.com", True), ("no-at", False), ("@no-user.com", False)],
    ids=["valid", "missing-at", "missing-user"],
)
def test_is_valid_email(raw, expected):
    assert is_valid_email(raw) is expected
```

Parametrize a fixture to run every dependent test against several backends:

```python
@pytest.fixture(params=["memory", "postgres"])
def store(request) -> Store:
    return make_store(request.param)
```

## Mocking and patching

Patch where the name is *used*, not where it is defined. Prefer `autospec=True` so a
mock rejects calls the real object would reject.

```python
@patch("mypackage.orders.payment_client", autospec=True)
def test_charge_is_recorded(payment_client_mock):
    payment_client_mock.charge.return_value = {"id": "ch_1"}
    result = process_one(order)
    payment_client_mock.charge.assert_called_once()
    assert result["charge_id"] == "ch_1"
```

- Simulate failure with `side_effect = ConnectionError(...)`.
- For async, use `assert_awaited_once()` and mock with `AsyncMock`.

## Testing exceptions

```python
def test_divide_rejects_zero_divisor():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_validate_reports_field_in_message():
    with pytest.raises(ValidationError, match="email"):
        validate({"email": ""})
```

Capture the exception object when you need to assert on its attributes:

```python
with pytest.raises(ApiError) as exc_info:
    call_api()
assert exc_info.value.status_code == 503
```

## Unreproducible conditions

Some failures you must handle cannot be summoned on demand: the disk fills, the network
partitions, the process is killed mid-transaction, two threads interleave badly. You never
reproduce the physical cause. You reproduce **what your code observes when it happens**,
which is always narrow.

Your code cannot perceive "the disk is full". It perceives `write()` raising `OSError` with
`errno.ENOSPC`. That signature is the whole test.

| Condition | What the code actually sees | Where to inject |
|---|---|---|
| Disk full | `OSError(ENOSPC)` from `write`/`flush` | filesystem port, or a 1 MB `tmpfs` |
| Network partition | `ConnectionResetError` / read timeout mid-stream | HTTP client seam, or a fault proxy |
| Power loss mid-write | file present, truncated, no trailing marker | write the truncated file as a fixture |
| Killed mid-transaction | step one committed, step two never ran | fake that succeeds once, then raises |
| Clock skew, DST, leap second | `now()` returning a value ≤ the previous one | injected clock |
| FD or memory exhaustion | `OSError(EMFILE)`, `MemoryError` | `resource.setrlimit`, `ulimit -n` |
| Upstream degradation | `503`, rate-limit header, truncated JSON | stubbed transport, recorded response |
| Counter wraparound | an integer that went negative | pass the value in — it is arithmetic |

**The evidence rule.** The value of these tests is entirely in the fidelity of the
signature. A retry test built on `ConnectionError` proves nothing if the driver raises
`psycopg.OperationalError` — it passes, and the bug ships. So the signature comes from a
real traceback, a real log line, or the dependency's documented error table. Never from
what seems plausible. Cite the source in the test:

```python
class FlakyMessageQueue:
    """Queue double that accepts one publish and then dies, as a broker crash would."""

    def __init__(self) -> None:
        """Records published messages and arms the failure for the second call."""
        self.published: list[str] = []

    def publish(self, message: str) -> None:
        """Publishes once, then raises the disconnect seen in incident 412."""
        if self.published:
            raise ConnectionResetError(errno.ECONNRESET, "Connection reset by peer")
        self.published.append(message)


def test_order_stays_pending_when_the_broker_dies_between_messages():
    queue = FlakyMessageQueue()
    repository = InMemoryOrderRepository({"order-1": Order(items=2)})

    with pytest.raises(PublishFailed):
        notify_all_items(repository, queue, "order-1")

    assert repository.get("order-1").status == "pending"
    assert len(queue.published) == 1
```

### Forcing an interleaving

Races need a different mechanism. There is no return value to substitute — the bug is
*when* calls happen relative to each other, so the double must provide a **control point**
where the test can park one thread and hold it there:

```python
class PausingRepository:
    """Wraps a repository and parks the first reader between its read and its write."""

    def __init__(self, inner: Repository) -> None:
        """Stores the wrapped repository and the two coordination events."""
        self.inner = inner
        self.entered_window = threading.Event()
        self.may_continue = threading.Event()
        self.pause_next_read = True

    def get_balance(self, account_id: str) -> int:
        """Reads the balance, holding the first caller inside the race window."""
        balance = self.inner.get_balance(account_id)
        if self.pause_next_read:
            self.pause_next_read = False
            self.entered_window.set()
            self.may_continue.wait(timeout=5)
        return balance


def test_withdrawal_inside_the_read_write_window_cannot_overdraw():
    repository = PausingRepository(InMemoryRepository({"acct-1": 100}))
    account = Account("acct-1", repository)
    outcomes: list[str] = []

    parked = threading.Thread(target=lambda: outcomes.append(withdraw_or_fail(account, 100)))
    parked.start()
    repository.entered_window.wait(timeout=5)   # parked between read and write

    outcomes.append(withdraw_or_fail(account, 100))   # runs fully inside the window

    repository.may_continue.set()
    parked.join(timeout=5)

    assert outcomes.count("ok") == 1
    assert repository.inner.get_balance("acct-1") == 0
```

This fails deterministically against check-then-act code, on every machine. Note what it
also rules out: you cannot satisfy it by wrapping the operation in a lock, because the
parked thread holds it and the test deadlocks. The fix it drives you toward is an atomic
repository operation — `decrement_if_sufficient(account_id, amount) -> bool`.

Two limits:

- The test pins **one** interleaving. It proves that bug stays dead, not that the code is
  race-free. Pair it with a `@pytest.mark.stress` run — many real-threaded repeats via
  `pytest-repeat` (`--count`), sampling many interleavings — excluded from the default
  suite. See *Plugins*.
- Prefer the real condition when it is cheap. A 1 MB `tmpfs`, `resource.setrlimit`,
  `ulimit -n 32`, or writing 40 bytes of a 200-byte format all beat a fake, because you
  observe the true signature instead of guessing it. Fake only when the real condition is
  expensive, destructive, or genuinely unreachable.

## Async tests

```python
@pytest.mark.asyncio
async def test_fetch_returns_payload(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
```

The `asyncio` marker comes from the `pytest-asyncio` plugin — it is not built in. Install
it and set `asyncio_mode` (below), or the test is silently skipped rather than run, which
looks exactly like a passing suite. See *Plugins*.

This covers *testing* async code; for writing it (asyncio, threads, processes, executors)
see **python-concurrency**.

## Markers and selection

```python
@pytest.mark.slow
def test_full_import():
    ...
```

```bash
pytest -m "not slow"     # skip slow tests
pytest -k "discount"      # run tests whose name matches
pytest -x --lf            # stop at first failure; rerun last-failed
```

Declare markers in config so `--strict-markers` catches typos.

## Configuration (pyproject.toml)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--strict-markers"]
markers = [
    "slow: slow tests",
    "integration: touches external systems",
    "stress: randomized/repeated runs, excluded from the default suite",
]
```

Coverage stays out of `addopts` deliberately: it slows every run, and putting the
percentage in front of you on every invocation is what turns a diagnostic into a target.
Run it when you want to read it.

For `pytest-asyncio`, pick the mode explicitly rather than relying on the default:

```toml
[tool.pytest.ini_options]
asyncio_mode = "strict"   # every async test must carry @pytest.mark.asyncio
```

## Plugins

A pytest plugin is a dependency like any other: add one when a real requirement needs it,
not on spec. Each plugin is one more thing the next reader must have installed and
understand, so the bar is the same YAGNI bar the tests themselves follow. Core pytest —
fixtures, `parametrize`, `raises`, `approx`, markers, `tmp_path`, `monkeypatch` — covers
most of a suite on its own; reach past it only when a technique here actually calls for it.

Every plugin below earns its place by a technique this skill already teaches — not by
popularity. That is the whole test for adding another.

| Plugin | Adds | Reach for it when |
|---|---|---|
| `pytest-cov` | the `--cov` integration used under *Coverage* | you want the diagnostic; not in `addopts` |
| `pytest-asyncio` | the `asyncio` marker under *Async tests* | testing coroutines — and set `asyncio_mode` |
| `pytest-randomly` | randomized test order, a printed seed | enforcing *Isolation* — it surfaces the order-dependence a fixed order hides |
| `pytest-repeat` | `--count=N` / `@pytest.mark.repeat` | the `stress` runs under *Unreproducible conditions* — many real-threaded repeats sample many interleavings |
| `freezegun` / `time-machine` | freezes wall-clock time by patching | you cannot inject a clock because the code under test calls `datetime.now()` directly |
| `pytest-mock` | the `mocker` fixture over `unittest.mock` | you prefer fixture-scoped patches that undo themselves — ergonomics, not new power |

Two honest caveats:

- **`freezegun`/`time-machine` are the fallback, not the default.** The *Unreproducible
  conditions* clock technique injects a clock object precisely so time is an ordinary
  collaborator. Patching wall-clock time globally is what you do when the code isn't yours
  to change — reaching for it in your own code is a sign the seam is missing.
- **Property-based testing (`hypothesis`) is its own discipline**, not a drop-in plugin
  row. It generates inputs to find the failing case you didn't think of, which is a
  different activity from the example-based tests here. Worth learning; out of scope for
  this catalog.

## Organization

```
tests/
  conftest.py          # shared fixtures
  unit/                # fast, isolated — one module each, collaborators faked
  integration/         # one adapter against its real DB, filesystem, or network double
  e2e/                 # spans modules; drives the whole app
```

Which directory a file goes in follows from how many source modules it covers: one module
mirrors the source path, several is named for the behavior instead. Full rules — including
when to mirror at all — → **python-project-structure**.

`e2e/` stays small — one file per user journey, not per branch. The supporting unit tests
outnumber it heavily; that is what turns "checkout is broken" into "the tax rounding is
broken". Fault-injection tests are unit tests: they fake the boundary, so they live under
`unit/` on the mirrored path, not in `integration/`.

Group related tests in a `Test<Subject>` class when they share a fixture; keep the class
thin — no logic beyond arranging and asserting.

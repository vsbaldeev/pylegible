# Python Testing — reference catalog

Depth for `python-testing`. Load when you need the details. Examples obey the project
`CLAUDE.md` conventions.

## TDD cycle

1. **RED** — write a failing test for the next behavior.
2. **GREEN** — write the minimum code to pass.
3. **REFACTOR** — improve names/structure with tests green.

Coverage target: 80%+ overall, 100% on critical paths. Measure, don't guess:

```bash
pytest --cov=mypackage --cov-report=term-missing
```

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

## Async tests

```python
@pytest.mark.asyncio
async def test_fetch_returns_payload(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
```

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
addopts = ["--strict-markers", "--cov=mypackage", "--cov-report=term-missing"]
markers = [
    "slow: slow tests",
    "integration: touches external systems",
]
```

## Organization

```
tests/
  conftest.py          # shared fixtures
  unit/                # fast, isolated
  integration/         # touches DB, filesystem, network doubles
```

Group related tests in a `Test<Subject>` class when they share a fixture; keep the class
thin — no logic beyond arranging and asserting.

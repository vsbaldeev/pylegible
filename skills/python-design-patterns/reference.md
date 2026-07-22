# Python Design Patterns — reference catalog

Depth for `python-design-patterns`. Load when you need the full shape of a pattern that
earns its keep, or evidence for rejecting one that does not. Every example here obeys the
house conventions in the project `CLAUDE.md` (no single-letter names, no leading single
underscore, ≤40-line bodies, Google-style docstrings, annotated signatures).

The eight patterns below are the ones worth knowing by name in Python. The other fifteen
are covered by the verdict table in `SKILL.md` — read that first.

## Strategy

A strategy is a behavior chosen at runtime. In Python that is a callable, so the pattern is
usually a parameter, not a hierarchy.

```python
from collections.abc import Callable, Iterable

RankKey = Callable[[Article], float]

def by_recency(article: Article) -> float:
    """Rank an article by how recently it was published."""
    return article.published_at.timestamp()

def by_popularity(article: Article) -> float:
    """Rank an article by view count."""
    return float(article.view_count)

def top_articles(articles: Iterable[Article], rank: RankKey, limit: int) -> list[Article]:
    """Return the highest-ranking articles under the given ranking function."""
    return sorted(articles, key=rank, reverse=True)[:limit]
```

**Selecting a strategy by name** — from config or a request parameter — is a `dict`, not a
factory class:

```python
RANKINGS: dict[str, RankKey] = {"recency": by_recency, "popularity": by_popularity}

def resolve_ranking(name: str) -> RankKey:
    """Look up a ranking function by its configured name."""
    try:
        return RANKINGS[name]
    except KeyError as error:
        raise ValueError(f"Unknown ranking {name!r}") from error
```

**When a class is still right:** the strategy holds configuration *and* exposes more than
one method, or it needs to be constructed with dependencies. Then define a `Protocol` with
those methods and pass instances. One method plus one config value is still a closure.

## Adapter

Make a foreign object satisfy an interface you own. This is the pattern that survives
Python most intact, because the whole point is that you cannot change the other side.

```python
from typing import Protocol

class Cache(Protocol):
    """The caching interface this application depends on."""

    def get(self, key: str) -> bytes | None:
        """Return the cached value, or None if absent."""

    def put(self, key: str, value: bytes, ttl_seconds: int) -> None:
        """Store a value under the key for the given lifetime."""

class RedisCache:
    """Adapts a redis client to the application's Cache interface."""

    def __init__(self, client: redis.Redis) -> None:
        self.client = client

    def get(self, key: str) -> bytes | None:
        """Return the cached value, or None if absent."""
        return self.client.get(key)

    def put(self, key: str, value: bytes, ttl_seconds: int) -> None:
        """Store a value under the key for the given lifetime."""
        self.client.setex(key, ttl_seconds, value)
```

The rest of the codebase depends on `Cache`, never on `redis`. Swapping the backend, or
substituting a dict in tests, touches one class. Note that implementers do not inherit from
`Protocol` — structural typing means `RedisCache` satisfies it by shape.

## Facade

One entry point over a subsystem that takes several coordinated steps. In Python the facade
is often a module, not a class.

```python
def publish_article(article_id: int) -> PublishedArticle:
    """Render, upload, and index an article, returning the published record.

    Args:
        article_id: Identifier of the draft to publish.

    Returns:
        The published article record.

    Raises:
        PublishError: If any stage of publication fails.
    """
    draft = drafts.load(article_id)
    rendered = renderer.to_html(draft)
    location = storage.upload(rendered, path=draft.slug)
    search.index(draft, location)
    return drafts.mark_published(draft, location)
```

Callers say `publish_article(42)` and never learn that four subsystems exist. Keep the
facade thin — it coordinates, it does not compute. When it starts making decisions, that
logic belongs in one of the modules underneath.

## Observer

Notify interested parties without the source knowing who they are. A list of callbacks
covers nearly every real case.

```python
from collections.abc import Callable

OrderListener = Callable[[Order], None]

class OrderBook:
    """Accepts orders and notifies registered listeners about each one."""

    def __init__(self) -> None:
        self.listeners: list[OrderListener] = []

    def subscribe(self, listener: OrderListener) -> None:
        """Register a listener to be called for every accepted order."""
        self.listeners.append(listener)

    def accept(self, order: Order) -> None:
        """Record an order and notify every listener."""
        self.store.append(order)
        for listener in self.listeners:
            listener(order)
```

**Failure policy is the real design question.** As written, one raising listener stops the
rest. Decide deliberately: let it propagate (fail fast — good when listeners are core), or
log and continue (good when they are incidental). Never swallow silently.

```python
        for listener in self.listeners:
            try:
                listener(order)
            except Exception as error:
                logger.exception("Order listener %s failed", listener, exc_info=error)
```

That is one of the few places a broad `except` is defensible: an incidental listener must
not take down order acceptance. Log it, never discard it.

## State

When an object behaves differently depending on which state it is in. Reach for the full
pattern only when transitions are numerous and each state carries its own behavior.

**Start here** — an `Enum` plus a transition table:

```python
class OrderState(Enum):
    DRAFT = auto()
    PAID = auto()
    SHIPPED = auto()
    CANCELLED = auto()

TRANSITIONS: dict[OrderState, frozenset[OrderState]] = {
    OrderState.DRAFT: frozenset({OrderState.PAID, OrderState.CANCELLED}),
    OrderState.PAID: frozenset({OrderState.SHIPPED, OrderState.CANCELLED}),
    OrderState.SHIPPED: frozenset(),
    OrderState.CANCELLED: frozenset(),
}

def transition(order: Order, target: OrderState) -> Order:
    """Move an order to a new state, rejecting illegal transitions.

    Raises:
        IllegalTransition: If the move is not allowed from the current state.
    """
    if target not in TRANSITIONS[order.state]:
        raise IllegalTransition(f"Cannot go from {order.state} to {target}")
    return dataclasses.replace(order, state=target)
```

The legal moves are one readable table instead of scattered `if` chains. Graduate to state
*objects* — one class per state behind a `Protocol` — only when each state needs several
distinct behaviors, not just a different set of allowed moves.

## Builder

For construction that is stepwise or conditional. Most Python objects do not need it:
keyword arguments and `@dataclass` already give you named, optional, defaulted fields.

Use a builder when the object is assembled across several decisions:

```python
class QueryBuilder:
    """Accumulates clauses and renders a parameterized SQL query."""

    def __init__(self, table: str) -> None:
        self.table = table
        self.conditions: list[str] = []
        self.parameters: list[object] = []

    def where(self, clause: str, value: object) -> "QueryBuilder":
        """Add a condition and its bound parameter, returning self for chaining."""
        self.conditions.append(clause)
        self.parameters.append(value)
        return self

    def build(self) -> tuple[str, list[object]]:
        """Render the accumulated clauses into SQL and its parameters."""
        sql = f"SELECT * FROM {self.table}"
        if self.conditions:
            sql += " WHERE " + " AND ".join(self.conditions)
        return sql, self.parameters
```

Returning `self` to allow chaining is the one place fluent style pays off in Python. Do not
apply it elsewhere — mutating methods should normally return `None`, so that a reader can
tell setters from queries at a glance.

## Chain of Responsibility

Try handlers in order until one takes the job. In Python this is a list and a loop, not a
linked structure where each handler holds the next.

```python
Handler = Callable[[Request], Response | None]

def handle(request: Request, handlers: Sequence[Handler]) -> Response:
    """Pass a request to each handler until one returns a response.

    Raises:
        Unhandled: If no handler claims the request.
    """
    for handler in handlers:
        response = handler(request)
        if response is not None:
            return response
    raise Unhandled(f"No handler for {request.path}")
```

GoF has each handler store a `successor` because those languages made a list of function
pointers awkward. Keeping the sequence outside the handlers means the order lives in one
visible place and any handler can be reused in another chain.

## Template Method

A fixed skeleton with variable steps. Legitimate, but it is inheritance for reuse, so hold
it to a higher bar than the others: use it only when the steps are genuinely meaningless
outside the skeleton.

```python
class Report(ABC):
    """Renders a report by fetching rows, formatting them, and adding a footer."""

    def render(self) -> str:
        """Produce the finished report. Subclasses do not override this."""
        rows = self.fetch_rows()
        body = "\n".join(self.format_row(row) for row in rows)
        return f"{body}\n{self.footer()}"

    @abstractmethod
    def fetch_rows(self) -> list[Row]:
        """Return the rows this report covers."""

    @abstractmethod
    def format_row(self, row: Row) -> str:
        """Render one row as a line of text."""

    def footer(self) -> str:
        """Return the closing line. Subclasses may override."""
        return "-- end of report"
```

`render` is the template; subclasses fill the holes. **The composition alternative** — pass
a fetcher and a formatter into one concrete `Report` — is better whenever those pieces make
sense on their own, because it keeps them testable and recombinable without subclassing.

## Java-isms to reject

Patterns that arrive by translation and should not survive review.

```python
# Reject: a class impersonating a module
class ConfigManager:
    instance = None

    def __new__(cls) -> "ConfigManager":
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

# Use: modules are already singletons, imported once and cached
SETTINGS = load_settings(Path("settings.json"))

# Or, when construction must be deferred until first use:
@functools.cache
def settings() -> Settings:
    """Load settings once, on first call."""
    return load_settings(Path("settings.json"))
```

```python
# Reject: getters and setters that do nothing
class Account:
    def get_balance(self) -> Decimal:
        return self.balance

    def set_balance(self, balance: Decimal) -> None:
        self.balance = balance

# Use: a plain attribute. Add @property later if a rule appears — callers do not change.
class Account:
    balance: Decimal
```

Also reject on sight:

- **`AbstractThingFactoryImpl`** and any name containing both `Abstract` and `Impl`. One
  authoritative name per concept, no ceremony.
- **An interface per class.** `Protocol` earns its place when two or more implementations
  exist, or when a test needs a substitute. Not before.
- **Deep hierarchies for reuse.** Inheritance is for substitutability (Liskov). If you are
  subclassing to borrow a method, compose instead.
- **Empty subclasses "for future extension."** Add them when the second case arrives.
- **A pattern name in a class name** (`OrderVisitor`, `PaymentStrategy`) when the object
  does not implement that pattern. The name is a promise to the next reader.

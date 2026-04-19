# Coding Conventions

**Analysis Date:** 2026-04-19

## Language Target

- **Python `>=3.9`** (`pyproject.toml` `requires-python = ">=3.9"`).
- Classifiers declare 3.9 / 3.10 / 3.11 / 3.12 / 3.13 / 3.14.
- Ruff `target-version = "py39"` — keeps the linter from suggesting 3.10+ syntax (PEP 604 unions, `match`, `from __future__ import annotations` is *optional*, used only in 7 newer modules: `mempalace/sources/*.py`, `mempalace/backends/registry.py`, `mempalace/sweeper.py`, `mempalace/fact_checker.py`).
- Wheel built by `hatchling` from the `mempalace/` package only (`pyproject.toml` `[tool.hatch.build.targets.wheel]`).

## Style & Lint

Configured in `pyproject.toml`:

- **Line length** `100` (E501 is explicitly *ignored* — long log lines and chained calls are allowed).
- **Quotes** double, set by `ruff format` (`[tool.ruff.format] quote-style = "double"`).
- **Indentation** 4 spaces (ruff default).
- **Lint rule families** `E` (pycodestyle errors), `F` (pyflakes), `W` (pycodestyle warnings), `C901` (mccabe complexity).
- **Complexity ceiling** `max-complexity = 25` (deliberately loose — `mcp_server.handle_request` and `searcher.search_memories` are large dispatchers).
- **Pre-commit** runs `ruff` + `ruff-format` pinned to `v0.4.10` (`.pre-commit-config.yaml`), kept in lock-step with the CI lint job (`.github/workflows/ci.yml` installs `ruff>=0.4.0,<0.5`).
- **Excluded from lint** the top-level `benchmarks/` directory (`extend-exclude = ["benchmarks"]`).
- Lint commands in `CLAUDE.md`: `ruff check .`, `ruff format .`, `ruff format --check .`.

## Naming

Confirmed across `mempalace/searcher.py`, `mempalace/mcp_server.py`, `mempalace/config.py`, `mempalace/backends/base.py`, `mempalace/cli.py`:

- **Functions / variables** `snake_case` — `search_memories`, `sanitize_name`, `build_where_filter`, `palace_path`.
- **Classes** `PascalCase` — `MempalaceConfig`, `ChromaBackend`, `BaseCollection`, `KnowledgeGraph`, `SearchError`.
- **Module constants** uppercase or `_LEADING_UNDERSCORE` for module-private — `MAX_NAME_LENGTH`, `DEFAULT_PALACE_PATH`, `DEFAULT_HALL_KEYWORDS`, `_TOKEN_RE`, `_CLOSET_DRAWER_REF_RE`, `_WAL_DIR`, `_REQUIRED_OPERATORS`, `_SAFE_NAME_RE`.
- **Private helpers** `_leading_underscore` — `_first_or_empty`, `_tokenize`, `_bm25_scores`, `_hybrid_rank`, `_validate_where`, `_get_collection`.
- **CLI command handlers** `cmd_<verb>` — `cmd_init`, `cmd_mine`, `cmd_search`, `cmd_repair` (`mempalace/cli.py`).
- **Test classes** `TestXxx` (xUnit grouping), test funcs `test_xxx` (`tests/test_searcher.py`, `tests/test_dialect.py`).

## Type Hints

**Partial coverage** — type hints appear where they aid readability, not as a project-wide mandate (`CONTRIBUTING.md`: "Type hints: where they improve readability"). No `mypy` configured; `mempalace/py.typed` ships an empty marker for downstream type-checkers.

- Public API surfaces are typed: `def sanitize_name(value: str, field_name: str = "name") -> str:` (`mempalace/config.py:22`), `def search_memories(query: str, palace_path: str, wing: str = None, ..., max_distance: float = 0.0) -> dict:` (`mempalace/searcher.py:304`).
- ABCs in `mempalace/backends/base.py` use `from typing import ClassVar, Optional` and parametric generics: `ids: list[list[str]]`, `embeddings: Optional[list[list[list[float]]]] = None` (PEP 585 builtins are fine because target is 3.9 — the `from __future__ import annotations` form is not used here, the file relies on the dataclass treating annotations as strings).
- Internal helpers often skip return types: `_bm25_scores(query: str, documents: list, k1: float = 1.5, b: float = 0.75) -> list:` (`mempalace/searcher.py:53`) — typed args, untyped element types.
- Idiomatic `Optional[X]` rather than `X | None` (kept compatible with 3.9).

## Docstrings

**Plain triple-double-quoted, no enforced style** (no Google/NumPy/Sphinx). Pattern observed:

- Module header: filename + one-line purpose, then a paragraph of design notes. Example:

```1:10:mempalace/searcher.py
#!/usr/bin/env python3
"""
searcher.py — Find anything. Exact words.

Hybrid search: BM25 keyword matching + vector semantic similarity. The
drawer query is the floor — always runs — and closet hits add a rank-based
boost when they agree. Closets are a ranking *signal*, never a gate, so
weak closets (regex extraction on narrative content) can only help, never
hide drawers the direct path would have found.
"""
```

- Function docstrings: one-line summary, blank line, free-form prose paragraphs. `Args:` / `Returns:` / `Raises:` headers appear only when useful — see `_bm25_scores` (`mempalace/searcher.py:53`) for a parameter-explaining example, and `quarantine_stale_hnsw` (`mempalace/backends/chroma.py:52`) for an `Args: / Returns:` block.
- Custom exceptions get a one-line docstring describing when they're raised — `class SearchError(Exception): """Raised when search cannot proceed (e.g. no palace found)."""` (`mempalace/searcher.py:26`).

## Error Handling

Pattern is **raise typed exceptions on contract violations, return error dicts on user-facing API surfaces**.

- **Custom exception hierarchies per concern**:
  - `mempalace/backends/base.py:26-54` — `BackendError` → `PalaceNotFoundError`, `BackendClosedError`, `UnsupportedFilterError`, `DimensionMismatchError`, `EmbedderIdentityMismatchError`. `PalaceNotFoundError` also subclasses `FileNotFoundError` so legacy callers keep working.
  - `mempalace/sources/base.py:33-58` — `SourceAdapterError` → `SourceNotFoundError`, `AuthRequiredError`, `AdapterClosedError`, `TransformationViolationError`, `SchemaConformanceError`.
  - `mempalace/searcher.py:26` — `SearchError` for unrecoverable search problems.
- **Validation in `mempalace/config.py`** uses `ValueError` with descriptive messages — `sanitize_name`, `sanitize_kg_value`, `sanitize_content` all raise `ValueError(f"{field_name} ...")` for null bytes, length overflows, path traversal, and bad characters.
- **Cross-platform graceful degradation** uses tuple-except for OS quirks: `except (OSError, NotImplementedError): pass` after `chmod(0o600)` calls (`mempalace/config.py:232`, `mempalace/mcp_server.py:121`) — Windows lacks Unix permissions.
- **API boundary translation**: `search_memories` catches all backend exceptions and returns `{"error": str(e)}` so MCP callers never see raw tracebacks (`mempalace/searcher.py:304+`); the CLI `search()` *prints* and re-raises `SearchError`.
- **Defensive fallbacks**: closet expansion (`_expand_with_neighbors`, `mempalace/searcher.py:175`) catches `Exception` and returns the matched drawer alone — search must never break because a side-channel failed.

## Logging

Stdlib `logging` only — no structured logger, no `print` for diagnostics (CLI uses `print` for human-facing output).

- **Two namespaces** in use:
  - `logger = logging.getLogger(__name__)` — most modules (`mempalace/backends/chroma.py:23`, `mempalace/sweeper.py:50`, `mempalace/sources/registry.py:29`, `mempalace/room_detector_local.py:19`).
  - `logger = logging.getLogger("mempalace_mcp")` — the MCP request path (`mempalace/mcp_server.py:76`, `mempalace/searcher.py:23`, `mempalace/query_sanitizer.py:24`) shares one log namespace so the server can route them together.
- **Telemetry suppression** at package import: `logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)` (`mempalace/__init__.py:11`).
- **basicConfig** is set exactly once in the MCP entry point: `logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)` (`mempalace/mcp_server.py:75`) — `stream=sys.stderr` is critical because stdout carries the JSON-RPC protocol.
- **`%`-formatting** for log calls: `logger.warning("Quarantined stale HNSW segment %s ...", seg_dir, ...)` (`mempalace/backends/chroma.py:122`) — defers string interpolation.
- `logger.exception(...)` is used inside `except` blocks to keep the traceback (`mempalace/backends/chroma.py:130, 163`).

## Module-Level Patterns

- **Order**: shebang (entry-point modules only) → module docstring → stdlib imports → third-party imports → local imports → module constants → logger → public API.
- **Module constants** live near the top, regex patterns precompiled at import time:
  - `_TOKEN_RE = re.compile(r"\w{2,}", re.UNICODE)` (`mempalace/searcher.py:30`)
  - `_SAFE_NAME_RE = re.compile(r"^(?:[^\W_]|[^\W_][\w .'-]{0,126}[^\W_])$")` (`mempalace/config.py:19`)
  - `_REQUIRED_OPERATORS = frozenset({"$eq", "$ne", "$in", "$nin", "$and", "$or", "$contains"})` (`mempalace/backends/chroma.py:26`).
- **Lazy imports inside CLI handlers** to defer heavy imports (chromadb, miner, sentence-transformers) until the relevant command runs — see `cmd_init` (`mempalace/cli.py:71-75`) and `cmd_mine` (`mempalace/cli.py:122-135`).
- **Optional dependencies** (`autocorrect`) declared as an `optional-dependencies` extra group in `pyproject.toml` — imported only inside the function that uses it.
- **Argparse pattern**: each `cmd_*` function takes a single `args` namespace; the dispatch table at the bottom of `main()` routes commands:

```730:743:mempalace/cli.py
    dispatch = {
        "init": cmd_init,
        "mine": cmd_mine,
        "split": cmd_split,
        "search": cmd_search,
        "sweep": cmd_sweep,
        "mcp": cmd_mcp,
        "compress": cmd_compress,
        "wake-up": cmd_wakeup,
        "repair": cmd_repair,
        "migrate": cmd_migrate,
        "status": cmd_status,
    }
    dispatch[args.command](args)
```

## I/O & Filesystem

- **`pathlib.Path`** is preferred for new code (`mempalace/config.py`, `mempalace/cli.py`, `mempalace/mcp_server.py`).
- **`os.path` still appears** for ChromaDB-adjacent code that interoperates with stat/inode checks (`mempalace/mcp_server.py:181-185`, `mempalace/backends/chroma.py:88-115`).
- **Encoding**: `open(..., "w", encoding="utf-8")` is explicit when writing JSON (`mempalace/config.py:226, 252`); JSON dumps use `ensure_ascii=False`.
- **Permissions**: every file/dir under `~/.mempalace/` is locked down with `chmod(0o600)` (files) or `chmod(0o700)` (dirs), wrapped in `try/except (OSError, NotImplementedError)` for Windows.
- **Atomic-create with restricted perms** uses `os.open(..., O_CREAT|O_WRONLY, 0o600)` to avoid TOCTOU races (`mempalace/mcp_server.py:128, 155`).

## Data Classes & Value Objects

- **`@dataclass(frozen=True)`** for typed result objects — `PalaceRef`, `HealthStatus`, `QueryResult`, `GetResult` (`mempalace/backends/base.py:62-165`). Mutable `@dataclass` for resolver helpers (`_IncludeSpec`).
- **No Pydantic** — input validation is done by the explicit `sanitize_*` functions in `mempalace/config.py`.
- **No async** in source code (all modules are sync). MCP transport is a synchronous JSON-RPC stdio loop.

## Public API Surface

`mempalace/__init__.py` exports **only** the version:

```1:27:mempalace/__init__.py
"""MemPalace — Give your AI a memory. No API key required."""

import logging

from .version import __version__  # noqa: E402

# chromadb telemetry: posthog capture() was broken in 0.6.x causing noisy stderr
# warnings ("capture() takes 1 positional argument but 3 were given"). In 1.x the
# posthog client is a no-op stub, so this is now harmless — kept as a guard in
# case future chromadb versions re-introduce real telemetry calls.
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
```

`__all__ = ["__version__"]`. Everything else is reached by explicit submodule import (`from mempalace.searcher import search_memories`, `from mempalace.backends.chroma import ChromaBackend`). Console script `mempalace = "mempalace.cli:main"` and entry-point group `mempalace.backends` are declared in `pyproject.toml`.

## Commit & PR Conventions

- **Conventional Commits** required (`CONTRIBUTING.md`, `CLAUDE.md`): `feat:`, `fix:`, `docs:`, `test:`, `ci:`, `bench:`, `refactor(scope):`, `chore:`. Recent log shows scoped variants in heavy use: `fix(searcher):`, `test(backends):`, `refactor(sources):`, `feat(backends):`.
- PRs target the `develop` branch, not `main` (`CONTRIBUTING.md:58`); CI runs on push/pr to both `main` and `develop`.
- All tests must pass before opening a PR; no API keys or network access in tests (`CONTRIBUTING.md:22`).
- One-shot commands required before commit: `pytest tests/ -v`, `ruff check .`, `ruff format --check .`.

## Design Principles That Bind Every Change

From `CLAUDE.md` (non-negotiable for every PR):

- **Verbatim always** — never summarize, paraphrase, or lossy-compress user data. Sanitizers in `mempalace/config.py` validate but do not transform content.
- **Incremental only** — append-only ingest after the initial build. No destructive rebuilds; a crash mid-write must leave the existing palace untouched.
- **Entity-first** — keyed by real names with disambiguation (DOB, ID, context).
- **Local-first, zero API** — no cloud dependency, no API key required for core memory ops.
- **Performance budgets** — hooks under 500 ms; startup injection under 100 ms.
- **Privacy by architecture** — no telemetry, no phone-home; ChromaDB telemetry is silenced at import.
- **Background everything** — filing, indexing, timestamps run via hooks; nothing interrupts the user's conversation.
- **Dependencies stay thin** — only `chromadb>=1.5.4,<2` and `pyyaml>=6.0,<7` runtime; `pytest`, `pytest-cov`, `ruff`, `psutil` for dev (`pyproject.toml:29-56`). Adding a new runtime dep requires explicit discussion (`CONTRIBUTING.md:66`).

---

*Convention analysis: 2026-04-19*

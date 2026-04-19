# Testing Patterns

**Analysis Date:** 2026-04-19

## Test Framework

**Runner:**
- `pytest >= 7.0` — declared in both `[project.optional-dependencies] dev` and `[dependency-groups] dev` in `pyproject.toml`.
- Config block `[tool.pytest.ini_options]` in `pyproject.toml`:
  - `testpaths = ["tests"]`
  - `pythonpath = ["."]`
  - `addopts = "-m 'not benchmark and not slow and not stress'"` — default invocation skips heavy markers.
  - `markers = ["benchmark", "slow", "stress"]` — registered to silence pytest's "unknown mark" warning.

**Plugins detected:**
- `pytest-cov >= 4.0` — coverage harness used in CI.
- **No** `pytest-mock`, `pytest-benchmark`, `pytest-xdist`, `pytest-asyncio` — mocking is done with stdlib `unittest.mock` + the built-in `monkeypatch` fixture; benchmark timing is hand-rolled (`time.perf_counter`) inside the marker-gated tests under `tests/benchmarks/`.

**Assertion style:**
- Plain `assert` (pytest rewrites). `pytest.raises(ValueError)` for negative cases (`tests/test_config.py:57-68`).

**Run commands** (canonical, from `CLAUDE.md` and `.github/workflows/ci.yml`):

```bash
# Default unit-test run (excludes the on-disk benchmarks subtree)
python -m pytest tests/ -v --ignore=tests/benchmarks

# With coverage (matches CI invocation)
python -m pytest tests/ -v --ignore=tests/benchmarks \
  --cov=mempalace --cov-report=term-missing --cov-fail-under=80 --durations=10

# Scale benchmarks (separate suite under tests/benchmarks/)
uv run pytest tests/benchmarks/ -v --bench-scale=small -m "benchmark and not slow"
uv run pytest tests/benchmarks/ -v --bench-scale=medium --bench-report=results.json
```

## Test Directory Layout

Tests **mirror the `mempalace/` source structure**, one `test_<module>.py` per source module (`CLAUDE.md` *Tests* convention).

```
tests/
  conftest.py                              # global fixtures + HOME isolation
  test_backends.py, test_cli.py, test_config.py, test_dialect.py, ...
  test_mcp_server.py                       # 723 lines, dispatcher coverage
  test_searcher.py, test_hybrid_search.py  # search algorithm tests
  test_knowledge_graph.py, test_kg_thread_safety.py
  test_palace_graph.py, test_palace_graph_tunnels.py
  test_save_hook_mines.py, test_save_hook_verbose.py
  test_readme_claims.py                    # docs-claims-vs-code consistency
  test_version_consistency.py              # version.py vs pyproject.toml
  benchmarks/
    conftest.py                            # --bench-scale / --bench-report options
    data_generator.py, report.py
    test_*_bench.py                        # 9 modules, ~106 tests
    test_chromadb_stress.py, test_recall_threshold.py
```

**Counts** (`grep -rE '^def test_|^    def test_' tests/`): **51 unit-test files / ~1033 functions** in `tests/`, plus **14 files / ~43 functions** in `tests/benchmarks/` (~1076 total).

## Test Structure

Tests use a **hybrid xUnit + functional** style — class-based grouping when several tests share setup intent, plain top-level functions when not.

**Class-based grouping** (most common pattern, `tests/test_dialect.py:11-37`):

```typescript
class TestPlainTextCompression:
    def test_compress_basic(self):
        d = Dialect()
        result = d.compress("We decided to use GraphQL instead of REST for the API layer.")
        assert isinstance(result, str)
        assert "|" in result

    def test_compress_with_metadata(self):
        d = Dialect()
        result = d.compress(
            "Authentication now uses JWT tokens.",
            metadata={"wing": "project", "room": "backend"},
        )
        assert "project" in result
```

**Top-level functions** for short test sets — `def test_default_config(): cfg = MempalaceConfig(config_dir=tempfile.mkdtemp()); assert "palace" in cfg.palace_path` (`tests/test_config.py:9-12`). Modules open with a docstring describing scope and noting "uses real ChromaDB" vs "all mocked" — see `tests/test_searcher.py:1-6`, `tests/test_palace_graph.py:1-4`.

## Fixture Catalog

**`tests/conftest.py`** (global, **session HOME isolation happens at module load**):

| Fixture | Scope | Provides |
|---|---|---|
| `_isolate_home` | session, autouse | Redirects `HOME`/`USERPROFILE`/`HOMEDRIVE`/`HOMEPATH` to a session temp dir **before** any `mempalace` import; restores on teardown. Critical because module-level `_kg = KnowledgeGraph()` in `mcp_server.py` would otherwise touch `~/.mempalace/`. |
| `_reset_mcp_cache` | function, autouse | Clears `mcp_server._client_cache` / `_collection_cache` before and after every test so cached ChromaDB handles never leak across tests. |
| `tmp_dir` | function | `tempfile.mkdtemp(prefix="mempalace_test_")` with `shutil.rmtree(..., ignore_errors=True)` cleanup. |
| `palace_path` | function | An empty palace directory inside `tmp_dir`. |
| `config` | function | `MempalaceConfig(config_dir=...)` writing a `config.json` that points at `palace_path`. |
| `collection` | function | A `chromadb.PersistentClient` collection in the temp palace; deletes the collection on teardown. |
| `seeded_collection` | function | `collection` pre-populated with 4 representative drawers (auth/db/frontend/planning) — the canonical "what does a populated palace look like" fixture used by search tests. |
| `kg` | function | Isolated `KnowledgeGraph` over a temp SQLite file. |
| `seeded_kg` | function | `kg` pre-loaded with sample triples (Alice/Max family + work history). |

**`tests/benchmarks/conftest.py`** (scale-suite specific):

| Fixture | Scope | Provides |
|---|---|---|
| `bench_scale` | session | Reads `--bench-scale` (`small`/`medium`/`large`/`stress`); defaults to `small`. |
| `bench_report_path` | session | Reads `--bench-report` JSON output path. |
| `palace_dir`, `kg_db`, `config_dir`, `project_dir` | function | Per-test isolated directories under `tmp_path`. |
| `bench_results` | session | `BenchmarkResults` collector consumed by `pytest_terminal_summary` to write JSON benchmark reports. |

The benchmarks `conftest.py` also defines `pytest_addoption` (`--bench-scale`, `--bench-report`) and `pytest_terminal_summary` for end-of-session JSON reports stamped with git SHA, Python version, ChromaDB version, OS, and CPU count (`tests/benchmarks/conftest.py:13-144`).

## Common Patterns

- **Temp palace** — three paths: `palace_path` from `tests/conftest.py` (preferred), pytest's builtin `tmp_path` (`tests/test_searcher.py:42`, `tests/test_hybrid_search.py:60`), or `palace_dir` from `tests/benchmarks/conftest.py` for scale tests.
- **Windows ChromaDB file-lock** — the cache-invalidation test that deletes `chroma.sqlite3` is platform-skipped (`@pytest.mark.skipif(sys.platform == "win32", ...)` at `tests/test_mcp_server.py:789-792`) because Windows holds the file open while the cached client is alive. CI drops the coverage gate to 80% on **all** OSes (`.github/workflows/ci.yml:21-41`); the pyproject `fail_under = 85` applies to local runs only.
- **Embedding mocks** — none. Tests use **real ChromaDB embeddings** (default `all-MiniLM-L6-v2`). The harness deliberately avoids mocking the embedder because retrieval quality is the product (`CLAUDE.md` *verbatim always*, *100% recall is the design requirement*).
- **MCP transport mocking** — protocol tests call `handle_request(...)` directly with synthetic JSON-RPC dicts (`tests/test_mcp_server.py:46-107`); module globals are swapped via `monkeypatch.setattr(mcp_server, "_config", config)` (helper at `tests/test_mcp_server.py:16-21`).
- **Mocking strategy** is stdlib only: `unittest.mock.MagicMock`/`patch` for collection mocks (`tests/test_searcher.py:8`), `monkeypatch.setattr`/`setenv` for globals and env vars, and `with patch.dict("sys.modules", {"chromadb": MagicMock()}):` to stub heavy modules at import time (`tests/test_palace_graph.py:27-34`).
- **Parametrize** is heavy in `tests/benchmarks/` (`@pytest.mark.parametrize("n_drawers", [200, 1_000, 5_000])` — `tests/benchmarks/test_search_bench.py:23`, `test_layers_bench.py:37`, `test_knowledge_graph_bench.py:21`) and rare in unit tests.

## Markers

Defined in `[tool.pytest.ini_options].markers` (`pyproject.toml:84-88`); excluded from default runs by `addopts`:

| Marker | Used in | Meaning |
|---|---|---|
| `@pytest.mark.benchmark` | `tests/benchmarks/test_*_bench.py` (every class) | Scale/performance tests; run only when explicitly selected. |
| `@pytest.mark.slow` | reserved | Tests taking >30 s even at small scale. |
| `@pytest.mark.stress` | `tests/benchmarks/test_chromadb_stress.py`, `test_recall_threshold.py` | Destructive scale tests (100K+ drawers); local-only. |

## Coverage

`[tool.coverage.run]` and `[tool.coverage.report]` in `pyproject.toml`:

- `source = ["mempalace"]` — only the package is measured (CLI, MCP server, backends).
- `fail_under = 85` (local default).
- `show_missing = true` — `term-missing` listing of uncovered lines.
- `exclude_lines = ["if __name__", "pragma: no cover"]`.
- **No** `branch = true` — coverage is line-based.

CI **overrides** to `--cov-fail-under=80` (`.github/workflows/ci.yml:21, 31, 41`) on every OS, not just Windows. The 80% number is the floor that survives the Windows ChromaDB file-lock cleanup pattern; locally the bar is 85%.

## Test Types

- **Unit** — `tests/test_<module>.py` (~50 files). Mostly real-component; mocks reserved for error paths in `mempalace/searcher.py`, the entire `palace_graph` module, and cases where real ChromaDB would download embeddings unnecessarily.
- **Integration** — search + ChromaDB end-to-end through the `seeded_collection` fixture (`tests/test_searcher.py`, `tests/test_hybrid_search.py`); MCP loop via `handle_request` (`tests/test_mcp_server.py`).
- **E2E / scale benchmarks** — `tests/benchmarks/`, marker-gated, real ChromaDB at 1K → 100K drawers, driven by `tests/benchmarks/data_generator.py` with seeded RNG and *planted needles* for measurable recall.

**External benchmarks** — `benchmarks/` (top-level, **not pytest**) hosts academic-dataset runners invoked directly with `python`:

| Script | Dataset | Measures |
|---|---|---|
| `benchmarks/longmemeval_bench.py` | LongMemEval (500 q) | R@5/R@10/NDCG@10 — 96.6% raw, 100% w/ hybrid_v4+Haiku rerank |
| `benchmarks/locomo_bench.py` | LoCoMo (1,986 multi-hop QA) | R@10 by category, multi-hop reasoning |
| `benchmarks/convomem_bench.py` | ConvoMem (75K+ pairs) | Recall by category — 92.9% verbatim |
| `benchmarks/membench_bench.py` | MemBench (ACL 2025, 8,500 items) | R@5 by category — 80.3% overall |

Reference results: `benchmarks/results_*.json[l]`; reproduction guide: `benchmarks/README.md`; integrity notes: `benchmarks/BENCHMARKS.md`. Ruff lint is **excluded** from this directory (`pyproject.toml:68`).

## CI Test Matrix

`.github/workflows/ci.yml` has four jobs:

| Job | OS | Python | Coverage gate |
|---|---|---|---|
| `test-linux` | `ubuntu-latest` | `3.9`, `3.11`, `3.13` (matrix) | `--cov-fail-under=80` |
| `test-windows` | `windows-latest` | `3.9` | `--cov-fail-under=80` |
| `test-macos` | `macos-latest` | `3.9` | `--cov-fail-under=80` |
| `lint` | `ubuntu-latest` | `3.11` | `ruff check .` + `ruff format --check .` (pinned `ruff>=0.4.0,<0.5`) |

All test jobs run `pip install -e ".[dev]"` then the canonical `python -m pytest tests/ -v --ignore=tests/benchmarks --cov=mempalace --cov-report=term-missing --cov-fail-under=80 --durations=10`. Triggers: push & PR to `main` and `develop`.

## Representative Snippets

**Mock-based error path** with `unittest.mock` + `patch`:

```77:86:tests/test_searcher.py
    def test_search_memories_query_error(self):
        """search_memories returns error dict when query raises."""
        mock_col = MagicMock()
        mock_col.query.side_effect = RuntimeError("query failed")

        with patch("mempalace.searcher.get_collection", return_value=mock_col):
            result = search_memories("test", "/fake/path")
        assert "error" in result
        assert "query failed" in result["error"]
```

**HOME isolation that runs before any `mempalace` import** — the trick that lets module-level `KnowledgeGraph()` initialisation be safe:

```19:34:tests/conftest.py
_original_env = {}
_session_tmp = tempfile.mkdtemp(prefix="mempalace_session_")

for _var in ("HOME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH"):
    _original_env[_var] = os.environ.get(_var)

os.environ["HOME"] = _session_tmp
os.environ["USERPROFILE"] = _session_tmp
os.environ["HOMEDRIVE"] = os.path.splitdrive(_session_tmp)[0] or "C:"
os.environ["HOMEPATH"] = os.path.splitdrive(_session_tmp)[1] or _session_tmp

# Now it is safe to import mempalace modules that trigger initialisation.
import chromadb  # noqa: E402
import pytest  # noqa: E402

from mempalace.config import MempalaceConfig  # noqa: E402
from mempalace.knowledge_graph import KnowledgeGraph  # noqa: E402
```

## Known Platform Quirks

- **Windows + ChromaDB file lock** — `chroma.sqlite3` stays open while a cached `PersistentClient` is alive, blocking `os.remove()` / `shutil.rmtree`. DB-deletion tests (`tests/test_mcp_server.py:789-792`) are `skipif(sys.platform == "win32", ...)`. The 80% CI coverage floor reflects this; locally the bar stays at 85%.
- **macOS arm64 + chromadb 0.x hnswlib** — historical SIGSEGV crashes on `count()`/`query()` resolved by upgrading to `chromadb>=1.5.4` (commentary at `mempalace/__init__.py:13-26`). The runtime dep enforces the minimum.
- **MCP stdio protection** — `mempalace/mcp_server.py:34-43` redirects stdout → stderr at FD level before heavy imports; tests run under the HOME-isolated env so this prelude is harmless in pytest.

---

*Testing analysis: 2026-04-19*

# Technology Stack

**Analysis Date:** 2026-04-19

MemPalace is a **local-first Python library + CLI + MCP server**. Distributed on PyPI as `mempalace==3.3.0`. Single source-of-truth version lives in `mempalace/version.py` and is mirrored to `pyproject.toml`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `.codex-plugin/plugin.json` (enforced by `.github/workflows/version-guard.yml`).

## Languages

**Primary:**
- Python — `requires-python = ">=3.9"` (`pyproject.toml:6`). CI matrix proves support on 3.9, 3.11, 3.13; classifiers extend the contract to 3.10, 3.12, 3.14.

**Secondary:**
- Bash — Claude Code / Codex hooks: `hooks/mempal_save_hook.sh`, `hooks/mempal_precompact_hook.sh`, `.devcontainer/post-create.sh`.
- TypeScript / Vue — docs site under `website/` (separate dev stack, built via Bun + VitePress in `.github/workflows/deploy-docs.yml`).

## Runtime

**Environment:**
- CPython 3.9+ on Linux, macOS, Windows. ChromaDB ships `cp39-abi3` wheels (`uv.lock:343-348`) so a single binary covers every supported Python.

**Package Manager:**
- uv (lockfile `uv.lock` is committed, ~800 KB).
- pip remains a first-class install path (`pip install -e ".[dev]"` is the documented dev setup in `CLAUDE.md` and `.devcontainer/post-create.sh`).

**Lockfile:** `uv.lock` present.

## Frameworks

**Core (runtime, hard deps):**
The full runtime dep set is just two packages — see `pyproject.toml:29-32`:
- `chromadb >=1.5.4,<2` — vector store (resolved to 1.5.7 in `uv.lock:299-348`). Used at `mempalace/backends/chroma.py:9`.
- `pyyaml >=6.0,<7` — YAML config parsing in `mempalace/config.py`.

**Testing:**
- `pytest >=7.0` (`pyproject.toml:52`; resolves to 8.4.2 on py3.9, 9.0.3 on py3.10+).
- `pytest-cov >=4.0` (resolved to 7.1.0).

**Build/Dev:**
- `hatchling` build backend (`pyproject.toml:58-63`); wheel packages = `["mempalace"]`.
- `ruff >=0.4.0` (`pyproject.toml:52`). CI and pre-commit pin `>=0.4.0,<0.5` (`.github/workflows/ci.yml:49`, `.devcontainer/post-create.sh:10`, `.pre-commit-config.yaml:6`) — `pyproject` only sets a floor, the upper bound is enforced at install time so contributors don't drift ahead of CI.
- `psutil >=5.9` — used by perf/scale tests in `tests/`.
- `pre-commit` — installed by `.devcontainer/post-create.sh:12-13`; config at `.pre-commit-config.yaml`.

## Key Dependencies

**Critical (transitively via chromadb):**
The hard-dep list is intentionally small, but `chromadb` pulls a large subtree (`uv.lock:299-348`). Notable transitive deps that affect runtime behavior:

- `onnxruntime` (1.20.1 / 1.24.x) — runs ChromaDB's default embedding model. Source of historical macOS arm64 segfaults documented in `mempalace/__init__.py:13-25`.
- `numpy` (2.x) — vector arithmetic.
- `httpx`, `grpcio`, `kubernetes` — pulled in but only used when ChromaDB runs in client/server mode (MemPalace uses `PersistentClient`).
- `tokenizers`, `posthog`, `opentelemetry-*` — bundled with ChromaDB. Posthog telemetry is muted at import time (`mempalace/__init__.py:11`).

**Infrastructure (stdlib-only):**
MemPalace itself imports nothing else from PyPI for its core. Notable stdlib choices:
- `sqlite3` — knowledge graph at `mempalace/knowledge_graph.py:41` (no ORM, raw SQL with WAL mode).
- `urllib.request` — optional outbound HTTP at `mempalace/closet_llm.py:43-44` and `mempalace/entity_registry.py:20`. No `httpx` / `requests` direct dependency.
- `argparse` — CLI parsing in `mempalace/cli.py:33` and `mempalace/mcp_server.py:45`.
- `fcntl` / `msvcrt` — cross-platform mine locks in `mempalace/palace.py:289-307`.
- `importlib.metadata` — entry-point backend discovery in `mempalace/backends/registry.py:18`.

## Configuration

**Project metadata:** `pyproject.toml`
- `[project]` — name, version, deps, entry points, scripts.
- `[project.scripts] mempalace = "mempalace.cli:main"` — one console script.
- `[project.entry-points."mempalace.backends"] chroma = "mempalace.backends.chroma:ChromaBackend"` — pluggable storage backend group (RFC 001).
- `[project.entry-points."mempalace.sources"]` — empty registration table for third-party source adapters (RFC 002).
- `[project.optional-dependencies] dev` and `spellcheck` (autocorrect>=2.0).
- `[dependency-groups] dev` — uv-style mirror of the `dev` extra.

**Build:** `[build-system] requires = ["hatchling"]` + `[tool.hatch.build.targets.wheel] packages = ["mempalace"]`.

**Lint/format:** `[tool.ruff]` block (`pyproject.toml:65-78`):
- `line-length = 100`
- `target-version = "py39"`
- `extend-exclude = ["benchmarks"]`
- `[tool.ruff.lint] select = ["E", "F", "W", "C901"]`, `ignore = ["E501"]`
- `[tool.ruff.lint.mccabe] max-complexity = 25`
- `[tool.ruff.format] quote-style = "double"`

**Test runner:** `[tool.pytest.ini_options]` (`pyproject.toml:80-88`):
- `testpaths = ["tests"]`, `pythonpath = ["."]`
- `addopts = "-m 'not benchmark and not slow and not stress'"` — slow/scale tests are opt-in.
- Custom markers: `benchmark`, `slow`, `stress` (≥30s, destructive 100K+ drawer tests).

**Coverage:** `[tool.coverage.run] source = ["mempalace"]`; `[tool.coverage.report] fail_under = 85`, excludes `if __name__` and `pragma: no cover`. CI invokes coverage with `--cov-fail-under=80` (note: lower than the project setting; see `.github/workflows/ci.yml:21`) — Windows runner is the limiting factor per `CLAUDE.md:105` ("80% on Windows due to ChromaDB file lock cleanup").

**Pre-commit:** `.pre-commit-config.yaml`
- `astral-sh/ruff-pre-commit` rev `v0.4.10` — must stay in lock-step with CI ruff pin.
- Hooks: `ruff --fix`, `ruff-format`.

**Devcontainer:** `.devcontainer/devcontainer.json`
- Base image `mcr.microsoft.com/devcontainers/python:3.11`.
- Feature `ghcr.io/devcontainers/features/github-cli:1`.
- VS Code extensions: `ms-python.python`, `ms-python.debugpy`, `charliermarsh.ruff`.
- `postCreateCommand = "bash .devcontainer/post-create.sh"` → `pip install -e ".[dev]"` + `pip install "ruff>=0.4.0,<0.5"` + `pre-commit install`.

## Platform Requirements

**Development:**
- Python 3.9+, ~300 MB free disk for ChromaDB's bundled embedding model (`README.md:158`).
- macOS, Linux, or Windows. CI proves all three (`.github/workflows/ci.yml`).

**Production:**
- Same. MemPalace is a desktop / single-machine package; there is no "server" deployment target. All persistence is on local disk under the user-chosen palace dir and `~/.mempalace/`.

## CLI Entry Points

**Console scripts (from `pyproject.toml:39-40`):**
- `mempalace` → `mempalace.cli:main` — single dispatcher with subcommands defined in `mempalace/cli.py`: `init`, `mine`, `sweep`, `search`, `wakeup`, `split`, `migrate`, `status`, `repair`, `hook`, `instructions`, `mcp`, `compress`.

**Module entry points:**
- `python -m mempalace` → `mempalace/__main__.py` → `cli.main()`.
- `python -m mempalace.mcp_server` — MCP stdio server (used by Claude Code / Codex plugin manifests).
- `python -m mempalace.diary_ingest` — diary ingest.
- `python -m mempalace.closet_llm` — optional LLM closet rebuild.

## Native / GPU Deps

**Optional GPU:** None at the application layer. ChromaDB's onnxruntime can use CoreML / CUDA execution providers transparently; MemPalace neither enables nor configures them.

**Native binaries shipped via ChromaDB wheel:** `chromadb_rust_bindings.abi3.so` (HNSW + compactor) plus `onnxruntime` shared libs. macOS arm64 historically segfaulted in the 0.x HNSW binding; the `chromadb >=1.5.4` floor at `pyproject.toml:30` is the fix (see comment in `mempalace/__init__.py:13-25`).

## CI/CD

**Platform:** GitHub Actions. Three active workflows under `.github/workflows/`:

| Workflow | File | Purpose |
|---|---|---|
| Tests | `ci.yml` | Test matrix on Linux (py 3.9 / 3.11 / 3.13), Windows (3.9), macOS (3.9). Runs `pytest --ignore=tests/benchmarks --cov=mempalace --cov-fail-under=80 --durations=10`. Separate `lint` job: `ruff check .` + `ruff format --check .` with ruff `>=0.4.0,<0.5` on py 3.11. |
| Version Guard | `version-guard.yml` | Cross-checks `mempalace/version.py`, `pyproject.toml`, `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`. On `v*` tag pushes also verifies tag matches manifest (semver pre-release tags `vX.Y.Z-rcN` skip the strict check). |
| Deploy Docs | `deploy-docs.yml` | Builds `website/` via Bun 1.1.38 + `bun run docs:build` (VitePress) and pushes to GitHub Pages on `develop` branch pushes. |

`.github/workflows/bump-plugin-version.yml.disabled` — disabled auto-bump workflow (kept as a `.disabled` artifact, not active).

---

*Stack analysis: 2026-04-19*

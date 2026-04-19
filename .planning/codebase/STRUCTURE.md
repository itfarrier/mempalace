# MemPalace Directory Structure

**Analysis date:** 2026-04-19  •  **Version:** 3.3.0  •  **Focus:** arch (structure)

Companion to `ARCHITECTURE.md`. Maps every directory + key file, names the
conventions, and answers "where do I add X?".

## 1. Repository Root

```
mempalace/                       ← Python package (33 .py files, ~14 067 LoC)
hooks/                           ← Claude Code / Codex shell hooks (3 files)
tests/                           ← pytest suite (50 test_*.py + conftest.py + benchmarks/)
benchmarks/                      ← public reproduction harnesses + result JSONs
docs/                            ← long-form docs + RFCs + reference SQL schema
examples/                        ← runnable mini-tutorials + setup snippets
integrations/                    ← third-party integration scaffolding
landing/                         ← single-page marketing site (index.html + logo)
website/                         ← VitePress documentation site
assets/                          ← shared image assets
.github/                         ← CI workflows, issue templates, CODEOWNERS
.planning/                       ← codebase analysis docs (this folder)

AGENTS.md → CLAUDE.md            ← agent instructions (symlink)
CLAUDE.md                        ← design principles + project map (must-read)
README.md  CONTRIBUTING.md
MISSION.md  ROADMAP.md  CHANGELOG.md  SECURITY.md  LICENSE
pyproject.toml                   ← deps, entry points, ruff/pytest/coverage
uv.lock
```

## 2. `mempalace/` — Package Tree

```
mempalace/
├── __init__.py                  package init, ChromaDB telemetry mute, exports __version__
├── __main__.py                  python -m mempalace → cli.main()
├── version.py                   __version__ = "3.3.0"  (SSoT, 3 lines)
├── py.typed                     PEP 561 marker
│
├── cli.py                       argparse dispatcher (init/mine/sweep/search/compress/
│                                wake-up/split/hook/instructions/repair/mcp/migrate/status)
├── mcp_server.py                MCP JSON-RPC server, TOOLS dict (30 tools), WAL, stdio guard
├── hooks_cli.py                 in-process hook runner (session-start/stop/precompact)
├── instructions_cli.py          prints help text from instructions/*.md
│
├── config.py                    MempalaceConfig + sanitize_name / sanitize_kg_value / sanitize_content
├── query_sanitizer.py           strip prompt-contamination from search queries
│
├── palace.py                    get_collection, get_closets_collection, mine_lock, NORMALIZE_VERSION,
│                                SKIP_DIRS, build_closet_lines, file_already_mined
├── palace_graph.py              room traversal, find_tunnels, create/list/delete/follow_tunnels
│                                (tunnels.json atomic write)
├── searcher.py                  hybrid BM25 + vector search, closet boost, neighbor expansion
├── layers.py                    L0 identity / L1 essential story / L2 wing-room / L3 deep search
│
├── miner.py                     project-file ingest pipeline (chunk → entities → upsert)
├── convo_miner.py               transcript ingest pipeline (Claude/ChatGPT/Codex/Slack)
├── sweeper.py                   message-granular safety net for jsonl sessions (idempotent)
├── diary_ingest.py              one-drawer-per-day ingest for ~/daily_summaries/
│
├── normalize.py                 transcript format detection + noise-strip
├── dialect.py                   AAAK compression — closets, emotion codes, encode_zettel/file
├── general_extractor.py         decisions / preferences / milestones / problems / emotional
├── room_detector_local.py       folder-name → room mapping (no API)
├── entity_detector.py           multi-language people/project candidate extraction
├── entity_registry.py           persistent ~/.mempalace/entities.json + Wikipedia disambig
├── fact_checker.py              KG-aware contradiction / similar-name / stale-fact checker
├── spellcheck.py                opt-in autocorrect for user turns (extras: "spellcheck")
├── split_mega_files.py          split concatenated jsonl mega-files into per-session files
│
├── knowledge_graph.py           SQLite temporal triple store (~/.mempalace/knowledge_graph.sqlite3)
├── onboarding.py                first-run interactive setup, seeds entities + bootstrap files
│
├── repair.py                    scan / prune / rebuild ChromaDB HNSW index
├── dedup.py                     near-duplicate drawer cleanup (cosine-distance threshold)
├── migrate.py                   recover palace from a different ChromaDB version (SQLite-direct)
├── exporter.py                  palace → markdown tree (one file per wing/room)
├── closet_llm.py                opt-in LLM-generated closets (any OpenAI-compatible endpoint)
│
├── backends/                    ── pluggable storage adapters (RFC 001) ──
│   ├── __init__.py              module re-exports + entry-point registration
│   ├── base.py                  BaseBackend / BaseCollection / PalaceRef + common errors
│   ├── registry.py              register / get_backend / discover via mempalace.backends EP group
│   └── chroma.py                ChromaBackend (default) — quarantine_stale_hnsw, blob seq_id repair
│
├── sources/                     ── pluggable source adapters (RFC 002 §9 scaffolding) ──
│   ├── __init__.py              public surface re-exports
│   ├── base.py                  BaseSourceAdapter, SourceRef, DrawerRecord, AdapterSchema, errors
│   ├── registry.py              register / get_adapter / mempalace.sources EP group
│   ├── context.py               PalaceContext facade passed to adapters
│   └── transforms.py            reserved transformation reference impls (utf8/newline/whitespace/…)
│
├── i18n/                        ── locale resources (15 files: __init__.py + 14 BCP-47 JSONs) ──
│   ├── __init__.py              load_lang, t(), get_entity_patterns(languages=...)
│   └── {de, en, es, fr, hi, id, it, ja, ko, pt-br, ru, zh-CN, zh-TW}.json
│
└── instructions/                ── help text printed by `mempalace instructions <name>` ──
    └── {init, mine, search, status, help}.md
```

## 3. Top-Level Directories

```
hooks/                3 files     mempal_save_hook.sh, mempal_precompact_hook.sh, README.md
                                  (Claude Code Stop / PreCompact wrappers; in-process runner is
                                  mempalace/hooks_cli.py)

tests/               53 entries   conftest.py + 50 test_*.py mirroring source modules
                                  + benchmarks/ subdir (slow / benchmark / stress markers)

benchmarks/          17 files     BENCHMARKS.md, HYBRID_MODE.md, README.md
                                  4 harnesses: longmemeval_bench, locomo_bench,
                                  convomem_bench, membench_bench
                                  + lme_split_50_450.json + 8 results_*.json[l] (auditable raw data)

docs/                 5 entries   CLOSETS.md, HISTORY.md, schema.sql,
                                  rfcs/002-source-adapter-plugin-spec.md

examples/             5 files     basic_mining.py, convo_import.py,
                                  HOOKS_TUTORIAL.md, mcp_setup.md, gemini_cli_setup.md

integrations/         1 dir       openclaw/ (SKILL.md placeholder for the OpenClaw integration)

landing/              2 files     index.html (single-page marketing) + mempalace_logo.png

website/             VitePress    .vitepress/, concepts/ (6 md), guide/ (10 md),
                                  reference/ (7 md), public/, index.md, package.json, bun.lock

assets/               1 file      mempalace_logo.png

.github/             7 entries    workflows/ (ci.yml, deploy-docs.yml, version-guard.yml,
                                  bump-plugin-version.yml.disabled),
                                  ISSUE_TEMPLATE/ (bug, feature),
                                  CODEOWNERS, dependabot.yml, PULL_REQUEST_TEMPLATE.md

.planning/            this dir    codebase/ARCHITECTURE.md + codebase/STRUCTURE.md
```

## 4. Naming Conventions

- **Modules:** `snake_case.py` (`palace_graph.py`, `entity_registry.py`).
- **Classes:** `PascalCase` (`ChromaBackend`, `KnowledgeGraph`, `MemoryStack`, `PalaceContext`).
- **Functions / vars:** `snake_case` (`mine_lock`, `build_closet_lines`, `sanitize_kg_value`).
- **Module-private constants:** `_LEADING_UNDERSCORE` (`_DEFAULT_BACKEND`, `_WAL_FILE`, `_NOISE_TAGS`).
- **Public constants:** `UPPER_SNAKE` (`NORMALIZE_VERSION`, `SKIP_DIRS`, `CLOSET_CHAR_LIMIT`, `DEFAULT_KG_PATH`).
- **CLI commands:** kebab-case in argv (`wake-up`, `hook run`), snake_case in dispatch (`cmd_wakeup`, `cmd_hook`).
- **MCP tools:** `mempalace_<verb>_<noun>` snake_case (`mempalace_kg_add`, `mempalace_diary_write`, `mempalace_create_tunnel`).
- **Tests:** `tests/test_<module>.py` mirrors `mempalace/<module>.py`. Extras (`_extra`, `_unit`, `_size_cap`, `_visibility`, `_thread_safety`, `_lang_case`, `_protection`) extend the same module's coverage.
- **Hooks (shell):** `mempal_<event>_hook.sh` in `hooks/`.
- **Locales:** BCP 47 lowercase stems (`pt-br.json`, `zh-CN.json`); resolver is case-insensitive (`mempalace/i18n/__init__.py:_canonical_lang`).
- **Benchmarks:** `<dataset>_bench.py` + `results_<dataset>_<mode>_<topk>_<YYYYMMDD>_<hhmm>.json[l]`.
- **Commits:** conventional (`fix:`, `feat:`, `test:`, `docs:`, `ci:`, `refactor:`); ruff `E/F/W/C901`; double quotes; line length 100.

## 5. Where to Add What — Cookbook

| Goal | Touch this | Then |
|---|---|---|
| Add a CLI subcommand | `mempalace/cli.py` | Add `cmd_<name>(args)` + `sub.add_parser("<name>", ...)` + entry in the `dispatch` dict at the bottom of `main()` |
| Add an MCP tool | `mempalace/mcp_server.py` | Write a handler function; add a `TOOLS["mempalace_<verb>_<noun>"]` entry with `description` / `inputSchema` / `handler`; call `_wal_log` for writes; sanitize via `config.sanitize_*` |
| Add a storage backend | `mempalace/backends/base.py` (subclass `BaseBackend` + `BaseCollection`) | Register via `[project.entry-points."mempalace.backends"]` in `pyproject.toml`; add conformance test in `tests/test_backends.py` |
| Add a source adapter (RFC 002) | `mempalace/sources/base.py` (subclass `BaseSourceAdapter`) | Use `PalaceContext.upsert_drawer`; declare `declared_transformations`; register via `[project.entry-points."mempalace.sources"]`; never import `palace` directly |
| Modify search ranking | `mempalace/searcher.py` (`_bm25_scores`, `_hybrid_rank`, `_expand_with_neighbors`) | Verify with `tests/test_searcher.py` + `tests/test_hybrid_search.py` and the LongMemEval / LoCoMo benchmarks |
| Modify ingest (project files) | `mempalace/miner.py` | Bump `palace.NORMALIZE_VERSION` if the chunking/cleanup changes so existing drawers silently rebuild on next mine |
| Modify ingest (transcripts) | `mempalace/convo_miner.py` + `mempalace/normalize.py` | Add new transcript format to `normalize.normalize`; add tests in `tests/test_normalize.py` |
| Change input validation | `mempalace/config.py` (`sanitize_name`, `sanitize_kg_value`, `sanitize_content`) and/or `mempalace/query_sanitizer.py` | Add cases to `tests/test_config.py`, `tests/test_query_sanitizer.py` |
| Add a Claude Code / Codex hook | `hooks/mempal_<event>_hook.sh` | Read JSON from stdin, output JSON to stdout, ≤ 500 ms; document in `hooks/README.md` |
| Add an in-process hook event | `mempalace/hooks_cli.py` | Add to the `--hook` choices in `cli.py` (`session-start | stop | precompact`) |
| Add a benchmark | `benchmarks/<name>_bench.py` | Document in `benchmarks/README.md`; results land as `benchmarks/results_*.json[l]` |
| Add a language | `mempalace/i18n/<bcp47>.json` (must include `entity` section) | `entity_detector` auto-discovers via `get_entity_patterns(languages=...)`; tests in `tests/test_i18n.py` |
| Compress drawers via LLM | `mempalace/closet_llm.py` (opt-in) | Configure `LLM_ENDPOINT` / `LLM_KEY` / `LLM_MODEL` env vars or pass `--endpoint` / `--model` flags |
| Recover a corrupt palace | `mempalace/repair.py` (`scan` / `prune` / `rebuild`) or `mempalace/migrate.py` for cross-version | Backups go to `~/.mempalace/palace.backup.<ts>/` |
| Export the palace | `mempalace/exporter.py` | Streams in 1000-drawer batches → `output_dir/wing/room.md` |
| Add CI step | `.github/workflows/ci.yml` (test/lint), `deploy-docs.yml` (website), `version-guard.yml` (version SSoT) | |
| Update the website | `website/{guide,concepts,reference}/*.md` | VitePress build; deploy via `deploy-docs.yml` |
| Update agent guidance | `CLAUDE.md` (and the `AGENTS.md` symlink follows automatically) | |

## 6. File-Count Summary

| Directory | Python `.py` | Other | Total entries (excl. caches) |
|---|---:|---:|---:|
| `mempalace/` (top level only) | 33 | 1 (`py.typed`) | 38 (incl. 4 subdirs) |
| `mempalace/backends/` | 4 | 0 | 4 |
| `mempalace/sources/` | 5 | 0 | 5 |
| `mempalace/i18n/` | 1 | 14 (locale JSON) | 15 |
| `mempalace/instructions/` | 0 | 5 (`*.md`) | 5 |
| `tests/` | 50 + `conftest.py` | — | 53 (incl. `benchmarks/`) |
| `benchmarks/` | 4 (`*_bench.py`) | 13 (3 md + 1 split JSON + 8 result JSON/JSONL + 1 README) | 17 |
| `docs/` | 0 | 4 (3 md + 1 sql + `rfcs/`) | 4 + 1 RFC |
| `examples/` | 2 | 3 (md) | 5 |
| `integrations/openclaw/` | 0 | 1 (`SKILL.md`) | 1 |
| `landing/` | 0 | 2 | 2 |
| `website/` | 0 | ~28 md across `concepts/` (6) + `guide/` (10) + `reference/` (7) + index + theme | site tree |
| `hooks/` | 0 | 3 (2 sh + README) | 3 |
| `assets/` | 0 | 1 | 1 |
| `.github/` | 0 | 7 (3 workflows + 1 disabled + 2 issue templates + CODEOWNERS + dependabot + PR template) | 7 |

LoC reference points: `mcp_server.py` 1 713, `dialect.py` 1 091, `miner.py`
868, `cli.py` 747, `chroma.py` 641, `normalize.py` 603, `searcher.py` 505,
`layers.py` 502, `convo_miner.py` 502, `onboarding.py` 489, `knowledge_graph.py`
441, `backends/base.py` 370, `palace.py` 343, `config.py` 294. Whole package
~14 067 LoC; tests ~14 299 LoC.

## 7. Single-Source-of-Truth Files

- **`mempalace/version.py`** — `__version__` (3 lines). Enforced by `.github/workflows/version-guard.yml`; imported by `mempalace/__init__.py`, `cli.py`, `mcp_server.py`. `pyproject.toml` carries the same string for build metadata.
- **`pyproject.toml`** — dependencies (`chromadb>=1.5.4,<2`, `pyyaml`), `[project.scripts] mempalace = mempalace.cli:main`, `[project.entry-points."mempalace.backends"]` and `[project.entry-points."mempalace.sources"]`, ruff (`line-length=100`, `target-version="py39"`, `select=["E","F","W","C901"]`, `max-complexity=25`), pytest markers (`benchmark`/`slow`/`stress`), coverage threshold (85 %).
- **`mempalace/config.py`** — palace path (`~/.mempalace/palace`), default collection name, hall keywords, hook settings, all sanitizers. Anything user-tunable lives here.
- **`mempalace/palace.py`** — `NORMALIZE_VERSION` (bump to trigger silent re-mine), `SKIP_DIRS` (ingest skip-list), `CLOSET_CHAR_LIMIT`, `mine_lock` (the concurrency primitive), `_DEFAULT_BACKEND` (the only place a concrete backend is wired by name).
- **`CLAUDE.md`** (and `AGENTS.md` symlink) — the canonical statement of design principles ("verbatim always", "incremental only", "local-first, zero API", performance budgets, "crash mid-op leaves palace untouched"). Treat it as the spec; PRs that violate it should be rejected.
- **`docs/rfcs/002-source-adapter-plugin-spec.md`** — read-side adapter contract that `mempalace/sources/` implements; reference for any new ingest source.
- **`docs/schema.sql`** — KG SQLite schema reference (companion to `mempalace/knowledge_graph.py`).
- **`~/.mempalace/`** (runtime, not in repo) — `palace/` (chroma), `knowledge_graph.sqlite3`, `entities.json`, `tunnels.json`, `identity.txt`, `wal/write_log.jsonl`, `locks/`, `hook_state/`, `state/`. Everything per-user, everything local.

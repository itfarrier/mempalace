# MemPalace Architecture

**Analysis date:** 2026-04-19  •  **Version:** 3.3.0 (`mempalace/version.py`)  •  **Focus:** arch

## 1. Architectural Style

MemPalace is a **local-first, append-only, hexagonal-ish memory store**. The
domain core (palace ops, miners, search, knowledge graph, AAAK dialect)
depends only on a small set of abstract storage and source contracts; the
concrete adapters (`ChromaBackend`, future `BaseSourceAdapter`s) are loaded
at the edges via Python entry points.

- **Local-first, zero API.** No network, no telemetry, no cloud sync. The
  one optional outbound path is `closet_llm.py`, which is opt-in and
  user-configured (any OpenAI-compatible URL, including localhost).
- **Append-only ingest.** After the initial palace exists, every write is
  an upsert; deletes are surgical (`repair.py`, `dedup.py`). The CLAUDE.md
  invariant "a crash mid-operation must leave the existing palace
  untouched" is implemented by per-file locking + delete-then-insert
  ordering inside the lock (see §6).
- **Pluggable adapters.** Storage backends register on the
  `mempalace.backends` entry point; source adapters (RFC 002, scaffolded
  in `mempalace/sources/`) register on `mempalace.sources`. Core never
  imports concrete adapters by name — `palace.py` instantiates a
  `ChromaBackend()` as the default, every other call goes through the
  abstract `BaseBackend` / `BaseCollection` interface (`backends/base.py`).

## 2. Core Domain Model

```
WING (person | project | topic)
  └── ROOM (day | session | sub-topic)
        └── DRAWER (verbatim chunk, ≤ chunk_size chars, never paraphrased)

Parallel index layer:
  CLOSET — AAAK-compressed pointer lines (topic|entities|→drawer_ids)
           one closet per (wing, room), used as a search ranking signal

Parallel relationship layer:
  KNOWLEDGE GRAPH — temporal triples (subject, predicate, object,
                                       valid_from, valid_to) in SQLite
```

Drawers carry flat scalar metadata (chroma constraint, `RFC 001 §1.4`):
`source_file`, `chunk_index`, `wing`, `room`, `hall`, `entities`,
`normalize_version`, plus optional `adapter_name`/`adapter_version` once
miners migrate onto `BaseSourceAdapter`. Verbatim is sacred — drawers
store the user's original bytes after a declared transformation pipeline
(`mempalace/sources/transforms.py`).

## 3. Layered View

```
┌─────────────────────────────────────────────────────────────────┐
│ User / AI client                                                │
│   • shell  • Claude Code  • Codex CLI  • Cursor                 │
└──────┬───────────────────────────────────┬──────────────────────┘
       │ argv / interactive                │ JSON-RPC over stdio
┌──────▼──────────────────┐    ┌───────────▼──────────────────────┐
│ CLI dispatcher          │    │ MCP server                       │
│ mempalace/cli.py        │    │ mempalace/mcp_server.py          │
│ + hooks/*.sh            │    │ TOOLS dict (30 tools)            │
│ + hooks_cli.py          │    │ + WAL (~/.mempalace/wal/)        │
└──────┬──────────────────┘    └───────────┬──────────────────────┘
       │                                   │
┌──────▼───────────────────────────────────▼──────────────────────┐
│ Domain layer (palace ops, ingest, search, knowledge)            │
│   palace.py  palace_graph.py  layers.py  searcher.py            │
│   miner.py  convo_miner.py  sweeper.py  diary_ingest.py         │
│   dialect.py  normalize.py  query_sanitizer.py                  │
│   knowledge_graph.py  entity_registry.py  entity_detector.py    │
│   onboarding.py  repair.py  dedup.py  exporter.py  migrate.py   │
│   fact_checker.py  general_extractor.py  room_detector_local.py │
│   closet_llm.py  spellcheck.py  split_mega_files.py             │
└──────┬───────────────────┬───────────────┬──────────────────────┘
       │ BaseBackend       │ KG SQLite     │ filesystem
┌──────▼──────────────┐  ┌─▼─────────┐  ┌──▼────────────────────┐
│ Storage adapters    │  │ SQLite    │  │ Filesystem state      │
│ backends/base.py    │  │ knowledge │  │ ~/.mempalace/         │
│ backends/registry.py│  │ _graph    │  │   palace/  locks/     │
│ backends/chroma.py  │  │ .sqlite3  │  │   wal/  tunnels.json  │
│  + future: lance,…  │  │           │  │   hook_state/  state/ │
└──────┬──────────────┘  └───────────┘  └───────────────────────┘
       │ ChromaDB PersistentClient
┌──────▼──────────────────────────────────────────────────────────┐
│ ~/.mempalace/palace/  →  chroma.sqlite3 + HNSW segments         │
│   collections: mempalace_drawers, mempalace_closets             │
└─────────────────────────────────────────────────────────────────┘
```

## 4. Entry Points

| Entry point | File | Notes |
|---|---|---|
| Console script `mempalace` | `mempalace/cli.py` (`main`) | Declared in `pyproject.toml [project.scripts]` |
| Module run `python -m mempalace` | `mempalace/__main__.py` | Delegates to `cli.main()` |
| MCP server | `mempalace/mcp_server.py` (`main`) | Started by `claude mcp add mempalace -- python -m mempalace.mcp_server [--palace PATH]` |
| Hook entry (in-process) | `mempalace/hooks_cli.py` (`run_hook`) | Invoked by `mempalace hook run --hook ... --harness ...` |
| Hook entry (shell wrappers) | `hooks/mempal_save_hook.sh`, `hooks/mempal_precompact_hook.sh` | Read JSON on stdin, may shell out to `python -m mempalace mine` |
| Backend plugin | `[project.entry-points."mempalace.backends"]` → `chroma = mempalace.backends.chroma:ChromaBackend` | Registry: `mempalace/backends/registry.py` |
| Source plugin (RFC 002) | `[project.entry-points."mempalace.sources"]` (no first-party adapters yet) | Registry: `mempalace/sources/registry.py` |

## 5. Data-Flow Walkthroughs

### 5.1 `mempalace mine ~/projects/X` — project files

`cli.cmd_mine` → `miner.mine(path)` →
1. Load `mempalace.yaml` (wings/rooms config) via `room_detector_local`.
2. Walk dir, skip `palace.SKIP_DIRS`, honor `.gitignore`.
3. For each file: `palace.mine_lock(source_file)` (fcntl exclusive, `~/.mempalace/locks/<sha256>.lock`) → `palace.file_already_mined()` (mtime + `NORMALIZE_VERSION` gate) → if dirty, **delete prior drawers for that source then upsert new ones inside the same lock** (the "crash mid-op" invariant; the lock guarantees serialized delete→insert).
4. `dialect.encode_file()` produces AAAK closet pointer lines; `palace.build_closet_lines()` packs them up to `CLOSET_CHAR_LIMIT=1500` and upserts into `mempalace_closets`.
5. KG triples extracted by `entity_detector` are appended to `~/.mempalace/knowledge_graph.sqlite3` via `KnowledgeGraph.add_triple`.

### 5.2 `mempalace mine <dir> --mode convos` — transcripts

`cli.cmd_mine` (`mode=convos`) → `convo_miner.mine_conversations(path)` →
`normalize.normalize(filepath)` (auto-detects Claude.ai JSON, ChatGPT
`conversations.json`, Claude Code JSONL, Codex JSONL, Slack JSON; strips
noise tags and hook chrome) → exchange-pair chunking → `entity_detector`
+ `room_detector_local` route to wing/room → same lock + upsert path as
§5.1. The `sweeper.py` complements file-level mining at message
granularity (idempotent, resume-safe via timestamp cursor + deterministic
drawer IDs).

### 5.3 `mempalace search "..."` — hybrid retrieval

`cli.cmd_search` → `query_sanitizer.sanitize_query()` strips
prompt-contamination tail (system reminders, tool results) → `searcher.search_memories()`:
1. **Drawer floor.** Always run a vector query against `mempalace_drawers` with optional `wing`/`room` `where` clause.
2. **Closet signal.** Vector query `mempalace_closets`, parse `→drawer_id` references from pointer lines.
3. **BM25 lane.** `_bm25_scores()` over the same documents on the tokenized query.
4. **Hybrid rank.** `_hybrid_rank()` combines vector distance + BM25; closet hits add a rank-based boost when they agree (signal, never gate).
5. **Neighbor expansion.** `_expand_with_neighbors()` pulls adjacent chunks for context.
6. Returns verbatim drawer text + metadata. No LLM in the loop.

### 5.4 `mempalace wake-up` — L0–L3 stack

`cli.cmd_wakeup` → `layers.MemoryStack.wake_up(wing=None)` →
- **L0 Identity** (`Layer0`): `~/.mempalace/identity.txt` (user-authored).
- **L1 Essential Story** (`Layer1`, `MAX_DRAWERS=15`): top-ranked drawers across the palace (or scoped to `wing`).
- L0+L1 fits a **~600–900 token budget**; L2/L3 stay dormant until the agent calls `Layer2.search` (wing/room filtered) or `Layer3.search_raw` (full hybrid).

### 5.5 MCP tool call lifecycle

Client → JSON-RPC `initialize`/`tools/list`/`tools/call` over stdio →
`mcp_server` dispatcher looks up `TOOLS[name]["handler"]` (30 tools) →
handler validates inputs via `config.sanitize_*` + `query_sanitizer` →
domain call (`searcher`, `palace_graph`, `KnowledgeGraph`, palace upsert)
→ writes are best-effort logged to `~/.mempalace/wal/write_log.jsonl`
(`_wal_log`, opened `O_CREAT|O_APPEND|O_WRONLY` mode `0o600`, with
redaction of sensitive keys) → response. Stdout/stderr are swapped at
import time (`sys.stdout = sys.stderr`, `os.dup2(2, 1)`) to keep noisy
transitive imports (chromadb, onnxruntime, posthog) from corrupting the
JSON-RPC channel; the real stdout fd is restored in `main()` before the
protocol loop.

### 5.6 Hook trigger lifecycle

Claude Code/Codex fires `Stop` or `PreCompact` → shell wrapper in
`hooks/` reads JSON on stdin → counts human messages, throttles via
`~/.mempalace/hook_state/<session>_last_save` → on threshold, returns
`{"decision":"block","reason":"..."}` (verbose mode) or `{}` (silent),
optionally backgrounding `python -m mempalace mine $TRANSCRIPT_DIR &` for
auto-ingest. PreCompact always blocks because compaction is irreversible
context loss.

## 6. Key Abstractions

- **`BaseBackend`** (`backends/base.py`): factory that returns
  `BaseCollection` instances (`add`/`upsert`/`query`/`get`/`delete`/`count`).
  Implementations: `ChromaBackend` (`backends/chroma.py`, default).
  Discovery: explicit + entry-point group `mempalace.backends`.
- **`BaseSourceAdapter`** (`sources/base.py`, RFC 002): read-side
  contract. Yields typed `SourceItemMetadata` / `DrawerRecord` records.
  `PalaceContext` (`sources/context.py`) is the facade core passes in;
  adapters never import `palace` directly. Reserved transformations live
  in `sources/transforms.py`.
- **`KnowledgeGraph`** (`knowledge_graph.py`): SQLite-backed temporal
  triple store at `~/.mempalace/knowledge_graph.sqlite3`. `add_triple`,
  `invalidate(ended=...)`, `query_entity`, `timeline`, `stats`.
- **`MempalaceConfig`** (`config.py`): single source of truth for palace
  path, hall keywords, hook settings, sanitizers (`sanitize_name`,
  `sanitize_kg_value`, `sanitize_content`).

## 7. Performance Budgets (asserted in code/docs)

- **Hooks < 500 ms**, **startup < 100 ms**: declared in `CLAUDE.md` Design Principles. Enforced operationally via stdio swap + lazy imports in `mcp_server.py` and the small hook scripts.
- **Wake-up ~600–900 tokens (L0+L1)**: `mempalace/layers.py:13`, `:362`, `:380`. `Layer1.MAX_DRAWERS=15` caps L1 size.
- **Closet pack ≤ 1500 chars**: `palace.CLOSET_CHAR_LIMIT=1500`.
- **Coverage gate ≥ 85 %** (80 % on Windows): `pyproject.toml [tool.coverage.report]`, CI in `.github/workflows/ci.yml`.
- **Search latency**: tracked by `benchmarks/longmemeval_bench.py`, `locomo_bench.py`, `convomem_bench.py`, `membench_bench.py`; results in `benchmarks/results_*.json[l]`.

## 8. Concurrency & Locking

- **Per-file mine lock** (`palace.mine_lock`, `palace.py:275`): cross-platform exclusive lock (`fcntl.LOCK_EX` / `msvcrt.LK_LOCK`) keyed by sha256 of `source_file` under `~/.mempalace/locks/`. Wraps the whole delete+upsert cycle so two terminals can't interleave on the same file.
- **PID file guard for mine processes**: prevents stacking mine processes; cross-platform check (`os.kill(pid, 0)` on POSIX, broad OSError catch on Windows; see commits `a6b6e55`, `dfba247`, `fe6b889`).
- **MCP cache invalidation**: `mcp_server` watches `chroma.sqlite3` inode + mtime; if it changes (e.g., the CLI mined while the server was idle), it drops cached `PersistentClient`s and reopens.
- **Tunnels.json atomic write**: `palace_graph._save_tunnels` writes `tunnels.json.tmp` then `os.replace` (`palace_graph.py:269`), so a crash mid-write can never leave a partial file.
- **WAL append**: `mcp_server._wal_log` opens with `O_APPEND` so concurrent writers don't truncate; failures are logged and swallowed (memory operations never fail because logging failed).
- **KG SQLite**: single-writer, `check_same_thread=False`, `timeout=10`s — sufficient for hook + interactive workloads.
- **ChromaDB HNSW resilience**: `ChromaBackend.quarantine_stale_hnsw` (commit `0c38dea`) detects HNSW/sqlite drift and quarantines the bad segment so a corrupted index never crashes the whole palace; `_fix_blob_seq_ids` repairs SQLite BLOB `seq_id` mismatches.

## 9. Error / Failure Model

The "crash mid-op leaves palace untouched" invariant is enforced at three
layers:

1. **File-level**: `mine_lock` serializes `delete(source_file=X) ; upsert(...)`. A crash before the upsert leaves the prior drawers intact (they were not deleted yet because lock acquisition precedes everything). A crash mid-upsert leaves a *subset* of new drawers; the next run's `file_already_mined` (mtime + `NORMALIZE_VERSION` gate) re-mines and overwrites them by deterministic ID.
2. **Index-level**: `repair.py` separates `scan` / `prune` / `rebuild`; rebuild backs up only `chroma.sqlite3` (the source of truth) and recreates HNSW from scratch, so a corrupt index can be recovered without losing drawers. `migrate.py` reads drawers directly from SQLite (bypassing the ChromaDB API) when a version mismatch breaks the API path.
3. **Sidecar files**: `tunnels.json`, identity files, hook state — every cross-cutting writer uses temp-file + `os.replace` or atomic-create-with-mode (`os.open(... O_CREAT|O_WRONLY, 0o600)`).

The WAL (`~/.mempalace/wal/write_log.jsonl`) is for **audit and rollback
of write tools**, not for crash recovery — palace mutations are already
durable in chroma.sqlite3 + KG SQLite.

## 10. Background / Async Behavior

- **Hooks run out-of-band** of the AI conversation (Stop/PreCompact, ≤ 500 ms budget). Heavy ingest is shelled out: `python -m mempalace mine "$DIR" >> log 2>&1 &`.
- **Mining is foreground** within its own process but logged; subprocess invocation from a hook detaches it.
- **WAL writes are synchronous** but small (single `O_APPEND` write per tool call) and fail-soft.
- **No threads inside the domain layer.** SQLite KG uses `check_same_thread=False` so the MCP server (which is single-threaded JSON-RPC) and any helper tools share one connection safely.

## 11. Extension Points

| Extend | How |
|---|---|
| Storage backend | Subclass `BaseBackend` + `BaseCollection` (`backends/base.py`); register via `[project.entry-points."mempalace.backends"]`. Tests: `tests/test_backends.py` (conformance suite). |
| Source adapter (RFC 002) | Subclass `BaseSourceAdapter` (`sources/base.py`); declare `name`, `adapter_version`, `supported_modes`, `declared_transformations`; register via `[project.entry-points."mempalace.sources"]`. Use `PalaceContext.upsert_drawer` — never import `palace` directly. |
| MCP tool | Add a handler in `mempalace/mcp_server.py` and an entry to the `TOOLS` dict (`name → {description, inputSchema, handler}`). Inputs must go through `config.sanitize_*`; writes should call `_wal_log`. |
| CLI subcommand | Add `cmd_<name>(args)` and `sub.add_parser("<name>", ...)` in `cli.py:main_parser`, then wire into the `dispatch` table. |
| Input validation | Extend `mempalace/config.py` (`sanitize_name`, `sanitize_kg_value`, `sanitize_content`) and/or `mempalace/query_sanitizer.py`. |
| Hook | Drop a `mempal_<event>_hook.sh` (or any executable) in `hooks/`; register in `~/.claude/settings.local.json` or `~/.codex/hooks.json`. |
| Language | Add `mempalace/i18n/<bcp47>.json` with an `entity` section; `entity_detector` picks it up via `get_entity_patterns(languages=...)`. |
| Benchmark | Add `benchmarks/<name>_bench.py`; results land in `benchmarks/results_*.jsonl`. |

## 12. Notable Cross-Cutting Files

- **`mempalace/version.py`** — single source of truth for the package version (3 lines).
- **`pyproject.toml`** — dependencies, entry points (backends + sources), ruff/pytest/coverage config.
- **`mempalace/config.py`** — palace path resolution, hall keywords, all sanitizers.
- **`CLAUDE.md`** / **`AGENTS.md`** (symlink) — design principles, must read before any PR.
- **`docs/rfcs/002-source-adapter-plugin-spec.md`** — the read-side adapter contract `mempalace/sources/` implements.

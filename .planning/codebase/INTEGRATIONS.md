# External Integrations

**Analysis Date:** 2026-04-19

MemPalace's design contract is **local-first, zero phone-home** (`CLAUDE.md:25-28`, `MISSION.md`). Every integration listed here is either fully on-disk, opt-in, or transitively bundled with `chromadb`. There is no first-party telemetry, no cloud sync, and no required API key.

## Storage Backends (Vector Store)

**Contract:** `mempalace/backends/base.py`
- `BaseBackend` (ABC) — long-lived per-process factory, addressed by `PalaceRef(id, local_path, namespace)` (RFC 001 §2). Capabilities advertised via `frozenset` of strings (`supports_embeddings_in`, `local_mode`, etc.).
- `BaseCollection` (ABC) — kwargs-only `add` / `upsert` / `query` / `get` / `delete` / `count` / `update`.
- Typed returns: `QueryResult`, `GetResult` (with a transitional `_DictCompatMixin` for legacy callers expecting Chroma's dict shape).
- Errors: `BackendError`, `PalaceNotFoundError` (also a `FileNotFoundError`), `BackendClosedError`, `UnsupportedFilterError`, `DimensionMismatchError`, `EmbedderIdentityMismatchError`.

**Default backend:** `ChromaBackend` at `mempalace/backends/chroma.py:378`
- ChromaDB `PersistentClient` per palace path, cached with `(inode, mtime)` freshness check on `chroma.sqlite3` so external rebuilds are picked up without restart (`mempalace/backends/chroma.py:423-475`).
- `hnsw:space = "cosine"` — collections always created with cosine distance (`mempalace/backends/chroma.py:532-538`).
- Defensive helpers: `_fix_blob_seq_ids` migrates ChromaDB 0.6→1.5 BLOB→INTEGER seq_ids (`chroma.py:134`); `quarantine_stale_hnsw` renames stale segment dirs to break a known macOS arm64 SIGSEGV pattern (`chroma.py:52`).
- Capabilities: `supports_embeddings_in`, `supports_embeddings_passthrough`, `supports_embeddings_out`, `supports_metadata_filters`, `supports_contains_fast`, `local_mode`.

**Discovery:** `mempalace/backends/registry.py`
- Entry-point group `mempalace.backends`. Third-party backends register via `pyproject.toml`:
```toml
[project.entry-points."mempalace.backends"]
postgres = "mempalace_postgres:PostgresBackend"
```
- Resolution priority (`registry.py:139` `resolve_backend_for_palace`): explicit kwarg → per-palace config → `MEMPALACE_BACKEND` env var → on-disk auto-detect (`cls.detect(path)`) → default `"chroma"`.
- Built-in: `_register_builtins()` registers `chroma → ChromaBackend` via `setdefault` so explicit test-time registration wins (`registry.py:180-189`).

**Currently registered backends:** `chroma` only. No other in-tree implementations.

## Source Adapters (Ingest)

**Contract:** `mempalace/sources/base.py` — `BaseSourceAdapter` (RFC 002 scaffolding only; landed in commit `552e992`).
- Records: `SourceRef`, `SourceItemMetadata`, `DrawerRecord`, `RouteHint`, `SourceSummary`, `AdapterSchema`, `FieldSpec`.
- Errors: `SourceNotFoundError`, `AuthRequiredError`, `AdapterClosedError`, `TransformationViolationError`, `SchemaConformanceError`.
- Facade: `PalaceContext` (`mempalace/sources/context.py`) — what core hands to adapters during `ingest`.
- Reference transformations live in `mempalace/sources/transforms.py`.

**Discovery:** `mempalace.sources` entry-point group (declared empty in `pyproject.toml:49-50`). `miner.py` and `convo_miner.py` will migrate onto this contract in a follow-up PR; today they are direct callers.

**Currently registered adapters:** None first-party. The infrastructure is in place; third-party packages (`mempalace-source-cursor`, `mempalace-source-git`, …) are the intended consumers.

## Embedding Models

**Default:** ChromaDB's bundled embedder, used implicitly by every `collection.add()` and `collection.query(query_texts=…)` call. MemPalace never overrides `embedding_function=` on collection creation (`mempalace/backends/chroma.py:537-583`, `mempalace/mcp_server.py:221-223`) — so ChromaDB's default (`onnxruntime` running a small all-MiniLM-class sentence-transformer) is what runs.

**Disk footprint:** ~300 MB on first use (`README.md:158`). The model is cached by ChromaDB outside the palace dir.

**No app-level use of `sentence-transformers`, `fastembed`, or any embedding library.** Only the benchmark harness (`benchmarks/longmemeval_bench.py:128-154`) wires a custom `EmbeddingFunction`, and that is out of `mempalace/`.

**Identity guard:** `EmbedderIdentityMismatchError` exists in the backend ABC (`backends/base.py:53`) for future enforcement when the embedder is changed across writes; not yet used by the chroma backend.

## Knowledge Graph

**Engine:** SQLite via stdlib `sqlite3` (`mempalace/knowledge_graph.py:41`). No ORM, no migrations framework.

**Default location:** `~/.mempalace/knowledge_graph.sqlite3` (`knowledge_graph.py:47`). Parent dir chmod'd `0o700` on first init.

**Schema (`knowledge_graph.py:63-97`):**
- `entities(id, name, type, properties, created_at)`
- `triples(id, subject, predicate, object, valid_from, valid_to, confidence, source_closet, source_file, source_drawer_id, adapter_name, extracted_at)`
- Indexes on `subject`, `object`, `predicate`, and the `(valid_from, valid_to)` pair.
- `PRAGMA journal_mode=WAL` + `check_same_thread=False` + module-level `threading.Lock` for cross-thread MCP-server use.
- Backwards-compatible `_migrate_schema()` adds `source_drawer_id` / `adapter_name` columns on pre-RFC-002 palaces.

## MCP Server

**Entry point:** `python -m mempalace.mcp_server` — registered by `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`. Invocable directly or via `claude mcp add mempalace -- python -m mempalace.mcp_server [--palace PATH]`.

**Protocol:** JSON-RPC 2.0 over stdio. Negotiates one of `2025-11-25 / 2025-06-18 / 2025-03-26 / 2024-11-05` (`mcp_server.py:1563-1568`).

**stdio safety (issue #225):** stdout is dup2'd to stderr at fd-level before any heavy import (`mcp_server.py:34-43`) and restored only inside `main()` — so chromadb / onnxruntime banners can't corrupt the JSON-RPC stream.

**Tools (29 total, all registered in the `TOOLS` dict at `mempalace/mcp_server.py:1144-1560`):**

| Tool | Description (one-liner) |
|---|---|
| `mempalace_status` | Palace overview — total drawers, wing/room counts. |
| `mempalace_list_wings` | List all wings with drawer counts. |
| `mempalace_list_rooms` | List rooms within a wing (or every room). |
| `mempalace_get_taxonomy` | Full wing → room → drawer-count tree. |
| `mempalace_get_aaak_spec` | Return the AAAK compressed-memory dialect spec. |
| `mempalace_kg_query` | Query knowledge graph for an entity's triples (with `as_of` time filter, direction). |
| `mempalace_kg_add` | Insert a `subject → predicate → object` triple with optional validity window. |
| `mempalace_kg_invalidate` | Mark a triple as no longer true (sets `valid_to`). |
| `mempalace_kg_timeline` | Chronological timeline of facts (per entity or global). |
| `mempalace_kg_stats` | Entity / triple counts, current vs expired, predicate list. |
| `mempalace_traverse` | Walk the palace graph from a starting room. |
| `mempalace_find_tunnels` | Find rooms bridging two wings. |
| `mempalace_graph_stats` | Palace-graph overview: rooms, tunnels, edges. |
| `mempalace_create_tunnel` | Explicit cross-wing tunnel between two rooms/drawers. |
| `mempalace_list_tunnels` | List explicit tunnels (optional wing filter). |
| `mempalace_delete_tunnel` | Delete a tunnel by ID. |
| `mempalace_follow_tunnels` | Follow tunnels from a (wing, room) and return connected rooms. |
| `mempalace_search` | Hybrid BM25 + vector search with optional wing/room filters and `max_distance` cap. |
| `mempalace_check_duplicate` | Return existing drawer if content already filed (configurable threshold). |
| `mempalace_add_drawer` | File verbatim content into a (wing, room); duplicate-check first. |
| `mempalace_delete_drawer` | Remove a drawer by ID (irreversible). |
| `mempalace_get_drawer` | Fetch a single drawer's full content + metadata. |
| `mempalace_list_drawers` | Paginated drawer listing with optional wing/room filter. |
| `mempalace_update_drawer` | Update an existing drawer's content / wing / room. |
| `mempalace_diary_write` | Append an AAAK-format diary entry to the calling agent's diary. |
| `mempalace_diary_read` | Read recent diary entries for an agent. |
| `mempalace_hook_settings` | Get/set hook behavior toggles (`silent_save`, `desktop_toast`). |
| `mempalace_memories_filed_away` | Check whether a recent palace checkpoint was saved. |
| `mempalace_reconnect` | Force ChromaDB cache invalidation after external palace writes. |

**Argument hardening:** `handle_request` whitelists incoming args against the schema's `properties` (unless the handler accepts `**kwargs`) and coerces declared `integer` / `number` types — defends against callers spoofing internal params like `added_by` (`mcp_server.py:1617-1650`).

## Claude Code / Codex Hooks

Two shell hooks live at `hooks/` and ship via the plugin manifests (`.claude-plugin/hooks/`, `.codex-plugin/hooks/`).

| Hook | File | Event | Trigger |
|---|---|---|---|
| Save | `hooks/mempal_save_hook.sh` | Claude Code `Stop` (also Codex `Stop`) | Every `SAVE_INTERVAL=15` user messages (`mempal_save_hook.sh:55`). Counts `role: user` entries in the JSONL transcript at `transcript_path`, tracks last-save offset under `~/.mempalace/hook_state/<session_id>_last_save`. Optionally background-mines the transcript dir or `$MEMPAL_DIR` via `python -m mempalace mine`. Honors `MEMPAL_VERBOSE` to switch between silent (`{}`) and `decision: block` modes. |
| PreCompact | `hooks/mempal_precompact_hook.sh` | Claude Code `PreCompact` (and Codex equivalent) | Always — fires unconditionally before context compression. Optional synchronous `mempalace mine` of `$MEMPAL_DIR`. Returns `{}` (silent) by default. |

Both hooks shell out to `python3 -m mempalace mine`. State + log directory: `~/.mempalace/hook_state/`.

**Hook-management surface inside the package:** `mempalace/hooks_cli.py` (CLI side) and the `mempalace_hook_settings` MCP tool (`mcp_server.py:1041`).

## Optional LLM Integrations (Closet Rebuild)

**File:** `mempalace/closet_llm.py` — opt-in, off by default, **no PyPI dep added** (uses stdlib `urllib.request`).

**Endpoint contract:** any OpenAI-compatible Chat Completions URL. Env vars (or CLI flags):
- `LLM_ENDPOINT` — base URL (required).
- `LLM_KEY` — bearer token (optional; local inference doesn't need it).
- `LLM_MODEL` — model name (required).

**Documented endpoints (`closet_llm.py:13-21`):**
- Ollama — `http://localhost:11434/v1`
- vLLM / llama.cpp — `http://localhost:8000/v1`
- OpenAI — `https://api.openai.com/v1`
- OpenRouter — `https://openrouter.ai/api/v1`
- Anthropic — `https://api.anthropic.com/v1` (only via an OpenAI-compat proxy)

**No vendor lock-in.** The README's "rerank pipeline" claim (`README.md:91-97`) — reproduced with Claude Haiku, Claude Sonnet, and minimax-m2.7 via Ollama Cloud — uses this same generic seam, not a vendor SDK.

## External HTTP Surface (App-level)

The whole app makes outbound HTTP from exactly two places, both via stdlib `urllib`:

| File | Endpoint | Purpose | Opt-in? |
|---|---|---|---|
| `mempalace/closet_llm.py:152` | User-supplied `LLM_ENDPOINT` (POST) | Optional LLM closet rebuild. | Yes — only fires when user runs the script with env/flags set. |
| `mempalace/entity_registry.py:189-191` | `https://en.wikipedia.org/api/rest_v1/page/summary/{word}` (GET, `User-Agent: MemPalace/1.0`) | Disambiguate ambiguous person/place names during entity detection. | Caller-driven — `entity_registry.py:529` notes "no data leaves the machine unless the caller requests it". |

There is **no `httpx` or `requests`** in the runtime dep set. Any `httpx` usage is transitive via `chromadb` (`uv.lock:306`) and only fires if Chroma is run in client/server mode, which MemPalace does not do.

## Transcript / File Format Integrations

`mempalace/normalize.py` is the single normalizer for all conversation exports. Detected formats (`normalize.py:559` and helpers):

| Format | Detector | Notes |
|---|---|---|
| Plain text with `>` markers | Pass-through | Default if no JSON detected. |
| Claude.ai JSON export | `_try_claude_ai_json` (`normalize.py:283`) | Walks message tree, joins by speaker. |
| ChatGPT `conversations.json` | `_try_chatgpt_json` (`normalize.py:332`) | Handles OpenAI's nested mapping shape. |
| Claude Code JSONL | `_try_claude_code_jsonl` (`normalize.py:173`) | Captures `tool_use` / `tool_result` blocks; strips `<system-reminder>`, `<command-message>`, `<hook_output>`, etc. via `_NOISE_TAGS` (`normalize.py:39-46`). |
| OpenAI Codex CLI JSONL | `_try_codex_jsonl` (`normalize.py:235`) | |
| Slack JSON export | `_try_slack_json` (`normalize.py:373`) | Appends `[source: slack-export | ...]` provenance footer (`normalize.py:25-27`). |

`mempalace/convo_miner.py` (`CONVO_EXTENSIONS = {".txt", ".md", ".json", ".jsonl"}`, `convo_miner.py:49-54`) is the entry point that drives `normalize.normalize()` over a directory.

## Cross-Process / OS Integrations

- **Mine lock:** `mempalace/palace.py:274-310` — `fcntl.flock` (POSIX) or `msvcrt.locking` (Windows) on a hash-named lockfile under `~/.mempalace/locks/`. Prevents two miners from racing on the same source file.
- **Hook state:** `~/.mempalace/hook_state/` — per-session counters + `hook.log`.
- **Backend env override:** `MEMPALACE_BACKEND` (`registry.py:143`).
- **Palace path env override:** `MEMPALACE_PALACE_PATH` (set by `mcp_server.py:94-95` when `--palace` is passed).

## Plugin Manifests (Distribution)

| Manifest | Path | Purpose |
|---|---|---|
| Claude Code plugin | `.claude-plugin/plugin.json` | Registers `mempalace` MCP server (`python3 -m mempalace.mcp_server`) and bundles hooks/skills/commands. |
| Claude Code marketplace | `.claude-plugin/marketplace.json` | Source-of-truth for the plugin catalog entry. |
| Codex plugin | `.codex-plugin/plugin.json` (+ `hooks.json`) | Equivalent registration for OpenAI Codex CLI. |
| OpenClaw skill | `integrations/openclaw/SKILL.md` | Markdown skill for the OpenClaw skill marketplace. |

## Authentication & Identity

**None.** No auth provider, no SSO, no user accounts, no API keys for core memory. The closet-LLM seam takes a `LLM_KEY` bearer token and the Wikipedia endpoint is unauthenticated.

## Monitoring / Observability

**Logging:** stdlib `logging` to stderr (`mcp_server.py:75`, every module's `logger = logging.getLogger(...)`). No structured-log library.

**Telemetry:** **None.** Per `CLAUDE.md:27` — *"Privacy by architecture — The system physically cannot send your data because it never leaves your machine. No telemetry, no phone-home, no external service dependencies for core operations."*

The single hostile actor is ChromaDB's bundled posthog client. It is silenced at import time:

```7:11:mempalace/__init__.py
import logging

from .version import __version__  # noqa: E402

# chromadb telemetry: posthog capture() was broken in 0.6.x causing noisy stderr
# warnings ("capture() takes 1 positional argument but 3 were given"). In 1.x the
# posthog client is a no-op stub, so this is now harmless — kept as a guard in
# case future chromadb versions re-introduce real telemetry calls.
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
```

`uv.lock` confirms `posthog` and `opentelemetry-*` packages are in the resolved tree (transitively, via chromadb), but neither is imported by any `mempalace/*.py` module.

## Required Environment Variables

| Var | Where read | Purpose |
|---|---|---|
| `MEMPALACE_PALACE_PATH` | `mcp_server.py:94`, `config.py` | Default palace dir if no `--palace` flag is passed. |
| `MEMPALACE_BACKEND` | `backends/registry.py:143` | Override the storage backend (`chroma`, third-party). |
| `LLM_ENDPOINT` / `LLM_KEY` / `LLM_MODEL` | `closet_llm.py` | Optional LLM closet rebuild only. |
| `MEMPAL_DIR` (hook env) | `hooks/mempal_save_hook.sh:62`, `hooks/mempal_precompact_hook.sh:55` | Override which directory the hook auto-mines. |
| `MEMPAL_VERBOSE` (hook env) | `hooks/mempal_save_hook.sh:163` | Switch save hook from silent to `decision: block` developer mode. |

**No required secrets.** No `.env*` files in the repo. No `serviceAccountKey.json` / `credentials.*` of any kind.

## Webhooks & Callbacks

**Incoming:** None — MemPalace runs no HTTP server.
**Outgoing:** None — see "External HTTP Surface" above for the only two outbound paths, both pull-only.

---

*Integration audit: 2026-04-19*

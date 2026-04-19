# MemPalace — Concerns

> Tech debt, known bugs, security posture, performance, fragile areas, migration debt, and sharp edges for new contributors. Generated 2026-04-19.

## 1. Severity Legend

| Severity     | Definition                                                                                                          |
| ------------ | ------------------------------------------------------------------------------------------------------------------- |
| **HIGH**     | Data loss, security boundary breach, or a CLAUDE.md invariant violation. Block on merge.                            |
| **MEDIUM**   | Correctness or performance risk that surfaces under realistic load (large palaces, concurrent agents, slow disks).  |
| **LOW**      | Code smell, duplication, dead-code, or contributor-onboarding friction. Cleanup work, no immediate user impact.     |

Every finding cites `path/to/file.py:LINE-LINE`. Findings are tagged **OBSERVED** (seen directly in code/CHANGELOG/tests) or **INFERRED** (reasoned from observed evidence — corroboration recommended).

## 2. Tech Debt

| Area                                      | Location                                                                          | Severity | Suggested next step                                                                              |
| ----------------------------------------- | --------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------ |
| AAAK not expanded before embedding        | `mempalace/mcp_server.py:958-961` (only `# TODO` in package)                      | MEDIUM   | Either expand AAAK → natural language pre-embed, or document the embedding-quality trade-off.    |
| Two hook implementations to maintain      | `hooks/mempal_save_hook.sh` + `mempalace/hooks_cli.py`                            | MEDIUM   | Pick one. Bash exists for shell-only environments; Python is safer. Mark one deprecated.         |
| `quarantine_stale_hnsw` defined but never auto-invoked | `mempalace/backends/chroma.py:52-131` (only called from `tests/test_backends.py`) | MEDIUM   | Wire into `ChromaBackend._client` cache-refresh path so HNSW drift self-heals.                   |
| `mcp_server.py` is 1,713 lines, 30 tools  | `mempalace/mcp_server.py:1-1713`                                                  | MEDIUM   | Split into `tools/{search,kg,diary,tunnels,settings}.py`. Test surface area is enormous.         |
| 49 broad `except Exception:` blocks       | grep -c on `mempalace/`: 49 hits across 21 files                                  | MEDIUM   | Narrow to specific exceptions; convert silent swallows to `logger.exception` minimum.            |
| McCabe complexity ceiling at 25           | `pyproject.toml:71` (`max-complexity = 25`)                                       | LOW      | Functions hitting that ceiling deserve refactor; ratchet ceiling down over time.                 |
| `pragma: no cover` on `BaseBackend.detect`| `mempalace/backends/base.py:331`                                                  | LOW      | Add a smoke test or remove the abstract sentinel — undocumented why it's excluded.               |
| `noqa: E402` on 28+ imports               | `mempalace/mcp_server.py:45-73`, `mempalace/__init__.py:5`                        | LOW      | Already justified (stdio redirect must precede `chromadb` import) — comment explains; keep.      |
| Schema migration runs on every KG init    | `mempalace/knowledge_graph.py:98-130`                                             | LOW      | Cache "schema_version" in a sentinel row; skip ALTER on hot path.                                |
| KG `_entity_id` collisions                | `mempalace/knowledge_graph.py:131-138` — `name.lower().replace(" ", "_").replace("'", "")` | MEDIUM | "Mary O'Brien" and "mary obrien" collapse to the same entity. Append a short hash of the original. |
| Single `threading.Lock` serializes all KG SQLite access | `mempalace/knowledge_graph.py:60, 140, 179, 230, 250, 313, 371`         | MEDIUM   | Move to per-thread connection or use `sqlite3` `check_same_thread=False` + WAL contention safely.|
| In-memory dialect coupling                | `mempalace/dialect.py:1-1091` (single 1k-line module)                             | MEDIUM   | Lossy by design (HISTORY 2026-04-07); needs a stronger boundary against accidental verbatim use. |

## 3. Known Bugs / Limitations

- **OBSERVED — Windows ChromaDB SQLite file-lock.** `tests/test_mcp_server.py:789-792` skips `test_missing_db_invalidates_cache` on `win32` because "Windows holds chroma.sqlite3 open while the client is cached, blocking `os.remove`." `.github/workflows/ci.yml` drops Windows coverage threshold to 80% (vs 85% Linux/macOS) for the same reason. Sharp edge documented in `CLAUDE.md`.
- **OBSERVED — AAAK is lossy compression.** `mempalace/dialect.py:6, 566, 970` calls itself a "lossy summarization format." `docs/HISTORY.md` 2026-04-07 retraction acknowledges the previous "30× lossless" claim was wrong; `docs/HISTORY.md` 2026-04-14 records a 12.4-pt R@5 regression vs raw mode in the LongMemEval rewrite.
- **OBSERVED — ChromaDB segfault chain.** `mempalace/__init__.py:13-25` documents three resolved crashes: macOS arm64 `ORT_DISABLE_COREML` no-op (issue #74 / #397), real fix being chromadb >= 1.5.4 (#521 / #581). `mempalace/backends/chroma.py:52-131` quarantines drifted HNSW segments (commit `0c38dea`). `mempalace/backends/chroma.py:134-164` repairs BLOB `seq_id` mismatches from chromadb 0.6.x → 1.5.x.
- **OBSERVED — None-metadata defensive guards.** Recent fix `3f0cfd5` ("guard tool_status/list_wings/list_rooms/get_taxonomy against None metadata") implies ChromaDB occasionally returns metadata rows that are `None`. Code now treats `m or {}` everywhere (`mempalace/mcp_server.py:318, 372, 396, 414`).
- **OBSERVED — Stale HNSW after external writes.** Fix `e200ce2` ("detect mtime changes in `_get_client` to prevent stale HNSW index, #757"). `mempalace/mcp_server.py:106-210` and `mempalace/backends/chroma.py:413-474` both maintain inode + mtime sentinels. CLI scripts that bypass MCP can still desynchronize the cache between checks.
- **OBSERVED — Impostor-domain incident.** `docs/HISTORY.md` 2026-04-11 documents that typo-squatted domains hosted malware claiming to be MemPalace. `README.md` and `SECURITY.md` now lead with verification guidance. No code-side mitigation possible.
- **INFERRED — Coverage tag `# pragma: no cover` on backend dispatcher** at `mempalace/backends/base.py:331` may hide an unexercised code path; no incident attached but worth a smoke test.

## 4. Security Posture (vs. CLAUDE.md invariants)

### "Verbatim always — never summarize, paraphrase, or compress source content."
- **Enforced at:** drawer write paths in `mempalace/sweeper.py`, `mempalace/diary_ingest.py`, `mempalace/miner.py`, `mempalace/convo_miner.py`, and `mempalace/mcp_server.py:921-987` (`tool_diary_write`). Documents are stored unmodified; AAAK lives only in metadata or in dedicated closet entries.
- **At risk:** `mempalace/dialect.py` is a 1k-line lossy translator. If a contributor accidentally feeds AAAK back to a drawer write, the verbatim invariant silently breaks. INFERRED — there's no assertion that drawer documents survive a round-trip.

### "Local-first, zero API for core memory operations."
- **OBSERVED — two outbound HTTP paths exist, both opt-in:**
  - `mempalace/entity_registry.py:520-558` — Wikipedia lookup, default `allow_network=False`. Tests at `tests/test_entity_registry.py:228-315` lock down the gate.
  - `mempalace/closet_llm.py:43-44, 152-153` — Optional LLM regeneration of closet summaries; only fires when `LLM_ENDPOINT` and `LLM_MODEL` env vars are set.
- **OBSERVED — benchmarks make their own network calls** (`benchmarks/longmemeval_bench.py:2390, 2803-2804`, `benchmarks/locomo_bench.py:30`) — out of scope for the "core" invariant; not loaded by the package's runtime modules.
- **No analytics, sentry, datadog, posthog, or telemetry imports** found in `mempalace/`. `mempalace/__init__.py:11` defensively silences `chromadb.telemetry.product.posthog` even though it's now a no-op stub.

### "Subprocess use must avoid shell injection."
- `mempalace/hooks_cli.py:203, 230` uses `subprocess.Popen`/`subprocess.run` with explicit list args (no `shell=True`). Path validation at `mempalace/hooks_cli.py:40-62` rejects `..`, non-`.jsonl`/`.json` suffixes, and non-string `SESSION_ID`s. Cross-platform PID liveness check at `_pid_alive`.
- `hooks/mempal_save_hook.sh:68` uses `eval $(echo "$INPUT" | python3 -c "...")` — sanitized by Python-side regex `re.sub(r'[^a-zA-Z0-9_/.\-~]', '', str(s))`. Looks frightening; is actually defended. Hardening commits: #114, #387, #812. Still fragile on principle — see Quick Wins.
- `hooks/mempal_precompact_hook.sh:60` logs `SESSION_ID` directly from JSON without sanitization, but only into a logfile — no shell execution path. Low risk.

### "Path traversal prevention."
- `mempalace/hooks_cli.py:40-62` (`_validate_transcript_path`) — explicit. `mempalace/config.py:_SAFE_NAME_RE` (`mempalace/config.py:19`) restricts wing/room names to `[\w.\-]+`. `sanitize_kg_value` is intentionally permissive (fix `79c9c0e`, closes #455) and accepts most printable chars but blocks NUL bytes.
- **MCP tool surface (untrusted LLM input).** Every wing/room argument flows through `sanitize_name`; content through `sanitize_content`; KG entity values through `sanitize_kg_value`; queries through `mempalace/query_sanitizer.py:sanitize_query`. Confirmed at `mempalace/mcp_server.py:286-290, 384, 439, 524-527, 558-561, 930, 996`.

### "No unsafe deserialization."
- **OBSERVED — zero hits** for `pickle.load`, `yaml.load(` (without Loader), `eval(`, or `exec(` inside `mempalace/`. JSON only, via `json.load`/`json.loads` and `json.dump`/`json.dumps`.

### "Privacy by architecture — secrets must not leak to logs."
- `mempalace/mcp_server.py:139-160` — `_wal_log` redacts keys in `_WAL_REDACT_KEYS = {content, query, text, …}` before writing. WAL file mode `0o600` (`mempalace/mcp_server.py:147`). `~/.mempalace/` chmod'd `0o700` (`mempalace/entity_registry.py:319-327`).

### "Prompt injection defense for retrieval."
- `mempalace/query_sanitizer.py:15-188` — strips system-prompt-style preambles, falls back to length truncation. Fix #333 referenced at `mempalace/mcp_server.py:447`.
- **OBSERVED — sanitized query is reported back to caller.** `mempalace/mcp_server.py:457-465` attaches `query_sanitized: true` and a sanitizer audit block when the query was rewritten. Good signal for downstream callers.

### "MCP tool input handling — every tool sanitizes."
- 30 tools in `mempalace/mcp_server.py:296-1138` (grep `^def tool_`). Spot-checked 12 — all that take wing/room/agent/entity arguments call `sanitize_name`/`sanitize_optional_name`/`sanitize_kg_value` before any DB call. Two tools accept free-form `content` (`tool_add_drawer`, `tool_diary_write`); both call `sanitize_content` which enforces NUL stripping and length caps.
- **INFERRED gap** — `tool_check_duplicate` (`mempalace/mcp_server.py:471`) accepts raw `content` without `sanitize_content`. Read-only path so blast radius is small, but worth normalizing.
- **OBSERVED — `wait_for_previous` argument quietly ignored.** Fix `007acca` (#322) absorbs an extra argument Gemini's MCP client sends. Defensive but worth knowing about.
- **OBSERVED — argument whitelist bypassed for **kwargs handlers.** Fix `862a07b` (#572 / #684) skips the whitelist for tools accepting `**kwargs`. Reduces false rejections; widens trust surface for those tools — currently none use `**kwargs`.

## 5. Performance Concerns

- **OBSERVED — no test asserts the <500ms hook budget or <100ms startup budget.** `CLAUDE.md` and `AGENTS.md` state both budgets; `tests/benchmarks/` contains `@pytest.mark.benchmark` files (`test_ingest_bench.py`, `test_mcp_bench.py`, `test_layers_bench.py`, `test_recall_threshold.py`, `test_knowledge_graph_bench.py`, `test_chromadb_stress.py`, `test_memory_profile.py`) but none assert the literal latency targets. INFERRED — a regression in hook startup would not be caught by CI.
- **OBSERVED — cold-start dominated by ChromaDB import side effects.** `mempalace/mcp_server.py:30-73` redirects stdout to stderr around the chromadb import to keep onnxruntime/posthog banners from breaking JSON-RPC (fix #225 / #864). Import alone loads onnxruntime + sentence-transformers + chromadb_rust_bindings — each measurable on cold disk.
- **OBSERVED — 500 MB transcript ceiling loads file fully into memory.** `mempalace/convo_miner.py:58-65` sets `MAX_FILE_SIZE = 500 * 1024 * 1024`; same module normalizes the entire file before chunking. Memory spike scales linearly with file size. `mempalace/miner.py` follows the same pattern.
- **OBSERVED — `repair.rebuild_index` is a full extract-delete-upsert.** `mempalace/repair.py:204-279` extracts every drawer into in-memory `all_ids`/`all_docs`/`all_metas` lists, deletes the collection, recreates it, then upserts in batches. On a 100k-drawer palace the lists alone are GB-scale. INFERRED — likely OOM territory at scale.
- **OBSERVED — `migrate.migrate` has a destructive window.** `mempalace/migrate.py:236-237` performs `shutil.rmtree(palace_path)` followed by `shutil.move(temp_palace, palace_path)`. A power loss between those two calls leaves the user with no palace. Recommend `os.replace` on a same-filesystem temp directory.
- **OBSERVED — `_metadata_cache` TTL is 5 s.** `mempalace/mcp_server.py:213-283`. For palaces with >1k drawers, every list/taxonomy call paginates 1000-row batches via `col.get(limit=1000, offset=offset)`. INFERRED — fine for personal palaces, slow at >100k drawers.
- **OBSERVED — `dedup_palace` is O(K·N) per source-file group.** `mempalace/dedup.py:102` issues one `col.query` per drawer in each group of >5 drawers. Acceptable for incremental dedup, expensive on first sweep over a large palace.
- **OBSERVED — `searcher.search_memories` over-fetches.** `mempalace/searcher.py:33-45` defends against ChromaDB's empty-list-of-lists return shape; the search itself fetches `n_results × 3` drawers + `n_results × 2` closets and re-ranks via BM25. INFERRED — adequate for n=5–20; latency grows linearly with `n_results`.
- **OBSERVED — KG `timeline` silently truncates at LIMIT 100.** `mempalace/knowledge_graph.py:342, 353`. Long-lived agents will lose history without warning.

## 6. Fragile / Risky Areas

- **High-churn files (`git log` last 6 months):**

  | File                              | Commits | Why it's fragile                                        |
  | --------------------------------- | ------- | -------------------------------------------------------- |
  | `mempalace/mcp_server.py`         | 46      | Tool surface area, validation, cache management, WAL.    |
  | `mempalace/cli.py`                | 32      | Many subcommands, evolving UX, init/onboarding flow.     |
  | `mempalace/miner.py`              | 25      | Many transcript formats × edge cases.                    |
  | `mempalace/convo_miner.py`        | 21      | Tool-block preservation, message granularity.            |
  | `mempalace/backends/chroma.py`    | 17      | Quarantine, BLOB-fix, dual `_normalize_get_collection_args` paths. |

- **Concurrency split-brain.** Drawer writes use the cross-platform `mine_lock` file lock (`mempalace/palace.py:274-310` — `fcntl.flock` on POSIX, `msvcrt.locking` on Windows). KG writes use only `threading.Lock` (`mempalace/knowledge_graph.py:60`). Two MCP servers writing the same KG concurrently can corrupt or race.
- **ChromaDB cache-invalidation lattice.** `mempalace/mcp_server.py:_get_client` and `mempalace/backends/chroma.py:_client` each maintain inode + mtime sentinels; the `_palace_db_inode`/`_palace_db_mtime` globals can drift if external scripts modify the palace between two MCP calls inside the 5 s metadata window.
- **AAAK index-format coupling.** `mempalace/dialect.py` hard-codes 3-letter entity codes and emotion markers in module-scope tables. Any change risks rendering existing palace closets unreadable. INFERRED — `NORMALIZE_VERSION` exists but no migration test asserts forward compatibility.
- **`_normalize_get_collection_args` dual code path.** `mempalace/backends/chroma.py:588-642` accepts both new `PalaceRef` and legacy positional path strings. Both supported indefinitely with no deprecation timer.
- **Diary entry IDs depend on full content hash + microsecond timestamp.** `mempalace/mcp_server.py:942-945` hashes the full `entry` and uses `%f` precision (fix `5db651a` / #819). Avoids ID collisions on rapid writes; a clock skew on the host can still produce out-of-order IDs (sort by `filed_at` ISO string at `mempalace/mcp_server.py:1027` mitigates but doesn't fix).
- **No locking around `entity_registry.json` writes.** `mempalace/entity_registry.py:317-327` does a non-atomic `write_text`. Two processes onboarding simultaneously can clobber each other. INFERRED — single-user palaces unlikely to hit this; multi-agent setups can.

## 7. Migration / Compatibility Debt

- **ChromaDB 0.6.x → 1.5.x BLOB seq_id repair runs on every PersistentClient open** — `mempalace/backends/chroma.py:134-164`. Permanent debt; safe to keep but documents how rough that migration was.
- **KG schema backfill on every init** — `mempalace/knowledge_graph.py:98-130` adds `source_drawer_id` and `adapter_name` columns if absent (RFC 002 §5.5).
- **Direct SQLite extraction in `migrate.py`** — `mempalace/migrate.py:28-88` reads chromadb's SQLite directly, bypassing the chromadb client API entirely. Tied to ChromaDB's internal schema; will need reworking if ChromaDB renames tables again.
- **Python 3.9 floor** (`pyproject.toml:6`). CI tests 3.9/3.11/3.13 on Linux but only 3.9 on Windows + macOS (`.github/workflows/ci.yml`). Raising the floor unblocks PEP 604 union syntax + `dict[str, Any]` hints at module level. INFERRED — i18n module added in #718 keeps 3.9 working; no hard blocker beyond user policy.
- **`chromadb >= 1.5.4, < 2`** pin. ChromaDB v2 will require a coordinated migration (`mempalace/backends/registry.py` would need a v2 backend).
- **Two hook implementations** — `hooks/*.sh` (Bash) and `mempalace/hooks_cli.py` (Python). Both maintained; no deprecation marker.
- **Removed `chromadb < 0.7` upper bound** (CHANGELOG `## [3.0.0]`) — historical migration debt now closed; useful as context for future major bumps.

## 8. Recent Activity Signal

Recent contributors (last 3 months): Igor Lins e Silva (~150+ commits), Ben Sigman (~70+), bensig (~30+), Tal Muskal (~25+). Sustained one-to-three-author rhythm. Recent fixes cluster around **None-metadata guards** (`3f0cfd5`), **palace cold-start handling** (`54a386d`, #830), **stale HNSW detection** (`e200ce2`, #757), **WAL/permissions hardening** (`b524b31`, #814), and **MCP tool argument validation** (`58eca50`, #647). The newest merged work is the explicit **cross-wing tunnels** feature (`1b4ce0b`) and a **ChromaBackend seam** refactor (`267a644`) that routes all chromadb access through one module — intentional surface-area reduction.

| Theme               | Representative commits                            | Inferred risk              |
| ------------------- | ------------------------------------------------- | -------------------------- |
| Defensive guards    | `3f0cfd5`, `54a386d`, `e200ce2`, `b226251`        | ChromaDB return shapes drift between minor versions. |
| Security hardening  | `b524b31`, `c478dfa`, `58eca50`, `79c9c0e`        | Sustained input-validation review; good signal.       |
| Backend refactor    | `267a644`, `ae5196b`                              | Single-seam ChromaBackend reduces blast radius.       |
| New surface area    | `1b4ce0b` (tunnels), `20255b0`, `1263c3c`         | New surface = new bugs near the seam.                 |

## 9. Sharp Edges for New Contributors

- **ChromaDB Windows file lock.** `tests/test_mcp_server.py:789-792` skips on `win32`; CI lowers Windows coverage to 80% to compensate. Anyone touching `_get_client` cache invalidation needs to test on Windows too.
- **Hooks need the executable bit.** `hooks/*.sh` are not auto-`chmod +x`'d; user must do it. INFERRED gotcha — no installer step.
- **Optional deps not installed by default.** `[spellcheck]` extra (autocorrect ≥ 2.0) is opt-in. `closet_llm` requires `LLM_ENDPOINT`/`LLM_KEY`/`LLM_MODEL` env vars — fail-soft when missing.
- **`quarantine_stale_hnsw` is opt-in.** Defined and tested (`tests/test_backends.py:399-443`) but never auto-invoked. Contributors hitting an HNSW segfault must know to call it manually.
- **"Verbatim always" auto-rejects PRs that summarize.** Stated in `CLAUDE.md` and `CONTRIBUTING.md:82`. Reviewer judgement, not a CI check.
- **WING/ROOM/DRAWER ≠ novel retrieval.** `CONTRIBUTING.md:85` warns explicitly: it's metadata filtering on a vector store. Easy to over-explain in docs/PRs.
- **AAAK is lossy and experimental.** `mempalace/dialect.py:6` and the 2026-04-07 HISTORY note. Verbatim drawers stay the source of truth.
- **Bash save hook uses `eval`.** `hooks/mempal_save_hook.sh:68` — defended via Python sanitization, but the construct itself looks unsafe at a glance. Reviewers should know to look at the Python `safe = lambda s: re.sub(...)` upstream.
- **`KnowledgeGraph._entity_id` is naive.** `mempalace/knowledge_graph.py:131-138` collapses spaces and apostrophes — `Mary O'Brien` and `mary obrien` become the same entity ID.
- **`MAX_FILE_SIZE = 500 MB`** is permissive. Mining a 500 MB transcript spikes RSS by at least the file size during normalization (`mempalace/convo_miner.py:58-65`).

## 10. Recommended Quick Wins

1. **Auto-invoke `quarantine_stale_hnsw` on stale-mtime detection** in `mempalace/backends/chroma.py:447-474`. Today the workaround is documented but manual.
2. **Add a `<500ms` regression test for hook startup** (`tests/test_hooks_cli.py`). The CLAUDE.md performance budget is currently unenforced anywhere in CI.
3. **Tighten `KnowledgeGraph._entity_id`** at `mempalace/knowledge_graph.py:131-138` to append a short hash of the original name, ending the `Mary O'Brien` collision class.
4. **Make `migrate.migrate` atomic.** Replace the `rmtree → shutil.move` pair at `mempalace/migrate.py:236-237` with `os.replace` on a same-filesystem staging directory. Eliminates the data-loss window on power failure.
5. **Stream `repair.rebuild_index`.** `mempalace/repair.py:241-275` should iterate page-by-page rather than loading every drawer's id/doc/metadata into RAM before delete + upsert.
6. **Narrow the worst silent swallowers in `mempalace/searcher.py`** (broad `except Exception:` near lines 209, 229, 246, 380). Bug #1011 (`None` metadata) was hard to diagnose because of this pattern.
7. **Add a deprecation timer for legacy `_normalize_get_collection_args` positional-path style** (`mempalace/backends/chroma.py:588-642`). Pick a release after which only `PalaceRef` is accepted.

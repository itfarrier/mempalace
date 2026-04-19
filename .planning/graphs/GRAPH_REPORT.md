# Graph Report - /Users/itfarrier/pet/mempalace  (2026-04-19)

## Corpus Check
- 114 files · ~274,830 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2955 nodes · 6820 edges · 43 communities detected
- Extraction: 53% EXTRACTED · 47% INFERRED · 0% AMBIGUOUS · INFERRED: 3224 edges (avg confidence: 0.68)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]

## God Nodes (most connected - your core abstractions)
1. `MempalaceConfig` - 244 edges
2. `ChromaBackend` - 217 edges
3. `PalaceDataGenerator` - 162 edges
4. `KnowledgeGraph` - 160 edges
5. `BaseCollection` - 131 edges
6. `Dialect` - 117 edges
7. `ChromaCollection` - 79 edges
8. `Layer1` - 53 edges
9. `_patch_mcp_server()` - 52 edges
10. `load()` - 52 edges

## Surprising Connections (you probably didn't know these)
- `Tests for mempalace.entity_detector.` --uses--> `MempalaceConfig`  [INFERRED]
  /Users/itfarrier/pet/mempalace/tests/test_entity_detector.py → /Users/itfarrier/pet/mempalace/mempalace/config.py
- `When fewer than 3 prose files, falls back to include all readable files.` --uses--> `MempalaceConfig`  [INFERRED]
  /Users/itfarrier/pet/mempalace/tests/test_entity_detector.py → /Users/itfarrier/pet/mempalace/mempalace/config.py
- `Context manager that drops a locale JSON into mempalace/i18n/ for the test body.` --uses--> `MempalaceConfig`  [INFERRED]
  /Users/itfarrier/pet/mempalace/tests/test_entity_detector.py → /Users/itfarrier/pet/mempalace/mempalace/config.py
- `Default languages tuple = ('en',) — accented names dropped (as today).` --uses--> `MempalaceConfig`  [INFERRED]
  /Users/itfarrier/pet/mempalace/tests/test_entity_detector.py → /Users/itfarrier/pet/mempalace/mempalace/config.py
- `A locale with a Latin+diacritics candidate_pattern catches accented names.` --uses--> `MempalaceConfig`  [INFERRED]
  /Users/itfarrier/pet/mempalace/tests/test_entity_detector.py → /Users/itfarrier/pet/mempalace/mempalace/config.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.01
Nodes (260): KnowledgeGraph pre-loaded with sample triples., seeded_kg(), PalaceDataGenerator, Deterministic data factory for MemPalace scale benchmarks.  Generates realistic, Generate deterministic, realistic test data at configurable scale., Create unique needle content for recall testing., Generate a random text block of realistic content., Write realistic project files + mempalace.yaml to base_path.          Returns th (+252 more)

### Community 1 - "Community 1"
Cohesion: 0.02
Nodes (209): ABC, BackendClosedError, BackendError, BaseBackend, BaseCollection, count(), detect(), _DictCompatMixin (+201 more)

### Community 2 - "Community 2"
Cohesion: 0.01
Nodes (185): get_collection(), resolve(), cmd_sweep(), Sweep a transcript file or directory.      The sweeper deduplicates against its, _call_llm(), LLMConfig, _parsed_to_closet_lines(), closet_llm.py — Generate closets via a user-configured LLM for richer indexing. (+177 more)

### Community 3 - "Community 3"
Cohesion: 0.02
Nodes (185): test_detect_entities_benchmark(), cmd_compress(), Compress drawers in a wing using AAAK Dialect., collection_name(), entity_languages(), hall_keywords(), hook_desktop_toast(), hook_silent_save() (+177 more)

### Community 4 - "Community 4"
Cohesion: 0.02
Nodes (164): _collect_claude_messages(), _extract_content(), _format_tool_result(), _format_tool_use(), _messages_to_transcript(), normalize(), Load a file and normalize to transcript format if it's a chat export.     Plain, Try all known JSON chat schemas. (+156 more)

### Community 5 - "Community 5"
Cohesion: 0.02
Nodes (115): Validate and sanitize a wing/room/entity name.      Raises ValueError if the nam, Validate a knowledge-graph entity name (subject or object).      More permissive, Validate drawer/diary content length., sanitize_content(), sanitize_kg_value(), sanitize_name(), Exception, knowledge_graph.py — Temporal Entity-Relationship Graph for MemPalace ========== (+107 more)

### Community 6 - "Community 6"
Cohesion: 0.02
Nodes (142): AdapterClosedError, AdapterSchema, AuthRequiredError, BaseSourceAdapter, DimensionMismatchError, DrawerRecord, EmbedderIdentityMismatchError, FieldSpec (+134 more)

### Community 7 - "Community 7"
Cohesion: 0.03
Nodes (120): ambiguous_flags(), _empty(), EntityRegistry, load(), mode(), people(), projects(), Look up a word via Wikipedia REST API.     Returns inferred type (person/place/c (+112 more)

### Community 8 - "Community 8"
Cohesion: 0.02
Nodes (132): cmd_hook(), cmd_init(), cmd_instructions(), cmd_mcp(), cmd_migrate(), cmd_mine(), cmd_repair(), cmd_search() (+124 more)

### Community 9 - "Community 9"
Cohesion: 0.03
Nodes (115): _build_patterns(), classify_entity(), confirm_entities(), detect_entities(), extract_candidates(), _get_stopwords(), _normalize_langs(), _print_entity_list() (+107 more)

### Community 10 - "Community 10"
Cohesion: 0.03
Nodes (117): _count_human_messages(), _get_mine_dir(), hook_precompact(), hook_session_start(), hook_stop(), _log(), _maybe_auto_ingest(), _mine_already_running() (+109 more)

### Community 11 - "Community 11"
Cohesion: 0.04
Nodes (53): Delete an explicit tunnel by its ID., tool_delete_tunnel(), build_graph(), _canonical_tunnel_id(), create_tunnel(), delete_tunnel(), _endpoint_key(), find_tunnels() (+45 more)

### Community 12 - "Community 12"
Cohesion: 0.03
Nodes (52): Semantic search, returns compact result text., _bm25_scores(), build_where_filter(), _extract_drawer_ids_from_closet(), _first_or_empty(), _hybrid_rank(), Re-rank ``results`` by a convex combination of vector similarity and BM25., Build ChromaDB where filter for wing/room filtering. (+44 more)

### Community 13 - "Community 13"
Cohesion: 0.05
Nodes (32): get(), Default non-atomic update: get + merge + upsert.          Backends advertising `, upsert(), _check_entity_confusion(), _check_kg_contradictions(), check_text(), _edit_distance(), _extract_claims() (+24 more)

### Community 14 - "Community 14"
Cohesion: 0.05
Nodes (39): _edit_distance(), _get_speller(), _get_system_words(), _load_known_names(), Pull all registered names from EntityRegistry. Returns empty set on failure., Levenshtein distance between two strings., Spell-correct a user message.      Args:         text: Raw user message text., Spell-correct a single transcript line.     Only touches lines that start with ' (+31 more)

### Community 15 - "Community 15"
Cohesion: 0.07
Nodes (51): extract_people(), extract_subject(), extract_timestamp(), find_session_boundaries(), is_true_session_start(), _load_known_names_config(), _load_known_people(), _load_username_map() (+43 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (21): query_sanitizer.py — Mitigate system prompt contamination in search queries.  Pr, Extract the actual search intent from a potentially contaminated query.      Arg, sanitize_query(), Tests for query_sanitizer.py — system prompt contamination mitigation (#333).  T, Step 4: Fallback — take the last MAX_QUERY_LENGTH characters., Verify output length constraints., Verify sanitizer metadata is correct., Simulate realistic system prompt contamination patterns. (+13 more)

### Community 17 - "Community 17"
Cohesion: 0.07
Nodes (41): Save current entity mappings to a JSON config file., detect_rooms_from_files(), detect_rooms_from_folders(), detect_rooms_local(), get_user_approval(), print_proposed_structure(), Walk the project folder structure.     Find top-level subdirectories that match, Fallback: if folder structure gives no signal,     detect rooms from recurring f (+33 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (41): _disambiguate(), extract_memories(), _extract_prose(), _get_sentiment(), _has_resolution(), _is_code_line(), Quick sentiment: 'positive', 'negative', or 'neutral'., Check if text describes a RESOLVED problem. (+33 more)

### Community 19 - "Community 19"
Cohesion: 0.08
Nodes (17): _chunk_by_exchange(), _chunk_by_paragraph(), chunk_exchanges(), detect_convo_room(), One user turn (>) + the AI response that follows = one or more chunks.      The, Fallback: chunk by paragraph breaks., Score conversation content against topic keywords., Find all potential conversation files. (+9 more)

### Community 20 - "Community 20"
Cohesion: 0.11
Nodes (30): _get_palace_path(), _paginate_ids(), prune_corrupt(), repair.py — Scan, prune corrupt entries, and rebuild HNSW index ================, Delete corrupt IDs listed in corrupt_ids.txt., Rebuild the HNSW index from scratch.      1. Extract all drawers via ChromaDB ge, Resolve palace path from config., Pull all IDs in a collection using pagination. (+22 more)

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (29): dedup_palace(), dedup_source_group(), _get_palace_path(), get_source_groups(), dedup.py — Detect and remove near-duplicate drawers ============================, Show duplication statistics without making changes., Main entry point: deduplicate near-identical drawers across the palace., Resolve palace path from config. (+21 more)

### Community 22 - "Community 22"
Cohesion: 0.1
Nodes (18): bench_report_path(), bench_results(), bench_scale(), BenchmarkResults, config_dir(), kg_db(), palace_dir(), project_dir() (+10 more)

### Community 23 - "Community 23"
Cohesion: 0.16
Nodes (7): detect_hall(), Route content to a hall based on keyword scoring.      Halls connect rooms withi, The detect_hall function should exist and route content to the right hall., detect_hall should cache config to avoid disk reads per drawer., After first call, config should be cached — no new MempalaceConfig()., TestDetectHall, TestDetectHallCaching

### Community 24 - "Community 24"
Cohesion: 0.2
Nodes (14): export_palace(), _quote_content(), exporter.py — Export the palace as a browsable folder of markdown files.  Produc, Format content for a markdown blockquote, handling multiline., Sanitize a string for use as a directory/file name component., Export all palace drawers as markdown files organized by wing/room.      Streams, _safe_path_component(), Create a small palace with drawers across two wings for testing. (+6 more)

### Community 25 - "Community 25"
Cohesion: 0.17
Nodes (14): backend_version(), confirm_destructive_action(), contains_palace_database(), detect_chromadb_version(), extract_drawers_from_sqlite(), migrate(), Return True when path looks like a MemPalace ChromaDB directory., Require confirmation before destructive palace operations. (+6 more)

### Community 26 - "Community 26"
Cohesion: 0.18
Nodes (12): Instruction text output for MemPalace CLI commands.  Each instruction lives as a, Read and print the instruction .md file for the given name., run_instructions(), Tests for mempalace.instructions_cli — instruction text output., Valid name prints the .md file content., Every name in AVAILABLE should succeed without error., Invalid name should sys.exit(1) and print error to stderr., If the .md file is missing on disk, should sys.exit(1). (+4 more)

### Community 27 - "Community 27"
Cohesion: 0.25
Nodes (6): Regression tests for issue #225 — MCP stdio protection.  The MCP protocol multip, At import time, sys.stdout must point at sys.stderr so any stray     print() fro, `python -m mempalace.mcp_server` with empty stdin must produce     nothing on st, test_mcp_server_no_stdout_noise_on_clean_exit(), test_module_import_redirects_stdout_to_stderr(), test_restore_stdout_returns_real_stdout()

### Community 28 - "Community 28"
Cohesion: 0.4
Nodes (3): TDD: convo_miner.py must not silently drop transcripts larger than 10 MB.  Mirro, The cap must be well above any realistic transcript.          Long sessions and, TestConvoMinerSizeCap

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (1): When chroma.sqlite3 disappears, a cached collection should be invalidated.

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (1): Path to the memory palace data directory.

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (1): ChromaDB collection name.

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (1): Mapping of name variants to canonical names.

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (1): List of topic wing names.

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (1): Mapping of hall names to keyword lists.

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (1): Languages whose entity-detection patterns should be applied.          Reads from

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (1): Whether the stop hook saves directly (True) or blocks for MCP calls (False).

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (1): Whether the stop hook shows a desktop notification via notify-send.

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (1): Load entity mappings from a JSON config file.          Config format:         {

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (1): Estimate token count using word-based heuristic (~1.3 tokens per word).

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **465 isolated node(s):** `test_closets.py — Tests for the closet (searchable index) layer and the features`, `Worker for multiprocessing-spawn concurrency test. Writes its     critical-secti`, `The lock's contract is inter-*process* (multi-agent), not         inter-thread.`, `Palaces without closets return results via direct drawer search —         every`, `When a closet agrees with direct search on source_file, the         matching dra` (+460 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 29`** (1 nodes): `When chroma.sqlite3 disappears, a cached collection should be invalidated.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `Path to the memory palace data directory.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `ChromaDB collection name.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `Mapping of name variants to canonical names.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `List of topic wing names.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `Mapping of hall names to keyword lists.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `Languages whose entity-detection patterns should be applied.          Reads from`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `Whether the stop hook saves directly (True) or blocks for MCP calls (False).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `Whether the stop hook shows a desktop notification via notify-send.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `Load entity mappings from a JSON config file.          Config format:         {`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `Estimate token count using word-based heuristic (~1.3 tokens per word).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `basic_mining.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `convo_import.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MempalaceConfig` connect `Community 8` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 5`, `Community 9`, `Community 11`, `Community 12`, `Community 13`, `Community 19`, `Community 20`, `Community 21`, `Community 23`?**
  _High betweenness centrality (0.163) - this node is a cross-community bridge._
- **Why does `ChromaBackend` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 5`, `Community 6`, `Community 8`, `Community 11`, `Community 20`, `Community 21`, `Community 25`?**
  _High betweenness centrality (0.156) - this node is a cross-community bridge._
- **Why does `KnowledgeGraph` connect `Community 0` to `Community 1`, `Community 5`, `Community 6`, `Community 8`, `Community 11`, `Community 13`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Are the 238 inferred relationships involving `MempalaceConfig` (e.g. with `Benchmark-specific pytest configuration, fixtures, and CLI options.` and `Reset the MCP server's cached ChromaDB client/collection between tests.`) actually correct?**
  _`MempalaceConfig` has 238 INFERRED edges - model-reasoned connections that need verification._
- **Are the 205 inferred relationships involving `ChromaBackend` (e.g. with `TestToolCount` and `TestReadmeToolsExistInCode`) actually correct?**
  _`ChromaBackend` has 205 INFERRED edges - model-reasoned connections that need verification._
- **Are the 152 inferred relationships involving `PalaceDataGenerator` (e.g. with `TestSearchLatencyVsSize` and `TestSearchRecallAtScale`) actually correct?**
  _`PalaceDataGenerator` has 152 INFERRED edges - model-reasoned connections that need verification._
- **Are the 145 inferred relationships involving `KnowledgeGraph` (e.g. with `Benchmark-specific pytest configuration, fixtures, and CLI options.` and `Reset the MCP server's cached ChromaDB client/collection between tests.`) actually correct?**
  _`KnowledgeGraph` has 145 INFERRED edges - model-reasoned connections that need verification._
# Project Research Summary — MemPalace Belarusian i18n

**Project:** MemPalace Belarusian i18n contribution (`be.json` Narkamauka + `be-tarask.json` Tarashkievitsa)
**Domain:** Brownfield i18n locale data contribution to an existing Python package
**Researched:** 2026-04-20
**Overall confidence:** HIGH

---

## Executive Summary

This is a **pure-data, two-file PR** to upstream `MemPalace/mempalace`: add `mempalace/i18n/be.json` (Narkamauka) and `mempalace/i18n/be-tarask.json` (Tarashkievitsa) — both **full-tier** locales with all 7 schema sections, contributed via a single PR against the `develop` branch following the established locale-PR pattern (Russian #760, Italian #907, pt-br #117, Indonesian #778). The user is a native Belarusian speaker who will review every string before commit.

The four research dimensions converged on a sharp, narrow plan:

- **No code changes are needed** — the i18n module already supports auto-discovery (`_LANG_DIR.glob("*.json")`), case-insensitive lookup (`_canonical_lang.lower()`), hyphenated tags (`pt-br` precedent for `be-tarask`), and per-locale entity merge (`get_entity_patterns`). Drop the two files in `mempalace/i18n/`, change nothing else. Editing `__init__.py` is the **#1 anti-pattern** identified by ARCHITECTURE.
- **The risk surface is linguistic, not technical.** Tests catch missing keys, wrong interpolation placeholders, and short `aaak.instruction` — they catch nothing about translation quality. The **NATIVE-01 review gate is the only line of defense** against the explicit "this project has failed" condition (Russified Belarusian / Trasianka). PITFALLS surfaces 8 critical traps; STACK reinforces with a discipline-focused "What NOT to Use" matrix; FEATURES enumerates anti-features per schema section.
- **The single highest-risk technical decision** is the `entity.candidate_pattern` character class. Russian's `[А-ЯЁ]` silently drops Belarusian-specific letters `Ў` (U+040E) and `І` (U+0406) — verified empirically by STACK (`re.compile(r'[А-ЯЁ][а-яё]{1,19}').findall("Іван сказаў…")` returns `['Алёна']`, missing `Іван`). Belarusian MUST use `[А-ЯЁІЎ][а-яёіў]{1,19}`. Tests pass either way; the bug only manifests at runtime on real Belarusian text.

A 5-phase roadmap mirrors the recent locale-PR commit pattern (base file + entity section as separate atomic commits per file), preserves sequential per-file authorship to prevent orthography mixing, and ends with a tests + native-review + PR phase.

---

## Key Findings

### Recommended Stack (no new dependencies)

The "stack" splits into two layers (per STACK.md). Layer 1 — what we must honor — is non-negotiable:

**Core technologies (existing constraints):**
- **Python ≥ 3.9** (`pyproject.toml`, ruff `target-version = "py39"`) — locale JSON consumed identically across the CI matrix (3.9 / 3.11 / 3.13 Linux + 3.9 Windows + 3.9 macOS).
- **JSON UTF-8 no BOM** — `_LANG_DIR.read_text(encoding="utf-8")` requires it. `ensure_ascii=False` for human-readable Cyrillic in diffs.
- **Python `re` stdlib (Unicode-default)** — `\w` and `\b` work for Cyrillic out of the box; **no `re.UNICODE` flag needed, no `re.ASCII` flag allowed**.
- **No new runtime deps** — CONTRIBUTING.md:66 limits us to ChromaDB + PyYAML; pure-data PR trivially satisfies this.

**Existing CI gates we must pass:** `ruff check .` + `ruff format --check .` (only relevant if we touch `tests/test_i18n.py`); `pytest --cov-fail-under=80` across the matrix; Version Guard (untouched — no version bump).

Layer 2 (linguistic toolkit, doesn't ship) — primary references for the human translator:
- **Narkamauka:** Закон №420-З (2008 orthography law) at `pravo.by`; verbum.by GrammarDB (НАН Беларусі 2026/01); Тлумачальны слоўнік (Капылоў 2022); Skarnik.by (anti-Russification check).
- **Tarashkievitsa:** Buslakou/Viacorka/Sanko/Sauka 2005 rule book ("Беларускі клясычны правапіс") at knihi.com — exact reference cited by IANA for the `tarask` variant subtag; Пашкевіч 2006 EN→BE dictionary (classical orthography); be-tarask.wikipedia.org and svaboda.org as living corpora.
- **MT systems are NOT a translation source:** DeepL doesn't support Belarusian; Google/Yandex produce Russified output and lack Narkamauka/Tarashkievitsa distinction.

### Expected Schema Sections (table stakes, differentiators, anti-features)

A "feature" in this contribution is a **schema section**. Per FEATURES.md, every existing locale shares a 7-section shape:

**Table stakes** (test enforces — failing CI if absent):
- `terms.{palace, wing, closet, drawer}` — 4 hard nouns, non-empty
- `cli.mine_complete` — must contain `{closets}` AND `{drawers}` placeholders
- `cli.status_drawers` — must use `{count}`, NOT `{drawers}` (Korean-PR regression)
- `aaak.instruction` — string ≥ 10 chars; **the only section live in production today** (consumed by `closet_llm._call_llm`)

**Differentiators** (all required for full tier per PROJECT.md):
- Remaining 9 `terms` keys + 12 `cli` keys + entire `regex` section + entire `entity` section
- The **`entity` section is critical** for Belarusian — without it, candidate extraction falls back to English `[A-Z][a-z]` and **misses 100% of Cyrillic names**
- 6 of 13 existing locales are full tier (`en`, `hi`, `id`, `it`, `pt-br`, `ru`); we join that group

**Anti-features** (do NOT add — reviewers will reject):
- `entity.boundary_chars` — only for combining-mark scripts (Devanagari etc.). No-op for Cyrillic.
- Russian's `[А-ЯЁ]` candidate class — drops Belarusian `Ў`/`І` silently
- Translating `ru.json` strings instead of translating from `en.json` — produces Russified output (the explicit failure condition)
- `{drawers}` in `status_drawers` instead of `{count}` — exact bug Korean shipped; regression-tested
- `ensure_ascii=True` JSON serialization — illegible diffs, 3× larger files
- UTF-8 BOM — silent JSON parse failure
- New top-level keys (e.g., `"orthography": "narkamauka"`) — unused; use `label` autonym + filename for the indication

**Defer (out of scope per PROJECT.md):** Latin-script Belarusian (`Łacinka`); Belarusian-Russian disambiguation in `entity_detector`; non-English search quality (issue #712 — embedding-model swap, not i18n).

### Architecture Approach (existing — what we must honor)

Per ARCHITECTURE.md, a locale file participates in **two decoupled flows** over the same on-disk JSON:

```
mempalace/i18n/<lang>.json on disk (auto-discovered via glob)
              │
       ┌──────┴──────┐
       ▼             ▼
   FLOW A         FLOW B
"string lookup"  "entity merge"
(lang/label/    (entity section
 terms/cli/      only)
 aaak/regex)
       │             │
       ▼             ▼
load_lang(lang)  get_entity_patterns(langs=())
       │             │
       ▼             ▼
  _strings       _entity_cache (per-lang-tuple)
       │             │
       ▼             ▼
  t(), get_regex   _build_patterns / _pronoun_re /
       │             _get_stopwords (lru_cache)
       ▼             │
  Dialect.__init__   ▼
  closet_llm._call_  extract_candidates / score_entity
                     palace._candidate_entity_words
```

**Key components our files plug into:**
1. **`mempalace/i18n/__init__.py`** — auto-discovers JSON files; provides `load_lang`, `t`, `get_regex`, `get_entity_patterns`. We change nothing here.
2. **`mempalace/dialect.py:Dialect.__init__`** — reads `aaak.instruction` and `regex.*` (the latter stored in `lang_regex` but never re-read — `regex` is currently dead-weight in production).
3. **`mempalace/closet_llm.py:_call_llm`** — concatenates `aaak.instruction` into the LLM prompt. **Only live production consumer of `t()`.**
4. **`mempalace/entity_detector.py`** — entire module is the consumer of merged `entity` patterns via `get_entity_patterns(langs)`.
5. **`mempalace/palace.py:_candidate_entity_words`** — uses `entity.candidate_pattern` only, gated on `MEMPALACE_ENTITY_LANGUAGES` env or `mempalace init --lang be`.

**Critical non-finding:** `mempalace/cli.py` does **NOT** import i18n — `cli.*` keys are functionally dead today (only tests exercise them). We translate them anyway because the test contract requires it AND because they're infrastructure-ready for a future CLI wiring. Same story for `regex.*` (loaded into `Dialect.lang_regex`, never read).

**Filename rule:** lowercase, hyphen (not underscore), `.json` suffix → `be.json` and `be-tarask.json`. Auto-discovered. Case-insensitive at lookup. Matches IANA + `pt-br` precedent.

### Critical Pitfalls (top 5 of 8 documented)

1. **Translating from `ru.json` instead of `en.json`** — the project-failing default. Native review (NATIVE-01) is the only safety net. Watch for false friends (`вяселле` BE = wedding, RU = fun; `благі` BE = bad, RU = good); past-tense `-аў`/`-ла`/`-лі` shape; `і` (not `и`); `ў` (not `у`); apostrophe (not `ъ`).
2. **Mixing Tarashkievitsa and Narkamauka in one file** — writing both files in one sitting causes mode-switching errors. Sequential per-file authorship required (PITFALLS Pitfall 2). Soft-sign placement, foreign-l adaptation (`план`/`плян`), and `-сістэма`/`-сыстэма` are the most common leakage points.
3. **Past-tense verb pattern shape** — Belarusian masc `-ў` has no trailing vowel, so the Russian elegant `сказал[аи]?` character-class trick does NOT extend. Each verb needs explicit 3-way alternation: `\b{name}\s+(?:сказа(?:ў|ла|лі)|казаў|казала|казалі)\b`.
4. **Belarusian-letter regex gap** — using Russian's `[А-ЯЁ][а-яё]{1,19}` candidate pattern silently drops `Ў`/`І`/`ў`/`і`. Empirically verified. Use `[А-ЯЁІЎ][а-яёіў]{1,19}`. Tests pass either way; the bug only shows on real Belarusian text.
5. **Empty `entity.stopwords` array** — English fallback only fires if NO requested locale has any entity section; with `("be","en")` the BE locale's *empty* stopword set is used (English doesn't add Belarusian function words). Belarusian function words like `Гэта`/`Так`/`Ну`/`Калі` capitalized at sentence-start become candidate "entities" and pollute detection. Need ≥30 native Belarusian entries.

Three additional pitfalls are documented in PITFALLS.md: incomplete pronoun-case coverage, `_entity_cache` staleness during local dev, and the apostrophe codepoint controversy (U+0027 vs U+02BC vs U+2019 — recommendation: U+0027 for pragmatic compatibility).

---

## Implications for Roadmap

The four researchers converged on the same phase structure. This is the recommendation for the gsd-roadmapper:

### Phase 1 — `be.json` (Narkamauka) base file
**Rationale:** Mirrors commit pattern of recent locale PRs (`b87ada3` Russian base, `2e998db` Italian base). Establishes Belarusian presence in the codebase before tackling the higher-risk entity section.
**Delivers:** `mempalace/i18n/be.json` with `lang`, `label`, `terms` (13), `cli` (14), `aaak.instruction`, `regex` (4) — everything except `entity`.
**Requirements addressed:** BE-01 (load), BE-02 (terms), BE-03 (cli), BE-04 (aaak), BE-05 (regex).
**Avoids:** Pitfalls 1, 3 (false friends, past-tense shape) caught at native review before commit.
**Test gate:** `pytest tests/test_i18n.py tests/test_i18n_lang_case.py -v` passes.

### Phase 2 — `be.json` (Narkamauka) entity section
**Rationale:** Mirrors `d6bd7de` (Russian entity), `69453b2` (Italian entity). Atomic commit isolates the highest-review-surface section. Lets the implementer iterate on `candidate_pattern` and verb alternations without rebasing the base file.
**Delivers:** `entity` block in `be.json` with `candidate_pattern` = `[А-ЯЁІЎ][а-яёіў]{1,19}`, `multi_word_pattern`, `person_verb_patterns` (~15 with gender/aspect alternation), `pronoun_patterns` (~9-12 covering 6 cases × 3 genders), `dialogue_patterns` (4), `direct_address_pattern` (≥5 alternatives), `project_verb_patterns` (~10), `stopwords` (≥30, native Belarusian). **No `boundary_chars`.**
**Requirements addressed:** BE-06 (entity).
**Avoids:** Pitfalls 4, 5 (Belarusian-letter regex gap, empty stopwords) verified at native review and entity-detector smoke test.
**Test gate:** `pytest tests/test_i18n.py tests/test_i18n_lang_case.py tests/test_entity_detector.py -v` plus runtime smoke: `_build_patterns("Іван", ("be",))` matches.

### Phase 3 — `be-tarask.json` (Tarashkievitsa) base file
**Rationale:** Sequential after Phase 2 lock — prevents orthography mixing (Pitfall 2). Same shape as Phase 1 with Tarashkievitsa orthography.
**Delivers:** `mempalace/i18n/be-tarask.json` with `lang`, `label` (`"Беларуская (тарашкевіца)"` or native-reviewer choice), `terms`, `cli`, `aaak.instruction`, `regex` — Tarashkievitsa lexical choices where they diverge from Narkamauka (`зала`/`заля`, `план`/`плян`, `сістэма`/`сыстэма`, etc.).
**Requirements addressed:** BE-07, BE-08.

### Phase 4 — `be-tarask.json` (Tarashkievitsa) entity section
**Rationale:** Mirrors Phase 2 with Tarashkievitsa morphology (soft-sign reflexives `-сь`/`-ся`, `-ьц-` clusters). Same character class as `be.json` (alphabet doesn't change between orthographies).
**Delivers:** `entity` block in `be-tarask.json`.
**Requirements addressed:** BE-09.

### Phase 5 — Tests + native review + PR submission
**Rationale:** Locks the contribution against the test contract, executes the NATIVE-01 hard gate one final time across both files, and ships the PR per CONTRIBUTING.md.
**Delivers:**
- (Optional) extend `tests/test_i18n.py::test_dialect_compress_samples` with one Belarusian sample sentence (TEST-02). ~6 lines added.
- Final native-speaker review pass on both files (NATIVE-01).
- Pre-PR gates: `ruff check .` + `ruff format --check .` (test changes only) + `pytest tests/ -v --cov=mempalace --cov-fail-under=80`.
- PR submitted to `MemPalace/mempalace`'s `develop` branch from `feat/i18n-belarusian`, with description following the prior i18n-PR template (cite #760, #907, #778).
**Requirements addressed:** NATIVE-01, TEST-01, TEST-02, PR-01, PR-02.

### Phase Ordering Rationale

- **Sequential per-file authorship (be → be-tarask)** prevents orthography mixing (PITFALLS Pitfall 2 — the highest-cost mistake to recover from after PR submission).
- **Base + entity split per file** mirrors the established commit pattern (verified via `user-git` `git_show` on commits `b87ada3`/`d6bd7de`, `2e998db`/`69453b2`, `3d13a72`). Reviewers expect this shape; deviating adds cognitive friction.
- **Native review is the LAST gate before each commit**, not just before PR submission (PITFALLS Pitfall 1 — Russified Belarusian is the failure mode the project explicitly fears).
- **Tests + PR as a final phase** (not interspersed) so the implementer can focus on translation work without context-switching to ruff/CI concerns until everything is locked.

### Research Flags

Phases that may need light additional research during planning:

- **Phase 2 / Phase 4:** Native reviewer needs verbum.by GrammarDB tabs open for verb conjugation lookups. Plan budget for cross-referencing every `person_verb_patterns` entry against the inflectional database.

Phases with standard patterns (skip planning research):

- **Phase 1 / Phase 3:** Schema is identical to `ru.json`'s shape; only translation work. No technical research needed.
- **Phase 5:** PR conventions are documented in CONTRIBUTING.md and mirrored in prior i18n PRs.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Existing technical contract (Python, JSON, ruff, pytest, CI) | **HIGH** | Every gate read from source files; behavior verified empirically (Cyrillic regex, JSON UTF-8 round-trip). |
| BCP 47 tags (`be`, `be-tarask`) | **HIGH** | IANA Language Subtag Registry fetched directly (file-dated 2026-04-09); `tarask` cites the exact 2005 Buslakou/Viacorka/Sanko/Sauka rule book. |
| Schema sections + test contract | **HIGH** | Every assertion in `tests/test_i18n.py`, `tests/test_i18n_lang_case.py`, `tests/test_entity_detector.py` mapped to a sub-key. |
| Cross-locale precedent (which sections each of 13 existing locales has) | **HIGH** | All 13 files read; counts verified empirically. |
| Live consumer surface (who reads what) | **HIGH** | Repo-wide grep on 4 import patterns; cli.py absence verified twice. |
| Recent locale-PR commit pattern | **HIGH** | `user-git` `git_show` verified verbatim 5 commits (`b87ada3`, `d6bd7de`, `2e998db`, `69453b2`, `3d13a72`). |
| Belarusian linguistic resources | **HIGH** for primary (verbum.by, pravo.by, knihi.com all live and queried); **MEDIUM** for living-corpus references (be.wikipedia.org, be-tarask.wikipedia.org — community-edited). |
| Belarusian-specific traps (false friends, past-tense, orthography divergence) | **HIGH** | Cross-checked Wikipedia/Wikibooks/MovaLark/Vitba; multiple sources agree. |
| Cyrillic regex behavior (`\b`, `\w`, `[А-ЯЁІЎ]` coverage) | **HIGH** | Empirically verified in Python 3.9. |
| Apostrophe codepoint choice (U+0027 vs U+02BC vs U+2019) | **MEDIUM** | Project-owner decision; recommendation is U+0027 for pragmatic compatibility but not prescriptive. |

**Overall confidence:** HIGH — the technical surface is small, fully understood, and well-documented; the linguistic surface is bounded by clear references and the NATIVE-01 review gate.

### Open Questions (consolidated from all four research files, with recommendations)

| # | Question | Recommendation | Resolution path |
|---|----------|----------------|-----------------|
| 1 | `label` autonym for Tarashkievitsa: `"Беларуская (тарашкевіца)"` / `"Беларуская тарашкевіца"` / `"Беларуская клясычная"`? | Use `"Беларуская (тарашкевіца)"` to match the Wikimedia convention (be-tarask.wikipedia.org's self-naming). | Native reviewer confirms during Phase 3. |
| 2 | Apostrophe codepoint for word-internal apostrophes: U+0027 (`'` ASCII), U+02BC (`ʼ` modifier letter), or U+2019 (`’` right single quotation)? | **U+0027** for pragmatic compatibility — matches how users actually type and how every existing locale file represents them. Document the choice in PR description. | Lock in Phase 1 (schema design); apply consistently across both files. |
| 3 | Tarashkievitsa lexical choices where the 2005 rule book is silent (modern technical terms like "drawer", "deploy", "system") | Defer to translator's judgment using Pashkievich 2006 dictionary + svaboda.org corpus + native review. | Per-string decision in Phases 3-4. |
| 4 | `cli.mine_skip` — translate `--force` literally or to a Belarusian flag name? | Keep `--force` literal — matches every existing locale (CLI flag names are not translated). | Apply uniformly in Phase 1 and Phase 3. |
| 5 | Aspectual pair coverage in `person_verb_patterns` — include both imperfective (`казаў`/`казала`/`казалі`) AND perfective (`сказаў`/`сказала`/`сказалі`) for each verb? | **Yes** — doubling pattern count from ~15 to ~25-30 has minimal `lru_cache` impact; aspect coverage materially improves recall. | Native reviewer confirms in Phase 2. |
| 6 | Include 2nd-person formal pronouns (`Вы`/`Вас`/`Вам`) in `pronoun_patterns`? | **Yes** for parity with pt-br precedent (added `você`/`seu`/`sua`); native reviewer should flag if false-positive rate becomes a concern in business writing. | Phase 2 / Phase 4. |
| 7 | Whether to extend `tests/test_i18n.py::test_dialect_compress_samples` with a Belarusian sample? | **Yes** — captured as PROJECT.md TEST-02; raises coverage slightly; demonstrates good citizenship. | Phase 5 (optional commit). |

**No question is blocking** — all can be resolved during the implementation phases by the native-reviewer translator.

---

## Sources

### Primary (HIGH confidence)
- **Codebase reads** — `mempalace/i18n/__init__.py` (286 lines), `mempalace/dialect.py:300-348`, `mempalace/closet_llm.py:115-134`, `mempalace/entity_detector.py` (591 lines), `mempalace/palace.py:_candidate_entity_words`, `mempalace/cli.py` (no i18n imports), all 13 existing locale JSON files, 3 i18n test files, `pyproject.toml`, `CONTRIBUTING.md`, `.github/workflows/ci.yml`.
- **`user-git` MCP** — `git_show b87ada3 d6bd7de 2e998db 69453b2 3d13a72` (verbatim commit messages and patches verified). `git log --follow mempalace/i18n/__init__.py` for module evolution. `git log --all -- 'mempalace/i18n/*'` for locale-PR pattern.
- **`user-context7` MCP** — `/python/cpython` `re.rst` for `\w`/`\b` Unicode-default behavior; `Doc/whatsnew/3.5.rst` for `ensure_ascii=False` performance.
- **`user-fetch` MCP** — IANA Language Subtag Registry (file-dated 2026-04-09), `https://be.wikipedia.org/wiki/Беларуская_мова`, `https://be-tarask.wikipedia.org/wiki/Беларуская_мова`, `https://verbum.by/`, `https://verbum.by/grammardb/?word=палац`, `https://www.skarnik.by/`, `https://github.com/MemPalace/mempalace/blob/develop/CONTRIBUTING.md`.
- **Empirical Python testing** — verified `[А-ЯЁ][а-яё]{1,19}` drops `Іван`; `[А-ЯЁІЎ][а-яёіў]{1,19}` matches it; `\b` works for Cyrillic without flags.

### Secondary (MEDIUM confidence)
- Wikipedia / Wikibooks — Taraškievica orthography differences, false-friends list, past-tense paradigm.
- MovaLark, Vitba.org — Belarusian verb conjugation tables.
- be.wiktionary.org closed-class word categories — preposition/conjunction/particle lists for stopwords.
- ICANN, MovaLark — apostrophe codepoint conventions in IDNA.

### Tertiary (LOW confidence — none load-bearing)
- stopwords-iso community list — useful starting point for `entity.stopwords` but **must filter through native review** (auto-generated from corpora; contains questionable entries).
- NLTK Belarusian stopwords — smaller curated list; cross-reference only.

---

## Cross-Document Convergences (the 9 things all four researchers agree on)

1. **No code changes** — i18n module already supports everything Belarusian needs (auto-discovery, case-insensitive, hyphenated tags, per-locale entity merge, English fallback).
2. **Two files: `be.json` + `be-tarask.json`**, both **full tier** with all 7 schema sections.
3. **`ru.json` is structural template only, NOT a translation source.** Translate from `en.json` with `ru.json` as a "what does an entity section look like" reference.
4. **Belarusian alphabet requires `[А-ЯЁІЎ][а-яёіў]{1,19}`** — the `[А-ЯЁ]` from `ru.json` silently drops `Ў`/`І`. Empirically verified.
5. **No `boundary_chars`** — only for combining-mark scripts (Devanagari, Arabic, Hebrew, Thai, Tamil, Burmese, Khmer). Cyrillic letters fit in `\w` already.
6. **NATIVE-01 review is the hard gate** — tests catch structural defects only; translation quality (the project-failing condition) requires native eyes.
7. **Past-tense verbs need explicit gender alternation** (`сказа(ў|ла|лі)`) — Russian `[аи]?` trick doesn't extend to Belarusian masc `-ў`.
8. **Sequential per-file authorship** (`be.json` first, lock, then `be-tarask.json`) — prevents orthography mixing (the costliest post-PR mistake).
9. **Single PR with multiple atomic commits** (base + entity per file) — mirrors recent locale-PR pattern verified in git history.

---

*Research completed: 2026-04-20*
*Synthesizer: orchestrator (gsd-research-synthesizer subagent unavailable; synthesis written from full reads of STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md)*
*Ready for roadmap: yes*

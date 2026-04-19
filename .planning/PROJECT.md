# MemPalace Belarusian i18n (`be` + `be-tarask`)

## What This Is

A focused contribution to the upstream [`MemPalace/mempalace`](https://github.com/MemPalace/mempalace)
package adding **two Belarusian locale files** to `mempalace/i18n/`:

- `be.json` — **Narkamauka** (Standard Belarusian, the post-1933 official orthography
  used in state media, schools, and `be.wikipedia.org`).
- `be-tarask.json` — **Tarashkievitsa** (Classical Belarusian, pre-1933, BCP 47 tag
  `be-tarask`, used by `be-tarask.wikipedia.org`, the Latvian-state-funded
  Radio Svaboda, and parts of the diaspora).

Each file is **full-tier**: all seven sections — `lang`, `label`, `terms`, `cli`,
`aaak`, `regex`, and `entity` — translated and tuned for Belarusian linguistics.
The user is a **native Belarusian speaker** who will personally review every
string before it is committed and again before the upstream PR is opened.

## Core Value

**Two upstream-merged Belarusian locales that pass `pytest tests/` and read like
they were written by a native speaker — not transliterated from Russian and not
machine-translated.**

If the file ships but reads like clumsy Russian-with-Belarusian-characters, this
project has failed regardless of test coverage.

## Requirements

### Validated

<!-- Existing capabilities the i18n system already provides — these constrain how we work, not what we build. -->

- ✓ Locale auto-discovery via `_LANG_DIR.glob("*.json")` — no registry edits needed (`mempalace/i18n/__init__.py:39-47`) — existing
- ✓ Case-insensitive BCP 47 lookup (`be`, `BE`, `Be` all resolve) — existing (PR #927 / `0174b93`)
- ✓ Hyphenated tags supported (`pt-br`, `zh-CN`, `be-tarask` ✓) — existing
- ✓ Per-locale `entity` section auto-merged by `get_entity_patterns(languages=...)` — existing
- ✓ Script-aware `boundary_chars` infra for combining-mark scripts — existing (commits `f895bc5`, `21da870`); **not needed for Cyrillic** (Belarusian fits within `\w`)
- ✓ English fallback when a section is missing — existing (`__init__.py:255-257`)

### Active

- [ ] **BE-01**: `mempalace/i18n/be.json` (Narkamauka) loads via `load_lang("be")` and passes all `tests/test_i18n.py` checks
- [ ] **BE-02**: `be.json` `terms` section translates all 13 nouns into Narkamauka
- [ ] **BE-03**: `be.json` `cli` section translates all 14 user-facing strings with correct `{var}` interpolation
- [ ] **BE-04**: `be.json` `aaak.instruction` is a fluent Narkamauka instruction (≥ 10 chars, instructs LLM to compress text using Belarusian inflectional shape)
- [ ] **BE-05**: `be.json` `regex` section: `topic_pattern`, `stop_words`, `quote_pattern`, `action_pattern` — all tuned for Cyrillic + Belarusian
- [ ] **BE-06**: `be.json` `entity` section: `candidate_pattern`, `multi_word_pattern`, `person_verb_patterns` (verbs of speech/feeling/decision in Belarusian aspect/gender forms), `pronoun_patterns` (ён/яна/яны and their cases), `dialogue_patterns`, `direct_address_pattern` (вітаю/прывітанне/дзякуй forms), `project_verb_patterns`, `stopwords` (Narkamauka prepositions/conjunctions/particles)
- [ ] **BE-07**: `mempalace/i18n/be-tarask.json` (Tarashkievitsa) loads via `load_lang("be-tarask")` and passes all `tests/test_i18n.py` checks
- [ ] **BE-08**: `be-tarask.json` mirrors the `be.json` schema but uses Tarashkievitsa orthography throughout — soft-sign before consonants (сьвет vs свет), `ў` rules, foreign-word adaptation, and Tarashkievitsa-specific lexical choices where they differ from Narkamauka
- [ ] **BE-09**: `be-tarask.json` `entity` section uses Tarashkievitsa morphology where it diverges (e.g. instrumental endings, soft-sign markings)
- [ ] **NATIVE-01**: Every translated string passes a native-speaker review pass by the project owner before commit
- [ ] **TEST-01**: `pytest tests/test_i18n.py tests/test_i18n_lang_case.py tests/test_entity_detector.py -v` passes locally with both new files
- [ ] **TEST-02**: `Dialect("be")` and `Dialect("be-tarask")` instantiate, `compress()` returns non-empty Belarusian text on a Belarusian sample sentence
- [ ] **PR-01**: Open one PR against `MemPalace/mempalace`'s `develop` branch following CONTRIBUTING.md conventions: `feat/i18n-belarusian` branch, conventional-commit messages, `area/i18n` label, ruff-clean, tests passing
- [ ] **PR-02**: PR description follows the prior-i18n-PR template (commits #760, #907, #778 as references): native name, orthography rationale, link to two-file rationale, screenshot of `pytest` output

### Out of Scope

- **Improving non-English semantic search quality** — open issue [#712](https://github.com/MemPalace/mempalace/issues/712) calls out that ChromaDB's default embedding model is English-only; non-English search is degraded across all locales. Out of scope here — this is an embedding-model swap, not an i18n contribution.
- **Latin-script Belarusian (`Łacinka`)** — historical/diaspora orthography; no precedent in upstream and no clear consumer.
- **Translating MemPalace docs/README/website** — locale files only. README sections like "Adding a new language" are referenced by `mempalace/i18n/__init__.py:13` but **don't currently exist** — surfacing that doc gap is not in this scope.
- **Adding new infra to `mempalace/i18n/__init__.py`** — the existing module already supports auto-discovery, case-insensitive lookup, hyphenated tags, and per-locale entity merge. Belarusian needs zero infra changes.
- **Belarusian-Russian disambiguation in `entity_detector`** — same Cyrillic block, would require language detection, materially changes the design contract. Defer.
- **Discord/community announcement** — not a code deliverable.

## Context

**Upstream project:**
- `MemPalace/mempalace` — Python 3.9+ local-first memory store, MIT-licensed, distributed on PyPI as `mempalace==3.3.0`. PR target branch is `develop`. CI gates: ruff (lint + format), pytest matrix (Linux py3.9/3.11/3.13, Windows py3.9, macOS py3.9), coverage `--cov-fail-under=80`.
- 13 existing locales (en, de, es, fr, hi, id, it, ja, ko, pt-br, ru, zh-CN, zh-TW) under `mempalace/i18n/`.

**Reference template:**
- `ru.json` is the obvious template for Cyrillic structure (161 lines, full tier, includes `entity` with Cyrillic candidate/multi-word patterns and Russian-specific person verbs/pronouns/direct-address). It will be the source for **structural** copying — but every string must be translated to Belarusian, not transliterated from Russian. The two languages share script and ~70-80% lexical overlap but diverge sharply on function words, verb conjugation, and some core terms.

**Recent i18n history (commit pattern to mirror):**
- `feat: add Russian language support to i18n module` (b87ada3, base file)
- `feat(i18n): add entity detection section to Russian locale` (d6bd7de, entity)
- `fix(i18n): apply review feedback on ru.json (#760)` (3e49522, review)
- `feat(i18n): expand Russian entity stopwords with prepositions and conjunctions` (4b998de, polish)

Italian, Hindi, pt-br all followed similar 1-3 commit patterns inside a single PR. Plan to do the same: one PR, multiple atomic commits.

**Test contract (`tests/test_i18n.py`):**
- `test_all_languages_load` — every JSON loads, has `terms`/`cli`/`aaak` sections, has `palace`/`wing`/`closet`/`drawer` terms (non-empty), has `aaak.instruction`.
- `test_interpolation` — `cli.mine_complete` interpolates `{closets}` and `{drawers}`.
- `test_dialect_loads_lang` — `Dialect(lang=X).aaak_instruction` length > 10.
- `test_dialect_compress_samples` — does not include Belarusian today; we should add a Belarusian sample to extend coverage (per the "Add or update tests" PR rule in CONTRIBUTING.md).

**Open i18n PRs/issues (none competing):**
The 12 open items at `?label=area/i18n&state=open` are all Unicode/encoding bugs (Windows CJK crashes, KG triple Unicode rejection, search quality on non-English) — not new-language contributions. Belarusian PR will land in a clean lane.

**Belarusian linguistic context (drives translation quality):**
- Belarusian is East Slavic, written in Cyrillic. Two living orthographies coexist: Narkamauka (official since 1933, post-Soviet reform) and Tarashkievitsa (pre-1933, used by independent media, Wikipedia's `be-tarask`).
- Key orthographic differences: Tarashkievitsa marks palatalization with soft sign before consonants (сьвет vs свет, прыняцьце vs прыняцце); Narkamauka uses fewer soft signs.
- Belarusian-specific letters: `ў` (short u — distinct from Russian `у`), `і` (dotted i — replaces Russian `и`), apostrophe `'` (separates prefix from soft vowel; cf. Russian hard sign `ъ`).
- Common term mapping (rough draft, subject to native review):
  - `palace` → `палац`  
  - `wing` → `крыло`  
  - `hall` → `зала` (Narkamauka) / `заля` (Tarashkievitsa often `заля`)  
  - `closet` → `шафа`  
  - `drawer` → `шуфляда` (both orthographies)  
  - `mine` (verb, "to extract") → `здабываць` / `капаць`  
- Verbs of speech: казаў/казала, спытаў/спытала, адказаў/адказала, расказаў/расказала. Both orthographies share core forms; Tarashkievitsa may use older variants (e.g. `сказаў` vs Narkamauka's preferred `сказаў`).

**MCP / research tools available for this project:**
- `user-mempalace` MCP — for in-codebase semantic search of i18n patterns
- `user-git` MCP — for deep git history inspection of each locale file
- `user-context7` MCP — for up-to-date docs on `pytest`, BCP 47 tooling, etc.
- `user-sequential-thinking` MCP — for multi-step reasoning during entity-pattern translation
- `user-fetch` / `user-tavily-remote` — for GitHub PR/issue inspection (no `gh` CLI installed)

## Constraints

- **Tech stack**: JSON only — no new Python dependencies, no infra changes to `mempalace/i18n/__init__.py`. Pure data contribution.
- **Encoding**: UTF-8, no BOM, ensure-ascii-false serialization. The `_LANG_DIR.read_text(encoding="utf-8")` in `__init__.py:57` requires this.
- **JSON schema parity**: Both files must match the schema established by `ru.json` for the `entity` section so `_collect_entity_section` (`__init__.py:162`) consumes them without surprise.
- **No `boundary_chars`**: Cyrillic characters fit within Python's `\w`. Adding `boundary_chars` would be a no-op and confusing — leave it out.
- **CI**: Must pass `ruff check .` and `ruff format --check .`. JSON files are not formatted by ruff but the surrounding test changes (if any) must be ruff-clean.
- **Coverage gate**: `--cov-fail-under=80`. Adding two JSON files plus one optional Belarusian sample to `test_dialect_compress_samples` keeps coverage neutral or improves it.
- **Native-speaker review gate**: No string is committed without the project owner's review. This is a hard gate, not a recommendation.
- **Scope discipline**: Resist scope creep into the "non-English search quality" rabbit hole — that's a separate, deeper project (#712).

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Ship both `be.json` and `be-tarask.json` rather than one default | Both orthographies have living user bases (state media + Wikipedia for Narkamauka; independent media + diaspora for Tarashkievitsa). Picking one would alienate ~half the audience. Cost is small (~6KB × 2). | — Pending (validated when PR is merged) |
| Full tier (with `entity` section) for both files | User chose "Full" explicitly. Without `entity`, person/project detection on Belarusian text falls back to English patterns and misses Cyrillic names entirely (the `[A-Z][a-z]` candidate pattern can't see `[А-ЯЁ]`). Full tier is the only useful choice for actual Belarusian users. | — Pending |
| Use `ru.json` as a structural template, not a translation source | Russian and Belarusian share script and grammar but diverge on function words, verb forms, and lexical choices. Translating from `ru.json` would produce subtly-Russian Belarusian — the worst outcome. Translate each string from English (`en.json`) with Russian only as a "what does this construction look like in a Slavic script" reference. | — Pending |
| BCP 47 tag for Tarashkievitsa is `be-tarask` (lowercase) | IANA-registered subtag (`tarask`); matches `be-tarask.wikipedia.org` and the Wikimedia convention. Lowercase per `_canonical_lang`'s case-folding (and consistent with `pt-br`). | ✓ Good (validated against IANA registry + existing pt-br precedent) |
| One PR with multiple atomic commits, not two PRs | Mirrors recent i18n PR pattern (Russian, Italian, pt-br all single-PR). Reviewer sees both orthographies side-by-side, easier to spot inconsistencies. Branch: `feat/i18n-belarusian`. | — Pending |
| No new module-level infra | The i18n module already handles every Belarusian need. Adding code = extra review surface, no benefit. Strictly data-only PR. | — Pending |
| Defer Latin-script Belarusian (Łacinka) | No upstream precedent for non-Cyrillic Belarusian; would need a `be-Latn` tag (BCP 47 script subtag); no clear user signal. Capture in Out of Scope. | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-20 after initialization*

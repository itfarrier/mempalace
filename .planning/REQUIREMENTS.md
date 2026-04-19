# Requirements: MemPalace Belarusian i18n

**Defined:** 2026-04-20
**Core Value:** Two upstream-merged Belarusian locales that pass `pytest tests/` and read like they were written by a native speaker — not transliterated from Russian and not machine-translated.

---

## v1 Requirements

Requirements for the initial PR. Each maps to exactly one roadmap phase (filled in `## Traceability` after roadmap creation).

### Locale Files (file-level structure & loading)

- [ ] **LOC-01**: `mempalace/i18n/be.json` exists, loads via `from mempalace.i18n import load_lang; load_lang("be")`, and is auto-discovered by `available_languages()`.
- [ ] **LOC-02**: `mempalace/i18n/be-tarask.json` exists, loads via `load_lang("be-tarask")`, is auto-discovered, and resolves case-insensitively (`load_lang("BE-TARASK")` returns the same dict per `tests/test_i18n_lang_case.py`).
- [ ] **LOC-03**: Both files are encoded UTF-8 without BOM. First byte is `0x7B` (`{`), not `EF BB BF`. Verifiable with `head -c 3 mempalace/i18n/be.json | xxd`.
- [ ] **LOC-04**: Neither file declares `entity.boundary_chars`. Belarusian Cyrillic letters fit in `\w`; the field is for combining-mark scripts only (Hindi precedent).
- [ ] **LOC-05**: No changes to `mempalace/i18n/__init__.py`, `mempalace/entity_detector.py`, or any other production module. Pure-data PR.
- [ ] **LOC-06**: Both files serialized with `ensure_ascii=False` and `indent=2` — Cyrillic is human-readable in PR diffs (`ru.json`/`zh-CN.json` precedent).
- [ ] **LOC-07**: Both files include `lang` (matches file stem) and `label` (autonym) top-level keys per the convention shared by all 13 existing locales.

### Translation — Narkamauka (`be.json`)

- [ ] **NARK-01**: `be.json` `terms` section contains all 13 keys translated to Narkamauka (`palace`, `wing`, `hall`, `closet`, `drawer`, `mine`, `search`, `status`, `init`, `repair`, `migrate`, `entity`, `topic`). Hard-required by tests: `palace`, `wing`, `closet`, `drawer` (non-empty per `tests/test_i18n.py:20-21`).
- [ ] **NARK-02**: `be.json` `cli` section contains all 14 keys with correct `{var}` interpolation per the schema in `STACK.md` § "JSON Schema". Specifically: `mine_complete` includes `{closets}` AND `{drawers}` literal placeholders; `status_drawers` uses `{count}` (NOT `{drawers}` — Korean-PR regression).
- [ ] **NARK-03**: `be.json` `aaak.instruction` is a fluent Narkamauka sentence ≥ 10 characters that instructs an LLM to compress text in Belarusian (the only `cli/aaak/regex` section live-consumed in production today, by `closet_llm._call_llm`).
- [ ] **NARK-04**: `be.json` `regex` section contains all 4 keys (`topic_pattern`, `stop_words`, `quote_pattern`, `action_pattern`) tuned for Narkamauka. `topic_pattern` includes Belarusian-specific letters (`ІЎіў`); `stop_words` uses native Belarusian function words (NOT translated wholesale from Russian); `quote_pattern` accepts `«»` and `"`; `action_pattern` uses Belarusian past-tense `-ў`/`-іў`/`-аў` endings.
- [ ] **NARK-05**: `be.json` `entity` section contains all 8 sub-keys (no `boundary_chars`): `candidate_pattern`, `multi_word_pattern`, `person_verb_patterns`, `pronoun_patterns`, `dialogue_patterns`, `direct_address_pattern`, `project_verb_patterns`, `stopwords`. The character class `[А-ЯЁІЎ][а-яёіў]{1,19}` is required for both candidate and multi-word patterns (verified empirically — Russian's `[А-ЯЁ]` drops `Ў`/`І`).
- [ ] **NARK-06**: `be.json` `entity.person_verb_patterns` covers verbs of speech, feeling, and decision with **explicit gender alternation** (masc `-ў` / fem `-ла` / pl `-лі`) — e.g. `\b{name}\s+(?:сказа(?:ў|ла|лі)|казаў|казала|казалі)\b`. Minimum 15 entries.
- [ ] **NARK-07**: `be.json` `entity.pronoun_patterns` covers all 6 cases × 3 genders for Belarusian personal pronouns: `ён/яго/яму/ім` (masc), `яна/яе/ёй/ёю` (fem), `яны/іх/ім/імі` (pl). Includes formal `Вы/Вас/Вам`.
- [ ] **NARK-08**: `be.json` `entity.direct_address_pattern` is a single string with `|`-alternation containing ≥ 5 Belarusian greeting/thanks/address forms (e.g., `прывітанне`, `вітаю`, `дзякуй`, `дарагі/дарагая`, `паважаны/паважаная`).
- [ ] **NARK-09**: `be.json` `entity.stopwords` array contains ≥ 30 native Belarusian function words across categories: prepositions, conjunctions, particles, copular forms. Words are NOT translated wholesale from `ru.json` stopwords — most entries differ (`и`→`і`, `у`→`ў`, `тоже`→`таксама`, `чтобы`→`каб`).

### Translation — Tarashkievitsa (`be-tarask.json`)

- [ ] **TARASK-01**: `be-tarask.json` `terms` section contains all 13 keys translated to Tarashkievitsa orthography. Lexical choices diverge from Narkamauka where the orthographies disagree (e.g., `hall` may be `заля` rather than Narkamauka's `зала` — defer to native reviewer).
- [ ] **TARASK-02**: `be-tarask.json` `cli` section mirrors `be.json`'s 14-key contract with Tarashkievitsa orthography (soft-sign placement, foreign-word adaptation `план→плян`, `сістэма→сыстэма`). Identical placeholders preserved.
- [ ] **TARASK-03**: `be-tarask.json` `aaak.instruction` is a fluent Tarashkievitsa sentence ≥ 10 characters with characteristic markers (soft-sign before consonants where Tarashkievitsa demands it: `сьцісьніце` / `сістэму → сыстэму`).
- [ ] **TARASK-04**: `be-tarask.json` `regex` section uses Tarashkievitsa-aware patterns. Same character class as `be.json` (alphabet doesn't change), but `action_pattern` verbs use Tarashkievitsa forms where they differ (e.g., reflexive `-сь` for some perfective verbs).
- [ ] **TARASK-05**: `be-tarask.json` `entity` section contains all 8 sub-keys with Tarashkievitsa morphology. `candidate_pattern` and `multi_word_pattern` are identical to `be.json` (alphabet is same).
- [ ] **TARASK-06**: `be-tarask.json` `entity.person_verb_patterns` uses Tarashkievitsa reflexive endings where they differ (`усьміхнуўся`/`усьміхнулася` vs Narkamauka `усміхнуўся`/`усмiхнулася`). Same gender alternation discipline as NARK-06.
- [ ] **TARASK-07**: `be-tarask.json` `label` is the Tarashkievitsa autonym (recommended: `"Беларуская (тарашкевіца)"` per Wikimedia convention; native reviewer confirms).

### Quality Assurance (Native Review — the hard gate)

- [ ] **QA-01**: Every string in `be.json` is reviewed by a native Belarusian speaker (the project owner per PROJECT.md) and approved before commit.
- [ ] **QA-02**: Every string in `be-tarask.json` is reviewed by a native Belarusian speaker and approved before commit.
- [ ] **QA-03**: Neither file contains Russian false friends in semantic positions (e.g., NOT using `вяселле` to mean "fun"; NOT using `благі` to mean "good"; NOT using `выгода` to mean "profit"). Reviewed against the false-friends table in PITFALLS.md Pitfall 1.
- [ ] **QA-04**: Neither file mixes orthographies. `be.json` contains no Tarashkievitsa-only tokens (`сьвет`, `плян`, `сыг-`, `фізы-`, `канф-` without `-ір-`); `be-tarask.json` contains no Narkamauka-preferred tokens where Tarashkievitsa demands a soft-sign or foreign-l adaptation. Verifiable by grep heuristic per PITFALLS.md Pitfall 2.
- [ ] **QA-05**: All past-tense verb patterns in both files use Belarusian endings (`-ў`/`-ла`/`-ло`/`-лі`), NOT Russian endings (`-л`/`-ла`/`-ло`/`-ли`). Verifiable by grep for `-л\b` followed by space-name pattern across files.
- [ ] **QA-06**: Apostrophe codepoint is consistent and documented in PR description. Recommendation: U+0027 (ASCII `'`) for pragmatic compatibility — matches user input behavior and existing locale-file convention.
- [ ] **QA-07**: Both files are NFC-normalized (precomposed Cyrillic). Verifiable: `unicodedata.is_normalized('NFC', open(path).read())` returns `True`.

### Tests

- [ ] **TEST-01**: `pytest tests/test_i18n.py -v` passes locally with both new files in place. Specifically: `test_all_languages_load` accepts both files; `test_interpolation` confirms `cli.mine_complete` interpolation works; `test_korean_status_drawers_uses_count` regression continues to pass.
- [ ] **TEST-02**: `pytest tests/test_i18n_lang_case.py -v` passes — both `be` and `be-tarask` resolve case-insensitively and `_load_entity_section` returns non-empty dicts for both.
- [ ] **TEST-03**: `pytest tests/test_entity_detector.py -v` passes — entity detection on Belarusian sample text via `_build_patterns("Іван", ("be",))` matches expected patterns; no regressions on existing locales.
- [ ] **TEST-04**: `pytest tests/ -v --cov=mempalace --cov-fail-under=80` passes the full suite + coverage gate locally before pushing.
- [ ] **TEST-05** *(optional but recommended)*: `tests/test_i18n.py::test_dialect_compress_samples` is extended with one Belarusian sample sentence (~6 lines added) demonstrating compression for `lang="be"`. Coverage rises slightly.
- [ ] **TEST-06**: A runtime smoke check confirms `extract_candidates(belarusian_sample_text, languages=("be",))` surfaces at least one Belarusian name (e.g., `Іван`/`Ўладзіслаў`/`Алёна`) and excludes function words from `entity.stopwords`.

### Pull Request (Upstream Submission)

- [ ] **SHIP-01**: Branch is `feat/i18n-belarusian` (matches recent locale-PR convention: `feat/i18n-russian`, `feat/italian-i18n-support`, `feat/add-i18n-hindi`, `feat/id-lang`).
- [ ] **SHIP-02**: Branch is created from upstream `develop` (NOT `main` — per CONTRIBUTING.md:58).
- [ ] **SHIP-03**: Commits follow Conventional Commits per CONTRIBUTING.md:53 — `feat(i18n): add Belarusian (Narkamauka) locale`, `feat(i18n): add entity detection section to Belarusian (Narkamauka)`, `feat(i18n): add Belarusian (Tarashkievitsa) locale`, `feat(i18n): add entity detection section to Belarusian (Tarashkievitsa)`. Optional: `test(i18n): add Belarusian sample to dialect compress test`.
- [ ] **SHIP-04**: PR description follows the established locale-PR template (cite #760 Russian, #907 Italian, #778 Indonesian as references) and includes:
  - Native autonyms (`Беларуская` / `Беларуская (тарашкевіца)`)
  - Orthography rationale (why two files, what differs between them)
  - Apostrophe codepoint decision
  - Screenshot or paste of `pytest tests/ -v` output (green)
  - Confirmation that no module-level changes were made (pure data PR)
- [ ] **SHIP-05**: PR is submitted against `develop` branch with label `area/i18n` (matches the issue tracker labeling convention).
- [ ] **SHIP-06**: All upstream CI checks pass: `ruff check .`, `ruff format --check .`, `pytest --cov=mempalace --cov-fail-under=80` across the matrix (Linux 3.9/3.11/3.13, Windows 3.9, macOS 3.9), and Version Guard.

---

## v2 Requirements

Deferred to future PRs once the v1 lands and the upstream community has feedback.

### Belarusian Search Quality

- **V2-SEARCH-01**: Address open issue #712 (non-English search degradation) by evaluating multilingual embedding models (e.g., `paraphrase-multilingual-MiniLM-L12-v2`, `intfloat/multilingual-e5-base`) for Belarusian semantic search recall. — Out of scope here; this is an embedding-model swap, not an i18n contribution.

### Latin-Script Belarusian (Łacinka)

- **V2-LATN-01**: Add `be-Latn.json` for Łacinka orthography if user demand emerges. Would require BCP 47 `be-Latn` script subtag (not `Suppress-Script: Cyrl`'s default).

### Belarusian-Russian Disambiguation

- **V2-DISAMB-01**: Add language-detection layer in `entity_detector` to distinguish Belarusian Cyrillic text from Russian Cyrillic text when both `be` and `ru` are loaded. Requires materially changing `get_entity_patterns` design contract — out of scope here.

### Documentation

- **V2-DOCS-01**: Add a "Adding a new language" section to the upstream README.md (referenced in `mempalace/i18n/__init__.py:13` but doesn't currently exist). Could be a separate small PR.

---

## Out of Scope

Explicitly excluded for the initial PR. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Latin-script Belarusian (`Łacinka`) | No upstream precedent; no clear consumer; would require `be-Latn` script subtag. Defer until demand emerges (V2-LATN-01). |
| Translating MemPalace docs/README/website to Belarusian | Locale files only. Project README/CONTRIBUTING/SECURITY/etc. are not in `mempalace/i18n/` scope. |
| Adding a "Adding a new language" section to README.md | Doc gap is real (referenced in `mempalace/i18n/__init__.py:13` but missing) — but scope is the locale files, not project docs. Capture as V2-DOCS-01. |
| Modifying `mempalace/i18n/__init__.py` | The module already supports auto-discovery, case-insensitive lookup, hyphenated tags, per-locale entity merge. Belarusian needs zero infra changes. Any change here expands review surface and risks rejection. |
| Modifying `mempalace/entity_detector.py` | Same reason. The merged `entity` patterns flow through unchanged. |
| Belarusian-Russian disambiguation in `entity_detector` | Same Cyrillic block — would require language-detection layer; materially changes the design contract. Defer (V2-DISAMB-01). |
| Improving non-English semantic search quality | Open issue [#712](https://github.com/MemPalace/mempalace/issues/712) — ChromaDB default embedding model is English-only. This is an embedding-model swap, not i18n. Defer (V2-SEARCH-01). |
| Discord / community announcement | Not a code deliverable. |
| Adding new Python dependencies | Violates CONTRIBUTING.md:66 ("ChromaDB + PyYAML only"). Trivially satisfied — pure-data PR needs no new deps. |
| Backporting Belarusian into the v8.json initial-batch refactor (`baf3c0a`) | History rewriting, not a contribution. The two new files are additions, not retrofits. |

---

## Traceability

Which phases cover which requirements. **Empty until roadmap creation.**

| Requirement | Phase | Status |
|-------------|-------|--------|
| LOC-01 | (pending roadmap) | Pending |
| LOC-02 | (pending roadmap) | Pending |
| LOC-03 | (pending roadmap) | Pending |
| LOC-04 | (pending roadmap) | Pending |
| LOC-05 | (pending roadmap) | Pending |
| LOC-06 | (pending roadmap) | Pending |
| LOC-07 | (pending roadmap) | Pending |
| NARK-01 | (pending roadmap) | Pending |
| NARK-02 | (pending roadmap) | Pending |
| NARK-03 | (pending roadmap) | Pending |
| NARK-04 | (pending roadmap) | Pending |
| NARK-05 | (pending roadmap) | Pending |
| NARK-06 | (pending roadmap) | Pending |
| NARK-07 | (pending roadmap) | Pending |
| NARK-08 | (pending roadmap) | Pending |
| NARK-09 | (pending roadmap) | Pending |
| TARASK-01 | (pending roadmap) | Pending |
| TARASK-02 | (pending roadmap) | Pending |
| TARASK-03 | (pending roadmap) | Pending |
| TARASK-04 | (pending roadmap) | Pending |
| TARASK-05 | (pending roadmap) | Pending |
| TARASK-06 | (pending roadmap) | Pending |
| TARASK-07 | (pending roadmap) | Pending |
| QA-01 | (pending roadmap) | Pending |
| QA-02 | (pending roadmap) | Pending |
| QA-03 | (pending roadmap) | Pending |
| QA-04 | (pending roadmap) | Pending |
| QA-05 | (pending roadmap) | Pending |
| QA-06 | (pending roadmap) | Pending |
| QA-07 | (pending roadmap) | Pending |
| TEST-01 | (pending roadmap) | Pending |
| TEST-02 | (pending roadmap) | Pending |
| TEST-03 | (pending roadmap) | Pending |
| TEST-04 | (pending roadmap) | Pending |
| TEST-05 | (pending roadmap) | Pending |
| TEST-06 | (pending roadmap) | Pending |
| SHIP-01 | (pending roadmap) | Pending |
| SHIP-02 | (pending roadmap) | Pending |
| SHIP-03 | (pending roadmap) | Pending |
| SHIP-04 | (pending roadmap) | Pending |
| SHIP-05 | (pending roadmap) | Pending |
| SHIP-06 | (pending roadmap) | Pending |

**Coverage:**
- v1 requirements: **42 total**
- Mapped to phases: 0
- Unmapped: 42 ⚠ (will resolve to 0 after roadmap creation)

---

*Requirements defined: 2026-04-20*
*Last updated: 2026-04-20 after initial definition*

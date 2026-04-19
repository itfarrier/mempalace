# Roadmap: MemPalace Belarusian i18n

## Overview

This is a **5-phase, sequential roadmap** for a brownfield i18n contribution to upstream `MemPalace/mempalace`. Two locale files (`be.json` Narkamauka, `be-tarask.json` Tarashkievitsa) are authored in lock-step with a hard native-speaker review gate. Each file is split into a base-file phase (terms / cli / aaak / regex) and an entity-section phase (the higher-review-surface section), mirroring the established locale-PR commit pattern (`b87ada3`/`d6bd7de` Russian; `2e998db`/`69453b2` Italian). Phases are **strictly sequential** — `config.json` enables parallelization, but `PITFALLS.md` Pitfall 2 (orthography mixing) overrides: doing both files in parallel is the single costliest mistake to recover from after PR submission.

The 5th phase locks the contribution against the test suite, runs final cross-file QA grep checks (false friends, orthography leakage, past-tense endings, NFC normalization), and ships the PR upstream against `develop` per the recent locale-PR convention.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: be.json (Narkamauka) base file** — Ship a loadable, test-passing Narkamauka locale with `terms` / `cli` / `aaak` / `regex`
- [ ] **Phase 2: be.json (Narkamauka) entity section** — Add the 8-sub-key `entity` block with Belarusian-Cyrillic candidate class and gender-aware verb patterns
- [ ] **Phase 3: be-tarask.json (Tarashkievitsa) base file** — Mirror Phase 1 with Tarashkievitsa orthography
- [ ] **Phase 4: be-tarask.json (Tarashkievitsa) entity section** — Mirror Phase 2 with Tarashkievitsa morphology
- [ ] **Phase 5: Tests + native review + upstream PR** — Final cross-file QA, test suite, and PR submission to `MemPalace/mempalace` `develop`

## Phase Details

### Phase 1: be.json (Narkamauka) base file

**Goal**: Ship a loadable, schema-conforming Narkamauka locale file with everything except the `entity` section. The first commit on the contribution branch.

**Depends on**: Nothing (first phase)

**Requirements**: LOC-01, LOC-03, LOC-06, LOC-07, NARK-01, NARK-02, NARK-03, NARK-04, QA-06

**Success Criteria** (what must be TRUE):
  1. `mempalace/i18n/be.json` exists, is UTF-8 without BOM (verified by `head -c 3 mempalace/i18n/be.json | xxd` showing `0x7B` as first byte), serialized with `ensure_ascii=False` and `indent=2`.
  2. `from mempalace.i18n import load_lang, available_languages; load_lang("be")` returns a non-empty dict; `"be"` appears in `available_languages()`.
  3. `pytest tests/test_i18n.py -v` passes — `test_all_languages_load` accepts the new file (4 hard `terms` keys + `cli` + `aaak.instruction` ≥ 10 chars present), `test_interpolation` succeeds for `cli.mine_complete`, `test_korean_status_drawers_uses_count` regression continues to pass.
  4. Apostrophe codepoint decision is locked (recommendation: U+0027 for pragmatic compatibility) and noted in the commit message.

**Plans**: TBD (likely 1 plan — single-commit file authoring)

Plans:
- [ ] 01-01: Author `mempalace/i18n/be.json` (lang/label/terms/cli/aaak/regex) and pass test_i18n.py

---

### Phase 2: be.json (Narkamauka) entity section

**Goal**: Add the `entity` section to `be.json` — Belarusian-aware candidate/multi-word patterns (correct character class), gender-alternating person verbs, all-cases pronoun coverage, native stopwords. The second commit on the contribution branch. This is the highest-review-surface section and the one that materially affects user behavior on real Belarusian text.

**Depends on**: Phase 1

**Requirements**: LOC-04, NARK-05, NARK-06, NARK-07, NARK-08, NARK-09, QA-01

**Success Criteria** (what must be TRUE):
  1. `be.json` `entity` section contains all 8 sub-keys (no `boundary_chars` — Cyrillic doesn't need it). The `candidate_pattern` is `[А-ЯЁІЎ][а-яёіў]{1,19}` and `multi_word_pattern` mirrors it.
  2. Runtime smoke check passes: `from mempalace.i18n import get_entity_patterns; from mempalace.entity_detector import _build_patterns; _build_patterns("Іван", ("be",))` returns compiled patterns and `extract_candidates("Іван сказаў, што Алёна знайшла нешта.", languages=("be",))` surfaces `Іван` AND `Алёна` (the empirical regression caught by STACK research — Russian's `[А-ЯЁ]` class drops `Іван`).
  3. `pytest tests/test_i18n.py tests/test_i18n_lang_case.py tests/test_entity_detector.py -v` passes; no regression on existing locales.
  4. Native-speaker review (QA-01) of every string in `be.json` is complete and approved before this phase's commit — no Russian transliteration, no false friends, gender-correct past-tense alternation throughout.

**Plans**: TBD (likely 1 plan)

Plans:
- [ ] 02-01: Add `entity` section to `be.json` and pass entity_detector tests + native review

---

### Phase 3: be-tarask.json (Tarashkievitsa) base file

**Goal**: Author the second locale file with Tarashkievitsa orthography. Mirror Phase 1's shape but apply soft-sign placement, foreign-word adaptation (`план→плян`, `сістэма→сыстэма`), and Tarashkievitsa lexical preferences where they diverge from Narkamauka. **Sequential after Phase 2 lock** — context-switching between orthographies in a single sitting is PITFALLS Pitfall 2.

**Depends on**: Phase 2

**Requirements**: LOC-02, TARASK-01, TARASK-02, TARASK-03, TARASK-04, TARASK-07

**Success Criteria** (what must be TRUE):
  1. `mempalace/i18n/be-tarask.json` exists, loads via `load_lang("be-tarask")`, and resolves case-insensitively (`load_lang("BE-TARASK")` returns the same dict per `tests/test_i18n_lang_case.py`).
  2. `pytest tests/test_i18n.py tests/test_i18n_lang_case.py -v` passes with the new file.
  3. `be-tarask.json` `label` is the Tarashkievitsa autonym (recommendation: `"Беларуская (тарашкевіца)"` per Wikimedia convention; native reviewer confirms).
  4. Quick grep heuristic confirms no Narkamauka-only tokens in `be-tarask.json` where Tarashkievitsa demands soft-sign or foreign-l adaptation (e.g., no `план`/`клуб`/`сістэма`/`фізіка` standalone — should be `плян`/`клюб`/`сыстэма`/`фізыка`).

**Plans**: TBD (likely 1 plan)

Plans:
- [ ] 03-01: Author `mempalace/i18n/be-tarask.json` (lang/label/terms/cli/aaak/regex) and pass test_i18n.py

---

### Phase 4: be-tarask.json (Tarashkievitsa) entity section

**Goal**: Add the `entity` section to `be-tarask.json` with Tarashkievitsa morphology (soft-sign reflexives `-сь`/`-ся`, `-ьц-` clusters where appropriate). Same character class as Phase 2 (Belarusian alphabet doesn't change between orthographies). Final author-side phase before testing & PR.

**Depends on**: Phase 3

**Requirements**: TARASK-05, TARASK-06, QA-02

**Success Criteria** (what must be TRUE):
  1. `be-tarask.json` `entity` section contains all 8 sub-keys with identical character classes to `be.json` (`[А-ЯЁІЎ][а-яёіў]{1,19}`) but Tarashkievitsa-specific verb forms in `person_verb_patterns` (e.g., `усьміхнуўся` rather than Narkamauka `усміхнуўся`) and reflexive endings.
  2. `pytest tests/test_i18n.py tests/test_i18n_lang_case.py tests/test_entity_detector.py -v` passes; no regression on existing locales or on `be.json`.
  3. Runtime smoke check: `extract_candidates(tarashkievitsa_sample_text, languages=("be-tarask",))` surfaces native names with Tarashkievitsa orthographic markers preserved.
  4. Native-speaker review (QA-02) of every string in `be-tarask.json` is complete and approved before this phase's commit.

**Plans**: TBD (likely 1 plan)

Plans:
- [ ] 04-01: Add `entity` section to `be-tarask.json` and pass entity_detector tests + native review

---

### Phase 5: Tests + native review + upstream PR

**Goal**: Lock the contribution against the full test suite, run cross-file QA grep checks (false friends, orthography leakage, past-tense endings, NFC normalization, "no `__init__.py` changes" verification), optionally extend `test_dialect_compress_samples` with a Belarusian sample, and ship the PR upstream against `develop` following the established locale-PR template.

**Depends on**: Phase 4

**Requirements**: LOC-05, QA-03, QA-04, QA-05, QA-07, TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, SHIP-01, SHIP-02, SHIP-03, SHIP-04, SHIP-05, SHIP-06

**Success Criteria** (what must be TRUE):
  1. `pytest tests/ -v --cov=mempalace --cov-fail-under=80` passes the full suite locally before pushing — coverage stays at or above 80%.
  2. `ruff check .` and `ruff format --check .` are clean (relevant only if `tests/test_i18n.py` is modified for TEST-05).
  3. Cross-file QA grep checks all pass: no Russian function-word leakage (no `и`, no `ъ`, no `у` in past-tense verb endings); no orthography mixing (no `сь`/`зь`/`дзь`/`плян`/`клюб`/`сыг`/`фізы` in `be.json`; no `сн` where `сьн` expected, no `план`/`клуб`/`сістэма` in `be-tarask.json`); no Russian `-л` past-tense endings in either file's verb patterns; both files are NFC-normalized (`unicodedata.is_normalized('NFC', open(path).read())` returns `True` for both); no changes to `mempalace/i18n/__init__.py` or any other production module (`git diff --stat develop -- mempalace/` shows ONLY the two new JSON files and at most one test file).
  4. PR is open at `https://github.com/MemPalace/mempalace/pulls` against `develop` from `feat/i18n-belarusian` branch with: native autonyms in description (`Беларуская` / `Беларуская (тарашкевіца)`), orthography rationale (why two files), apostrophe codepoint decision noted, paste of `pytest tests/ -v` green output, confirmation that the PR is pure-data with no module changes, label `area/i18n` applied. Conventional commits (4-5 commits per phases 1-5).
  5. All upstream CI checks pass (Linux 3.9/3.11/3.13, Windows 3.9, macOS 3.9, Version Guard).

**Plans**: TBD (likely 2 plans — one for tests/QA grep, one for PR submission)

Plans:
- [ ] 05-01: Run cross-file QA grep checks, full pytest suite, optionally add Belarusian sample to test_dialect_compress_samples
- [ ] 05-02: Push branch, open PR against MemPalace/mempalace develop, verify CI green

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 (strictly sequential, no parallelization — see PITFALLS.md Pitfall 2)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. be.json (Narkamauka) base file | 0/1 | Not started | - |
| 2. be.json (Narkamauka) entity section | 0/1 | Not started | - |
| 3. be-tarask.json (Tarashkievitsa) base file | 0/1 | Not started | - |
| 4. be-tarask.json (Tarashkievitsa) entity section | 0/1 | Not started | - |
| 5. Tests + native review + upstream PR | 0/2 | Not started | - |

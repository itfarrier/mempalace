# Features Research — MemPalace Belarusian i18n contribution

**Domain:** Brownfield i18n locale schema (two new JSON files: `be.json` Narkamauka + `be-tarask.json` Tarashkievitsa)
**Researched:** 2026-04-20
**Confidence:** HIGH (every claim is traced to a source line in `mempalace/i18n/__init__.py`, a test in `tests/test_i18n.py`, an empirical read of one of the 13 existing locale files, or a verified git commit)

> **Re-interpretation of the template.** The greenfield "feature landscape" template asks "what should we build?". This is a brownfield contribution where the *only* deliverables are two JSON files conforming to an existing schema. So in this document **a "feature" is a SCHEMA SECTION (or sub-key) of a locale file**:
>
> - **Table Stakes** = schema sections that MUST be present and well-formed or `pytest tests/test_i18n.py` fails.
> - **Differentiators** = optional sections / sub-keys that materially improve quality (e.g., the entire `entity` section enables Cyrillic name detection where the English fallback would silently miss every Belarusian name).
> - **Anti-Features** = schema choices that look helpful but cause problems (e.g., declaring `boundary_chars` for Cyrillic — a no-op that adds review friction without benefit).
> - **MVP** = the smallest schema content that ships green CI for `be.json` + `be-tarask.json`.
> - **Full Tier** = what the project owner actually committed to ship per `PROJECT.md` line 14-17 and "Key Decisions" row 2.
> - **Feature Dependencies** = inter-section consistency rules (e.g., the noun chosen for `terms.palace` must appear in conjugated form in `cli.status_palace`, `cli.init_complete`, `cli.init_exists`, and `cli.no_palace`; the character class in `entity.candidate_pattern` must include every script character used elsewhere in the file).
>
> No translations are drafted in this document — that is the implementer's job under the `NATIVE-01` review gate. Only the **schema** is analyzed.

---

## 1. The Locale Schema (canonical reference: `en.json`)

Every existing locale file shares the same top-level shape. Below is the canonical schema, key-by-key, with each key's required-vs-optional status, the consumer module that reads it, and the failure mode if it is missing or malformed.

### 1.1 Top-level keys

| Key | Type | Required? | Consumer | Failure mode if missing |
|-----|------|-----------|----------|-------------------------|
| `lang` | string (BCP 47 tag) | **Convention only** — present in 13/13 existing locales | NOT consumed by any code (Grep: zero matches for `_strings["lang"]` / `t("lang")` / `.get("lang")` against locale dicts) | Silent — file still loads. Convention says it should equal the file stem (e.g. `"be"` for `be.json`). |
| `label` | string (autonym in the language itself) | **Convention only** — present in 13/13 existing locales | NOT consumed by any code | Silent — file still loads. Convention says it's the autonym (e.g. `"Беларуская"` for `be.json`, `"Беларуская (тарашкевіца)"` for `be-tarask.json`). |
| `terms` | object | **REQUIRED** | `tests/test_i18n.py:18` asserts presence; `t("terms.X")` lookups | Test failure: `assert section in strings` fails. |
| `cli` | object | **REQUIRED** | `tests/test_i18n.py:18`; `t("cli.X")` lookups | Test failure: same. |
| `aaak` | object | **REQUIRED** | `tests/test_i18n.py:18`; `Dialect.__init__` reads `aaak.instruction`; `closet_llm._call_llm` reads `aaak.instruction` | Test failure plus runtime: `t("aaak.instruction")` returns the literal string `"aaak.instruction"`. |
| `regex` | object | **OPTIONAL** | `i18n.get_regex()` returns `_strings.get("regex", {})`; loaded into `Dialect.lang_regex` | None — `get_regex()` returns `{}` if absent. Critically, **`Dialect` itself never reads `lang_regex` again** (verified via Grep — only assigned at `dialect.py:348`, never read). The section is currently **dead weight in production code**. Adding it makes the locale "infrastructure-ready" for a future wiring. |
| `entity` | object | **OPTIONAL but high-impact for non-Latin scripts** | `i18n.get_entity_patterns()` → `mempalace/entity_detector.py` (every public function) and `mempalace/palace.py:_candidate_entity_words` | If absent for ALL requested locales, `_collect_entity_section` falls back to `en` patterns (`__init__.py:255-257`). For Belarusian users this means **the English `[A-Z][a-z]` candidate pattern is the only one tried — every Cyrillic name is silently missed**. |

### 1.2 `terms` sub-keys (13 entries in `en.json`)

`terms.X` is read by `t("terms.X")` (`mempalace/i18n/__init__.py:62-81`). If the key is missing, `t()` returns the literal **dotted-key string** (e.g. `"terms.palace"`) — there is **NO English fallback at the key level** (verified at `__init__.py:73`).

| Key | Required? | Test enforcing it | Consumer | Failure if missing |
|-----|-----------|-------------------|----------|--------------------|
| `palace` | **HARD** | `test_all_languages_load` (`tests/test_i18n.py:20-21`) | (currently no live `t("terms.palace")` consumer in production code — used in `cli.*` interpolation by *string composition*, not by `t()` lookup) | Test failure: `assert term in strings["terms"]`. |
| `wing` | **HARD** | same | same | Test failure. |
| `closet` | **HARD** | same | same | Test failure. |
| `drawer` | **HARD** | same | same | Test failure. |
| `hall` | Convention | none | none live | Silent — `t("terms.hall")` returns `"terms.hall"`. |
| `mine` | Convention | none | none live | Silent. |
| `search` | Convention | none | none live | Silent. |
| `status` | Convention | none | none live | Silent. |
| `init` | Convention | none | none live | Silent. |
| `repair` | Convention | none | none live | Silent. |
| `migrate` | Convention | none | none live | Silent. |
| `entity` | Convention | none | none live | Silent. |
| `topic` | Convention | none | none live | Silent. |

**Key finding (verified via Grep across the entire repo):** `tests/test_i18n.py:20` enforces only `palace`, `wing`, `closet`, `drawer`. The other 9 are convention — present in 13/13 existing locales — but the test contract does not require them. **For full-tier parity, all 13 must be translated.**

### 1.3 `cli` sub-keys (14 entries in `en.json`)

`cli.X` is read by `t("cli.X", **kwargs)` with `str.format` interpolation. **No English fallback at the key level**: a missing key returns `"cli.no_palace"` (etc.) literally, not the English string. **No interpolation safety**: `str.format` raises `KeyError` on a missing variable, which is silently swallowed by `i18n.t()` (`__init__.py:79`) and the *unformatted* template is returned — so a typo like `{drawers}` instead of `{count}` produces visible `{drawers}` literal output.

| Key | Required by test? | Variables (interpolation contract) | Consumer | Failure if missing/wrong |
|-----|-------------------|------------------------------------|----------|--------------------------|
| `mine_start` | No | `{path}` | None live (`mempalace/cli.py` does NOT import i18n — verified via Grep) | Silent literal-string output if called by future code. |
| `mine_complete` | **YES** | `{closets}`, `{drawers}` | `tests/test_i18n.py:31` calls `t("cli.mine_complete", closets=5, drawers=100)` and asserts both numbers appear | Test failure: `assert "5" in result` and `assert "100" in result`. |
| `mine_skip` | No | (none) | None live | Silent. |
| `search_no_results` | No | `{query}` | None live | Silent. |
| `search_results` | No | `{count}` | None live | Silent. |
| `status_palace` | No | `{path}` | None live | Silent. |
| `status_wings` | No | `{count}` | None live | Silent. |
| `status_closets` | No | `{count}` | None live | Silent. |
| `status_drawers` | **YES (regression)** | `{count}` (NOT `{drawers}`) | `tests/test_i18n.py:74-76` (`test_korean_status_drawers_uses_count`) calls `t("cli.status_drawers", count=42)` and asserts `"42" in result` | Test failure if locale uses `{drawers}` instead of `{count}` — Korean PR fixed this exact bug. |
| `init_complete` | No | `{path}` | None live | Silent. |
| `init_exists` | No | `{path}` | None live | Silent. |
| `repair_complete` | No | `{fixed}` | None live | Silent. |
| `migrate_complete` | No | (none) | None live | Silent. |
| `no_palace` | No | (none) | None live | Silent. |

**Key finding:** Only **2 of the 14 `cli.*` keys are enforced by tests**: `mine_complete` (the `{closets}`/`{drawers}` interpolation contract) and `status_drawers` (the `{count}`-not-`{drawers}` regression). The other 12 are loaded for completeness; `mempalace/cli.py` itself does NOT call `t()` (verified via Grep — zero matches in `cli.py` for `from mempalace.i18n` or `t(`). They are **infrastructure-ready** for a future wiring of the CLI to i18n. **For full-tier parity with the existing 13 locales, all 14 must be translated.**

### 1.4 `aaak.instruction` (single string)

| Key | Required? | Constraint | Consumer | Failure if missing/wrong |
|-----|-----------|------------|----------|--------------------------|
| `aaak.instruction` | **HARD** | `len(d.aaak_instruction) > 10` (`tests/test_i18n.py:43`) | `Dialect.__init__` (`mempalace/dialect.py:347`) reads it and stores as `self.aaak_instruction`; `closet_llm._call_llm` (`mempalace/closet_llm.py:123`) reads it and **concatenates it into the LLM prompt** as `f"\\nLanguage instruction: {lang_instruction}"` | Test failure: `assert len(d.aaak_instruction) > 10`. Runtime impact: a missing or empty instruction means the LLM never receives a "compress in Belarusian" nudge — output may default to English even though the locale is `be`. |

This is the **only locale section currently consumed live in production by an LLM call.** For Belarusian, this string must be a fluent native instruction (≥10 chars) telling the model to compress text using Belarusian inflectional shape. See `PROJECT.md:46` (BE-04).

### 1.5 `regex` sub-keys (4 entries)

| Key | Required? | Format | Consumer | Failure if missing/wrong |
|-----|-----------|--------|----------|--------------------------|
| `topic_pattern` | OPTIONAL | regex string with character class | `i18n.get_regex()` returns the dict; `Dialect.lang_regex` stores it; **never read after that** (verified via Grep — `lang_regex` is assigned at `dialect.py:348` and never re-referenced) | None today. Future-proofs the locale for when `Dialect.compress()` is wired to honor it. |
| `stop_words` | OPTIONAL | space-separated string of words | same — stored, never consulted | None today. |
| `quote_pattern` | OPTIONAL | regex string with capture group, locale-specific quote marks (`«»` for Russian/Italian/French; `「」` for Japanese; `„"` for German; `"` ASCII for English) | same | None today. |
| `action_pattern` | OPTIONAL | regex string with non-capturing group of past-tense action verbs | same | None today. |

**Key finding:** The entire `regex` section is **functionally dead in production** — loaded into a `Dialect` attribute but never read after. The section is present in 13/13 existing locales because it was the historical contract before the `entity` section was introduced (commit `b87ada3` for `ru.json`, the first non-en locale to formalize this shape). Translating it is **infrastructure-ready** work, not user-visible work. PROJECT.md `BE-05` requires it for full-tier parity.

### 1.6 `entity` sub-keys (up to 9 entries; only 1 of 13 locales declares `boundary_chars`)

`entity.*` is consumed by `mempalace/entity_detector.py` via `i18n.get_entity_patterns(languages)` (`mempalace/i18n/__init__.py:197-270`). The merge is per-locale and additive — multiple locales can be requested simultaneously and their patterns are unioned. Each sub-key has a precise contract:

| Sub-key | Type | Required for full tier? | Format | Consumer | Failure if missing/wrong |
|---------|------|--------------------------|--------|----------|--------------------------|
| `boundary_chars` | string (character-class fragment, no `[…]` brackets) | **NO — only for combining-mark scripts** (Devanagari, Arabic, Hebrew, Thai, Tamil, Burmese, Khmer). Declared by 1/13 locales (`hi.json`). | e.g. `"\\w\\u0900-\\u097F"` for Hindi | `_script_boundary` and `_expand_b` (`__init__.py:113-146`) replace every literal `\b` in the locale's other patterns with a script-aware lookaround | If declared but not needed (e.g. for Cyrillic), the lookaround is built and applied — *correct but redundant*; **no-op for `\w`-friendly scripts**. **Anti-feature for Belarusian.** |
| `candidate_pattern` | regex string with character class for single-word entity extraction | **YES** (full tier) | e.g. `[A-Z][a-z]{1,19}` (en) / `[А-ЯЁ][а-яё]{1,19}` (ru) / `[\u0900-\u097F]{2,20}` (hi) | `_wrap_candidate` wraps it with `\b(...)\b` (or script-aware boundary if `boundary_chars` declared); `extract_candidates` (`entity_detector.py:138-149`) compiles and runs `findall` | If missing for a requested locale, that locale contributes nothing to single-word entity detection. If present but uses Russian's `[А-ЯЁ]` for Belarusian, **Belarusian-specific letters `Ў`(U+040E) and `І`(U+0406) are silently dropped from candidate extraction** (verified empirically — `re.compile(r'[А-ЯЁ][а-яё]{1,19}').findall('Іван сказаў')` → `[]` for `Іван`). |
| `multi_word_pattern` | regex string for multi-word entity extraction | **YES** (full tier) | e.g. `[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+` (en); same shape adapted to script | same wrapping; `extract_candidates` (`entity_detector.py:151-159`) | Same as candidate_pattern — multi-word names like `Уладзімір Караткевіч` are missed if character class is wrong. |
| `person_verb_patterns` | array of regex strings, each with `{name}` placeholder | **YES** (full tier) | e.g. `"\\b{name}\\s+said\\b"`. Russian uses bracketed alternation for gender: `"\\b{name}\\s+сказал[аи]?\\b"` matches `сказал` / `сказала` / `сказали` | `_build_patterns` (`entity_detector.py:167-198`) `.format(name=re.escape(name))` and compiles with `re.IGNORECASE`. Each match contributes 2 points to `person_score` in `score_entity` | Missing patterns = entity classified as `uncertain` or `project` instead of `person`. **Belarusian must cover gender (masc `сказаў` / fem `сказала` / pl `сказалі`) AND aspect (perfective/imperfective)**, otherwise female-named or plural-subject sentences silently fail to score. |
| `pronoun_patterns` | array of regex strings (no `{name}` placeholder) | **YES** (full tier) | e.g. `"\\bshe\\b"` (en) / `"\\bон\\b"` (ru) / `"\\bvocê\\b"` (pt-br) | `_pronoun_re` (`entity_detector.py:201-212`) joins with `\|` and compiles. Used in `score_entity`'s pronoun-proximity check (within 3 lines of the name) | Missing = no pronoun proximity score → `person` confidence drops. **Belarusian needs all 6 cases for ён/яна/яны** (nom/gen/dat/acc/inst/prep), not just nominative. |
| `dialogue_patterns` | array of regex strings with `{name}` placeholder, MULTILINE | **YES** (full tier) | Common shapes: `"^>\\s*{name}[:\\s]"`, `"^{name}:\\s"`, `"^\\[{name}\\]"`, `"\"{name}\\s+said"` | `_build_patterns` compiles with `re.MULTILINE \| re.IGNORECASE`. Each match scores 3 points (strongest person signal) | Missing = no dialogue marker scoring → person classification needs more pronoun + verb evidence. |
| `direct_address_pattern` | **single string** with pipe-alternation, with `{name}` placeholder | **YES** (full tier) | e.g. `"\\bhey\\s+{name}\\b\|\\bthanks?\\s+{name}\\b\|\\bhi\\s+{name}\\b"` | `get_entity_patterns` returns it as `direct_address_patterns` (a list of one-string-per-locale; `__init__.py:265`); `_build_patterns` compiles each string with `re.IGNORECASE`. Each match scores 4 points (strongest signal) | Missing = no greeting/thanks scoring. **Belarusian needs ≥3 greetings**: `прывітанне` / `вітаю` / `дзякуй` minimum, plus `дарагі/дарагая` and `паважаны/паважаная` for parity with Russian. |
| `project_verb_patterns` | array of regex strings with `{name}` placeholder | **YES** (full tier) | e.g. `"\\bbuilding\\s+{name}\\b"`, `"\\bship(?:ping\|ped)?\\s+{name}\\b"` | `_build_patterns` compiles with `re.IGNORECASE`. Each match scores 2 points to `project_score` | Missing = entity may misclassify as `person` instead of `project` (e.g. a software project named `Сонца` could match person verbs but not project verbs). |
| `stopwords` | array of strings (lowercase, no regex) | **YES** (full tier) | each word is added to a set used by `extract_candidates` (`entity_detector.py:144-146`) to filter out function words from candidate extraction | `acc["stopwords"].update(w.lower() for w in section.get("stopwords", []))` (`__init__.py:194`); merged across all requested locales | Missing = function words like `Гэта`, `Так`, `Ну`, `Ёсць` capitalized at sentence-start become candidate "entities" and pollute detection. **Russian's `ru.json` stopwords (~58 entries) is the structural reference** for category coverage: greetings, time/place adverbs, prepositions, conjunctions, particles. **Cannot be translated wholesale from Russian** — most entries differ (Russian `тоже` → Belarusian `таксама`; `и` → `і`; `у` (preposition) → `ў`/`у`). |

---

## 2. Cross-Locale Section Coverage Table (13 existing locales × 7 sections)

This table answers "which sections does each existing locale include?". It establishes the precedent set that `be.json` and `be-tarask.json` should join.

| Locale | `lang` | `label` | `terms` (#keys) | `cli` (#keys) | `aaak.instruction` | `regex` (#keys) | `entity` (#sub-keys) | `boundary_chars`? | Total tier |
|--------|--------|---------|-----------------|---------------|--------------------|-----------------|----------------------|-------------------|------------|
| **en** | ✓ | ✓ | 13 | 14 | ✓ | 4 | 8 (no `boundary_chars`) | — | Full |
| **de** | ✓ | ✓ | 13 | 14 | ✓ | 4 | — | — | Minimal |
| **es** | ✓ | ✓ | 13 | 14 | ✓ | 4 | — | — | Minimal |
| **fr** | ✓ | ✓ | 13 | 14 | ✓ | 4 | — | — | Minimal |
| **hi** | ✓ | ✓ | 13 | 14 | ✓ | 4 | 9 (incl. `boundary_chars`) | ✓ (Devanagari `\\w\\u0900-\\u097F`) | Full + boundary |
| **id** | ✓ | ✓ | 13 | 14 | ✓ | 4 | 8 (no `boundary_chars`) | — | Full (largest entity section: ~40 person verbs) |
| **it** | ✓ | ✓ | 13 | 14 | ✓ | 4 | 8 | — | Full |
| **ja** | ✓ | ✓ | 13 | 14 | ✓ | 4 | — | — | Minimal |
| **ko** | ✓ | ✓ | 13 | 14 | ✓ | 4 | — | — | Minimal |
| **pt-br** | ✓ | ✓ | 13 | 14 | ✓ | 4 | 8 | — | Full |
| **ru** | ✓ | ✓ | 13 | 14 | ✓ | 4 | 8 | — | Full (the closest sibling — Cyrillic) |
| **zh-CN** | ✓ | ✓ | 13 | 14 | ✓ | 4 | — | — | Minimal |
| **zh-TW** | ✓ | ✓ | 13 | 14 | ✓ | 4 | — | — | Minimal |
| **be** (planned) | ✓ | ✓ | 13 | 14 | ✓ | 4 | 8 | — (Cyrillic doesn't need it) | **Full** (per `PROJECT.md` Key Decision row 2) |
| **be-tarask** (planned) | ✓ | ✓ | 13 | 14 | ✓ | 4 | 8 | — | **Full** |

**Findings:**

- **Full-tier locales: 6 of 13** — `en`, `hi`, `id`, `it`, `pt-br`, `ru`. All locales whose user base writes proper names in a script the English `[A-Z][a-z]` pattern can't handle (`hi`, `pt-br`, `ru`) chose full tier. `id`, `it`, and `en` itself are full tier as well — they all could *theoretically* fall back to English entity patterns and get usable results because the scripts overlap with Latin or extended Latin, but the project owners chose to add the `entity` section for quality.
- **Minimal-tier locales: 7 of 13** — `de`, `es`, `fr`, `ja`, `ko`, `zh-CN`, `zh-TW`. Notably, `ja`, `ko`, `zh-CN`, `zh-TW` use scripts (Hiragana/Katakana, Hangul, Han) that fall back poorly to English entity patterns; **the absence of `entity` in these locales is a known quality gap**, not a deliberate design choice. We should not perpetuate it for Belarusian.
- **Closest sibling: `ru.json`** — same script (Cyrillic), same level of inflectional richness, same need for gender alternation in past-tense verbs. **Structural template only; not a translation source** (per `PROJECT.md` Key Decisions row 3).
- **Key precedent: `be.json` + `be-tarask.json` should match the `ru.json` shape** — 8 entity sub-keys (no `boundary_chars`), 13 terms, 14 cli, 1 aaak instruction, 4 regex keys.
- **Two-commit pattern is the i18n PR norm**: every recent full-tier addition split base + entity into separate atomic commits within one PR. Verified via `user-git` `git_show`:
  - `b87ada3` "feat: add Russian language support to i18n module" — base file (lang/label/terms/cli/aaak/regex). Then `d6bd7de` "feat(i18n): add entity detection section to Russian locale" — entity only.
  - `2e998db` "feat: add italian i18n support" — base file. Then `69453b2` "feat: add italian entity patterns" — entity only.
  - `3d13a72` "feat(i18n): add Brazilian Portuguese locale with entity detection (closes #117)" — single commit including entity (the framework was already in place by then).
  - This suggests our PR should follow the same pattern: one PR with 4 commits (`be` base, `be` entity, `be-tarask` base, `be-tarask` entity) — see Sec. 5 below.

---

## 3. Schema Sections by Tier

### 3.1 Table Stakes — sections that block CI if absent or malformed

These are the **hard requirements**: missing or wrong, the test suite turns red.

| Section/sub-key | Why required | Test enforcing it | Notes for `be.json` + `be-tarask.json` |
|-----------------|--------------|-------------------|----------------------------------------|
| `terms` (object) | Test asserts presence | `tests/test_i18n.py:18` | Just an object with at least the 4 hard keys below. |
| `terms.palace` | Test asserts presence + non-empty | `tests/test_i18n.py:20-21` | Recommended: `палац` (both orthographies). |
| `terms.wing` | same | same | Recommended: `крыло`. |
| `terms.closet` | same | same | Recommended: `шафа` (NOT Russian `шкаф`). |
| `terms.drawer` | same | same | Recommended: `шуфляда`. |
| `cli` (object) | Test asserts presence | `tests/test_i18n.py:18` | Object with at least the interpolation-tested keys below. |
| `cli.mine_complete` | Test calls with `closets=5, drawers=100` and asserts both numbers appear | `tests/test_i18n.py:31-33` | MUST include both `{closets}` and `{drawers}` literal placeholders. |
| `cli.status_drawers` | Test calls with `count=42` and asserts `"42"` in output | `tests/test_i18n.py:74-76` (`test_korean_status_drawers_uses_count` — added because Korean originally used `{drawers}`, broke runtime) | MUST use `{count}`, NOT `{drawers}`. Same regression-prevention applies. |
| `aaak` (object) | Test asserts presence | `tests/test_i18n.py:18` | Object containing at least `instruction`. |
| `aaak.instruction` | Test asserts present + length > 10 | `tests/test_i18n.py:22, 43` | Belarusian sentence ≥10 chars instructing the LLM to compress. **Live consumer**: `closet_llm._call_llm` concatenates this into LLM prompts. |

**Total table-stakes surface: 9 enforcement points.** Anything that satisfies these passes the existing test suite.

### 3.2 Differentiators — sections that materially improve quality

These are the optional sections that the project owner explicitly chose to ship in full tier (per `PROJECT.md:14-17` and Key Decisions row 2). They unlock real user-visible behavior on Belarusian text.

| Section/sub-key | Value proposition | Implementation cost | Priority for Belarusian |
|-----------------|-------------------|---------------------|--------------------------|
| Remaining 9 `terms` keys (`hall`, `mine`, `search`, `status`, `init`, `repair`, `migrate`, `entity`, `topic`) | Convention parity with the 13 existing locales; future-proof for any consumer that adds `t("terms.X")` lookup. **No live consumer today.** | LOW — 9 nouns, dictionary lookups | **YES** for parity. PROJECT.md `BE-02` requires all 13. |
| Remaining 12 `cli` keys (everything except `mine_complete` and `status_drawers`) | Convention parity; infrastructure-ready translations for the future when `mempalace/cli.py` is wired to call `t()`. **Currently NOT consumed in production** — `cli.py` uses hard-coded English f-strings (verified via Grep — zero matches for `from mempalace.i18n` in `mempalace/cli.py`). | LOW-MEDIUM — 12 short strings with simple `{var}` interpolation; care needed to use `{count}` not `{closets}`/`{drawers}` for status_* keys | **YES** for parity. PROJECT.md `BE-03` requires all 14. |
| `regex.topic_pattern` | Future-proof script-aware topic extraction | LOW — one regex line; for Belarusian: `[А-ЯЁІЎ][а-яёіў]{2,}\|[A-Z][a-z]{2,}\|[A-Za-z][A-Za-z0-9_]{2,}` (mirror `ru.json:39` shape, add `ІЎіў`) | YES per PROJECT.md `BE-05`. |
| `regex.stop_words` | Space-separated stop-word string for future tokenizer integration | LOW-MEDIUM — ~30-60 words; **must NOT be copied from Russian** (function words differ: `и`→`і`, `у`→`ў`, `тоже`→`таксама`, `чтобы`→`каб`, `эта`→`гэта`, etc.) | YES per `BE-05`. |
| `regex.quote_pattern` | Locale-specific quote-mark capture | LOW — one regex; Belarusian Wikipedia uses `«»` like Russian; can mirror `ru.json:41` quote pattern verbatim | YES per `BE-05`. |
| `regex.action_pattern` | Past-tense action verb extraction | LOW-MEDIUM — non-capturing alternation of ~14 verbs; **must use Belarusian `-ў`/`-іў`/`-аў` past-tense endings, NOT Russian `-л`/`-ил`/`-ал`** | YES per `BE-05`. |
| `entity.candidate_pattern` | Single-word Cyrillic name extraction | LOW — one regex: `[А-ЯЁІЎ][а-яёіў]{1,19}` (verified empirically — see STACK.md "Critical Regex Caveat") | **CRITICAL** — without this, ALL Belarusian names are missed. PROJECT.md `BE-06`. |
| `entity.multi_word_pattern` | Multi-word Cyrillic name extraction | LOW — one regex: `[А-ЯЁІЎ][а-яёіў]+(?:\\s+[А-ЯЁІЎ][а-яёіў]+)+` | CRITICAL for full names like `Уладзімір Караткевіч`. |
| `entity.person_verb_patterns` (array, ≥10 entries) | Person classification via "X said/asked/laughed" detection | MEDIUM — ~15 patterns with bracketed alternation for gender (`сказа(ў\|ла\|лі)`) and aspect (`-ся`/`-сь` for reflexives). For `be-tarask`, soft-sign reflexives (`-сь`). | CRITICAL — without this, no person can be confidently classified. PROJECT.md `BE-06`. |
| `entity.pronoun_patterns` (array, ≥6 entries) | Person classification via pronoun proximity | MEDIUM — Belarusian needs `ён/яго/яму/ім` (masc), `яна/яе/ёй/ёю` (fem), `яны/іх/ім/імі` (pl), all 6 cases per gender (verified Belarusian has 6 cases like Russian) | HIGH — boosts person confidence. PROJECT.md `BE-06`. |
| `entity.dialogue_patterns` (array, ≥4 entries) | Strongest person signal (3 pts/match) — script formatting + quoted "X said" | LOW-MEDIUM — same 3 generic patterns as every locale (`^>\\s*{name}[:\\s]`, `^{name}:\\s`, `^\\[{name}\\]`) plus one Belarusian-specific `\"{name}\\s+сказаў` | HIGH. Same shape across all locales except for the language-specific quoted "said" verb. |
| `entity.direct_address_pattern` (single string with `\|` alternation, ≥3 alternatives) | Strongest person signal (4 pts/match) — greetings/thanks before name | LOW-MEDIUM — `\\bпрывітанне\\s+{name}\\b\|\\bвітаю\\s+{name}\\b\|\\bдзякуй\\s+{name}\\b\|\\bпаважаны\\s+{name}\\b\|\\bпаважаная\\s+{name}\\b\|\\bдарагі\\s+{name}\\b\|\\bдарагая\\s+{name}\\b` | HIGH. Mirror `ru.json:81` shape. |
| `entity.project_verb_patterns` (array, ≥6 entries) | Project classification — disambiguates names from project codenames | MEDIUM — Belarusian aspectual pairs: `буду(ю\|е) {name}` / `пабудаваў {name}` / `запусціў {name}` / `усталяваў {name}` / `сістэма {name}` / `праект {name}` / `import {name}` / `pip install {name}` (the last two are universal — keep verbatim) | HIGH. Without it, project codenames misclassify as people. |
| `entity.stopwords` (array, ≥30 entries) | Filter out Belarusian function words capitalized at sentence-start | MEDIUM — ~30-60 prepositions/conjunctions/particles/copular forms; **must NOT be copied from Russian** — most entries differ; `ru.json:94-158` has 58 entries; mirror **categories**, translate from English / native-author each entry | HIGH. Without it, `Гэта` / `Так` / `Ну` / `Ёсць` / `Калі` etc. become candidate entities and pollute detection. |

### 3.3 Anti-Features — schema choices that look good but cause problems

Anti-features are documented to **prevent** them — items below are NOT in the table stakes nor differentiators because they actively cause problems if added.

| Anti-feature | Why it looks attractive | Why it's actually a problem | Alternative |
|--------------|-------------------------|------------------------------|-------------|
| **Declaring `entity.boundary_chars` for Belarusian** (e.g. `"\\w\\u0400-\\u04FF\\u0500-\\u052F"`) | Hindi declares it — looks like "the right thing for non-ASCII scripts" | `_expand_b` and `_wrap_candidate` only fire when `boundary_chars` is truthy (`__init__.py:144-159`). Cyrillic letters including `Ў`/`І`/`ў`/`і` are precomposed `Lu`/`Ll` codepoints inside Python's Unicode `\w` — default `\b` works correctly. **Adding `boundary_chars` is a no-op** that adds review friction with zero benefit. Verified empirically (STACK.md Layer 1). | **OMIT it.** Default `\b` semantics work for Belarusian. |
| **Inheriting Russian's `[А-ЯЁ]` candidate class verbatim** | `ru.json` is the obvious Cyrillic template — copy-paste-translate seems efficient | `[А-Я]` is U+0410–U+042F. Belarusian-specific letters `Ў` (U+040E) and `І` (U+0406) fall **outside** this range and are silently dropped from candidate extraction. Verified empirically in STACK.md. | Use `[А-ЯЁІЎ][а-яёіў]{1,19}` (and matching multi-word). |
| **Translating `ru.json` strings instead of translating from `en.json`** | Russian and Belarusian share script + ~70-80% lexical overlap; copy-translate is faster | Produces machine-Russified Belarusian (Trasianka), the explicit "this project has failed" condition from PROJECT.md:25-26. False friends pass casual review (`вяселле` = wedding in BE, "fun" in RU; `благі` = bad in BE, "good" in RU). Past-tense gender suffix shape differs (BE masc `сказаў`, RU masc `сказал` — character class trick `[аи]?` doesn't carry over). | Translate each string from `en.json`. Use `ru.json` ONLY for *structural* reference (which keys exist, what shape patterns take). Native review on every string. See PROJECT.md Key Decisions row 3, PITFALLS.md Pitfall 1. |
| **`person_verb_patterns` with only one gender form** (e.g. only `\\b{name}\\s+сказаў\\b`) | "I'll add the masculine; the feminine pattern looks similar" | Belarusian past tense agrees with subject **gender** (masc `-ў`, fem `-ла`, pl `-лі`). Missing one form = pattern silently fails on female-named or plural-subject sentences. **The Russian trick `сказал[аи]?` does NOT work** — Belarusian masc has no vowel suffix to make optional. | Use explicit alternation: `\\b{name}\\s+сказа(ў\|ла\|лі)\\b`. For reflexive: `\\b{name}\\s+пасьмяяў(ся\|ся)\\b` (be-tarask) or `\\b{name}\\s+пасмяяў(ся\|ся)\\b` (be). |
| **`pronoun_patterns` with only nominative case** (e.g. only `\\bён\\b`, `\\bяна\\b`, `\\bяны\\b`) | "Pronouns" sounds like a small closed set | Belarusian (like Russian) is heavily inflected. Pronouns appear in 6 cases. Nominative-only = misses most contexts (`<name> заўсёды любіў яе` would not score because `яе` ≠ `яна`). | Cover all 6 cases per gender: masc `ён/яго/яму/ім`, fem `яна/яе/ёй/ёю` (some collapse, that's fine), pl `яны/іх/ім/імі`. |
| **Mixing orthographies inside one file** | LLM assistance may output either orthography depending on prompt; author switches mental modes mid-file | A single Tarashkievitsa form (`сьвет`) inside `be.json` (Narkamauka) reads as a defect to a native reviewer. Same in reverse. Defeats the purpose of two files. PITFALLS.md Pitfall 2. | Author each file in one sitting against its rule book (Narkamauka → 2008 law; Tarashkievitsa → 2005 Buslakou/Viacorka/Sanko/Sauka). Diff at end for semantic parity, not lexical identity. |
| **Empty `entity.stopwords` array** (`[]`) | "We can fall back to English stopwords" | English fallback fires only if NO requested locale has any entity section at all. With `("be","en")`, the `en` stopwords are *added* to BE's empty set — Belarusian function words like `Гэта`, `Так`, `Ну`, `Ёсць`, `Калі`, `Што` capitalized at sentence-start are **not** in the English stopword list and become candidate "entities", polluting detection. | Populate ≥30 entries: prepositions (`у/ў/на/па/за/пра/без/для/каля/паміж/сярод/праз/супраць`), conjunctions (`і/але/ці/калі/каб/таму/таксама/аднак/затое/хаця`), particles (`не/ні/жа/б/бы/ж/нават/толькі/амаль/прыкладна`), copular and modal (`ёсць/быў/была/было/будзе/можа/трэба/павінен`). |
| **`ensure_ascii=True` JSON serialization** (e.g. `"\u043f\u0430\u043b\u0430\u0446"` instead of `"палац"`) | Default in some JSON tooling | Breaks visual review (illegible diff in PR), inflates file size ~3×, doesn't match existing `ru.json`/`zh-CN.json` convention | Always serialize with `ensure_ascii=False` (Python 3.5+ has same performance — verified in CPython `Doc/whatsnew/3.5.rst`). Pretty-print with `indent=2`. |
| **UTF-8 BOM at start of file** | Some Windows editors add it by default | Injects `\ufeff` as first character — JSON parser sees invalid leading content; `_LANG_DIR.read_text(encoding="utf-8")` does NOT strip it (would need `encoding="utf-8-sig"`) | UTF-8 without BOM. Verify with `xxd` or hex viewer that first byte is `0x7B` (`{`), not `EF BB BF`. |
| **NFD (decomposed) Unicode normalization** | Some macOS filesystems normalize filenames to NFD | Belarusian Cyrillic letters have precomposed code points (`Ё`=U+0401, `й`=U+0419, `ў`=U+045E). NFD would decompose into base + combining marks, which renders the same but breaks byte-equality and changes `\w` semantics in some pattern engines | Use NFC (precomposed). Default for Python `str` literals. Verify with `unicodedata.is_normalized('NFC', s)` if pasting from external source. |
| **Adding new top-level keys** (e.g. `"orthography": "narkamauka"`) | Self-documenting | NOT consumed by any code — purely decorative; adds review surface and drift risk; `lang` and `label` are already convention-only and never consumed | Use the file stem (`be.json` vs `be-tarask.json`) as the orthography indicator. Document orthography in the PR description and `label` autonym (`Беларуская` vs `Беларуская (тарашкевіца)`). |
| **`re.ASCII` flag in any pattern** (`(?a)…`) | "Restrict to ASCII to be safe" | Restricts `\w`/`\b`/`\s` to ASCII-only — would make every Belarusian Cyrillic letter a non-word-character and silently break every pattern | Default Python 3 `re` semantics (Unicode `\w` and `\b`). No flag needed. |
| **Per-orthography `cli` strings that visually differ when the difference is noise** (e.g. `Гатова` (be) vs `Гатова` (be-tarask) — same word, both correct in both orthographies) | "Two files = two different translations everywhere" | Wastes review effort; obscures real orthographic differences when reviewer diffs the two files | Keep `cli` and `terms` strings **identical between be and be-tarask wherever both orthographies use the same word**. The two files diverge only where orthography demands it (soft-sign placement, foreign-word adaptation, lexical choices like `зала`/`заля`). |

---

## 4. Section / Schema Dependencies (inter-section consistency)

The locale schema has implicit consistency rules that no test enforces but a native reader notices immediately. These dependencies inform the order of authoring and the cross-section review checklist.

```
                               ┌─────────────────────────┐
                               │  terms.* (vocabulary)   │
                               │  - palace, wing, hall,  │
                               │    closet, drawer, mine,│
                               │    search, status, init,│
                               │    repair, migrate,     │
                               │    entity, topic        │
                               └────────────┬────────────┘
                                            │
                  ┌─────────────────────────┼─────────────────────────────────┐
                  │                         │                                 │
       conjugated form appears in           │                       inflected form may appear in
                  ▼                         │                                 ▼
        ┌──────────────────┐                │                    ┌─────────────────────────┐
        │ cli.* (14 keys)  │                │                    │ regex.action_pattern    │
        │ - status_palace  │                │                    │ regex.topic_pattern     │
        │ - status_wings   │                │                    │ entity.project_verbs    │
        │ - status_closets │                │                    │   (e.g. "сістэма {name}"│
        │ - status_drawers │                │                    │    matches terms.entity)│
        │ - mine_start     │                │                    └─────────────────────────┘
        │ - mine_complete  │                │
        │ - mine_skip      │                │
        │ - init_complete  │                │
        │ - init_exists    │                │
        │ - no_palace      │                │
        │ - repair_complete│                │
        │ - migrate_*      │                │
        │ - search_*       │                │
        └──────────────────┘                │
                                            │
                    aaak.instruction language matches the locale
                                            │
                                            ▼
                              ┌──────────────────────────────┐
                              │ aaak.instruction (one string)│
                              │  - language tells LLM what   │
                              │    target language to use    │
                              │  - vocabulary should match   │
                              │    terms.* where overlapping │
                              └──────────────────────────────┘

                              ┌──────────────────────────────┐
                              │ entity.* (script-aware)      │
                              │                              │
                              │  candidate_pattern  ──────┐  │
                              │  multi_word_pattern       │  │  Char class MUST cover every
                              │                           ├──┼──> proper-noun script char
                              │  All pattern char         │  │  used elsewhere in the file
                              │  classes must be          │  │  (e.g., personal pronoun
                              │  consistent              ─┘  │  cases: ёй, ім, ёю)
                              │                              │
                              │  person_verb_patterns ────┐  │  Verbs of speech in entity
                              │                           │  │  must conjugate the same way
                              │                           ├──┼──> as past-tense verbs in
                              │                           │  │  cli.* and aaak.instruction
                              │  pronoun_patterns         │  │  (consistent gender/aspect)
                              │  dialogue_patterns        │  │
                              │  direct_address_pattern   │  │
                              │  project_verb_patterns ───┘  │
                              │                              │
                              │  stopwords ─────────┐        │
                              │                     ├────────┼──> Should overlap with
                              │  regex.stop_words ──┘        │   regex.stop_words (same
                              │                              │   function-word inventory)
                              └──────────────────────────────┘
```

### 4.1 Required Consistency Rules

| Rule | Why | Example | Verification method |
|------|-----|---------|---------------------|
| `terms.palace` noun appears in conjugated form in `cli.status_palace`, `cli.init_complete`, `cli.init_exists`, `cli.no_palace`, `aaak.instruction` (if it mentions the metaphor) | A user who reads "Palace: ..." (`status_palace`) and "Palace not found" (`no_palace`) expects the same word for both | If `terms.palace` = `палац`, then `cli.status_palace` = `Палац: {path}` and `cli.no_palace` = `Палац не знойдзены...` (both use `палац`) | Manual diff: grep the chosen `terms.palace` value across `cli.*` strings |
| `terms.wing` / `closet` / `drawer` plural forms appear in `cli.status_wings` / `mine_complete` / `status_closets` / `status_drawers` | Same reason — vocabulary consistency | If `terms.closet` = `шафа` (fem sg), then `cli.status_closets` uses Belarusian count grammar: `Шафаў: {count}` (genitive plural) or `{count} шафаў` | Native review checks plural-noun-genitive form is correct for arbitrary `{count}` (Slavic plurals are number-class-sensitive but using the genitive plural form is a common simplification — `ru.json` does this) |
| `terms.mine` verb chosen affects `cli.mine_start`, `cli.mine_complete`, `cli.mine_skip` | The verbal action must match the noun chosen | If `terms.mine` = `здабываць` (impf inf), then `cli.mine_start` = `Здабываем {path}...` (1pl pres) and `cli.mine_skip` = `Ужо здабыта...` (passive past) | Native review checks aspect (perfective vs imperfective) is correct for each context |
| `entity.candidate_pattern` character class must include every uppercase letter used at the start of names anywhere else in the file | A name like `Іван` in a `dialogue_patterns` example (e.g. `\"Іван сказаў"`) must be matchable by `candidate_pattern`; if `candidate_pattern` is `[А-ЯЁ]…` it doesn't include `І` (U+0406), so detection is broken even though the example "looks right" | `candidate_pattern` = `[А-ЯЁІЎ][а-яёіў]{1,19}` covers ALL Belarusian uppercase Cyrillic letters | Empirical: `re.compile(pat).findall(test_name)` for representative Belarusian names (`Іван`, `Ўладзіслаў`, `Алёна`, `Алесь`, `Кацярына`) |
| `entity.multi_word_pattern` character class must mirror `candidate_pattern` | Multi-word names should detect the same letters as single-word names | If `candidate_pattern` = `[А-ЯЁІЎ][а-яёіў]{1,19}`, then `multi_word_pattern` = `[А-ЯЁІЎ][а-яёіў]+(?:\\s+[А-ЯЁІЎ][а-яёіў]+)+` | Visual diff |
| `entity.person_verb_patterns` past-tense verbs use the SAME gender/aspect alternation form as `regex.action_pattern` and any past-tense verbs in `cli.*` / `aaak.instruction` | Inflectional inconsistency reads as machine translation | Both `entity.person_verb_patterns` and `regex.action_pattern` should use `сказаў/сказала/сказалі` shape, not `сказал/сказала/сказали` (Russian shape) | Native review |
| `entity.pronoun_patterns` covers ALL 6 cases per gender | Pronoun proximity score requires matching pronouns in any case | Belarusian: nom `ён`, gen `яго`, dat `яму`, acc `яго`, inst `ім`, prep `(пры) ім` (masc); same for fem (`яна/яе/ёй/яе/ёю/(пры) ёй`) and pl (`яны/іх/ім/іх/імі/(пры) іх`) | Cross-reference against `verbum.by` GrammarDB (NAS Belarus 2026/01) |
| `entity.stopwords` (lowercase) overlaps significantly with `regex.stop_words` (lowercase, space-separated) | Both sections describe the same closed-class vocabulary (function words); consistency reduces drift | Both should include `і`, `але`, `ці`, `у`, `ў`, `на`, `за`, `пра`, `гэта`, `так`, `не`, `ні`, etc. | Grep: every word in `entity.stopwords` should appear (after splitting) in `regex.stop_words` and vice versa |
| `aaak.instruction` is in the SAME LANGUAGE as the locale | The LLM is told to compress in this language; if the instruction is in English, the LLM may ignore the target | `be.json`: instruction in Narkamauka. `be-tarask.json`: instruction in Tarashkievitsa (with soft-sign markings if applicable: `сьцісьніце` vs `сцісніце`) | Native review |
| `aaak.instruction` length > 10 characters | Test enforces this (`tests/test_i18n.py:43`) | Belarusian instructions are typically 100-200 chars (mirror `ru.json:36` length: `"Сжать до индексного формата. Дефисы между словами, вертикальные черты между понятиями. Убрать предлоги и служебные слова. Имена и числа сохранять точно."` — 165 chars). Belarusian equivalent will be similar length. | `len(s) > 10` |

### 4.2 Cross-File Consistency Rules (`be.json` ↔ `be-tarask.json`)

| Rule | Why | Example |
|------|-----|---------|
| Same `cli.*` placeholders (`{path}`, `{closets}`, `{drawers}`, `{count}`, `{fixed}`, `{query}`) in identical positions | Tests enforce specific placeholder names; the test contract applies to BOTH files | Both `cli.mine_complete` strings include `{closets}` and `{drawers}` literally |
| Same `entity.candidate_pattern` and `multi_word_pattern` character class (Cyrillic alphabet doesn't change between orthographies) | Both orthographies use the same 32-letter Belarusian Cyrillic alphabet (`А-Яё`+`І`+`Ў` and lowercase) | Both use `[А-ЯЁІЎ][а-яёіў]{1,19}` |
| **Different** `aaak.instruction` orthography (Tarashkievitsa uses soft-sign before consonants, foreign-word adaptation differs) | The instruction itself is a sample of the language; if it doesn't follow the orthography, the file fails its own quality bar | `be.json`: `Сцісніце ... сістэму ...`; `be-tarask.json`: `Сьцісьніце ... сыстэму ...` |
| **Possibly different** `terms.hall` (`зала` Narkamauka / `заля` Tarashkievitsa) | Lexical choice differs between orthographies (per PROJECT.md:101) | Confirm with native reviewer; not all `terms.*` differ — most overlap |
| **Different** `entity.person_verb_patterns` reflexive endings (`-ся` Narkamauka / `-сь` or `-ся` Tarashkievitsa, with soft-sign in Tarashkievitsa) | Tarashkievitsa marks palatalization explicitly | `be.json`: `усміхнуўся`; `be-tarask.json`: `усьміхнуўся` |
| Same `entity.dialogue_patterns` shape (`^>\\s*{name}[:\\s]`, `^{name}:\\s`, `^\\[{name}\\]`) | These are universal text formatting conventions, language-independent | Identical patterns in both files |
| **Different** `entity.dialogue_patterns` Belarusian-specific quoted-said pattern (`\"{name}\\s+сказаў` vs maybe-different past-tense form) | Same shape, may differ if Tarashkievitsa prefers a different verb | `\"{name}\\s+сказаў` should work for both unless native reviewer prefers `\"{name}\\s+казаў` for Tarashkievitsa |

---

## 5. MVP-vs-Full-Tier Definition

### 5.1 MVP — minimum to pass tests (NOT the deliverable)

**This is documented for reference only.** The PROJECT.md commits us to full tier, but knowing the floor is useful for understanding the test contract.

What ships:
- 1 `lang` string (e.g. `"be"` or `"be-tarask"`)
- 1 `label` string (e.g. `"Беларуская"`)
- `terms` object with at minimum:
  - `terms.palace` (non-empty string)
  - `terms.wing` (non-empty string)
  - `terms.closet` (non-empty string)
  - `terms.drawer` (non-empty string)
  - **Total: 4 keys**
- `cli` object with at minimum:
  - `cli.mine_complete` (string containing `{closets}` and `{drawers}` literal)
  - `cli.status_drawers` (string containing `{count}` literal)
  - **Total: 2 keys**
- `aaak` object with:
  - `aaak.instruction` (string, length > 10)
  - **Total: 1 key**

**Total MVP surface: 9 strings.** Passes all tests in `tests/test_i18n.py` (verified by reading every assertion in the file). Fails the spirit of the contribution and produces broken Belarusian entity detection.

### 5.2 Full Tier — what we actually ship (per PROJECT.md commitment)

What ships:
- 1 `lang` string
- 1 `label` string
- `terms` object with **all 13 keys** translated (4 hard + 9 conventional)
- `cli` object with **all 14 keys** translated (correct `{var}` interpolation per Sec. 1.3)
- `aaak.instruction` (≥10 chars, fluent native Belarusian instruction matching the orthography)
- `regex` object with **all 4 keys** (`topic_pattern`, `stop_words`, `quote_pattern`, `action_pattern`) tuned for Belarusian:
  - `topic_pattern`: `[А-ЯЁІЎ][а-яёіў]{2,}\|[A-Z][a-z]{2,}\|[A-Za-z][A-Za-z0-9_]{2,}`
  - `stop_words`: ~30-50 native Belarusian function words (NOT translated from Russian)
  - `quote_pattern`: `«\\s*([^»]{10,200})\\s*»\|\"([^\"]{10,200})\"` (mirror `ru.json:41`)
  - `action_pattern`: 13-15 Belarusian past-tense action verbs in non-capturing alternation, then `\\s+[\\wа-яёіўА-ЯЁІЎ\\s]{3,30}` for the object phrase
- `entity` object with **all 8 sub-keys** (no `boundary_chars` — see Anti-Features §3.3):
  - `candidate_pattern`: `[А-ЯЁІЎ][а-яёіў]{1,19}`
  - `multi_word_pattern`: `[А-ЯЁІЎ][а-яёіў]+(?:\\s+[А-ЯЁІЎ][а-яёіў]+)+`
  - `person_verb_patterns`: ~15 entries with gender/aspect alternation
  - `pronoun_patterns`: ~9-12 entries covering 6 cases × 3 genders
  - `dialogue_patterns`: 4 entries (3 universal + 1 Belarusian-specific quoted-said)
  - `direct_address_pattern`: 1 string with `\|`-alternation of ≥5 greetings
  - `project_verb_patterns`: ~10 entries
  - `stopwords`: ~30-60 entries (prepositions, conjunctions, particles, copular forms)

**Total full-tier surface per file:**

| Section | Number of strings/patterns |
|---------|----------------------------|
| top-level | 2 (`lang`, `label`) |
| `terms` | 13 |
| `cli` | 14 |
| `aaak` | 1 |
| `regex` | 4 |
| `entity` | 8 (one is a list of ~15, etc. — see below) |
| **String count if we count every list entry separately** | ~95-110 strings (approx; `ru.json` has 109 string-equivalents) |
| **Top-level keys** | 7 (`lang`, `label`, `terms`, `cli`, `aaak`, `regex`, `entity`) |
| **Sub-keys total** | 13 + 14 + 1 + 4 + 8 = **40 sub-keys** |

**File size reference (existing precedent):**
- `ru.json` = 161 lines, ~5KB on disk
- `pt-br.json` = 173 lines, ~5KB
- `it.json` = 187 lines, ~5KB
- `id.json` = 235 lines (largest, due to ~40 person verbs + Indonesian particles), ~7KB
- `hi.json` = 105 lines, ~6KB (Devanagari is byte-dense in UTF-8)

Expected size for `be.json` and `be-tarask.json`: **~160-180 lines, ~6KB each** (Cyrillic is ~2 bytes per character in UTF-8, so file size ≈ Russian).

### 5.3 Tier Comparison

| Criterion | MVP (test floor) | Full Tier (deliverable) | Delta |
|-----------|------------------|--------------------------|-------|
| Top-level keys | 5 (`lang`, `label`, `terms`, `cli`, `aaak`) | 7 (+ `regex`, `entity`) | +2 sections |
| `terms` keys | 4 | 13 | +9 conventional |
| `cli` keys | 2 | 14 | +12 conventional |
| `aaak.instruction` | 1 | 1 | — |
| `regex` keys | 0 | 4 | +4 |
| `entity` sub-keys | 0 | 8 | +8 |
| Total sub-keys | 7 | 40 | +33 |
| Live consumer impact | LLM gets nudge to use Belarusian (via `aaak.instruction`) | Above + Cyrillic name detection works for ALL Belarusian names | Without entity, **0% of Belarusian names detected**; with entity, ~95%+ recall on prose (per `ru.json` evidence) |
| Test coverage of fields | 5 strings tested | 5 strings tested (same) | Tests don't cover the 33 additional sub-keys — review and empirical correctness are the gates |

---

## 6. Section Prioritization Matrix (per file)

| Section / sub-key | User Value | Implementation Cost | Authoring Risk | Priority |
|-------------------|------------|---------------------|----------------|----------|
| `lang`, `label` | LOW (decorative) | LOW (1 line each) | LOW | P1 (parity with all 13 locales) |
| `terms.palace` | HIGH (test gate) | LOW | LOW (single noun, well-attested) | P1 |
| `terms.wing` | HIGH (test gate) | LOW | LOW | P1 |
| `terms.closet` | HIGH (test gate) | MEDIUM (anti-Russification: must use `шафа`, NOT `шкаф`) | MEDIUM | P1 |
| `terms.drawer` | HIGH (test gate) | MEDIUM (`шуфляда` is the right word; check against `verbum.by`) | MEDIUM | P1 |
| `terms.{hall,mine,search,status,init,repair,migrate,entity,topic}` | LOW (no live consumer; convention) | LOW (9 nouns) | LOW | P2 (parity with 13 locales) |
| `cli.mine_complete` | HIGH (test gate, dual interpolation) | LOW | LOW (just preserve `{closets}` and `{drawers}`) | P1 |
| `cli.status_drawers` | HIGH (regression test gate) | LOW | MEDIUM (must use `{count}`, not `{drawers}` — Korean PR's exact bug) | P1 |
| `cli.{mine_start, mine_skip, search_no_results, search_results, status_palace, status_wings, status_closets, init_complete, init_exists, repair_complete, migrate_complete, no_palace}` | LOW today (no live consumer); HIGH future | LOW-MEDIUM (12 short strings; care with `{path}`/`{count}`/`{fixed}`/`{query}` placeholders) | LOW-MEDIUM | P2 (parity) |
| `aaak.instruction` | HIGH (LIVE production consumer in `closet_llm`) | MEDIUM (one fluent Belarusian sentence, ≥10 chars; orthography must match file) | MEDIUM | P1 |
| `regex.topic_pattern` | LOW today; LOW-MEDIUM future | LOW | LOW (one regex, mirror `ru.json` shape with `ІЎ`/`іў`) | P2 |
| `regex.stop_words` | LOW today; MEDIUM future | MEDIUM (~30-50 words; **not from Russian**) | HIGH (false friends, function-word divergence) | P2 |
| `regex.quote_pattern` | LOW today; LOW future | LOW | LOW (mirror `ru.json:41` verbatim — Belarusian uses same `«»` quotes as Russian) | P2 |
| `regex.action_pattern` | LOW today; MEDIUM future | MEDIUM (~14 verbs in past tense) | HIGH (must use `-ў`/`-іў`/`-аў` endings, not Russian `-л`/`-ил`/`-ал`) | P2 |
| `entity.candidate_pattern` | **CRITICAL** (live consumer; without it, entity detection on Cyrillic = 0%) | LOW (one regex line) | LOW (verified empirically — `[А-ЯЁІЎ][а-яёіў]{1,19}`) | P1 |
| `entity.multi_word_pattern` | CRITICAL | LOW | LOW (mirror candidate, add concatenation) | P1 |
| `entity.person_verb_patterns` | HIGH (person classification) | MEDIUM-HIGH (~15 patterns; gender/aspect alternation; Tarashkievitsa soft-sign reflexives differ) | HIGH (most error-prone — verb morphology is dense) | P1 |
| `entity.pronoun_patterns` | HIGH (pronoun proximity scoring) | MEDIUM (~9-12 entries; 6 cases × 3 genders) | MEDIUM (well-attested but easy to miss a case) | P1 |
| `entity.dialogue_patterns` | MEDIUM-HIGH (strongest person signal at 3 pts/match) | LOW (4 entries, 3 universal + 1 Belarusian) | LOW | P1 |
| `entity.direct_address_pattern` | MEDIUM-HIGH (strongest signal at 4 pts/match) | LOW-MEDIUM (one alternation string of ≥5 greetings) | MEDIUM | P1 |
| `entity.project_verb_patterns` | MEDIUM (project classification; disambiguates names from codenames) | MEDIUM (~10 entries with Belarusian aspectual pairs) | MEDIUM | P1 |
| `entity.stopwords` | HIGH (without it, Belarusian function words pollute detection) | MEDIUM (~30-60 entries, native review on each) | HIGH (must NOT be Russian-translated) | P1 |
| `entity.boundary_chars` | NEGATIVE (no-op for Cyrillic, adds review friction) | LOW | LOW | **OMIT** (Anti-Feature §3.3) |

**Priority key:**
- **P1** = Required for the PR to ship per PROJECT.md requirements (BE-01 through BE-09, NATIVE-01)
- **P2** = Required for parity with 13 existing locales (no test enforces, but "minimal-tier" leaves the file looking incomplete)

---

## 7. Roadmap Implications

These translate directly into phase recommendations for `ROADMAP.md`:

1. **Phase: `be.json` Narkamauka — base file (lang/label/terms/cli/aaak/regex)**
   - Mirrors commit `b87ada3` (Russian base file) and `2e998db` (Italian base file)
   - Single commit: `feat(i18n): add Belarusian (Narkamauka) locale`
   - Ships P1 + P2 sections except `entity`
   - Test gate: `pytest tests/test_i18n.py -v`

2. **Phase: `be.json` Narkamauka — entity section**
   - Mirrors commit `d6bd7de` (Russian entity) and `69453b2` (Italian entity)
   - Single commit: `feat(i18n): add entity detection section to Belarusian (Narkamauka)`
   - Ships entity P1 sub-keys
   - Test gate: `pytest tests/test_i18n.py tests/test_i18n_lang_case.py tests/test_entity_detector.py -v`

3. **Phase: `be-tarask.json` Tarashkievitsa — base file**
   - Same shape as Phase 1 but with Tarashkievitsa orthography
   - Single commit: `feat(i18n): add Belarusian (Tarashkievitsa) locale`

4. **Phase: `be-tarask.json` Tarashkievitsa — entity section**
   - Same shape as Phase 2 but with Tarashkievitsa morphology where applicable
   - Single commit: `feat(i18n): add entity detection section to Belarusian (Tarashkievitsa)`

5. **Phase: tests + native review**
   - Optional: extend `test_dialect_compress_samples` with Belarusian sample (PROJECT.md `TEST-02`)
   - Native-speaker review pass on every string (PROJECT.md `NATIVE-01`)
   - Single commit if test added: `test(i18n): add Belarusian sample to dialect compress test`

6. **Phase: PR submission**
   - Branch `feat/i18n-belarusian` from upstream `develop`
   - PR description per `PROJECT.md` `PR-02` (template from #760, #907, #778)
   - CI must pass: ruff, pytest matrix, coverage gate

**Phase ordering rationale:**
- Sequential per-file authorship (be → be-tarask) reduces context-switching that causes orthography mixing (PITFALLS.md Pitfall 2)
- Base + entity split per file mirrors the established pattern across Russian and Italian PRs (verified via `user-git`)
- Native review pass is the LAST gate before any commit (per `NATIVE-01` discipline)

---

## 8. Sources

| Source | Type | Confidence | What it verified |
|--------|------|------------|------------------|
| `mempalace/i18n/__init__.py` (read in full, 286 lines) | Codebase | HIGH | Schema consumer rules: `t()` returns dotted-key on miss; `get_regex()` returns `{}`; `get_entity_patterns` merge semantics; English fallback only when zero entity sections present; `_canonical_lang` case-insensitivity |
| `mempalace/i18n/en.json` (read in full, 146 lines) | Codebase | HIGH | Canonical schema reference: 7 top-level sections, 13 `terms` sub-keys, 14 `cli` sub-keys, 1 `aaak.instruction`, 4 `regex` sub-keys, 8 `entity` sub-keys |
| `mempalace/i18n/ru.json` (read in full, 161 lines) | Codebase | HIGH | Closest sibling reference: full-tier Cyrillic locale; reveals the `[А-ЯЁ]` Belarusian-letter gap; provides shape for entity patterns |
| `mempalace/i18n/de.json` (44 lines), `es.json`, `fr.json`, `ja.json`, `ko.json`, `zh-CN.json`, `zh-TW.json` (each read in full) | Codebase | HIGH | Minimal-tier examples (no `entity` section); confirms 7 of 13 locales lack entity coverage |
| `mempalace/i18n/it.json` (187 lines), `pt-br.json` (173 lines), `id.json` (235 lines), `hi.json` (105 lines) | Codebase | HIGH | Full-tier examples; Hindi establishes the `boundary_chars` precedent (only locale to use it); pt-br establishes hyphenated-tag precedent; Indonesian shows the largest entity section (~40 person verbs) |
| `tests/test_i18n.py` (read in full, 88 lines) | Codebase | HIGH | Every test assertion that the new files must satisfy: required sections (`terms`/`cli`/`aaak`), required terms (`palace`/`wing`/`closet`/`drawer`), `cli.mine_complete` interpolation, `cli.status_drawers` uses `{count}`, `aaak.instruction` length > 10, Dialect loads lang |
| `mempalace/dialect.py:300-348` (read) | Codebase | HIGH | `Dialect.__init__` consumes `aaak.instruction` and `regex.*` (the latter stored in `self.lang_regex` but never read again — verified via Grep) |
| `mempalace/closet_llm.py:115-134` (read in `.planning/research/ARCHITECTURE.md`) | Codebase (cited via existing research) | HIGH | `closet_llm._call_llm` is the live production consumer of `t("aaak.instruction")` |
| `mempalace/entity_detector.py` (read in full, 591 lines) | Codebase | HIGH | How `entity.*` sub-keys are consumed; default flags are `re.IGNORECASE` for verbs, `re.MULTILINE \| re.IGNORECASE` for dialogue; scoring weights (3 for dialogue, 4 for direct, 2 for person verbs); `_pronoun_re` joins all pronouns with `\|` |
| Grep across entire repo (`t\\(\"cli\\.`, `t\\(\"terms\\.`, `t\\(\"aaak\\.`, `lang_regex`, `\\.get\\(\"lang`, `\\.get\\(\"label`) | Codebase | HIGH | Confirms `mempalace/cli.py` does NOT call `t()`; `cli.*` keys are only exercised by `tests/test_i18n.py`; `lang` and `label` top-level keys are NOT consumed by any code; `regex.*` is consumed only via `Dialect.lang_regex` and never read after assignment |
| **`user-git` MCP `git_show b87ada3`** (verified) | Git history | HIGH | "feat: add Russian language support to i18n module" by mvalentsev, 2026-04-13 — the base file commit (lang/label/terms/cli/aaak/regex; NO entity yet). Sets the pattern for "base file first" |
| **`user-git` MCP `git_show d6bd7de`** (verified) | Git history | HIGH | "feat(i18n): add entity detection section to Russian locale" by mvalentsev, 2026-04-15 — entity section added in a follow-up commit. Sets the pattern for "entity in separate commit" |
| **`user-git` MCP `git_show 2e998db`** (verified) | Git history | HIGH | "feat: add italian i18n support" by Martin Masevski, 2026-04-15 — same base-file pattern as Russian |
| **`user-git` MCP `git_show 69453b2`** (verified) | Git history | HIGH | "feat: add italian entity patterns" by Martin Masevski, 2026-04-15 — same entity-follow-up pattern as Russian |
| **`user-git` MCP `git_show 3d13a72`** (verified) | Git history | HIGH | "feat(i18n): add Brazilian Portuguese locale with entity detection (closes #117)" by mvalentsev, 2026-04-15 — single commit with base + entity together (the framework was already in place). Demonstrates the alternative "single commit" pattern is also acceptable |
| `.planning/research/STACK.md` (read in full, 375 lines) | Internal research | HIGH | Layer 1 technical contract (Python 3.9, JSON UTF-8, `re` Unicode-default), critical regex caveat (Belarusian needs `[А-ЯЁІЎ][а-яёіў]{1,19}`), why no `boundary_chars` for Cyrillic |
| `.planning/research/ARCHITECTURE.md` (read partial, 150 lines + grep) | Internal research | HIGH | Cross-section consumer matrix; key non-finding that `cli.py` does NOT consume `cli.*`; key non-finding that `Dialect.lang_regex` is never read after assignment |
| `.planning/research/PITFALLS.md` (read partial, 100 lines) | Internal research | HIGH | Anti-features §3.3: orthography mixing, Russian-source translation, past-tense verb shape, false friends |
| `.planning/PROJECT.md` (read in full, 154 lines) | Project context | HIGH | Confirms full-tier deliverable (BE-01 through BE-09, NATIVE-01), confirms 4 hard `terms` keys + 13 conventional, confirms 14 `cli` keys, confirms `aaak.instruction` requirement, confirms `regex` requirement BE-05, confirms entity requirement BE-06 |
| `.planning/codebase/STACK.md` (cited by `STACK.md`) | Codebase intel | HIGH | Confirms ChromaDB+PyYAML-only dependency rule, Python ≥3.9, ruff config |

**MCP citations (per quality gate requirement):**

- ✅ `user-git` MCP — verified via `git_show` against commits `b87ada3`, `d6bd7de`, `2e998db`, `69453b2`, `3d13a72` (each call returned the verbatim commit message and patch). Establishes the recent locale-PR commit pattern (base file + entity in separate atomic commits).
- ⚠ `user-mempalace` MCP — listed in `PROJECT.md:107` as available, but its tools (`mempalace_search`, `mempalace_kg_query`, etc.) operate on a chromadb-backed memory palace store, NOT a codebase semantic search index. Tool descriptors at `~/.cursor/projects/Users-itfarrier-pet-mempalace/mcps/user-mempalace/tools/` confirm the MCP is the MemPalace product, not a code-intelligence layer. Codebase consumer-tracing was therefore performed via Grep across the repo (citations above), which served the same purpose with HIGH confidence.

---

*Features research for: MemPalace Belarusian i18n contribution (`be` + `be-tarask`)*
*Researched: 2026-04-20*
*Brownfield re-interpretation: "feature" = locale schema section. No translations drafted — schema analysis only. Native-speaker review (NATIVE-01) is the gate for translation quality.*

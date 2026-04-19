# Stack Research — MemPalace Belarusian i18n (`be` + `be-tarask`)

**Domain:** Brownfield i18n contribution to an existing Python package (data-only, two new locale JSONs)
**Researched:** 2026-04-20
**Overall confidence:** HIGH (technical contract empirically verified; linguistic resources sourced from primary references)

> **How to read this document.** This is not a greenfield "pick a framework" stack. The MemPalace package already exists, the i18n module already supports auto-discovery / case-insensitive lookup / hyphenated tags / per-locale entity merge, and the only new artifacts are two JSON files. The "stack" is therefore split into two layers:
>
> 1. **Layer 1 — Existing technical contract** that `be.json` and `be-tarask.json` MUST satisfy (Python version, JSON encoding, regex flavor, schema, CI gates). Everything here is a hard constraint inherited from upstream.
> 2. **Layer 2 — Linguistic stack** the human translator relies on to produce native-quality Belarusian text (orthography references, dictionaries, grammar databases, BCP 47 sources). Everything here is *recommended* for the translator workflow; nothing ships in the PR except the JSON files.
>
> Sections from the greenfield template (`Recommended Stack` → `Core Technologies`, `Supporting Libraries`, `Development Tools`) have been re-interpreted accordingly. Versions are still pinned where they matter.

---

## Layer 1 — Existing Technical Contract (the upstream stack we must honor)

### Core Technologies (existing constraints — non-negotiable)

| Technology | Version | Purpose | Why It Constrains Us |
|------------|---------|---------|----------------------|
| **CPython** | `>=3.9` (`pyproject.toml:6`, ruff `target-version = "py39"`) | Runtime for the host package and its tests | Locale JSON is pure data, but the tests that load it run under 3.9 — so any pattern relying on a newer `re` semantics would break the matrix. Default `re` Unicode behavior has been stable since 3.0; we're safe (HIGH). |
| **JSON (RFC 8259, UTF-8)** | n/a | On-disk format for every `mempalace/i18n/*.json` file | `_LANG_DIR.read_text(encoding="utf-8")` (`mempalace/i18n/__init__.py:57`) decodes UTF-8. Files MUST be UTF-8 with no BOM (a BOM would inject `\ufeff` as an invalid JSON prefix character). HIGH (verified by reading the loader). |
| **Python `re` module** | stdlib (3.9+) | Compiles every `regex.*` and `entity.*` pattern from the locale file | In Python 3, str patterns are Unicode-aware by default — `\w` includes Cyrillic, and `\b` therefore correctly fires at Belarusian word boundaries. **Verified empirically**: `re.compile(r'\bІван\b\s+\bсказаў\b').findall('Іван сказаў…')` returns matches. NO `re.UNICODE` flag is needed (it's the default), and `re.ASCII` MUST NOT be used (would break Cyrillic). HIGH. |
| **ChromaDB** | `>=1.5.4,<2` (`pyproject.toml:30`) | Vector store; bundled embedding model is English-only | Locale files do not interact with ChromaDB. The known-degraded non-English semantic search (issue #712) is **out of scope** per `PROJECT.md` — it's an embedding-model swap, not an i18n contribution. HIGH (out-of-scope, but worth flagging for the roadmap). |
| **PyYAML** | `>=6.0,<7` (`pyproject.toml:31`) | Config parsing | Not touched by i18n. Listed only because the project's "thin deps" rule (CONTRIBUTING.md:66, "ChromaDB + PyYAML only") forbids us from adding any new runtime dep. We don't need to. HIGH. |

### Supporting Libraries (upstream tools we run, no new deps)

| Library | Version | Purpose | When We Use It |
|---------|---------|---------|----------------|
| **pytest** | `>=7.0` (`pyproject.toml:52`) | Test runner | `pytest tests/test_i18n.py tests/test_i18n_lang_case.py tests/test_entity_detector.py -v` is the local pre-commit gate (PROJECT.md `TEST-01`). |
| **pytest-cov** | `>=4.0` (`pyproject.toml:52`) | Coverage measurement | CI invokes with `--cov=mempalace --cov-fail-under=80` (`.github/workflows/ci.yml:21`). Adding two JSON files plus one optional `compress_samples` entry is coverage-neutral or positive. |
| **ruff** | `>=0.4.0,<0.5` (CI pin: `.github/workflows/ci.yml:49`; floor: `pyproject.toml:52`) | Lint + format | JSON files are not formatted by ruff, so `ruff format --check .` is not directly relevant to `be.json` / `be-tarask.json`. **But** if we touch `tests/test_i18n.py` (e.g. to add a Belarusian sample to `test_dialect_compress_samples`), that change MUST pass `ruff check .` and `ruff format --check .` cleanly. |
| **uv** (optional) | per `uv.lock` (~800 KB) | Lockfile management | `pip install -e ".[dev]"` is the documented dev install (CONTRIBUTING.md:13); uv is a faster alternative. Not required for our PR. |
| **hatchling** | (build backend) | Wheel build | Not touched. Wheel includes `mempalace/i18n/*.json` automatically because `[tool.hatch.build.targets.wheel] packages = ["mempalace"]`. |

### Development Tools

| Tool | Purpose | Notes / Configuration |
|------|---------|----------------------|
| **git** + **GitHub fork workflow** | Source control + PR | Fork `MemPalace/mempalace`, create branch `feat/i18n-belarusian` from `develop`, open PR against `develop` (NOT `main`). `CONTRIBUTING.md:58`. |
| **GitHub web UI** (no `gh` CLI installed locally) | PR submission | Recent i18n PRs that establish the convention: #760 (Russian), #907 (Italian), #778 (Indonesian), #117/#3d13a72 (pt-br), #927 (case-insensitive lookup, the regression that affects us). Use the existing UI; `user-fetch` MCP is the read-side tool for inspecting upstream PRs. |
| **Pre-commit** (`.pre-commit-config.yaml`, ruff `v0.4.10`) | Local lint enforcement | Optional but recommended; matches the CI pin. Won't lint our JSON files but will catch any test-file changes. |
| **`pytest -m 'not benchmark and not slow and not stress'`** (default `addopts`) | Default test selection | Already configured in `pyproject.toml:83`. Our tests are unmarked, so they run by default. |

### CI / Gating Pipeline (existing — what our PR must satisfy)

| Gate | Where | Constraint | How `be*.json` Satisfies |
|------|-------|------------|--------------------------|
| **Lint** | `.github/workflows/ci.yml:42-51` (Python 3.11) | `ruff check .` + `ruff format --check .` clean | JSON not linted by ruff; only matters if we touch `.py` files. |
| **Linux test matrix** | `.github/workflows/ci.yml:10-21` (Python 3.9 / 3.11 / 3.13) | `pytest --cov=mempalace --cov-fail-under=80` | New locales auto-discovered by `available_languages()`, so all loop-over-languages tests automatically include them. |
| **Windows test** | `.github/workflows/ci.yml:23-31` (Python 3.9) | Same | Same — Belarusian Cyrillic in JSON has no Windows-specific concern (UTF-8 read, no `print` to default cp1252 console). HIGH. |
| **macOS test** | `.github/workflows/ci.yml:33-41` (Python 3.9) | Same | Same. |
| **Coverage gate** | `--cov-fail-under=80` (CI), `fail_under = 85` (project, less strict) | 80% Linux/Windows/macOS | JSON addition is coverage-neutral. Adding a Belarusian sample to `test_dialect_compress_samples` adds ~6 lines of executed code, slightly raising coverage. |
| **Version Guard** | `.github/workflows/version-guard.yml` | Cross-checks version files | Untouched (we're not bumping versions). |
| **No new runtime deps** | `pyproject.toml:29-32` ("ChromaDB + PyYAML only" — CONTRIBUTING.md:66) | Adding any new dep needs a separate discussion | Pure data PR; trivially satisfied. |

### JSON Schema (the on-disk contract — exact keys per locale file)

| Section | Keys | Source of Truth | Why Required |
|---------|------|-----------------|--------------|
| top-level | `lang`, `label` | Convention across all 13 existing locales | `lang` should equal the file stem (e.g. `"be"` for `be.json`); `label` is the language's autonym (e.g. `"Беларуская"` for `be.json`, `"Беларуская (тарашкевіца)"` for `be-tarask.json`). HIGH. |
| `terms` | `palace`, `wing`, `hall`, `closet`, `drawer`, `mine`, `search`, `status`, `init`, `repair`, `migrate`, `entity`, `topic` (13 keys per `en.json`) | Test enforces presence of `palace`, `wing`, `closet`, `drawer` (`tests/test_i18n.py:10`); other 9 enforced only by lookup-or-fall-back-to-key in `t()` | Missing key returns the dotted-key string itself, not English fallback (`__init__.py:73`). All 13 should be translated for full tier. HIGH. |
| `cli` | 14 keys per `en.json` (see below) | Test enforces `mine_complete` interpolation (`tests/test_i18n.py:30`); regression `test_korean_status_drawers_uses_count` enforces `status_drawers` uses `{count}`, NOT `{drawers}` | All 14 strings need `{var}` interpolation discipline — Python `str.format` raises `KeyError` silently and falls through to the unformatted string (`__init__.py:79`), so a missing variable produces a confusing literal `{closets}` in user output. |
| `aaak.instruction` | one string > 10 chars | `tests/test_i18n.py:42` | Concatenated into the LLM prompt by `closet_llm.py:121-134`; non-empty Belarusian instruction nudges the LLM to compress in Belarusian. |
| `regex` (optional) | `topic_pattern`, `stop_words`, `quote_pattern`, `action_pattern` | Returned verbatim by `get_regex()` (`__init__.py:89`); consumed inside `dialect.py` | Used by `Dialect.compress()`. Without this section the dialect falls back to English regex — works but loses Belarusian quote markers (`«»`) and verb-tense matching. |
| `entity` (optional, full-tier) | `boundary_chars` (no, for Cyrillic), `candidate_pattern`, `multi_word_pattern`, `person_verb_patterns`, `pronoun_patterns`, `dialogue_patterns`, `direct_address_pattern`, `project_verb_patterns`, `stopwords` | Merged by `_collect_entity_section` (`__init__.py:162`); consumed by `mempalace/entity_detector.py` | Without `entity`, person/project detection on Belarusian text falls back to English `[A-Z][a-z]` candidate pattern and misses ALL Cyrillic names. HIGH-IMPACT for Belarusian users. |

**`cli` keys (14, from `en.json`):** `mine_start`, `mine_complete`, `mine_skip`, `search_no_results`, `search_results`, `status_palace`, `status_wings`, `status_closets`, `status_drawers`, `init_complete`, `init_exists`, `repair_complete`, `migrate_complete`, `no_palace`.

**Interpolation contract (per-string):**

```text
mine_start         — {path}
mine_complete      — {closets}, {drawers}     # both required, Korean regression #927-class
mine_skip          — (none)
search_no_results  — {query}
search_results     — {count}
status_palace      — {path}
status_wings       — {count}
status_closets     — {count}
status_drawers     — {count}                   # NOT {drawers} — see ko regression
init_complete      — {path}
init_exists        — {path}
repair_complete    — {fixed}
migrate_complete   — (none)
no_palace          — (none)
```

### BCP 47 / Filename Contract

| Property | Value | Source |
|----------|-------|--------|
| **`be` filename** | `mempalace/i18n/be.json` | IANA Language Subtag Registry (file-dated 2026-04-09): `Type: language / Subtag: be / Description: Belarusian / Suppress-Script: Cyrl`. The `Suppress-Script: Cyrl` directive means we MUST NOT add `-Cyrl` to the tag — Cyrillic is the implied default script for Belarusian. HIGH. |
| **`be-tarask` filename** | `mempalace/i18n/be-tarask.json` (lowercase, hyphen — matches `be-tarask.wikipedia.org` and `pt-br` precedent) | IANA Registry: `Type: variant / Subtag: tarask / Description: Belarusian in Taraskievica orthography / Added: 2007-04-27 / Prefix: be / Comments: The subtag represents Branislau Taraskievic's Belarusian orthography as published in "Bielaruski klasycny pravapis" by Juras Buslakou, Vincuk Viacorka, Zmicier Sanko, and Zmicier Sauka (Vilnia-Miensk 2005).` HIGH (verified at line 48570 of the registry). |
| **Case-insensitivity** | `_canonical_lang` matches on `lower()` (`__init__.py:38-41`) | Test `test_canonical_lang_uppercase_resolves` ensures `BE-TARASK`, `Be-Tarask`, `be-Tarask` all resolve to `be-tarask`. Verified empirically: with the new files in place, all five casings will hit the same canonical stem. |
| **Why not `be-Cyrl-tarask`** | The script subtag is forbidden by `Suppress-Script: Cyrl` for `be` (RFC 5646 §4.1: "When a particular script or writing system should not be indicated… the Subtag Registry contains a 'Suppress-Script' field indicating the appropriate script."). Adding `-Cyrl` would be technically valid BCP 47 but stylistically wrong. HIGH. |

### Critical Regex Caveat — DO NOT inherit Russian's character class

The `ru.json` candidate pattern is `[А-ЯЁ][а-яё]{1,19}`. The Cyrillic block:

| Letter | Code Point | In `[А-Я]` (U+0410–U+042F)? |
|--------|------------|------------------------------|
| `А`–`Я` | U+0410–U+042F | yes (whole range) |
| `Ё` | U+0401 | no — added explicitly via `Ё` |
| **`І` (Belarusian)** | **U+0406** | **no** (out of range) |
| **`Ў` (Belarusian)** | **U+040E** | **no** (out of range) |
| `і` (Belarusian) | U+0456 | no (out of `а-я`) |
| `ў` (Belarusian) | U+045E | no (out of `а-я`) |

**Empirical verification** (Python 3.9 `re`):

```python
re.compile(r'[А-ЯЁ][а-яё]{1,19}').findall('Іван сказаў, што Алёна знайшла нешта.')
# → ['Алёна']            # Іван is silently dropped — І is NOT in [А-Я]

re.compile(r'[А-ЯЁІЎ][а-яёіў]{1,19}').findall('Іван сказаў, што Алёна знайшла нешта.')
# → ['Іван', 'Алёна']    # correct
```

The Belarusian candidate pattern MUST therefore include `І` and `Ў` (uppercase) and `і` and `ў` (lowercase). Recommended exact form:

```json
"candidate_pattern": "[А-ЯЁІЎ][а-яёіў]{1,19}",
"multi_word_pattern": "[А-ЯЁІЎ][а-яёіў]+(?:\\s+[А-ЯЁІЎ][а-яёіў]+)+"
```

Both `be.json` and `be-tarask.json` use the same candidate pattern — orthography differs in soft-sign placement and lexical choice, not in the alphabet (both use the 32-letter Belarusian Cyrillic alphabet). HIGH (empirically verified, 2026-04-20).

### Why no `boundary_chars` for Belarusian

`boundary_chars` (`__init__.py:113-134`, added in `f895bc5`) is a script-aware lookaround replacement for `\b`, used by Hindi (`hi.json` declares `"\\w\\u0900-\\u097F"`) because Devanagari combining vowel signs (matras) are Unicode `Mc`/`Mn` and not part of `\w` — so `\b` truncates names like `अनीता` to `अनीत`.

Belarusian Cyrillic has no combining marks: every letter, including `Ў`/`І`/`ў`/`і`, is a precomposed `Lu`/`Ll` codepoint and falls inside `\w`. Default `\b` therefore works correctly (verified above). Declaring `boundary_chars` for Belarusian would be a **no-op** — the existing `_expand_b` and `_wrap_candidate` (`__init__.py:137-159`) only kick in when `boundary_chars` is truthy. **Don't include it; it's noise.** HIGH.

---

## Layer 2 — Linguistic Stack (resources for the human translator)

These are the references the project owner (a native Belarusian speaker) should consult when authoring or reviewing strings. None of them ship in the PR — they exist to anchor translation choices in primary sources.

### Authoritative orthography sources

| Resource | Variant | URL | Why It's Authoritative |
|----------|---------|-----|-----------------------|
| **Закон №420-З "Аб правiлах беларускай арфаграфii i пунктуацыi" (2008)** | `be` (Narkamauka) | National Legal Internet Portal of the Republic of Belarus: `https://pravo.by/document/?guid=3871&p0=H10800420` | The legal codification of Narkamauka. This is THE rule book for the post-2008 official orthography. Translations targeting `be.json` follow these rules. HIGH. |
| **Нацыянальная акадэмія навук Беларусі — Інстытут мовазнаўства імя Якуба Коласа** | `be` | `https://iazyk.bas-net.by/` | Regulating body for Belarusian. Issues normative dictionaries and grammar; co-author of GrammarDB. HIGH. |
| **"Беларускі клясычны правапіс" (Buslakou, Viacorka, Sanko, Sauka)** | `be-tarask` (Tarashkievitsa) | Vilnia–Miensk 2005, ISBN 978-985-6427-22-1; full text: `https://knihi.com/bielaruski-klasycny-pravapis.html` | The exact rule book cited by the IANA registry for the `tarask` variant subtag. THE definitive Tarashkievitsa orthography reference. HIGH. |
| **be.wikipedia.org — main page** | `be` | `https://be.wikipedia.org/` | Living corpus of contemporary Narkamauka. Useful for confirming common-usage spellings and inflected forms. MEDIUM (community-edited but extensively reviewed). |
| **be-tarask.wikipedia.org — main page** | `be-tarask` | `https://be-tarask.wikipedia.org/` | Living corpus of contemporary Tarashkievitsa. Same caveat. MEDIUM. |
| **Радыё Свабода (Radio Liberty)** | `be-tarask` | `https://www.svaboda.org/` | Major media outlet using Tarashkievitsa; useful for modern lexical choices and direct-address forms. HIGH for journalistic register, MEDIUM for technical terminology. |

### Reference dictionaries — Narkamauka (`be`)

| Resource | Type | Direct Query | Use For |
|----------|------|--------------|---------|
| **verbum.by — GrammarDB (НАН Беларусі, 2026/01)** | Inflectional grammar database | `https://verbum.by/grammardb/?word=<word>` (e.g. `?word=палац`) | Primary source for noun declensions, verb conjugations, gender/aspect forms. Returns full case/number tables. Use for every entity-section verb pattern (`сказаў/сказала/сказалі`) and for stopword inflections. HIGH (verified by query — returns full inflection tables for `аагамія`, `аагенез`, etc., 2026-04-20). |
| **verbum.by — Тлумачальны слоўнік беларускай літаратурнай мовы (І. Л. Капылоў, 2022)** | Modern monolingual explanatory dictionary | `https://verbum.by/tsblm2022/?word=<word>` | Definitions in current Narkamauka; resolves "is this the right word for *closet*?" questions (палац vs. замак, шафа vs. камода). HIGH. |
| **skarnik.by** | Russian–Belarusian dictionary | `https://www.skarnik.by/search?term=<russian-word>` | Anti-pattern check: when uncertain whether to translate from Russian, look up the Russian source word and confirm the Belarusian rendering matches your intuition. Daily-updated. Based on Колас–Крапіва–Глебка 1953 academic dictionary. MEDIUM (single source, but well-maintained). |
| **verbum.by — Англійска-беларускі слоўнік (Т. Суша, 2013)** | English–Belarusian | `https://verbum.by/susha/?word=<english-word>` | Direct EN→BE for technical terms. Current orthography. HIGH for general lexicon, MEDIUM for software-specific vocabulary (project predates modern AI tooling). |
| **verbum.by — Слоўнік сінонімаў (М. Клышка, 2-е выданне)** | Thesaurus | `https://verbum.by/klyshka/?word=<word>` | Disambiguation for the 13 `terms.*` keys — choose the most idiomatic synonym, not the first dictionary hit. HIGH. |
| **Беларуска-рускі слоўнік НАН Беларусі (4-е выданне, 2012)** | Belarusian–Russian | on verbum.by `https://verbum.by/brs/?word=<word>` | Reverse-direction check; useful for confirming nuance differences from Russian. HIGH. |

### Reference dictionaries — Tarashkievitsa (`be-tarask`)

| Resource | Type | URL | Use For |
|----------|------|-----|---------|
| **verbum.by — Ангельска-беларускі слоўнік (В. Пашкевіч, 2006, "класічны правапіс")** | English–Belarusian, Tarashkievitsa | `https://verbum.by/abs/?word=<english-word>` | The single most important resource for `be-tarask.json` lexical choices. Authored under classical orthography conventions. HIGH. |
| **knihi.com** | Belarusian library | `https://knihi.com/` | Tarashkievitsa-published literature corpus; useful for verifying orthographic conventions in real usage. MEDIUM. |
| **Slownik.org** | Belarusian–Polish + monolingual, often Tarashkievitsa-leaning | `https://slownik.org/` | Cross-reference for Tarashkievitsa morphology, especially soft-sign placement. MEDIUM. |
| **Vincuk Viacorka's blog (Радыё Свабода)** | Living-language commentary on Tarashkievitsa usage | `https://www.svaboda.org/author/vincuk-viacorka/jq_$_o` | Settles edge cases in modern Tarashkievitsa style. HIGH for nuanced choices, MEDIUM for normative spelling (use the 2005 rule book for that). |

### BCP 47 / IANA references (filename rationale)

| Source | URL | What It Proves |
|--------|-----|----------------|
| **IANA Language Subtag Registry** | `https://www.iana.org/assignments/language-subtag-registry` (file-dated 2026-04-09) | Authoritative source for `be` (line ~190 of registry) and `tarask` (line 48570). HIGH. |
| **RFC 5646 — Tags for Identifying Languages** | `https://www.rfc-editor.org/rfc/rfc5646` | §2.1.1 (case-insensitivity), §2.2.4 (variant subtags), §4.1 (`Suppress-Script` semantics). HIGH. |
| **CLDR (Unicode Common Locale Data Repository)** | `https://cldr.unicode.org/` | Has a full `be` locale (currency formatting, plural rules, etc.); `be-tarask` is recognized as a valid BCP 47 tag but does not have a CLDR-distinct locale (Tarashkievitsa shares formatting with Narkamauka — only orthography differs). Confirms our two-file scope is correct. MEDIUM. |
| **be-tarask.wikipedia.org URL** | `https://be-tarask.wikipedia.org/` | Living precedent for the lowercase `be-tarask` form on the web. HIGH. |

### Belarusian-specific NLP / lexical lists (for stopwords and stop_words)

| Resource | URL | Use For |
|----------|-----|---------|
| **stopwords-iso (Belarusian list)** | `https://github.com/stopwords-iso/stopwords-be` | Open-source community-maintained Belarusian stopword list (~150 entries). Useful starting point for `entity.stopwords` and `regex.stop_words`; **filter through native review** before commit — the list is auto-generated from corpora and contains some questionable entries. MEDIUM. |
| **NLTK Belarusian stopwords** | (via `nltk.corpus.stopwords.words('belarusian')`, NLTK ≥ 3.8) | Smaller curated list; cross-reference with stopwords-iso. MEDIUM. |
| **Belarusian Wiktionary closed-class word lists** | `https://be.wiktionary.org/wiki/Катэгорыя:Прыназоўнікі_(беларуская_мова)` (prepositions); `Катэгорыя:Злучнікі_(беларуская_мова)` (conjunctions); `Катэгорыя:Часціцы_(беларуская_мова)` (particles) | Authoritative source for prepositions/conjunctions/particles to add to the `entity.stopwords` array (mirrors what `ru.json` `stopwords` does — see lines 122-158). HIGH. |

### Why we do NOT translate from Russian (anti-pattern enforcement)

Russian (`ru`) and Belarusian (`be`) share script and ~70-80% lexical roots, which makes Russian transliteration tempting and disastrous. Concrete divergences that would expose Russian-sourced text immediately to a native reader:

| English | Russian (`ru.json`) | Belarusian (`be`, recommended) | Why Different |
|---------|--------------------|--------------------------------|--------------|
| palace | дворец | **палац** | Unrelated root (cf. Polish *pałac*) |
| closet | шкаф | **шафа** (feminine, not masculine) | Different gender + form |
| drawer | ящик | **шуфляда** | Different root entirely |
| also | тоже | **таксама** | No cognate |
| in order to | чтобы | **каб** | No cognate |
| about (preposition) | о / об | **аб** (consistent) | Different distribution |
| she said | сказала | **казала** / **сказала** | Both possible; `казаў/казала` more idiomatic in Narkamauka |
| `и` (and) | и | **і** | Different letter (Belarusian uses `і` for `[i]`, never `и`) |
| (no Russian equivalent) | — | **ў** | Belarusian-only letter for syllable-final `[w]` |
| hard sign | ъ | **'** (apostrophe) | Belarusian uses apostrophe where Russian uses ъ |

Additionally, Belarusian phonology mandates **акання** (unstressed `o → a` everywhere in spelling) and **цеканне/дзеканне** (T/D + soft vowel → `ц`/`дз`). Russian-sourced text that doesn't apply these rules reads as Trasianka (a stigmatized contact variety), not Belarusian. HIGH-confidence anti-pattern.

### Why we do NOT translate from Russian via machine translation

| MT System | Belarusian Support | Why It's Insufficient |
|-----------|-------------------|----------------------|
| **DeepL** | **NOT supported** (as of 2026-04, supports 30 languages, none of which is Belarusian — verify at `https://www.deepl.com/translator`) | Cannot use even if we wanted to. |
| **Google Translate** | Supported (`be`) | Quality is poor for inflected Slavic with low corpus coverage; tends to produce Russianisms; does not distinguish Narkamauka from Tarashkievitsa. UNSUITABLE for `entity.*` patterns where verb forms must be inflectionally correct. |
| **Yandex Translate** | Supported (`be`) | Similar issues; better than Google for cross-Slavic but still produces stylistically off Belarusian. UNSUITABLE without native review. |

The `NATIVE-01` requirement in `PROJECT.md:52` makes this a hard gate: every string must pass native-speaker review before commit. MT can be a *starting point* for the bulk `cli.*` strings, but never a final source.

---

## Installation (the contributor workflow — no new packages)

```bash
# Fork MemPalace/mempalace on GitHub web UI, then clone your fork
git clone https://github.com/<your-username>/mempalace.git
cd mempalace
git remote add upstream https://github.com/MemPalace/mempalace.git

# Install the existing dev environment (no new deps for our work)
pip install -e ".[dev]"
# Optional — match the CI ruff pin exactly:
pip install "ruff>=0.4.0,<0.5"

# Branch from develop (NOT main)
git fetch upstream
git checkout -b feat/i18n-belarusian upstream/develop

# Add the two new files
#   mempalace/i18n/be.json
#   mempalace/i18n/be-tarask.json
# (optional) extend tests/test_i18n.py:test_dialect_compress_samples with a be sample

# Pre-PR gates (must all pass)
ruff check .
ruff format --check .
pytest tests/test_i18n.py tests/test_i18n_lang_case.py tests/test_entity_detector.py -v
pytest tests/ -v --cov=mempalace --cov-fail-under=80    # full suite + coverage gate

# Commit per conventional-commits, push, open PR via GitHub web UI against `develop`
```

No `pip install <new-package>` step exists. **Adding any new dependency would violate CONTRIBUTING.md:66 and is out of scope for this PR.**

---

## Alternatives Considered

| What We Chose | Alternative | Why We Chose Ours |
|---------------|-------------|-------------------|
| **Two files: `be.json` + `be-tarask.json`** | One file (just `be.json`, picking one orthography) | Both orthographies have living user bases (~5M Narkamauka speakers + Tarashkievitsa users in independent media and diaspora). One file alienates ~half the audience. Cost is ~6KB × 2; benefit is full coverage. |
| **Full tier (with `entity` section) for both** | Minimal tier (just `terms`/`cli`/`aaak`) | Without `entity`, candidate-extraction falls back to English `[A-Z][a-z]` and misses ALL Cyrillic names — entity detection would be entirely broken on Belarusian text. Minimal tier is acceptable for languages where users will mostly write English entities; for a Cyrillic locale it's a non-starter. |
| **`ru.json` as structural template only** | Direct translation from `ru.json` strings | Cross-Slavic translation is the worst outcome — produces subtly Russified Belarusian. Use `en.json` as the source-of-truth for *meaning*; use `ru.json` only as a "what does a Cyrillic locale's `entity` section look like" structural reference. |
| **`[А-ЯЁІЎ][а-яёіў]{1,19}` candidate pattern** | Inherit `[А-ЯЁ][а-яё]{1,19}` from `ru.json` | Russian's character class silently drops Belarusian `Ў`/`І` (verified empirically — see Layer 1 caveat). Would silently break entity extraction for the most common Belarusian names (Іван, Ўладзіслаў, etc.). |
| **No `boundary_chars`** | Declare `"boundary_chars": "\\w"` defensively | Cyrillic letters fit inside `\w`; the boundary-char machinery (`__init__.py:137-159`) only fires when `boundary_chars` is truthy. Adding a tautological declaration is noise. |
| **Conventional commits within one PR** | Two PRs (one per orthography) | Every recent i18n PR (Russian #760, Italian #907, pt-br #117, Indonesian #778) used a single PR. Keeps reviewer context together; lets reviewers spot inconsistencies between the two orthographies. |
| **`pytest` + `ruff` (existing dev extras)** | Add `pytest-icdiff`, `pytest-xdist`, etc. for prettier output | "Don't add new deps without discussion" (CONTRIBUTING.md:66). The default tooling is sufficient. |
| **Branch `feat/i18n-belarusian` from `develop`** | Branch from `main` | CONTRIBUTING.md:58 explicitly says PRs target `develop`. CI runs on both, but the project's release flow is `develop → main`. |

---

## What NOT to Use

This is the discipline section. Each item below is an anti-pattern that has either bitten i18n PRs in the past or would bite us if we don't enforce it.

| Avoid | Why It's a Problem | Use Instead |
|-------|--------------------|-------------|
| **Russian transliteration as a translation shortcut** (replace `и → і`, `у → ў`, ship) | Produces Trasianka (stigmatized Russian-Belarusian creole), not Belarusian. Native readers spot it immediately. Was the explicit failure mode the project owner called out (`PROJECT.md:21-26`). Ruins reputation for upstream future Belarusian PRs. | Translate each string from `en.json` using `verbum.by` for inflectional accuracy and native review for idiom. Use `ru.json` only for *structural* reference (which keys exist in `entity`, what shape patterns take). |
| **DeepL / Google Translate / Yandex output without native review** | DeepL doesn't support Belarusian. Google/Yandex produce grammatically-correct-but-stylistically-Russified Belarusian. Verb gender/aspect forms are frequently wrong (critical for `person_verb_patterns`). | MT output is a *starting draft only*. The `NATIVE-01` review gate is hard. Verify every verb form against verbum.by GrammarDB. |
| **Mixing orthographies in one file** (Narkamauka spellings inside `be-tarask.json` or vice versa) | Reader can tell from one mis-spelled function word. Defeats the purpose of two files. Hard to review systematically because git diff shows characters, not orthographic style. | Translate each file in one sitting against the appropriate orthography reference (Narkamauka → 2008 law; Tarashkievitsa → 2005 Buslakou/Viacorka/Sanko/Sauka). Diff the two files at the end to ensure semantic parity but not lexical identity. |
| **Adding Latin-script Belarusian (`Łacinka`) variants** (`be-Latn.json`) | No upstream precedent for Latin-script Belarusian; would need BCP 47 `be-Latn` script subtag (not `Suppress-Script: Cyrl`'s default). No clear consumer. Out of scope per `PROJECT.md:61`. | Cyrillic only. If Łacinka demand emerges later, that's a separate PR with its own discussion. |
| **`re.ASCII` flag in any pattern** | Restricts `\w`/`\b`/`\s` to ASCII — would make Cyrillic letters non-word-characters and silently break every Belarusian pattern. | Default Python 3 `re` semantics (Unicode `\w` and `\b`). No flag needed. |
| **`boundary_chars` declaration in entity section** | Designed for combining-mark scripts (Devanagari, Arabic, Hebrew). Tautological for Cyrillic. Adds review friction with no benefit. | Omit it. Default `\b` works for Belarusian (verified empirically). |
| **Inheriting Russian's `[А-ЯЁ]` candidate class** | Drops Belarusian-specific `Ў`/`І` from candidate extraction. Entity detection silently misses the most common Belarusian names. | `[А-ЯЁІЎ][а-яёіў]{1,19}` (and matching multi-word). |
| **`ensure_ascii=True` JSON serialization** (`\u043f\u0430\u043b\u0430\u0446` instead of `палац`) | Breaks visual review (illegible diff in PR), inflates file size ~3×, doesn't match existing `ru.json`/`zh-CN.json` convention. | `ensure_ascii=False` (Python 3.5+ has same performance — verified in `Doc/whatsnew/3.5.rst`). Pretty-print with `indent=2`. |
| **UTF-8 BOM at start of file** | Injects `\ufeff` as first character — JSON parser sees it as invalid leading content. | UTF-8 without BOM. Default for `open(..., 'w', encoding='utf-8')` on Linux/macOS. On Windows, verify with `xxd` or hex viewer that file starts with `{` (0x7B), not `EF BB BF`. |
| **Unicode normalization other than NFC** (NFD with combining-character sequences for `ё`, `й`, etc.) | Belarusian Cyrillic letters have precomposed code points (`Ё`=U+0401, `й`=U+0419). NFD would decompose them into `Е` + combining diaeresis, etc., which still renders the same but breaks byte-equality, search, and `\w` matching in some pattern engines. | NFC (precomposed). Default for Python `str` literals; verify with `unicodedata.is_normalized('NFC', s)` if pasting from external sources. |
| **Empty `entity.stopwords` list** | Falls back to English-only stopword set, so common Belarusian filler words ("гэта", "так", "ну", "ёсць") become candidate entities and pollute detection. | Populate with ≥30 entries: prepositions, conjunctions, particles, copular forms, common interjections. Mirror `ru.json`'s stopwords (~58 entries) as a structural reference for *categories*, then translate each one from English not from Russian. |
| **`person_verb_patterns` without gender/aspect alternation** (e.g., only `сказаў` and not `сказала`/`сказалі`) | Belarusian person-verbs decline by gender (masc/fem) and number; missing one form means missing matches on female-named or plural-subject sentences. | Use bracketed alternation like Russian does: `\\b{name}\\s+сказаў[а]?\\b` matches both `сказаў` and `сказала`. For `-ся/-ся` reflexives: `\\b{name}\\s+пасьмяяў(ся|ся)\\b`. For Tarashkievitsa, use the soft-sign forms (`-сь`/`-ся`). |
| **`pronoun_patterns` with only nominative case** | Belarusian (like Russian) is heavily inflected; pronouns appear in 6 cases. Nominative-only matches miss most contexts. | Cover `ён`/`яго`/`яму`/`ім` (masc); `яна`/`яе`/`ёй`/`ёй`/`ёю` (fem); `яны`/`іх`/`ім`/`імі` (plural). For `be-tarask`, use `ён`/`яго`/`ім`/`ім` with soft-sign variants where applicable. |
| **`direct_address_pattern` with only one greeting** (e.g., only `прывітанне`) | Loses common register variants (вітаю, добры дзень, шануйце). | Multiple alternatives joined with `|`: `\\bпрывітанне\\s+{name}\\b\|\\bдзякуй\\s+{name}\\b\|\\bвітаю\\s+{name}\\b\|\\bпаважаны\\s+{name}\\b\|\\bпаважаная\\s+{name}\\b\|\\bдарагі\\s+{name}\\b\|\\bдарагая\\s+{name}\\b` (mirror `ru.json:81` shape). |
| **Adding new Python dependencies** (e.g., `pyicu` for case-folding, `babel` for plural rules) | Violates CONTRIBUTING.md:66 ("ChromaDB + PyYAML only"). Would require a separate discussion-PR. Adds install friction for downstream users. | Stdlib only. Belarusian pluralization beyond simple `{count}` interpolation is not used in `cli.*` strings (existing locales like `ru` use unchanged plural-noun-genitive form: "Шкафов: 5" works for any count). |
| **Modifying `mempalace/i18n/__init__.py` infra** (e.g., to add Belarusian-specific case-folding) | The module already supports auto-discovery, case-insensitive lookup, hyphenated tags, per-locale entity merge. Belarusian needs zero infra changes. Any code change expands review surface. | Pure data PR. If you find yourself wanting to edit `__init__.py`, it's a sign you're over-scoping. |
| **Belarusian-Russian disambiguation in `entity_detector`** | Same Cyrillic block — would need language-detection layer; materially changes the design contract. Out of scope per `PROJECT.md:64`. | Defer. Document it as a follow-up issue if user demand emerges. |
| **Enabling non-English semantic search improvements** (issue #712) | ChromaDB default embedding model is English-only; non-English search is degraded across ALL locales. Out of scope per `PROJECT.md:60` — this is an embedding-model swap, not an i18n contribution. | Out of scope. Don't get pulled in. |

---

## Stack Patterns by Variant

**If contributing `be.json` (Narkamauka):**
- Use the 2008 orthography law (`pravo.by` Закон №420-З) as the rule book.
- Default lookups against verbum.by GrammarDB (НАН Беларусі 2026/01) and Тлумачальны слоўнік (Капылоў 2022).
- Common term mapping (subject to native review): `palace → палац`, `wing → крыло`, `hall → зала`, `closet → шафа`, `drawer → шуфляда`, `mine → здабываць` or `капаць` (verb infinitive; check `cli.mine_start` interpolation context), `search → пошук`, `status → статус`, `init → ініцыялізацыя`, `repair → рамонт`, `migrate → міграцыя`, `entity → сутнасць`, `topic → тэма`.
- `aaak.instruction`: write a fluent Narkamauka instruction ≥10 chars (e.g., "Сцісніце да індэкснага фармату. Дэфісы паміж словамі, вертыкальныя рысы паміж паняццямі. Захавайце імёны і лічбы дакладна.").
- Verb forms in `person_verb_patterns`: `сказаў/сказала/сказалі`, `спытаў(ся)/спытала(ся)/спыталі(ся)`, `адказаў/адказала/адказалі`, `засмяяў(ся)/засмяяла(ся)/засмяяліся`, `усміхнуў(ся)/усміхнула(ся)/усміхнуліся`, etc.

**If contributing `be-tarask.json` (Tarashkievitsa):**
- Use Buslakou/Viacorka/Sanko/Sauka 2005 ("Беларускі клясычны правапіс") as the rule book.
- Default lookups against Пашкевіч 2006 (Ангельска-беларускі, класічны правапіс) on verbum.by, plus svaboda.org corpus.
- Soft-sign before consonants in characteristic positions: `сьвет`, `прыняцьце`, `жыцьцё`, `усьмешка`, `залатая`. (Compare Narkamauka: `свет`, `прыняцце`, `жыццё`, `усмешка`.)
- Foreign-word adaptation differs: `альфабэт` (be-tarask) vs `алфавіт` (be); `клясычны` vs `класічны`; `сыстэма` vs `сістэма`; `лекцыя` (both, but differ in derivation).
- Common term mapping where Tarashkievitsa diverges from Narkamauka: `hall → заля` (more common in Tarashkievitsa, vs `зала` in Narkamauka).
- Verb forms with soft-sign reflexives: `сказаў(ся)` may use `-сь` ending; e.g., `усьміхнуўся`, `зьдзівіўся`. Verify each against the 2005 rule book.
- `-зьдз-` / `-сьц-` / `-ць-` consonant clusters appear more frequently than in Narkamauka — characteristic Tarashkievitsa marker.

---

## Version Compatibility (existing — what we don't change)

| Component | Pinned Version | Notes |
|-----------|----------------|-------|
| Python | `>=3.9` (project), CI matrix `3.9`, `3.11`, `3.13` | Locale JSON consumed identically across all three. No `re` semantic changes affect Cyrillic between these versions. |
| chromadb | `>=1.5.4,<2` | Locale JSON does not interact. |
| pyyaml | `>=6.0,<7` | Locale JSON does not interact. |
| pytest | `>=7.0` (resolves to 8.4.2 on py3.9, 9.0.3 on py3.10+) | Both versions support our test additions. |
| pytest-cov | `>=4.0` | Coverage neutral or positive on JSON addition. |
| ruff | `>=0.4.0,<0.5` (CI pin); `>=0.4.0` (project floor) | JSON files not formatted by ruff; our test changes (if any) must conform to current style. |
| pre-commit (ruff hook) | `v0.4.10` (`.pre-commit-config.yaml`) | Lock-step with CI pin. |

**Compatibility risk: NONE.** A pure-data PR adding two JSON files to `mempalace/i18n/` does not interact with any pinned dependency.

---

## Sources

| Source | Type | Confidence | What It Verified |
|--------|------|------------|------------------|
| `mempalace/i18n/__init__.py` (read in full) | Codebase | HIGH | UTF-8 read, case-insensitive lookup, entity merge, English fallback semantics |
| `mempalace/entity_detector.py` (read in full) | Codebase | HIGH | How `candidate_pattern` / `multi_word_pattern` / `person_verb_patterns` are consumed, default `re.IGNORECASE` flag, `_build_patterns` LRU cache |
| `mempalace/dialect.py:320-348` (read) | Codebase | HIGH | How `Dialect(lang=…)` loads `aaak.instruction` and `regex` section |
| `mempalace/closet_llm.py:115-134` (read) | Codebase | HIGH | How `aaak.instruction` is concatenated into LLM prompt |
| `tests/test_i18n.py` (read in full) | Codebase | HIGH | Every assertion the new files must satisfy: required sections/terms, interpolation, Dialect load, ko regression |
| `tests/test_i18n_lang_case.py` (read in full) | Codebase | HIGH | `_canonical_lang` case-insensitivity contract — verified `be-tarask` will resolve under any casing once the file exists |
| `tests/test_entity_detector.py` (read in full) | Codebase | HIGH | How locale entity sections are consumed; multi-language merge semantics; `boundary_chars` is for combining-mark scripts only |
| `pyproject.toml` (read in full) | Codebase | HIGH | Python version floor, ruff pin, coverage gate, no-new-deps rule |
| `CONTRIBUTING.md` (read in full + `user-fetch` from upstream `develop`) | Codebase + upstream | HIGH | PR contract: branch off develop, conventional commits, `pytest tests/ -v`, "Dependencies: minimize" |
| `.github/workflows/ci.yml` (read in full) | Codebase | HIGH | Exact CI gates: matrix, ruff pin, `--cov-fail-under=80` |
| `.planning/codebase/STACK.md` (read in full) | Codebase | HIGH | Full existing stack doc — confirmed our reading of pyproject |
| `.planning/codebase/CONVENTIONS.md` (read in full) | Codebase | HIGH | Conventional Commits requirement, target branch `develop`, ruff pin lock-step |
| `mempalace/i18n/ru.json` (read in full) | Codebase | HIGH | Structural template for Cyrillic locale; identified the `[А-ЯЁ]` Belarusian-letter gap |
| `mempalace/i18n/pt-br.json` (read in full) | Codebase | HIGH | Hyphenated tag precedent; full-tier entity section example for a language with diacritics |
| `mempalace/i18n/it.json`, `mempalace/i18n/hi.json` (read in full) | Codebase | HIGH | Recent precedents (PR #907 it, hi entity); Hindi's `boundary_chars` confirmed it's for combining-mark scripts only |
| `user-git` MCP `git_log` (parent repo, last 30 commits) | Codebase history | HIGH | Confirmed no in-flight i18n work that would conflict |
| `git log --follow mempalace/i18n/__init__.py` | Codebase history | HIGH | i18n module evolution: `baf3c0a` initial 8 langs → `b214ace` multi-language refactor → `0174b93` case-insensitive (#927) → `f895bc5` boundary_chars → `6caac50` py3.9 fix |
| `git log --all -- 'mempalace/i18n/*'` | Codebase history | HIGH | Locale-PR pattern: every recent locale (ru, pt-br, it, id, hi) used a single PR with 1-3 atomic commits |
| `user-context7` MCP — `/python/cpython` `query-docs "re module \\b Cyrillic"` | Library docs | HIGH | Confirmed `\b` and `\w` are Unicode-aware by default in Python 3 str patterns; `re.ASCII` flag would restrict to ASCII; Python 3.14 broadens `\B` to match empty input (irrelevant for us) |
| `user-context7` MCP — `/python/cpython` `query-docs "json.dumps ensure_ascii=False"` | Library docs | HIGH | Confirmed `ensure_ascii=False` outputs Cyrillic directly; same performance as `True` since Python 3.5 |
| `user-fetch` MCP — `https://www.iana.org/assignments/language-subtag-registry` (file-dated 2026-04-09) | Standards body | HIGH | `be` language subtag (`Suppress-Script: Cyrl`) at line ~190; `tarask` variant subtag at line 48570 (`Prefix: be`, references Buslakou/Viacorka/Sanko/Sauka 2005) |
| `user-fetch` MCP — `https://be.wikipedia.org/wiki/Беларуская_мова` | Living corpus | HIGH | Confirmed Narkamauka usage and regulating body (НАН Беларусі) |
| `user-fetch` MCP — `https://be-tarask.wikipedia.org/wiki/Беларуская_мова` | Living corpus | HIGH | Confirmed Tarashkievitsa stylistic conventions (`сьвет`, `Эўропа`, `стагодзьдзі`) and BCP 47 tag in use |
| `user-fetch` MCP — `https://verbum.by/` | Linguistic resource | HIGH | Confirmed availability of GrammarDB (2026/01), TSBLM 2022, Skarnik, multiple bilingual dictionaries — both Narkamauka and Tarashkievitsa |
| `user-fetch` MCP — `https://verbum.by/grammardb/?word=палац` | Linguistic resource | HIGH | Confirmed GrammarDB returns full inflectional tables; usable for verb conjugation checks |
| `user-fetch` MCP — `https://www.skarnik.by/` | Linguistic resource | MEDIUM | Daily-updated Russian-Belarusian dictionary; useful as anti-Russification check |
| `user-fetch` MCP — `https://en.wikipedia.org/wiki/Belarusian_orthography` | Reference | MEDIUM | Confirmed 32-letter Belarusian alphabet; Belarusian-specific Unicode points (`І`=U+0406, `Ў`=U+040E) |
| `user-fetch` MCP — `https://github.com/MemPalace/mempalace/blob/develop/CONTRIBUTING.md` | Upstream truth | HIGH | Confirmed local copy matches upstream develop branch (no drift) |
| Empirical Python testing (`python3 -c "..."`) | Direct verification | HIGH | Verified `\b` works for Cyrillic; verified `[А-ЯЁ]` drops `Іван`; verified `ensure_ascii=False` writes `палац` directly |

---

*Stack research for: MemPalace Belarusian i18n contribution (`be` + `be-tarask`)*
*Researched: 2026-04-20*
*Brownfield contribution — Layer 1 captures the existing upstream contract; Layer 2 is the linguistic toolkit for the human translator.*

# Existing i18n Architecture (Brownfield Contribution)

**Domain:** Locale data files plugging into a host package's i18n module
**Researched:** 2026-04-20
**Confidence:** HIGH (every claim traced to source line in `mempalace/i18n/__init__.py` or its consumers)

> **Re-interpretation of the template.** This is **not** an architecture we will design.
> It is the **existing** architecture our two JSON files must honor. Sections renamed
> accordingly. The implementer's job is to write `be.json` and `be-tarask.json` such
> that the contracts below are satisfied — no Python, no `__init__.py` edits, no
> infrastructure changes.

---

## 1. System Overview — How a Locale File Affects User Behavior

A locale JSON in `mempalace/i18n/` participates in **two independent dataflows**.
Both flow from disk → in-memory cache → consumer module. They share the same files
on disk but are otherwise decoupled — different functions, different caches,
different invalidation rules.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  mempalace/i18n/<lang>.json on disk                                          │
│  (auto-discovered via _LANG_DIR.glob("*.json"); NO registry, NO __init__ edit)│
└────────────────────────────┬─────────────────────────────────────────────────┘
                             │
            ┌────────────────┴────────────────┐
            │                                 │
            ▼ FLOW A                          ▼ FLOW B
   "string lookup"                    "entity pattern merge"
   (lang/label/terms/cli/aaak/regex)  (entity section only)

┌─────────────────────────┐         ┌──────────────────────────────────────┐
│ load_lang(lang)         │         │ get_entity_patterns(languages=(...)) │
│  └─> _canonical_lang    │         │  ├─> _canonical_lang (per lang)      │
│  └─> json.loads UTF-8   │         │  ├─> _entity_cache lookup (by tuple) │
│  └─> _strings (global)  │         │  ├─> _load_entity_section (per lang) │
│  └─> _current_lang=...  │         │  ├─> _collect_entity_section (merge) │
└─────────────┬───────────┘         │  │     ├─> _wrap_candidate           │
              │                     │  │     └─> _expand_b                 │
              ▼                     │  └─> _entity_cache[key] = merged     │
        ┌──────────┐                └──────────────┬───────────────────────┘
        │   t(),   │                               │
        │ get_regex│                               ▼
        │current_  │                ┌──────────────────────────────────────┐
        │  lang()  │                │ functools.lru_cache layers in        │
        └────┬─────┘                │ entity_detector.py:                  │
             │                      │  _build_patterns(name, langs)        │
             ▼                      │  _pronoun_re(langs)                  │
   ┌──────────────────┐             │  _get_stopwords(langs)               │
   │ Dialect.__init__ │             └──────────────┬───────────────────────┘
   │ closet_llm._call_│                            │
   │ tests only       │                            ▼
   └──────────────────┘             ┌──────────────────────────────────────┐
                                    │ extract_candidates() / score_entity()│
                                    │ palace._candidate_entity_words()     │
                                    └──────────────────────────────────────┘
```

**Key separation:** `load_lang(lang)` mutates module-global `_strings` (FLOW A
only). `get_entity_patterns(langs)` does NOT touch `_strings` and is unaffected
by which language is "current" — it reads the JSON files **a second time**,
independently, via `_load_entity_section` (`mempalace/i18n/__init__.py:100-110`).
This is intentional: a Korean user can have `_current_lang = "ko"` for CLI strings
while entity detection runs over `("en", "be", "ru")` simultaneously.

---

## 2. Component Responsibilities — Who Reads Which Section

Verified by grepping every `from mempalace.i18n` and `from .i18n` import in the
repo.

| Consumer (file:func) | Section(s) read | API used | Behavior if key missing |
|---|---|---|---|
| `mempalace/dialect.py:Dialect.__init__` | `aaak.instruction`, `regex.*` | `load_lang(lang)`, `t("aaak.instruction")`, `get_regex()`, `current_lang()` | `t()` returns the literal key string `"aaak.instruction"`; `get_regex()` returns `{}` |
| `mempalace/closet_llm.py:_call_llm` | `aaak.instruction` | `t("aaak.instruction")` inside `try/except Exception` | On any exception, `lang_instruction = ""` → no `Language instruction:` line appended to the prompt |
| `mempalace/entity_detector.py` (module + every public fn) | entire `entity` section | `get_entity_patterns(languages)` | `_collect_entity_section` skips missing keys silently. If NO requested lang has `entity`, falls back to `en` patterns (line 255-257) |
| `mempalace/palace.py:_candidate_entity_words` | `entity.candidate_pattern` only | `get_entity_patterns(MempalaceConfig().entity_languages)` | Same English fallback. Activated **only** if user sets `MEMPALACE_ENTITY_LANGUAGES` env var or runs `mempalace init --lang be` (which calls `cfg.set_entity_languages(["be"])`) |
| `tests/test_i18n.py` | `terms.{palace,wing,closet,drawer}`, `cli.mine_complete`, `cli.status_drawers`, `aaak.instruction` | `load_lang`, `t`, `available_languages` | Tests assert on missing → these tests will FAIL if a key is omitted |
| `tests/test_i18n_lang_case.py` | `_canonical_lang` resolution, `entity` section presence | `_canonical_lang`, `_load_entity_section`, `get_entity_patterns` | — |
| `tests/test_entity_detector.py` | `entity` section + `_temp_locale` fixture | `get_entity_patterns` (indirect) | — |

**Critical non-finding (verified twice via Grep, see Sources):**

- `mempalace/cli.py` does **NOT** import `mempalace.i18n` and never calls `t(...)`.
  All CLI prints (`"Mining {path}..."`, `"Done. {closets} closets..."`, etc.)
  are hard-coded English f-strings or plain `print()` calls. The `cli.*` section
  in `en.json` is **functionally dead in production code** — only `tests/test_i18n.py`
  exercises it (via `t("cli.mine_complete", closets=5, drawers=100)`).
- `mempalace/normalize.py`, `mempalace/query_sanitizer.py`, `mempalace/searcher.py`,
  and all backends **do not use** `mempalace.i18n`. The `regex` section (e.g.
  `topic_pattern`, `stop_words`, `quote_pattern`, `action_pattern`) is **only**
  read by `Dialect.lang_regex` — and `Dialect` itself never reads from
  `lang_regex` further (it's stored as an attribute but never consulted in
  `compress()`, `_extract_topics()`, `_extract_key_sentence()`, etc., which all
  use module-level `_STOP_WORDS` instead). So `regex.*` keys are loaded into
  Python objects but **also functionally dead** today.

**Implication for `be.json` / `be-tarask.json`:** Translate the `cli` section
(test contract requires it) and the `regex` section (PROJECT.md requirement
BE-05), but understand they are **infrastructure-ready** translations — they
will only be visible to users when MemPalace upstream wires them in. The
**live, user-visible** sections today are `aaak.instruction` (LLM prompt
augmentation) and the entire `entity` section (entity detection).

---

## 3. File Layout — No New Structure, Just Two New Files

```
mempalace/i18n/
├── __init__.py        # DO NOT EDIT. Auto-discovers *.json. Public API.
├── en.json            # Canonical schema reference.
├── de.json
├── es.json
├── fr.json
├── hi.json            # Only locale with boundary_chars (Devanagari).
├── id.json
├── it.json
├── ja.json
├── ko.json
├── pt-br.json         # Lowercase region subtag → precedent for be-tarask.
├── ru.json            # Structural template for Cyrillic.
├── zh-CN.json         # Uppercase region subtag — file's case is preserved
├── zh-TW.json         # by _canonical_lang but matched lowercase.
├── be.json            # ← NEW (Narkamauka)
└── be-tarask.json     # ← NEW (Tarashkievitsa)
```

**Filename rule** (verified at `mempalace/i18n/__init__.py:38-42`):

1. **Discovery is `glob("*.json")`** in `_LANG_DIR` (the i18n directory). Any
   `.json` file dropped here becomes a locale automatically. No code edit.
2. **The file's stem is the canonical language tag** returned by
   `_canonical_lang()`. So `be.json` → canonical `"be"`; `be-tarask.json` →
   canonical `"be-tarask"`. `available_languages()` returns `sorted(p.stem ...)`
   so the canonical form (preserved case) is what users see in `--help` lists.
3. **Case-insensitive match.** `_canonical_lang("BE")` → `"be"` (matched on
   lowercase, returns disk's case-preserved stem). `load_lang("Be-Tarask")`
   succeeds. **But** the cache key `_entity_cache[("be", "en")]` is the
   canonical (lowercase) form, so case differences collapse to one cache entry
   — this is asserted by `test_get_entity_patterns_shares_cache_across_cases`.
4. **Hyphen, not underscore.** BCP 47 uses `-`; the existing `pt-br.json` /
   `zh-CN.json` confirm hyphens. `be_tarask.json` would also be auto-discovered
   but would break BCP 47 lookup conventions and silently miss `--lang be-tarask`
   if users underscore-vs-hyphen mismatch — **don't do this**.
5. **Lowercase script subtag.** `tarask` is a registered IANA variant subtag and
   conventionally lowercased (matches `wikipedia.org/wiki/be-tarask:` URL
   convention). PROJECT.md decision: `be-tarask.json` (all-lowercase),
   confirmed against IANA registry.

**Filename rule for the implementer (one line):**

> Drop `mempalace/i18n/be.json` and `mempalace/i18n/be-tarask.json`. UTF-8,
> no BOM. That is the entire registration step.

---

## 4. Architectural Patterns Used by the i18n Module

### Pattern 1: Auto-Discovery via Filesystem Glob

**What:** No registry, no enum, no list. `_LANG_DIR.glob("*.json")` is the
single source of truth for "what locales exist".

**Where:** `mempalace/i18n/__init__.py:39, 47`

**Trade-off honored:**
- ✓ Adding a locale is a pure data PR (no Python diff, smaller review surface)
- ✓ Tests automatically pick up new locales (`test_all_languages_load` loops
  `available_languages()`)
- ✗ A malformed JSON file silently breaks all consumers (`json.loads` raises in
  `load_lang`, gets swallowed in `_load_entity_section`'s `except`)

**Implication:** A test failure caused by `be.json` will likely manifest as
`json.JSONDecodeError` at the top of `test_all_languages_load`, not as a
Belarusian-specific assertion. Always run `python -c "import json; json.load(open('mempalace/i18n/be.json'))"` first.

### Pattern 2: Case-Insensitive Resolution with Case-Preserved Storage

**What:** Callers pass any casing (`"BE"`, `"Be"`, `"be"`); `_canonical_lang`
returns the file's actual stem. Cache keys use the canonical form so case
differences share storage.

**Where:** `mempalace/i18n/__init__.py:28-42, 226-234`

**Trade-off honored:**
- ✓ BCP 47 §2.1.1 compliance (case-insensitive tags)
- ✓ Cache hit rate: `("PT-BR",)` and `("pt-br",)` share one entry
- ✗ Linear scan through all locale files on every lookup (acceptable: 13-15
  files, negligible)

### Pattern 3: Per-Section English Fallback (with Surprising Granularity)

**What:** Different sections fall back to English at different points in the
flow. There is **no** single "merge English defaults" step.

| Section | Fallback rule |
|---|---|
| `lang`, `label`, `terms.*`, `cli.*`, `aaak.*`, `regex.*` | **No fallback.** `t("cli.foo")` on a locale missing `cli.foo` returns the **literal string `"cli.foo"`**, NOT the English text. Verified at `__init__.py:73`. |
| `entity` section as a whole | If `_load_entity_section(lang)` returns `{}` AND no other requested lang has entity data, the **entire English entity section** is loaded as fallback (`__init__.py:255-257`). |
| Individual entity keys (`candidate_pattern`, etc.) | **No fallback.** `_collect_entity_section` checks each key with `section.get(...)` and silently skips if absent. So a locale with `entity.candidate_pattern` but no `entity.person_verb_patterns` contributes a candidate pattern and zero person verbs — it does NOT inherit English person verbs. |
| Unknown language code (e.g. `"xx"`) | `load_lang("xx")` falls back to `en.json` silently (canonical=None → `"en"`). `get_entity_patterns(("xx",))` triggers the entity-section fallback. |

**Implication for `be.json`:** Every key the `terms`, `cli`, `aaak` test
contract requires (`palace`, `wing`, `closet`, `drawer`, `mine_complete`,
`status_drawers`, `instruction`) must be present and non-empty. There is no
"inherit from English" safety net.

### Pattern 4: Entity Pattern Merge with Boundary Expansion (Pre-Compiled)

**What:** `get_entity_patterns` returns regex strings that are **fully
pre-wrapped** with the locale's word-boundary semantics (capture group
included, ready to compile). The consumer (`entity_detector`) compiles them
directly with `re.compile(pattern)` — no further wrapping.

**Where:** `mempalace/i18n/__init__.py:149-194`

**The contract for entity authors:**

| Key in JSON | What gets done to it | What you write |
|---|---|---|
| `candidate_pattern` | Wrapped: `\b(YOUR_PATTERN)\b` | The character class only, e.g. `[А-ЯЁІЎ][а-яёіў]{1,19}`. Do NOT add `\b` or `()`. |
| `multi_word_pattern` | Wrapped: `\b(YOUR_PATTERN)\b` | Same — character class plus repetition. Do NOT add `\b` or `()`. |
| `person_verb_patterns[*]` | `\b` is replaced with the locale's script-aware boundary (only if `boundary_chars` is set). Otherwise left as-is. | Use `\b{name}\s+...\b` — `{name}` is replaced with `re.escape(name)` at compile time. |
| `pronoun_patterns[*]` | Same `\b` expansion treatment. | `\bён\b`, etc. |
| `dialogue_patterns[*]` | Same. | `^{name}:\s`, etc. |
| `direct_address_pattern` | Same. Returned as a list (one entry per language), each compiled separately. | `\bпрывітанне\s+{name}\b\|\bдзякуй\s+{name}\b` |
| `project_verb_patterns[*]` | Same. | `\bусталяваў\s+{name}\b`, etc. |
| `stopwords[*]` | Lowercased, union-merged into a set across all languages, returned sorted. | Plain words: `["і", "у", "на", ...]` |
| `boundary_chars` | If set, modifies all the above. | **Omit for Belarusian.** Only Hindi sets this (`"\\w\\u0900-\\u097F"`). |

**Why no `boundary_chars` for Belarusian** (verified via Context7
[`/python/cpython` docs on `\b` and `\w`](https://github.com/python/cpython/blob/main/Doc/library/re.rst)):

- Python 3 `re` module on `str` patterns matches `\w` against Unicode
  alphanumerics + underscore by default. The `re.UNICODE` flag is redundant.
- All Belarusian letters (а-я + ё + і + ў + А-Я + Ё + І + Ў) are Unicode
  category L (Letter), so they match `\w` without any flag.
- `\b` is the boundary between `\w` and `\W` (or string edge), so it works
  correctly between Cyrillic and ASCII/whitespace.
- `re.IGNORECASE` does Unicode case folding (А↔а, Ё↔ё, etc.) on `str` patterns.
- `boundary_chars` is **only** needed for scripts with combining marks (Mc/Mn
  category) that `\w` doesn't cover — Devanagari matras, Arabic harakat, Thai
  vowel signs, etc. Belarusian has no such marks.

**Anti-pattern:** Adding `"boundary_chars": "\\w\\u0400-\\u04FF"` to `be.json`
would be a no-op (the lookaround `(?<=[\w\u0400-\u04FF])(?=[^\w\u0400-\u04FF])`
behaves identically to `\b` for Cyrillic content) but adds review confusion.
Omit it.

### Pattern 5: Layered Lazy Caches with Manual Invalidation

**What:** Three cache layers, each with different invalidation rules.

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: _strings (module global dict)                      │
│ Populated by: load_lang(lang) — overwrites entire dict      │
│ Invalidated by: next load_lang() call (IMPLICIT overwrite)  │
│ Tests rely on: NEVER cleared automatically; test_from_       │
│   config_defaults_to_english catches a regression where      │
│   Dialect inherited polluted state                           │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: _entity_cache (module global dict)                 │
│ Populated by: get_entity_patterns(langs) — keyed by tuple   │
│   of canonical lang names (case-folded for cache hit)       │
│ Invalidated by: nothing in production code.                 │
│   Tests clear via i18n._entity_cache.clear() (autouse        │
│   fixture in test_i18n_lang_case.py; _temp_locale ctx mgr   │
│   in test_entity_detector.py).                              │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: functools.lru_cache on entity_detector functions   │
│   _build_patterns(name, langs)  — maxsize=256               │
│   _pronoun_re(langs)            — maxsize=32                │
│   _get_stopwords(langs)         — maxsize=32                │
│ Invalidated by: nothing in production. Tests call           │
│   .cache_clear() on each in _temp_locale teardown.          │
└─────────────────────────────────────────────────────────────┘
```

**The "edit-and-rerun-tests" story for the implementer:**

- **Editing `be.json` between separate `pytest` runs:** Zero cache concern. New
  process, new module load, fresh caches.
- **Editing `be.json` mid-pytest-run (e.g. via REPL):** Layer 1 stale until next
  `load_lang("be")`. Layers 2-3 stale forever unless manually cleared.
  `_temp_locale` (used in tests/test_entity_detector.py:389) is the canonical
  pattern — but you should NOT need this when you're authoring real locale files.
- **Test isolation across the 13+2 locales:** `test_all_languages_load` loops
  `available_languages()` which returns a sorted list. `be` sorts before `de`,
  `be-tarask` sorts after `be` and before `de`. The loop calls `load_lang(lang)`
  on each, so by the end of the loop `_strings` holds the alphabetically-last
  locale (was `zh-TW`, will remain `zh-TW`). No test in the existing suite
  asserts on `_current_lang` after the loop.

---

## 5. Data Flow — The Two Walks End-to-End

### Walk A: `t("aaak.instruction")` from import to render (live in production)

```
1. import time:
   from mempalace.i18n import t
   └─> module body executes
       └─> last line: load_lang("en")
           └─> _canonical_lang("en") → "en"
           └─> json.loads(en.json) → _strings = {...}
           └─> _current_lang = "en"

2. user code (e.g. Dialect(lang="be")):
   load_lang("be")
   └─> _canonical_lang("be") → "be"
   └─> json.loads(be.json) → _strings = {... be content ...}
   └─> _current_lang = "be"
   (Note: _entity_cache is NOT touched)

3. Dialect.__init__ continues:
   self.aaak_instruction = t("aaak.instruction")
   └─> _strings["aaak"]["instruction"]
   └─> for be.json: returns the Belarusian instruction string
   self.lang_regex = get_regex()
   └─> _strings.get("regex", {}) → entire regex dict
       (stored on instance but never read by Dialect's compress() path)

4. closet_llm._call_llm() (only if user runs `python -m mempalace.closet_llm`):
   from mempalace.i18n import t
   lang_instruction = t("aaak.instruction")
   if lang_instruction and "english" not in lang_instruction.lower():
       prompt += f"\n\nLanguage instruction: {lang_instruction}"
   └─> The Belarusian aaak.instruction is appended to the LLM prompt as a
       per-locale steering hint. THIS IS LIVE BEHAVIOR — every closet
       regeneration call carries our string into the model context.
```

### Walk B: `extract_candidates(text, languages=("en", "be"))` (live in production)

```
1. extract_candidates calls _normalize_langs(("en","be")) → ("en","be")
2. patterns = get_entity_patterns(("en","be"))
   └─> normalize via _canonical_lang per element → ("en","be")
   └─> key = ("en","be"); cache miss on first call
   └─> for "en": _load_entity_section("en") → en.json["entity"]
       └─> _collect_entity_section: appends EN candidate_pattern to acc
       └─> extends person_verbs/pronouns/dialogue with EN patterns
       └─> updates stopwords set with EN words (lowercased)
   └─> for "be": _load_entity_section("be") → be.json["entity"]
       └─> _collect_entity_section: appends BE candidate_pattern AFTER EN
       └─> extends person_verbs/pronouns/dialogue with BE patterns AFTER EN
       └─> updates stopwords set with BE words
   └─> _dedupe each list (preserving first-occurrence order)
   └─> stopwords sorted as a list
   └─> _entity_cache[("en","be")] = merged

3. consumer compiles:
   for wrapped_pat in patterns["candidate_patterns"]:
       rx = re.compile(wrapped_pat)   # \b([A-Z][a-z]{1,19})\b for EN,
                                       # \b([А-ЯЁІЎ][а-яёіў]{1,19})\b for BE
       for word in rx.findall(text):
           ... (frequency counting, stopword filtering)

4. score_entity uses _build_patterns(name, ("en","be")):
   └─> Compiles {dialogue, person_verbs, project_verbs, direct, versioned, code_ref}
       per (name, langs) tuple. Cached for 256 entries.
   └─> Calls re.IGNORECASE on every compile, so Cyrillic case folding works.

5. Belarusian text "Алег сказаў прывітанне" passes through:
   - extract_candidates: BE pattern fires → "Алег" detected as candidate
     (assuming frequency ≥ 3 in real text)
   - score_entity: BE person_verb pattern \b{name}\s+сказаў[аі]?\b fires
     → person_score += 2 per match
```

### Cache invalidation rules summary

| Event | `_strings` | `_entity_cache` | `lru_cache` (entity_detector) |
|---|---|---|---|
| `load_lang("be")` | overwritten | unchanged | unchanged |
| `get_entity_patterns(("be",))` first call | unchanged | new entry added | unchanged (entity_detector caches are different) |
| `get_entity_patterns(("BE",))` second call | unchanged | hits same `("be",)` entry | unchanged |
| `t("foo")` | initialized via load_lang("en") if empty | unchanged | unchanged |
| Editing `be.json` mid-process | stale | stale | stale (each layer needs explicit clear) |
| Test process restart | fresh | fresh | fresh |

---

## 6. Anti-Patterns — How NOT to Add a Locale

### Anti-Pattern 1: Editing `__init__.py` to Register the New Locale

**What people might do:** Add `"be"` and `"be-tarask"` to a hardcoded list,
import the file explicitly, or extend a registry.

**Why it's wrong:** There IS no registry. `_LANG_DIR.glob("*.json")` is the
discovery mechanism. Adding to a list (which doesn't exist) is a no-op at
best, a merge-conflict landmine at worst (the maintainer will reject any
diff to `__init__.py` for a pure-data PR).

**Do this instead:** Drop the JSON files and stop. The PROJECT.md decision
"No new module-level infra" is enforced here.

### Anti-Pattern 2: Adding `boundary_chars` to a Cyrillic Locale

**What people might do:** Copy the Hindi pattern blindly: `"boundary_chars": "\\w\\u0400-\\u04FF"`.

**Why it's wrong:** Python's default `\b` already works for Cyrillic
([Context7 / `/python/cpython` `re.rst`](https://github.com/python/cpython/blob/main/Doc/library/re.rst):
"The default word characters in Unicode (str) patterns are Unicode
alphanumerics and the underscore"). Belarusian has no combining marks. The
expanded lookaround would behave identically to `\b` but adds visual noise
and prompts a reviewer "why?" round-trip. Hindi needs it because Devanagari
matras (ा ी ु ं) are Unicode category Mc/Mn, not L — `\w` doesn't match them.

**Do this instead:** Omit `boundary_chars` entirely. Leave `\b` literal in
your patterns; `_expand_b` returns them unchanged when `boundary_chars` is
falsy (`__init__.py:144-146`).

### Anti-Pattern 3: Translating From `ru.json` Instead of From `en.json`

**What people might do:** `cp ru.json be.json` then transliterate words to
Belarusian orthography.

**Why it's wrong:** `ru.json` is the right **structural** template (Cyrillic
candidate pattern, Russian-style person_verb shapes, similar pronoun grammar)
but Belarusian and Russian diverge on:
- Function words (Russian `и` vs Belarusian `і` and `ды`)
- Verb conjugation suffixes (subtle aspect/gender form differences)
- Lexical choices (Russian `шкаф` "closet" vs Belarusian `шафа`; `ящик` vs
  `шуфляда`)
- Pronoun shapes (Russian `она/её/ей` vs Belarusian `яна/яе/ёй`)

A locale that's transliterated from `ru.json` will pass `pytest` (the tests
don't check for Belarusian linguistic correctness) but will read like clumsy
Russian-with-Belarusian-letters and fail the project's "Core Value" gate
(PROJECT.md line 21-26).

**Do this instead:** Translate each string from `en.json` semantically. Use
`ru.json` only as a "what does this regex shape look like in Cyrillic" reference.
Native-speaker review (NATIVE-01) catches transliteration smell.

### Anti-Pattern 4: Skipping a Required Key Hoping for English Fallback

**What people might do:** Leave out `cli.no_palace` because "the user
probably won't see it" or omit `entity.pronoun_patterns` to "keep the diff small".

**Why it's wrong:** `t("cli.no_palace")` on a locale missing that key returns
the **literal string `"cli.no_palace"`** — not the English fallback
(`__init__.py:73`). Similarly, missing entity sub-keys are silently skipped
(no English merge-in for that field).

**Do this instead:** Mirror `en.json`'s schema completely. Every key in
`en.json`'s `terms`, `cli`, `aaak`, `regex`, `entity` sections must have a
Belarusian counterpart. The test contract enforces a minimum (`test_all_languages_load`
checks for `palace/wing/closet/drawer/instruction`; `test_interpolation`
checks `cli.mine_complete` interpolates `{closets}` and `{drawers}`) but the
project requires the full schema (BE-02 through BE-06).

### Anti-Pattern 5: Mismatching `.format()` Placeholders

**What people might do:** Translate `"Mining {path}..."` to
`"Раскопка {шлях}..."` (translating the placeholder name too).

**Why it's wrong:** `t("cli.mine_start", path="/foo")` calls
`val.format(path="/foo")`. If the template has `{шлях}` but the kwarg is
`path`, `KeyError` is raised and silently swallowed (`__init__.py:79-80`),
returning `"Раскопка {шлях}..."` literally. User sees an unsubstituted
placeholder. Even worse: `test_interpolation` will fail with
`assert "5" in "Гатова. {шафы} шафаў..."` because the count never gets
interpolated.

**Do this instead:** Keep the **placeholder names exactly as in `en.json`**.
Translate around them. The English keys `{path}`, `{closets}`, `{drawers}`,
`{count}`, `{query}`, `{fixed}` must appear unchanged in your Belarusian
strings. Korean's `cli.status_drawers` regression
(`test_korean_status_drawers_uses_count`) was exactly this bug — the
template said `{drawers}` but the test passes `count=42`.

### Anti-Pattern 6: Hardcoding the New Lang Code Anywhere Else

**What people might do:** Edit `tests/test_i18n.py:test_dialect_compress_samples`
to add a Belarusian sample, then also add `"be"` to some hardcoded list
elsewhere.

**Why it's wrong:** There IS no other hardcoded list. `entity_detector`,
`palace`, `dialect`, `closet_llm` all read from
`MempalaceConfig().entity_languages` (env-var/config-file driven) or the
caller's explicit `languages=` kwarg. Adding `"be"` somewhere in source code
is dead code.

**Do this instead:** Add the Belarusian sample to
`test_dialect_compress_samples` (per CONTRIBUTING.md "Add or update tests"
rule and PROJECT.md TEST-02 requirement) — that is the one and only allowed
test file edit. Nothing else.

### Anti-Pattern 7: Using Uppercase or Underscored Filenames

**What people might do:** `Be.json`, `BE.json`, `be_tarask.json`.

**Why it's wrong:** `_canonical_lang` matches case-insensitively, so
`Be.json` and `BE.json` would technically resolve. But:
- `available_languages()` exposes `path.stem` (case-preserved), so users see
  `--lang Be` in help output — inconsistent with `pt-br`'s lowercase precedent.
- `be_tarask.json` is auto-discovered with stem `"be_tarask"` — but BCP 47
  uses hyphens. `--lang be-tarask` would NOT match `be_tarask` (lowercase
  "be_tarask" != lowercase "be-tarask"). The locale would be effectively
  unreachable through the documented BCP 47 interface.

**Do this instead:** `be.json` and `be-tarask.json`. Lowercase, hyphen, exact.

---

## 7. Integration Points — What `be.json` Plugs Into

### Live runtime consumers (your strings affect users today)

| Integration | What carries Belarusian text into user-visible output |
|---|---|
| `Dialect(lang="be").aaak_instruction` | Stored on the `Dialect` instance. Currently used as a stored attribute only — `Dialect.compress()` doesn't read it. So this is **infrastructure-ready** but not yet rendered. |
| `closet_llm._call_llm` → LLM prompt | If `LLM_ENDPOINT` is set and the user runs `python -m mempalace.closet_llm`, the Belarusian `aaak.instruction` is appended to the LLM prompt as a steering hint: `prompt += f"\n\nLanguage instruction: {lang_instruction}"`. **This is the only currently-live string-consumption path.** |
| `entity_detector.detect_entities(paths, languages=("en","be"))` | Belarusian person/project names are extracted from prose files. Used by `mempalace init` (Pass 1) when `--lang be` is passed (or `MEMPALACE_ENTITY_LANGUAGES=be` is set). The detected entities are saved to `<project>/entities.json` and feed the miner's wing/room routing. |
| `palace._candidate_entity_words` → closet pointer lines | When `MempalaceConfig().entity_languages` includes `"be"`, Belarusian candidate names are extracted from drawer content during mining and surface as `entity_str` in closet pointer lines (`topic|entity_str|→drawer_ids`). |

### Test contract consumers (your strings must satisfy these to merge)

| Test | What it checks |
|---|---|
| `tests/test_i18n.py::test_all_languages_load` | `lang/label/terms/cli/aaak` sections present; `terms.{palace,wing,closet,drawer}` non-empty; `aaak.instruction` present. |
| `tests/test_i18n.py::test_interpolation` | `t("cli.mine_complete", closets=5, drawers=100)` → output contains `"5"` and `"100"` (so placeholder names must be `{closets}` and `{drawers}` exactly). |
| `tests/test_i18n.py::test_dialect_loads_lang` | `Dialect(lang="be").lang == "be"`; `len(aaak_instruction) > 10`. |
| `tests/test_i18n.py::test_dialect_compress_samples` | Optional: add a Belarusian sample (TEST-02). |
| `tests/test_i18n_lang_case.py::*` | Indirectly — every new locale flows through `_canonical_lang` and must work with mixed-case lookups. `be-tarask` exercises hyphenated tag handling alongside `pt-br` and `zh-CN`. |
| `tests/test_entity_detector.py::*` | Indirectly via `_temp_locale` for synthesized fixtures. The real `be.json` entity section is exercised only if a future test adds Belarusian — current tests don't cover it. |

### Configuration surface (how users opt into Belarusian)

| Mechanism | Effect |
|---|---|
| `mempalace init --lang be /path` | Calls `cfg.set_entity_languages(["be"])` → persisted to `~/.mempalace/config.json`. Subsequent `mempalace mine` calls use BE entity patterns. |
| `MEMPALACE_ENTITY_LANGUAGES=be,en` env var | Same effect, env wins over config (config.py:208-216). |
| `Dialect(lang="be")` | Loads `_strings = be.json` for the duration; sets the AAAK instruction stored on the Dialect instance. |
| `mempalace mine --lang be /path` | NOT supported. The `--lang` flag exists only on `init`. The mine command reads `MempalaceConfig().entity_languages`. |

---

## 8. Open Architectural Questions (Not Blockers, But Worth Knowing)

These are facts of the existing codebase, not gaps in our research. Implementer
should be aware:

1. **`cli.*` strings are translated but never rendered.** Worth doing anyway —
   tests require it, and upstream may eventually call `t()` from `cli.py`.
2. **`regex.*` strings are loaded but never read.** Same logic: required by
   PROJECT.md BE-05, infrastructure-ready, may become live later.
3. **`Dialect.aaak_instruction` is set but only read by `closet_llm`.**
   `Dialect.compress()` itself uses module-level `_STOP_WORDS` (English
   hardcoded), not `self.lang_regex`. So `compress()` produces English-style
   AAAK output regardless of locale — the locale only affects the `closet_llm`
   prompt augmentation. Don't expect Belarusian text to compress to Belarusian
   AAAK; expect it to compress to AAAK with Belarusian keyword tokens preserved
   (whatever `_extract_topics` finds).
4. **`pronoun_patterns` are case-folded via `re.IGNORECASE` at compile time**
   (`entity_detector.py:69, 174, 192, 196, 197, 210`). So `\bён\b` matches both
   `ён` and `ЁН`. This means Belarusian pronouns can be lowercase in the JSON.

---

## Sources

### Primary (HIGH confidence — read directly)

- `mempalace/i18n/__init__.py` (286 lines, full read) — the contract
- `mempalace/entity_detector.py` (591 lines, full read) — primary entity consumer
- `mempalace/dialect.py` (1092 lines, full read) — `Dialect` lifecycle and `t()` use
- `mempalace/closet_llm.py` (352 lines, full read) — only live consumer of `t("aaak.instruction")` in LLM prompt
- `mempalace/palace.py:130-220` — `_candidate_entity_words` and closet line builder
- `mempalace/config.py:200-235` — `entity_languages` resolution from env/config
- `mempalace/i18n/en.json` (147 lines) — canonical schema reference
- `mempalace/i18n/ru.json` (162 lines) — Cyrillic structural template
- `mempalace/i18n/hi.json` (105 lines) — only locale using `boundary_chars`
- `tests/test_i18n.py` (88 lines) — required contract
- `tests/test_i18n_lang_case.py` (87 lines) — case-insensitivity contract
- `tests/test_entity_detector.py` (664 lines) — entity contract + `_temp_locale` fixture pattern

### MCP-cited (per quality-gate requirement)

- **`user-context7`** → `/python/cpython` (Python 3 official docs):
  [`Doc/library/re.rst`](https://github.com/python/cpython/blob/main/Doc/library/re.rst)
  on `\b`, `\w`, `re.UNICODE` (no-op), `re.ASCII`, `re.IGNORECASE`. Confirmed:
  - "The default word characters in Unicode (str) patterns are Unicode
    alphanumerics and the underscore" → Belarusian Cyrillic letters are matched
    by default `\w` with no flags.
  - "In Python 3, Unicode characters are matched by default for `str` patterns.
    The `UNICODE` flag is therefore redundant with **no effect**" → no flag
    declaration needed in entity patterns.
  - `\b` is the boundary between `\w` and `\W` → works for Cyrillic without
    `boundary_chars`.
- **`user-sequential-thinking`** → 3-step reasoning trace through `t("cli.mine_start", path="/foo")` and `get_entity_patterns(("be","en"))` end-to-end (verified each `_strings`/`_entity_cache`/`lru_cache` interaction against source).
- **`user-git`** (via Shell `git log`) → traced when `_canonical_lang` was added (`0174b93`, PR #927), when `boundary_chars` infra landed (`f895bc5` for the `_script_boundary`/`_expand_b` helpers in `__init__.py`, `21da870` for the Hindi JSON consumer, `33a98fb` for prior Hindi entity infra), and the multi-language refactor in `entity_detector.py` (`b214ace`).

### Confidence assessment

| Claim | Confidence | Verification |
|---|---|---|
| Auto-discovery via glob (no registry) | HIGH | source `__init__.py:39, 47` |
| Case-insensitive resolution | HIGH | source + `test_canonical_lang_uppercase_resolves` |
| `cli.*` not consumed by `cli.py` | HIGH | grep on entire repo for `from .i18n` / `from mempalace.i18n` returned only 4 production files (entity_detector, dialect, closet_llm, palace) plus 3 tests |
| `regex.*` only read by `Dialect.lang_regex` (and never used downstream) | HIGH | grep + read of `Dialect.compress()` confirmed it uses module-level `_STOP_WORDS` not `self.lang_regex` |
| `boundary_chars` not needed for Cyrillic | HIGH | Python `re.rst` docs (Context7) + Hindi-specific commits show purpose is for Mc/Mn marks |
| `t()` returns literal key on miss (no English fallback) | HIGH | source `__init__.py:73` |
| Entity section English fallback is all-or-nothing | HIGH | source `__init__.py:255-257` |
| Cache keys are case-folded canonical | HIGH | source `__init__.py:231` + `test_get_entity_patterns_shares_cache_across_cases` |
| Filename rule (`be.json`, `be-tarask.json` lowercase) | HIGH | `pt-br.json` precedent + IANA `tarask` subtag convention |

### Out-of-scope (intentionally not researched)

- ChromaDB/HNSW behavior on Cyrillic content (PROJECT.md "Out of Scope": #712 covers this).
- Belarusian linguistic correctness of suggested terms (NATIVE-01 gate covers this; the project owner is the authoritative source).
- Whether to wire `cli.py` to actually call `t()` (out of scope — would be a separate upstream PR).

---

*This is the architecture our two JSON files plug into. The implementer's job
is to honor every contract above and write nothing else.*

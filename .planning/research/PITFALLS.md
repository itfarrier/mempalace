# Pitfalls Research — MemPalace Belarusian i18n contribution

**Domain:** Brownfield i18n contribution — adding `be.json` (Narkamauka) and `be-tarask.json` (Tarashkievitsa) to `mempalace/i18n/`
**Researched:** 2026-04-20
**Confidence:** HIGH (git history + PR review threads are direct evidence; Belarusian linguistic claims verified against Wikipedia / Wikibooks / IANA)

> Three failure surfaces converge in this PR:
>
> 1. **Mistakes prior i18n PRs made** that reviewers caught — and that were merged as `fix(i18n): ...` follow-ups. Each is a concrete, named lesson with a commit hash.
> 2. **Belarusian-specific linguistic traps** — orthographic mixing, false friends from Russian, gender-agreement errors in past-tense verbs, the `ў`/`і`/apostrophe character set.
> 3. **Generic i18n traps in this codebase** — JSON validates but regex fails at `re.compile`, interpolation key drift, `_entity_cache` staleness during local dev, English fallback that hides real bugs.
>
> The native-speaker review pass (NATIVE-01 from PROJECT.md) is the only line of defense that catches the linguistic traps. Tests catch interpolation and load failures but not "this reads like clumsy Russian-with-Belarusian-characters" — which is the explicit failure mode called out in PROJECT.md *Core Value*.

---

## Critical Pitfalls

### Pitfall 1: Translating `ru.json` instead of translating from `en.json`

**What goes wrong:**
Russian and Belarusian share script and ~70-80% lexical overlap, so it's tempting to copy `ru.json` and tweak a few characters. The result *looks* Belarusian but reads as machine-Russified Belarusian to a native speaker — the explicit "this project has failed" condition from `PROJECT.md` line 25-26.

**Why it happens:**
`ru.json` is the obvious structural template (only Cyrillic full-tier locale, 161 lines). Copy-paste-translate is faster than translating from English. False friends pass casual inspection because they're real Belarusian words — they just mean something different than the user expects. Past-tense masculine forms in Russian (`сказал`) and Belarusian (`сказаў`) differ by one character — easy to miss in a scan.

**Concrete failure examples drawn from `ru.json`:**

| `ru.json` token | Wrong if copied to BE | Correct BE | Why |
|---|---|---|---|
| `сказал[аи]?` (`person_verb`) | matches RU only | `сказа(ў\|ла\|лі)` | BE masc past tense ends in `-ў`, not `-л`. The `[аи]?` trick assumes a vowel suffix that doesn't exist on the BE masc form. |
| `благі` (in CLI; not actually in `ru.json`, but same trap) | "good" if you read it as Russian `благой` | "bad" in BE | False friend — opposite meaning. |
| `вяселле` | "fun/joy" if read as RU `веселье` | "wedding" in BE | False friend. |
| `выгода` | "profit" (RU) | "comfort" (BE) | False friend. |
| `беседа` (`бяседа` in BE) | "conversation" (RU) | "party/ceremony" (BE) | False friend. |
| `арбуз` (RU `palace`-adjacent? No, but: `palace` → `дворец` (RU) → `палац` (BE)) | wrong character: `е` vs `а` | `палац` | Different vowel; spelling differs. |
| `и` (RU letter) used in BE patterns | `и` doesn't exist in BE alphabet | `і` (U+0456) | BE replaced `и` with `і` in 1918 — every `и` in a BE pattern is a defect. |
| `у` used where BE wants `ў` | unstressed full `у` | `ў` (U+045E, short u) | `ў` is the most distinctive BE letter. Missing it = pattern doesn't match real BE text. |
| `ru.json regex.action_pattern` `[\\wа-яёА-ЯЁ\\s]` | misses BE-specific letters | `[\\wа-яёіІўЎ'ʼ\\s]` (or rely on `\w` if Unicode-aware) | Missing `і/І/ў/Ў` = action pattern silently truncates after BE-specific letters. |

**How to avoid:**
- Translate every string from `en.json`, keeping `ru.json` open only as a *structural* reference (which keys exist, what shape entity patterns take). PROJECT.md *Key Decisions* row 3 already commits to this — enforce it during native review.
- Run a `grep` pass on the candidate `be.json` for `и`, `ы` (in stop words), `ъ` (the RU hard sign), `ё` after consonants where BE would use `е`, and bare `у` in past-tense verb endings.
- Mandatory native review pass on every string (NATIVE-01) — script the diff against `ru.json` so the reviewer sees them side-by-side.

**Warning signs:**
- Any BE past-tense masculine verb ending in `-ал/-ил/-ел` instead of `-аў/-іў/-еў`.
- Any word from the `ru.json → be.json` false-friends table above.
- `и` appearing anywhere in the file (BE alphabet has no `и`).
- Russian hard sign `ъ` anywhere (BE uses apostrophe `ʼ`/`'` instead).
- `у` (full u) in a past-tense verb context where Belarusian morphology demands `ў` (short u).

**Phase to address:** Phase 2 (be.json author + native review) and Phase 3 (be-tarask.json author + native review). Add a pre-commit grep heuristic to the verification script.

**Source:** `mempalace/i18n/ru.json:43-89` (the patterns that should NOT be copied verbatim); Wikibooks, [False Friends of the Slavist/Russian-Belarusian](https://wikibooks.org/wiki/False_Friends_of_the_Slavist/Russian-Belarusian); MovaLark, [Belarusian past-tense conjugation](https://movalark.com/grammar_theory/verb-conjugation-patterns-in-belarusian-full-list/).

---

### Pitfall 2: Mixing Tarashkievitsa and Narkamauka inside one file

**What goes wrong:**
Both orthographies use the same alphabet, so a single typo carries an orthography from one file into the other. A `be.json` (Narkamauka) string containing a Tarashkievitsa-only token like `сьвет` (vs Narkamauka `свет`) is a defect; same for the reverse. The file ships, tests pass, but the user gets mixed-orthography output that signals "this contributor doesn't know which is which."

**Why it happens:**
- The two orthographies share ~95% of vocabulary; differences cluster in soft-sign placement, foreign-word adaptation, and a handful of morpheme endings.
- Author writes both files in one sitting and switches between mental modes.
- LLM assistance may output either orthography depending on prompt and not flag the choice.

**Concrete differences to watch for** (from [Wikipedia: Taraškievica](https://en.wikipedia.org/wiki/Tara%C5%A1kievica) §Differences):

| Feature | Narkamauka (`be.json`) | Tarashkievitsa (`be-tarask.json`) |
|---|---|---|
| Soft sign before consonant | `снег`, `зява`, `дзве` | `сьнег`, `зьява`, `дзьве` |
| Foreign-l in borrowings | `план`, `клуб`, `лагіка`, `Платон` | `плян`, `клюб`, `лёгіка`, `Плятон` |
| `д/т/з/с` before front vowels in borrowings | `сігнал`, `фізіка`, `сістэма` | `сыгнал`, `фізыка`, `сыстэма` |
| `-ір-/-ыр-` formant on borrowed verbs | KEEP: `фарміраваць`, `канфігураваць` (often `канфігурыраваць`) | DROP: `фармаваць`, `канфігураваць` |
| Adverb prefix `не-` vs `ня-` | `не толькі`, `нельга` | `ня толькі`, `нельга` (some retained) |
| Prepositional plural masc/neut endings | `у лясах`, `у палях` (only) | `у лясах` or `у лясох`, `у палях` or `у палёх` |
| Optional `ґ` (plosive g) | not present | optional, allowed |
| `ё` vs `е` in unstressed position after labial | `маянэз` | `маянэз` (similar; check case-by-case) |

**How to avoid:**
- Treat the two files as **two separate authoring tasks**, not "do `be-tarask.json` by find-and-replace from `be.json`".
- Build a small script that flags Tarashkievitsa-only patterns inside `be.json` and vice versa. Minimal version: grep for `сь`, `зь`, `дзь`, `плян`, `клюб`, `сыг`, `фізы` in `be.json`; grep for the soft-sign-less equivalents in `be-tarask.json`.
- Native review: tell the reviewer explicitly which file they're reading and ask them to flag any orthography leakage.

**Warning signs:**
- `be.json` contains substrings: `сь`, `зь`, `дзь`, `тс` before consonants, `плян`, `клюб`, `сыг`, `фізы`, `канф_iguraваць` without `-ір-`.
- `be-tarask.json` contains substrings: `сн` (where `сьн` is expected — `сьнег`/`сьнежань`), `план`/`клуб`/`сігнал`/`фізіка`, `фарміраваць` with `-ір-` formant.

**Phase to address:** Phase 3 (be-tarask.json) — **after** be.json is reviewed and locked. Sequential authorship reduces context switching.

**Source:** [Wikipedia: Taraškievica §Differences between Taraškievica and the official orthography](https://en.wikipedia.org/wiki/Tara%C5%A1kievica#Differences_between_Tara%C5%A1kievica_and_the_official_orthography); [Wikipedia: Belarusian orthography reform of 1933](https://en.wikipedia.org/wiki/Belarusian_orthography_reform_of_1933).

---

### Pitfall 3: Past-tense verb pattern shape — `-ў` ≠ `-л`

**What goes wrong:**
Belarusian past tense agrees with subject **gender** (not person), and the masculine ending is `-ў`, not the Russian `-л`. The `ru.json` pattern shape `\\b{name}\\s+сказал[аи]?\\b` cannot be character-class-tweaked into the Belarusian shape because BE masc has no vowel suffix after the `ў`. The pattern needs three explicit alternations.

**Belarusian past-tense paradigm** (verified [MovaLark](https://movalark.com/grammar_theory/verb-conjugation-patterns-in-belarusian-full-list/), [Vitba.org Ch.15](https://www.vitba.org/fofmb/chapter15.html)):

| Subject | Ending | Example: `казаць` (impf) | Example: `сказаць` (perf) |
|---|---|---|---|
| Masc sg | `-ў` | `Іван казаў` | `Іван сказаў` |
| Fem sg | `-ла` | `Алеся казала` | `Алеся сказала` |
| Neut sg | `-ло` (or `-ла` unstressed) | `дзіця казала` | `дзіця сказала` |
| Plural (all genders) | `-лі` | `яны казалі` | `яны сказалі` |

**Why it happens:**
Russian uses `-л` for all four forms (`сказал/сказала/сказало/сказали`), so the elegant `сказал[аи]?` covers RU completely. The trap is that one-character substitution `сказал → сказаў` doesn't extend — the BE pattern is a 3-way alternation not a character class.

**Concrete pattern shape for `be.json`** (illustrative — must be reviewed by native speaker, *not committed as-is*):

```json
"person_verb_patterns": [
  "\\b{name}\\s+(?:сказа(?:ў|ла|лі)|казаў|казала|казалі)\\b",
  "\\b{name}\\s+(?:спыта(?:ў|ла|лі)|пытаў|пытала|пыталі)\\b",
  "\\b{name}\\s+(?:адказа(?:ў|ла|лі)|адказваў|адказвала|адказвалі)\\b",
  "\\b{name}\\s+(?:расказа(?:ў|ла|лі)|расказваў|расказвала|расказвалі)\\b",
  "\\b{name}\\s+(?:засмяя(?:ўся|лася|ліся))\\b",
  "\\b{name}\\s+(?:усміхну(?:ўся|лася|ліся))\\b",
  "\\b{name}\\s+(?:заплака(?:ў|ла|лі))\\b",
  "\\b{name}\\s+(?:адчу(?:ў|ла|лі)|адчуваў|адчувала|адчувалі)\\b",
  "\\b{name}\\s+думае\\b",
  "\\b{name}\\s+хоча\\b",
  "\\b{name}\\s+любіць\\b",
  "\\b{name}\\s+ненавідзіць\\b",
  "\\b{name}\\s+ведае\\b",
  "\\b{name}\\s+(?:вырашы(?:ў|ла|лі))\\b",
  "\\b{name}\\s+(?:напіса(?:ў|ла|лі)|пісаў|пісала|пісалі)\\b"
]
```

**Aspectual pairs**: speech verbs come in imperfective/perfective pairs (`казаць/сказаць`, `пытаць/спытаць`, `пісаць/напісаць`). `ru.json` only includes perfective forms. For BE, native review should decide whether to include both aspects (recommended) or just perfective. Including both roughly doubles the person_verb pattern count from ~15 to ~25-30 — still well within `lru_cache(maxsize=256)` budget.

**Tarashkievitsa note:** The past-tense paradigm is **identical** between Narkamauka and Tarashkievitsa. The orthographic differences from Pitfall 2 don't touch verb morphology. So `person_verb_patterns` can largely be shared text between `be.json` and `be-tarask.json`. (But check borrowed verbs — `канфігураваць` vs `канфігурыраваць`.)

**Reflexive forms** end in `-ся` (sometimes `-ца`/`-цца` after specific consonants). `засмяяцца → засмяяўся/засмяялася/засмяяліся` — three forms, not the Russian `засмеялся/засмеялась/засмеялись`.

**How to avoid:**
- Build the `person_verb_patterns` list from a Belarusian grammar reference, not by character-substituting `ru.json`.
- Ask the native-speaker reviewer specifically: "for each verb, does this pattern match all gender/aspect forms a Belarusian author would naturally write?" Provide a sample sentence in each form.
- Add an integration test that constructs a Belarusian-prose sample with at least one masc, one fem, and one plural past-tense verb pattern, then asserts `score_entity` returns `person_score > 0`.

**Warning signs:**
- Any `person_verb_pattern` in `be.json` containing `сказал` (without alternation) — that's RU, not BE.
- Reflexive verb patterns ending in `(ся|ась|ись)` (RU) instead of `(ўся|лася|ліся)` (BE).
- Single regex character class `[аиоу]?` after a verb stem — BE morphology doesn't follow that shape.

**Phase to address:** Phase 2 (be.json) and Phase 3 (be-tarask.json). Reviewer focus block in PR description.

**Source:** [MovaLark, Verb Conjugation Patterns in Belarusian](https://movalark.com/grammar_theory/verb-conjugation-patterns-in-belarusian-full-list/); [Vitba.org Belarusian textbook Ch. 15](https://www.vitba.org/fofmb/chapter15.html); `mempalace/i18n/ru.json:47-63` (the pattern shape NOT to copy).

---

### Pitfall 4: JSON validates, regex compiles, but matches the wrong thing

**What goes wrong:**
A regex with a JSON-escaping artifact compiles to a syntactically-valid Python regex that matches literal characters the author didn't intend. `test_all_languages_load` (which only checks `json.loads`) passes. `test_interpolation` (which only checks one string) passes. But entity detection silently misses a category of input.

**Concrete prior incident — pt-br PR #156, fix `4221589`:**

```diff
-      "^\">\\s*{name}[:\\s]",
+      "^>\\s*{name}[:\\s]",
```

The original pattern required a literal `">` at the start of the line. JSON loaded fine, regex compiled fine — but no real markdown-quoted dialogue line (`> Maria: hello`) ever matched. Caught only when reviewer @igorls ran a sample through `re.findall` locally.

**Other concrete failure modes from `ru.json` initial commit (`b87ada3`) → fix (`3e49522`):**

```diff
-    "quote_pattern": "\"([^\"]{20,200})\"",
+    "quote_pattern": "«\\s*([^»]{10,200})\\s*»|\"([^\"]{10,200})\"",
```

Russian uses guillemets `«…»`, not just ASCII quotes. Initial PR shipped with English-style quote regex; reviewer @almirus caught it.

**Why it happens:**
- JSON requires escaping `"` and `\` — the encoded form looks unfamiliar and easy to mis-type.
- Cursor/IDE syntax highlighting confirms valid JSON, not valid regex semantics.
- `test_all_languages_load` validates JSON shape, not regex behavior.
- The python `re.compile` step happens *inside* `entity_detector._build_patterns` — a try/except swallows `re.error` (`mempalace/entity_detector.py:179`), so a broken pattern silently disappears from the active set.

**The silent-swallow path** (`mempalace/entity_detector.py:174-181`):
```python
def _compile_each(raw_patterns, flags=re.IGNORECASE):
    compiled = []
    for p in raw_patterns:
        try:
            compiled.append(re.compile(p.format(name=n), flags))
        except (re.error, KeyError, IndexError):
            continue
    return compiled
```

A `re.error` from a malformed pattern is caught and the pattern is dropped without warning. The locale appears functional but is silently weaker.

**Concrete BE-specific risks:**

| Risk | Example |
|---|---|
| Apostrophe in regex char class without escape | `[а-яёі'ʼ]` — the `'` is fine in a char class, but `ʼ` (U+02BC) inside JSON requires no escaping; mixing in a backslash you remember from RU `\\` patterns can poison the class. |
| Belarusian opening quote `«` inside JSON | Unicode is fine in UTF-8 JSON; common mistake is to escape with `\\u00ab` for "safety" and miss the closing `\\u00bb`. |
| Pattern `(?:сказа(?:ў|ла|лі))` written as `(?:сказа(?:ў\|ла\|лі))` — the inner `\|` JSON escape works inside a regex (JSON unescapes to `|`), but `(?:сказа(\u0455|ла|лі))` if mistyped breaks the alternation. |
| Combining `і` (LATIN small letter i, U+0069) with Belarusian `і` (CYRILLIC small letter byelorussian-ukrainian i, U+0456) — visually identical, won't match. |

**How to avoid:**
- Add a verification step to the PR plan: load each new locale, compile every entity pattern, run `re.findall` against a representative Belarusian sample paragraph. Fail loudly on `re.error`.
- The test file at `tests/test_entity_detector.py:_temp_locale` (lines 392-432) is the model — instantiate the locale, call `extract_candidates`, assert names are extracted. Mirror this for `be` and `be-tarask`.
- Run a Unicode-codepoint check on the JSON file: every Cyrillic character should be in `U+0400..U+04FF` (or `U+02BC` for the apostrophe). A stray `i` (U+0069) inside what looks like Cyrillic word is a defect.

**Warning signs:**
- Any backslash sequence in a regex string that you can't trace through both JSON unescape and Python regex compile.
- Tests pass but `extract_candidates(belarusian_text, languages=("be",))` returns `{}` — silent regex drop.
- A real BE sentence containing `Іван сказаў` doesn't fire `score_entity > 0`.

**Phase to address:** Phase 4 (verification — the integration smoke test for `Dialect("be").compress(...)` plus a `score_entity` round-trip on a Belarusian sample is the catcher).

**Source:** Commit `4221589` (pt-br dialogue_patterns fix); commit `3e49522` (Russian quote_pattern fix); `mempalace/entity_detector.py:179` (silent `re.error` swallow); GH PR #156 review thread (@igorls catching the pattern locally).

---

### Pitfall 5: Interpolation key drift — `{drawers}` vs `{count}` and friends

**What goes wrong:**
A `cli.<key>` string uses a placeholder name that doesn't match what `mempalace/cli.py` actually passes via `t(...)`. The string literally renders `{drawers}` to the user instead of "5".

**Concrete prior incident — Hindi PR #718, fix `d565718`:**

```diff
-    "status_drawers": "{drawers} दराज़ें",
+    "status_drawers": "{count} दराज़ें",
```

Korean had the same bug (`ko.json status_drawers`). Caught only because `tests/test_i18n.py:test_interpolation` happens to use `closets=5, drawers=100` — but `test_korean_status_drawers_uses_count` (added as a regression test in the same fix) uses `count=42`. Without that targeted test, the Hindi/Korean bug would have shipped.

**The contract:** `mempalace/cli.py` calls `t("cli.status_drawers", count=N)`. Any locale that uses `{drawers}` instead of `{count}` is broken. Only one locale-defined key (`mine_complete`) actually takes both `{closets}` AND `{drawers}` — every other count-bearing key uses `{count}`.

**The full placeholder contract** (verified against `en.json` and `tests/test_i18n.py:79-87`):

| `cli.<key>` | Required placeholders |
|---|---|
| `mine_start` | `{path}` |
| `mine_complete` | `{closets}`, `{drawers}` |
| `mine_skip` | none |
| `search_no_results` | `{query}` |
| `search_results` | `{count}` |
| `status_palace` | `{path}` |
| `status_wings` | `{count}` |
| `status_closets` | `{count}` |
| `status_drawers` | `{count}` |
| `init_complete` | `{path}` |
| `init_exists` | `{path}` |
| `repair_complete` | `{fixed}` |
| `migrate_complete` | none |
| `no_palace` | none |

**Why it happens:**
- Translator reads `status_drawers` and reflexively names the placeholder "drawers" in the translation, mirroring the key.
- `test_interpolation` only checks `mine_complete` (which uses `closets` and `drawers`), so other keys aren't covered.
- `t()` silently passes through unmatched placeholders due to the `except (KeyError, IndexError): pass` at `mempalace/i18n/__init__.py:79-80` — no error is raised.

**How to avoid:**
- Diff every BE locale `cli.*` value against the English equivalent and confirm that placeholder names match exactly. A simple grep: every `{` in `be.json` `cli.*` must appear at the same position semantically as the matching `en.json` value.
- Add a generic test (or extend `test_interpolation`) that walks every cli key and checks the placeholder names in the translated string match the English placeholders. This is a one-time cost that prevents the entire class of bug for every future locale, not just BE.

**Warning signs:**
- `be.json` contains `{drawers}` outside of `mine_complete` — defect.
- `be.json` contains `{<anything>}` not present in the English equivalent — defect.
- `be.json cli.mine_complete` is missing one of `{closets}` or `{drawers}` — `test_interpolation` will fail.

**Phase to address:** Phase 2 (be.json author writes them); Phase 4 (verification — extend the test or do explicit grep diff in the verification script).

**Source:** Commit `d565718` (Korean fix); `mempalace/i18n/__init__.py:76-81` (silent passthrough on `KeyError`); `tests/test_i18n.py:72-77` (`test_korean_status_drawers_uses_count` regression).

---

### Pitfall 6: Thin `entity.stopwords` → false-positive entity candidates from sentence-starting function words

**What goes wrong:**
Belarusian function words at the start of sentences (`У`, `На`, `Ад`, `Калі`, `Бо`, `Але`, etc.) match the `[А-ЯЁІЎ][а-яёіў]{1,19}` candidate pattern and surface as entity candidates. The candidate threshold is 3+ occurrences, so any word starting >3 sentences in a Belarusian document becomes a "person" or "project" candidate.

**Concrete prior incident — pt-br PR #156, fix `4221589`:**

The initial pt-br stopwords list had 30 words. After review, @igorls confirmed that words like `Para`, `Como`, `Mas`, `Porém` (sentence-starters meaning "for/as/but/however") were producing false positives. The fix added 40 more stopwords (prepositions, conjunctions, demonstratives), bringing the list to ~70.

**Same trap, larger scale — Russian PR #760, follow-up `4b998de`:**

After the entity section landed, a separate commit added 34 prepositions and conjunctions to `ru.json entity.stopwords` ("Adds 34 prepositions and conjunctions to reduce false positives in entity detection when these words appear sentence-initial"). The initial entity section had ~30 stopwords; final list has 64.

**Concrete BE risk — sentence-starting words that match `[А-ЯЁІЎ][а-яёіў]{1,19}` and would surface as candidates if not in `entity.stopwords`:**

Conjunctions/particles: `Калі`, `Бо`, `Але`, `Аднак`, `Хаця`, `Таму`, `Так`, `Ну`, `Дык`, `Дзеля`, `Каб`, `Можа`, `Мабыць`, `Здаецца`, `Праўда`, `Канечне`, `Аднак`, `Зрэшты`.

Prepositions taking capital position: `У`, `Ва`, `На`, `За`, `Ад`, `Да`, `Аб`, `Пра`, `Без`, `Каля`, `Каля`, `Праз`, `Пасля`, `Перад`, `Пад`, `Над`, `Між`, `Сярод`, `Супраць`, `Замест`, `Паміж`, `Дзякуючы`, `Згодна`, `Насуперак`.

Adverbs: `Тут`, `Там`, `Цяпер`, `Заўсёды`, `Ніколі`, `Заўтра`, `Учора`, `Сёння`, `Пасля`, `Раней`, `Хутка`, `Доўга`, `Адразу`.

Pronouns/demonstratives: `Гэта`, `Гэты`, `Гэтая`, `Тое`, `Той`, `Тая`, `Усё`, `Усе`, `Кожны`, `Іншы`, `Іншая`.

Greetings (also in pt-br/ru pattern): `Прывітанне`, `Вітаю`, `Дзякуй`, `Калі ласка`, `Так`, `Не`.

**Why it happens:**
- Author focuses on translating `cli` and `aaak` strings; entity is "infra" and gets less attention.
- `ru.json` final list (64 stopwords) is the model, not the initial 30 — author who only sees the current `ru.json` doesn't realize 34 of those were added in a follow-up commit (`4b998de`).
- Test `test_extract_candidates_finds_frequent_names` uses ASCII names; nothing tests "sentence-starting Belarusian function words don't produce false positives".

**Note on cross-section duplication:**
`regex.stop_words` (used by AAAK compressor for topic extraction, `mempalace/dialect.py`) and `entity.stopwords` (used by `entity_detector.extract_candidates` to filter candidates) are **two different lists**. Both must contain Belarusian function words. `regex.stop_words` is space-separated; `entity.stopwords` is a JSON array of strings. The pt-br PR `4221589` review specifically called out: "Your `regex.stop_words` already has `para, como, mas, porém, embora, porque` — but the `entity.stopwords` list … is a separate list and missing them. Worth syncing."

**How to avoid:**
- Build `entity.stopwords` from a Belarusian frequency list (top 100-150 function words minimum) — not from translating `ru.json`'s list literally.
- Sync `regex.stop_words` and `entity.stopwords` so common function words appear in both. They serve different purposes but the same words populate both.
- Verification step: pick a 1000-word Belarusian text sample (e.g. a Wikipedia article in BE), run `extract_candidates(text, languages=("be",))`, and confirm that no function word appears in the result.

**Warning signs:**
- `entity.stopwords` has fewer than 50 items — almost certainly thin.
- Sentence-starting function words like `У`, `Калі`, `Аднак` not in the list.
- `regex.stop_words` and `entity.stopwords` diverge on common words.

**Phase to address:** Phase 2 (be.json) and Phase 3 (be-tarask.json). Add a verification step that runs candidate extraction on a Belarusian Wikipedia paragraph and asserts no function words surface.

**Source:** Commit `4221589` (pt-br stopwords expansion, +40 words); commit `4b998de` (Russian stopwords expansion, +34 words); GH PR #156 review thread (igorls's table of false-positive candidates).

---

### Pitfall 7: Apostrophe character variants — `'` vs `'` vs `ʼ`

**What goes wrong:**
Belarusian uses an apostrophe in words like `сям'я`, `аб'ява`, `пад'ехаць` (where Russian uses the hard sign `ъ`). Three Unicode characters look nearly identical:

| Codepoint | Glyph | Name | Status in IDNA Belarusian |
|---|---|---|---|
| U+0027 | `'` | APOSTROPHE | DISALLOWED |
| U+2019 | `'` | RIGHT SINGLE QUOTATION MARK | DISALLOWED |
| U+02BC | `ʼ` | MODIFIER LETTER APOSTROPHE | **REQUIRED** |

Source: [ICANN LGR for be-Cyrl](https://www.icann.org/sites/default/files/packages/lgr/lgr-second-level-belarusian-15may16-en.html), [LanguageTool forum thread](https://forum.languagetool.org/t/words-with-typographic-apostrophe-marked-wrong-for-belarusian/7888).

A regex pattern using one apostrophe variant won't match text typed with another. A user pasting BE prose into a memory note may use any of the three, and `extract_candidates(...)` will silently miss names containing apostrophes that don't match the pattern's variant.

**Why it happens:**
- IDE auto-corrects ASCII `'` to typographic `'` in JSON strings (or doesn't, depending on settings).
- The "linguistically correct" choice (U+02BC) is rare in real-world Belarusian text — most users type U+0027.
- Different sources of Belarusian text on the web use different conventions.

**Concrete BE word risks:**
- Personal names: `Вячаслаў` (no apostrophe), but `Сяр'жук` / `Сяр'гей` / `Сяр'ё́жа` (informal forms with apostrophe).
- Common nouns that hit `candidate_pattern`: `сям'я` (family), `аб'ект` (object), `пад'ём` (lift/rise), `здароўе` no apostrophe but `мадзьяр` has one in some sources.

**Decision required for PR:**
1. **Pick one canonical apostrophe in our JSON files** — recommend U+0027 (`'`) for pragmatic compatibility with how users actually type. Document the choice in PROJECT.md.
2. **Optional:** Make `candidate_pattern` and entity patterns tolerate all three. Easiest fix: include all three in the character class, e.g. `[а-яёіў'ʼ\u2019]`.

**How to avoid:**
- Pick the apostrophe convention before writing patterns. Document the choice.
- If matching liberally, include the three variants explicitly in any regex character class that can contain an apostrophe.
- Run a Unicode codepoint scan on the final JSON: every apostrophe-shaped character should be the chosen variant, no mixing.

**Warning signs:**
- Three different apostrophe codepoints appearing in one JSON file.
- A `candidate_pattern` character class that omits one apostrophe variant the document text uses.
- Native reviewer says "this name has an apostrophe in real life and your regex doesn't catch it."

**Phase to address:** Phase 1 (decide the convention as part of the be.json schema design); Phase 4 (verify with a sample containing apostrophe words).

**Source:** [ICANN LGR for be-Cyrl](https://www.icann.org/sites/default/files/packages/lgr/lgr-second-level-belarusian-15may16-en.html); [LanguageTool forum: Words with typographic apostrophe marked wrong for Belarusian](https://forum.languagetool.org/t/words-with-typographic-apostrophe-marked-wrong-for-belarusian/7888).

---

### Pitfall 8: Adding a no-op `boundary_chars` "for safety"

**What goes wrong:**
A contributor sees `hi.json` declares `"boundary_chars": "\\w\\u0900-\\u097F"` and reasons "BE is a non-English script too, let me add `"boundary_chars": "\\w\\u0400-\\u04FF"` to match." The result is a confusing no-op — `\w` already includes Cyrillic, so the script-aware boundary expression is identical to default `\b` behavior, just with added regex compilation cost.

**Why this matters specifically:**
- The Devanagari boundary fix (`f895bc5`) exists *because* Devanagari combining marks (Unicode category Mc) are NOT in `\w`. Hindi names like `अनीता` truncate to `अनीत` without the script-aware boundary.
- Cyrillic letters U+0400-U+04FF are all category Lu/Ll/Lt — they ARE in `\w`. No truncation issue exists. **PROJECT.md *Validated* row 5 already calls this out.**
- `_script_boundary` (`mempalace/i18n/__init__.py:113-134`) generates a four-clause lookaround. Adding it for Cyrillic adds compile-time cost and runtime overhead with zero behavior change.

**Why it happens:**
- Cargo-culting from `hi.json` because it's "a non-English locale".
- Misreading `hi.json` as the canonical "non-English locale" template instead of `ru.json`.
- The cost is invisible (test passes) so the mistake survives review unless someone explicitly checks.

**How to avoid:**
- Do NOT include `boundary_chars` in `be.json` or `be-tarask.json`.
- If the apostrophe is included in candidate text (Pitfall 7), still don't use `boundary_chars` — the apostrophe issue is character-class membership, not word-boundary semantics.
- Native reviewer should confirm by running `extract_candidates` against a sample with full-form names like `Святлана`, `Уладзімір`, `Рыгор`, `Алесь` and observing that no truncation occurs.

**Warning signs:**
- `boundary_chars` key present in `be.json` or `be-tarask.json`.
- Names ending in `ў` (Алясандру → Алясандр, Васiлю → Васiль) that could plausibly truncate. (They won't, because `ў` is `\w`, but check.)

**Phase to address:** Phase 2 / Phase 3 (don't include the field). Phase 4 (verify by extracting names from a BE sample).

**Source:** Commit `f895bc5` (the Devanagari fix that introduced `boundary_chars`); commit `21da870` (Hindi follow-up adding it); `mempalace/i18n/__init__.py:113-134` (`_script_boundary` implementation); PROJECT.md *Validated* row 5.

---

## Technical Debt Patterns

Shortcuts during translation that read fine but produce subtle long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|---|---|---|---|
| Copy `ru.json` and find/replace Cyrillic letters | Fast bootstrap of structure | Subtle Russification, false friends, wrong verb endings — the explicit "this project has failed" condition (PROJECT.md L25-26) | **Never** for translated strings; OK only for *schema/key* copying (which keys exist, what shape patterns take). |
| Use `LLM assist` for translation | Fast first draft of 14 cli + 13 terms strings | LLM may produce mixed orthography or false friends; pt-br PR #156 author flagged "I relied on LLM assistance for the linguistic choices. If any of the stopwords or verb forms look off to a native speaker, happy to correct." Same risk for BE. | OK as a starting draft but **mandatory** native-speaker review before commit (NATIVE-01 already enforces this). |
| Skip `entity.stopwords` expansion past ~30 entries | Fast first commit | Reviewer @igorls will run `extract_candidates` on sample text and find ~10-20 false-positive candidates from sentence-starting function words; round-trip cost = one extra commit (Russian had `4b998de`, pt-br had `4221589`). | Never for first PR — bake it in (target 60-100 stopwords like Russian's 64). |
| Omit `entity.action_pattern` localization or use English verbs | Faster | Hindi PR #773 was blocked at review for exactly this. The action pattern is used by AAAK extraction; English verbs in a BE locale silently extract nothing. | Never. |
| Reuse `ru.json` `quote_pattern` as-is | One less thing to think about | Russian uses `«…»`; Belarusian also uses `«…»` — actually OK to reuse the **shape**, but verify Belarusian doesn't prefer different quote marks (BE traditionally uses `«…»` in print and `„…"` informally). | Verify with native reviewer; accept if quotes match BE convention. |
| Use bare `у` where BE wants `ў` because the keyboard you're on doesn't have `ў` | Fast typing | Pattern doesn't match real BE text — entity detection silently fails on Belarusian past-tense verbs. | Never. Configure a Belarusian input method or paste from a BE source. |
| Skip the `aaak.instruction` rewrite, copy from `ru.json` | One fewer string to author | RU instruction says "Сжать" / "Дефисы"; BE equivalents are "Сцiснуць" / "Працяжнікі"; copying RU produces a `Dialect("be").compress()` instruction that is 95% Russian — affects every AAAK output. | Never. |
| Copy `direct_address_pattern` from `ru.json` | Fast | RU patterns include `привет/спасибо/здравствуйте/уважаемый` — these are RU, not BE. BE forms: `прывітанне/дзякуй/вітаю/паважаны/паважаная/спадар/спадарыня`. Direct-address is a +4 score signal — getting this wrong breaks person classification on BE prose. | Never. |
| Skip the integration smoke test (`Dialect("be").compress(...)` and `extract_candidates(be_text, languages=("be",))`) | Faster PR submission | The test contract only catches structural defects (load + interpolation); semantic defects (regex doesn't match real BE prose) ship undetected. | Never for full-tier PR — the explicit "Active" item TEST-02 already requires this. |

---

## Integration Gotchas

Mistakes that surface only when the locale interacts with `entity_detector`, `dialect`, `normalize`, or other consumers.

| Integration | Common Mistake | Correct Approach |
|---|---|---|
| `entity_detector._build_patterns` (`mempalace/entity_detector.py:167-198`) | Pattern with `KeyError` on `.format(name=n)` (e.g. `\\b{NAME}\\s+...` with wrong case) silently dropped via `except (re.error, KeyError, IndexError): continue` (line 179). Locale appears functional but is silently weaker. | Use `{name}` (lowercase) consistently. Verify by running `_build_patterns("Іван", ("be",))` and asserting all pattern lists are non-empty. |
| `entity_detector.extract_candidates` | The candidate `wrapped_pat` is **already wrapped with `\b(...)\b`** by `_collect_entity_section` (`mempalace/i18n/__init__.py:172-179`). Don't re-wrap in BE patterns or you'll get `\b\b(...)\b\b`. | Provide the raw character class only: `[А-ЯЁІЎ][а-яёіў]{1,19}`. The loader wraps. |
| `_canonical_lang` (`mempalace/i18n/__init__.py:28-42`) | Filename casing matters on case-sensitive filesystems. `be-Tarask.json` (capital T) would be discoverable via `_canonical_lang("be-tarask")` only if the on-disk stem matches lowercase. | Save as exactly `be.json` and `be-tarask.json` (all lowercase). PROJECT.md row 4 in *Key Decisions* confirms this. |
| `_entity_cache` invalidation | Module-level dict at `mempalace/i18n/__init__.py:25`. During iterative local dev (edit `be.json`, re-run `python -c "from mempalace.i18n import get_entity_patterns; print(get_entity_patterns(('be',)))"` *in the same interpreter session* via `importlib.reload`), the cache returns stale data from the first call. | Restart the Python interpreter between edits, OR call `i18n._entity_cache.clear()`, `entity_detector._build_patterns.cache_clear()`, `entity_detector._pronoun_re.cache_clear()`, `entity_detector._get_stopwords.cache_clear()` — see `tests/test_entity_detector.py:418-422` for the canonical reset sequence. |
| `Dialect.from_config()` (`mempalace/dialect.py`) | Per fix `d565718`: passing `lang=config.get("lang")` defaults to `None`, which made `__init__` inherit the module-level `_current_lang` set by some earlier `load_lang()` call. State leak. | Already fixed upstream — `Dialect.from_config()` defaults to `"en"`. Don't try to "improve" this. |
| `mempalace/cli.py` interpolation contract | Passing `t("cli.status_drawers", drawers=N)` instead of `t("cli.status_drawers", count=N)` would silently render `{drawers}` literally if the locale uses `{drawers}`. | The CLI uses `count=N`; locale must use `{count}`. Pitfall 5 above. |
| `entity_detector` ASCII-only fallback paths | Per fix `8bf940f`: `miner.py`, `palace.py`, `entity_registry.py` previously hardcoded `[A-Z][a-z]{2,}` ignoring i18n. Now they route through `_candidate_entity_words`. Implication: in older mempalace versions (pre-#931), users of the BE locale would still get ASCII-only entity tagging in some closet/registry paths. | Not our problem to fix in this PR. Note in PR description that we target `develop` post-#931 (i.e. mempalace ≥ 3.3.1 wire-up). |
| Locale auto-discovery | `_LANG_DIR.glob("*.json")` (`mempalace/i18n/__init__.py:39, 47`) picks up *every* `.json` file. Orphaned `zz-test-*.json` from a SIGKILLed test run will break `test_all_languages_load` because it lacks required sections. | Documented at `tests/test_entity_detector.py:399`. If a developer runs the test suite on a machine with a stale orphan locale, `test_all_languages_load` fails first — **before** our BE tests run. Recovery: `rm mempalace/i18n/zz-test-*.json`. |
| `entity_languages` config key | `MempalaceConfig.entity_languages` defaults to `["en"]` (`tests/test_entity_detector.py:553-557`). Adding `be.json` does NOT automatically include it in entity detection — the user must set `entity_languages=["en","be"]` (or env var `MEMPALACE_ENTITY_LANGUAGES=en,be`). | This is the consumer's responsibility, not ours. PR description should document: "After installing, add to `~/.mempalace/config.json`: `{\"entity_languages\": [\"en\", \"be\"]}`." |
| `t()` fallback semantics | `t("cli.no_palace")` when current lang is `be` and the key is missing returns the literal key string `"cli.no_palace"`, not the English string. (`mempalace/i18n/__init__.py:62-81`). | Every required `cli.*` key from `en.json` must be present in `be.json` and `be-tarask.json`. Missing key = literal-string output to the user. |

---

## Performance Traps

Mostly N/A for static JSON, but two real concerns:

| Trap | Symptoms | Prevention | When It Breaks |
|---|---|---|---|
| `entity_detector._build_patterns` LRU cache (`@lru_cache(maxsize=256)`, line 167) | First call per `(name, languages)` tuple compiles all person/dialogue/project verb regex; each unique BE entity name evicts an English entry once we cross 256. | Keep `person_verb_patterns` count bounded — Russian has 15, target similar (~15-25 incl. aspectual pairs) for BE. | Long-running MCP server processing >256 distinct names with `entity_languages=["en","be"]` triggers cache eviction churn. Fine for personal palaces; visible at corporate scale. |
| Catastrophic regex backtracking from poorly-bounded patterns | `re.findall` hangs or takes seconds on long input | Always bound quantifiers with `{m,n}`. Avoid nested `(.+)+` or `(.*)+` in `multi_word_pattern`. Russian `[А-ЯЁ][а-яё]+(?:\\s+[А-ЯЁ][а-яё]+)+` is fine — single repetition with bounded inner; mirror the shape. | A pattern like `[А-ЯЁІЎ][а-яёіў]+(?:\\s+[\\wа-яёіў\\s]+)+` (overlapping inner class with the outer) would be vulnerable. Don't write that. |
| `_entity_cache` hot-path | First call after locale change is slow; cached calls are O(1) | Cache size = `O(unique language tuples)`. Adding `be` and `be-tarask` adds ~6 new entries (en+be, en+be-tarask, be alone, be-tarask alone, be+be-tarask, en+be+be-tarask) at most. Negligible. | Never. |
| Adding a Belarusian sample to `test_dialect_compress_samples` | Each call instantiates a `Dialect`, which loads embeddings via `chromadb` if not already loaded. CI test time +1-2s. | Acceptable cost; explicitly listed in TEST-02. | Never breaks; just adds CI seconds. |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---|---|---|
| Mixing `і` (CYRILLIC small letter byelorussian-ukrainian i, U+0456) with Latin `i` (U+0069) in patterns | Homoglyph confusion: a user pasting from a copy-paste source that swapped `і` for `i` would not match. Worst case: an attacker socially-engineers a memory note where a name uses Latin `i` and BE patterns silently miss the entity. | Codepoint audit on all JSON files. Every Cyrillic-shaped character should be in U+0400-U+04FF (or apostrophe variants from Pitfall 7). Document the convention. |
| Catastrophic regex backtracking from poorly-bounded patterns (see Performance) | DoS: a maliciously-crafted file in a mined directory could pin an MCP server doing entity scoring. | Always use bounded `{m,n}`; never nest `(...)+` repetitions; avoid alternations of overlapping prefixes inside repetitions. Russian's pattern shapes are safe — follow them. |
| Apostrophe variants creating regex injection-like surprises | Less of a "security" issue than a correctness one, but a pattern compiled with one apostrophe variant in the wrong context (e.g. inside a character class) could match unintended characters. | Pitfall 7. Pick one variant; document; verify. |
| JSON values containing accidental control characters (NUL, vertical tab) from clipboard rounds | NUL bytes in candidate JSON keys would be rejected by `sanitize_kg_value` downstream (`.planning/codebase/CONCERNS.md` §4). Less of a load-time risk; more of a "this string flows through `t()` to the CLI which prints to terminal" risk. | Run `python -c 'import json; d=json.load(open("mempalace/i18n/be.json")); ...'` and walk every string for `\x00`-`\x1f` non-tab control chars. |
| Unicode normalization form mismatch (NFC vs NFD) | Same word may not match if pattern is NFC and text is NFD (or vice versa). For Belarusian this is rare — most Cyrillic is precomposed in NFC — but `й` could in theory be `и` + combining breve (NFD) which won't match `\bй\b`. | Save JSON as NFC. Sanity check: `python -c 'import unicodedata; ... assert all(c == unicodedata.normalize("NFC", c) for c in text)'` on the locale file. |
| The "looks-Cyrillic but is Latin" trick — characters like Latin `o` (U+006F), Latin `e` (U+0065) interleaved with Cyrillic | Same homoglyph problem, broader scope. Less of an issue for *file authoring* (we're typing from a Belarusian keyboard) than for *future maintenance* (someone editing the file in a non-CJK-aware editor). | Codepoint audit again. The audit script for the PR plan should flag any character outside U+0400-U+04FF, U+02BC, U+0027, U+2019, U+0020-U+007E (ASCII printable for JSON keys/punctuation), U+0009/U+000A (whitespace in JSON). |

---

## UX Pitfalls

Common user-facing mistakes specific to this i18n contribution.

| Pitfall | User Impact | Better Approach |
|---|---|---|
| Inconsistent vocabulary between `terms` and `cli` | User runs `mempalace status` and sees `Палац: ...` (terms.palace = `палац`) but `mempalace mine` shows `Раскопка ...` (cli.mine_start uses a verb form not derived from terms.mine). Reads jarring. | Pick the noun-stem first (e.g. `palace = палац`); derive every CLI usage from the same stem. If `mine` is `здабыча`, then `mine_start = "Здабываем {path}…"`. |
| Untranslated English in the `<dir>` placeholder of `cli.no_palace` | Russian uses `<директория>`; Italian uses `<cartella>`; Hindi uses `<dir>` (the Hindi PR left it as English). For BE: should be `<тэчка>` or `<каталог>`. | Don't ship `<dir>` literal; pick the BE word. |
| Tarashkievitsa-flavored words slipping into `be.json` (or vice versa) | A user who enabled `be` (Narkamauka) gets a `cli.mine_complete` saying "Гатова. Сьнегу няма…" (Tarashkievitsa-style soft sign) instead of "Гатова. Снегу няма…". Reads as "this contributor doesn't know which is which." | Pitfall 2 — script the orthography check; native review pass per file separately. |
| Direct-address pattern using only formal forms | BE has formal (`Шаноўны/Шаноўная/Паважаны`) and informal (`Прывітанне X`, `Дзякуй X`) registers; missing one halves the +4 direct-address score signal on the missing register. | Include both formal and informal: `\\bпрывітанне\\s+{name}\\b\|\\bдзякуй\\s+{name}\\b\|\\bвітаю\\s+{name}\\b\|\\bпаважаны\\s+{name}\\b\|\\bпаважаная\\s+{name}\\b\|\\bдарагі\\s+{name}\\b\|\\bдарагая\\s+{name}\\b\|\\bспадар\\s+{name}\\b\|\\bспадарыня\\s+{name}\\b`. |
| Diminutives not handled in entity detection | BE names have rich diminutive forms (Уладзімір → Валодзя/Валодзька/Уладак; Святлана → Света/Святка/Святачка). Pattern `[А-ЯЁІЎ][а-яёіў]{1,19}` catches them as candidates, but `person_verb` patterns use the formal name. | This is fine — the diminutive is a separate candidate, scored independently. Just confirm diminutives aren't accidentally in `entity.stopwords`. |
| `aaak.instruction` translated literally | The English instruction says "Hyphens between words, pipes between concepts. Drop articles and filler. Keep names and numbers exact." A literal BE translation works, but BE has no articles to drop (no `the`/`a`) — a BE-native instruction would say "drop prepositions/particles" instead. | Ask native reviewer to rewrite the instruction in idiomatic BE, not translate it. The model receiving this instruction will follow whatever feels most natural. |

---

## "Looks Done But Isn't" Checklist

Final review pass — before opening the PR. Every item is a verifiable check, not a feeling.

### Schema parity (catches structural drift)

- [ ] **Required keys present:** `lang`, `label`, `terms` (with `palace`, `wing`, `closet`, `drawer`), `cli` (all 14 keys from `en.json`), `aaak.instruction` (>10 chars), `regex.topic_pattern`, `regex.stop_words`, `regex.quote_pattern`, `regex.action_pattern`, `entity.candidate_pattern`, `entity.multi_word_pattern`, `entity.person_verb_patterns`, `entity.pronoun_patterns`, `entity.dialogue_patterns`, `entity.direct_address_pattern`, `entity.project_verb_patterns`, `entity.stopwords`. **Missing key = `t()` returns the literal key string.**
- [ ] **No extra `boundary_chars`** in `entity` section (Cyrillic doesn't need it; Pitfall 8).
- [ ] **`lang` field matches filename:** `be.json` has `"lang": "be"`; `be-tarask.json` has `"lang": "be-tarask"` (lowercase, hyphen — matches IANA registry).
- [ ] **`label` is in BE script:** `"Беларуская"` for both files (NOT `"Belarusian"`).

### Interpolation contract (catches the Korean/Hindi `{drawers}` bug)

- [ ] **`cli.mine_complete` contains both `{closets}` and `{drawers}`** — `test_interpolation` will fail otherwise.
- [ ] **Every `cli.<key>` placeholder matches the English equivalent's placeholder names exactly.** Diff the `{...}` sets per key against `en.json`. Pitfall 5.
- [ ] **No extra placeholders** in any `cli.<key>` (would fail silently via `except KeyError`).

### Regex sanity (catches the pt-br dialogue bug)

- [ ] **Every entity pattern compiles.** Run `python -c "from mempalace.entity_detector import _build_patterns; p = _build_patterns('Іван', ('be',)); assert all(p[k] for k in ['dialogue','person_verbs','project_verbs','direct'])"`.
- [ ] **`extract_candidates` finds at least one BE name in a sample.** Test against a 1000-word Belarusian Wikipedia paragraph; assert at least one capitalized BE name surfaces.
- [ ] **No false-positive function words surface.** Same 1000-word sample; assert that no word from the BE function-word stoplist appears in `extract_candidates(...)` output.
- [ ] **`score_entity('Іван', ...)` returns `person_score > 0`** when the sample has `Іван сказаў ...` AND `Іван думае ...`. If it returns 0, person_verb patterns don't match real text.
- [ ] **Direct-address pattern matches `Прывітанне Іван`, `Дзякуй Іван`, `Паважаны Іван`** — at least three forms tested.

### Linguistic correctness (catches the false-friend bug)

- [ ] **`be.json` contains no Russian-only letters:** grep `и` (Russian i — should be `і` in BE), `ъ` (Russian hard sign — BE uses `ʼ`). Both should return zero hits.
- [ ] **`be.json` masculine past-tense verbs end in `-ў`, not `-л`:** every `person_verb_pattern` for past tense should include the `-ў` ending alternation, not just `-л`. (Pitfall 3.)
- [ ] **`be.json` doesn't contain Tarashkievitsa-only forms:** grep for substrings `сь` (before consonant), `зь` (before consonant), `плян`, `клюб`, `сыг`, `фізы`, `фарміраваць`. Each should be reviewed; most should not be in the Narkamauka file. (Pitfall 2.)
- [ ] **`be-tarask.json` doesn't contain Narkamauka-only forms:** grep for `план`, `клуб`, `сігнал`, `фізіка`, `фармаваць`. Each should be reviewed; most should not be in the Tarashkievitsa file.
- [ ] **No false-friend Russian words masquerading as BE:** specifically check `благі`, `вяселле`, `выгода`, `бяседа`, `буйны`, `арбуз`, `гарбуз` aren't used in their Russian senses. (Pitfall 1.)
- [ ] **Apostrophe convention is consistent within and across both files:** all apostrophes are the same Unicode codepoint. (Pitfall 7.) Recommend U+0027 for pragmatic compatibility; document the choice in a top-of-file comment if JSON allowed comments — or in the PR description.

### Test contract (catches "I forgot to run pytest")

- [ ] `python -m pytest tests/test_i18n.py -v` passes (`test_all_languages_load`, `test_interpolation`, `test_dialect_loads_lang`, `test_dialect_compress_samples`, `test_korean_status_drawers_uses_count`, `test_from_config_defaults_to_english`).
- [ ] `python -m pytest tests/test_i18n_lang_case.py -v` passes — confirms `_canonical_lang("BE")`, `_canonical_lang("Be-Tarask")`, etc. resolve correctly.
- [ ] `python -m pytest tests/test_entity_detector.py -v` passes — including `_temp_locale`-based tests with no orphan files left behind.
- [ ] `python -m pytest tests/ -v --ignore=tests/benchmarks` passes the full suite (covers regression).
- [ ] `ruff check .` clean and `ruff format --check .` clean (CONTRIBUTING.md gate).
- [ ] **Optional but strongly recommended:** add a Belarusian sample to `test_dialect_compress_samples` (per PROJECT.md note in *Context*) — extends coverage and catches `aaak.instruction` defects.

### PR-author hygiene (catches "did you actually run it")

- [ ] **Local test was run with `entity_languages=["en","be"]`** at least once via env var: `MEMPALACE_ENTITY_LANGUAGES=en,be python -c "from mempalace.entity_detector import detect_entities; ..."`. Verifies the BE patterns actually fire end-to-end through config.
- [ ] **`Dialect("be").compress("...belarusian sample...")` returns non-empty Belarusian-shaped text** (TEST-02 from PROJECT.md).
- [ ] **`Dialect("be-tarask").compress("...tarashkievitsa sample...")` returns non-empty text.**
- [ ] **PR description follows the prior-i18n-PR template** (PR-02): native name (`Беларуская`), orthography rationale, two-file rationale, screenshot of pytest output. References commits `#760` (RU), `#907` (IT), `#778` (ID) as precedents.
- [ ] **Branch is `feat/i18n-belarusian`** targeting `develop`.
- [ ] **Conventional commits used** for all atomic commits within the PR (mirror Russian's pattern: `feat(i18n): add ...` → `fix(i18n): apply review feedback ...` if needed → `feat(i18n): expand ... stopwords` if reviewer flags).
- [ ] **Maintainer asked to approve fork CI workflow run** — Italian and Hindi PRs both stalled briefly because fork CI didn't auto-trigger. Add a one-line note to the PR opening message: "Please approve the workflow run for this fork PR."

### Native-speaker review pass (the hard gate, NATIVE-01)

- [ ] **Every translated string was read aloud** by the native-speaker reviewer.
- [ ] **Reviewer was told which file is which orthography** before reading (Narkamauka vs Tarashkievitsa).
- [ ] **Reviewer specifically confirmed:** no Russian-flavored phrasing in CLI strings; no awkward calques; verb forms agree with the implied subject; direct-address forms sound natural; greeting forms (`Прывітанне`, `Вітаю`) match the register the user would expect.
- [ ] **Reviewer signed off on the `aaak.instruction`** as something a Belarusian-speaking LLM would understand without confusion — not a literal translation of the English instruction.

---

## Recovery Strategies

When a pitfall slips through despite prevention, what to do.

| Pitfall | Recovery Cost | Recovery Steps |
|---|---|---|
| Russian transliteration in `be.json` (Pitfall 1) | MEDIUM (one follow-up commit, possibly two reviewers) | Mirror the Russian PR pattern: open a `fix(i18n): apply review feedback on be.json (#XXX)` follow-up commit. Don't force-push the original; preserve the review history. |
| Tarashkievitsa-Narkamauka mixing (Pitfall 2) | MEDIUM | Same — `fix(i18n): orthography correction` follow-up commit per file. The git log will become a learning artifact for future Slavic locales. |
| Wrong past-tense verb endings (Pitfall 3) | LOW (single commit, mechanical fix) | `fix(i18n/be): correct masculine past-tense verb forms`. Update both files if both have the same defect. |
| Regex compiles but matches nothing (Pitfall 4) | LOW if caught pre-merge; HIGH if caught post-merge by users (silent wrong behavior, no tests fire) | Add a test specifically for the failure mode (e.g. `test_dialogue_pattern_matches_markdown_quote`); fix the pattern; commit both. Test prevents regression in any future locale. |
| Wrong interpolation key (Pitfall 5) | LOW | One-line fix per locale. Add a test that asserts `t("cli.<key>", count=N)` interpolates `N` for every `cli.*` key that takes `{count}` — applies to all locales. |
| Thin stopwords (Pitfall 6) | LOW | `feat(i18n/be): expand entity stopwords with prepositions and conjunctions` follow-up commit (mirror RU `4b998de`). |
| Apostrophe variant mismatch (Pitfall 7) | MEDIUM | Decide convention; codepoint-rewrite all apostrophes in both files via `python -c 'p = Path("mempalace/i18n/be.json"); p.write_text(p.read_text().replace("\\u2019","\u0027").replace("\\u02bc","\u0027"))'`. Commit + test. |
| `boundary_chars` accidentally added (Pitfall 8) | LOW | Single deletion. `fix(i18n/be): remove no-op boundary_chars`. |
| Orphan `zz-test-*.json` from killed test run | LOW | `rm mempalace/i18n/zz-test-*.json` and re-run. Documented at `tests/test_entity_detector.py:399`. |
| User reports "BE entity detection misses my names" post-merge | MEDIUM-HIGH | Iterate via issue → PR cycle. The Russian locale shipped, then `4b998de` expanded stopwords; same lifecycle is acceptable for BE. Don't aim for 100% on day 1. |

---

## Pitfall-to-Phase Mapping

How each ROADMAP phase should address these pitfalls.

| Pitfall | Prevention Phase | Verification (concrete check) |
|---|---|---|
| **1. Russian transliteration** | Phase 2 (be.json author + native review) | Native reviewer signs off; grep for `и`, `ъ`, RU-specific past-tense `-л`. |
| **2. Orthography mixing** | Phase 2 + Phase 3 (separate authoring sessions) | Grep test for Tarashkievitsa-marker substrings in `be.json` and Narkamauka-marker substrings in `be-tarask.json`. |
| **3. Past-tense verb shape** | Phase 2, Phase 3 | `_build_patterns("Іван", ("be",))` returns non-empty `person_verbs`; `score_entity("Іван", "Іван сказаў ...", ...)` returns `> 0`. |
| **4. Regex compile-but-fail** | Phase 4 (verification) | Integration test: `extract_candidates(belarusian_sample, languages=("be",))` finds expected names. |
| **5. Interpolation key drift** | Phase 2 + Phase 4 | Diff placeholder set against `en.json`; `test_interpolation` passes. |
| **6. Thin stopwords** | Phase 2 + Phase 3 | Run `extract_candidates` on 1000-word BE Wikipedia paragraph; assert no function words surface. Target 60-100 stopwords each file. |
| **7. Apostrophe variants** | Phase 1 (decide) + Phase 4 (verify) | Codepoint scan: every apostrophe is the same character. |
| **8. No-op `boundary_chars`** | Phase 2 + Phase 3 | Grep: `"boundary_chars"` does NOT appear in `be.json` or `be-tarask.json`. |
| **9. Native-speaker gate** (NATIVE-01) | Every phase | NATIVE-01 in PROJECT.md is the hard gate; PR cannot proceed without sign-off. |
| **10. Cache staleness during local dev** | Phase 4 (developer note) | Document the cache-clear sequence in PR description for future contributors. |
| **11. Fork CI not auto-triggering** | Phase 5 (PR submission) | Add explicit one-liner to PR opening message asking maintainer to approve workflow run. |

---

## Sources

### Primary — git history (commit hashes verifiable in the repo)

- `b87ada3` — initial Russian i18n commit (what NOT to over-trust as a copy source).
- `d6bd7de` — Russian entity section addition (the structural template for `entity` schema).
- `3e49522` — `fix(i18n): apply review feedback on ru.json (#760)` — the `mine_skip` semantic-translation fix and the `quote_pattern` guillemets fix.
- `4b998de` — Russian stopwords expansion (+34 words) — pattern for "thin first PR, expanded after review".
- `3d13a72` — initial pt-br commit with entity section (the reference implementation of full-tier non-English locale).
- `4221589` — `fix(i18n): address review feedback on pt-br.json` — `dialogue_patterns` stray-quote fix, +40 stopwords, +6 pronouns.
- `921db17` — initial Hindi commit (CLI/regex only, no entity).
- `33a98fb` — Hindi entity section addition (after #911 framework landed).
- `21da870` — `fix(i18n/hi): add boundary_chars and update action_pattern for Devanagari-aware matching` — the script-aware boundary trap (NOT applicable to Cyrillic) and the `action_pattern` Unicode-class extension trap (IS applicable to Cyrillic if action_pattern is sloppy).
- `f895bc5` — `fix(entity_detector): script-aware word boundaries for combining-mark scripts` — the Devanagari fix that introduced `boundary_chars`. Confirms why Cyrillic doesn't need it.
- `d565718` — `fix: address i18n review issues from PR #718` — Korean `{drawers}` vs `{count}` bug + test file location bug + `Dialect.from_config()` state-leak bug.
- `0174b93` — `fix(i18n): resolve language codes case-insensitively (#927)` — case-sensitivity trap; cache-key normalization.
- `6caac50` — `fix(i18n): use Optional[str] for Python 3.9 compatibility` — Python 3.9 floor (CI matrix).
- `8bf940f` — `fix: use i18n candidate patterns for entity extraction in miner and palace` — confirms i18n locale is the single source of truth for candidate extraction (post-#931, mempalace ≥ 3.3.1).
- `b214ace` — `refactor(entity_detector): make multi-language extensible via i18n JSON` — the framework that enables our PR (our PR depends on this being merged).

### Primary — GitHub PR review threads

- [PR #760 (Russian)](https://github.com/MemPalace/mempalace/pull/760) — review comments by @almirus and merge by @igorls.
- [PR #156 (pt-br)](https://github.com/MemPalace/mempalace/pull/156) — review comments by @bgauryy, @web3guru888, @igorls; multiple force-pushes; reviewer @igorls's table of false-positive candidates.
- [PR #773 (Hindi)](https://github.com/MemPalace/mempalace/pull/773) — review by @igorls (action_pattern localization, then `boundary_chars` follow-up).
- [PR #907 (Italian)](https://github.com/MemPalace/mempalace/pull/907) — review by @igorls (test file location, optional entity section).
- [Issue #712 (non-English search quality)](https://github.com/MemPalace/mempalace/issues/712) — confirms the embedding model issue is OUT OF SCOPE for our PR; cited in PROJECT.md.
- [Issue #929 (MCP unicode crash)](https://github.com/MemPalace/mempalace/issues/929) — open-issue context; doesn't affect adding new locale JSONs.

### Primary — code in this repo

- `mempalace/i18n/__init__.py:25` (`_entity_cache` module-level dict — staleness during dev).
- `mempalace/i18n/__init__.py:113-134` (`_script_boundary` — confirms why Cyrillic skips `boundary_chars`).
- `mempalace/i18n/__init__.py:162-194` (`_collect_entity_section` — the candidate-pattern wrapping rule).
- `mempalace/entity_detector.py:174-181` (`_compile_each` silent `re.error` swallow — Pitfall 4).
- `mempalace/entity_detector.py:51-55` (`_get_stopwords` LRU cache).
- `mempalace/entity_detector.py:167-198` (`_build_patterns` LRU cache).
- `tests/test_i18n.py` (the test contract: `test_all_languages_load`, `test_interpolation`, `test_dialect_loads_lang`, `test_dialect_compress_samples`, `test_korean_status_drawers_uses_count`).
- `tests/test_i18n_lang_case.py` (case-insensitivity regression tests for #927).
- `tests/test_entity_detector.py:392-432` (`_temp_locale` helper + the orphan-locale-recovery comment).
- `tests/test_entity_detector.py:617-664` (`boundary_chars` regression tests — confirms the framework, confirms Cyrillic doesn't need it).

### Primary — Belarusian linguistic references

- [Wikipedia: Taraškievica](https://en.wikipedia.org/wiki/Tara%C5%A1kievica) — orthographic differences table (foreign-l, soft-sign-before-consonant, dental softness, prepositional plural).
- [Wikipedia: Belarusian orthography reform of 1933](https://en.wikipedia.org/wiki/Belarusian_orthography_reform_of_1933) — historical context for Narkamauka.
- [Wikibooks: False Friends of the Slavist/Russian-Belarusian](https://wikibooks.org/wiki/False_Friends_of_the_Slavist/Russian-Belarusian) — the seven-word false-friend list cited in Pitfall 1.
- [MovaLark: Verb Conjugation Patterns in Belarusian](https://movalark.com/grammar_theory/verb-conjugation-patterns-in-belarusian-full-list/) — past-tense `-ў/-ла/-ло/-лі` paradigm cited in Pitfall 3.
- [Vitba.org Belarusian textbook Chapter 15: Past Tenses](https://www.vitba.org/fofmb/chapter15.html) — secondary source for past-tense paradigm.
- [ICANN LGR for be-Cyrl](https://www.icann.org/sites/default/files/packages/lgr/lgr-second-level-belarusian-15may16-en.html) — apostrophe codepoint contract (U+02BC required, U+0027/U+2019 disallowed in IDNA) cited in Pitfall 7.
- [LanguageTool forum: Words with typographic apostrophe marked wrong for Belarusian](https://forum.languagetool.org/t/words-with-typographic-apostrophe-marked-wrong-for-belarusian/7888) — practical apostrophe-variant guidance.

### MCPs cited

- **`user-git`** — `git log --all --oneline -- mempalace/i18n/`, `git show <hash>` for every fix commit. Direct evidence; HIGH confidence.
- **`user-fetch`** — GitHub PR threads #760, #156, #773, #907; issues #712, #929. Direct evidence; HIGH confidence.
- **`user-context7` / WebSearch** — Belarusian linguistic references (Wikipedia, Wikibooks, ICANN, MovaLark, Vitba). Cross-checked against multiple sources; HIGH confidence.
- **`user-mempalace`** — searched for `TODO`/`FIXME`/`HACK` in i18n/entity_detector — none found. (Negative result; HIGH confidence in *absence* of in-code TODOs about i18n.)
- **`user-sequential-thinking`** — applied implicitly in the per-pitfall reasoning (e.g. "would this Hindi-specific bug also affect Cyrillic? No, because `\w` includes Cyrillic but not Devanagari Mc marks").

---

*Pitfalls research for: MemPalace Belarusian i18n contribution (`be` + `be-tarask`)*
*Researched: 2026-04-20*

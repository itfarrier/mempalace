# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-20)

**Core value:** Two upstream-merged Belarusian locales that pass `pytest tests/` and read like they were written by a native speaker — not transliterated from Russian and not machine-translated.
**Current focus:** Phase 1 — be.json (Narkamauka) base file

## Current Position

Phase: 1 of 5 (be.json (Narkamauka) base file)
Plan: 0 of 1 in current phase
Status: Ready to plan
Last activity: 2026-04-20 — Roadmap created; 42 v1 requirements mapped across 5 sequential phases

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: —
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. be.json base | 0/1 | — | — |
| 2. be.json entity | 0/1 | — | — |
| 3. be-tarask.json base | 0/1 | — | — |
| 4. be-tarask.json entity | 0/1 | — | — |
| 5. Tests + PR | 0/2 | — | — |

**Recent Trend:**
- Last 5 plans: (none yet)
- Trend: N/A — project just initialized

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- **Init**: Ship both `be.json` (Narkamauka) and `be-tarask.json` (Tarashkievitsa), full-tier with `entity` section, upstream PR to MemPalace/mempalace `develop`, native-speaker review on every string.
- **Init**: Use `ru.json` as a STRUCTURAL template only — translate from `en.json`, not from `ru.json`. Russian transliteration is the explicit project-failure condition.
- **Init**: Belarusian candidate pattern MUST be `[А-ЯЁІЎ][а-яёіў]{1,19}` — Russian's `[А-ЯЁ]` silently drops Belarusian-specific letters `Ў`/`І` (verified empirically in STACK.md).
- **Init**: Sequential per-file authorship (be.json fully done before starting be-tarask.json) — orthography mixing across files is the costliest mistake to recover from after PR submission (PITFALLS Pitfall 2).
- **Init**: No infrastructure changes — `mempalace/i18n/__init__.py` already supports auto-discovery, case-insensitive lookup, hyphenated tags, and per-locale entity merge. Pure-data PR.
- **Init recommendation** (deferred to Phase 1): Apostrophe codepoint U+0027 (ASCII `'`) for pragmatic compatibility — matches user input behavior and existing locale-file convention.

### Pending Todos

None yet — roadmap just created.

### Blockers/Concerns

None yet.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none — first milestone)* | | | |

## Session Continuity

Last session: 2026-04-20
Stopped at: Roadmap created and committed; 42 requirements mapped across 5 phases (LOC + NARK + TARASK + QA + TEST + SHIP)
Resume file: None — run `/gsd-plan-phase 1` to enter Phase 1

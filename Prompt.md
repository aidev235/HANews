# HANews weekly prompt

Produce issue: KB, EN/ZH reports/archives/logs, validation, Git publication; no
crawler/app/API client/scheduler.

## Invariants

- Timezone `America/Chicago`; default window = last completed ISO week (Mon–Sun).
- Copy the request's final nonempty `Model: <identifier>` after outer trim to reports/logs; else use
  `unavailable` and warn in both logs.
- Invent nothing; store no secrets. Modify only:

```text
latest-week.md; latest-week-zh.md
archive/YYYYWeekWW.md; archive/YYYYWeekWW-zh.md
knowledge-base/YYYYWeekWW.md
logs/generation.log; logs/runs/<run_id>.json
```

## Workflow

1. Inspect artifacts. Create collision-safe `run_id`; immediately log human START and
schema-v1 JSON (`running`): window/start/timezone/trigger/model. On failure finalize both logs with
stage/partial results.

2. Search broadly; verify via primary paper/author/institution/event sources. New/revised paper,
publication, correction/retraction, result, event, note, or survey qualifies only when its event is
in-window; record type/date.

AI-math: in-window reputable coverage + technical source + advance date; self-reports are
interested. Exclude product/opinion, uninspectable claims/marketing, and old results without a
material verified update. A news source is evidence and an index destination, never the naming
authority. Use the technical work/release title as the canonical English title; if none is usable,
write a neutral factual title. Never substitute a coverage headline or marketing slogan.

HA scope: substantive restriction/Kakeya/decoupling, oscillatory/FIO, smoothing, maximal/Radon/
singular, CZ/time-frequency, Carleson/Bochner–Riesz, wave packets/partitioning, related GMT/
dispersive PDE/variable coefficients; passing Fourier mentions fail.

Dedup: arXiv, DOI↔arXiv, normalized title/authors, semantics. Before ranking write the KB header
(window/generated/run/model/method) plus every plausible normalized candidate (raw noise: counts
only). Preserve same-week IDs, sources, dates, retrieval time. `<title>` is the canonical English
title, independent of which URL the report links. Each `### <ID> — <title>` has:

```markdown
- Chinese title: <faithful Chinese translation of the canonical English title>
- Status: selected-ha | selected-general | selected-ai-math | not-selected | verification-pending
- Rank: <list integer, or none>
- Area: ...
- Event: <type and date>
- Authors: ...
- Primary source: <URL>
- News source: <URL, or none>
- Corroborating sources: <URLs, or none>
- Identifiers: ...
- Source status: ...
- Credibility: high | medium | low
- Credibility rationale: ...
- Evidence summary: ...
- Mathematical meaning: ...
- Uncertainty and caveats: ...
- Scores: relevance <1-5>; importance <1-5>; novelty <1-5>; timeliness <1-5>; source reliability <1-5>; research interest <1-5>; confidence <1-5>
- Selection rationale: ...
- Retrieved: <zoned timestamp>
```

Paraphrase; separate provenance, correctness, significance, interpretation, uncertainty. Fame,
prestige, publicity, and AI branding are not evidence.

3. Post-assessment caps: HA/general/AI = 20/8/3. Never pad/duplicate; normally exclude low/pending.
Mirror final KB status/rank/scores/rationale and both display titles as `title_en`/`title_zh` in JSON
`ranking_audit` by ID.
Report only selected IDs in exact rank order. English display text uses the KB canonical title;
Chinese display text uses `Chinese title`. HA/general links → primary; AI index link → news and AI
briefing technical source → primary. Link choice never changes either display title.
Rank priorities: HA relevance/importance; general importance/novelty; AI verified substance,
genuine AI contribution, independent reporting, and research-practice impact.

4. `latest-week.md` structure:

```markdown
# HANews Weekly
Weekly report on YYYY-MM-DD — YYYY-MM-DD
Generated: YYYY-MM-DD HH:MM TZ
Model: <request model or unavailable>

## Harmonic Analysis — Top 20
## General Mathematics — Top 8
## AI in Mathematics Progress — Top 3
---
# Harmonic Analysis Briefing
# General Mathematics Briefing
# AI in Mathematics Progress Briefing
```

Indexes: numbered links only. Briefing caps = 5/3/3; bold exactly those links: `**[Title](URL)**`.
Briefings: authors/source/topics/event/importance/connections/caveats; AI adds technical source,
human guidance vs autonomy, credibility limits. Entries use `## <rank>. <Title>`.

5. Translate final English to `latest-week-zh.md`; translate every reader-visible item title in
both index and briefing, using the KB `Chinese title`. Do not copy an English or third-language
source headline merely to force parity. Preserve URLs, IDs, author names, formulas, standard
acronyms, selection/order, claims, and caveats; retain untranslated title fragments only when they
are proper names or notation. Archive by ISO week; before replacing another week's latest confirm
its archive. Same-week reruns update existing paths.

6. Human FINAL: run/timing/window/status/stage, request/runtime models, source outcomes, all counts,
outputs/validation/files, warnings/errors, branch/commit/push. Equivalent valid final schema-v1
JSON: IDs/project/times/timezone/window, models/sources/statistics/`ranking_audit`, KB output,
validation/warnings/errors/git/status.

7. Validate dates/links, KB coverage, 20/8/3 + 5/3/3 limits, bold rules, evidence/interpretation/
uncertainty separation, ISO archives, valid logs, and no secrets. Mechanically verify by ID that
KB↔JSON↔EN share rank/canonical English title/link/score and KB↔JSON↔ZH share rank/Chinese title/
link. EN↔ZH parity means the same IDs, ranks, URLs, claims, and bold positions—not byte-identical
display text. Fail validation if a Chinese index or briefing title was not translated, or if an AI
coverage headline replaced the technical/canonical title. Repair before publication.

Commit only run artifacts as `report: generate HANews YYYY Week WW [run:<run_id>]`; push current
branch or open a draft PR if inappropriate. Log Git failures; claim success only after publication.

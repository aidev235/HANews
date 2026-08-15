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
material verified update.

HA scope: substantive restriction/Kakeya/decoupling, oscillatory/FIO, smoothing, maximal/Radon/
singular, CZ/time-frequency, Carleson/Bochner–Riesz, wave packets/partitioning, related GMT/
dispersive PDE/variable coefficients; passing Fourier mentions fail.

Dedup: arXiv, DOI↔arXiv, normalized title/authors, semantics. Before ranking write the KB header
(window/generated/run/model/method) plus every plausible normalized candidate (raw noise: counts
only). Preserve same-week IDs, sources, dates, retrieval time. Each `### <ID> — <title>` has:

```markdown
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
Mirror final KB status/rank/scores/rationale in JSON `ranking_audit` by ID. Report only these entries
with exact order/title/link: HA/general → primary; AI index → news, briefing → technical.
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

5. Translate final English to `latest-week-zh.md`; preserve structure, selection/order, links,
names, claims, caveats. Archive by ISO week; before replacing another week's latest confirm its
archive. Same-week reruns update existing paths.

6. Human FINAL: run/timing/window/status/stage, request/runtime models, source outcomes, all counts,
outputs/validation/files, warnings/errors, branch/commit/push. Equivalent valid final schema-v1
JSON: IDs/project/times/timezone/window, models/sources/statistics/`ranking_audit`, KB output,
validation/warnings/errors/git/status.

7. Validate dates/links, KB coverage, KB↔JSON↔report ID/list/rank/title/link/score/order parity,
20/8/3 + 5/3/3 limits, bold rules, evidence/interpretation/uncertainty separation, EN↔ZH parity,
ISO archives, valid logs, no secrets. Repair before publication.

Commit only run artifacts as `report: generate HANews YYYY Week WW [run:<run_id>]`; push current
branch or open a draft PR if inappropriate. Log Git failures; claim success only after publication.

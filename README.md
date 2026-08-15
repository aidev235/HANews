# HANews

HANews is a prompt-driven weekly briefing on recent developments in harmonic analysis, general
mathematics, and AI-assisted mathematical progress. There is no application to install or scheduled
workflow to configure. Codex performs the research and updates the repository by following
[`Prompt.md`](Prompt.md).

## Generate a report

Open this repository in Codex and ask:

```text
Read `Prompt.md` and generate this week's HANews report. Model: CodeX-GPT5.6-sol-ultra-fast
```

For a backfill, add an ISO week or explicit date range:

```text
Read `Prompt.md` and generate HANews for 2026-W36.
```

Codex will search current authoritative sources, assess each plausible candidate's evidence,
credibility, and mathematical meaning in a durable knowledge base, choose the ranked lists from
that assessment—including up to three verified AI-in-mathematics news stories—write the English
and Chinese reports, preserve the weekly archive, create both required log formats, validate the
result, and commit/push when authorized.

## Repository layout

```text
Prompt.md                 Canonical instructions for every weekly run
latest-week.md            Latest English report
latest-week-zh.md         Latest Chinese report
archive/                  Reports named YYYYWeekWW.md and YYYYWeekWW-zh.md
knowledge-base/           Weekly candidate evidence, assessments, scores, and decisions
logs/generation.log       Append-only human-readable run history
logs/runs/                One structured JSON record per run
```

The English report is canonical. The Chinese report must preserve exactly the same selection,
ranking, links, mathematical claims, and uncertainty statements.

## Reporting convention

Unless the request specifies otherwise, a run covers the most recently completed ISO week
(Monday through Sunday) in `America/Chicago`. Quotas are maxima: up to 20 harmonic-analysis
items, 8 general-mathematics items, and 3 AI-in-mathematics news stories, with detailed briefings
for at most 5, 3, and 3.

## History

Weekly archives preserve named issues, while Git retains prior revisions. Weekly knowledge-base
files preserve the evidence and reasoning behind selected and omitted candidates in a format that
both people and AI systems can reuse. Each run also adds a human log entry and a versioned JSON
record containing its sources, model, counts, outputs, warnings, errors, validation result, and Git
association.

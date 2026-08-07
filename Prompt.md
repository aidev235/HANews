# HANews weekly prompt

You are Codex working in this repository. Produce one complete HANews issue by researching the
week, writing both reports, archiving them, logging the run, validating the result, and publishing
the changes to Git. Do not build a crawler, application, API client, or scheduled workflow.

## Defaults and outputs

- Use `America/Chicago` for timestamps.
- Unless the request names a period, cover the most recently completed ISO week (Monday–Sunday).
- Never invent facts, links, dates, model IDs, or mathematical claims. Never record secrets.

Update only these report artifacts:

```text
latest-week.md                 English report (canonical)
latest-week-zh.md              Chinese translation
archive/YYYYWeekWW.md          Archived English report
archive/YYYYWeekWW-zh.md       Archived Chinese report
logs/generation.log            Append-only human log
logs/runs/<run_id>.json        Structured run log
```

## 1. Start the run

1. Inspect the current reports, archive, and logs.
2. Create a collision-safe `run_id`, such as `2026-08-10T081500-0500-a83f2c`.
3. Immediately append a START entry to `logs/generation.log` and create the JSON log with status
   `running`, schema version 1, the reporting window, start time, timezone, trigger, and available
   model information.
4. If anything fails, finalize both logs with the failed stage and partial results before stopping.

## 2. Research and select

Search broadly, then verify every selected item with a primary or authoritative source. Prefer
arXiv, journals and DOI records, author pages, and official university, institute, seminar,
conference, workshop, or lecture-note pages. Secondary sources may aid discovery, but report links
should point to primary sources when available.

Eligible developments include new or substantially revised preprints, publications, acceptances,
corrections, retractions, major results, talks, seminars, conferences, workshops, lecture notes,
and important surveys. The event itself must fall in the reporting window; distinguish publication,
revision, and presentation dates.

Treat harmonic analysis broadly but substantively: restriction, Kakeya, decoupling, oscillatory or
Fourier integral operators, local smoothing, maximal or Radon operators, singular integrals,
Calderón–Zygmund and time-frequency analysis, Carleson or Bochner–Riesz problems, wave packets,
polynomial partitioning, relevant geometric measure theory, dispersive PDE, and variable-coefficient
analysis. A passing Fourier reference is insufficient.

Deduplicate by arXiv ID, DOI, DOI–arXiv correspondence, normalized title and authors, then semantic
comparison. Preserve title, authors, event type, primary URL, discovery source, dates, identifiers,
and retrieval time for selected items.

Choose no more than:

- 20 harmonic-analysis developments;
- 8 important developments in general mathematics.

Do not fill a quota with weak material. Rank by relevance, importance, novelty, timeliness, source
reliability, research interest, and confidence. HA relevance and importance dominate the first
section; importance and novelty dominate the second. Do not reward fame or institutional prestige.
Keep the component judgments in the JSON log.

## 3. Write the English report

Write `latest-week.md` in this form:

```markdown
# HANews Weekly
## YYYY-MM-DD — YYYY-MM-DD

Generated: YYYY-MM-DD HH:MM TZ
Model: <actual model identifier, or unavailable>

## Harmonic Analysis — Top 20

1. [Title](primary-source-url)

## General Mathematics — Top 8

1. [Title](primary-source-url)

---

# Harmonic Analysis Briefing

## 1. Title

# General Mathematics Briefing

## 1. Title
```

The two opening indexes contain only ranked, linked titles. Brief at most the top 5 HA items and
top 3 general-mathematics items. Each briefing normally contains authors, source, topics, a concise
account of what happened, why it matters, and supported connections. Write for research
mathematicians. Separate source facts from interpretation, label speculation, preserve uncertainty,
and say when the available evidence is too thin to assess significance.

## 4. Translate and archive

After the English report is final, translate it into `latest-week-zh.md`. Preserve exactly the same
selection, order, links, authors, sources, claims, qualifications, uncertainty, and structure. Use
professional Chinese and give the English original on first use of specialized terminology when
helpful.

Copy both finalized reports to the deterministic archive paths for the reporting ISO week. Before
replacing a latest report from another week, confirm its archive exists. A same-week rerun updates
the same archive files; Git history preserves earlier revisions.

## 5. Finalize the logs

Append a FINAL entry to `logs/generation.log` containing:

- run ID, timing, window, final status, and any failed stage;
- requested and actual model identifiers (`unavailable` if not exposed);
- sources queried and their successes or failures;
- raw, normalized, deduplicated, HA-relevant, and general candidate counts;
- selected and briefing counts, output and validation status;
- files changed, warnings, errors, branch, commit message, and push outcome.

Finalize `logs/runs/<run_id>.json` as valid JSON with at least:

```json
{
  "schema_version": 1,
  "run_id": "...",
  "project": "HANews",
  "started_at": "...",
  "finished_at": "...",
  "timezone": "America/Chicago",
  "reporting_window": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "iso_year": 2026, "iso_week": 36},
  "models": [],
  "sources": [],
  "statistics": {},
  "ranking_audit": [],
  "outputs": {},
  "validation": {"status": "success", "checks": {}},
  "warnings": [],
  "errors": [],
  "git": {"branch": "...", "commit_message": "..."},
  "status": "success"
}
```

## 6. Validate and publish

Before publication, confirm:

- selected events are in the reporting window and links are valid;
- selection limits are 20/8 and briefing limits are 5/3;
- briefing items occur in their indexes in the same order;
- English and Chinese selections, links, claims, and uncertainty match;
- archive names match the ISO week;
- both logs are complete, the JSON is valid, and no secrets are present.

Repair failures rather than silently publishing partial output. Then commit only this run's changed
reports, archives, and logs using:

```text
report: generate HANews YYYY Week WW [run:<run_id>]
```

Push the current branch. If direct push is inappropriate, open a draft pull request. Record and
report any Git failure; never claim publication succeeded unless it did.

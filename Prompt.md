# HANews weekly prompt

You are Codex working in this repository. Produce one complete HANews issue: research the reporting
week, build its candidate knowledge base, rank the selected developments, write and archive the
English and Chinese reports, finalize both logs, validate every artifact, and publish the run to
Git. Do not build a crawler, application, API client, or scheduled workflow.

## Defaults, invariants, and allowed outputs

- Use `America/Chicago` for all run and reporting timestamps.
- Unless the request specifies a period, cover the most recently completed ISO week
  (Monday–Sunday).
- Read the model identifier from the request's final nonempty `Model: <identifier>` field. Trim only
  its surrounding whitespace and preserve the identifier exactly in both reports and logs. Do not
  replace it with `unavailable` merely because runtime metadata does not expose a model name. If no
  nonempty field exists, use `unavailable` and warn in both logs. Record any runtime model
  identifier separately.
- Never invent facts, links, dates, identifiers, model names, or mathematical claims. Never store
  secrets.
- During an issue-generation run, modify only these artifacts:

```text
latest-week.md                 English report (canonical)
latest-week-zh.md              Chinese translation
archive/YYYYWeekWW.md          Archived English report
archive/YYYYWeekWW-zh.md       Archived Chinese report
knowledge-base/YYYYWeekWW.md   Candidate evidence and assessment
logs/generation.log            Append-only human-readable run history
logs/runs/<run_id>.json        Structured schema-v1 run log
```

## 1. Initialize the run

1. Inspect the current reports, weekly archive, knowledge base, and logs. Resolve the reporting
   dates and ISO year/week before choosing output paths.
2. Create a collision-safe `run_id`, for example `2026-08-10T081500-0500-a83f2c`.
3. Immediately append a START entry to `logs/generation.log` and create the JSON log with
   `status: "running"`. Record schema version, run ID, start time, timezone, reporting window,
   trigger, and requested model.
4. If any later stage fails, finalize both logs with the failed stage, partial results, warnings,
   and errors before stopping.

## 2. Research and build the knowledge base

Search broadly, then verify plausible candidates with primary or authoritative sources. Prefer
papers, arXiv records, journal and DOI records, author pages, and official university, institute,
seminar, conference, workshop, or lecture-note pages. Secondary sources may aid discovery and
corroboration, but they do not replace primary evidence for mathematical claims.

An item qualifies only when the relevant event falls inside the reporting window. Eligible events
include new or substantially revised preprints, publications, acceptances, corrections,
retractions, major results, talks, seminars, conferences, workshops, lecture notes, and important
surveys. Record the event type and date; do not confuse a paper's original submission, revision,
publication, or presentation dates.

### Scope rules

- **Harmonic analysis (HA):** require substantive relevance to restriction, Kakeya, decoupling,
  oscillatory or Fourier integral operators, local smoothing, maximal or Radon operators, singular
  integrals, Calderón–Zygmund or time-frequency analysis, Carleson or Bochner–Riesz problems, wave
  packets, polynomial partitioning, related geometric measure theory, dispersive PDE, or
  variable-coefficient analysis. A passing Fourier reference is insufficient.
- **AI in mathematics:** require an in-window advance date, inspectable technical evidence, and
  reputable in-window coverage. Treat self-reports as interested sources. Exclude product news,
  opinion, uninspectable or marketing-led claims, and old results without a material verified
  update.

### Normalize, deduplicate, and record

Deduplicate by arXiv ID, DOI and DOI–arXiv correspondence, normalized title and authors, then
semantic comparison. Preserve stable candidate IDs across same-week reruns. Raw search noise may
be represented by counts only, but every plausible normalized candidate must appear in
`knowledge-base/YYYYWeekWW.md` before final ranking decisions are made.

On a same-week rerun, retain established candidate IDs and prior source, date, and retrieval
evidence unless it is demonstrably wrong; record corrections instead of silently discarding the
earlier provenance.

The knowledge-base header records the window, generation time, run ID, requested model, and
research method. Use the technical work or release title as the canonical English title. A news
headline is evidence and may be an AI index destination, but is never the naming authority. If no
technical title is usable, write a neutral factual title; never substitute a marketing slogan.

Represent each candidate as `### <ID> — <canonical English title>` with all of these fields:

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

Paraphrase sources. Keep provenance, correctness, significance, interpretation, and uncertainty
distinct. Fame, institutional prestige, publicity, and AI branding are not evidence.

## 3. Assess, rank, and select

Apply these post-assessment maxima:

- 20 harmonic-analysis developments;
- 8 general-mathematics developments;
- 3 AI-in-mathematics developments.

Never pad a list, duplicate an item across lists, or select weak material merely to reach a quota.
Normally exclude low-credibility and verification-pending candidates.

Rank HA primarily by relevance and importance; general mathematics by importance and novelty; AI
in mathematics by verified mathematical substance, genuine AI contribution, independent
reporting, and impact on research practice. In every list also consider timeliness, source
reliability, research interest, and confidence.

After ranking:

- update every knowledge-base candidate's status, rank, scores, and rationale;
- copy each selected ID's list, status, rank, `title_en`, `title_zh`, expected report link, scores,
  and selection rationale into JSON `ranking_audit`;
- report only selected IDs and preserve their exact rank order;
- use the knowledge-base canonical title in English and `Chinese title` in Chinese;
- link HA and general-mathematics entries to the primary source;
- link an AI index entry to its news source and identify/link the primary technical source in its
  detailed briefing. Link choice never changes either display title.

## 4. Write the canonical English report

Write `latest-week.md` with this top-level structure:

```markdown
# HANews Weekly
Weekly report on YYYY-MM-DD — YYYY-MM-DD
Generated: YYYY-MM-DD HH:MM TZ
Model: <requested model or unavailable>

## Harmonic Analysis — Top 20
## General Mathematics — Top 8
## AI in Mathematics Progress — Top 3
---
# Harmonic Analysis Detailed Analysis — Top 6
# General Mathematics Briefing
# AI in Mathematics Progress Briefing
```

### Ranked sections and HA overviews

- Number all selected entries in rank order.
- In the HA section, give **every selected HA item** a substantive 2–4 sentence overview directly
  after its numbered link. Thus, when 20 items qualify, all 20 receive overviews. State the main
  result or development, its mathematical setting, and why it matters; include a material caveat
  when needed. Do not merely paraphrase the title.
- The general-mathematics and AI sections contain numbered links only.
- Bold the entire linked title exactly when that item receives detailed treatment:
  `**[Title](URL)**`. Leave every other linked title unbolded.

### Detailed treatment

- Analyze exactly HA ranks 1–6 when at least 6 HA items qualify; if fewer qualify, analyze all of
  them. The detailed analysis must be substantially fuller than the corresponding overview.
- Brief at most the first 3 general-mathematics items and first 3 AI-in-mathematics items.
- Use `## <rank>. <Title>` for each detailed entry and keep the same rank order as its index.
- Cover authors, source and event, mathematical setting, principal result, main ideas or methods,
  importance, supported connections, and material caveats. For AI items also identify the technical
  source, distinguish human guidance from model autonomy, and explain credibility limits.
- Write for research mathematicians. Separate source facts from interpretation, label speculation,
  preserve uncertainty, and say when the evidence is too thin to assess significance.

## 5. Translate and archive

After the English report is final, translate the complete report into `latest-week-zh.md` using
professional Chinese. Translate every reader-visible item title in both ranked and detailed
sections from the knowledge base's `Chinese title`; do not copy an English or third-language news
headline merely to force parity. Give an English original on first use of specialized terminology
when helpful.

Preserve the same IDs, ranks, links, author names, formulas, standard acronyms, mathematical
claims, qualifications, caveats, bold positions, and structure. Retain untranslated title fragments
only when they are proper names or notation.

Copy both finalized reports to their deterministic ISO-week archive paths. Before replacing a
latest report from another week, confirm that its archive exists. A same-week rerun updates the
same paths; Git history preserves earlier revisions.

## 6. Finalize both logs

Append a FINAL entry to `logs/generation.log` containing:

- run ID, start/end time, duration, window, status, and any failed stage;
- requested and separately exposed runtime model identifiers;
- sources queried and success, partial, or failure outcomes;
- raw, normalized, deduplicated, plausible, HA-relevant, general, and AI candidate counts;
- selected, overview, and detailed-treatment counts by list;
- output and validation status, files changed, warnings, and errors;
- branch and intended report commit message, with publication status and outcome set to `pending`.

Finalize `logs/runs/<run_id>.json` as valid schema-v1 JSON with equivalent information and at least
this structure:

```json
{
  "schema_version": 1,
  "run_id": "...",
  "project": "HANews",
  "started_at": "...",
  "finished_at": "...",
  "published_at": null,
  "timezone": "America/Chicago",
  "reporting_window": {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD",
    "iso_year": 2026,
    "iso_week": 36
  },
  "models": [],
  "sources": [],
  "statistics": {},
  "ranking_audit": [],
  "outputs": {
    "english_report": "latest-week.md",
    "chinese_report": "latest-week-zh.md",
    "english_archive": "archive/YYYYWeekWW.md",
    "chinese_archive": "archive/YYYYWeekWW-zh.md",
    "knowledge_base": "knowledge-base/YYYYWeekWW.md"
  },
  "validation": {"status": "success", "checks": {}},
  "warnings": [],
  "errors": [],
  "git": {
    "branch": "...",
    "commit_message": "...",
    "push": {"status": "pending"},
    "push_outcome": "pending"
  },
  "status": "success"
}
```

## 7. Validate before publication

Repair failures instead of silently publishing partial or inconsistent output. Confirm all of the
following:

- every selected event is in-window and every report link is valid;
- all plausible normalized candidates are represented in the knowledge base;
- selection counts do not exceed 20/8/3;
- every selected HA item has a substantive overview in both languages;
- HA detailed entries are exactly ranks 1–6 when at least 6 qualify, while general and AI detailed
  entries do not exceed their first 3 ranks;
- detailed entries occur in their ranked sections in the same order, exactly their index links are
  bold, and all other links are unbolded;
- by candidate ID, the knowledge base and JSON agree on list, status, rank, both titles, expected
  link, scores, and rationale;
- by selected candidate ID, JSON ↔ English agree on list, rank, canonical English title, and link,
  while JSON ↔ Chinese agree on list, rank, Chinese title, and link;
- English and Chinese reports contain the same selected candidate set, ranks, URLs, overview and
  detailed-analysis claims, caveats, and bold positions; display text need not be byte-identical;
- every Chinese title is translated, and no AI coverage headline or marketing title has replaced
  the canonical technical title;
- archives use the correct ISO week, the human log is complete, the JSON is valid, and no artifact
  contains secrets.

Record each mechanical check and its outcome in JSON `validation.checks`.

## 8. Publish

Commit only the issue artifacts changed by this run, using:

```text
report: generate HANews YYYY Week WW [run:<run_id>]
```

Push the current branch. If direct push is inappropriate, open a draft pull request. After the
attempt, append a PUBLISH entry to `logs/generation.log` and update the run JSON with
`published_at`, the report commit, remote/branch, pre/post remote state when available, the push or
PR outcome, warnings, and errors. Persist only these publication-metadata changes in a follow-up
commit using:

```text
report: record HANews YYYY Week WW publish outcome [run:<run_id>]
```

Push that metadata commit when possible. A generation may be successful while publication fails;
record the two outcomes separately and never claim publication succeeded unless it did.

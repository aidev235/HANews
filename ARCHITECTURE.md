# HANews architecture

## Design goals

HANews is a research-monitoring system, not a generic crawler. Its design prioritizes
provenance, mathematical fidelity, deterministic mechanics, auditability, recoverable writes,
and graceful partial failure. The MVP stays deliberately small: one authoritative structured
collector, one provider adapter, plain JSONL state, Markdown output, and Git-native history.

## Module boundaries

| Package | Boundary |
|---|---|
| `collectors` | Retrieve and parse source-owned metadata into events; never rank or summarize |
| `models` | Typed research-event, score, briefing, week, and run-log contracts |
| `pipeline` | Normalize, deduplicate, classify, rank, orchestrate, and validate |
| `llm` | Provider protocol, OpenAI Responses adapter, schemas, and narrow semantic tasks |
| `reporting` | Render canonical Markdown and manage collision-safe archives |
| `storage` | Atomic replacement, append-only item versions, and dual run logs |
| `git` | Stage explicit outputs, bounded commit protocol, and push failure handling |
| `config` | Load and validate centralized YAML behavior |

Dependencies point inward toward models and configuration. Collectors do not know about
reports, renderers do not retrieve sources, and the LLM adapter does not write files or choose
URLs. This prevents a single prompt or monolithic script from becoming an implicit pipeline.

## Core invariants

1. Every report item has source provenance and a syntactically valid primary URL.
2. The reporting window is an explicit ISO Monday–Sunday interval.
3. `canonical_id` identifies a work; `event_id` identifies a dated event about that work.
4. Separate event types are not collapsed merely because they concern the same work.
5. Every component score is retained in `[0,1]`; programmatic weights determine final rank.
6. Detailed items are subsets of their indexes, and both are bounded by configured maxima.
7. English selection is canonical; Chinese selection and URL order must be identical.
8. A run creates its JSON log before source access and records failure at the active stage.
9. Archive names depend only on the reporting interval; changed prior bytes are preserved.
10. Git stages only known generated paths and makes at most one report and one metadata commit.

## Configuration schemas

`settings.yaml` controls operations and paths. Paths are repository-relative. Count values are
upper bounds. `sources.yaml` is a list of collector records with an implementation name and
source-specific options. `topics.yaml` is editorial scope supplied to semantic assessment.
`ranking.yaml` maps component names to floats whose domain total must be 1. `models.yaml` maps
roles to provider, exact model, and supported request configuration.

Unknown collector types and absent model roles fail configuration loading. A future formal
configuration JSON Schema can be added without changing runtime interfaces.

## Event flow

1. Establish `run_id`, reporting window, JSON log, and human START record.
2. Query each enabled collector and retain success/failure separately.
3. Exclude out-of-window events, normalize metadata, and compute stable identities.
4. Deduplicate the same work/event using identifier and normalized-title/author evidence.
5. Ask the classifier for semantic components only; verify exact event-ID correspondence.
6. Deterministically select and rank the two domains with thresholds and quotas.
7. Brief only the configured leading subsets from verified metadata.
8. Render the English report; translate keyed finalized fields; render Chinese from the same
   ordered event objects.
9. Validate both structured selections and rendered link order.
10. Store event versions, state, latest reports, archives, and content-addressed revisions.
11. Finalize both logs and, when enabled, publish through the bounded Git protocol.

## Provenance and deduplication

Each source observation contributes a provenance record. The current merge hierarchy is exact
arXiv ID, exact DOI, then normalized title with author overlap. The preferred observation uses
source reliability, description completeness, and identifier completeness, while alternate
URLs, categories, identifiers, and provenance are merged.

DOI–arXiv mapping, fuzzy comparison, and semantic pair resolution are future enrichment
stages. The MVP prefers a visible duplicate to an unjustified merge. Any future ambiguous
merge must retain candidates, evidence, decision, model if used, and confidence.

## Ranking semantics

Semantic assessment and score aggregation are separate. The classifier cannot emit a final
rank. Source reliability comes from collector configuration; timeliness is derived from the
source date and window. The two domains have independent weights and thresholds. Deterministic
tie-breakers make reruns structurally stable.

Fame, affiliation, venue, and wording are excluded as direct components. Citation signals are
absent from the MVP because newly posted work has little citation history and naive counts
would systematically reward older and already prominent work.

## Translation semantics

English is finalized before translation. The translation request contains exactly the selected
event IDs and finalized English title/brief fields. The response must return each ID once and
only once. The renderer takes URLs, rank order, authors, and source identity from canonical
events—not from translated output. Rendered index URLs are then compared in order.

## Dual logging and recovery

The JSON record is written atomically at stage boundaries. The human log is append-only, so a
crash cannot erase earlier runs. Each enabled model call records task, provider, requested and
actual model, configuration, and call count. Fallbacks should add `fallback_reason` when a
future provider adapter implements them.

If atomic JSON replacement fails, the old checkpoint remains. If JSONL contains a malformed
line, generation stops with the exact line number rather than silently truncating history. If
an archive changes, the old bytes move to a content-addressed revision before replacement.

The Git protocol and its non-self-referential hash semantics are documented in the README.
The metadata commit is bounded and never attempts to include its own identity.

## Foreseeable failure modes

| Failure | Behavior |
|---|---|
| Source timeout or malformed Atom | Retry retrieval; record source error; continue only if another source succeeded |
| Source returns a wrong date | Exclude and warn; never stretch the week |
| Missing DOI or abstract | Retain the event; lower semantic certainty rather than invent data |
| Duplicate metadata | Merge only on documented evidence and preserve provenance |
| Invalid or refused model response | Fail the active semantic stage and finalize failure logs |
| Model fallback | Future adapter must record requested model, actual model, and reason |
| Empty/thin week | Publish fewer items; quotas remain maxima |
| English/Chinese drift | Ordered-link parity validation blocks publication |
| Existing archive differs | Preserve old content by hash, then replace canonical week atomically |
| Corrupt state | Stop with an explicit path/line; do not overwrite it |
| Commit or report push fails | Record locally, create bounded metadata commit, fail the run |
| Metadata push fails | Amend failure into that local metadata commit once, upload logs in Actions, stop |
| Concurrent scheduled runs | GitHub Actions concurrency serializes the workflow |

## Extension points

New structured sources implement `Collector`. Enrichment belongs between deduplication and
classification. New LLM providers implement `LLMClient.generate_json`; provider fallback must
remain observable. A database can replace JSONL behind `ItemStore` without changing event or
report contracts. New publication targets should consume validated artifacts and must not
change canonical English selection.


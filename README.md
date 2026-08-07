# HANews

HANews is an auditable weekly harmonic-analysis news pipeline. Deterministic code—not a
language model—owns identifiers, dates, provenance, selection, files, logs, and Git.

## Architecture and stage order

The CLI orders: initialize logs → configure → collect → normalize → deduplicate → classify
→ rank → threshold/limit → summarize → render English → translate finalized English →
validate → archive → commit/push → finalize logs. Narrow collector and model-provider
interfaces point inward to typed domain models; orchestration depends on them, never the
reverse. The current CLI exposes a deterministic `--dry-run`; production providers are
deliberately explicit wiring rather than hidden defaults.

arXiv is the MVP source. Its Atom snapshot, retrieval time, authoritative URL, names and
dates are retained. A canonical work identity is separate from event identity, preserving
new preprint, major revision, and journal-publication events. Metadata storage is JSONL and
contains metadata, snapshots, scores, decisions, and generated analysis—not paper bodies.

## Setup and use

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.lock
cp .env.example .env
pytest -q
hanews --dry-run --date 2026-08-07
```

`--no-push` is available for local publication and every configured failure returns nonzero.
The workflow uses UTC, a previous completed Monday–Sunday interval, concurrency control,
pinned actions, minimal write permission, a secret model key, deterministic checks, and
failed-log artifact retention.

## Configuration, trust, and ranking

All YAML keys are documented inline and strictly parsed (unknown fields fail). `settings`
defines timezone, limits, archives, logging and Git; `sources` defines enablement, categories,
timeouts, bounded retries and query options; `topics` defines vocabulary/thresholds;
`ranking` defines convex component weights/floors; and `models` separately assigns classifier,
importance, summary and translation roles/fallbacks.

Model responses have task-specific schemas. Requested/actual models and fallback reasons are
run-log fields. Prompts separate sourced claims, interpretation, and uncertainty. The merge
boundary rejects model-authored URLs, authors, identifiers, and dates. Final scores are a
visible weighted formula over retained components. Significance floors precede quotas; stable
date/event-ID tie-breaking makes reruns reproducible. Ambiguous duplicates remain separate
unless an explicit semantic-equivalence pair resolves them.

## Reports, weeks, archives, and recovery

English contains a linked index then at most five HA and three general briefings. Chinese is
only a translation of finalized English; validation checks identity, order, URLs, claims,
uncertainty and structure. An archive uses the ISO year/week of the interval end. Atomic
replacement updates latest files; a non-identical existing archive is rejected unless
`safe_update` is explicitly enabled. Atomic writes plus collision checks make reruns safe.

Every run initializes `logs/runs/<run-id>.json` before collection and appends delimited START
and FINAL records to `logs/generation.log`, including partial/failed runs. The versioned JSON
Schema is authoritative. It covers ISO identity, task models, sources, statistics, outputs,
validation, failures, Git and status; likely secrets are rejected/redacted.

Only `archive/`, latest reports, canonical generated data and committed logs may be staged.
`git.commit_hash` means the immutable report commit discovered after commit creation. Push and
other post-commit observations go in ignored `logs/receipts/`, preventing recursive metadata.
On failure, inspect the per-run record and workflow artifact, correct the adapter/configuration,
then rerun the same window; no differing archive is overwritten silently.

## Architectural review

The dependency direction is orchestration → narrow ports → deterministic domain/storage code.
Source failures are values, not empty successes. Atomic metadata/report/log writes and stable
selection support idempotence. Both log artifacts finalize through the CLI exception boundary.
No model interface can mutate authoritative provenance, and publication validation is a hard
gate. Tests cover boundaries, formulas, parity, collision, persistence, logging, secrets,
collector fixtures and mocked Git errors.

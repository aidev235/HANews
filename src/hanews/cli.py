"""Explicit orchestration. Failures after logger creation always finalize both logs."""
import argparse,uuid
from datetime import date,datetime,timezone
from pathlib import Path
from hanews.config import load_config
from hanews.models import RunRecord
from hanews.reporting.archive import window_for
from hanews.storage.run_log import RunLogger
def run(args)->int:
    root=Path(args.root).resolve(); settings,*_=load_config(root/"config"); window=window_for(date.fromisoformat(args.date) if args.date else date.today(),settings.timezone)
    record=RunRecord(run_id=str(uuid.uuid4()),started_at=datetime.now(timezone.utc),updated_at=datetime.now(timezone.utc),timezone=settings.timezone,reporting_window=window,trigger=args.trigger)
    logger=RunLogger(root/"logs",record)
    try:
        logger.update(stage="configured")
        # Network/model/publication adapters are intentionally invoked by deployments; dry-run proves configuration and logging.
        if not args.dry_run: raise RuntimeError("live provider wiring is required; use --dry-run for deterministic validation")
        logger.finalize("success");return 0
    except Exception as exc:
        logger.finalize("failed",record.stage,str(exc));return 1
def main(argv=None)->int:
    p=argparse.ArgumentParser();p.add_argument("--root",default=".");p.add_argument("--date");p.add_argument("--trigger",default="manual");p.add_argument("--dry-run",action="store_true");p.add_argument("--no-push",action="store_true")
    return run(p.parse_args(argv))
if __name__=="__main__":raise SystemExit(main())

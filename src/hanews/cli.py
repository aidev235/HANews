from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hanews.config import load_config
from hanews.llm.client import OpenAIResponsesClient
from hanews.models.run import ReportingWindow
from hanews.pipeline.orchestrator import GenerationPipeline


def _week(value: str) -> tuple[int, int]:
    normalized = value.upper().replace("W", "-").replace("--", "-")
    try:
        year_text, week_text = normalized.split("-", 1)
        year, week = int(year_text), int(week_text)
        ReportingWindow.from_iso_week(year, week)
        return year, week
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("Week must look like 2026-W36") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hanews")
    parser.add_argument("--root", type=Path, help="Repository root (normally auto-detected)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate a weekly report")
    generate.add_argument(
        "--week",
        type=_week,
        help="ISO reporting week, e.g. 2026-W36; defaults to the previous completed week",
    )
    generate.add_argument(
        "--no-git", action="store_true", help="Generate and validate without committing or pushing"
    )

    subparsers.add_parser("window", help="Print the default reporting window")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        config = load_config(arguments.root)
        if arguments.command == "window":
            window = ReportingWindow.previous_complete_week(timezone=config.timezone)
            print(
                f"{window.iso_year}-W{window.iso_week:02d}: "
                f"{window.start.isoformat()} -- {window.end.isoformat()}"
            )
            return 0
        if arguments.week:
            window = ReportingWindow.from_iso_week(*arguments.week)
        else:
            window = ReportingWindow.previous_complete_week(timezone=config.timezone)
        pipeline = GenerationPipeline(config, OpenAIResponsesClient())
        record = pipeline.run(window, publish_git=not arguments.no_git)
        print(f"HANews run {record.run_id} completed with status {record.status}")
        return 0
    except Exception as exc:
        print(f"HANews failed: {exc}", file=sys.stderr)
        return 1

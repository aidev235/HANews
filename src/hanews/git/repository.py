from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterable

from hanews.models.run import RunRecord
from hanews.storage.run_log import DualRunLogger


class GitPublishError(RuntimeError):
    pass


class GitRepository:
    """Explicit-path Git publication with a bounded two-commit logging protocol."""

    def __init__(self, root: Path, settings: dict[str, object]) -> None:
        self.root = root
        self.remote = str(settings.get("remote", "origin"))
        self.expected_branch = str(settings.get("branch", "main"))
        self.auto_push = bool(settings.get("auto_push", True))
        self.report_template = str(settings["report_commit_template"])
        self.metadata_template = str(settings["metadata_commit_template"])

    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ)
        environment.setdefault("GIT_TERMINAL_PROMPT", "0")
        process = subprocess.run(
            ["git", *args],
            cwd=self.root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if check and process.returncode:
            detail = process.stderr.strip() or process.stdout.strip()
            raise GitPublishError(f"git {' '.join(args)} failed: {detail}")
        return process

    def _relative_paths(self, paths: Iterable[Path]) -> list[str]:
        values: list[str] = []
        for path in paths:
            resolved = path.resolve()
            try:
                relative = resolved.relative_to(self.root.resolve())
            except ValueError as exc:
                raise GitPublishError(f"Refusing to stage path outside repository: {path}") from exc
            values.append(relative.as_posix())
        return sorted(set(values))

    def _commit(self, paths: list[str], message: str, *, amend: bool = False) -> str:
        self._run("add", "--", *paths)
        staged = self._run("diff", "--cached", "--quiet", check=False)
        if staged.returncode == 0:
            return self._run("rev-parse", "HEAD").stdout.strip()
        if staged.returncode != 1:
            raise GitPublishError("Could not inspect staged Git changes")
        commit_args = ("--amend", "--no-edit") if amend else ("-m", message)
        self._run(
            "-c",
            f"user.name={os.getenv('HANEWS_GIT_AUTHOR_NAME', 'HANews Bot')}",
            "-c",
            "user.email="
            f"{os.getenv('HANEWS_GIT_AUTHOR_EMAIL', 'hanews-bot@users.noreply.github.com')}",
            "commit",
            *commit_args,
        )
        return self._run("rev-parse", "HEAD").stdout.strip()

    def publish(
        self,
        *,
        record: RunRecord,
        logger: DualRunLogger,
        generated_paths: Iterable[Path],
    ) -> str:
        branch = self._run("branch", "--show-current").stdout.strip()
        if not branch:
            raise GitPublishError("Refusing to publish from a detached HEAD")
        if branch != self.expected_branch:
            raise GitPublishError(
                f"Configured branch is {self.expected_branch!r}, but checkout is {branch!r}"
            )

        record.git.update(
            {
                "commit_attempted": True,
                "remote": self.remote,
                "branch": branch,
            }
        )
        report_message = self.report_template.format(
            year=record.reporting_window["iso_year"],
            week=record.reporting_window["iso_week"],
            run_id=record.run_id,
        )
        record.git["commit_message"] = report_message
        paths = self._relative_paths(generated_paths)
        report_hash = self._commit(paths, report_message)
        record.git["commit_success"] = True
        record.git["commit_hash"] = report_hash
        if not self.auto_push:
            logger.append_git_result("report committed locally; automatic push is disabled")
            metadata_message = self.metadata_template.format(run_id=record.run_id)
            self._commit(
                self._relative_paths([logger.human_path, logger.json_path]), metadata_message
            )
            return report_hash
        record.git["push_attempted"] = True

        first_push = self._run("push", self.remote, f"HEAD:{branch}", check=False)
        if first_push.returncode:
            record.git["push_success"] = False
            detail = first_push.stderr.strip() or first_push.stdout.strip()
            record.errors.append({"stage": "git_push", "type": "GitPublishError", "message": detail})
            logger.append_git_result(f"report push failed: {detail}")
            metadata_message = self.metadata_template.format(run_id=record.run_id)
            self._commit(
                self._relative_paths([logger.human_path, logger.json_path]), metadata_message
            )
            raise GitPublishError(f"Report commit was created locally, but push failed: {detail}")

        record.git["push_success"] = True
        logger.append_git_result("report commit pushed; finalizing run metadata")
        metadata_message = self.metadata_template.format(run_id=record.run_id)
        metadata_paths = self._relative_paths([logger.human_path, logger.json_path])
        self._commit(metadata_paths, metadata_message)
        metadata_push = self._run("push", self.remote, f"HEAD:{branch}", check=False)
        if metadata_push.returncode:
            detail = metadata_push.stderr.strip() or metadata_push.stdout.strip()
            record.git["push_success"] = False
            record.errors.append(
                {"stage": "git_metadata_push", "type": "GitPublishError", "message": detail}
            )
            logger.append_git_result(f"metadata push failed: {detail}")
            self._commit(metadata_paths, metadata_message, amend=True)
            raise GitPublishError(
                "Report commit reached the remote, but metadata finalization did not: " + detail
            )
        return report_hash

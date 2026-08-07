from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

from hanews.collectors.base import Collector, CollectorResult
from hanews.config import ModelConfig, load_config
from hanews.llm.client import LLMResponse
from hanews.models.run import ReportingWindow
from hanews.pipeline.orchestrator import GenerationPipeline
from tests.helpers import make_event


class FakeCollector(Collector):
    name = "fixture"

    def collect(self, window: ReportingWindow, retrieved_at: str) -> CollectorResult:
        ha = make_event(event_id="ha", canonical_id="ha-work")
        general = make_event(
            title="A major result in algebra",
            event_id="general",
            canonical_id="general-work",
            arxiv_id="2608.00002",
            coverage="general_mathematics",
            relationship="unrelated",
        )
        return CollectorResult(source_name=self.name, status="success", events=[ha, general])


class FakeLLM:
    def generate_json(
        self,
        *,
        task: str,
        model: ModelConfig,
        instructions: str,
        payload: dict[str, Any],
        schema: dict[str, Any],
    ) -> LLMResponse:
        if task == "classify_research_events":
            assessments = []
            for item in payload["items"]:
                general = "algebra" in item["title"].casefold()
                assessments.append(
                    {
                        "event_id": item["event_id"],
                        "coverage": "general_mathematics" if general else "harmonic_analysis",
                        "ha_relationship": "unrelated" if general else "direct",
                        "topics": ["Algebra"] if general else ["Fourier restriction"],
                        "harmonic_analysis_relevance": 0.05 if general else 0.95,
                        "mathematical_importance": 0.85,
                        "novelty": 0.75,
                        "research_interest": 0.8,
                        "confidence": 0.9,
                        "rationale": "Fixture assessment.",
                    }
                )
            data = {"assessments": assessments}
        elif task == "write_research_briefings":
            data = {
                "briefings": [
                    {
                        "event_id": item["event_id"],
                        "brief": "Evidence-bounded brief.",
                        "why_it_matters": "Evidence-bounded importance.",
                        "connections": "A supported connection.",
                    }
                    for item in payload["items"]
                ]
            }
        elif task == "translate_finalized_report_fields_zh":
            data = {
                "translations": [
                    {
                        "event_id": item["event_id"],
                        "title": "中译：" + item["title"],
                        "topics": ["中译主题（English term）"],
                        "brief": "中译简报。" if item["brief"] else "",
                        "why_it_matters": "中译重要性。" if item["why_it_matters"] else "",
                        "connections": "中译关联。" if item["connections"] else "",
                    }
                    for item in payload["finalized_english_fields"]
                ]
            }
        else:
            raise AssertionError(f"Unexpected task {task}")
        return LLMResponse(data, model.model, model.model, model.provider, "fixture-response")


class PipelineIntegrationTests(unittest.TestCase):
    def test_pipeline_writes_valid_bilingual_outputs_and_logs(self) -> None:
        source_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(source_root / "config", root / "config")
            shutil.copytree(source_root / "prompts", root / "prompts")
            config = load_config(root)
            pipeline = GenerationPipeline(config, FakeLLM(), [FakeCollector()])
            record = pipeline.run(ReportingWindow.from_iso_week(2026, 32), publish_git=False)
            self.assertEqual(record.status, "success")
            self.assertTrue((root / "latest-week.md").exists())
            self.assertTrue((root / "latest-week-zh.md").exists())
            self.assertTrue((root / "archive/2026Week32.md").exists())
            self.assertTrue((root / "logs/generation.log").exists())
            self.assertEqual(len(list((root / "logs/runs").glob("*.json"))), 1)
            self.assertEqual(record.statistics["ha_selected"], 1)
            self.assertEqual(record.statistics["general_math_selected"], 1)


if __name__ == "__main__":
    unittest.main()


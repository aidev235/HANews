from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigurationError(ValueError):
    """Raised when required configuration is absent or inconsistent."""


@dataclass(frozen=True)
class ModelConfig:
    role: str
    provider: str
    model: str
    temperature: float = 0.0


@dataclass(frozen=True)
class AppConfig:
    root: Path
    raw: dict[str, Any]
    sources: list[dict[str, Any]]
    topics: dict[str, Any]
    ranking: dict[str, dict[str, float]]
    models: dict[str, ModelConfig]

    @property
    def timezone(self) -> str:
        return str(self.raw["project"]["timezone"])

    def path(self, configured: str) -> Path:
        return self.root / configured


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigurationError(f"Required configuration file does not exist: {path}")
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle) or {}
    if not isinstance(value, dict):
        raise ConfigurationError(f"Top level of {path} must be a mapping")
    return value


def discover_root(explicit: Path | None = None) -> Path:
    if explicit:
        return explicit.resolve()
    if env_root := os.getenv("HANEWS_ROOT"):
        return Path(env_root).resolve()
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists() and (candidate / "config").is_dir():
            return candidate
    raise ConfigurationError("Could not locate the HANews project root; set HANEWS_ROOT")


def load_config(root: Path | None = None) -> AppConfig:
    project_root = discover_root(root)
    config_dir = project_root / os.getenv("HANEWS_CONFIG_DIR", "config")
    settings = _load_yaml(config_dir / "settings.yaml")
    sources_doc = _load_yaml(config_dir / "sources.yaml")
    topics = _load_yaml(config_dir / "topics.yaml")
    ranking_doc = _load_yaml(config_dir / "ranking.yaml")
    models_doc = _load_yaml(config_dir / "models.yaml")

    required_sections = {"project", "report", "archive", "logging", "storage", "git"}
    missing = required_sections - settings.keys()
    if missing:
        raise ConfigurationError(f"settings.yaml is missing sections: {sorted(missing)}")

    source_list = sources_doc.get("sources")
    if not isinstance(source_list, list):
        raise ConfigurationError("sources.yaml must contain a sources list")

    models: dict[str, ModelConfig] = {}
    for role, value in models_doc.get("models", {}).items():
        if not isinstance(value, dict) or not value.get("provider") or not value.get("model"):
            raise ConfigurationError(f"Invalid model configuration for {role}")
        models[role] = ModelConfig(
            role=role,
            provider=str(value["provider"]),
            model=str(value["model"]),
            temperature=float(value.get("temperature", 0.0)),
        )

    expected_roles = {"classifier", "summarizer", "translator", "ranker"}
    if missing_roles := expected_roles - models.keys():
        raise ConfigurationError(f"models.yaml is missing roles: {sorted(missing_roles)}")

    ranking = ranking_doc
    for domain in ("harmonic_analysis", "general_mathematics"):
        weights = ranking.get(domain)
        if not isinstance(weights, dict):
            raise ConfigurationError(f"ranking.yaml is missing {domain}")
        total = sum(float(value) for value in weights.values())
        if abs(total - 1.0) > 1e-9:
            raise ConfigurationError(f"Ranking weights for {domain} sum to {total}, not 1")

    return AppConfig(
        root=project_root,
        raw=settings,
        sources=source_list,
        topics=topics,
        ranking=ranking,
        models=models,
    )


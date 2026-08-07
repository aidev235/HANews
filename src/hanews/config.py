"""Strict YAML configuration loading; schemas are the Pydantic models below."""
from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel, ConfigDict, Field

class ConfigModel(BaseModel): model_config=ConfigDict(extra="forbid")
class Settings(ConfigModel):
    timezone:str; report_limits:dict[str,int]; archive:dict[str,Any]; logging:dict[str,str]; git:dict[str,Any]
class Collector(ConfigModel):
    enabled:bool; categories:list[str]; timeout_seconds:float=Field(gt=0); retries:int=Field(ge=0,le=10); query:dict[str,Any]
class Sources(ConfigModel): collectors:dict[str,Collector]
class Topics(ConfigModel): vocabulary:list[str]; adjacent:list[str]; thresholds:dict[str,float]
class RankingProfile(ConfigModel): weights:dict[str,float]; minimum_score:float
class Ranking(ConfigModel): ha:RankingProfile; general:RankingProfile
class ModelRole(ConfigModel): provider:str; model:str; fallback:str|None=None
class Models(ConfigModel): classifier:ModelRole; importance:ModelRole; summarization:ModelRole; translation:ModelRole

def load_config(directory: Path)->tuple[Settings,Sources,Topics,Ranking,Models]:
    def read(name:str)->dict: return yaml.safe_load((directory/name).read_text())
    return (Settings.model_validate(read("settings.yaml")), Sources.model_validate(read("sources.yaml")),
            Topics.model_validate(read("topics.yaml")), Ranking.model_validate(read("ranking.yaml")),
            Models.model_validate(read("models.yaml")))

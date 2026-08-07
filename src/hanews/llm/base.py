from abc import ABC,abstractmethod
from typing import TypeVar
from pydantic import BaseModel,ConfigDict
T=TypeVar("T",bound=BaseModel)
class RelevanceResponse(BaseModel): model_config=ConfigDict(extra="forbid"); category:str; rationale:str; uncertainty:str|None=None
class ImportanceResponse(BaseModel): model_config=ConfigDict(extra="forbid"); significance:float; novelty:float; breadth:float; sourced_claims:list[str]
class SummaryResponse(BaseModel): model_config=ConfigDict(extra="forbid"); summary:str; interpretation:str; uncertainty:str
class TranslationResponse(BaseModel): model_config=ConfigDict(extra="forbid"); markdown:str; item_ids:list[str]
class Provider(ABC):
    @abstractmethod
    def invoke(self,task:str,prompt:str,response_type:type[T],model:str)->tuple[T,str]: ...
AUTHORITATIVE_FIELDS=frozenset({"url","authors","identifiers","dates"})
def merge_analysis(metadata:dict,analysis:dict)->dict:
    if AUTHORITATIVE_FIELDS&analysis.keys(): raise ValueError("model attempted to replace authoritative metadata")
    return metadata|{"analysis":analysis}

from abc import ABC, abstractmethod
from hanews.models import ReportingWindow, SourceResult
class Collector(ABC):
    name: str
    @abstractmethod
    def collect(self, window: ReportingWindow)->SourceResult: ...

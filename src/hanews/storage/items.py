import json
from pathlib import Path
from hanews.storage.atomic import write
class ItemStore:
    """Append-friendly JSONL store; rewrites atomically to prevent torn records."""
    def __init__(self,path:Path):self.path=path
    def append(self,record:dict)->None:
        existing=self.path.read_text() if self.path.exists() else ""
        write(self.path,existing+json.dumps(record,ensure_ascii=False,sort_keys=True,default=str)+"\n")
    def read(self):
        return [json.loads(x) for x in self.path.read_text().splitlines()] if self.path.exists() else []

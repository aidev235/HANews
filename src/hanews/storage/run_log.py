import re
from datetime import datetime,timezone
from pathlib import Path
from hanews.models import RunRecord
from hanews.storage.atomic import write
MASK=re.compile(r"(token|key|password)(['\" ]*[:=]['\" ]*)([^, }]+)",re.I)
def redact(value:str)->str:return MASK.sub(r"\1\2[REDACTED]",value)
class RunLogger:
    def __init__(self,root:Path,record:RunRecord):
        self.root,self.record=root,record; self.run_path=root/"runs"/f"{record.run_id}.json"; self.generation=root/"generation.log"
        self._save(); self._append("START")
    def _save(self):
        self.record.updated_at=datetime.now(timezone.utc); write(self.run_path,redact(self.record.model_dump_json(indent=2)))
    def _append(self,label):
        old=self.generation.read_text() if self.generation.exists() else ""
        write(self.generation,old+f"\n--- {label} {self.record.run_id} {datetime.now(timezone.utc).isoformat()} ---\n"+redact(self.record.model_dump_json())+"\n")
    def update(self,**changes):
        for k,v in changes.items():setattr(self.record,k,v)
        self._save()
    def finalize(self,status:str,failed_stage:str|None=None,error:str|None=None):
        self.record.status=status; self.record.failed_stage=failed_stage
        if error:self.record.errors.append(redact(error))
        self._save();self._append("FINAL")

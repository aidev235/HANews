import re
from pathlib import Path
from urllib.parse import urlparse
from hanews.models import ReportingWindow,ValidationResult
SECRET=re.compile(r"(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|(?:api[_-]?key|token|password)\s*[:=]\s*\S+)",re.I)
def contains_secret(text:str)->bool:return bool(SECRET.search(text))
def validate_url(value:str)->bool:
    p=urlparse(value); return p.scheme in {"http","https"} and bool(p.netloc)
def validate_publication(english:dict,chinese:dict,window:ReportingWindow,archive_name:str,log_paths:list[Path],models:list,limits=(5,3))->list[ValidationResult]:
    tests={"dates":window.start<=window.end,"counts":len(english.get("ha",[]))<=limits[0] and len(english.get("general",[]))<=limits[1],
      "urls":all(validate_url(x["url"]) for k in ("ha","general") for x in english.get(k,[])),
      "translation_parity":[x["id"] for k in ("ha","general") for x in english.get(k,[])]==[x["id"] for k in ("ha","general") for x in chinese.get(k,[])],
      "archive":archive_name==f"{window.iso_year}-W{window.iso_week:02d}.md","logs":all(p.exists() for p in log_paths),
      "models":all(m.actual_model for m in models),"secrets":not contains_secret(str(english)+str(chinese))}
    return [ValidationResult(name=k,passed=v,message="" if v else f"{k} invariant failed") for k,v in tests.items()]

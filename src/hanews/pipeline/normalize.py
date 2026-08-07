import re, unicodedata
from urllib.parse import urlsplit,urlunsplit
from hanews.models import ResearchEvent
def whitespace(value:str)->str: return " ".join(unicodedata.normalize("NFKC",value).split())
def doi(value:str|None)->str|None:
    if not value:return None
    return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)","",value.strip(),flags=re.I).lower()
def title_key(value:str)->str: return re.sub(r"[^a-z0-9]+"," ",whitespace(value).casefold()).strip()
def url(value:str)->str:
    p=urlsplit(value.strip()); return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip("/"),p.query,""))
def event(item:ResearchEvent)->ResearchEvent:
    item.normalized={"title":title_key(item.title),"authors":[whitespace(a).casefold() for a in item.authors],"url":url(item.url),"doi":doi(item.work.doi)}
    return item

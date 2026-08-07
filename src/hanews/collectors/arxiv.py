"""arXiv Atom collector with bounded network behavior and lossless snapshots."""
from datetime import datetime, timezone
from time import sleep
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
from hanews.collectors.base import Collector
from hanews.models import *

ATOM="{http://www.w3.org/2005/Atom}"
class ArxivCollector(Collector):
    name="arxiv"
    def __init__(self,categories:list[str],timeout:float=20,retries:int=2,user_agent:str="HANews/0.1 (+https://github.com/hanews)"):
        self.categories,self.timeout,self.retries,self.user_agent=categories,timeout,retries,user_agent
    def collect(self,window:ReportingWindow)->SourceResult:
        query=" OR ".join(f"cat:{x}" for x in self.categories)
        url="https://export.arxiv.org/api/query?"+urlencode({"search_query":query,"start":0,"max_results":200,"sortBy":"submittedDate"})
        error=None
        for attempt in range(1,self.retries+2):
            try:
                with urlopen(Request(url,headers={"User-Agent":self.user_agent}),timeout=self.timeout) as r: data=r.read()
                return SourceResult(source=self.name,ok=True,items=self.parse(data,window,url),attempts=attempt)
            except Exception as exc:
                error=f"{type(exc).__name__}: {exc}"
                if attempt<=self.retries: sleep(min(2**(attempt-1),4))
        return SourceResult(source=self.name,ok=False,attempts=self.retries+1,error=error)
    @staticmethod
    def parse(data:bytes,window:ReportingWindow,source_url:str="fixture")->list[ResearchEvent]:
        root=ET.fromstring(data); out=[]
        for e in root.findall(ATOM+"entry"):
            raw={c.tag.split("}")[-1]:c.text for c in e}; published=datetime.fromisoformat(raw["published"].replace("Z","+00:00"))
            if not(window.start<=published.date()<=window.end): continue
            identifier=raw["id"].rstrip("/").split("/")[-1]; base=identifier.split("v")[0]
            authors=[a.findtext(ATOM+"name","") for a in e.findall(ATOM+"author")]
            out.append(ResearchEvent(event_id=f"arxiv:{identifier}",event_type=EventType.NEW_PREPRINT,
              work=WorkIdentity(canonical_id=f"arxiv:{base}",arxiv_id=base),title=raw["title"],authors=authors,
              url=raw["id"],occurred_at=published,provenance=[Provenance(source="arxiv",retrieved_at=datetime.now(timezone.utc),source_url=source_url,snapshot=raw)]))
        return out

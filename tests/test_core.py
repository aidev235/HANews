from datetime import date,datetime,timezone
from pathlib import Path
import pytest
from hanews.models import *
from hanews.reporting.archive import window_for,publish
from hanews.pipeline.normalize import whitespace,doi,event
from hanews.pipeline.deduplicate import deduplicate
from hanews.pipeline.rank import score,select
from hanews.collectors.arxiv import ArxivCollector
from hanews.storage.atomic import write
def item(eid="x",kind=EventType.NEW_PREPRINT):
 return event(ResearchEvent(event_id=eid,event_type=kind,work=WorkIdentity(canonical_id="w",arxiv_id="1"),title=" A  title ",authors=["A.  B"],url="https://x.test/a/",occurred_at=datetime(2026,8,4,tzinfo=timezone.utc),provenance=[Provenance(source="x",retrieved_at=datetime.now(timezone.utc),source_url="x")]))
def test_iso_boundary():
 w=window_for(date(2021,1,4));assert (w.iso_year,w.iso_week,w.start,w.end)==(2020,53,date(2020,12,28),date(2021,1,3))
def test_normalization_and_event_identity():
 assert whitespace(" a  b ")=="a b" and doi("https://doi.org/ABC")=="abc"
 assert len(deduplicate([item("a"),item("b",EventType.MAJOR_REVISION)]))==2
 assert len(deduplicate([item("a"),item("b")]))==1
def test_rank_threshold_before_quota_and_tie():
 c=lambda n:RankingComponents(topical_relevance=n,significance=n,novelty=n,breadth=n,source_confidence=n)
 weights={k:.2 for k in ("topical_relevance","significance","novelty","breadth","source_confidence")}
 assert score(c(.7),weights)==.7
 rows=select([(item("b"),c(.8)),(item("a"),c(.8)),(item("low"),c(.2))],weights,.5,5)
 assert [x[0].event_id for x in rows]==["a","b"]
def test_archive_collision_and_atomic(tmp_path):
 a=tmp_path/"a";latest=tmp_path/"l";publish("one",a,latest)
 with pytest.raises(FileExistsError):publish("two",a,latest)
 write(latest,"three");assert latest.read_text()=="three"
def test_arxiv_fixture():
 w=ReportingWindow(start=date(2026,8,3),end=date(2026,8,9),timezone="UTC",iso_year=2026,iso_week=32)
 rows=ArxivCollector.parse((Path(__file__).parent/"fixtures/arxiv.xml").read_bytes(),w)
 assert rows[0].work.arxiv_id=="2608.00001" and rows[0].title.startswith(" Fourier")

from hanews.models import ResearchEvent
def _overlap(a,b):
    x,y=set(a.normalized.get("authors",[])),set(b.normalized.get("authors",[])); return len(x&y)/max(1,min(len(x),len(y)))
def definite(a:ResearchEvent,b:ResearchEvent)->bool:
    # Event identity is deliberately part of the strongest arXiv match.
    if a.event_type==b.event_type and a.work.arxiv_id and a.work.arxiv_id==b.work.arxiv_id:return True
    if a.work.doi and b.work.doi and a.normalized.get("doi")==b.normalized.get("doi"):return True
    if set(a.work.correspondence)&set(b.work.correspondence):return True
    return a.normalized.get("title")==b.normalized.get("title") and _overlap(a,b)>=.5
def deduplicate(items:list[ResearchEvent],semantic_equivalences:set[frozenset[str]]|None=None)->list[ResearchEvent]:
    kept=[]; semantic_equivalences=semantic_equivalences or set()
    for item in items:
        match=next((x for x in kept if definite(item,x) or frozenset((item.event_id,x.event_id)) in semantic_equivalences),None)
        if not match: kept.append(item)
        else: match.provenance.extend(item.provenance)
    return kept

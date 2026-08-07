from hanews.models import Relevance,ResearchEvent
def classify(item:ResearchEvent,vocabulary:list[str],adjacent:list[str])->Relevance:
    text=(item.title+" "+str(item.provenance[0].snapshot.get("summary",""))).casefold()
    direct=sum(term.casefold() in text for term in vocabulary)
    near=sum(term.casefold() in text for term in adjacent)
    return Relevance.DIRECT_HA if direct>=2 else Relevance.STRONGLY_ADJACENT if direct or near>=2 else Relevance.SUPERFICIAL if near else Relevance.UNRELATED

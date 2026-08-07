from hanews.models import RankingComponents,ResearchEvent
def score(c:RankingComponents,weights:dict[str,float])->float:
    if abs(sum(weights.values())-1)>1e-9: raise ValueError("ranking weights must sum to 1")
    c.final_score=round(sum(getattr(c,k)*v for k,v in weights.items()),6); return c.final_score
def select(rows:list[tuple[ResearchEvent,RankingComponents]],weights:dict[str,float],minimum:float,limit:int):
    eligible=[x for x in rows if score(x[1],weights)>=minimum]
    return sorted(eligible,key=lambda x:(-float(x[1].final_score or 0),x[0].occurred_at,x[0].event_id))[:limit]

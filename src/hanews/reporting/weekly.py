def build(ha:list[dict],general:list[dict])->dict:
    return {"ha":ha[:5],"general":general[:3]}
def translated(english:dict,translation:dict)->dict:
    """Translation must be made only after selection and retain immutable identity/order."""
    result={}
    for section in ("ha","general"):
        result[section]=[]
        for source,target in zip(english[section],translation[section],strict=True):
            if source["id"]!=target["id"] or source["url"]!=target["url"]:raise ValueError("translation changed identity or URL")
            result[section].append(target)
    return result

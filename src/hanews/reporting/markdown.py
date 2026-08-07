def render(report:dict,title:str="HANews Weekly")->str:
    items=report.get("ha",[])+report.get("general",[])
    lines=[f"# {title}","","## Index",*(f"- [{x['title']}]({x['url']})" for x in items),""]
    for heading,key in (("Harmonic Analysis","ha"),("General Mathematics","general")):
        lines += [f"## {heading}",""]
        for x in report.get(key,[]):lines += [f"### [{x['title']}]({x['url']})",x["briefing"],""]
    return "\n".join(lines).rstrip()+"\n"

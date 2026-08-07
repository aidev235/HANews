from datetime import date,timedelta
from pathlib import Path
from hanews.models import ReportingWindow
from hanews.storage.atomic import write
def window_for(day:date,timezone:str="UTC")->ReportingWindow:
    end=day-timedelta(days=day.weekday()+1);start=end-timedelta(days=6);iso=end.isocalendar()
    return ReportingWindow(start=start,end=end,timezone=timezone,iso_year=iso.year,iso_week=iso.week)
def archive_name(window:ReportingWindow,language:str="en")->str:
    suffix="-zh" if language=="zh" else "";return f"{window.iso_year}-W{window.iso_week:02d}{suffix}.md"
def publish(content:str,archive:Path,latest:Path,safe_update:bool=False):
    if archive.exists() and archive.read_text()!=content and not safe_update:raise FileExistsError(f"non-identical archive collision: {archive}")
    write(archive,content);write(latest,content)

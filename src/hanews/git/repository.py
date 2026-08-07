import subprocess
from pathlib import Path
from hanews.pipeline.validate import contains_secret
ALLOWED=("archive/","logs/generation.log","logs/runs/","latest-week.md","latest-week-zh.md","data/")
class GitError(RuntimeError):pass
class Repository:
    def __init__(self,root:Path):self.root=root
    def _run(self,args:list[str])->str:
        p=subprocess.run(["git",*args],cwd=self.root,text=True,capture_output=True)
        if p.returncode:raise GitError(f"git {' '.join(args)}: {p.stderr.strip()}")
        return p.stdout.strip()
    def publish(self,paths:list[str],message:str,push:bool=True)->str:
        if any(not any(p==a or p.startswith(a) for a in ALLOWED) for p in paths):raise GitError("staging path outside generated artifacts")
        if any((self.root/p).is_file() and contains_secret((self.root/p).read_text(errors="ignore")) for p in paths):raise GitError("secret-bearing artifact rejected")
        self._run(["add","--",*paths]);self._run(["commit","-m",message]);commit=self._run(["rev-parse","HEAD"])
        # The immutable report commit is returned; push observations belong in an ignored receipt.
        if push:self._run(["push"])
        return commit

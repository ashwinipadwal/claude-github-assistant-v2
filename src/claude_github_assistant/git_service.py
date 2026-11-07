import subprocess
from typing import Sequence
from .config import Settings
from .security import resolve_repository

class GitService:
    def __init__(self, settings: Settings): self.settings = settings

    def _run(self, repo_path: str, args: Sequence[str]) -> str:
        repo = resolve_repository(repo_path, self.settings)
        result = subprocess.run(["git", *args], cwd=repo, text=True,
            capture_output=True, timeout=120, check=False, shell=False)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result.stdout.strip()

    def status(self, repo): return self._run(repo, ["status", "--short", "--branch"])
    def branches(self, repo): return self._run(repo, ["branch", "--all", "--verbose"])
    def diff(self, repo, staged=False):
        return self._run(repo, ["diff", *(["--cached"] if staged else [])])
    def log(self, repo, limit=10):
        if not 1 <= limit <= 100: raise ValueError("limit must be 1..100")
        return self._run(repo, ["log", f"-{limit}", "--oneline", "--decorate"])
    def fetch(self, repo, remote="origin"):
        _atom(remote, "remote"); return self._run(repo, ["fetch", "--prune", remote])
    def create_branch(self, repo, branch, base=None):
        _ref(branch); args=["switch", "-c", branch]
        if base: _ref(base); args.append(base)
        return self._run(repo, args)
    def switch_branch(self, repo, branch):
        _ref(branch); return self._run(repo, ["switch", branch])
    def stage(self, repo, paths):
        _paths(paths); return self._run(repo, ["add", "--", *paths])
    def unstage(self, repo, paths):
        _paths(paths); return self._run(repo, ["restore", "--staged", "--", *paths])
    def commit(self, repo, message):
        if not message.strip(): raise ValueError("Commit message is required.")
        return self._run(repo, ["commit", "-m", message])
    def pull(self, repo, remote="origin", branch=None):
        _atom(remote, "remote"); args=["pull", "--ff-only", remote]
        if branch: _ref(branch); args.append(branch)
        return self._run(repo, args)
    def push(self, repo, remote="origin", branch=None, force_with_lease=False):
        _atom(remote, "remote"); args=["push"]
        if force_with_lease: args.append("--force-with-lease")
        args.append(remote)
        if branch: _ref(branch); args.append(branch)
        return self._run(repo, args)
    def rebase(self, repo, onto):
        _ref(onto); return self._run(repo, ["rebase", onto])
    def rebase_continue(self, repo): return self._run(repo, ["rebase", "--continue"])
    def rebase_abort(self, repo): return self._run(repo, ["rebase", "--abort"])
    def merge(self, repo, branch, no_ff=False):
        _ref(branch); return self._run(repo, ["merge", *(["--no-ff"] if no_ff else []), branch])
    def stash(self, repo, message=None):
        args=["stash", "push"]
        if message: args += ["-m", message]
        return self._run(repo, args)

def _ref(v):
    if (not v or v.startswith(("-", "/", ".")) or v.endswith(("/", ".")) or ".." in v
        or "//" in v or any(c in v for c in [" ", "\\\\", "~", "^", ":", "?", "*", "[", "@{"])):
        raise ValueError("Invalid Git ref.")
def _atom(v, label):
    if not v or v.startswith("-") or any(c.isspace() for c in v):
        raise ValueError(f"Invalid {label}.")
def _paths(paths):
    if not paths or any(not p or p.startswith("-") for p in paths):
        raise ValueError("Provide paths; paths beginning with '-' are not accepted.")

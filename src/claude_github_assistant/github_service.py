from urllib.parse import quote
import httpx
from .config import Settings

class GitHubService:
    def __init__(self, settings: Settings): self.settings = settings
    def _request(self, method, endpoint, **kwargs):
        if not self.settings.github_token:
            raise RuntimeError("Set GITHUB_TOKEN in .env to enable GitHub API tools.")
        headers={"Accept":"application/vnd.github+json",
                 "X-GitHub-Api-Version":"2022-11-28",
                 "Authorization":f"Bearer {self.settings.github_token}"}
        with httpx.Client(timeout=self.settings.github_api_timeout) as client:
            r=client.request(method, f"{self.settings.github_api_url}/{endpoint.lstrip('/')}",
                             headers=headers, **kwargs)
        if r.status_code >= 400:
            try: detail=r.json().get("message", r.text)
            except ValueError: detail=r.text
            raise RuntimeError(f"GitHub API {r.status_code}: {detail}")
        if r.status_code == 204 or not r.content:
            return {"status":"success","status_code":r.status_code}
        return r.json()
    @staticmethod
    def _repo(owner, name):
        if not owner.strip() or not name.strip(): raise ValueError("owner and repository required")
        return f"repos/{quote(owner, safe='')}/{quote(name, safe='')}"
    def repository(self, owner, name): return self._request("GET", self._repo(owner,name))
    def branches(self, owner, name, per_page=30):
        _page(per_page); return self._request("GET",f"{self._repo(owner,name)}/branches",
                                               params={"per_page":per_page})
    def create_branch(self, owner,name,branch,sha):
        _branch(branch)
        if not sha or len(sha)<7: raise ValueError("Provide a commit SHA.")
        return self._request("POST",f"{self._repo(owner,name)}/git/refs",
                             json={"ref":f"refs/heads/{branch}","sha":sha})
    def delete_branch(self,owner,name,branch):
        _branch(branch)
        return self._request("DELETE",f"{self._repo(owner,name)}/git/refs/heads/{quote(branch,safe='/')}")
    def pull_requests(self,owner,name,state="open",per_page=20):
        _page(per_page); _state(state)
        return self._request("GET",f"{self._repo(owner,name)}/pulls",
                             params={"state":state,"per_page":per_page})
    def create_pull_request(self,owner,name,title,head,base,body=""):
        if not title.strip() or not head.strip() or not base.strip():
            raise ValueError("title, head and base are required")
        return self._request("POST",f"{self._repo(owner,name)}/pulls",
                             json={"title":title,"head":head,"base":base,"body":body})
    def merge_pull_request(self,owner,name,number,method="squash"):
        if number<1 or method not in {"merge","squash","rebase"}:
            raise ValueError("Invalid PR number or merge method.")
        return self._request("PUT",f"{self._repo(owner,name)}/pulls/{number}/merge",
                             json={"merge_method":method})
    def issues(self,owner,name,state="open",per_page=20):
        _page(per_page); _state(state)
        return self._request("GET",f"{self._repo(owner,name)}/issues",
                             params={"state":state,"per_page":per_page})
    def create_issue(self,owner,name,title,body="",labels=None):
        if not title.strip(): raise ValueError("Issue title is required.")
        return self._request("POST",f"{self._repo(owner,name)}/issues",
                             json={"title":title,"body":body,"labels":labels or []})

def _page(n):
    if not 1<=n<=100: raise ValueError("per_page must be 1..100")
def _state(s):
    if s not in {"open","closed","all"}: raise ValueError("state must be open, closed, or all")
def _branch(s):
    if not s or s.startswith(("-", "/")) or s.endswith("/") or ".." in s or " " in s or "//" in s:
        raise ValueError("Invalid branch name.")

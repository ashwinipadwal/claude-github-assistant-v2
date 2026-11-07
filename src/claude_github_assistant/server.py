from mcp.server.fastmcp import FastMCP
from .config import Settings
from .git_service import GitService
from .github_service import GitHubService
from .security import audit, require_approval

settings=Settings.from_env()
git=GitService(settings)
gh=GitHubService(settings)
mcp=FastMCP("claude-github-assistant")

def mutate(op, repo, approved, fn, **details):
    try:
        require_approval(approved, op, settings)
        result=fn()
        audit(settings,op,repo,approved,"success",details)
        return result or f"{op} completed."
    except Exception as exc:
        audit(settings,op,repo,approved,"error",{**details,"error":str(exc)})
        raise

# Local Git: read-only
@mcp.tool()
def git_status(repository_path: str)->str:
    """Show status for a local repository inside an allowed root."""
    return git.status(repository_path)
@mcp.tool()
def git_branches(repository_path: str)->str:
    """List local and remote branches."""
    return git.branches(repository_path)
@mcp.tool()
def git_log(repository_path: str, limit: int=10)->str:
    """Show recent commits."""
    return git.log(repository_path,limit)
@mcp.tool()
def git_diff(repository_path: str, staged: bool=False)->str:
    """Show unstaged diff, or staged diff when staged=true."""
    return git.diff(repository_path,staged)

# Local Git: every mutation is approval-gated
@mcp.tool()
def git_fetch(repository_path: str, remote: str="origin", approved: bool=False)->str:
    """Fetch remote refs. Requires approved=true after user confirmation."""
    return mutate("git_fetch",repository_path,approved,lambda:git.fetch(repository_path,remote),remote=remote)
@mcp.tool()
def git_create_branch(repository_path: str, branch: str, base: str="", approved: bool=False)->str:
    """Create and switch branch. Requires approved=true."""
    return mutate("git_create_branch",repository_path,approved,
                  lambda:git.create_branch(repository_path,branch,base or None),branch=branch,base=base)
@mcp.tool()
def git_switch_branch(repository_path: str, branch: str, approved: bool=False)->str:
    """Switch branch. Requires approved=true."""
    return mutate("git_switch_branch",repository_path,approved,
                  lambda:git.switch_branch(repository_path,branch),branch=branch)
@mcp.tool()
def git_stage(repository_path: str, paths: list[str], approved: bool=False)->str:
    """Stage only the supplied paths. Requires approved=true."""
    return mutate("git_stage",repository_path,approved,lambda:git.stage(repository_path,paths),paths=paths)
@mcp.tool()
def git_unstage(repository_path: str, paths: list[str], approved: bool=False)->str:
    """Unstage only the supplied paths. Requires approved=true."""
    return mutate("git_unstage",repository_path,approved,lambda:git.unstage(repository_path,paths),paths=paths)
@mcp.tool()
def git_commit(repository_path: str, message: str, approved: bool=False)->str:
    """Create commit. Requires approved=true."""
    return mutate("git_commit",repository_path,approved,lambda:git.commit(repository_path,message),message=message)
@mcp.tool()
def git_pull(repository_path: str, remote: str="origin", branch: str="", approved: bool=False)->str:
    """Fast-forward-only pull. Requires approved=true."""
    return mutate("git_pull",repository_path,approved,
                  lambda:git.pull(repository_path,remote,branch or None),remote=remote,branch=branch)
@mcp.tool()
def git_push(repository_path: str, remote: str="origin", branch: str="",
             force_with_lease: bool=False, approved: bool=False)->str:
    """Push; optional force uses --force-with-lease. Requires approved=true."""
    return mutate("git_push",repository_path,approved,
                  lambda:git.push(repository_path,remote,branch or None,force_with_lease),
                  remote=remote,branch=branch,force_with_lease=force_with_lease)
@mcp.tool()
def git_rebase(repository_path: str, onto: str, approved: bool=False)->str:
    """Rebase current branch. Requires approved=true."""
    return mutate("git_rebase",repository_path,approved,lambda:git.rebase(repository_path,onto),onto=onto)
@mcp.tool()
def git_rebase_continue(repository_path: str, approved: bool=False)->str:
    """Continue paused rebase. Requires approved=true."""
    return mutate("git_rebase_continue",repository_path,approved,lambda:git.rebase_continue(repository_path))
@mcp.tool()
def git_rebase_abort(repository_path: str, approved: bool=False)->str:
    """Abort paused rebase. Requires approved=true."""
    return mutate("git_rebase_abort",repository_path,approved,lambda:git.rebase_abort(repository_path))
@mcp.tool()
def git_merge(repository_path: str, branch: str, no_ff: bool=False, approved: bool=False)->str:
    """Merge branch into current branch. Requires approved=true."""
    return mutate("git_merge",repository_path,approved,lambda:git.merge(repository_path,branch,no_ff),
                  branch=branch,no_ff=no_ff)
@mcp.tool()
def git_stash(repository_path: str, message: str="", approved: bool=False)->str:
    """Stash working changes. Requires approved=true."""
    return mutate("git_stash",repository_path,approved,lambda:git.stash(repository_path,message or None),
                  message=message)

# GitHub: read-only
@mcp.tool()
def github_repository(owner: str, repository: str)->dict:
    """Get repository metadata."""
    return gh.repository(owner,repository)
@mcp.tool()
def github_list_branches(owner: str, repository: str, per_page: int=30)->list:
    """List remote branches."""
    return gh.branches(owner,repository,per_page)
@mcp.tool()
def github_list_pull_requests(owner: str, repository: str, state: str="open", per_page: int=20)->list:
    """List pull requests."""
    return gh.pull_requests(owner,repository,state,per_page)
@mcp.tool()
def github_list_issues(owner: str, repository: str, state: str="open", per_page: int=20)->list:
    """List issues; GitHub may include PRs with a pull_request field."""
    return gh.issues(owner,repository,state,per_page)

# GitHub: approval-gated writes
@mcp.tool()
def github_create_branch(owner: str, repository: str, branch: str, base_sha: str,
                         approved: bool=False)->dict:
    """Create remote branch from commit SHA. Requires approved=true."""
    return mutate("github_create_branch",None,approved,
                  lambda:gh.create_branch(owner,repository,branch,base_sha),
                  owner=owner,repository=repository,branch=branch)
@mcp.tool()
def github_delete_branch(owner: str, repository: str, branch: str, approved: bool=False)->dict:
    """Delete remote branch. Requires approved=true."""
    return mutate("github_delete_branch",None,approved,
                  lambda:gh.delete_branch(owner,repository,branch),
                  owner=owner,repository=repository,branch=branch)
@mcp.tool()
def github_create_pull_request(owner: str, repository: str, title: str, head: str,
                               base: str, body: str="", approved: bool=False)->dict:
    """Open a PR. Requires approved=true."""
    return mutate("github_create_pull_request",None,approved,
                  lambda:gh.create_pull_request(owner,repository,title,head,base,body),
                  owner=owner,repository=repository,title=title,head=head,base=base)
@mcp.tool()
def github_merge_pull_request(owner: str, repository: str, number: int,
                              merge_method: str="squash", approved: bool=False)->dict:
    """Merge PR. Requires approved=true."""
    return mutate("github_merge_pull_request",None,approved,
                  lambda:gh.merge_pull_request(owner,repository,number,merge_method),
                  owner=owner,repository=repository,number=number,merge_method=merge_method)
@mcp.tool()
def github_create_issue(owner: str, repository: str, title: str, body: str="",
                        labels: list[str]|None=None, approved: bool=False)->dict:
    """Create issue. Requires approved=true."""
    return mutate("github_create_issue",None,approved,
                  lambda:gh.create_issue(owner,repository,title,body,labels),
                  owner=owner,repository=repository,title=title)

if __name__=="__main__":
    mcp.run()

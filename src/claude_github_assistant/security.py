import json
from datetime import datetime, timezone
from pathlib import Path
from .config import Settings

class ApprovalError(PermissionError): pass
class RepositoryAccessError(PermissionError): pass

def require_approval(approved: bool, operation: str, settings: Settings):
    if settings.approval_required and not approved:
        raise ApprovalError(
            f"Approval required for '{operation}'. Explain the exact action and ask the user; "
            "retry with approved=true only after explicit approval."
        )

def resolve_repository(raw_path: str, settings: Settings) -> Path:
    candidate = Path(raw_path).expanduser().resolve(strict=True)
    if not candidate.is_dir():
        raise RepositoryAccessError("Repository path must be a directory.")
    allowed = False
    for root in settings.allowed_roots:
        try:
            candidate.relative_to(root.resolve(strict=True))
            allowed = True
            break
        except (ValueError, OSError):
            pass
    if not allowed:
        raise RepositoryAccessError("Repository is outside GITHUB_AGENT_ALLOWED_ROOTS.")
    if not (candidate / ".git").exists():
        raise RepositoryAccessError("Selected directory is not a Git repository.")
    return candidate

def audit(settings: Settings, operation: str, repo, approved: bool, outcome: str, details=None):
    path = settings.audit_log
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": datetime.now(timezone.utc).isoformat(),
              "operation": operation, "repository": repo, "approved": approved,
              "outcome": outcome, "details": details or {}}
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

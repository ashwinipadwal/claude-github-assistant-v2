import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

@dataclass(frozen=True)
class Settings:
    github_token: str
    github_api_url: str
    github_api_timeout: float
    allowed_roots: tuple[Path, ...]
    approval_required: bool
    audit_log: Path

    @classmethod
    def from_env(cls):
        project_root = Path(__file__).resolve().parents[2]
        load_dotenv(project_root / ".env")
        raw = os.getenv("GITHUB_AGENT_ALLOWED_ROOTS", "")
        roots = tuple(Path(x.strip()).expanduser().resolve()
                      for x in raw.split(",") if x.strip())
        if not roots:
            raise ValueError("Set GITHUB_AGENT_ALLOWED_ROOTS to trusted absolute directories.")
        audit_path = Path(os.getenv("GITHUB_AGENT_AUDIT_LOG", "./logs/audit.jsonl")).expanduser()
        if not audit_path.is_absolute():
            audit_path = project_root / audit_path
        return cls(
            github_token=os.getenv("GITHUB_TOKEN", "").strip(),
            github_api_url=os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/"),
            github_api_timeout=float(os.getenv("GITHUB_API_TIMEOUT", "30")),
            allowed_roots=roots,
            approval_required=os.getenv("GITHUB_AGENT_APPROVAL_REQUIRED", "true").lower()
                not in {"0", "false", "no"},
            audit_log=audit_path.resolve(),
        )

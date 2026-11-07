import pytest
from claude_github_assistant.config import Settings
from claude_github_assistant.security import (
    ApprovalError, RepositoryAccessError, require_approval, resolve_repository
)

def cfg(root):
    return Settings("", "https://api.github.com", 10, (root.resolve(),), True, root/"audit.jsonl")

def test_mutation_requires_approval(tmp_path):
    with pytest.raises(ApprovalError): require_approval(False,"git_push",cfg(tmp_path))
    require_approval(True,"git_push",cfg(tmp_path))

def test_allowed_git_repository(tmp_path):
    repo=tmp_path/"repo"; repo.mkdir(); (repo/".git").mkdir()
    assert resolve_repository(str(repo),cfg(tmp_path))==repo.resolve()

def test_non_git_directory_rejected(tmp_path):
    folder=tmp_path/"folder"; folder.mkdir()
    with pytest.raises(RepositoryAccessError): resolve_repository(str(folder),cfg(tmp_path))

def test_outside_root_rejected(tmp_path):
    allow=tmp_path/"allowed"; allow.mkdir()
    outside=tmp_path/"outside"; outside.mkdir(); (outside/".git").mkdir()
    with pytest.raises(RepositoryAccessError): resolve_repository(str(outside),cfg(allow))

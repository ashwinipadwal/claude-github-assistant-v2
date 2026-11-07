# Claude GitHub Assistant v2

An approval-first MCP server for multiple local Git repositories and multiple GitHub repositories. Connect it to Claude Desktop and Claude Code in VS Code.

## Capabilities

**Local Git (read):** status, branches, recent log, diff/staged diff.

**Local Git (approval required):** fetch, create/switch branch, stage/unstage selected files, commit, fast-forward-only pull, push, optional `--force-with-lease`, rebase/continue/abort, merge, stash.

**GitHub (read):** repository metadata, branches, pull requests, issues.

**GitHub (approval required):** create/delete branch, create PR, merge PR, create issue.

## Safety

- Every write/mutating tool rejects the call unless `approved=true`.
- Claude should first explain the exact operation, repository, branch/files/PR and likely impact, then ask you to approve. It should only retry with `approved=true` after your explicit confirmation.
- Local repositories must be under `GITHUB_AGENT_ALLOWED_ROOTS`.
- Git is invoked with argument arrays and `shell=False`; arbitrary shell commands are not exposed.
- Pull is `--ff-only`; force push uses `--force-with-lease`.
- Mutations are written to an append-only JSONL audit log.
- No `reset --hard`, arbitrary command execution, or automatic conflict resolution.

The `approved=true` flag is an application-level guard, not a cryptographic approval system. Keep tokens least-privileged and review high-impact changes yourself.

## Requirements

Python 3.11+, Git installed and on PATH, and Claude Desktop and/or Claude Code in VS Code. A GitHub fine-grained token is needed only for GitHub API features; local Git features can run without it.

## Windows setup (Git Bash recommended)

1. Extract the ZIP and open Git Bash in the folder containing `pyproject.toml`.

```bash
cd /c/workspace/claude-github-assistant-v2
ls
python --version
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Use `python -m pip`, not bare `pip` (avoids the common Windows PATH issue). If `python` is not recognized, install Python 3.11+ and select **Add Python to PATH**, then reopen the terminal.

2. Create your environment file:

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
GITHUB_TOKEN=github_pat_your_token
GITHUB_AGENT_ALLOWED_ROOTS=C:/workspace,C:/projects
GITHUB_AGENT_APPROVAL_REQUIRED=true
GITHUB_AGENT_AUDIT_LOG=C:/workspace/claude-github-assistant-v2/logs/audit.jsonl
```

Add every parent folder that contains repositories you intend to access. Use forward slashes in Windows paths. Leave `GITHUB_TOKEN` blank if you only need local Git tools. Never commit or share `.env`.

### GitHub token permissions

Create a fine-grained personal access token limited to the specific repositories you use. Typical minimum permissions:
- Metadata: read
- Contents: read/write for branch creation/deletion
- Pull requests: read/write for PR listing/creation/merge
- Issues: read/write for issue listing/creation

Organization approval or SSO may be required. Do not grant organization-wide access unless necessary.

3. Run tests:

```bash
python -m pytest
```

Optional lint:

```bash
ruff check .
```

## Connect Claude Desktop

Edit `%APPDATA%\Claude\claude_desktop_config.json` and add this server (replace the example paths):

```json
{
  "mcpServers": {
    "github-assistant": {
      "command": "C:\\workspace\\claude-github-assistant-v2\\.venv\\Scripts\\python.exe",
      "args": ["-m", "claude_github_assistant.server"],
      "cwd": "C:\\workspace\\claude-github-assistant-v2",
      "env": {
        "PYTHONPATH": "C:\\workspace\\claude-github-assistant-v2\\src"
      }
    }
  }
}
```

Restart Claude Desktop. Confirm the MCP tools are listed.

## Connect Claude Code in VS Code

Create `.mcp.json` in the VS Code project root:

```json
{
  "mcpServers": {
    "github-assistant": {
      "command": "C:/workspace/claude-github-assistant-v2/.venv/Scripts/python.exe",
      "args": ["-m", "claude_github_assistant.server"],
      "env": {
        "PYTHONPATH": "C:/workspace/claude-github-assistant-v2/src"
      }
    }
  }
}
```

Open Claude Code in VS Code and approve/enable the project MCP server when prompted. The server loads `.env` from its working directory; launch it with the assistant project as its working directory. If your Claude Code version does not use the project root as working directory, configure the launch command/wrapper to `cd` to the assistant project first.

## Multiple repositories

Set a shared allowlisted root such as `C:/workspace`. The local Git tools accept the full path of each repository, for example:

- `C:/workspace/CardiacRehab-UI`
- `C:/workspace/CardiacRehabApi`
- `C:/workspace/CMUnifiedApi`

GitHub API tools accept `owner` and `repository` on each call, so you can work across multiple owners/repositories as permitted by your token.

## Example prompts

- "Show status for C:/workspace/CardiacRehab-UI."
- "Review the staged and unstaged diffs and summarize risks. Do not modify anything."
- "I want a branch feature/tro-dependency-fixes from develop. Tell me the exact operation and wait for approval."
- "Stage only package.json and package-lock.json, but ask me first."
- "Prepare a PR from feature/tro-dependency-fixes to develop. Show the title/body and ask before creating it."
- "Never merge a PR without asking me for explicit approval."

For each mutation, the MCP server itself enforces the `approved=true` argument.

## Troubleshooting

**`pip` is not recognized:** use `python -m pip install ...`.

**`does not appear to be a Python project`:** terminal is not in the folder containing `pyproject.toml`; use `pwd` and `ls`, then `cd` to the extracted project root.

**MCP server missing:** check the Python executable path, `PYTHONPATH`, `.env` location, then run `python -m claude_github_assistant.server` from the project root to inspect startup errors. Restart the Claude client after config edits.

**GitHub 401/403:** check token expiry, repository selection, permission scopes, organization policy and SSO.

## Current scope / limitations

This is a modular MCP foundation, not a self-modifying autonomous coding agent. It does not edit source files, run CI, resolve conflicts automatically, submit PR reviews, or manage releases/workflow dispatch. GitHub list calls return one page (maximum 100 records). Add those capabilities as separate tools with the same approval and audit controls when needed.

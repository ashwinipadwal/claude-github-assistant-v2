import shutil, sys
print("Python:", sys.version.split()[0])
print("Git:", shutil.which("git") or "NOT FOUND")
try:
    import mcp, httpx, dotenv
    print("Python dependencies: OK")
except ImportError as exc:
    print("Missing dependency:", exc)
    raise SystemExit(1)

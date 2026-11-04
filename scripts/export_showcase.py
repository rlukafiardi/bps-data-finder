"""Export the public showcase repo from this private one: an allow-list of code, tests, docs and screenshots, then a leak scan that
fails the export if anything private slipped through. Writes projects/bps-data-finder-showcase/ (its own git repo; commits locally with
the GitHub noreply identity, never pushes).

    uv run python scripts/export_showcase.py
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT.parent / "bps-data-finder-showcase"

CODE = ["app/*.py", "src/**/*.py", "tests/*.py", "tests/e2e/*.mjs", "tests/e2e/fixtures/*.json", "tests/conftest.py", "tests/fixtures/catalog/*.json", "evals/*.py", "evals/golden_set.csv",
        "evals/history.csv", "evals/README.md", "scripts/refresh.sh", "scripts/check_live.py", "Dockerfile", "pyproject.toml", "uv.lock",
        ".env.example", "web/index.html", "web/style.css", "web/app.js", "web/config.js", "web/_headers"]
DOCS = {"showcase/README.md": "README.md", "docs/architecture.svg": "docs/architecture.svg", "docs/eval-report.html": "docs/eval-report.html",
        "docs/linkedin/shots/search_light.png": "docs/screenshots/search.png", "docs/linkedin/shots/panel_garut_light.png": "docs/screenshots/answer.png"}
TEXT_SUFFIXES = {".py", ".md", ".csv", ".toml", ".mjs", ".js", ".json", ".html", ".css", ".svg", ".sh", ".example", ".lock", ""}
LEAKS = {"credential assignment": r"(?i)(BPS_API_KEY|GEMINI_API_KEY|NETLIFY_AUTH_TOKEN)[ \t]*=[ \t]*\S{8,}",
         "email": r"[\w.+-]+@[\w-]+(\.[\w-]+)*\.[a-z]{2,}",  # a package version like name@5.24.0 is not an address
         "employer": r"(?i)\bioh\b|ioh\.co\.id|tfe_ioh",
         "owner name": r"(?i)lukafiardi|radikal",
         "cloud ids": r"823141605435|bps-data-finder-data|api-runtime|014936|4e212512|My Billing|gcloud\.sh",
         "local path": r"/Users/|/private/tmp"}
ALLOWED = ["https://cari-data-bps.netlify.app", "github.com/rlukafiardi/bps-data-finder-showcase"]  # the live site and this repo's address
NOREPLY = re.compile(r"^\d+\+[\w-]+@users\.noreply\.github\.com$")
MIT_LICENSE = """MIT License

Copyright (c) 2026 Radikal Lukafiardi

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

The licence covers the code. The statistics come from the BPS WebAPI and keep the terms of Badan Pusat Statistik; no BPS data is included except
a few small test fixtures.
"""


def files():
    out = [(p, str(p.relative_to(ROOT))) for pattern in CODE for p in ROOT.glob(pattern) if p.is_file() and "__pycache__" not in p.parts]
    return out + [(ROOT / source, target) for source, target in DOCS.items()]


def write(source, relative):
    target = EXPORT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def secret_values():
    env = ROOT / ".env"
    pairs = [line.strip().split("=", 1) for line in env.read_text().splitlines() if "=" in line and not line.startswith("#")] if env.exists() else []
    return [v.strip("\"'") for _, v in pairs if len(v.strip("\"'")) >= 8]


def leak_scan():
    hits, secrets = [], secret_values()
    for path in EXPORT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(EXPORT)
        if re.search(r"(?i)(^|/)\.env$|token|secret|credential|\.pem$|\.key$", str(rel)):
            hits.append(f"credential-like file name: {rel}")
        if path.suffix in TEXT_SUFFIXES or path.name == "Dockerfile":
            text = path.read_text(encoding="utf-8", errors="ignore")
            hits += [f"your .env value in {rel}" for v in secrets if v in text]
            for allowed in ALLOWED:
                text = text.replace(allowed, "")
            hits += [f"{name}: {rel}" for name, pattern in LEAKS.items() if re.search(pattern, text)]
    return hits


def clear_export():
    for child in EXPORT.iterdir():  # the files, never the git history
        if child.name != ".git":
            shutil.rmtree(child) if child.is_dir() else child.unlink()


if __name__ == "__main__":
    missing = [rel for src, rel in files() if not src.exists()]
    if missing:
        sys.exit(f"missing: {missing}")
    git_config = lambda *args: subprocess.run(["git", "config", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    identity = {"name": git_config("user.name"), "email": git_config("--local", "user.email")}  # the email must be set in this repo, never taken from the global one
    if not NOREPLY.match(identity["email"]):
        sys.exit(f"the repo's local git email must be the GitHub noreply address, got {identity['email']!r}")
    EXPORT.mkdir(parents=True, exist_ok=True)
    clear_export()
    for source, relative in files():
        write(source, relative)
    package = json.loads((ROOT / "package.json").read_text())
    package["devDependencies"].pop("netlify-cli", None)  # the Netlify deploy is not part of the showcase
    (EXPORT / "package.json").write_text(json.dumps(package, indent=2) + "\n")
    (EXPORT / ".gitignore").write_text(".env\n.venv/\n__pycache__/\n.DS_Store\ndata/\nnode_modules/\ntests/e2e/shots/\n.pytest_cache/\n", encoding="utf-8")
    hits = leak_scan()
    if hits:
        clear_export()
        sys.exit("leak scan failed, export files removed:\n" + "\n".join(hits))
    (EXPORT / "LICENSE").write_text(MIT_LICENSE, encoding="utf-8")  # after the scan: it carries your name on purpose
    if not (EXPORT / ".git").exists():
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=EXPORT, check=True)
    for k, v in identity.items():
        subprocess.run(["git", "config", "--local", f"user.{k}", v], cwd=EXPORT, check=True)
    subprocess.run(["git", "add", "-A"], cwd=EXPORT, check=True)
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    committed = subprocess.run(["git", "commit", "-q", "-m", f"Update from the private repo at {sha}"], cwd=EXPORT)
    count = sum(1 for p in EXPORT.rglob("*") if p.is_file() and ".git" not in p.parts)
    print(f"exported {count} files to {EXPORT}; leak scan clean" + ("" if committed.returncode == 0 else "; nothing new to commit"))

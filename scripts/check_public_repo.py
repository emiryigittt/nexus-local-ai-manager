"""Read-only pre-publication checks on Git-visible files (not a full secret/history audit)."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DIRS = {".venv", "venv", "env", "models", "__pycache__", ".pytest-tmp"}
FORBIDDEN_NAMES = {"settings.json", "mcp_servers.json", "last_debug.json",
                   "arayuz_goruntusu.png", "gorsel_isleme_ozelligi.png", "pano_ozelligi.png"}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".bat", ".example"}
SECRET_PATTERNS = (
    re.compile(r"(?m)^-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----$"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b"),
)


def path_problem(relative: Path) -> str | None:
    parts = {part.casefold() for part in relative.parts}
    name = relative.name.casefold()
    prefix = tuple(part.casefold() for part in relative.parts[:2])
    if prefix in {("output", "pdf"), ("tmp", "pdfs")}:
        return "personal document-generation output"
    if parts & FORBIDDEN_DIRS or name in FORBIDDEN_NAMES:
        return "runtime or unreviewed personal file"
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        return "private environment file"
    if re.search(r"\.(?:db|sqlite3?)(?:-(?:wal|shm|journal))?$", name):
        return "local database"
    ui_sound = (relative.as_posix() in {f"frontend/assets/sounds/{name}.wav" for name in
                                      ("open", "collapse", "success", "attachment", "error", "listen")})
    if relative.suffix.casefold() in {".wav", ".mp3", ".log", ".onnx", ".gguf"} and not ui_sound:
        return "recording, log or model artifact"
    if name.startswith("memory-export") and name.endswith(".json"):
        return "memory export"
    return None


def inspect_text(
    relative: Path, content: str, root: Path, published_paths: set[str] | None = None,
) -> list[str]:
    problems = []
    if any(pattern.search(content) for pattern in SECRET_PATTERNS):
        # Never print the matching value or its line.
        problems.append("possible credential/private key; inspect privately")
    if relative.suffix.casefold() != ".md":
        return problems
    if "YOUR_USERNAME" in content:
        problems.append("unresolved repository placeholder")
    # Check simple inline Markdown links/images, outside fenced code. Anchors and
    # remote URLs are intentionally not fetched. This is not a Markdown parser.
    prose = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
    for raw in re.findall(r"!?\[[^\]\n]*\]\(([^)\n]+)\)", prose):
        target = raw.strip().strip("<>")
        if urlsplit(target).scheme or target.startswith(("#", "//")):
            continue
        target = unquote(target.split("#", 1)[0])
        resolved = (root / relative.parent / target).resolve()
        if not resolved.is_relative_to(root.resolve()):
            problems.append("local link escapes repository")
        elif not resolved.exists():
            problems.append(f"missing local link: {target}")
        elif (published_paths is not None and resolved.is_file()
              and resolved.relative_to(root.resolve()).as_posix() not in published_paths):
            problems.append(f"local link points to a file excluded from publication: {target}")
    return problems


def check_language_pairs(root: Path) -> list[tuple[str, str]]:
    """Check declared document pairs and navigation, not semantic translation parity."""
    manifest = root / "docs/languages.json"
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8-sig"))
        pairs = payload["pairs"]
        if not isinstance(pairs, list) or not pairs:
            raise ValueError("empty pairs")
    except (OSError, ValueError, KeyError, TypeError):
        return [("docs/languages.json", "missing or invalid translation manifest")]
    findings = []
    seen = set()
    for pair in pairs:
        if (not isinstance(pair, list) or len(pair) != 2
                or not all(isinstance(name, str) for name in pair)):
            findings.append(("docs/languages.json", "each language pair must name two files"))
            continue
        for index, name in enumerate(pair):
            path = (root / name).resolve()
            if (not path.is_relative_to(root.resolve()) or not path.is_file()
                    or path.suffix != ".md" or path.is_symlink()):
                findings.append(("docs/languages.json", "language file missing or outside repository"))
                continue
            if name in seen:
                findings.append((name, "document appears in multiple language pairs"))
            seen.add(name)
            try:
                content = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                findings.append((name, "language file is not UTF-8"))
                continue
            counterpart = (root / pair[1 - index]).resolve()
            links = re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", content)
            if not any(
                not urlsplit(link).scheme
                and (path.parent / unquote(link.split("#", 1)[0])).resolve() == counterpart
                for link in links
            ):
                findings.append((name, "missing link to paired language document"))
    return findings


def main() -> int:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT, check=True, capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        print("Git could not list this checkout. Check Git availability and repository ownership.")
        print("No files changed; no content scanned. The checker does not change Git trust settings.")
        return 2
    names = sorted(set(result.stdout.decode("utf-8").split("\0")) - {""})
    findings = check_language_pairs(ROOT)
    for name in names:
        relative = Path(name)
        problem = path_problem(relative)
        if problem:
            findings.append((name, problem))
            continue  # Do not read potentially private runtime files.
        path = ROOT / relative
        if path.is_symlink():
            findings.append((name, "symlink requires manual publication review"))
            continue
        if not path.is_file():
            findings.append((name, "tracked file missing from working tree; review deletion"))
            continue
        if path.stat().st_size > 5 * 1024 * 1024:
            findings.append((name, "file exceeds 5 MiB review threshold"))
            continue
        if path.suffix.casefold() in TEXT_SUFFIXES:
            try:
                content = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                findings.append((name, "text file is not UTF-8; review encoding"))
                continue
            findings.extend((name, issue) for issue in inspect_text(relative, content, ROOT, set(names)))
    for name, problem in findings:
        print(f"REVIEW {name}: {problem}")
    print(f"Checked {len(names)} Git-visible files; {len(findings)} findings. No files changed.")
    print("Scope: working tree only; not Git history, image contents, all secret formats, or remote links.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

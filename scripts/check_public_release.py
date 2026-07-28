from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PREFIXES = ("data/", "exports/", "screenshots/")
TEXT_SUFFIXES = {
    ".bat", ".css", ".html", ".ini", ".js", ".json", ".md", ".py", ".toml", ".txt", ".yml", ".yaml"
}
PATTERNS = {
    "Windows user path": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE),
    "GitHub token": re.compile(r"(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private key": re.compile(r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
}
ORDER_ID = re.compile(r"\b\d{3}-\d{7}-\d{7}\b")
SYNTHETIC_ORDER_ID = re.compile(r"\b\d{3}-0{7}-0{6}\d\b")


def tracked_files() -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        names = [name for name in result.stdout.decode("utf-8").split("\0") if name]
        if names:
            return [ROOT / name for name in names]
    except (FileNotFoundError, subprocess.CalledProcessError, UnicodeDecodeError):
        pass
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and not any(path.relative_to(ROOT).as_posix().startswith(prefix) for prefix in PRIVATE_PREFIXES)
    ]


def main() -> int:
    violations: list[str] = []
    for path in tracked_files():
        relative = path.relative_to(ROOT).as_posix()
        if any(relative.startswith(prefix) for prefix in PRIVATE_PREFIXES):
            violations.append(f"private path is tracked: {relative}")
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE", ".gitignore"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                violations.append(f"{label}: {relative}")
        for match in ORDER_ID.finditer(text):
            if not SYNTHETIC_ORDER_ID.fullmatch(match.group(0)):
                violations.append(f"non-synthetic Amazon order ID: {relative}")
                break
    if violations:
        print("Public release safety scan failed:")
        for violation in sorted(set(violations)):
            print(f"- {violation}")
        return 1
    print(f"Public release safety scan passed ({len(tracked_files())} files checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

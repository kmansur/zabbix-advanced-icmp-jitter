#!/usr/bin/env python3
"""Validate bilingual documentation parity and local Markdown links."""

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCS_EN = ROOT / "docs" / "en"
DOCS_PTBR = ROOT / "docs" / "pt-BR"
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")

ROOT_PAIRS = {
    "README.md": "README.pt-BR.md",
    "CONTRIBUTING.md": "CONTRIBUTING.pt-BR.md",
    "SECURITY.md": "SECURITY.pt-BR.md",
    "NOTICE.md": "NOTICE.pt-BR.md",
    "CHANGELOG.md": "CHANGELOG.pt-BR.md",
}


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def markdown_names(directory):
    return {path.name for path in directory.glob("*.md") if path.is_file()}


def validate_root_pairs():
    for english, portuguese in ROOT_PAIRS.items():
        if not (ROOT / english).is_file():
            fail(f"missing English root document: {english}")
        if not (ROOT / portuguese).is_file():
            fail(f"missing Brazilian Portuguese root document: {portuguese}")


def validate_docs_parity():
    english = markdown_names(DOCS_EN)
    portuguese = markdown_names(DOCS_PTBR)

    if english != portuguese:
        missing_en = sorted(portuguese - english)
        missing_pt = sorted(english - portuguese)
        details = []
        if missing_en:
            details.append(f"missing in docs/en: {', '.join(missing_en)}")
        if missing_pt:
            details.append(f"missing in docs/pt-BR: {', '.join(missing_pt)}")
        fail("documentation trees are not mirrored; " + "; ".join(details))

    for name in sorted(english):
        en_text = (DOCS_EN / name).read_text(encoding="utf-8")
        pt_text = (DOCS_PTBR / name).read_text(encoding="utf-8")
        if f"../pt-BR/{name}" not in en_text:
            fail(f"docs/en/{name} has no link to its pt-BR counterpart")
        if f"../en/{name}" not in pt_text:
            fail(f"docs/pt-BR/{name} has no link to its English counterpart")


def markdown_files():
    files = list(ROOT.glob("*.md"))
    files.extend((ROOT / "docs").rglob("*.md"))
    return sorted(path for path in files if path.is_file())


def local_link_target(source, destination):
    destination = destination.strip()
    if destination.startswith("<") and destination.endswith(">"):
        destination = destination[1:-1]
    destination = destination.split(maxsplit=1)[0]

    parsed = urlparse(destination)
    if parsed.scheme or parsed.netloc or destination.startswith("#"):
        return None

    relative_path = unquote(parsed.path)
    if not relative_path:
        return None

    return (source.parent / relative_path).resolve()


def validate_local_links():
    for source in markdown_files():
        text = source.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            destination = match.group(1)
            target = local_link_target(source, destination)
            if target is None:
                continue
            if not target.is_relative_to(ROOT):
                fail(f"{source.relative_to(ROOT)} links outside the repository: {destination!r}")
            if not target.exists():
                fail(f"broken local link in {source.relative_to(ROOT)}: {destination!r}")


def main():
    validate_root_pairs()
    validate_docs_parity()
    validate_local_links()
    print("OK: bilingual documentation parity and local links validated")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Check an Arabic chapter against its English original.

The translation is done in place: each Arabic file replaces its English
original at the same path. The English original is read from git, from the
branch that still holds the untouched English text (default: arabic-version).

Usage (from the repository root):
    python3 tools/check_translation.py hello-world.md
    python3 tools/check_translation.py hello-world.md --ref upstream/main

This compares:
    original:    hello-world.md as it is on the reference branch
    translation: ./hello-world.md in the working tree
    glossary:    ./glossary.md

ERRORS (exit code 1) mean the translation is structurally broken:
    - code blocks differ from the original (count or content)
    - heading count differs

WARNINGS (exit code 0) need a human look:
    - inline code spans or links missing / added
    - an English glossary term left untranslated in Arabic prose
    - a pending (not yet approved) glossary term is used
    - an Arabic paragraph starts or ends with a Latin word (bidi risk)
    - Latin punctuation (, ; ?) next to Arabic text
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

FENCE_RE = re.compile(r"^(```|~~~)")
HEADING_RE = re.compile(r"^#{1,6}\s")
LIST_ITEM_RE = re.compile(r"^\s*([*+-]|\d+[.)])\s")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
LINK_RE = re.compile(r"\]\(([^)\s]+)")
ARABIC_RE = re.compile(r"[؀-ۿ]")
LATIN_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_'-]*")
LATIN_PUNCT_NEAR_ARABIC_RE = re.compile(
    r"[؀-ۿ]\s*[,;?]|[,;?]\s*[؀-ۿ]"
)

STATUS_APPROVED = "معتمد"
STATUS_PENDING = "مقترح"
STATUS_KEEP = "يبقى بالإنجليزية"


@dataclass
class Document:
    code_blocks: list[str]
    prose_lines: list[str]
    paragraphs: list[str]


def parse_markdown(text: str) -> Document:
    """Split a markdown file into fenced code blocks and prose."""
    code_blocks: list[str] = []
    prose_lines: list[str] = []
    paragraphs: list[str] = []

    in_code = False
    fence = ""
    current_block: list[str] = []
    current_para: list[str] = []

    def flush_paragraph() -> None:
        if current_para:
            paragraphs.append(" ".join(current_para).strip())
            current_para.clear()

    for line in text.splitlines():
        match = FENCE_RE.match(line.strip())
        if not in_code and match:
            flush_paragraph()
            in_code = True
            fence = match.group(1)
            current_block = [line.strip()]
            continue
        if in_code:
            current_block.append(line.rstrip())
            if line.strip().startswith(fence) and len(current_block) > 1:
                code_blocks.append("\n".join(current_block))
                in_code = False
            continue

        prose_lines.append(line)
        if line.strip() == "" or LIST_ITEM_RE.match(line) or HEADING_RE.match(line):
            flush_paragraph()
        else:
            current_para.append(line.strip())

    flush_paragraph()
    return Document(code_blocks, prose_lines, paragraphs)


def load_glossary(path: Path) -> list[tuple[str, str, str]]:
    """Return (english, arabic, status) rows from the glossary table."""
    rows: list[tuple[str, str, str]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        english, arabic, status = cells[0], cells[1], cells[2]
        if english.lower() in ("english", "") or set(english) <= {"-", ":"}:
            continue
        rows.append((english, arabic, status))
    return rows


def strip_inline_code(line: str) -> str:
    return INLINE_CODE_RE.sub(" ", line)


def strip_links_and_markup(text: str) -> str:
    text = re.sub(r"\]\([^)]*\)", "]", text)  # link targets
    text = re.sub(r"<[^>]+>", " ", text)  # html tags
    text = re.sub(r"https?://\S+", " ", text)  # bare urls
    return text


def read_original(chapter: str, ref: str) -> str | None:
    """Read the English original from git, as it is at `ref`."""
    result = subprocess.run(
        ["git", "show", f"{ref}:{chapter}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        print(f"ERROR: cannot read {chapter} at {ref}: {result.stderr.strip()}")
        return None
    return result.stdout


def check(chapter: str, ref: str) -> int:
    root = Path.cwd()
    translation_path = root / chapter
    glossary_path = root / "glossary.md"

    if not translation_path.exists():
        print(f"ERROR: file not found: {translation_path}")
        return 1
    original_text = read_original(chapter, ref)
    if original_text is None:
        return 1

    original = parse_markdown(original_text)
    translation = parse_markdown(translation_path.read_text(encoding="utf-8"))
    glossary = load_glossary(glossary_path)

    errors: list[str] = []
    warnings: list[str] = []

    # 1. Code blocks must be identical.
    if len(original.code_blocks) != len(translation.code_blocks):
        errors.append(
            f"code block count: original {len(original.code_blocks)}, "
            f"translation {len(translation.code_blocks)}"
        )
    for index, (left, right) in enumerate(
        zip(original.code_blocks, translation.code_blocks), start=1
    ):
        if left != right:
            first_line = left.splitlines()[1] if len(left.splitlines()) > 1 else ""
            errors.append(f"code block #{index} differs (starts: {first_line!r})")

    # 2. Headings: same count.
    original_headings = [l for l in original.prose_lines if HEADING_RE.match(l)]
    translated_headings = [l for l in translation.prose_lines if HEADING_RE.match(l)]
    if len(original_headings) != len(translated_headings):
        errors.append(
            f"heading count: original {len(original_headings)}, "
            f"translation {len(translated_headings)}"
        )

    # 3. Inline code spans and links: same multiset.
    def spans(doc: Document, regex: re.Pattern[str]) -> Counter[str]:
        found: Counter[str] = Counter()
        for line in doc.prose_lines:
            found.update(regex.findall(line))
        return found

    for label, regex in (("inline code", INLINE_CODE_RE), ("link", LINK_RE)):
        left, right = spans(original, regex), spans(translation, regex)
        missing = left - right
        added = right - left
        for item, count in missing.items():
            warnings.append(f"{label} missing in translation ({count}x): {item}")
        for item, count in added.items():
            warnings.append(f"{label} added in translation ({count}x): {item}")

    # 4. Glossary checks on Arabic prose (outside code).
    prose = "\n".join(
        strip_links_and_markup(strip_inline_code(line))
        for line in translation.prose_lines
    )
    # English is allowed in parentheses right after the Arabic term
    # (first occurrence only), so parenthesised Latin text is checked apart.
    paren_re = re.compile(r"\(\s*([A-Za-z][^()؀-ۿ]*?)\s*\)")
    parenthesised = Counter(m.lower() for m in paren_re.findall(prose))
    prose_without_parens = paren_re.sub(" ", prose)

    pending_used: list[str] = []
    for english, arabic, status in glossary:
        if status == STATUS_KEEP:
            continue
        english_re = re.compile(
            rf"(?<![A-Za-z]){re.escape(english)}(?![A-Za-z])", re.I
        )
        in_parentheses = parenthesised[english.lower()]
        if english_re.search(prose_without_parens):
            warnings.append(
                f"English term left in prose: {english!r} -> use {arabic!r}"
            )
        if in_parentheses > 1:
            warnings.append(
                f"English term in parentheses {in_parentheses}x "
                f"(first occurrence only): {english!r}"
            )
        if status == STATUS_PENDING and arabic and arabic in prose:
            pending_used.append(arabic)
    if pending_used:
        warnings.append("pending glossary terms used: " + "، ".join(pending_used))

    # 5. Bidi lint on Arabic paragraphs.
    for paragraph in translation.paragraphs:
        plain = strip_links_and_markup(strip_inline_code(paragraph))
        plain = paren_re.sub(" ", plain)  # "(English gloss)" is allowed
        plain = re.sub(r"^[#>*\-+\d.\s]+", "", plain).strip()  # list/heading markers
        if not ARABIC_RE.search(plain):
            continue
        words = plain.split()
        first = words[0].strip("*_()[]") if words else ""
        last = words[-1].strip("*_()[].:،؛؟!") if words else ""
        preview = plain[:60]
        if LATIN_WORD_RE.fullmatch(first):
            warnings.append(f"paragraph starts with a Latin word: {preview!r}")
        if LATIN_WORD_RE.fullmatch(last):
            warnings.append(f"paragraph ends with a Latin word: {preview!r}")
        if LATIN_PUNCT_NEAR_ARABIC_RE.search(plain):
            warnings.append(f"Latin punctuation in Arabic text: {preview!r}")

    for message in errors:
        print(f"ERROR:   {message}")
    for message in warnings:
        print(f"WARNING: {message}")
    if not errors and not warnings:
        print("OK: no issues found")

    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


DEFAULT_REF = "arabic-version"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("chapter", help="chapter path, e.g. hello-world.md")
    parser.add_argument(
        "--ref",
        default=DEFAULT_REF,
        help=f"git branch or commit holding the English original (default: {DEFAULT_REF})",
    )
    args = parser.parse_args()
    return check(args.chapter, args.ref)


if __name__ == "__main__":
    sys.exit(main())

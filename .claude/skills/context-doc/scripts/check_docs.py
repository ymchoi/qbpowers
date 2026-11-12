#!/usr/bin/env python3
"""Mechanical check of a project's documents under the context-doc rules.

Usage: python check_docs.py <project directory>

Prints token counts and the problems of each check; exits 1 when there is a problem, 0 otherwise.
"""

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

import tiktoken

RULES_FILE = Path(__file__).resolve().parent.parent / "rules.md"
DOC_LIMIT = 5_000
DEFAULT_BUDGET = 100_000
RULES_HEADING = "## Document rules"

SIZE = "Size"
TABLE = "Document table"
LINKS = "Links"
PATHS = "Paths"
TEMP = "Temporary paths"
RULES = "Rule block"
CHECKS = (SIZE, TABLE, LINKS, PATHS, TEMP, RULES)

FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
ATX_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
SECTION_END = re.compile(r"^ {0,3}#{1,2}(?:[ \t]|$)")
CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")
INLINE_LINK = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
REFERENCE_DEF = re.compile(r"^ {0,3}\[[^\]]+\]:\s*(<[^>]*>|\S+)")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
BUDGET_PREFIX = "Document budget:"
BUDGET_LINE = re.compile(r"Document budget:\s*(\d{1,3}(?:,\d{3})+|\d+)\s+tokens")
TEMP_REFERENCE = re.compile(r"\.temp_files/[^\s`'\")\]|,;]+")
TEMPORARY_PLAN_START = "Delete this file when"
SHELL_INFOS = {"sh", "bash", "zsh", "shell", "console"}
PLACEHOLDERS = ("<", ">", "*", "{", "$", "...", "(", "|")
# A file named with a place in it: a line (`a.py:12`), a symbol (`a.py:main`) or a pytest node (`a.py::test_x`).
LOCATION_SUFFIX = re.compile(r":[^/]*$")


@dataclass(frozen=True)
class Problem:
    check: str
    message: str
    file: Path | None = None
    line: int | None = None


@dataclass(frozen=True)
class Link:
    file: Path
    line: int
    written: str
    target: Path
    fragment: str


def find_repo_root(project: Path) -> Path | None:
    for directory in (project, *project.parents):
        if (directory / ".git").exists():
            return directory
    return None


def project_documents(project: Path) -> list[Path]:
    agents = project / "AGENTS.md"
    entry = [agents] if agents.is_file() else []
    return entry + sorted(p for p in (project / "docs").glob("*.md") if p.is_file())


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def fence_infos(lines: Sequence[str]) -> list[str | None]:
    """Per line: None outside fenced code, else the block's info word in lower case ('' if none).

    Fence lines count as inside the block.
    """
    infos: list[str | None] = []
    fence: str | None = None
    info = ""
    for line in lines:
        match = FENCE.match(line)
        if fence is None:
            if match:
                fence = match.group(1)
                words = line[match.end() :].split()
                info = words[0].lower() if words else ""
            infos.append(None if fence is None else info)
        else:
            infos.append(info)
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence):
                if not line[match.end() :].strip():
                    fence = None
    return infos


def prose_lines(lines: Sequence[str]) -> Iterator[tuple[int, str]]:
    """Yield (1-based number, line) for lines outside fenced code blocks."""
    for number, (line, info) in enumerate(zip(lines, fence_infos(lines), strict=True), start=1):
        if info is None:
            yield number, line


def code_spans(line: str) -> list[str]:
    return [match.group(2) for match in CODE_SPAN.finditer(line)]


def without_code_spans(line: str) -> str:
    return CODE_SPAN.sub(lambda match: " " * len(match.group(0)), line)


def rule_block_range(lines: Sequence[str]) -> range | None:
    """0-based line indexes of the `## Document rules` section, heading included."""
    infos = fence_infos(lines)
    start = next(
        (i for i, line in enumerate(lines) if infos[i] is None and line.rstrip() == RULES_HEADING),
        None,
    )
    if start is None:
        return None
    end = next(
        (i for i in range(start + 1, len(lines)) if infos[i] is None and SECTION_END.match(lines[i])),
        len(lines),
    )
    return range(start, end)


def rendered_text(markup: str) -> str:
    """Heading text as rendered: link and image text kept, HTML tags and emphasis stars dropped."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", markup)
    return re.sub(r"<[^>]+>", "", text).replace("*", "")


def github_anchor(heading: str) -> str:
    parts = []
    last = 0
    for match in CODE_SPAN.finditer(heading):
        parts += [rendered_text(heading[last : match.start()]), match.group(2)]
        last = match.end()
    parts.append(rendered_text(heading[last:]))
    text = re.sub(r"[^\w\- ]", "", "".join(parts).lower())
    return text.replace(" ", "-")


def heading_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    seen: dict[str, int] = {}
    for _, line in prose_lines(read_lines(path)):
        match = ATX_HEADING.match(line)
        if not match:
            continue
        text = re.sub(r"[ \t]+#+$", "", match.group(2) or "")
        base = github_anchor(text.strip())
        count = seen.get(base, 0)
        seen[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def relative_link_targets(line: str) -> list[str]:
    stripped = without_code_spans(line)
    written = [match.group(1) for match in INLINE_LINK.finditer(stripped)]
    definition = REFERENCE_DEF.match(stripped)
    if definition:
        written.append(definition.group(1))
    targets = [w[1:-1] if w.startswith("<") else w for w in written]
    return [t for t in targets if t and not SCHEME.match(t) and not t.startswith("/")]


def iter_links(path: Path) -> Iterator[Link]:
    for number, line in prose_lines(read_lines(path)):
        for written in relative_link_targets(line):
            location, _, fragment = written.partition("#")
            target = (path.parent / unquote(location)).resolve() if location else path.resolve()
            yield Link(path, number, written, target, unquote(fragment).lower())


def broken_link_reason(link: Link) -> str | None:
    if not link.target.exists():
        return f"link `{link.written}`: target does not exist"
    if link.fragment and link.target.suffix == ".md" and link.fragment not in heading_anchors(link.target):
        return f"link `{link.written}`: no heading with anchor #{link.fragment}"
    return None


def link_problems(check: str, links: Iterator[Link]) -> list[Problem]:
    problems = []
    for link in links:
        reason = broken_link_reason(link)
        if reason:
            problems.append(Problem(check, reason, link.file, link.line))
    return problems


def count_tokens(documents: Sequence[Path]) -> dict[Path, int]:
    encoding = tiktoken.get_encoding("o200k_base")
    return {doc: len(encoding.encode(doc.read_text(encoding="utf-8"), disallowed_special=())) for doc in documents}


def read_budget(project: Path) -> tuple[int, list[Problem]]:
    """The total budget, and a problem for each budget line that is not in the form the check reads."""
    agents = project / "AGENTS.md"
    budget = DEFAULT_BUDGET
    problems: list[Problem] = []
    if not agents.is_file():
        return budget, problems
    for number, line, info in checked_lines(agents, project):
        if info is not None or not line.startswith(BUDGET_PREFIX):
            continue
        match = BUDGET_LINE.fullmatch(line.rstrip())
        if match:
            budget = int(match.group(1).replace(",", ""))
        else:
            message = f"not in the form `{BUDGET_PREFIX} <N> tokens`, so the default {DEFAULT_BUDGET:,} applies"
            problems.append(Problem(SIZE, message, agents, number))
    return budget, problems


def check_size(counts: dict[Path, int], budget: int) -> list[Problem]:
    problems = [
        Problem(SIZE, f"{tokens:,} tokens, over the {DOC_LIMIT:,} limit per document", doc)
        for doc, tokens in counts.items()
        if tokens > DOC_LIMIT
    ]
    total = sum(counts.values())
    if total > budget:
        problems.append(Problem(SIZE, f"total {total:,} tokens, over the budget of {budget:,}"))
    return problems


def check_document_table(project: Path) -> list[Problem]:
    agents = project / "AGENTS.md"
    if not agents.is_file():
        return [Problem(TABLE, "AGENTS.md does not exist", agents)]
    links = list(iter_links(agents))
    linked = {link.target for link in links}
    problems = [
        Problem(TABLE, "not linked from AGENTS.md", doc)
        for doc in project_documents(project)
        if doc != agents and doc.resolve() not in linked
    ]
    problems += [
        Problem(TABLE, "in a subfolder of docs/, which has no subdirectories", doc)
        for doc in sorted((project / "docs").rglob("*.md"))
        if doc.parent != project / "docs"
    ]
    return problems + link_problems(TABLE, iter(links))


def inbound_sources(project: Path, root: Path) -> list[Path]:
    """Markdown files in the repository, tracked or untracked but not ignored.

    Leaves out the project's documents, checked on their own, and its ref/ folder, whose files are kept as they are.
    """
    listed = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        encoding="utf-8",
        check=True,
    ).stdout
    own = {doc.resolve() for doc in project_documents(project)}
    paths = {(root / name) for name in listed.split("\0") if name.endswith(".md")}
    return sorted(
        p for p in paths if p.is_file() and p.resolve() not in own and not p.resolve().is_relative_to(project / "ref")
    )


def is_project_document_path(target: Path, project: Path) -> bool:
    return target == project / "AGENTS.md" or (target.parent == project / "docs" and target.suffix == ".md")


def check_links(project: Path, root: Path | None) -> list[Problem]:
    """Links in the documents other than AGENTS.md (the document table check covers those), and inbound links."""
    agents = project / "AGENTS.md"
    problems = [
        problem
        for doc in project_documents(project)
        if doc != agents
        for problem in link_problems(LINKS, iter_links(doc))
    ]
    if root is not None:
        for source in inbound_sources(project, root):
            inbound = (link for link in iter_links(source) if is_project_document_path(link.target, project))
            problems += link_problems(LINKS, inbound)
    return problems


def checked_lines(doc: Path, project: Path) -> Iterator[tuple[int, str, str | None]]:
    """Yield (number, line, fence info) for the lines of a document, leaving out the rule block of AGENTS.md.

    The rule block is a copy of rules.md, which the rule block check covers.
    """
    lines = read_lines(doc)
    skipped = (rule_block_range(lines) if doc == project / "AGENTS.md" else None) or range(0)
    for index, (line, info) in enumerate(zip(lines, fence_infos(lines), strict=True)):
        if index not in skipped:
            yield index + 1, line, info


def is_placeholder(text: str) -> bool:
    return any(mark in text for mark in PLACEHOLDERS)


def is_missing_path(word: str, bases: Sequence[Path]) -> bool:
    if "/" not in word or "://" in word or is_placeholder(word):
        return False
    path = LOCATION_SUFFIX.sub("", word)
    first = path.split("/", 1)[0]
    # A path that starts with . or .. is relative to a place the text does not name, so it cannot be checked.
    if first in ("", ".", ".."):
        return False
    roots = [base for base in bases if (base / first).exists()]
    return bool(roots) and not any((base / path).exists() for base in roots)


def missing_paths(text: str, bases: Sequence[Path]) -> list[str]:
    """Paths named in text that do not exist. Text with whitespace is a command: each word is checked, options not."""
    words = [word.strip("'\"") for word in text.split() if not word.startswith("-")]
    return [word for word in words if is_missing_path(word, bases)]


def check_paths(project: Path, root: Path | None) -> list[Problem]:
    bases = [project] if root is None else [root, project]
    problems = []
    for doc in project_documents(project):
        for number, line, info in checked_lines(doc, project):
            if info is None:
                texts = code_spans(line)
            elif info in SHELL_INFOS:
                texts = [line]
            else:
                continue
            for text in texts:
                for path in missing_paths(text, bases):
                    problems.append(Problem(PATHS, f"`{path}` does not exist", doc, number))
    return problems


def may_refer_to_temp_files(doc: Path, project: Path) -> bool:
    """Status and temporary plan documents may point at material of the work in progress."""
    if doc == project / "docs" / "status.md":
        return True
    return doc.parent == project / "docs" and doc.read_text(encoding="utf-8").startswith(TEMPORARY_PLAN_START)


def check_temp_paths(project: Path) -> list[Problem]:
    return [
        Problem(TEMP, "refers to a path under .temp_files/", doc, number)
        for doc in project_documents(project)
        if not may_refer_to_temp_files(doc, project)
        for number, line, _ in checked_lines(doc, project)
        if any(not is_placeholder(match.group(0)) for match in TEMP_REFERENCE.finditer(line))
    ]


def numbered_content(lines: Sequence[str], first_number: int) -> list[tuple[int, str]]:
    """(line number, line) pairs with trailing whitespace and leading and trailing blank lines dropped."""
    numbered = [(first_number + i, line.rstrip()) for i, line in enumerate(lines)]
    while numbered and not numbered[0][1]:
        numbered.pop(0)
    while numbered and not numbered[-1][1]:
        numbered.pop()
    return numbered


def check_rule_block(project: Path, rules: Path = RULES_FILE) -> list[Problem]:
    agents = project / "AGENTS.md"
    if not agents.is_file():
        return [Problem(RULES, "AGENTS.md does not exist", agents)]
    lines = read_lines(agents)
    block = rule_block_range(lines)
    if block is None:
        return [Problem(RULES, f"no `{RULES_HEADING}` section", agents)]
    section = numbered_content(lines[block.start : block.stop], block.start + 1)
    expected = numbered_content(read_lines(rules), 1)
    for (number, actual), (rules_number, wanted) in zip(section, expected):
        if actual != wanted:
            return [Problem(RULES, f"differs from {rules} line {rules_number}: {wanted}", agents, number)]
    if len(section) > len(expected):
        return [Problem(RULES, f"line not in {rules}", agents, section[len(expected)][0])]
    if len(section) < len(expected):
        rules_number, wanted = expected[len(section)]
        message = f"the section ends here; {rules} continues at line {rules_number}: {wanted}"
        return [Problem(RULES, message, agents, section[-1][0])]
    return []


def display(path: Path, project: Path) -> str:
    # Forward slashes on every OS, the form documents use for paths.
    return Path(os.path.relpath(path, project)).as_posix()


def format_report(
    project: Path, counts: dict[Path, int], budget: int, problems: Sequence[Problem], repo_found: bool
) -> str:
    out = [f"Project: {project}", ""]
    names = [display(doc, project) for doc in counts]
    width = max([len("Total"), *map(len, names)])
    out.append(f"{'Document':<{width}}  {'Tokens':>7}")
    for name, tokens in zip(names, counts.values(), strict=True):
        flag = f"  over {DOC_LIMIT:,}" if tokens > DOC_LIMIT else ""
        out.append(f"{name:<{width}}  {tokens:>7,}{flag}")
    out.append(f"{'Total':<{width}}  {sum(counts.values()):>7,}  of {budget:,}")
    if not repo_found:
        out += ["", "No .git found above the project: links from elsewhere in the repository were not checked."]
    for number, check in enumerate(CHECKS, start=1):
        found = [p for p in problems if p.check == check]
        out += ["", f"{number}. {check}: {'ok' if not found else f'{len(found)} problem(s)'}"]
        for problem in found:
            where = "" if problem.file is None else display(problem.file, project)
            if problem.line is not None:
                where += f":{problem.line}"
            out.append(f"  {where + ': ' if where else ''}{problem.message}")
    out += ["", f"Result: {len(problems)} problem(s)" if problems else "Result: all checks passed"]
    return "\n".join(out)


def main(argv: Sequence[str], rules: Path = RULES_FILE) -> int:
    parser = argparse.ArgumentParser(description="Check a project's documents under the context-doc rules.")
    parser.add_argument("project", type=Path, help="project directory (holds AGENTS.md and docs/)")
    project = parser.parse_args(argv).project.resolve()
    if not project.is_dir():
        parser.error(f"not a directory: {project}")
    root = find_repo_root(project)
    counts = count_tokens(project_documents(project))
    budget, budget_problems = read_budget(project)
    problems = [
        *budget_problems,
        *check_size(counts, budget),
        *check_document_table(project),
        *check_links(project, root),
        *check_paths(project, root),
        *check_temp_paths(project),
        *check_rule_block(project, rules),
    ]
    print(format_report(project, counts, budget, problems, root is not None))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

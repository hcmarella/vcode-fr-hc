import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

import frontmatter
from pydantic import BaseModel, ValidationError

from app.sync_engine.schemas import (
    AgentFrontmatter,
    CommandFrontmatter,
    KnowledgeFrontmatter,
    SkillFrontmatter,
)

FrontmatterT = TypeVar("FrontmatterT", bound=BaseModel)


class EmptyFrontmatter(BaseModel):
    """CLAUDE.md has no frontmatter of its own -- used as a placeholder."""


# Real command frontmatter in the wild writes argument-hint as an unquoted,
# human-readable hint like `[story|bug|task] <short description>`. YAML reads
# a leading `[` as a flow sequence, and the `|` inside it then breaks parsing
# entirely (or, without a `|`, silently parses into a list instead of a
# string). Quote the value before handing it to the YAML parser so it's
# always read as plain text, matching the spec's `argument-hint: string`.
_UNQUOTED_ARGUMENT_HINT_RE = re.compile(r'^(argument-hint:\s*)(?!["\']).+$', re.MULTILINE)


def _sanitize_frontmatter_text(raw_text: str) -> str:
    def _quote(match: re.Match) -> str:
        prefix = match.group(1)
        value = match.group(0)[len(prefix):]
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'{prefix}"{escaped}"'

    return _UNQUOTED_ARGUMENT_HINT_RE.sub(_quote, raw_text)


class ParseError(Exception):
    def __init__(self, source_path: str, reason: str):
        self.source_path = source_path
        self.reason = reason
        super().__init__(f"{source_path}: {reason}")


@dataclass
class ParsedFile:
    source_path: str
    frontmatter: BaseModel
    body_markdown: str
    content_hash: str


def parse_file(path: Path, repo_root: Path, schema: type[FrontmatterT]) -> ParsedFile:
    raw_bytes = path.read_bytes()
    source_path = path.relative_to(repo_root).as_posix()

    try:
        post = frontmatter.loads(_sanitize_frontmatter_text(raw_bytes.decode("utf-8")))
    except Exception as exc:  # malformed YAML/encoding
        raise ParseError(source_path, f"could not parse frontmatter: {exc}") from exc

    try:
        parsed = schema.model_validate(post.metadata)
    except ValidationError as exc:
        raise ParseError(source_path, f"frontmatter failed validation: {exc}") from exc

    return ParsedFile(
        source_path=source_path,
        frontmatter=parsed,
        body_markdown=post.content.strip(),
        content_hash=hashlib.sha256(raw_bytes).hexdigest(),
    )


def parse_agent(path: Path, repo_root: Path) -> ParsedFile:
    return parse_file(path, repo_root, AgentFrontmatter)


def parse_skill(path: Path, repo_root: Path) -> ParsedFile:
    return parse_file(path, repo_root, SkillFrontmatter)


def parse_command(path: Path, repo_root: Path) -> ParsedFile:
    return parse_file(path, repo_root, CommandFrontmatter)


def parse_knowledge(path: Path, repo_root: Path) -> ParsedFile:
    return parse_file(path, repo_root, KnowledgeFrontmatter)


def parse_about(path: Path, repo_root: Path) -> ParsedFile:
    """CLAUDE.md has no frontmatter -- the whole file is the body."""
    raw_bytes = path.read_bytes()
    source_path = path.relative_to(repo_root).as_posix()
    return ParsedFile(
        source_path=source_path,
        frontmatter=EmptyFrontmatter(),
        body_markdown=raw_bytes.decode("utf-8").strip(),
        content_hash=hashlib.sha256(raw_bytes).hexdigest(),
    )

from dataclasses import dataclass
from pathlib import Path


@dataclass
class WalkResult:
    agents: list[Path]
    skills: list[Path]
    commands: list[Path]
    knowledge: list[Path]
    about: Path | None


def walk_source(repo_root: Path) -> WalkResult:
    agents = sorted((repo_root / ".claude" / "agents").glob("*.md"))
    skills = sorted((repo_root / ".claude" / "skills").glob("*/SKILL.md"))
    commands = sorted((repo_root / ".claude" / "commands").glob("*.md"))

    memory_dir = repo_root / "memory"
    knowledge = sorted(
        p for p in memory_dir.rglob("*.md") if p.name != "MEMORY.md"
    ) if memory_dir.is_dir() else []

    about_path = repo_root / "CLAUDE.md"
    about = about_path if about_path.is_file() else None

    return WalkResult(
        agents=agents, skills=skills, commands=commands, knowledge=knowledge, about=about
    )

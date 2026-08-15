import uuid
from pathlib import Path

import git


def is_git_url(source: str) -> bool:
    return source.startswith(("http://", "https://", "git@", "ssh://"))


def clone_or_pull(source: str, ref: str | None, scratch_dir: Path) -> tuple[Path, str | None]:
    """Resolve a sync source to a local, read-only-usable path.

    - A local filesystem path is used as-is (never written to).
    - A git URL is shallow-cloned into scratch on first sync, or fetched +
      hard-reset to the target ref on subsequent syncs of the same source.
      Never writes back to the source remote.

    Returns (local_path, resolved_commit_sha_or_None).
    """
    if not is_git_url(source):
        local_path = Path(source)
        if not local_path.is_dir():
            raise FileNotFoundError(f"Source path does not exist: {source}")
        return local_path, None

    scratch_dir.mkdir(parents=True, exist_ok=True)
    repo_dir = scratch_dir / _slug_for_source(source)

    if repo_dir.is_dir() and (repo_dir / ".git").is_dir():
        repo = git.Repo(repo_dir)
        origin = repo.remotes.origin
        origin.fetch(depth=1)
        target = f"origin/{ref}" if ref else "origin/HEAD"
        repo.git.reset("--hard", target)
    else:
        clone_kwargs = {"depth": 1}
        if ref:
            clone_kwargs["branch"] = ref
        repo = git.Repo.clone_from(source, repo_dir, **clone_kwargs)

    return repo_dir, repo.head.commit.hexsha


def _slug_for_source(source: str) -> str:
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, source)
    return str(namespace)

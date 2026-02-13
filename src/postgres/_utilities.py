from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, assert_never

from postgres._constants import DEFAULT_REPO

if TYPE_CHECKING:
    from postgres._types import Repo


def to_repo_num(
    *, repo: Repo = DEFAULT_REPO, mapping: Mapping[str, int] | None = None
) -> int:
    """Convert a repo number/name to a number."""
    match repo, mapping:
        case int(), _:
            return repo
        case str(), Mapping():
            return mapping[repo]
        case str(), None:
            msg = f"Repo {repo!r} is a string, but mappings were not provided"
            raise ValueError(msg)
        case never:
            assert_never(never)


__all__ = ["to_repo_num"]

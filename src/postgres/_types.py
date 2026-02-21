from __future__ import annotations

from collections.abc import Mapping

type RepoNumOrName[T: str] = T | int
type RepoNameMapping[T: str] = Mapping[T, int]


__all__ = ["RepoNameMapping", "RepoNumOrName"]

from __future__ import annotations

from enum import StrEnum, unique
from typing import assert_never


@unique
class Type(StrEnum):
    full = "full"
    diff = "diff"
    incr = "incr"

    @property
    def desc(self) -> str:
        match self:
            case Type.full:
                return "full"
            case Type.diff:
                return "differential"
            case Type.incr:
                return "incremental"
            case never:
                assert_never(never)


DEFAULT_TYPE = Type.incr


__all__ = ["DEFAULT_TYPE", "Type"]

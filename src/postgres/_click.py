from __future__ import annotations

from typing import TYPE_CHECKING, override

from click import Context, Parameter, ParamType
from utilities.click import Enum, Str, argument, option

from postgres._constants import DEFAULT_REPO, POSTGRES_VERSION
from postgres._enums import Type

if TYPE_CHECKING:
    import postgres._types

# parameters


class Repo(ParamType):
    name = "repo"

    @override
    def __repr__(self) -> str:
        return self.name.upper()

    @override
    def convert(
        self, value: postgres._types.Repo, param: Parameter | None, ctx: Context | None
    ) -> postgres._types.Repo:
        _ = (param, ctx)
        return value


# options


stanza_argument = argument("--stanza", type=Str())
repo_option = option(
    "--repo", type=Repo(), default=DEFAULT_REPO, help="Repo number/name"
)
type_default_option, type_no_default_option = [
    option("--type", "type_", type=Enum(Type), default=d, help="Backup type")
    for d in [Type.incr, None]
]
user_option = option("--user", type=Str(), default=None, help="User to run as")
version_option = option(
    "--version", type=int, default=POSTGRES_VERSION, help="Postgres version"
)


__all__ = [
    "stanza_argument",
    "type_default_option",
    "type_no_default_option",
    "version_option",
]

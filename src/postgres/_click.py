from __future__ import annotations

from typing import TYPE_CHECKING, override

from click import Context, Parameter, ParamType
from utilities.click import Enum, Str, argument, option

from postgres._constants import POSTGRES_VERSION
from postgres._enums import DEFAULT_TYPE, Type

if TYPE_CHECKING:
    import postgres._types


# parameters


class ClickRepo(ParamType):
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
stanza_option = option("--stanza", type=Str(), default=None, help="Stanza name")
repo_option = option("--repo", type=ClickRepo(), default=None, help="Repo number/name")
type_default_option, type_no_default_option = [
    option("--type", "type_", type=Enum(Type), default=d, help="Backup type")
    for d in [DEFAULT_TYPE, None]
]
user_option = option("--user", type=Str(), default=None, help="User to run as")
version_option = option(
    "--version", type=int, default=POSTGRES_VERSION, help="Postgres version"
)


__all__ = [
    "ClickRepo",
    "stanza_argument",
    "stanza_option",
    "type_default_option",
    "type_no_default_option",
    "user_option",
    "version_option",
]

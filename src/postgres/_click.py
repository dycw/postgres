from __future__ import annotations

from typing import TYPE_CHECKING, override

from click import Context, Parameter, ParamType
from utilities.click import Enum, Str, argument, flag, option

from postgres._constants import PROCESS_MAX, VERSION
from postgres._enums import DEFAULT_BACKUP_TYPE, BackupType

if TYPE_CHECKING:
    from postgres._types import RepoNumOrName


# parameters


class ClickRepoNumOrName(ParamType):
    name = "repo num or name"

    @override
    def __repr__(self) -> str:
        return self.name.upper()

    @override
    def convert(
        self, value: RepoNumOrName, param: Parameter | None, ctx: Context | None
    ) -> RepoNumOrName:
        _ = (param, ctx)
        return value


# options


print_option = flag("--print", default=True, help="Print the output to the console")
process_max_option = option(
    "--process-max",
    type=int,
    default=PROCESS_MAX,
    help="Max processes to use for compression/transfer",
)
repo_option = option(
    "--repo", type=ClickRepoNumOrName(), default=None, help="Repo number/name"
)
stanza_argument = argument("stanza", type=Str())
stanza_option = option("--stanza", type=Str(), default=None, help="Stanza name")
type_default_option, type_no_default_option = [
    option("--type", "type_", type=Enum(BackupType), default=d, help="Backup type")
    for d in [DEFAULT_BACKUP_TYPE, None]
]
user_option = option("--user", type=Str(), default=None, help="User to run as")
version_option = option("--version", type=int, default=VERSION, help="Postgres version")


__all__ = [
    "ClickRepoNumOrName",
    "print_option",
    "process_max_option",
    "repo_option",
    "stanza_argument",
    "stanza_option",
    "type_default_option",
    "type_no_default_option",
    "user_option",
    "version_option",
]

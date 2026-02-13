from __future__ import annotations

from shlex import join
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import always_iterable, is_pytest, set_up_logging, to_logger
from utilities.subprocess import run

from postgres import __version__
from postgres._click import (
    repo_option,
    stanza_argument,
    type_default_option,
    user_option,
)
from postgres._constants import DEFAULT_REPO
from postgres._enums import DEFAULT_TYPE
from postgres._utilities import to_repo_num

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from click import Command
    from utilities.types import MaybeIterable

    from postgres._enums import Type
    from postgres._types import Repo


_LOGGER = to_logger(__name__)


##


def backup(
    stanza: str,
    /,
    *,
    repo: MaybeIterable[Repo] = DEFAULT_REPO,
    repo_mapping: Mapping[str, int] | None = None,
    type_: Type = DEFAULT_TYPE,
    user: str | None = None,
) -> None:
    for repo_i in always_iterable(repo):
        _backup_repo(
            stanza, repo=repo_i, repo_mapping=repo_mapping, type_=type_, user=user
        )


def _backup_repo(
    stanza: str,
    /,
    *,
    type_: Type = DEFAULT_TYPE,
    repo: Repo,
    repo_mapping: Mapping[str, int] | None = None,
    user: str | None = None,
) -> None:
    _LOGGER.info("%s backup %r to repo %r...", type_.desc.title(), stanza, repo)
    repo_num = to_repo_num(repo=repo, mapping=repo_mapping)
    _backup_repo(stanza, repo=repo_num, type_=type_)
    parts: list[str] = [
        "pgbackrest",
        f"--repo={repo_mapping}",
        f"--stanza={stanza}",
        f"--type={type_.value}",
        "backup",
    ]
    if user is None:
        run(*parts)
    else:
        run("su", "-", "postgres", input=join(parts))
    _LOGGER.info("Finished %s backup %r to %r ", type_.desc, stanza, repo)


##


def make_backup_cmd(
    *, cli: Callable[..., Command] = command, name: str | None = None
) -> Command:
    @stanza_argument
    @type_default_option
    @repo_option
    @user_option
    def func(*, stanza: str, type_: Type, repo: Repo, user: str | None) -> None:
        if is_pytest():
            return
        set_up_logging(__name__, root=True, log_version=__version__)
        backup(stanza, repo=repo, type_=type_, user=user)

    return cli(name=name, help="Backup a database cluster", **CONTEXT_SETTINGS)(func)


cli = make_backup_cmd()


__all__ = ["backup"]

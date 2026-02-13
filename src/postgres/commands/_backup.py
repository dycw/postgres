from __future__ import annotations

from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import always_iterable, is_pytest, set_up_logging, to_logger

from postgres import __version__
from postgres._click import (
    repo_option,
    stanza_argument,
    type_default_option,
    user_option,
)
from postgres._enums import DEFAULT_TYPE
from postgres._utilities import run_or_as_user, to_repo_num

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
    repo: MaybeIterable[Repo] | None = None,
    repo_mapping: Mapping[str, int] | None = None,
    type_: Type = DEFAULT_TYPE,
    user: str | None = None,
) -> None:
    if repo is None:
        _backup_core(stanza, type_=type_, user=user)
    else:
        for repo_i in always_iterable(repo):
            _backup_core(
                stanza, repo=repo_i, repo_mapping=repo_mapping, type_=type_, user=user
            )


def _backup_core(
    stanza: str,
    /,
    *,
    repo: Repo | None = None,
    repo_mapping: Mapping[str, int] | None = None,
    type_: Type = DEFAULT_TYPE,
    user: str | None = None,
) -> None:
    args: list[str] = ["pgbackrest"]
    if repo is None:
        _LOGGER.info("%s backup %r to default repo...", type_.desc.title(), stanza)
        repo_num = repo
    else:
        _LOGGER.info("%s backup %r to repo %r...", type_.desc.title(), stanza, repo)
        repo_num = to_repo_num(repo=repo, mapping=repo_mapping)
        args.append(f"--repo={repo_num}")
    args.extend([f"--stanza={stanza}", f"--type={type_.value}", "backup"])
    run_or_as_user(*args, user=user, print=True, logger=_LOGGER)
    if repo is None:
        _LOGGER.info("Finished %s backup %r to default repo", type_.desc, stanza)
    else:
        _LOGGER.info("Finished %s backup %r to repo %r", type_.desc, stanza, repo)


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


__all__ = ["backup", "make_backup_cmd"]

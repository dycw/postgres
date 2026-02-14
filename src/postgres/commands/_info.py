from __future__ import annotations

from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest, set_up_logging, to_logger

from postgres import __version__
from postgres._click import (
    repo_option,
    stanza_option,
    type_no_default_option,
    user_option,
)
from postgres._utilities import run_or_as_user, to_repo_num

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from click import Command

    from postgres._enums import BackupType
    from postgres._types import RepoNumOrName


_LOGGER = to_logger(__name__)


##


def info(
    *,
    repo: RepoNumOrName | None = None,
    repo_mapping: Mapping[str, int] | None = None,
    stanza: str | None = None,
    type_: BackupType | None = None,
    user: str | None = None,
) -> None:
    _LOGGER.info("Getting info...")
    args: list[str] = ["pgbackrest"]
    if repo is not None:
        repo_num = to_repo_num(repo=repo, mapping=repo_mapping)
        args.append(f"--repo={repo_num}")
    if stanza is not None:
        args.append(f"--stanza={stanza}")
    if type_ is not None:
        args.append(f"--type={type_.value}")
    run_or_as_user(*args, user=user, print=True, logger=_LOGGER)
    _LOGGER.info("Finished getting info")


##


def make_info_cmd(
    *, cli: Callable[..., Command] = command, name: str | None = None
) -> Command:
    @repo_option
    @stanza_option
    @type_no_default_option
    @user_option
    def func(
        *,
        repo: RepoNumOrName | None,
        stanza: str | None,
        type_: BackupType | None,
        user: str | None,
    ) -> None:
        if is_pytest():
            return
        set_up_logging(__name__, root=True, log_version=__version__)
        info(repo=repo, stanza=stanza, type_=type_, user=user)

    return cli(
        name=name, help="Retrieve information about backups", **CONTEXT_SETTINGS
    )(func)


__all__ = ["info", "make_info_cmd"]

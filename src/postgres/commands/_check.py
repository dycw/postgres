from __future__ import annotations

from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest, set_up_logging, to_logger

from postgres import __version__
from postgres._click import stanza_argument, user_option
from postgres._utilities import run_or_as_user

if TYPE_CHECKING:
    from collections.abc import Callable

    from click import Command


_LOGGER = to_logger(__name__)


##


def check(stanza: str, /, *, user: str | None = None) -> None:
    _LOGGER.info("Checking %r...", stanza)
    run_or_as_user(
        "pgbackrest",
        f"--stanza={stanza}",
        "check",
        user=user,
        print=True,
        logger=_LOGGER,
    )
    _LOGGER.info("Finished checking %r...", stanza)


##


def make_check_cmd(
    *, cli: Callable[..., Command] = command, name: str | None = None
) -> Command:
    @stanza_argument
    @user_option
    def func(*, stanza: str, user: str | None) -> None:
        if is_pytest():
            return
        set_up_logging(__name__, root=True, log_version=__version__)
        check(stanza, user=user)

    return cli(name=name, help="Check the configuration", **CONTEXT_SETTINGS)(func)


__all__ = ["check", "make_check_cmd"]

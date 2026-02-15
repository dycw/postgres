from __future__ import annotations

from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest, set_up_logging, to_logger

from postgres import __version__
from postgres._click import print_option, stanza_option, user_option
from postgres._utilities import run_or_as_user

if TYPE_CHECKING:
    from collections.abc import Callable

    from click import Command


_LOGGER = to_logger(__name__)


##


def start(
    *,
    stanza: str | None = None,
    user: str | None = None,
    print: bool = True,  # noqa: A002
) -> None:
    _LOGGER.info("Starting 'pgbackrest'...")
    args: list[str] = ["pgbackrest"]
    if stanza is None:
        args.append(f"--stanza={stanza}")
    args.append("start")
    run_or_as_user(*args, user=user, print=print, logger=_LOGGER)
    _LOGGER.info("Finished starting 'pgbackrest'")


##


def make_start_cmd(
    *, cli: Callable[..., Command] = command, name: str | None = None
) -> Command:
    @stanza_option
    @user_option
    @print_option
    def func(
        *,
        stanza: str | None,
        user: str | None,
        print: bool,  # noqa: A002
    ) -> None:
        if is_pytest():
            return
        set_up_logging(__name__, root=True, log_version=__version__)
        start(stanza=stanza, user=user, print=print)

    return cli(name=name, help="Allow pgBackRest processes to run", **CONTEXT_SETTINGS)(
        func
    )


__all__ = ["make_start_cmd", "start"]

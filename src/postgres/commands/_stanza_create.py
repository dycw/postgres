from __future__ import annotations

from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest, set_up_logging, to_logger

from postgres import __version__
from postgres._click import print_option, stanza_argument, user_option
from postgres._utilities import run_or_as_user

if TYPE_CHECKING:
    from collections.abc import Callable

    from click import Command


_LOGGER = to_logger(__name__)


##


def stanza_create(
    stanza: str,
    /,
    *,
    user: str | None = None,
    print: bool = True,  # noqa: A002
) -> None:
    _LOGGER.info("Creating stanza...")
    run_or_as_user(
        "pgbackrest",
        f"--stanza={stanza}",
        "stanza-create",
        user=user,
        print=print,
        logger=_LOGGER,
    )
    _LOGGER.info("Finished creating stanza")


##


def make_stanza_create_cmd(
    *, cli: Callable[..., Command] = command, name: str | None = None
) -> Command:
    @stanza_argument
    @user_option
    @print_option
    def func(
        *,
        stanza: str,
        user: str | None,
        print: bool,  # noqa: A002
    ) -> None:
        if is_pytest():
            return
        set_up_logging(__name__, root=True, log_version=__version__)
        stanza_create(stanza, user=user, print=print)

    return cli(name=name, help="Create the required stanza data", **CONTEXT_SETTINGS)(
        func
    )


__all__ = ["make_stanza_create_cmd", "stanza_create"]

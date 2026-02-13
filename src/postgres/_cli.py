from __future__ import annotations

from click import group, version_option
from utilities.click import CONTEXT_SETTINGS

from postgres import __version__
from postgres.commands._backup import make_backup_cmd
from postgres.commands._check import make_check_cmd
from postgres.commands._info import make_info_cmd
from postgres.commands._restore import make_restore_cmd
from postgres.commands._stanza_create import make_stanza_create_cmd
from postgres.commands._start import make_start_cmd
from postgres.commands._stop import make_stop_cmd

backup_cli = make_backup_cmd()
check_cli = make_check_cmd()
info_cli = make_info_cmd()
stanza_create_cli = make_stanza_create_cmd()
restore_cli = make_restore_cmd()
start_cli = make_start_cmd()
stop_cli = make_stop_cmd()


@group(**CONTEXT_SETTINGS)
@version_option(version=__version__)
def group_cli() -> None: ...


_ = make_backup_cmd(cli=group_cli.command, name="backup")
_ = make_check_cmd(cli=group_cli.command, name="check")
_ = make_info_cmd(cli=group_cli.command, name="info")
_ = make_restore_cmd(cli=group_cli.command, name="restore")
_ = make_stanza_create_cmd(cli=group_cli.command, name="stanza-create")
_ = make_start_cmd(cli=group_cli.command, name="start")
_ = make_stop_cmd(cli=group_cli.command, name="stop")


__all__ = [
    "backup_cli",
    "check_cli",
    "group_cli",
    "info_cli",
    "restore_cli",
    "stanza_create_cli",
    "start_cli",
    "stop_cli",
]

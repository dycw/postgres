from __future__ import annotations

from typing import TYPE_CHECKING

from click.testing import CliRunner
from pytest import mark, param
from utilities.constants import MINUTE
from utilities.pytest import skipif_ci, throttle_test
from utilities.subprocess import run

from postgres._cli import (
    backup_cli,
    check_cli,
    group_cli,
    info_cli,
    restore_cli,
    stanza_create_cli,
    start_cli,
    stop_cli,
)

if TYPE_CHECKING:
    from click import Command


class TestCLI:
    @mark.parametrize(
        ("command", "args"),
        [
            # backup
            param(backup_cli, ["stanza"]),
            param(group_cli, ["backup", "stanza"]),
            # check
            param(check_cli, []),
            param(group_cli, ["check"]),
            # info
            param(info_cli, []),
            param(group_cli, ["info"]),
            # restore
            param(restore_cli, ["cluster", "stanza"]),
            param(group_cli, ["restore", "cluster", "stanza"]),
            # stanza-create
            param(stanza_create_cli, ["stanza"]),
            param(group_cli, ["stanza-create", "stanza"]),
            # start
            param(start_cli, []),
            param(group_cli, ["start"]),
            # stop
            param(stop_cli, []),
            param(group_cli, ["stop"]),
            # version
            param(group_cli, ["--version"]),
        ],
    )
    @throttle_test(duration=MINUTE)
    def test_main(self, *, command: Command, args: list[str]) -> None:
        runner = CliRunner()
        result = runner.invoke(command, args)
        assert result.exit_code == 0, result.stderr

    @throttle_test(duration=MINUTE)
    def test_entrypoint(self) -> None:
        run("postgres-cli", "--help")

    @skipif_ci
    @throttle_test(duration=MINUTE)
    def test_justfile(self) -> None:
        run("just", "cli", "--help")

    @mark.parametrize("head", [param([]), param(["just"], marks=skipif_ci)])
    @mark.parametrize(
        "arg",
        [
            param("backup"),
            param("check"),
            param("info"),
            param("restore"),
            param("stanza-create"),
            param("start"),
            param("stop"),
        ],
    )
    @throttle_test(duration=MINUTE)
    def test_entrypoints_and_justfile(self, *, head: list[str], arg: str) -> None:
        run(*head, arg, "--help")

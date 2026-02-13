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
            param(backup_cli, ["path", "local:/tmp"]),
            param(group_cli, ["backup", "path", "local:/tmp"]),
            # check
            param(check_cli, ["local:/tmp", "local:/tmp2"]),
            param(group_cli, ["check", "local:/tmp", "local:/tmp2"]),
            # info
            param(info_cli, ["local:/tmp"]),
            param(group_cli, ["info", "local:/tmp"]),
            # start
            param(start_cli, ["local:/tmp"]),
            param(group_cli, ["start", "local:/tmp"]),
            # restore
            param(restore_cli, ["local:/tmp", "target"]),
            param(group_cli, ["restore", "local:/tmp", "target"]),
            # stanza_create
            param(stanza_create_cli, ["local:/tmp"]),
            param(group_cli, ["stanza_create", "local:/tmp"]),
            # stop
            param(stop_cli, ["local:/tmp"]),
            param(group_cli, ["stop", "local:/tmp"]),
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
        "args",
        [
            param(["backup", "path", "local:/tmp"]),
            param(["check"]),
            param(["info"]),
            param(["start"]),
            param(["restore"]),
            param(["stanza_create"]),
            param(["stop"]),
        ],
    )
    @throttle_test(duration=MINUTE)
    def test_entrypoints_and_justfile(
        self, *, head: list[str], args: list[str]
    ) -> None:
        run(*head, *args, "--help")

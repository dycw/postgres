from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from click import Command, command
from installer import get_root
from utilities.click import CONTEXT_SETTINGS, Str, argument, option
from utilities.core import is_pytest, set_up_logging, to_logger
from utilities.subprocess import run
from utilities.types import PathLike

from postgres import __version__
from postgres._click import (
    print_option,
    repo_option,
    stanza_argument,
    user_option,
    version_option,
)
from postgres._constants import VERSION
from postgres._utilities import run_or_as_user, to_repo_num

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from utilities.types import PathLike

    from postgres._types import RepoNumOrName


_LOGGER = to_logger(__name__)


##


def restore(
    cluster: str,
    stanza: str,
    /,
    *,
    version: int = VERSION,
    repo: RepoNumOrName | None = None,
    repo_mapping: Mapping[str, int] | None = None,
    target_timeline: int | None = None,
    user: str | None = None,
    print: bool = True,  # noqa: A002
) -> None:
    _LOGGER.info("Restoring Postgres...")
    _stop_cluster(cluster, version=version)
    _delete_data(cluster, version=version)
    _run_restore(
        stanza,
        repo=repo,
        repo_mapping=repo_mapping,
        target_timeline=target_timeline,
        user=user,
        print=print,
    )
    _start_cluster(cluster, version=version)
    _LOGGER.info("Finished restoring Postgres")


def _stop_cluster(cluster: str, /, *, version: int = VERSION) -> None:
    _LOGGER.info("Stopping cluster '%d-%s'...", version, cluster)
    run("pg_ctlcluster", str(version), cluster, "stop", suppress=True)


def _delete_data(
    name: str, /, *, version: int = VERSION, root: PathLike | None = None
) -> None:
    _LOGGER.info("Deleting cluster '%d-%s' data...", version, name)
    path = get_root(root=root) / f"var/lib/postgresql/{version}/{name}"
    run("find", str(path), "-mindepth", "1", "-delete")


def _run_restore(
    stanza: str,
    /,
    *,
    repo: RepoNumOrName | None = None,
    repo_mapping: Mapping[str, int] | None = None,
    target_timeline: int | None = None,
    user: str | None = None,
    print: bool = True,  # noqa: A002
) -> None:
    args: list[str] = ["pgbackrest"]
    if repo is None:
        _LOGGER.info("Restoring default repo to %r...", stanza)
    else:
        _LOGGER.info("Restoring repo %r to %r...", repo, stanza)
        repo_num = to_repo_num(repo=repo, mapping=repo_mapping)
        args.append(f"--repo={repo_num}")
    args.append(f"--stanza={stanza}")
    if target_timeline is not None:
        args.append(f"--target-timeline={target_timeline}")
    args.append("restore")
    run_or_as_user(*args, user=user, print=print, logger=_LOGGER)
    if repo is None:
        _LOGGER.info("Finished restoring default repo to %r...", stanza)
    else:
        _LOGGER.info("Finished restoring repo %r to %r", repo, stanza)


def _start_cluster(name: str, /, *, version: int = VERSION) -> None:
    _LOGGER.info("Starting cluster %r...", name)
    run("pg_ctlcluster", str(version), name, "start")


##


def make_restore_cmd(
    *, cli: Callable[..., Command] = command, name: str | None = None
) -> Command:
    @argument("cluster", type=Str())
    @stanza_argument
    @version_option
    @repo_option
    @option(
        "--target-timeline", type=int, default=None, help="Recover along a timeline"
    )
    @user_option
    @print_option
    def func(
        *,
        cluster: str,
        stanza: str,
        version: int,
        repo: RepoNumOrName | None,
        target_timeline: int | None,
        user: str | None,
        print: bool,  # noqa: A002
    ) -> None:
        if is_pytest():
            return
        set_up_logging(__name__, root=True, log_version=__version__)
        restore(
            cluster,
            stanza,
            version=version,
            repo=repo,
            target_timeline=target_timeline,
            user=user,
            print=print,
        )

    return cli(name=name, help="Restore a database cluster", **CONTEXT_SETTINGS)(func)


__all__ = ["make_restore_cmd", "restore"]

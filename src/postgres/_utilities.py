from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from shlex import join
from typing import TYPE_CHECKING, assert_never

from installer import get_root
from utilities.core import to_logger
from utilities.subprocess import maybe_sudo_cmd, run

from postgres._constants import VERSION

if TYPE_CHECKING:
    from utilities.types import LoggerLike, PathLike, Retry, StrStrMapping

    from postgres._types import Restorable


_LOGGER = to_logger(__name__)


##


def drop_cluster(name: str, /, *, version: int = VERSION, sudo: bool = False) -> None:
    """Drop a cluster."""
    _LOGGER.info("Dropping cluster '%d-%s'...", version, name)
    args: list[str] = ["pg_dropcluster", "--stop", str(version), name]
    run(*maybe_sudo_cmd(*args, sudo=sudo), suppress=True)


##


def get_pg_root(
    *, root: PathLike | None = None, version: int | None = None, name: str | None = None
) -> Path:
    """Get the Postgres root directory."""
    parts: list[PathLike] = [get_root(root=root), "etc/postgresql"]
    match version, name:
        case None, None:
            ...
        case int(), None:
            parts.append(str(version))
        case None, str():
            msg = f"Expected 'version' if 'name' ({name!r}) is given"
            raise ValueError(msg)
        case int(), str():
            parts.extend([str(version), name])
        case never:
            assert_never(never)
    return Path(*parts)


##


def to_repo_num(
    *, repo: Restorable | None = None, mapping: Mapping[str, int] | None = None
) -> int:
    """Convert a repo number/name to a number."""
    match repo, mapping:
        case int(), _:
            return repo
        case None, _:
            return 1
        case str(), Mapping():
            return mapping[repo]
        case str(), None:
            msg = f"Repo {repo!r} is a string, but mappings were not provided"
            raise ValueError(msg)
        case never:
            assert_never(never)


##


def run_or_as_user(
    cmd: str,
    /,
    *args: str,
    executable: str | None = None,
    shell: bool = False,
    cwd: PathLike | None = None,
    env: StrStrMapping | None = None,
    user: str | int | None = None,
    print: bool = False,  # noqa: A002
    print_stdout: bool = False,
    print_stderr: bool = False,
    suppress: bool = False,
    retry: Retry | None = None,
    retry_skip: Callable[[int, str, str], bool] | None = None,
    logger: LoggerLike | None = None,
) -> None:
    if user is None:
        run(
            cmd,
            *args,
            executable=executable,
            shell=shell,
            cwd=cwd,
            env=env,
            print=print,
            print_stdout=print_stdout,
            print_stderr=print_stderr,
            suppress=suppress,
            retry=retry,
            retry_skip=retry_skip,
            logger=logger,
        )
    else:
        run(
            "su",
            "-",
            str(user),
            executable=executable,
            shell=shell,
            cwd=cwd,
            env=env,
            input=join([cmd, *args]),
            print=print,
            print_stdout=print_stdout,
            print_stderr=print_stderr,
            suppress=suppress,
            retry=retry,
            retry_skip=retry_skip,
            logger=logger,
        )


__all__ = ["drop_cluster", "get_pg_root", "run_or_as_user", "to_repo_num"]

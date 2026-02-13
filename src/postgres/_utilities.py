from __future__ import annotations

from collections.abc import Callable, Mapping
from shlex import join
from typing import TYPE_CHECKING, assert_never

from utilities.subprocess import run

from postgres._constants import DEFAULT_REPO

if TYPE_CHECKING:
    from utilities.types import LoggerLike, PathLike, Retry, StrStrMapping

    from postgres._types import Repo


def to_repo_num(
    *, repo: Repo = DEFAULT_REPO, mapping: Mapping[str, int] | None = None
) -> int:
    """Convert a repo number/name to a number."""
    match repo, mapping:
        case int(), _:
            return repo
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


__all__ = ["to_repo_num"]

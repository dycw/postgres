from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import utilities.click
from click import Command, command
from installer import get_root, set_up_pgbackrest, set_up_postgres, ssh_option
from utilities.click import CONTEXT_SETTINGS, Str, argument
from utilities.core import TemporaryFile, get_local_ip, is_pytest, to_logger
from utilities.pydantic import extract_secret
from utilities.subprocess import chown, copy_text, maybe_sudo_cmd, rm, run

from postgres._constants import PATH_CONFIGS, PORT, PROCESSES, VERSION
from postgres._enums import DEFAULT_CIPHER_TYPE, DEFAULT_REPO_TYPE, CipherType, RepoType
from postgres._utilities import drop_cluster, get_pg_root, run_or_as_user

if TYPE_CHECKING:
    from collections.abc import Callable

    import pydantic
    from utilities.types import PathLike, SecretLike


_LOGGER = to_logger(__name__)


##


def set_up(
    name: str,
    password: SecretLike,
    repo: RepoSpec,
    /,
    *repos: RepoSpec,
    sudo: bool = False,
    version: int = VERSION,
    port: int = PORT,
    root: PathLike | None = None,
) -> None:
    _LOGGER.info("Setting up Postgres & pgBackRest...")
    set_up_postgres(sudo=sudo)
    set_up_pgbackrest(sudo=sudo)
    drop_cluster("main", version=version, sudo=sudo)
    drop_cluster(name, version=version, sudo=sudo)
    _create_cluster(name, version=version, port=port, sudo=sudo)
    _set_up_pg_hba(name, version=version, root=root, sudo=sudo)
    _set_up_postgresql_conf(name, version=version, root=root, sudo=sudo)
    _remove_debian_pgbackrest_conf(root=root, sudo=sudo)
    _set_up_pgbackrest(name, repo, *repos, root=root, sudo=sudo, version=version)
    _change_ownership(root=root, sudo=sudo)
    _restart_cluster(name, sudo=sudo, version=version)
    _set_postgres_password(password)
    _LOGGER.info("Finished setting up Postgres & pgBackRest")


def _create_cluster(
    name: str, /, *, version: int = VERSION, port: int = PORT, sudo: bool = False
) -> None:
    _LOGGER.info("Creating cluster '%d-%s'...", version, name)
    args: list[str] = ["pg_createcluster", "--port", str(port), str(version), name]
    run(*maybe_sudo_cmd(*args, sudo=sudo))


def _set_up_pg_hba(
    name: str,
    /,
    *,
    version: int = VERSION,
    root: PathLike | None = None,
    sudo: bool = False,
) -> None:
    _LOGGER.info("Setting up '%d-pg_hba.conf'...", version)
    pg_root = get_pg_root(root=root, version=version, name=name)
    copy_text(
        PATH_CONFIGS / "pg_hba_conf.conf",
        pg_root / "pg_hba.conf",
        sudo=sudo,
        perms="u=rw,g=r,o=r",
    )
    copy_text(
        PATH_CONFIGS / "pg_hba.custom.conf",
        pg_root / "pg_hba.conf.d/custom.conf",
        sudo=sudo,
        perms="u=rw,g=r,o=r",
    )


def _set_up_postgresql_conf(
    name: str,
    /,
    *,
    version: int = VERSION,
    root: PathLike | None = None,
    sudo: bool = False,
) -> None:
    _LOGGER.info("Setting up '%d-postgresql.conf'...", version)
    pg_root = get_pg_root(root=root, version=version, name=name)
    copy_text(
        PATH_CONFIGS / "postgresql.conf",
        pg_root / "conf.d/custom.conf",
        sudo=sudo,
        substitutions={"LISTEN_ADDRESSES": get_local_ip(), "CLUSTER": name},
        perms="u=rw,g=r,o=r",
    )


def _remove_debian_pgbackrest_conf(
    *, root: PathLike | None = None, sudo: bool = False
) -> None:
    _LOGGER.info("Removing Debian 'pgbackrest.conf'...")
    path = get_root(root=root) / "etc/pgbackrest.conf"
    rm(path, sudo=sudo)


def _set_up_pgbackrest(
    name: str,
    repo: RepoSpec,
    /,
    *repos: RepoSpec,
    root: PathLike | None = None,
    sudo: bool = False,
    processes: int = PROCESSES,
    version: int = VERSION,
) -> None:
    _LOGGER.info("Setting up 'pgbackrest.conf'...")
    dest = get_root(root=root) / "etc/pgbackrest/pgbackrest.conf"
    all_repos = [repo, *repos]
    copy_text(
        PATH_CONFIGS / "pgbackrest.conf",
        dest,
        sudo=sudo,
        substitutions={
            "PROCESS_MAX": processes,
            "REPOS": "".join(r.text for r in all_repos),
            "NAME": name,
            "VERSION": version,
        },
        perms="u=rw,g=r,o=r",
    )


def _change_ownership(*, root: PathLike | None = None, sudo: bool = False) -> None:
    _LOGGER.info("Changing ownership of 'postgres'...")
    path = get_pg_root(root=root)
    chown(path, sudo=sudo, recursive=True, owner="postgres", group="postgres")


def _restart_cluster(
    name: str, /, *, sudo: bool = False, version: int = VERSION
) -> None:
    _LOGGER.info("Restarting cluster...")
    args: list[str] = ["pg_ctlcluster", str(version), name, "restart"]
    run(*maybe_sudo_cmd(*args, sudo=sudo))


def _set_postgres_password(password: SecretLike, /) -> None:
    _LOGGER.info("Setting 'postgres' role password...")
    cmd = f"ALTER ROLE postgres WITH PASSWORD '{extract_secret(password)}';"
    with TemporaryFile(text=cmd, perms="u=rw,g=r,o=r") as temp:
        run_or_as_user("psql", "-f", str(temp), user="postgres")


##


@dataclass(order=True, unsafe_hash=True, slots=True)
class RepoSpec:
    path: Path = field(kw_only=True)
    n: int = field(default=1)
    cipher_pass: pydantic.SecretStr | None = field(default=None, kw_only=True)
    cipher_type: CipherType | None = field(default=DEFAULT_CIPHER_TYPE, kw_only=True)
    repo_type: RepoType = field(default=DEFAULT_REPO_TYPE, kw_only=True)
    retention_diff: int | None = field(default=None, kw_only=True)
    retention_full: int | None = field(default=None, kw_only=True)
    s3_bucket: Path | None = field(default=None, kw_only=True)
    s3_endpoint: str | None = field(default=None, kw_only=True)
    s3_key: pydantic.SecretStr | None = field(default=None, kw_only=True)
    s3_key_secret: pydantic.SecretStr | None = field(default=None, kw_only=True)
    s3_region: str | None = field(default=None, kw_only=True)

    @property
    def text(self) -> str:
        raise NotImplementedError

    @property
    def _path_leading(self) -> Path:
        return Path("/") / self.path


##


def make_set_up_cmd(
    *, cli: Callable[..., Command] = command, name: str | None = None
) -> Command:
    @argument("name", type=Str())
    @argument("password", type=utilities.click.SecretStr())
    @ssh_option
    @option(
        "--os-password",
        type=SecretStr(),
        default=INFRA_UTILITIES_SETTINGS.os.password,
        help="OS password",
    )
    @option(
        "--port", type=int, default=POSTGRES_SETTINGS.postgres.port, help="Cluster port"
    )
    @version_option
    @option(
        "--name",
        type=Str(),
        default=POSTGRES_SETTINGS.postgres.name,
        help="Cluster name",
    )
    @option(
        "--pg-password",
        type=SecretStr(),
        default=POSTGRES_SETTINGS.postgres.password,
        help="Postgres password",
    )
    def set_up_sub_cmd(
        *,
        ssh: str | None,
        os_password: SecretLike | None,
        port: int,
        version: int,
        name: str,
        pg_password: SecretLike,
    ) -> None:
        if is_pytest():
            return
        set_up(
            ssh=ssh,
            os_password=os_password,
            port=port,
            version=version,
            name=name,
            password=pg_password,
        )

    return cli(name=name, help="Set up 'pgbackrest'", **CONTEXT_SETTINGS)(func)


__all__ = ["make_set_up_cmd", "set_up"]

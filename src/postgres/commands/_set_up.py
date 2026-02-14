from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from installer import get_root, set_up_pgbackrest, set_up_postgres
from pydantic import SecretStr
from utilities.core import get_local_ip, substitute, to_logger
from utilities.subprocess import copy_text, maybe_sudo_cmd, rm, run

from postgres._constants import PATH_CONFIGS, PORT, VERSION
from postgres._enums import DEFAULT_REPO_TYPE, RepoType
from postgres._utilities import drop_cluster

if TYPE_CHECKING:
    from utilities.types import PathLike, SecretLike

_LOGGER = to_logger(__name__)


##


def set_up(
    name: str,
    password: SecretLike,
    /,
    *,
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
    _set_up_pgbackrest(name, root=root, sudo=sudo, version=version)
    _change_ownership()
    _restart_cluster(version=version, name=name)
    _set_postgres_password(password=password)
    ensure_git_clone("gitea", "qrt", "postgres")
    _LOGGER.info("Finished setting up Postgres")


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
    pg_root = _get_pg_root(name, root=root, version=version)
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


def _get_pg_root(
    name: str, /, *, root: PathLike | None = None, version: int = VERSION
) -> Path:
    return get_root(root=root) / "etc/postgresql" / str(version) / name


def _set_up_postgresql_conf(
    name: str,
    /,
    *,
    version: int = VERSION,
    root: PathLike | None = None,
    sudo: bool = False,
) -> None:
    _LOGGER.info("Setting up '%d-postgresql.conf'...", version)
    pg_root = _get_pg_root(name, root=root, version=version)
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
    /,
    *,
    root: PathLike | None = None,
    sudo: bool = False,
    version: int = VERSION,
) -> None:
    _LOGGER.info("Setting up 'pgbackrest.conf'...")
    dest = get_root(root=root) / "etc/pgbackrest/pgbackrest.conf"
    copy_text(
        PATH_CONFIGS / "pgbackrest.conf",
        dest,
        substitutions={
            "PROCESS_MAX": max(round(CPU_COUNT / 4), 1),
            "CIPHER_PASS": POSTGRES_SETTINGS.pgbackrest.cipher_pass.get_secret_value(),
            "TRUENAS_PATH": _ensure_leading_slash(
                MOUNT_SETTINGS.datasets.postgres.local
            ),
            "TRUENAS_RETENTION_DIFF": POSTGRES_SETTINGS.backup.truenas.retention.diff,
            "TRUENAS_RETENTION_FULL": POSTGRES_SETTINGS.backup.truenas.retention.full,
            "BACKBLAZE_QRT_PATH": _ensure_leading_slash(
                POSTGRES_SETTINGS.backup.backblaze.qrt.path
            ),
            "BACKBLAZE_QRT_RETENTION_DIFF": POSTGRES_SETTINGS.backup.backblaze.qrt.retention.diff,
            "BACKBLAZE_QRT_RETENTION_FULL": POSTGRES_SETTINGS.backup.backblaze.qrt.retention.full,
            "BACKBLAZE_QRT_BUCKET": qrt.bucket,
            "BACKBLAZE_QRT_ENDPOINT": qrt.endpoint,
            "BACKBLAZE_QRT_APPLICATION_KEY": qrt.application_key.get_secret_value(),
            "BACKBLAZE_QRT_KEY_ID": qrt.key_id.get_secret_value(),
            "BACKBLAZE_QRT_REGION": qrt.region,
            "BACKBLAZE_DYCW_PATH": _ensure_leading_slash(
                POSTGRES_SETTINGS.backup.backblaze.dycw.path
            ),
            "BACKBLAZE_DYCW_RETENTION_DIFF": POSTGRES_SETTINGS.backup.backblaze.dycw.retention.diff,
            "BACKBLAZE_DYCW_RETENTION_FULL": POSTGRES_SETTINGS.backup.backblaze.dycw.retention.full,
            "BACKBLAZE_DYCW_BUCKET": dycw.bucket,
            "BACKBLAZE_DYCW_ENDPOINT": dycw.endpoint,
            "BACKBLAZE_DYCW_APPLICATION_KEY": dycw.application_key.get_secret_value(),
            "BACKBLAZE_DYCW_KEY_ID": dycw.key_id.get_secret_value(),
            "BACKBLAZE_DYCW_REGION": dycw.region,
            "NAME": name,
            "VERSION": version,
        },
        perms="u=rw,g=r,o=r",
    )


def _ensure_leading_slash(path: PathLike, /) -> Path:
    return Path("/") / path


def _change_ownership(*, __root: PathLike | None = None) -> None:
    _LOGGER.info("Changing ownership of 'postgres'...")
    root = FILE_SYSTEM_ROOT if __root is None else Path(__root)
    path = root / "etc/postgresql"
    chown(path, recursive=True, user="postgres", group="postgres")


def _restart_cluster(
    *,
    version: int = POSTGRES_SETTINGS.postgres.version,
    name: str = POSTGRES_SETTINGS.postgres.name,
) -> None:
    _LOGGER.info("Restarting cluster...")
    run("pg_ctlcluster", str(version), name, "restart")


def _set_postgres_password(
    *, password: SecretLike = POSTGRES_SETTINGS.postgres.password
) -> None:
    _LOGGER.info("Setting 'postgres' role password...")
    cmd = f"ALTER ROLE postgres WITH PASSWORD '{extract_secret(password)}';"
    with TemporaryFile(text=cmd) as temp:
        chmod(temp, "u=rw,g=r,o=r")
        run("psql", "-f", str(temp), user="postgres")


##


def _set_up_remote(
    user: str,
    hostname: str,
    /,
    *,
    os_password: SecretLike | None = None,
    port: int = POSTGRES_SETTINGS.postgres.port,
    version: int = POSTGRES_SETTINGS.postgres.version,
    name: str = POSTGRES_SETTINGS.postgres.name,
    pg_password: SecretLike = POSTGRES_SETTINGS.postgres.password,
) -> None:
    _LOGGER.info("Setting up Postgres on %r...", hostname)
    cmd_and_args = uv_tool_run_set_up_cmd(
        os_password=os_password,
        port=port,
        version=version,
        name=name,
        pg_password=pg_password,
    )
    ssh(
        user,
        hostname,
        *BASH_LS,
        input=join(cmd_and_args),
        print=True,
        retry=INFRA_UTILITIES_SETTINGS.ssh_retry,
        logger=_LOGGER,
    )
    _LOGGER.info("Finished setting up Postgres on %r...", hostname)


##


@dataclass(order=True, unsafe_hash=True, slots=True)
class Repo:
    path: Path = field(kw_only=True)
    n: int = field(default=1)
    cipher_pass: SecretStr | None = field(default=None, kw_only=True)
    repo_type: RepoType = field(default=DEFAULT_REPO_TYPE, kw_only=True)

    @property
    def text(self) -> str:
        return substitute(
            (PATH_CONFIGS / "job.tmpl"),
            SCHEDULE=self.schedule,
            USER=self.user,
            NAME=self.name,
            TIMEOUT=round(duration_to_seconds(self.timeout)),
            KILL_AFTER=round(duration_to_seconds(self.kill_after)),
            COMMAND=self.command,
            COMMAND_ARGS_SPACE=" "
            if (self.args is not None) and (len(self.args) >= 1)
            else "",
            SUDO="sudo" if self.sudo else "",
            SUDO_TEE_SPACE=" " if self.sudo else "",
            ARGS="" if self.args is None else " ".join(self.args),
            LOG=self.log_use,
        )


##


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
    "--name", type=Str(), default=POSTGRES_SETTINGS.postgres.name, help="Cluster name"
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


__all__ = ["make_set_up_cmd", "set_up"]

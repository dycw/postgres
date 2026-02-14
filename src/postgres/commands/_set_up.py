from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Self, assert_never

import utilities.click
from click import Command, command
from installer import (
    get_root,
    root_option,
    set_up_pgbackrest,
    set_up_postgres,
    sudo_option,
)
from pydantic import SecretStr
from utilities.click import CONTEXT_SETTINGS, Enum, Str, argument, option
from utilities.constants import Sentinel, sentinel
from utilities.core import (
    TemporaryFile,
    get_local_ip,
    is_pytest,
    kebab_case,
    normalize_str,
    replace_non_sentinel,
    set_up_logging,
    to_logger,
)
from utilities.dataclasses import yield_fields
from utilities.pydantic import ensure_secret, extract_secret
from utilities.subprocess import chown, copy_text, maybe_sudo_cmd, rm, run

from postgres import __version__
from postgres._constants import PATH_CONFIGS, PORT, PROCESS_MAX, VERSION
from postgres._enums import DEFAULT_REPO_TYPE, CipherType, RepoType
from postgres._utilities import drop_cluster, get_pg_root, run_or_as_user

if TYPE_CHECKING:
    from collections.abc import Callable

    import pydantic
    from utilities.types import PathLike, SecretLike


_LOGGER = to_logger(__name__)


##


def set_up(
    cluster: str,
    stanza: str,
    repo: RepoSpec,
    /,
    *repos: RepoSpec,
    sudo: bool = False,
    version: int = VERSION,
    port: int = PORT,
    root: PathLike | None = None,
    process_max: int = PROCESS_MAX,
    password: SecretLike | None = None,
) -> None:
    """Set up 'postgres' and 'pgbackrest'."""
    _LOGGER.info("Setting up 'postgres' & 'pgbackrest'...")
    set_up_postgres(sudo=sudo)
    set_up_pgbackrest(sudo=sudo)
    drop_cluster("main", version=version, sudo=sudo)
    drop_cluster(cluster, version=version, sudo=sudo)
    _create_cluster(cluster, version=version, port=port, sudo=sudo)
    _set_up_pg_hba(cluster, version=version, root=root, sudo=sudo)
    _set_up_postgresql_conf(cluster, version=version, root=root, sudo=sudo)
    _remove_debian_pgbackrest_conf(root=root, sudo=sudo)
    _set_up_pgbackrest(
        cluster,
        stanza,
        repo,
        *repos,
        version=version,
        root=root,
        sudo=sudo,
        process_max=process_max,
    )
    _change_ownership(root=root, sudo=sudo)
    _restart_cluster(cluster, version=version, sudo=sudo)
    if password is not None:
        _set_postgres_password(password)
    _LOGGER.info("Finished setting up 'postgres' & 'pgbackrest'")


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
    _LOGGER.info("Setting up '%d-%s' 'pg_hba.conf'...", version, name)
    pg_root = get_pg_root(root=root, version=version, name=name)
    copy_text(
        PATH_CONFIGS / "pg_hba.conf",
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
    _LOGGER.info("Setting up '%d-%s' 'postgresql.conf'...", version, name)
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
    cluster: str,
    stanza: str,
    repo: RepoSpec,
    /,
    *repos: RepoSpec,
    version: int = VERSION,
    root: PathLike | None = None,
    sudo: bool = False,
    process_max: int = PROCESS_MAX,
) -> None:
    _LOGGER.info("Setting up '%d-%s-%s' 'pgbackrest.conf'...", version, cluster, stanza)
    dest = get_root(root=root) / "etc/pgbackrest/pgbackrest.conf"
    all_repos = [repo, *repos]
    all_repos = [r.replace(n=n) for n, r in enumerate(all_repos, start=1)]
    copy_text(
        PATH_CONFIGS / "pgbackrest.conf",
        dest,
        sudo=sudo,
        substitutions={
            "PROCESS_MAX": process_max,
            "REPOS": "\n".join(r.text for r in all_repos).rstrip("\n"),
            "STANZA": stanza,
            "VERSION": version,
            "CLUSTER": cluster,
        },
        perms="u=rw,g=r,o=r",
    )


def _change_ownership(*, root: PathLike | None = None, sudo: bool = False) -> None:
    _LOGGER.info("Changing ownership of 'postgres'...")
    path = get_pg_root(root=root)
    chown(path, sudo=sudo, recursive=True, owner="postgres", group="postgres")


def _restart_cluster(
    name: str, /, *, version: int = VERSION, sudo: bool = False
) -> None:
    _LOGGER.info("Restarting cluster '%d-%s'...", version, name)
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
    path: Path = field()
    n: int = field(default=1, kw_only=True)
    cipher_pass: pydantic.SecretStr | None = field(default=None, kw_only=True)
    cipher_type: CipherType | None = field(default=None, kw_only=True)
    retention_diff: int | None = field(default=None, kw_only=True)
    retention_full: int | None = field(default=None, kw_only=True)
    type: RepoType = field(default=DEFAULT_REPO_TYPE, kw_only=True)
    s3_bucket: str | None = field(default=None, kw_only=True)
    s3_endpoint: str | None = field(default=None, kw_only=True)
    s3_key: pydantic.SecretStr | None = field(default=None, kw_only=True)
    s3_key_secret: pydantic.SecretStr | None = field(default=None, kw_only=True)
    s3_region: str | None = field(default=None, kw_only=True)

    def replace(
        self,
        *,
        path: Path | Sentinel = sentinel,
        n: int | Sentinel = sentinel,
        cipher_pass: pydantic.SecretStr | None | Sentinel = sentinel,
        cipher_type: CipherType | None | Sentinel = sentinel,
        retention_diff: int | None | Sentinel = sentinel,
        retention_full: int | None | Sentinel = sentinel,
        type: RepoType | None | Sentinel = sentinel,  # noqa: A002
        s3_bucket: str | None | Sentinel = sentinel,
        s3_endpoint: str | None | Sentinel = sentinel,
        s3_key: pydantic.SecretStr | None | Sentinel = sentinel,
        s3_key_secret: pydantic.SecretStr | None | Sentinel = sentinel,
        s3_region: str | None | Sentinel = sentinel,
    ) -> Self:
        return replace_non_sentinel(
            self,
            path=path,
            n=n,
            cipher_pass=cipher_pass,
            cipher_type=cipher_type,
            retention_diff=retention_diff,
            retention_full=retention_full,
            type=type,
            s3_bucket=s3_bucket,
            s3_endpoint=s3_endpoint,
            s3_key=s3_key,
            s3_key_secret=s3_key_secret,
            s3_region=s3_region,
        )

    @property
    def text(self) -> str:
        lines: list[str] = []
        for fld in yield_fields(self):
            match fld.name, fld.value:
                case "path" as name, Path():
                    value = Path("/") / fld.value
                case str() as name, SecretStr():
                    value = fld.value.get_secret_value()
                case (name, value) if (name != "n") and (value is not None):
                    ...
                case _, _:
                    name = value = None
                case never:
                    assert_never(never)
            if (name is not None) and (value is not None):
                key = f"repo{self.n}-{kebab_case(name)}"
                lines.append(f"{key} = {value}")
        return normalize_str("\n".join(lines))


##


def make_set_up_cmd(
    *, cli: Callable[..., Command] = command, name: str | None = None
) -> Command:
    @argument("cluster", type=Str())
    @argument("stanza", type=Str())
    @argument("path", type=utilities.click.Path(exist="dir if exists"))
    @option(
        "--cipher-pass",
        type=utilities.click.SecretStr(),
        default=None,
        help="Repository cipher passphrase",
    )
    @option(
        "--cipher-type",
        type=Enum(CipherType),
        default=None,
        help="Cipher used to encrypt the repository",
    )
    @option(
        "--retention-diff",
        type=int,
        default=None,
        help="Number of differential backups to retain",
    )
    @option(
        "--retention-full",
        type=int,
        default=None,
        help="Full backup retention count/time",
    )
    @option(
        "--type",
        "type_",
        type=Enum(RepoType),
        default=DEFAULT_REPO_TYPE,
        help="Type of storage used for the repository",
    )
    @option("--s3-bucket", type=Str(), default=None, help="S3 repository bucket")
    @option("--s3-endpoint", type=Str(), default=None, help="S3 repository endpoint")
    @option(
        "--s3-key",
        type=utilities.click.SecretStr(),
        default=None,
        help="S3 repository access key",
    )
    @option(
        "--s3-key-secret",
        type=utilities.click.SecretStr(),
        default=None,
        help="S3 repository secret access key",
    )
    @option("--s3-region", type=Str(), default=None, help="S3 repository region")
    @sudo_option
    @option("--port", type=int, default=PORT, help="Cluster port")
    @root_option
    @option(
        "--process-max",
        type=int,
        default=PROCESS_MAX,
        help="Max processes to use for compression/transfer",
    )
    @option(
        "--password",
        type=utilities.click.SecretStr(),
        default=None,
        help="'postgres' user password",
    )
    def func(
        *,
        cluster: str,
        stanza: str,
        path: PathLike,
        cipher_pass: SecretLike | None,
        cipher_type: CipherType | None,
        retention_diff: int | None,
        retention_full: int | None,
        type_: RepoType,
        s3_bucket: str | None,
        s3_endpoint: str | None,
        s3_key: SecretLike | None,
        s3_key_secret: SecretLike | None,
        s3_region: str | None,
        sudo: bool = False,
        version: int = VERSION,
        port: int = PORT,
        root: PathLike | None,
        process_max: int,
        password: SecretLike | None,
    ) -> None:
        if is_pytest():
            return
        set_up_logging(__name__, root=True, log_version=__version__)
        repo = RepoSpec(
            Path(path),
            cipher_pass=None if cipher_pass is None else ensure_secret(cipher_pass),
            cipher_type=cipher_type,
            retention_diff=retention_diff,
            retention_full=retention_full,
            type=type_,
            s3_bucket=s3_bucket,
            s3_endpoint=s3_endpoint,
            s3_key=None if s3_key is None else ensure_secret(s3_key),
            s3_key_secret=None
            if s3_key_secret is None
            else ensure_secret(s3_key_secret),
            s3_region=s3_region,
        )
        set_up(
            cluster,
            stanza,
            repo,
            sudo=sudo,
            version=version,
            port=port,
            root=root,
            process_max=process_max,
            password=password,
        )

    return cli(
        name=name, help="Set up 'postgres' and 'pgbackrest'", **CONTEXT_SETTINGS
    )(func)


__all__ = ["RepoSpec", "make_set_up_cmd", "set_up"]

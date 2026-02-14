from __future__ import annotations

from pathlib import Path

from utilities.core import normalize_multi_line_str

from postgres.commands._set_up import (
    RepoSpec,
    _set_up_pg_hba,
    _set_up_pgbackrest,
    _set_up_postgresql_conf,
)


class TestSetUpPGHBA:
    def test_main(self, *, tmp_path: Path) -> None:
        _set_up_pg_hba("name", root=tmp_path)
        assert (tmp_path / "etc/postgresql/17/name/pg_hba.conf").is_file()
        assert (tmp_path / "etc/postgresql/17/name/pg_hba.conf.d/custom.conf").is_file()


class TestSetUpPGBackrest:
    def test_single(self, *, tmp_path: Path) -> None:
        repo = RepoSpec(Path("path"))
        _set_up_pgbackrest("cluster", "stanza", repo, root=tmp_path)
        result = (tmp_path / "etc/pgbackrest/pgbackrest.conf").read_text()
        expected = normalize_multi_line_str("""
            [global]
            archive-async=y
            archive-check=y
            process-max=1
            log-level-console=info
            start-fast=y

            repo1-path = path
            repo1-repo-type = posix

            [global:archive-push]
            compress-level=3

            [stanza]
            pg1-path=/var/lib/postgresql/17/cluster
        """)
        assert result == expected

    def test_multiple(self, *, tmp_path: Path) -> None:
        repo1 = RepoSpec(Path("path1"))
        repo2 = RepoSpec(Path("path2"))
        _set_up_pgbackrest("cluster", "stanza", repo1, repo2, root=tmp_path)
        result = (tmp_path / "etc/pgbackrest/pgbackrest.conf").read_text()
        expected = normalize_multi_line_str("""
            [global]
            archive-async=y
            archive-check=y
            process-max=1
            log-level-console=info
            start-fast=y

            repo1-path = path1
            repo1-repo-type = posix

            repo2-path = path2
            repo2-repo-type = posix

            [global:archive-push]
            compress-level=3

            [stanza]
            pg1-path=/var/lib/postgresql/17/cluster
        """)
        assert result == expected


class TestSetUpPostgresqlConf:
    def test_main(self, *, tmp_path: Path) -> None:
        _set_up_postgresql_conf("name", root=tmp_path)
        assert (tmp_path / "etc/postgresql/17/name/conf.d/custom.conf").is_file()

from __future__ import annotations

from pathlib import Path

from pydantic import SecretStr
from utilities.core import normalize_multi_line_str

from postgres import CipherType, RepoType
from postgres.commands import RepoSpec
from postgres.commands._set_up import (
    _set_up_pg_hba,
    _set_up_pgbackrest,
    _set_up_postgresql_conf,
)


class TestRepoSpec:
    def test_main(self) -> None:
        text = RepoSpec(Path("path")).text
        expected = normalize_multi_line_str("""
            repo1-path = /path
            repo1-repo-type = posix
        """)
        assert text == expected

    def test_n(self) -> None:
        text = RepoSpec(Path("path"), n=2).text
        expected = normalize_multi_line_str("""
            repo2-path = /path
            repo2-repo-type = posix
        """)
        assert text == expected

    def test_cipher_pass(self) -> None:
        text = RepoSpec(Path("path"), cipher_pass=SecretStr("secret")).text
        expected = normalize_multi_line_str("""
            repo1-path = /path
            repo1-cipher-pass = secret
            repo1-repo-type = posix
        """)
        assert text == expected

    def test_cipher_type(self) -> None:
        text = RepoSpec(Path("path"), cipher_type=CipherType.aes_256_cbc).text
        expected = normalize_multi_line_str("""
            repo1-path = /path
            repo1-cipher-type = aes-256-cbc
            repo1-repo-type = posix
        """)
        assert text == expected

    def test_repo_type(self) -> None:
        text = RepoSpec(Path("path"), repo_type=RepoType.s3).text
        expected = normalize_multi_line_str("""
            repo1-path = /path
            repo1-repo-type = s3
        """)
        assert text == expected

    def test_retention_diff(self) -> None:
        text = RepoSpec(Path("path"), retention_diff=1).text
        expected = normalize_multi_line_str("""
            repo1-path = /path
            repo1-repo-type = posix
            repo1-retention-diff = 1
        """)
        assert text == expected

    def test_retention_full(self) -> None:
        text = RepoSpec(Path("path"), retention_full=1).text
        expected = normalize_multi_line_str("""
            repo1-path = /path
            repo1-repo-type = posix
            repo1-retention-full = 1
        """)
        assert text == expected

    def test_s3_bucket(self) -> None:
        text = RepoSpec(Path("path"), s3_bucket="bucket").text
        expected = normalize_multi_line_str("""
            repo1-path = /path
            repo1-repo-type = posix
            repo1-s3-bucket = bucket
        """)
        assert text == expected

    def test_s3_endpoint(self) -> None:
        text = RepoSpec(Path("path"), s3_endpoint="endpoint").text
        expected = normalize_multi_line_str("""
            repo1-path = /path
            repo1-repo-type = posix
            repo1-s3-endpoint = endpoint
        """)
        assert text == expected

    def test_s3_key(self) -> None:
        text = RepoSpec(Path("path"), s3_key=SecretStr("key")).text
        expected = normalize_multi_line_str("""
            repo1-path = /path
            repo1-repo-type = posix
            repo1-s3-key = key
        """)
        assert text == expected

    def test_s3_key_secret(self) -> None:
        text = RepoSpec(Path("path"), s3_key_secret=SecretStr("key-secret")).text
        expected = normalize_multi_line_str("""
            repo1-path = /path
            repo1-repo-type = posix
            repo1-s3-key-secret = key-secret
        """)
        assert text == expected

    def test_s3_region(self) -> None:
        text = RepoSpec(Path("path"), s3_region="region").text
        expected = normalize_multi_line_str("""
            repo1-path = /path
            repo1-repo-type = posix
            repo1-s3-region = region
        """)
        assert text == expected


class TestSetUpPGHBA:
    def test_main(self, *, tmp_path: Path) -> None:
        _set_up_pg_hba("name", root=tmp_path)
        assert (tmp_path / "etc/postgresql/17/name/pg_hba.conf").is_file()
        assert (tmp_path / "etc/postgresql/17/name/pg_hba.conf.d/custom.conf").is_file()


class TestSetUpPGBackrest:
    def test_single(self, *, tmp_path: Path) -> None:
        repo = RepoSpec(Path("path"))
        _set_up_pgbackrest("cluster", "stanza", repo, root=tmp_path, process_max=1)
        result = (tmp_path / "etc/pgbackrest/pgbackrest.conf").read_text()
        expected = normalize_multi_line_str("""
            [global]
            archive-async=y
            archive-check=y
            process-max=1
            log-level-console=info
            start-fast=y

            repo1-path = /path
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
        _set_up_pgbackrest(
            "cluster", "stanza", repo1, repo2, root=tmp_path, process_max=1
        )
        result = (tmp_path / "etc/pgbackrest/pgbackrest.conf").read_text()
        expected = normalize_multi_line_str("""
            [global]
            archive-async=y
            archive-check=y
            process-max=1
            log-level-console=info
            start-fast=y

            repo1-path = /path1
            repo1-repo-type = posix

            repo2-path = /path2
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

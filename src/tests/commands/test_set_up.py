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


class TestSetUpPGBackrest:
    def test_main(self, *, tmp_path: Path) -> None:
        repo = RepoSpec(Path("path"))
        _set_up_pgbackrest("name", repo, root=tmp_path)
        result = (tmp_path / "etc/pgbackrest/pgbackrest.conf").read_text()
        expected = normalize_multi_line_str("""
            asdfasdf
        """)
        assert result == expected


class TestSetUpPostgresqlConf:
    def test_main(self, *, tmp_path: Path) -> None:
        _set_up_postgresql_conf("name", root=tmp_path)

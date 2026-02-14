from __future__ import annotations

from typing import TYPE_CHECKING

from postgres.commands._set_up import (
    _set_up_pg_hba,
    _set_up_pgbackrest,
    _set_up_postgresql_conf,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestSetUpPGHBA:
    def test_main(self, *, tmp_path: Path) -> None:
        _set_up_pg_hba("name", root=tmp_path)


class TestSetUpPGBackrest:
    def test_main(self, *, tmp_path: Path) -> None:
        _set_up_pgbackrest("name", root=tmp_path)


class TestSetUpPostgresqlConf:
    def test_main(self, *, tmp_path: Path) -> None:
        _set_up_postgresql_conf("name", root=tmp_path)

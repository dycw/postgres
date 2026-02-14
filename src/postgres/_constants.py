from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.importlib import files

if TYPE_CHECKING:
    from pathlib import Path


PORT: int = 5432
PROCESSES: int = 1
VERSION: int = 17


PATH_CONFIGS: Path = files(anchor="postgres") / "configs"


__all__ = ["PATH_CONFIGS", "PORT", "PROCESSES", "VERSION"]

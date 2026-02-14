from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.constants import CPU_COUNT
from utilities.importlib import files

if TYPE_CHECKING:
    from pathlib import Path


PORT: int = 5432
PROCESS_MAX: int = max(round(CPU_COUNT * 3 / 4), 1)
VERSION: int = 17


PATH_CONFIGS: Path = files(anchor="postgres") / "configs"


__all__ = ["PATH_CONFIGS", "PORT", "PROCESS_MAX", "VERSION"]

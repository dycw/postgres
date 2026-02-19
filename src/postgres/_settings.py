from __future__ import annotations

from pydantic_settings import BaseSettings


class RetentionSettings(BaseSettings):
    full: int
    diff: int


__all__ = ["RetentionSettings"]

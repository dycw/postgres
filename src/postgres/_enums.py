from __future__ import annotations

from enum import StrEnum, unique
from typing import assert_never


@unique
class BackupType(StrEnum):
    full = "full"
    diff = "diff"
    incr = "incr"

    @property
    def desc(self) -> str:
        match self:
            case BackupType.full:
                return "full"
            case BackupType.diff:
                return "differential"
            case BackupType.incr:
                return "incremental"
            case never:
                assert_never(never)


DEFAULT_BACKUP_TYPE = BackupType.incr


##


@unique
class CipherType(StrEnum):
    aes_256_cbc = "aes-256-cbc"


DEFAULT_CIPHER_TYPE = CipherType.aes_256_cbc


##


@unique
class RepoType(StrEnum):
    azure = "azure"
    cifs = "cifs"
    gcs = "gcs"
    posix = "posix"
    s3 = "s3"
    sftp = "sftp"


DEFAULT_REPO_TYPE = RepoType.posix


__all__ = [
    "DEFAULT_BACKUP_TYPE",
    "DEFAULT_CIPHER_TYPE",
    "DEFAULT_REPO_TYPE",
    "BackupType",
    "CipherType",
    "RepoType",
]

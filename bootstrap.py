#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
from logging import basicConfig, getLogger
from pathlib import Path
from subprocess import PIPE, check_output
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


basicConfig(
    format="{asctime} | {message}", datefmt="%Y-%m-%d %H:%M:%S", style="{", level="INFO"
)
_LOGGER = getLogger()
_REPO_ROOT = Path(__file__).parent


@dataclass(frozen=True, kw_only=True)
class _Replacement:
    from_: str
    to: str


def main() -> None:
    dashed = "dycw-template"
    underscore = dashed.replace("-", "_")
    name = _get_repo_name()
    replacements = [
        _Replacement(from_=dashed, to=name.replace("_", "-")),
        _Replacement(from_=underscore, to=name.replace("-", "_")),
    ]
    _process_file_contents(_REPO_ROOT, replacements)
    _process_file_names(_REPO_ROOT, replacements)


def _get_repo_name() -> str:
    """Get the repo name."""
    output = check_output(
        ["git", "remote", "get-url", "origin"], stderr=PIPE, cwd=_REPO_ROOT, text=True
    )
    return Path(output.strip("\n")).stem


def _process_file_contents(root: Path, replacements: Iterable[_Replacement], /) -> None:
    replacements = list(replacements)
    _LOGGER.info(
        "Processing file contents: %s (%s)", root, _desc_replacements(replacements)
    )
    for path in _yield_paths(root):
        if path.is_file():
            try:
                with path.open() as fh:
                    old_contents = fh.read()
            except UnicodeDecodeError:
                _LOGGER.exception("Failed to read %s", path)
            else:
                new_contents = _apply_replacements(old_contents, replacements)
                if old_contents != new_contents:
                    _LOGGER.info("Re-writing %s...", path)
                    with path.open(mode="w") as fh:
                        _ = fh.write(new_contents)


def _desc_replacements(replacements: Iterable[_Replacement], /) -> str:
    return ", ".join(f"{r.from_}->{r.to}" for r in replacements)


def _yield_paths(root: Path, /) -> Iterator[Path]:
    skips = {root.joinpath(".git"), root.joinpath(".venv")}
    for path in root.rglob("**/*"):
        if not any(path.is_relative_to(skip) for skip in skips):
            yield path


def _apply_replacements(text: str, replacements: Iterable[_Replacement], /) -> str:
    def inner(text: str, replacement: _Replacement, /) -> str:
        return text.replace(replacement.from_, replacement.to)

    return reduce(inner, replacements, text)


def _process_file_names(root: Path, replacements: Iterable[_Replacement], /) -> None:
    replacements = list(replacements)
    _LOGGER.info(
        "Processing file names: %s (%s)", root, _desc_replacements(replacements)
    )
    for path in list(_yield_paths(root)):
        old_stem = path.stem
        new_stem = _apply_replacements(old_stem, replacements)
        new_path = path.with_stem(new_stem)
        if path != new_path:
            _LOGGER.info("Renaming %s -> %s...", path, new_path)
            _ = path.rename(new_path)


if __name__ == "__main__":
    main()

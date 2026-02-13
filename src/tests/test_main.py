from __future__ import annotations

from postgres import __version__


class TestMain:
    def test_main(self) -> None:
        assert isinstance(__version__, str)

"""Pure-logic tests for the Direct Line client (no network)."""
from __future__ import annotations

from app.cs_directline import _DL_BASE_DEFAULT, _dl_base_from_stream_url


def test_dl_base_us_region():
    assert _dl_base_from_stream_url(
        "https://unitedstates.directline.botframework.com/v3/directline/conversations/abc/stream?t=foo"
    ) == "https://unitedstates.directline.botframework.com/v3/directline"


def test_dl_base_eu_region():
    assert _dl_base_from_stream_url(
        "wss://europe.directline.botframework.com/v3/directline/conversations/abc/stream?t=foo"
    ) == "https://europe.directline.botframework.com/v3/directline"


def test_dl_base_empty_falls_back():
    assert _dl_base_from_stream_url("") == _DL_BASE_DEFAULT


def test_dl_base_garbage_falls_back():
    assert _dl_base_from_stream_url("not-a-url") == _DL_BASE_DEFAULT

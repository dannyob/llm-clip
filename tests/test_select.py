import pytest

from llm_clip.errors import NoUsableContent, ForcedTypeAbsent
from llm_clip.select import choose


def test_picks_highest_priority_present():
    assert choose(["text/plain", "text/html", "image/png"]) == "image/png"


def test_html_over_plain():
    assert choose(["text/plain", "text/html"]) == "text/html"


def test_png_over_tiff():
    assert choose(["image/tiff", "image/png"]) == "image/png"


def test_ignores_unknown_types():
    assert choose(["image/gif", "text/plain"]) == "text/plain"


def test_empty_raises():
    with pytest.raises(NoUsableContent):
        choose([])


def test_forced_explicit_mimetype_present():
    assert choose(["image/png", "text/plain"], forced="text/plain") == "text/plain"


def test_forced_explicit_mimetype_absent():
    with pytest.raises(ForcedTypeAbsent):
        choose(["text/plain"], forced="image/png")


def test_forced_alias_resolves_to_present_member():
    assert choose(["image/tiff", "text/plain"], forced="image") == "image/tiff"


def test_forced_alias_absent():
    with pytest.raises(ForcedTypeAbsent):
        choose(["text/plain"], forced="image")

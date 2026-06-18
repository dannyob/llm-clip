import pytest

from llm_clip.errors import ClipError
from llm_clip.cli import Options, split_args


def test_passthrough_preserved_in_order():
    opts, rest = split_args(["-m", "gpt-4o", "describe this"])
    assert opts == Options()
    assert rest == ["-m", "gpt-4o", "describe this"]


def test_extracts_force_type_space_form():
    opts, rest = split_args(["--force-type", "text/html", "-m", "x", "go"])
    assert opts.force_type == "text/html"
    assert rest == ["-m", "x", "go"]


def test_extracts_force_type_equals_form():
    opts, rest = split_args(["--force-type=image", "go"])
    assert opts.force_type == "image"
    assert rest == ["go"]


def test_extracts_flags_interleaved_with_llm_flags():
    opts, rest = split_args(["-m", "x", "--keep", "go", "--dry-run"])
    assert opts.keep is True
    assert opts.dry_run is True
    assert rest == ["-m", "x", "go"]


def test_help_flag():
    opts, rest = split_args(["-h"])
    assert opts.help is True


def test_force_type_missing_value_raises():
    with pytest.raises(ClipError):
        split_args(["--force-type"])


def test_force_type_equals_empty_raises():
    with pytest.raises(ClipError):
        split_args(["--force-type="])

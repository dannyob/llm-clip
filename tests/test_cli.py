import os

import pytest

from llm_clip.errors import ClipError
from llm_clip.cli import Options, split_args, build_command, main


class FakeBackend:
    def __init__(self, types, data):
        self._types = types
        self._data = data
        self.read_mimetype = None

    def available_types(self):
        return self._types

    def read(self, mimetype):
        self.read_mimetype = mimetype
        return self._data


class FakeRunner:
    def __init__(self, returncode=0):
        self.returncode = returncode
        self.cmd = None

    def __call__(self, cmd):
        self.cmd = cmd

        class _R:
            pass

        r = _R()
        r.returncode = self.returncode
        return r


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


def test_build_command_uses_at_form():
    assert build_command("/tmp/x.png", "image/png", ["-m", "m", "go"]) == [
        "llm", "--at", "/tmp/x.png", "image/png", "-m", "m", "go",
    ]


def test_main_runs_llm_with_clipboard_text(tmp_path):
    backend = FakeBackend(["text/plain"], b"hello world")
    runner = FakeRunner(returncode=0)
    rc = main(["-m", "gpt-4o", "go"], backend=backend, runner=runner)
    assert rc == 0
    assert runner.cmd[:2] == ["llm", "--at"]
    written_path = runner.cmd[2]
    assert runner.cmd[3] == "text/plain"
    assert runner.cmd[4:] == ["-m", "gpt-4o", "go"]
    # temp file cleaned up after llm exits
    assert not os.path.exists(written_path)


def test_main_propagates_returncode(tmp_path):
    backend = FakeBackend(["text/plain"], b"x")
    runner = FakeRunner(returncode=3)
    assert main(["go"], backend=backend, runner=runner) == 3


def test_main_keep_leaves_file(tmp_path):
    backend = FakeBackend(["text/plain"], b"x")
    runner = FakeRunner()
    rc = main(["--keep", "go"], backend=backend, runner=runner)
    assert rc == 0
    assert os.path.exists(runner.cmd[2])
    os.unlink(runner.cmd[2])


def test_main_dry_run_does_not_call_runner(capsys, tmp_path):
    backend = FakeBackend(["text/plain"], b"x")
    runner = FakeRunner()
    rc = main(["--dry-run", "go"], backend=backend, runner=runner)
    assert rc == 0
    assert runner.cmd is None  # llm never invoked
    out = capsys.readouterr().out
    assert out.startswith("llm --at ")
    # dry-run keeps the file; clean it up using the path printed
    path = out.split()[2]
    assert os.path.exists(path)
    os.unlink(path)


def test_main_transcodes_tiff(tmp_path):
    import io
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (4, 4), (1, 2, 3)).save(buf, format="TIFF")
    backend = FakeBackend(["image/tiff"], buf.getvalue())
    runner = FakeRunner()
    main(["go"], backend=backend, runner=runner)
    assert runner.cmd[3] == "image/png"
    assert runner.cmd[2].endswith(".png")


def test_main_no_usable_content_errors(capsys):
    backend = FakeBackend([], b"")
    rc = main(["go"], backend=backend, runner=FakeRunner())
    assert rc == 1
    assert "llm-clip:" in capsys.readouterr().err


def test_main_llm_not_found(capsys, tmp_path):
    backend = FakeBackend(["text/plain"], b"x")
    recorded = {}

    def boom(cmd):
        recorded["cmd"] = cmd
        raise FileNotFoundError("llm")

    rc = main(["go"], backend=backend, runner=boom)
    assert rc == 127
    assert "llm" in capsys.readouterr().err
    # temp file must be cleaned up even when llm is missing
    assert not os.path.exists(recorded["cmd"][2])

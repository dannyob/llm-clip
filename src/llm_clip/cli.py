"""Command-line entry point for llm-clip."""

import mimetypes
import os
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass

from .errors import ClipError
from .images import normalise_image
from .select import choose


@dataclass
class Options:
    force_type: str | None = None
    keep: bool = False
    dry_run: bool = False
    help: bool = False


def split_args(argv: list[str]) -> tuple[Options, list[str]]:
    """Split argv into llm-clip's own options and the llm passthrough.

    A manual scan rather than an option parser, so llm's own flags
    (e.g. -m, abbreviations) are forwarded untouched.
    """
    opts = Options()
    passthrough: list[str] = []
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--force-type":
            if i + 1 >= len(argv):
                raise ClipError("--force-type requires a value")
            opts.force_type = argv[i + 1]
            i += 2
            continue
        if tok.startswith("--force-type="):
            value = tok.split("=", 1)[1]
            if not value:
                raise ClipError("--force-type requires a value")
            opts.force_type = value
        elif tok == "--keep":
            opts.keep = True
        elif tok == "--dry-run":
            opts.dry_run = True
        elif tok in ("-h", "--help"):
            opts.help = True
        else:
            passthrough.append(tok)
        i += 1
    return opts, passthrough


USAGE = """\
Usage: llm-clip [--force-type TYPE] [--keep] [--dry-run] [llm args...]

Reads the clipboard, writes it to a temp file, and runs:
    llm --at <tempfile> <mimetype> [llm args...]

Options:
  --force-type TYPE  Force a clipboard type: a mimetype (image/png,
                     text/html, text/plain) or an alias (image, html, text).
  --keep             Do not delete the temp file; print its path to stderr.
  --dry-run          Print the llm command and keep the temp file; do not run.
  -h, --help         Show this help.

All other arguments are forwarded to llm unchanged.
"""


def build_command(path: str, mimetype: str, passthrough: list[str]) -> list[str]:
    return ["llm", "--at", path, mimetype, *passthrough]


def main(argv: list[str] | None = None, *, backend=None, runner=subprocess.run) -> int:
    if argv is None:
        argv = sys.argv[1:]

    try:
        opts, passthrough = split_args(argv)
    except ClipError as exc:
        print(f"llm-clip: {exc}", file=sys.stderr)
        return 2

    if opts.help:
        print(USAGE)
        return 0

    if backend is None:
        from .clipboard import get_backend

        backend = get_backend()

    try:
        mimetype = choose(backend.available_types(), opts.force_type)
    except ClipError as exc:
        print(f"llm-clip: {exc}", file=sys.stderr)
        return 1

    data = backend.read(mimetype)
    if mimetype == "image/tiff":
        data, mimetype = normalise_image(data, mimetype)

    suffix = mimetypes.guess_extension(mimetype) or ""
    fd, path = tempfile.mkstemp(prefix="llm-clip-", suffix=suffix)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)

    cmd = build_command(path, mimetype, passthrough)

    if opts.dry_run:
        print(shlex.join(cmd))
        print(f"llm-clip: kept {path}", file=sys.stderr)
        return 0

    try:
        result = runner(cmd)
        return result.returncode
    except FileNotFoundError:
        print("llm-clip: could not run 'llm' — is it installed and on PATH?",
              file=sys.stderr)
        return 127
    finally:
        if opts.keep:
            print(f"llm-clip: kept {path}", file=sys.stderr)
        elif os.path.exists(path):
            os.unlink(path)

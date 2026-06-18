"""Command-line entry point for llm-clip."""

from dataclasses import dataclass

from .errors import ClipError


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
            opts.force_type = tok.split("=", 1)[1]
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

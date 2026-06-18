"""Choose which clipboard mimetype to attach."""

from .errors import NoUsableContent, ForcedTypeAbsent

PRIORITY = ["image/png", "image/tiff", "image/jpeg", "text/html", "text/plain"]

ALIASES = {
    "image": ["image/png", "image/tiff", "image/jpeg"],
    "html": ["text/html"],
    "text": ["text/plain"],
}


def choose(available: list[str], forced: str | None = None) -> str:
    """Return the mimetype to attach, or raise a ClipError subclass."""
    present = set(available)

    if forced is not None:
        candidates = ALIASES.get(forced, [forced])
        for mime in candidates:
            if mime in present:
                return mime
        raise ForcedTypeAbsent(
            f"requested type {forced!r} is not on the clipboard"
        )

    for mime in PRIORITY:
        if mime in present:
            return mime
    raise NoUsableContent("clipboard holds nothing in a supported format")

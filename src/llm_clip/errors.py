"""User-facing error types for llm-clip."""


class ClipError(Exception):
    """Base class for expected, user-facing llm-clip failures."""


class NoUsableContent(ClipError):
    """The clipboard holds nothing in a supported format."""


class ForcedTypeAbsent(ClipError):
    """A --force-type was requested but is not on the clipboard."""

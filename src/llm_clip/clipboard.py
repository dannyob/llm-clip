"""Platform clipboard backends speaking mimetypes."""

import shutil
import subprocess
import sys

from .errors import NoUsableContent

UTI_TO_MIME = {
    "public.png": "image/png",
    "public.tiff": "image/tiff",
    "public.jpeg": "image/jpeg",
    "public.html": "text/html",
    "public.utf8-plain-text": "text/plain",
    "public.plain-text": "text/plain",
}

_LINUX_TEXT_ATOMS = {"UTF8_STRING", "STRING", "TEXT"}
_SUPPORTED_MIMES = {"image/png", "image/tiff", "image/jpeg", "text/html", "text/plain"}


def normalise_linux_type(raw: str) -> str | None:
    """Map a wl-paste/xclip target to a supported mimetype, or None."""
    raw = raw.strip()
    if raw in _LINUX_TEXT_ATOMS:
        return "text/plain"
    base = raw.split(";", 1)[0]  # drop ;charset=utf-8
    if base in _SUPPORTED_MIMES:
        return base
    return None


def parse_linux_types(lines: list[str]) -> dict[str, str]:
    """Return {mimetype: raw_target}; first raw target wins on collision."""
    mapping: dict[str, str] = {}
    for raw in lines:
        mime = normalise_linux_type(raw)
        if mime is not None and mime not in mapping:
            mapping[mime] = raw.strip()
    return mapping


class MacBackend:
    """Read the macOS pasteboard via PyObjC NSPasteboard."""

    def _pasteboard(self):
        from AppKit import NSPasteboard

        return NSPasteboard.generalPasteboard()

    def available_types(self) -> list[str]:
        pb = self._pasteboard()
        seen: list[str] = []
        for uti in pb.types():
            mime = UTI_TO_MIME.get(str(uti))
            if mime and mime not in seen:
                seen.append(mime)
        return seen

    def read(self, mimetype: str) -> bytes:
        pb = self._pasteboard()
        for uti in pb.types():
            if UTI_TO_MIME.get(str(uti)) == mimetype:
                data = pb.dataForType_(uti)
                if data is not None:
                    return bytes(data)
        raise NoUsableContent(f"no clipboard data for {mimetype}")


class LinuxBackend:
    """Read the Linux clipboard via wl-paste, xclip, or xsel."""

    def __init__(self, tool: str | None = None, run=None):
        self.tool = tool or self._detect_tool()
        self._run = run or self._default_run
        self._map: dict[str, str] = {}

    @staticmethod
    def _detect_tool() -> str:
        for tool in ("wl-paste", "xclip", "xsel"):
            if shutil.which(tool):
                return tool
        raise NoUsableContent(
            "no clipboard tool found; install wl-clipboard, xclip, or xsel"
        )

    @staticmethod
    def _default_run(args: list[str]) -> bytes:
        return subprocess.run(args, check=True, capture_output=True).stdout

    def _list_args(self) -> list[str]:
        if self.tool == "wl-paste":
            return ["wl-paste", "--list-types"]
        if self.tool == "xclip":
            return ["xclip", "-selection", "clipboard", "-t", "TARGETS", "-o"]
        return ["xsel", "--clipboard"]  # xsel: text only

    def _read_args(self, raw_target: str) -> list[str]:
        if self.tool == "wl-paste":
            return ["wl-paste", "--type", raw_target]
        if self.tool == "xclip":
            return ["xclip", "-selection", "clipboard", "-t", raw_target, "-o"]
        return ["xsel", "--clipboard"]

    def available_types(self) -> list[str]:
        if self.tool == "xsel":
            self._map = {"text/plain": "text/plain"}
            return ["text/plain"]
        output = self._run(self._list_args()).decode("utf-8", "replace")
        self._map = parse_linux_types(output.splitlines())
        return list(self._map)

    def read(self, mimetype: str) -> bytes:
        if not self._map:
            self.available_types()
        if mimetype not in self._map:
            raise NoUsableContent(f"no clipboard data for {mimetype}")
        raw_target = self._map[mimetype]
        return self._run(self._read_args(raw_target))


def get_backend():
    if sys.platform == "darwin":
        return MacBackend()
    return LinuxBackend()

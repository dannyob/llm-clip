from llm_clip.clipboard import (
    UTI_TO_MIME,
    normalise_linux_type,
    parse_linux_types,
    LinuxBackend,
    get_backend,
)


def test_uti_mapping_has_core_types():
    assert UTI_TO_MIME["public.png"] == "image/png"
    assert UTI_TO_MIME["public.tiff"] == "image/tiff"
    assert UTI_TO_MIME["public.html"] == "text/html"
    assert UTI_TO_MIME["public.utf8-plain-text"] == "text/plain"


def test_normalise_linux_text_atoms():
    assert normalise_linux_type("UTF8_STRING") == "text/plain"
    assert normalise_linux_type("STRING") == "text/plain"
    assert normalise_linux_type("text/plain;charset=utf-8") == "text/plain"
    assert normalise_linux_type("image/png") == "image/png"
    assert normalise_linux_type("text/html") == "text/html"


def test_normalise_linux_unsupported_returns_none():
    assert normalise_linux_type("TIMESTAMP") is None
    assert normalise_linux_type("text/uri-list") is None


def test_parse_linux_types_maps_mime_to_raw():
    mapping = parse_linux_types(["image/png", "UTF8_STRING", "TIMESTAMP"])
    assert mapping["image/png"] == "image/png"
    assert mapping["text/plain"] == "UTF8_STRING"
    assert "TIMESTAMP" not in mapping.values()


def test_linux_backend_available_and_read_use_runner():
    calls = []

    def fake_run(args):
        calls.append(args)
        if "--list-types" in args or "TARGETS" in args:
            return b"image/png\nUTF8_STRING\n"
        return b"PNGDATA"

    backend = LinuxBackend(tool="wl-paste", run=fake_run)
    assert set(backend.available_types()) == {"image/png", "text/plain"}
    assert backend.read("image/png") == b"PNGDATA"


def test_get_backend_returns_something():
    assert get_backend() is not None

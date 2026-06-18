import io

from PIL import Image

from llm_clip.images import normalise_image


def _make(fmt: str) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), (10, 20, 30)).save(buf, format=fmt)
    return buf.getvalue()


def test_tiff_becomes_png():
    data, mime = normalise_image(_make("TIFF"), "image/tiff")
    assert mime == "image/png"
    assert Image.open(io.BytesIO(data)).format == "PNG"


def test_png_passes_through_unchanged():
    original = _make("PNG")
    data, mime = normalise_image(original, "image/png")
    assert mime == "image/png"
    assert data == original


def test_jpeg_passes_through_unchanged():
    original = _make("JPEG")
    data, mime = normalise_image(original, "image/jpeg")
    assert mime == "image/jpeg"
    assert data == original


def test_text_passes_through_unchanged():
    data, mime = normalise_image(b"hello", "text/plain")
    assert (data, mime) == (b"hello", "text/plain")

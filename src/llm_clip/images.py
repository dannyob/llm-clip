"""Normalise clipboard image bytes for llm attachment."""

import io

from PIL import Image


def normalise_image(data: bytes, mimetype: str) -> tuple[bytes, str]:
    """Transcode TIFF to PNG; return everything else unchanged.

    TIFF is rarely accepted by multimodal models but is what older macOS
    apps put on the pasteboard. PNG and JPEG are widely accepted, so they
    pass through byte-for-byte.
    """
    if mimetype != "image/tiff":
        return data, mimetype

    img = Image.open(io.BytesIO(data))
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue(), "image/png"

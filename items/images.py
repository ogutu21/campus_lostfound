import os
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

MAX_SIDE = 1600       # longest side in pixels
JPEG_QUALITY = 82


def shrink_image(source):
    """Return a smaller, privacy-friendly JPEG copy of an image file.

    - Applies the phone's rotation, so photos aren't sideways.
    - Scales the picture down so its longest side is at most MAX_SIDE.
    - Saves a fresh JPEG, which drops EXIF data such as GPS location.
    """
    source.seek(0)
    img = Image.open(source)
    img = ImageOps.exif_transpose(img)

    # JPEG has no transparency, so put see-through images on white.
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.getchannel("A"))
        img = background
    else:
        img = img.convert("RGB")

    img.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)

    base = os.path.splitext(os.path.basename(source.name))[0] or "photo"
    return ContentFile(buffer.getvalue(), name=f"{base}.jpg")
from __future__ import annotations

from pathlib import Path

from PIL import Image


def prepare_ebook_cover(source_path: str | Path, output_path: str | Path, size: tuple[int, int] = (1600, 2560)) -> Path:
    """Create a KDP-sized RGB JPEG without stretching the approved artwork."""
    source = Path(source_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image = image.convert("RGB")
        target_width, target_height = size
        scale = target_width / image.width
        resized_height = round(image.height * scale)
        resized = image.resize((target_width, resized_height), Image.Resampling.LANCZOS)
        if resized_height > target_height:
            top = (resized_height - target_height) // 2
            canvas = resized.crop((0, top, target_width, top + target_height))
        else:
            background = image.getpixel((8, 8))
            canvas = Image.new("RGB", size, background)
            top = (target_height - resized_height) // 2
            canvas.paste(resized, (0, top))
        canvas.save(output, "JPEG", quality=95, optimize=True, progressive=True, dpi=(300, 300))
    return output

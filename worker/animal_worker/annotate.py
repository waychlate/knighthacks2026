"""Draw the detection box on the full frame and upload clean + annotated copies for Dev mode."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from .annotate_sightings import COLORS, DEFAULT_COLOR


def annotate_frame(frame_bgr, box, label: str, text: str, color: str | None = None) -> Image.Image:
    """Return a PIL copy of the BGR frame with `box` drawn and `text` in a black tag above it."""
    image = Image.fromarray(frame_bgr[:, :, ::-1].copy())
    draw = ImageDraw.Draw(image)
    color = color or COLORS.get(label, DEFAULT_COLOR)
    box = tuple(int(v) for v in box)
    draw.rectangle(box, outline=color, width=max(3, round(min(image.size) / 240)))
    font = ImageFont.load_default(size=max(14, round(min(image.size) / 45)))
    tag = draw.textbbox((box[0], box[1]), text, font=font)
    h, w = tag[3] - tag[1] + 8, tag[2] - tag[0] + 10
    y = max(0, box[1] - h)
    draw.rectangle((box[0], y, box[0] + w, y + h), fill="black")
    draw.text((box[0] + 5, y + 3), text, fill=color, font=font)
    return image


def frame_extras(store, species, confidence: float, detection) -> dict:
    """Upload the clean and annotated full frame; return the extra `sightings` columns."""
    frame = getattr(detection, "frame", None)
    if frame is None:
        return {}
    clean = Image.fromarray(frame[:, :, ::-1].copy())
    text = f"{species.common_name} {confidence:.0%} | YOLO {detection.score:.2f}"
    return {
        "frame_url": store.upload_snapshot(clean),
        "annotated_url": store.upload_snapshot(annotate_frame(frame, detection.box, detection.label, text)),
        "bbox": list(detection.box),
        "yolo_score": round(float(detection.score), 3),
    }

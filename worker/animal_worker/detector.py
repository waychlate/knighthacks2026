"""Stage 1: find animals in a frame with YOLO and return cropped images."""

from __future__ import annotations

from dataclasses import dataclass

# COCO classes that are animals: bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe
ANIMAL_CLASS_IDS = [14, 15, 16, 17, 18, 19, 20, 21, 22, 23]


def _animal_class_ids(names) -> list[int]:
    """Use two-class IDs for our custom model and COCO animal IDs otherwise."""
    items = names.items() if hasattr(names, "items") else enumerate(names)
    mapping = dict(items)
    if len(mapping) <= 2 and set(mapping.values()).issubset({"bear", "bird"}):
        return sorted(mapping)
    return ANIMAL_CLASS_IDS


@dataclass
class Detection:
    crop: "PIL.Image.Image"
    box: tuple[int, int, int, int]
    score: float
    class_id: int
    label: str


class AnimalDetector:
    def __init__(self, weights: str = "yolov8n.pt", min_score: float = 0.4,
                 tile_size: int | None = None, overlap: float = 0.2,
                 class_min_scores: dict[str, float] | None = None):
        from ultralytics import YOLO

        self.model = YOLO(weights)  # downloads weights on first run
        self.class_ids = _animal_class_ids(self.model.names)
        self.min_score = min_score
        self.tile_size = tile_size
        self.overlap = overlap
        self.class_min_scores = class_min_scores or {}

    def detect(self, frame) -> list[Detection]:
        """Detect animals, optionally adding overlapping tiles for small subjects."""
        height, width = frame.shape[:2]
        regions = [(0, 0, width, height)]
        if self.tile_size and (width > self.tile_size or height > self.tile_size):
            regions.extend(self._tile_regions(width, height))

        detections = []
        for x1, y1, x2, y2 in regions:
            detections.extend(self._detect_region(frame, x1, y1, x2, y2))
        return self._nms(detections)

    def _detect_region(self, frame, left, top, right, bottom) -> list[Detection]:
        from PIL import Image

        region = frame[top:bottom, left:right]
        inference_score = min([self.min_score, *self.class_min_scores.values()])
        result = self.model.predict(region, classes=self.class_ids, conf=inference_score, verbose=False)[0]
        rgb = frame[:, :, ::-1]
        out = []
        for box in result.boxes:
            class_id = int(box.cls[0])
            label = str(self.model.names[class_id])
            score = float(box.conf[0])
            if score < self.class_min_scores.get(label, self.min_score):
                continue
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            x1, x2 = x1 + left, x2 + left
            y1, y2 = y1 + top, y2 + top
            if x2 <= x1 or y2 <= y1:
                continue
            crop = Image.fromarray(rgb[y1:y2, x1:x2].copy())
            out.append(Detection(
                crop=crop,
                box=(x1, y1, x2, y2),
                score=score,
                class_id=class_id,
                label=label,
            ))
        return out

    def _tile_regions(self, width: int, height: int):
        size = self.tile_size
        step = max(1, round(size * (1 - self.overlap)))

        def starts(length):
            values = list(range(0, max(1, length - size + 1), step))
            last = max(0, length - size)
            if not values or values[-1] != last:
                values.append(last)
            return values

        return [
            (x, y, min(x + size, width), min(y + size, height))
            for y in starts(height)
            for x in starts(width)
        ]

    @staticmethod
    def _nms(detections: list[Detection], iou_threshold: float = 0.5) -> list[Detection]:
        """Remove duplicate same-class boxes created by overlapping tiles."""
        kept = []
        for det in sorted(detections, key=lambda item: item.score, reverse=True):
            if any(det.class_id == other.class_id and _iou(det.box, other.box) >= iou_threshold
                   for other in kept):
                continue
            kept.append(det)
        return kept


def _iou(a, b) -> float:
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    if not intersection:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return intersection / (area_a + area_b - intersection)

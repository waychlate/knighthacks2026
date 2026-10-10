"""Stage 1: find animals in a frame with YOLO and return cropped images."""

from __future__ import annotations

from dataclasses import dataclass

# COCO classes that are animals: bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe
ANIMAL_CLASS_IDS = [14, 15, 16, 17, 18, 19, 20, 21, 22, 23]


@dataclass
class Detection:
    crop: "PIL.Image.Image"
    box: tuple[int, int, int, int]
    score: float


class AnimalDetector:
    def __init__(self, weights: str = "yolov8n.pt", min_score: float = 0.4):
        from ultralytics import YOLO

        self.model = YOLO(weights)  # downloads weights on first run
        self.min_score = min_score

    def detect(self, frame) -> list[Detection]:
        from PIL import Image

        result = self.model.predict(frame, classes=ANIMAL_CLASS_IDS, conf=self.min_score, verbose=False)[0]
        rgb = frame[:, :, ::-1]
        out = []
        for box in result.boxes:
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            if x2 <= x1 or y2 <= y1:
                continue
            crop = Image.fromarray(rgb[y1:y2, x1:x2].copy())
            out.append(Detection(crop=crop, box=(x1, y1, x2, y2), score=float(box.conf[0])))
        return out

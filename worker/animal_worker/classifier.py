"""Stage 2: name the species in a crop with BioCLIP (Hugging Face), zero-shot."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

HF_MODEL = "hf-hub:imageomics/bioclip"


@dataclass
class Species:
    common_name: str
    scientific_name: str
    group: str | None = None


def load_species(path: str | Path) -> list[Species]:
    data = json.loads(Path(path).read_text())
    return [Species(s["common_name"], s["scientific_name"], s.get("group")) for s in data["species"]]


class SpeciesClassifier:
    def __init__(self, species: list[Species], min_confidence: float = 0.5):
        import open_clip
        import torch

        self.torch = torch
        self.species = species
        self.min_confidence = min_confidence
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(HF_MODEL)
        self.model.eval()
        tokenizer = open_clip.get_tokenizer(HF_MODEL)
        # "scientific (common)" beat scientific-only, common-only, ensemble and taxonomy-prefix prompts on bison clips
        prompts = [f"a photo of {s.scientific_name} ({s.common_name})." for s in species]
        with torch.no_grad():
            text = self.model.encode_text(tokenizer(prompts))
            self.text_features = text / text.norm(dim=-1, keepdim=True)

    def classify(self, crop) -> tuple[Species, float] | None:
        """Return (species, confidence) or None if below the confidence threshold."""
        return self._classify_indices(crop, list(range(len(self.species))))

    def classify_for_label(self, crop, broad_label: str, detector_score: float):
        """Classify only among species compatible with YOLO's broad label.

        If a configured group has one possible species (Katmai bear), preserve
        the detector confidence rather than manufacturing a 100% softmax score.
        """
        group = {
            "bear": "bear",
            "bird": "bird",
            "dog": "canid",
            "horse": "ungulate",
            "cow": "ungulate",
            "sheep": "ungulate",
            "cat": "felid",
        }.get(broad_label)
        indices = [i for i, species in enumerate(self.species) if species.group == group]
        if not indices:
            return self.classify(crop)
        if len(indices) == 1:
            return self.species[indices[0]], detector_score
        result = self._classify_indices(crop, indices)
        if result is not None:
            return result
        return Species(f"{broad_label.title()} (unidentified)", "", group), detector_score

    def _classify_indices(self, crop, indices: list[int]) -> tuple[Species, float] | None:
        torch = self.torch
        with torch.no_grad():
            image = self.preprocess(crop).unsqueeze(0)
            feats = self.model.encode_image(image)
            feats = feats / feats.norm(dim=-1, keepdim=True)
            candidates = self.text_features[indices]
            probs = (100.0 * feats @ candidates.T).softmax(dim=-1)[0]
        conf, idx = probs.max(dim=0)
        if conf.item() < self.min_confidence:
            return None
        return self.species[indices[idx.item()]], conf.item()

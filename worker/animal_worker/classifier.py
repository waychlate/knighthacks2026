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


def load_species(path: str | Path) -> list[Species]:
    data = json.loads(Path(path).read_text())
    return [Species(s["common_name"], s["scientific_name"]) for s in data["species"]]


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
        prompts = [f"a photo of {s.scientific_name}." for s in species]
        with torch.no_grad():
            text = self.model.encode_text(tokenizer(prompts))
            self.text_features = text / text.norm(dim=-1, keepdim=True)

    def classify(self, crop) -> tuple[Species, float] | None:
        """Return (species, confidence) or None if below the confidence threshold."""
        torch = self.torch
        with torch.no_grad():
            image = self.preprocess(crop).unsqueeze(0)
            feats = self.model.encode_image(image)
            feats = feats / feats.norm(dim=-1, keepdim=True)
            probs = (100.0 * feats @ self.text_features.T).softmax(dim=-1)[0]
        conf, idx = probs.max(dim=0)
        if conf.item() < self.min_confidence:
            return None
        return self.species[idx.item()], conf.item()

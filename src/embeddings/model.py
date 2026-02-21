from sentence_transformers import SentenceTransformer
import os

ALLOWED_MODELS = {
    "all-MiniLM-L6-v2",
    "all-mpnet-base-v2",
}

# load model version from env
MODEL: str = os.getenv("MODEL", "all-MiniLM-L6-v2")
if MODEL not in ALLOWED_MODELS:
    raise ValueError(f"Model {MODEL} is not in the allowlist")

device = os.getenv("DEVICE", "cpu")

# Load model at module import time
_model: SentenceTransformer = SentenceTransformer(MODEL, device=device)


def get_model() -> SentenceTransformer:
    return _model

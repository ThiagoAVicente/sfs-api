from functools import lru_cache
from sentence_transformers import SentenceTransformer
import os

ALLOWED_MODELS = {
    "all-MiniLM-L6-v2",
    "all-mpnet-base-v2",
}

# load model from env
MODEL: str = os.getenv("MODEL", "all-MiniLM-L6-v2")
if MODEL not in ALLOWED_MODELS:
    raise ValueError(f"Model {MODEL} is not in the allowlist")

device = os.getenv("DEVICE", "cpu")

model: SentenceTransformer | None = None

@lru_cache
def get_model() -> SentenceTransformer:
    global model
    if model is None:
        model = SentenceTransformer(MODEL, device=device)
    return model

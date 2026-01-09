from sentence_transformers import SentenceTransformer
import os

# load model from env
MODEL: str = os.getenv("MODEL", "all-MiniLM-L6-v2")

model: SentenceTransformer | None = None

def get_model() -> SentenceTransformer:
    global model
    if model is None:
        model = SentenceTransformer(MODEL)
    return model

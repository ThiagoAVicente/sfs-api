from sentence_transformers import SentenceTransformer
import os

ALLOWED_MODELS = {
    "all-MiniLM-L6-v2",
    "all-mpnet-base-v2",
    "jinaai/jina-embeddings-v2-base-code",
    "microsoft/codebert-base",
    "flax-sentence-embeddings/st-codesearch-distilroberta-base",
    "Salesforce/codet5p-110m-embedding",
}

# models that require non-standard loader kwargs
_MODEL_KWARGS: dict[str, dict] = {
    "jinaai/jina-embeddings-v2-base-code": {"trust_remote_code": True},
}

MODEL: str = os.getenv("MODEL", "all-MiniLM-L6-v2")
if MODEL not in ALLOWED_MODELS:
    raise ValueError(f"Model {MODEL} is not in the allowlist")

device = os.getenv("DEVICE", "cpu")

_model: SentenceTransformer = SentenceTransformer(
    MODEL, device=device, **_MODEL_KWARGS.get(MODEL, {})
)


def get_model() -> SentenceTransformer:
    return _model

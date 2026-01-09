from sentence_transformers import SentenceTransformer
import os

# load model from env
MODEL:str = os.getenv("MODEL", "all-MiniLM-L6-v2")

model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer(MODEL)
    return model

from .model import model
import numpy as np

def embed(texts:list[str]) -> np.ndarray:
    """
    Generate embeddings for a list of texts using the pre-trained model.

    Args:
        texts (List[str]): A list of text strings to generate embeddings for.

    Returns:
        np.ndarray: An array of embeddings, where each row corresponds to an input text.
    """
    return model.encode(texts)

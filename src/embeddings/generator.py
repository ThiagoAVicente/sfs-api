from .model import get_model
import numpy as np

class EmbeddingGenerator:

    @staticmethod
    def embed(texts: list[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts using the pre-trained model.

        Args:
            texts (List[str]): A list of text strings to generate embeddings for.

        Returns:
            np.ndarray: An array of embeddings, where each row corresponds to an input text.
        """
        # list can't be empty
        if not texts:
            raise ValueError("Input list is empty")

        # embed text
        model = get_model()
        return model.encode(texts)

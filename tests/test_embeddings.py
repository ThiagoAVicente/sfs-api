from unittest import TestCase
import numpy as np
from src.embeddings import EmbeddingGenerator, get_model

def setup_module():
    get_model()



class TestEmbeddings(TestCase):

    model = get_model()

    def test_embedding_returns_correct_shape(self):
        text = "This is a test"
        embedding = EmbeddingGenerator.embed(text)
        assert embedding is not None
        assert len(embedding) == 1
        assert len(embedding[0]) == self.model.get_sentence_embedding_dimension()

    def test_identical_texts_produce_identical_embeddings(self):
        text = "This is a test"
        embedding = EmbeddingGenerator.embed(text)
        equal = EmbeddingGenerator.embed(text)
        assert np.allclose(embedding, equal)

    def test_different_texts_produce_different_embeddings(self):
        text = "This is a test"
        embedding = EmbeddingGenerator.embed(text)
        dif = EmbeddingGenerator.embed("This is another test")
        assert not np.allclose(embedding, dif)

    def test_empty_list_raises_value_error(self):
        with self.assertRaises(ValueError) as context:
            EmbeddingGenerator.embed([])
        assert "Input is empty" in str(context.exception)

from unittest import TestCase
from src.embeddings.generator import embed
import numpy as np

class TestEmbeddings(TestCase):
    def test_embedding(self):
        text = "This is a test"
        embedding = embed([text])
        self.assertIsNotNone(embedding)
        self.assertEqual(len(embedding), 1)
        self.assertEqual(len(embedding[0]), 384)

        equal = embed([text])
        dif = embed(["This is another test"])

        assert np.allclose(embedding, equal)
        assert not np.allclose(embedding, dif)

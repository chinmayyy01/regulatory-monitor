from functools import lru_cache

from fastembed import TextEmbedding

MODEL_NAME = "BAAI/bge-small-en-v1.5"
DIMENSIONS = 384
BATCH_SIZE = 32


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    return TextEmbedding(MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return [vector.tolist() for vector in _model().embed(texts, batch_size=BATCH_SIZE)]


def parse_vector(value) -> list[float]:
    if isinstance(value, str):
        return [float(part) for part in value.strip("[]").split(",") if part]
    return list(value)


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{float(value):.6f}" for value in values) + "]"

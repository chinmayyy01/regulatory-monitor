from functools import lru_cache

from fastembed.rerank.cross_encoder import TextCrossEncoder

MODEL_NAME = "Xenova/ms-marco-MiniLM-L-6-v2"


@lru_cache(maxsize=1)
def _model() -> TextCrossEncoder:
    return TextCrossEncoder(MODEL_NAME)


def rerank(query: str, texts: list[str], top_k: int) -> list[int]:
    if not texts:
        return []
    scores = [float(score) for score in _model().rerank(query, texts)]
    order = sorted(range(len(texts)), key=lambda index: scores[index], reverse=True)
    return order[:top_k]

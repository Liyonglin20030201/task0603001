from __future__ import annotations
import jieba.analyse
from app.utils.textrank import textrank_summary


def generate_summary(text: str, num_sentences: int = 5) -> str:
    if not text or len(text.strip()) < 20:
        return text.strip() if text else ""
    return textrank_summary(text, num_sentences)


def extract_tags(text: str, top_k: int = 8) -> list[str]:
    if not text or len(text.strip()) < 5:
        return []
    tags = jieba.analyse.extract_tags(text, topK=top_k, withWeight=False)
    return tags

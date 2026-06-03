import re
import numpy as np
import jieba


def textrank_summary(text: str, num_sentences: int = 5) -> str:
    sentences = re.split(r'[。！？.!?\n]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    if len(sentences) <= num_sentences:
        return "。".join(sentences)

    words_per_sentence = []
    for sent in sentences:
        words = list(jieba.cut(sent))
        words_per_sentence.append(set(words))

    n = len(sentences)
    similarity_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(i + 1, n):
            common = words_per_sentence[i] & words_per_sentence[j]
            if not words_per_sentence[i] or not words_per_sentence[j]:
                continue
            sim = len(common) / (
                np.log(len(words_per_sentence[i]) + 1) + np.log(len(words_per_sentence[j]) + 1)
            )
            similarity_matrix[i][j] = sim
            similarity_matrix[j][i] = sim

    damping = 0.85
    scores = np.ones(n) / n
    for _ in range(30):
        new_scores = np.zeros(n)
        for i in range(n):
            row_sum = similarity_matrix[:, i].sum()
            if row_sum == 0:
                new_scores[i] = (1 - damping) / n
            else:
                new_scores[i] = (1 - damping) / n + damping * (
                    similarity_matrix[:, i] / row_sum * scores
                ).sum()
        scores = new_scores

    ranked_indices = scores.argsort()[::-1][:num_sentences]
    ranked_indices = sorted(ranked_indices)

    return "。".join(sentences[i] for i in ranked_indices)

"""
Lightweight TextRank summarizer
Uses NLTK + NetworkX only (no transformers / torch)
"""

import nltk

# Download required NLTK resources (silent if already present)
nltk.download("punkt", quiet=True)       # sentence tokenizer
nltk.download("punkt_tab", quiet=True)   # tokenization tables (NLTK ≥3.8)
nltk.download("stopwords", quiet=True)   # stop-word list

from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
import numpy as np
import networkx as nx

STOP_WORDS = set(stopwords.words("english"))

def _sentence_vector(sentence):
    """Return frequency vector for a sentence."""
    words = [w.lower() for w in word_tokenize(sentence) if w.isalnum()]
    all_words = list(set(words))
    return np.array([words.count(w) for w in all_words]), all_words

def _similarity(s1, s2):
    v1, vocab = _sentence_vector(s1)
    v2 = np.array([s2.lower().split().count(w) for w in vocab])
    if v1.sum() == 0 or v2.sum() == 0:
        return 0
    return 1 - cosine_distance(v1, v2)

def summarize_text(text: str) -> str:
    """Return a ~100-word TextRank summary (or fallback string)."""
    if not text or not text.strip():
        return "No summary available."

    # Truncate to 500 words for speed
    words = text.split()
    text = " ".join(words[:500])

    # Short texts just return themselves
    if len(words) < 30:
        return text

    sentences = sent_tokenize(text)
    if len(sentences) == 1:
        return sentences[0]

    # Build similarity matrix
    size = len(sentences)
    sim_matrix = np.zeros((size, size))
    for i in range(size):
        for j in range(size):
            if i != j:
                sim_matrix[i][j] = _similarity(sentences[i], sentences[j])

    # Rank sentences
    scores_dict = nx.pagerank(nx.from_numpy_array(sim_matrix), alpha=0.85, max_iter=100, tol=1e-4)
    scores = [scores_dict[i] for i in range(len(sentences))]
    ranked = sorted(
        ((scores[i], s, len(word_tokenize(s))) for i, s in enumerate(sentences)),
        reverse=True,
    )

    # Pick sentences until ~100 words
    chosen, total = [], 0
    for _, sent, wc in ranked:
        if total + wc > 100:
            break
        chosen.append(sent)
        total += wc

    chosen.sort(key=lambda s: sentences.index(s))
    summary = " ".join(chosen)
    return summary if summary.strip() else "Summary unavailable."

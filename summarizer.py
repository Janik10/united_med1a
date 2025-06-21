import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
import numpy as np
import networkx as nx

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

def build_similarity_matrix(sentences):
    """Build a similarity matrix for sentences using cosine similarity."""
    stop_words = set(stopwords.words('english'))
    similarity_matrix = np.zeros((len(sentences), len(sentences)))

    for i in range(len(sentences)):
        for j in range(len(sentences)):
            if i == j:
                continue
            sentence1 = [word.lower() for word in word_tokenize(sentences[i]) if word.lower() not in stop_words and word.isalnum()]
            sentence2 = [word.lower() for word in word_tokenize(sentences[j]) if word.lower() not in stop_words and word.isalnum()]
            if not sentence1 or not sentence2:
                continue
            similarity = 1 - cosine_distance(
                np.array([sentence1.count(word) for word in set(sentence1 + sentence2)]),
                np.array([sentence2.count(word) for word in set(sentence1 + sentence2)])
            )
            similarity_matrix[i][j] = similarity

    return similarity_matrix

def summarize_text(text):
    """Summarize text using TextRank with a word limit."""
    try:
        # Handle empty or whitespace-only text
        if not text or not text.strip():
            return "No summary available due to missing content."

        words = text.split()
        # If text is too short, return it as-is or a truncated version
        if len(words) < 10:
            return " ".join(words) if len(words) > 0 else "No summary available."

        # Truncate input text to first 500 words
        text = " ".join(words[:500])

        # Tokenize into sentences
        sentences = sent_tokenize(text)
        if not sentences:
            return " ".join(words[:10]) + "..." if words else "No summary available."

        # Build similarity matrix and rank sentences
        similarity_matrix = build_similarity_matrix(sentences)
        sentence_graph = nx.from_numpy_array(similarity_matrix)
        scores = nx.pagerank(sentence_graph, max_iter=100, tol=1e-06)

        # Sort sentences by score
        ranked_sentences = sorted(((scores[i], s, len(word_tokenize(s))) for i, s in enumerate(sentences)), reverse=True)

        # Select sentences until ~100 words
        summary_sentences = []
        total_words = 0
        for score, sentence, word_count in ranked_sentences:
            if total_words + word_count > 100:
                break
            summary_sentences.append(sentence)
            total_words += word_count

        # Order selected sentences by their original position
        summary_sentences.sort(key=lambda s: sentences.index(s))

        summary = " ".join(summary_sentences)
        return summary if summary.strip() else "Summary too brief to generate."

    except Exception as e:
        print(f"Error during TextRank summarization: {e}")
        return "Summary unavailable due to error. Partial text: " + text[:50] + "..." if text else "No content to summarize."
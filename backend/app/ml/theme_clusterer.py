"""
Theme Clustering ML Service

Identifies recurring themes in journal entries using embeddings and HDBSCAN.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import HDBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass
class ThemeCluster:
    """A detected theme cluster."""
    cluster_id: int
    keywords: list[str]          # Top keywords describing theme
    entry_indices: list[int]     # Indices of entries in this cluster
    entry_count: int
    percentage: float            # Percentage of total entries


@dataclass
class ThemeResult:
    """Result from theme clustering."""
    themes: list[ThemeCluster]
    unclustered_count: int
    model_version: str


class ThemeClusterer:
    """
    Identifies recurring themes in journal entries.
    
    Uses Sentence-BERT embeddings with HDBSCAN clustering.
    Does NOT interpret meaning or assign clinical significance.
    """

    MIN_ENTRIES = 5           # Minimum entries for clustering
    MIN_CLUSTER_SIZE = 2      # Minimum entries per cluster
    MODEL_VERSION = "theme-v1.0.0"

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize theme clusterer.
        
        Args:
            model_name: Sentence-BERT model name
        """
        self.encoder = SentenceTransformer(model_name)

    def detect_themes(
        self, 
        entries: list[str],
        min_cluster_size: Optional[int] = None,
    ) -> ThemeResult:
        """
        Detect recurring themes across entries.
        
        Args:
            entries: List of journal entry texts
            min_cluster_size: Override minimum cluster size
            
        Returns:
            ThemeResult with detected theme clusters
        """
        if len(entries) < self.MIN_ENTRIES:
            return ThemeResult(
                themes=[],
                unclustered_count=len(entries),
                model_version=self.MODEL_VERSION,
            )

        # Generate embeddings
        embeddings = self.encoder.encode(entries, show_progress_bar=False)

        # Cluster with HDBSCAN
        min_size = min_cluster_size or self.MIN_CLUSTER_SIZE
        clusterer = HDBSCAN(
            min_cluster_size=min_size,
            min_samples=1,
            metric="cosine",
        )
        labels = clusterer.fit_predict(embeddings)

        # Group entries by cluster
        clusters: dict[int, list[int]] = {}
        for idx, label in enumerate(labels):
            if label == -1:  # Noise
                continue
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(idx)

        # Extract keywords for each cluster
        themes = []
        for cluster_id, indices in clusters.items():
            cluster_texts = [entries[i] for i in indices]
            keywords = self._extract_keywords(cluster_texts)
            
            themes.append(ThemeCluster(
                cluster_id=cluster_id,
                keywords=keywords,
                entry_indices=indices,
                entry_count=len(indices),
                percentage=round(len(indices) / len(entries), 3),
            ))

        # Sort by size (largest themes first)
        themes.sort(key=lambda t: t.entry_count, reverse=True)

        unclustered = sum(1 for label in labels if label == -1)

        return ThemeResult(
            themes=themes,
            unclustered_count=unclustered,
            model_version=self.MODEL_VERSION,
        )

    def _extract_keywords(self, texts: list[str], top_k: int = 3) -> list[str]:
        """
        Extract top keywords from cluster texts using TF-IDF.
        
        Args:
            texts: Texts in the cluster
            top_k: Number of keywords to extract
            
        Returns:
            List of top keywords
        """
        if not texts:
            return []

        try:
            vectorizer = TfidfVectorizer(
                max_features=20,
                stop_words="english",
                ngram_range=(1, 2),
            )
            tfidf = vectorizer.fit_transform(texts)
            
            # Sum TF-IDF scores across documents
            scores = np.asarray(tfidf.sum(axis=0)).flatten()
            indices = scores.argsort()[-top_k:][::-1]
            keywords = [vectorizer.get_feature_names_out()[i] for i in indices]
            
            return keywords
        except ValueError:
            # Not enough text to extract keywords
            return []

    def get_entry_embedding(self, text: str) -> list[float]:
        """
        Get embedding vector for a single entry.
        
        Args:
            text: Entry text
            
        Returns:
            384-dimensional embedding vector
        """
        embedding = self.encoder.encode(text, show_progress_bar=False)
        return embedding.tolist()


# Singleton instance
_clusterer: Optional[ThemeClusterer] = None


def get_theme_clusterer() -> ThemeClusterer:
    """Get or create theme clusterer singleton."""
    global _clusterer
    if _clusterer is None:
        _clusterer = ThemeClusterer()
    return _clusterer

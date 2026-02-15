"""
Reflection Generation Engine

RAG-based system for generating grounded, multi-entry reflections
with psychological theory citations.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

import numpy as np

from app.ml.emotion_detector import EmotionDetector, EmotionResult
from app.ml.theme_clusterer import ThemeClusterer, ThemeResult
from app.ml.linguistic_analyzer import LinguisticAnalyzer, LinguisticMetrics
from app.ml.temporal_tracker import TemporalTracker, TemporalResult


@dataclass
class ConceptReference:
    """A psychological/philosophical concept referenced in reflection."""
    id: str
    name: str
    description: str
    source: str
    relevance_score: float


@dataclass
class ReflectionOutput:
    """Generated reflection with full metadata."""
    content: str
    entry_ids: list[UUID]
    date_range_start: date
    date_range_end: date
    concepts: list[ConceptReference]
    confidence_score: float
    patterns_detected: dict
    disclaimer: str
    model_version: str
    generated_at: datetime


class ReflectionEngine:
    """
    Generates grounded reflections from longitudinal journal analysis.
    
    Requirements (enforced):
    - Minimum 3 entries across 7+ days
    - Probabilistic language only ("may suggest", "resembles")
    - At least 1 concept citation per reflection
    - Confidence capped at 80%
    - Never diagnostic, never prescriptive
    """

    MIN_ENTRIES = 3
    MIN_DAYS_SPAN = 7
    MAX_CONFIDENCE = 0.80
    MAX_REFLECTIONS_PER_WEEK = 2
    MODEL_VERSION = "reflection-v1.0.0"

    DISCLAIMER = (
        "This reflection is not medical advice. Pensieve does not diagnose "
        "or treat mental health conditions. If you're experiencing distress, "
        "please reach out to a mental health professional."
    )

    # Hedging words required in reflections
    HEDGING_PHRASES = [
        "may suggest", "could indicate", "resembles", "appears to",
        "might reflect", "seems to show", "patterns that resemble",
        "which may relate to", "possibly connected to"
    ]

    # Forbidden language patterns
    FORBIDDEN_PATTERNS = [
        r"\byou should\b", r"\byou must\b", r"\byou need to\b",
        r"\bstop\b.*\bing\b", r"\bdiagnos", r"\bdepression\b",
        r"\banxiety disorder\b", r"\bbipolar\b", r"\bschizophren",
        r"\byou are experiencing\b", r"\byou have\b.*\bdisorder\b",
    ]

    def __init__(
        self,
        emotion_detector: EmotionDetector,
        theme_clusterer: ThemeClusterer,
        linguistic_analyzer: LinguisticAnalyzer,
        temporal_tracker: TemporalTracker,
    ):
        self.emotion_detector = emotion_detector
        self.theme_clusterer = theme_clusterer
        self.linguistic_analyzer = linguistic_analyzer
        self.temporal_tracker = temporal_tracker

    def should_generate_reflection(
        self,
        entry_count: int,
        date_span_days: int,
        recent_reflection_count: int,
    ) -> bool:
        """
        Determine if a reflection should be generated.
        
        Args:
            entry_count: Number of entries available
            date_span_days: Days between oldest and newest entry
            recent_reflection_count: Reflections generated in past 7 days
            
        Returns:
            True if conditions are met for generating a reflection
        """
        if entry_count < self.MIN_ENTRIES:
            return False
        if date_span_days < self.MIN_DAYS_SPAN:
            return False
        if recent_reflection_count >= self.MAX_REFLECTIONS_PER_WEEK:
            return False
        return True

    def generate(
        self,
        entries: list[dict],  # {id, content, date}
        concepts: list[dict],  # {id, name, description, source, embedding}
    ) -> Optional[ReflectionOutput]:
        """
        Generate a reflection from multiple entries.
        
        Args:
            entries: List of decrypted journal entries with id, content, date
            concepts: Available concepts for citation
            
        Returns:
            ReflectionOutput or None if conditions not met
        """
        # Validate minimum requirements
        if len(entries) < self.MIN_ENTRIES:
            return None

        dates = [e["date"] for e in entries]
        date_span = (max(dates) - min(dates)).days
        if date_span < self.MIN_DAYS_SPAN:
            return None

        # Extract texts
        texts = [e["content"] for e in entries]
        entry_ids = [e["id"] for e in entries]

        # Run analysis pipeline
        emotion_results = [self.emotion_detector.predict(t) for t in texts]
        theme_result = self.theme_clusterer.detect_themes(texts)
        linguistic_results = [self.linguistic_analyzer.analyze(t) for t in texts]
        
        # Aggregate for temporal analysis
        temporal_result = self._run_temporal_analysis(dates, emotion_results, linguistic_results)

        # Find dominant patterns
        dominant_emotion = self._get_dominant_emotion(emotion_results)
        dominant_theme = self._get_dominant_theme(theme_result)
        linguistic_trend = self._get_linguistic_trend(linguistic_results, temporal_result)

        # Retrieve relevant concepts
        pattern_summary = f"{dominant_emotion} {dominant_theme} {linguistic_trend}"
        relevant_concepts = self._retrieve_concepts(pattern_summary, concepts, top_k=2)

        if not relevant_concepts:
            return None  # Cannot generate without conceptual grounding

        # Calculate confidence
        confidence = self._calculate_confidence(emotion_results, theme_result, temporal_result)

        # Generate reflection text
        content = self._compose_reflection(
            entry_count=len(entries),
            date_span=date_span,
            dominant_emotion=dominant_emotion,
            dominant_theme=dominant_theme,
            linguistic_trend=linguistic_trend,
            temporal_trend=self._get_primary_trend(temporal_result),
            concepts=relevant_concepts,
        )

        # Validate reflection
        if not self._validate_reflection(content):
            return None

        return ReflectionOutput(
            content=content,
            entry_ids=entry_ids,
            date_range_start=min(dates),
            date_range_end=max(dates),
            concepts=relevant_concepts,
            confidence_score=confidence,
            patterns_detected={
                "dominant_emotion": dominant_emotion,
                "dominant_theme": dominant_theme,
                "linguistic_trend": linguistic_trend,
                "temporal_trends": [t.metric_name for t in temporal_result.trends] if temporal_result else [],
            },
            disclaimer=self.DISCLAIMER,
            model_version=self.MODEL_VERSION,
            generated_at=datetime.now(timezone.utc),
        )

    def _run_temporal_analysis(
        self,
        dates: list[date],
        emotions: list[EmotionResult],
        linguistics: list[LinguisticMetrics],
    ) -> Optional[TemporalResult]:
        """Run temporal analysis on aggregated metrics."""
        if len(dates) < 5:
            return None

        # Aggregate metrics
        metrics = {}
        metric_types = {}

        # Emotion metrics (top emotions over time)
        if emotions:
            for emotion in ["joy", "sadness", "anger", "fear", "love"]:
                values = [e.emotions.get(emotion, 0.0) for e in emotions]
                metrics[emotion] = values
                metric_types[emotion] = "emotion"

        # Linguistic metrics
        if linguistics:
            metrics["first_person"] = [l.pronoun_usage["first_person"] for l in linguistics]
            metrics["certainty"] = [l.certainty_score for l in linguistics]
            metric_types["first_person"] = "linguistic"
            metric_types["certainty"] = "linguistic"

        return self.temporal_tracker.analyze_trends(dates, metrics, metric_types)

    def _get_dominant_emotion(self, results: list[EmotionResult]) -> str:
        """Find the most frequent dominant emotion across entries."""
        from collections import Counter
        top_emotions = []
        for r in results:
            if r.top_emotions:
                top_emotions.append(r.top_emotions[0])
        if not top_emotions:
            return "mixed feelings"
        return Counter(top_emotions).most_common(1)[0][0]

    def _get_dominant_theme(self, result: ThemeResult) -> str:
        """Get the largest theme cluster's keywords."""
        if not result.themes:
            return "various topics"
        largest = result.themes[0]
        return " and ".join(largest.keywords[:2]) if largest.keywords else "general themes"

    def _get_linguistic_trend(
        self,
        results: list[LinguisticMetrics],
        temporal: Optional[TemporalResult],
    ) -> str:
        """Summarize linguistic patterns."""
        if not results:
            return "consistent writing style"

        # Check first-person usage
        avg_first_person = np.mean([r.pronoun_usage["first_person"] for r in results])
        
        # Check certainty
        avg_certainty = np.mean([r.certainty_score for r in results])

        if avg_first_person > 0.08:
            if avg_certainty > 0.5:
                return "self-focused and assertive writing"
            else:
                return "self-reflective and tentative writing"
        else:
            return "outward-focused writing"

    def _get_primary_trend(self, temporal: Optional[TemporalResult]) -> Optional[str]:
        """Get the most significant trend."""
        if not temporal or not temporal.trends:
            return None
        
        # Find trend with highest confidence
        significant = [t for t in temporal.trends if t.direction not in ("stable", "insufficient_data")]
        if not significant:
            return None
        
        best = max(significant, key=lambda t: t.confidence)
        return f"{best.metric_name} is {best.direction}"

    def _retrieve_concepts(
        self,
        query: str,
        concepts: list[dict],
        top_k: int = 2,
    ) -> list[ConceptReference]:
        """Retrieve relevant concepts using semantic similarity."""
        if not concepts:
            return []

        # Simple keyword matching for now (in production, use vector similarity)
        query_words = set(query.lower().split())
        scored = []
        
        for concept in concepts:
            # Score based on keyword overlap
            concept_words = set(concept["name"].lower().split())
            concept_words.update(concept["description"].lower().split()[:50])
            if "tags" in concept:
                concept_words.update(t.lower() for t in concept.get("tags", []))
            
            overlap = len(query_words & concept_words)
            if overlap > 0:
                scored.append((concept, overlap / len(query_words)))

        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [
            ConceptReference(
                id=str(c[0]["id"]),
                name=c[0]["name"],
                description=c[0]["description"][:200],
                source=c[0]["source_citation"],
                relevance_score=min(c[1], self.MAX_CONFIDENCE),
            )
            for c in scored[:top_k]
        ]

    def _calculate_confidence(
        self,
        emotions: list[EmotionResult],
        themes: ThemeResult,
        temporal: Optional[TemporalResult],
    ) -> float:
        """Calculate overall confidence score (capped at 80%)."""
        scores = []

        # Emotion confidence
        if emotions:
            avg_emotion_conf = np.mean([e.confidence for e in emotions])
            scores.append(avg_emotion_conf)

        # Theme confidence (based on cluster coverage)
        if themes.themes:
            coverage = 1 - (themes.unclustered_count / (themes.unclustered_count + sum(t.entry_count for t in themes.themes)))
            scores.append(coverage * 0.8)

        # Temporal confidence
        if temporal and temporal.trends:
            avg_temporal = np.mean([t.confidence for t in temporal.trends if t.direction != "insufficient_data"])
            if not np.isnan(avg_temporal):
                scores.append(avg_temporal)

        if not scores:
            return 0.3  # Low default confidence

        # Average and cap
        raw_confidence = np.mean(scores)
        return round(min(raw_confidence, self.MAX_CONFIDENCE), 3)

    def _compose_reflection(
        self,
        entry_count: int,
        date_span: int,
        dominant_emotion: str,
        dominant_theme: str,
        linguistic_trend: str,
        temporal_trend: Optional[str],
        concepts: list[ConceptReference],
    ) -> str:
        """Compose reflection text with hedging language and citations."""
        # Opening with temporal context
        reflection = f"Over the past {date_span} days across {entry_count} entries, "
        reflection += f"your writing shows patterns that may suggest "

        # Core insight with hedging
        if temporal_trend:
            reflection += f"a period where {temporal_trend}. "
        else:
            reflection += f"themes of {dominant_theme} paired with {dominant_emotion}. "

        # Connect to concept with hedging
        if concepts:
            concept = concepts[0]
            reflection += f"\n\nThis pattern resembles what "
            reflection += f"researchers describe as **{concept.name}**"
            
            # Add source
            reflection += f" ({concept.source}). "
            
            # Brief explanation
            reflection += f"{concept.description}"
            if not concept.description.endswith("."):
                reflection += "."

        # Add second concept if available
        if len(concepts) > 1:
            reflection += f"\n\nYou might also find the concept of "
            reflection += f"**{concepts[1].name}** relevant—it offers "
            reflection += "another lens for understanding these patterns."

        return reflection

    def _validate_reflection(self, content: str) -> bool:
        """
        Validate reflection meets ethical constraints.
        
        Returns:
            True if reflection is valid, False if it violates constraints
        """
        content_lower = content.lower()

        # Check for forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, content_lower):
                return False

        # Check for hedging language
        has_hedging = any(phrase in content_lower for phrase in self.HEDGING_PHRASES)
        if not has_hedging:
            return False

        return True

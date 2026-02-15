"""
Linguistic Trend Analyzer

Extracts writing patterns and linguistic metrics from journal entries.
"""

from dataclasses import dataclass
from typing import Optional

import spacy
from collections import Counter


@dataclass
class LinguisticMetrics:
    """Linguistic metrics extracted from text."""
    pronoun_usage: dict[str, float]   # first_person, second_person, third_person
    tense_distribution: dict[str, float]  # past, present, future
    certainty_score: float            # 0-1, higher = more certain language
    hedging_score: float              # 0-1, higher = more hedging
    emotional_intensity: float        # 0-1, based on emotion words
    complexity: dict[str, float]      # avg_sentence_length, word_count
    model_version: str


class LinguisticAnalyzer:
    """
    Analyzes writing patterns in journal entries.
    
    Extracts:
    - Pronoun usage (I/we vs they)
    - Verb tense distribution
    - Certainty vs hedging language
    - Sentence complexity
    
    Does NOT infer mental state from linguistics alone.
    """

    MODEL_VERSION = "linguistic-v1.0.0"

    # Word lists for analysis
    FIRST_PERSON = {"i", "me", "my", "mine", "myself", "we", "us", "our", "ours", "ourselves"}
    SECOND_PERSON = {"you", "your", "yours", "yourself", "yourselves"}
    THIRD_PERSON = {"he", "she", "it", "they", "him", "her", "them", "his", "hers", "its", "their", "theirs"}

    HEDGING_WORDS = {
        "might", "maybe", "perhaps", "possibly", "probably", "could", "would", 
        "should", "seem", "seems", "appear", "appears", "guess", "think", 
        "believe", "feel", "suppose", "somewhat", "slightly", "rather"
    }

    CERTAINTY_WORDS = {
        "definitely", "certainly", "absolutely", "always", "never", "must",
        "will", "know", "sure", "certain", "clearly", "obviously", "undoubtedly",
        "truly", "really", "completely", "totally", "exactly"
    }

    EMOTION_WORDS = {
        "happy", "sad", "angry", "afraid", "anxious", "excited", "frustrated",
        "grateful", "hopeful", "hopeless", "love", "hate", "fear", "joy",
        "worry", "stress", "stressed", "overwhelmed", "peaceful", "calm",
        "nervous", "confident", "insecure", "proud", "ashamed", "guilty"
    }

    # Verb tags for tense detection
    PAST_TAGS = {"VBD", "VBN"}
    PRESENT_TAGS = {"VB", "VBG", "VBP", "VBZ"}
    FUTURE_INDICATORS = {"will", "shall", "going"}

    def __init__(self, model: str = "en_core_web_sm"):
        """
        Initialize linguistic analyzer.
        
        Args:
            model: spaCy model name
        """
        try:
            self.nlp = spacy.load(model)
        except OSError:
            # Download model if not present
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model], check=True)
            self.nlp = spacy.load(model)

    def analyze(self, text: str) -> LinguisticMetrics:
        """
        Analyze linguistic patterns in text.
        
        Args:
            text: Journal entry text
            
        Returns:
            LinguisticMetrics with extracted patterns
        """
        doc = self.nlp(text)
        words = [token.text.lower() for token in doc if token.is_alpha]
        word_count = len(words)

        if word_count == 0:
            return self._empty_metrics()

        # Pronoun analysis
        pronoun_usage = self._analyze_pronouns(words, word_count)

        # Tense distribution
        tense_distribution = self._analyze_tense(doc)

        # Certainty vs hedging
        certainty_score, hedging_score = self._analyze_certainty(words, word_count)

        # Emotional intensity
        emotional_intensity = self._analyze_emotion_words(words, word_count)

        # Complexity
        sentences = list(doc.sents)
        complexity = {
            "word_count": float(word_count),
            "sentence_count": float(len(sentences)),
            "avg_sentence_length": word_count / len(sentences) if sentences else 0.0,
            "avg_word_length": sum(len(w) for w in words) / word_count if word_count else 0.0,
        }

        return LinguisticMetrics(
            pronoun_usage=pronoun_usage,
            tense_distribution=tense_distribution,
            certainty_score=round(certainty_score, 3),
            hedging_score=round(hedging_score, 3),
            emotional_intensity=round(emotional_intensity, 3),
            complexity=complexity,
            model_version=self.MODEL_VERSION,
        )

    def _analyze_pronouns(self, words: list[str], total: int) -> dict[str, float]:
        """Analyze pronoun usage patterns."""
        first = sum(1 for w in words if w in self.FIRST_PERSON) / total
        second = sum(1 for w in words if w in self.SECOND_PERSON) / total
        third = sum(1 for w in words if w in self.THIRD_PERSON) / total

        return {
            "first_person": round(first, 4),
            "second_person": round(second, 4),
            "third_person": round(third, 4),
        }

    def _analyze_tense(self, doc) -> dict[str, float]:
        """Analyze verb tense distribution."""
        verbs = [token for token in doc if token.pos_ == "VERB"]
        
        if not verbs:
            return {"past": 0.0, "present": 0.0, "future": 0.0}

        past = sum(1 for v in verbs if v.tag_ in self.PAST_TAGS)
        present = sum(1 for v in verbs if v.tag_ in self.PRESENT_TAGS)
        
        # Detect future tense (will + verb, going to + verb)
        future = 0
        for i, token in enumerate(doc):
            if token.text.lower() in self.FUTURE_INDICATORS:
                if i + 1 < len(doc) and doc[i + 1].pos_ == "VERB":
                    future += 1

        total_verbs = past + present + future
        if total_verbs == 0:
            return {"past": 0.0, "present": 0.0, "future": 0.0}

        return {
            "past": round(past / total_verbs, 3),
            "present": round(present / total_verbs, 3),
            "future": round(future / total_verbs, 3),
        }

    def _analyze_certainty(self, words: list[str], total: int) -> tuple[float, float]:
        """Analyze certainty vs hedging language."""
        hedging = sum(1 for w in words if w in self.HEDGING_WORDS)
        certain = sum(1 for w in words if w in self.CERTAINTY_WORDS)

        hedging_score = hedging / total
        certainty_score = certain / total

        # Normalize to 0-1 scale (typical values are quite low)
        hedging_score = min(hedging_score * 10, 1.0)
        certainty_score = min(certainty_score * 10, 1.0)

        return certainty_score, hedging_score

    def _analyze_emotion_words(self, words: list[str], total: int) -> float:
        """Analyze emotional word frequency."""
        emotion_count = sum(1 for w in words if w in self.EMOTION_WORDS)
        intensity = emotion_count / total
        # Normalize to 0-1 scale
        return min(intensity * 20, 1.0)

    def _empty_metrics(self) -> LinguisticMetrics:
        """Return empty metrics for empty/invalid text."""
        return LinguisticMetrics(
            pronoun_usage={"first_person": 0.0, "second_person": 0.0, "third_person": 0.0},
            tense_distribution={"past": 0.0, "present": 0.0, "future": 0.0},
            certainty_score=0.0,
            hedging_score=0.0,
            emotional_intensity=0.0,
            complexity={"word_count": 0.0, "sentence_count": 0.0, "avg_sentence_length": 0.0, "avg_word_length": 0.0},
            model_version=self.MODEL_VERSION,
        )


# Singleton instance
_analyzer: Optional[LinguisticAnalyzer] = None


def get_linguistic_analyzer() -> LinguisticAnalyzer:
    """Get or create linguistic analyzer singleton."""
    global _analyzer
    if _analyzer is None:
        _analyzer = LinguisticAnalyzer()
    return _analyzer

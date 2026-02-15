"""
Emotion Detection ML Service

Multi-label emotion classification using fine-tuned DistilBERT on GoEmotions.
"""

from dataclasses import dataclass
from typing import Optional

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


@dataclass
class EmotionResult:
    """Result from emotion detection."""
    emotions: dict[str, float]  # emotion -> probability
    top_emotions: list[str]     # Top 5 emotions above threshold
    confidence: float           # Overall confidence (capped at 0.8)
    model_version: str


class EmotionDetector:
    """
    Multi-label emotion classifier using GoEmotions-trained model.
    
    Outputs probability distributions over 27 emotions, never claims
    ground truth. Confidence is capped at 80% per ethical constraints.
    """

    EMOTIONS = [
        "admiration", "amusement", "anger", "annoyance", "approval",
        "caring", "confusion", "curiosity", "desire", "disappointment",
        "disapproval", "disgust", "embarrassment", "excitement", "fear",
        "gratitude", "grief", "joy", "love", "nervousness",
        "optimism", "pride", "realization", "relief", "remorse",
        "sadness", "surprise", "neutral"
    ]

    MAX_CONFIDENCE = 0.80  # Ethical constraint: never claim certainty
    THRESHOLD = 0.25       # Minimum probability to include emotion
    MODEL_VERSION = "emotion-v1.0.0"

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize emotion detector.
        
        Args:
            model_path: Path to fine-tuned model. If None, uses pretrained.
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Use a pretrained model for now (in production, use fine-tuned)
        model_name = model_path or "SamLowe/roberta-base-go_emotions"
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

    def predict(self, text: str) -> EmotionResult:
        """
        Detect emotion probabilities in text.
        
        Args:
            text: Journal entry text
            
        Returns:
            EmotionResult with probability distribution
        """
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        ).to(self.device)

        # Inference
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.sigmoid(outputs.logits).squeeze().cpu().numpy()

        # Build emotion dict
        emotions = {
            emotion: float(prob)
            for emotion, prob in zip(self.EMOTIONS, probabilities)
        }

        # Filter to emotions above threshold, sorted by probability
        filtered = {
            k: v for k, v in sorted(emotions.items(), key=lambda x: x[1], reverse=True)
            if v >= self.THRESHOLD
        }

        top_emotions = list(filtered.keys())[:5]

        # Calculate overall confidence (average of top emotions, capped)
        if top_emotions:
            raw_confidence = sum(filtered[e] for e in top_emotions) / len(top_emotions)
            confidence = min(raw_confidence, self.MAX_CONFIDENCE)
        else:
            confidence = 0.0

        return EmotionResult(
            emotions=filtered,
            top_emotions=top_emotions,
            confidence=round(confidence, 3),
            model_version=self.MODEL_VERSION,
        )

    def predict_batch(self, texts: list[str]) -> list[EmotionResult]:
        """
        Detect emotions in multiple texts.
        
        Args:
            texts: List of journal entries
            
        Returns:
            List of EmotionResults
        """
        return [self.predict(text) for text in texts]


# Singleton instance (lazy-loaded)
_detector: Optional[EmotionDetector] = None


def get_emotion_detector() -> EmotionDetector:
    """Get or create emotion detector singleton."""
    global _detector
    if _detector is None:
        _detector = EmotionDetector()
    return _detector

"""
Temporal Pattern Tracker

Detects trends in metrics across time series of journal entries.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

import numpy as np
from scipy import stats


@dataclass
class Trend:
    """A detected trend in a metric."""
    metric_name: str
    metric_type: str              # 'emotion', 'linguistic', 'theme'
    direction: str                # 'increasing', 'decreasing', 'stable', 'cyclical', 'insufficient_data'
    slope: float                  # Rate of change
    confidence: float             # Statistical confidence (capped at 0.8)
    r_squared: float              # Goodness of fit
    period_days: Optional[int]    # For cyclical patterns


@dataclass
class TemporalResult:
    """Result from temporal analysis."""
    trends: list[Trend]
    window_start: date
    window_end: date
    data_points: int
    model_version: str


class TemporalTracker:
    """
    Detects trends in metrics over time.
    
    Analyzes time series of emotion, linguistic, and theme patterns
    to identify increasing, decreasing, stable, or cyclical trends.
    
    Does NOT predict future states or label patterns as pathological.
    """

    MIN_DATA_POINTS = 5           # Minimum entries for trend detection
    SIGNIFICANCE_THRESHOLD = 0.1  # p-value threshold for significance
    SLOPE_THRESHOLD = 0.005       # Minimum slope to call increasing/decreasing
    MAX_CONFIDENCE = 0.80         # Ethical constraint
    MODEL_VERSION = "temporal-v1.0.0"

    def analyze_trends(
        self,
        dates: list[date],
        metrics: dict[str, list[float]],
        metric_types: dict[str, str],
    ) -> TemporalResult:
        """
        Analyze trends across multiple metrics.
        
        Args:
            dates: List of dates corresponding to entries
            metrics: Dict of metric_name -> list of values
            metric_types: Dict of metric_name -> type ('emotion', 'linguistic', 'theme')
            
        Returns:
            TemporalResult with detected trends
        """
        if len(dates) < self.MIN_DATA_POINTS:
            return TemporalResult(
                trends=[],
                window_start=min(dates) if dates else date.today(),
                window_end=max(dates) if dates else date.today(),
                data_points=len(dates),
                model_version=self.MODEL_VERSION,
            )

        trends = []
        for metric_name, values in metrics.items():
            if len(values) != len(dates):
                continue
                
            trend = self._detect_trend(
                dates=dates,
                values=values,
                metric_name=metric_name,
                metric_type=metric_types.get(metric_name, "unknown"),
            )
            trends.append(trend)

        return TemporalResult(
            trends=trends,
            window_start=min(dates),
            window_end=max(dates),
            data_points=len(dates),
            model_version=self.MODEL_VERSION,
        )

    def _detect_trend(
        self,
        dates: list[date],
        values: list[float],
        metric_name: str,
        metric_type: str,
    ) -> Trend:
        """
        Detect trend direction for a single metric.
        
        Uses linear regression for trend detection and
        autocorrelation for cyclical patterns.
        """
        if len(values) < self.MIN_DATA_POINTS:
            return Trend(
                metric_name=metric_name,
                metric_type=metric_type,
                direction="insufficient_data",
                slope=0.0,
                confidence=0.0,
                r_squared=0.0,
                period_days=None,
            )

        # Convert dates to numeric (days since start)
        start_date = min(dates)
        x = np.array([(d - start_date).days for d in dates], dtype=float)
        y = np.array(values, dtype=float)

        # Check for cyclical pattern first
        is_cyclical, period = self._detect_cyclical(y)
        if is_cyclical:
            return Trend(
                metric_name=metric_name,
                metric_type=metric_type,
                direction="cyclical",
                slope=0.0,
                confidence=min(0.7, self.MAX_CONFIDENCE),  # Moderate confidence for cycles
                r_squared=0.0,
                period_days=period,
            )

        # Linear regression for trend
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        r_squared = r_value ** 2

        # Calculate confidence (1 - p_value, capped)
        raw_confidence = 1 - p_value
        confidence = min(raw_confidence, self.MAX_CONFIDENCE)

        # Determine direction
        if p_value > self.SIGNIFICANCE_THRESHOLD:
            direction = "stable"
        elif slope > self.SLOPE_THRESHOLD:
            direction = "increasing"
        elif slope < -self.SLOPE_THRESHOLD:
            direction = "decreasing"
        else:
            direction = "stable"

        return Trend(
            metric_name=metric_name,
            metric_type=metric_type,
            direction=direction,
            slope=round(slope, 6),
            confidence=round(confidence, 3),
            r_squared=round(r_squared, 3),
            period_days=None,
        )

    def _detect_cyclical(
        self, 
        values: list[float], 
        min_period: int = 5,
        max_period: int = 14,
    ) -> tuple[bool, Optional[int]]:
        """
        Detect cyclical patterns using autocorrelation.
        
        Args:
            values: Time series values
            min_period: Minimum period to check (days)
            max_period: Maximum period to check (days)
            
        Returns:
            Tuple of (is_cyclical, period_days)
        """
        if len(values) < max_period * 2:
            return False, None

        # Normalize values
        values = np.array(values)
        values = (values - np.mean(values)) / (np.std(values) + 1e-8)

        # Compute autocorrelation
        autocorr = np.correlate(values, values, mode="full")
        autocorr = autocorr[len(autocorr) // 2:]
        autocorr = autocorr / autocorr[0]

        # Find peaks in autocorrelation (indicates periodicity)
        for lag in range(min_period, min(max_period, len(autocorr))):
            if autocorr[lag] > 0.4:  # Significant correlation at lag
                # Check if this is a local maximum
                if lag > 0 and lag < len(autocorr) - 1:
                    if autocorr[lag] > autocorr[lag - 1] and autocorr[lag] > autocorr[lag + 1]:
                        return True, lag

        return False, None

    def get_rolling_average(
        self,
        dates: list[date],
        values: list[float],
        window_days: int = 7,
    ) -> list[tuple[date, float]]:
        """
        Calculate rolling average for smoothing.
        
        Args:
            dates: List of dates
            values: Corresponding values
            window_days: Window size in days
            
        Returns:
            List of (date, rolling_average) tuples
        """
        if not dates or not values:
            return []

        # Sort by date
        sorted_pairs = sorted(zip(dates, values), key=lambda x: x[0])
        
        result = []
        for i, (current_date, _) in enumerate(sorted_pairs):
            window_start = current_date - timedelta(days=window_days)
            window_values = [
                v for d, v in sorted_pairs
                if window_start <= d <= current_date
            ]
            if window_values:
                avg = sum(window_values) / len(window_values)
                result.append((current_date, round(avg, 4)))

        return result


# Singleton instance
_tracker: Optional[TemporalTracker] = None


def get_temporal_tracker() -> TemporalTracker:
    """Get or create temporal tracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = TemporalTracker()
    return _tracker

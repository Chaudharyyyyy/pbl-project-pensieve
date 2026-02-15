"""
Reflections API Routes

Full implementation with ML-powered reflection generation.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import json
import logging

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func

from app.api.dependencies import CurrentUser, DbSession, Encryption
from app.api.schemas import (
    ConceptReferenceResponse,
    ReflectionListResponse,
    ReflectionMetadata,
    ReflectionResponse,
)
from app.models.database import Entry, Reflection, Concept, User

router = APIRouter(prefix="/reflections", tags=["Reflections"])
logger = logging.getLogger(__name__)

DISCLAIMER = "This reflection is not medical advice. Pensieve does not diagnose or treat mental health conditions."

# ML components - lazy loaded
_reflection_engine = None


def get_reflection_engine():
    """Lazy-load the reflection engine and ML models."""
    global _reflection_engine
    if _reflection_engine is not None:
        return _reflection_engine
    
    try:
        from app.services.reflection_engine import ReflectionEngine
        from app.ml.emotion_detector import EmotionDetector
        from app.ml.theme_clusterer import ThemeClusterer
        from app.ml.linguistic_analyzer import LinguisticAnalyzer
        from app.ml.temporal_tracker import TemporalTracker
        
        # Initialize ML components
        emotion_detector = EmotionDetector()
        theme_clusterer = ThemeClusterer()
        linguistic_analyzer = LinguisticAnalyzer()
        temporal_tracker = TemporalTracker()
        
        _reflection_engine = ReflectionEngine(
            emotion_detector=emotion_detector,
            theme_clusterer=theme_clusterer,
            linguistic_analyzer=linguistic_analyzer,
            temporal_tracker=temporal_tracker,
        )
        logger.info("Reflection engine initialized successfully")
        return _reflection_engine
    except ImportError as e:
        logger.warning(f"ML dependencies not available: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize reflection engine: {e}")
        return None


@router.get("/suggest", response_model=ReflectionListResponse)
async def suggest_reflections(
    current_user: CurrentUser,
    db: DbSession,
    encryption: Encryption,
):
    """
    Generate reflections based on recent journal entries.
    
    Requires:
    - Minimum 3 entries
    - Entries spanning at least 7 days
    - No more than 2 reflections in the past week
    """
    user_id = current_user.user_id
    
    # Check recent reflection count (max 2 per week)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_reflection_count = (await db.execute(
        select(func.count()).select_from(Reflection).where(
            Reflection.user_id == user_id,
            Reflection.created_at >= week_ago,
        )
    )).scalar() or 0
    
    if recent_reflection_count >= 2:
        return ReflectionListResponse(reflections=[], total=0)
    
    # Get user's entries from the last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    entries_result = await db.execute(
        select(Entry)
        .where(Entry.user_id == user_id, Entry.created_at >= thirty_days_ago)
        .order_by(Entry.entry_date.desc())
        .limit(50)
    )
    entries = entries_result.scalars().all()
    
    if len(entries) < 3:
        return ReflectionListResponse(reflections=[], total=0)
    
    # Check date span
    dates = [e.entry_date for e in entries]
    date_span = (max(dates) - min(dates)).days
    if date_span < 7:
        return ReflectionListResponse(reflections=[], total=0)
    
    # Get reflection engine
    engine = get_reflection_engine()
    if engine is None:
        # ML not available - return empty
        return ReflectionListResponse(reflections=[], total=0)
    
    # Decrypt entries
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()
    key = encryption.derive_key("temp_session_key", user.encryption_key_salt)
    
    decrypted_entries = []
    for entry in entries:
        try:
            content = encryption.decrypt_from_storage(
                entry.encrypted_content,
                entry.encryption_iv,
                entry.auth_tag,
                key,
            )
            decrypted_entries.append({
                "id": entry.id,
                "content": content,
                "date": entry.entry_date,
            })
        except Exception:
            continue
    
    if len(decrypted_entries) < 3:
        return ReflectionListResponse(reflections=[], total=0)
    
    # Get concepts for citation
    concepts_result = await db.execute(select(Concept))
    concepts = concepts_result.scalars().all()
    concepts_data = [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "source": c.source_citation,
            "embedding": json.loads(c.embedding_json) if c.embedding_json else None,
        }
        for c in concepts
    ]
    
    # Check if should generate
    if not engine.should_generate_reflection(
        entry_count=len(decrypted_entries),
        date_span_days=date_span,
        recent_reflection_count=recent_reflection_count,
    ):
        return ReflectionListResponse(reflections=[], total=0)
    
    # Generate reflection
    try:
        reflection_output = engine.generate(
            entries=decrypted_entries,
            concepts=concepts_data,
        )
    except Exception as e:
        logger.error(f"Reflection generation failed: {e}")
        return ReflectionListResponse(reflections=[], total=0)
    
    if reflection_output is None:
        return ReflectionListResponse(reflections=[], total=0)
    
    # Save reflection to database
    new_reflection = Reflection(
        user_id=user_id,
        content=reflection_output.content,
        metadata_json=json.dumps({
            "patterns_detected": reflection_output.patterns_detected,
            "model_version": reflection_output.model_version,
        }),
        entry_ids_json=json.dumps([str(eid) for eid in reflection_output.entry_ids]),
        date_range_start=reflection_output.date_range_start,
        date_range_end=reflection_output.date_range_end,
        confidence_score=reflection_output.confidence_score,
    )
    db.add(new_reflection)
    await db.commit()
    await db.refresh(new_reflection)
    
    # Build response
    response_reflection = ReflectionResponse(
        id=new_reflection.id,
        content=new_reflection.content,
        metadata=ReflectionMetadata(
            entries_analyzed=len(reflection_output.entry_ids),
            date_range=f"{reflection_output.date_range_start} to {reflection_output.date_range_end}",
            concepts=[
                ConceptReferenceResponse(
                    id=c.id,
                    name=c.name,
                    description=c.description,
                    source=c.source,
                    relevance_score=c.relevance_score,
                )
                for c in reflection_output.concepts
            ],
            confidence="high" if reflection_output.confidence_score > 0.7 else "moderate" if reflection_output.confidence_score > 0.5 else "low",
            confidence_score=reflection_output.confidence_score,
            model_version=reflection_output.model_version,
        ),
        created_at=new_reflection.created_at,
        disclaimer=DISCLAIMER,
    )
    
    return ReflectionListResponse(
        reflections=[response_reflection],
        total=1,
    )


@router.get("", response_model=ReflectionListResponse)
async def list_reflections(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    """List user's past reflections."""
    user_id = current_user.user_id
    
    count_result = await db.execute(
        select(func.count()).select_from(Reflection).where(
            Reflection.user_id == user_id,
            Reflection.dismissed_at.is_(None),
        )
    )
    total = count_result.scalar() or 0
    
    result = await db.execute(
        select(Reflection)
        .where(Reflection.user_id == user_id, Reflection.dismissed_at.is_(None))
        .order_by(Reflection.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    reflections = result.scalars().all()
    
    return ReflectionListResponse(
        reflections=[
            ReflectionResponse(
                id=r.id,
                content=r.content,
                metadata=ReflectionMetadata(
                    entries_analyzed=len(json.loads(r.entry_ids_json)),
                    date_range=f"{r.date_range_start} to {r.date_range_end}",
                    concepts=[],
                    confidence="high" if r.confidence_score > 0.7 else "moderate" if r.confidence_score > 0.5 else "low",
                    confidence_score=r.confidence_score,
                    model_version="v1.0.0",
                ),
                created_at=r.created_at,
                disclaimer=DISCLAIMER,
            )
            for r in reflections
        ],
        total=total,
    )


@router.post("/{reflection_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss_reflection(
    reflection_id: str,
    current_user: CurrentUser,
    db: DbSession,
):
    """Dismiss a reflection so it no longer appears."""
    user_id = current_user.user_id
    
    result = await db.execute(
        select(Reflection).where(
            Reflection.id == reflection_id,
            Reflection.user_id == user_id,
        )
    )
    reflection = result.scalar_one_or_none()
    
    if not reflection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reflection not found",
        )
    
    reflection.dismissed_at = datetime.now(timezone.utc)
    await db.commit()

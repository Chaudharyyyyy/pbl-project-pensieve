"""
Simplified Concepts Routes for SQLite
"""

import json

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func

from app.api.dependencies import DbSession
from app.api.schemas import ConceptListResponse, ConceptResponse
from app.models.database import Concept

router = APIRouter(prefix="/concepts", tags=["Concepts"])


@router.get("", response_model=ConceptListResponse)
async def list_concepts(
    db: DbSession,
    category: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List available concepts."""
    query = select(Concept)
    
    if category:
        query = query.where(Concept.category == category)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            Concept.name.ilike(search_pattern) | 
            Concept.description.ilike(search_pattern)
        )
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    query = query.order_by(Concept.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    concepts = result.scalars().all()
    
    return ConceptListResponse(
        concepts=[
            ConceptResponse(
                id=c.id,
                name=c.name,
                category=c.category,
                subcategory=c.subcategory,
                description=c.description,
                source_citation=c.source_citation,
                source_year=c.source_year,
                tags=json.loads(c.tags_json) if c.tags_json else [],
            )
            for c in concepts
        ],
        total=total,
    )


@router.get("/{concept_id}", response_model=ConceptResponse)
async def get_concept(
    concept_id: str,
    db: DbSession,
):
    """Get a specific concept."""
    result = await db.execute(select(Concept).where(Concept.id == concept_id))
    concept = result.scalar_one_or_none()
    
    if not concept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found")
    
    return ConceptResponse(
        id=concept.id,
        name=concept.name,
        category=concept.category,
        subcategory=concept.subcategory,
        description=concept.description,
        source_citation=concept.source_citation,
        source_year=concept.source_year,
        tags=json.loads(concept.tags_json) if concept.tags_json else [],
    )

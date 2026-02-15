"""
Simplified Schemas for SQLite

Updated schemas without UUID types for SQLite compatibility.
"""

from datetime import date, datetime
from typing import Optional, Any

from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================
# Authentication Schemas
# ============================================

class UserCreate(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Authentication token response."""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class UserResponse(BaseModel):
    """User profile response."""
    id: str
    email: str
    created_at: datetime


# ============================================
# Entry Schemas
# ============================================

class EntryCreate(BaseModel):
    """Create journal entry request."""
    content: str = Field(min_length=1, max_length=50000)
    entry_date: Optional[date] = None


class EntryUpdate(BaseModel):
    """Update journal entry request."""
    content: str = Field(min_length=1, max_length=50000)


class EntryResponse(BaseModel):
    """Journal entry response."""
    id: str
    content: str
    entry_date: date
    word_count: Optional[int]
    created_at: datetime
    updated_at: datetime


class EntryListResponse(BaseModel):
    """Paginated entry list response."""
    entries: list[EntryResponse]
    total: int
    page: int
    page_size: int


class AutosaveRequest(BaseModel):
    """Autosave draft request."""
    content: str
    entry_id: Optional[str] = None


class AutosaveResponse(BaseModel):
    """Autosave response."""
    entry_id: str
    saved_at: datetime
    word_count: int


# ============================================
# Reflection Schemas
# ============================================

class ConceptReferenceResponse(BaseModel):
    """Concept referenced in reflection."""
    id: str
    name: str
    description: str
    source: str
    relevance_score: float


class ReflectionMetadata(BaseModel):
    """Reflection metadata."""
    entries_analyzed: int
    date_range: str
    concepts: list[ConceptReferenceResponse]
    confidence: str
    confidence_score: float
    model_version: str


class ReflectionResponse(BaseModel):
    """Reflection response."""
    id: str
    content: str
    metadata: ReflectionMetadata
    created_at: datetime
    disclaimer: str


class ReflectionListResponse(BaseModel):
    """List of reflections."""
    reflections: list[ReflectionResponse]
    total: int


# ============================================
# Concept Schemas
# ============================================

class ConceptResponse(BaseModel):
    """Concept detail response."""
    id: str
    name: str
    category: str
    subcategory: Optional[str]
    description: str
    source_citation: str
    source_year: Optional[int]
    tags: list[str]


class ConceptListResponse(BaseModel):
    """List of concepts."""
    concepts: list[ConceptResponse]
    total: int


# ============================================
# Health Schemas
# ============================================

class HealthResponse(BaseModel):
    """API health check response."""
    status: str
    version: str
    environment: str

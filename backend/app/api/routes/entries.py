"""
Simplified API Routes for SQLite

Updated routes without PostgreSQL-specific features.
"""

from datetime import date, datetime, timezone
from typing import Optional
import json

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func

from app.api.dependencies import CurrentUser, DbSession, Encryption
from app.api.schemas import (
    AutosaveRequest,
    AutosaveResponse,
    EntryCreate,
    EntryListResponse,
    EntryResponse,
    EntryUpdate,
)
from app.models.database import Entry, User, AuditLog

router = APIRouter(prefix="/entries", tags=["Journal Entries"])


@router.post("", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    request: EntryCreate,
    current_user: CurrentUser,
    db: DbSession,
    encryption: Encryption,
):
    """Create a new encrypted journal entry."""
    user_id = current_user.user_id
    
    # Get user's encryption salt
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    
    # Derive key and encrypt
    key = encryption.derive_key("temp_session_key", user.encryption_key_salt)
    ciphertext, iv, auth_tag = encryption.encrypt_for_storage(request.content, key)
    
    # Count words
    word_count = len(request.content.split())
    
    # Create entry
    entry = Entry(
        user_id=user_id,
        encrypted_content=ciphertext,
        encryption_iv=iv,
        auth_tag=auth_tag,
        entry_date=request.entry_date or date.today(),
        word_count=word_count,
    )
    db.add(entry)
    
    # Audit log
    audit = AuditLog(
        user_id=user_id,
        action="entry_created",
        entity_type="entry",
        entity_id=entry.id,
        metadata_json=json.dumps({"word_count": word_count}),
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(entry)
    
    return EntryResponse(
        id=entry.id,
        content=request.content,
        entry_date=entry.entry_date,
        word_count=entry.word_count,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@router.get("", response_model=EntryListResponse)
async def list_entries(
    current_user: CurrentUser,
    db: DbSession,
    encryption: Encryption,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List user's journal entries (decrypted)."""
    user_id = current_user.user_id
    
    # Get user's encryption key
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    key = encryption.derive_key("temp_session_key", user.encryption_key_salt)
    
    # Query entries
    query = select(Entry).where(Entry.user_id == user_id).order_by(Entry.entry_date.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(Entry).where(Entry.user_id == user_id)
    total = (await db.execute(count_query)).scalar()
    
    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    entries = result.scalars().all()
    
    # Decrypt entries
    decrypted_entries = []
    for entry in entries:
        try:
            content = encryption.decrypt_from_storage(
                entry.encrypted_content,
                entry.encryption_iv,
                entry.auth_tag,
                key,
            )
            decrypted_entries.append(EntryResponse(
                id=entry.id,
                content=content,
                entry_date=entry.entry_date,
                word_count=entry.word_count,
                created_at=entry.created_at,
                updated_at=entry.updated_at,
            ))
        except Exception:
            continue
    
    return EntryListResponse(
        entries=decrypted_entries,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{entry_id}", response_model=EntryResponse)
async def get_entry(
    entry_id: str,
    current_user: CurrentUser,
    db: DbSession,
    encryption: Encryption,
):
    """Get a single entry by ID."""
    user_id = current_user.user_id
    
    result = await db.execute(
        select(Entry).where(Entry.id == entry_id, Entry.user_id == user_id)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    
    # Get encryption key
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()
    key = encryption.derive_key("temp_session_key", user.encryption_key_salt)
    
    # Decrypt
    content = encryption.decrypt_from_storage(
        entry.encrypted_content,
        entry.encryption_iv,
        entry.auth_tag,
        key,
    )
    
    return EntryResponse(
        id=entry.id,
        content=content,
        entry_date=entry.entry_date,
        word_count=entry.word_count,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: str,
    current_user: CurrentUser,
    db: DbSession,
):
    """Delete an entry."""
    user_id = current_user.user_id
    
    result = await db.execute(
        select(Entry).where(Entry.id == entry_id, Entry.user_id == user_id)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    
    await db.delete(entry)
    await db.commit()


@router.post("/autosave", response_model=AutosaveResponse)
async def autosave_entry(
    request: AutosaveRequest,
    current_user: CurrentUser,
    db: DbSession,
    encryption: Encryption,
):
    """Autosave endpoint for real-time saving."""
    user_id = current_user.user_id
    
    # Get encryption key
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()
    key = encryption.derive_key("temp_session_key", user.encryption_key_salt)
    
    # Encrypt content
    ciphertext, iv, auth_tag = encryption.encrypt_for_storage(request.content, key)
    word_count = len(request.content.split())
    
    if request.entry_id:
        # Update existing
        result = await db.execute(
            select(Entry).where(Entry.id == str(request.entry_id), Entry.user_id == user_id)
        )
        entry = result.scalar_one_or_none()
        
        if entry:
            entry.encrypted_content = ciphertext
            entry.encryption_iv = iv
            entry.auth_tag = auth_tag
            entry.word_count = word_count
        else:
            entry = Entry(
                user_id=user_id,
                encrypted_content=ciphertext,
                encryption_iv=iv,
                auth_tag=auth_tag,
                entry_date=date.today(),
                word_count=word_count,
            )
            db.add(entry)
    else:
        entry = Entry(
            user_id=user_id,
            encrypted_content=ciphertext,
            encryption_iv=iv,
            auth_tag=auth_tag,
            entry_date=date.today(),
            word_count=word_count,
        )
        db.add(entry)
    
    await db.commit()
    await db.refresh(entry)
    
    return AutosaveResponse(
        entry_id=entry.id,
        saved_at=datetime.now(timezone.utc),
        word_count=word_count,
    )

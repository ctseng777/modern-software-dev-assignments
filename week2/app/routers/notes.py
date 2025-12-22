"""
Notes router with well-defined API contracts.

This module handles all endpoints related to note creation and retrieval.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from .. import db
from ..schemas import NoteCreate, NoteResponse


router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteResponse, status_code=201)
def create_note(request: NoteCreate) -> NoteResponse:
    """
    Create a new note.
    
    Args:
        request: NoteCreate containing note content
        
    Returns:
        NoteResponse with created note data
        
    Raises:
        HTTPException: If note creation fails
    """
    try:
        note_id = db.insert_note(request.content)
        note = db.get_note(note_id)
        if note is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve created note"
            )
        return NoteResponse(
            id=note["id"],
            content=note["content"],
            created_at=note["created_at"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create note: {str(e)}"
        )


@router.get("", response_model=List[NoteResponse])
def list_all_notes() -> List[NoteResponse]:
    """
    List all notes.
    
    Returns:
        List of NoteResponse objects
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        rows = db.list_notes()
        return [
            NoteResponse(
                id=row["id"],
                content=row["content"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list notes: {str(e)}"
        )


@router.get("/{note_id}", response_model=NoteResponse)
def get_single_note(note_id: int) -> NoteResponse:
    """
    Get a single note by ID.
    
    Args:
        note_id: ID of the note to retrieve
        
    Returns:
        NoteResponse with note data
        
    Raises:
        HTTPException: If note not found
    """
    row = db.get_note(note_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteResponse(
        id=row["id"],
        content=row["content"],
        created_at=row["created_at"],
    )



"""
Action items router with well-defined API contracts.

This module handles all endpoints related to action item extraction and management.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from .. import db
from ..schemas import (
    ExtractRequest,
    ExtractResponse,
    ActionItemResponse,
    MarkDoneRequest,
    MarkDoneResponse,
)
from ..services.extract import extract_action_items


router = APIRouter(prefix="/action-items", tags=["action-items"])


@router.post("/extract", response_model=ExtractResponse)
def extract(request: ExtractRequest) -> ExtractResponse:
    """
    Extract action items from text using heuristic-based extraction.
    
    Args:
        request: ExtractRequest containing text and save_note flag
        
    Returns:
        ExtractResponse with extracted action items and optional note_id
        
    Raises:
        HTTPException: If extraction fails or database operation fails
    """
    try:
        note_id: Optional[int] = None
        if request.save_note:
            note_id = db.insert_note(request.text)

        items = extract_action_items(request.text)
        ids = db.insert_action_items(items, note_id=note_id)
        
        action_items = [
            ActionItemResponse(
                id=item_id,
                note_id=note_id,
                text=text,
                done=False,
                created_at="",  # Will be set from DB if needed
            )
            for item_id, text in zip(ids, items)
        ]
        
        return ExtractResponse(note_id=note_id, items=action_items)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract action items: {str(e)}"
        )


@router.post("/extract-llm", response_model=ExtractResponse)
def extract_llm(request: ExtractRequest) -> ExtractResponse:
    """
    Extract action items from text using LLM-powered extraction via RunPod API.
    
    Args:
        request: ExtractRequest containing text and save_note flag
        
    Returns:
        ExtractResponse with extracted action items and optional note_id
        
    Raises:
        HTTPException: If LLM extraction fails or database operation fails
    """
    try:
        from ..services.extract import extract_action_items_llm
        
        note_id: Optional[int] = None
        if request.save_note:
            note_id = db.insert_note(request.text)

        items = extract_action_items_llm(request.text)
        ids = db.insert_action_items(items, note_id=note_id)
        
        action_items = [
            ActionItemResponse(
                id=item_id,
                note_id=note_id,
                text=text,
                done=False,
                created_at="",  # Will be set from DB if needed
            )
            for item_id, text in zip(ids, items)
        ]
        
        return ExtractResponse(note_id=note_id, items=action_items)
    except ValueError as e:
        # Handle missing API key or configuration errors
        raise HTTPException(
            status_code=503,
            detail=f"LLM service unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract action items with LLM: {str(e)}"
        )


@router.get("", response_model=List[ActionItemResponse])
def list_all(
    note_id: Optional[int] = Query(None, description="Filter by note ID")
) -> List[ActionItemResponse]:
    """
    List all action items, optionally filtered by note_id.
    
    Args:
        note_id: Optional note ID to filter action items
        
    Returns:
        List of ActionItemResponse objects
    """
    try:
        rows = db.list_action_items(note_id=note_id)
        return [
            ActionItemResponse(
                id=r["id"],
                note_id=r["note_id"],
                text=r["text"],
                done=bool(r["done"]),
                created_at=r["created_at"],
            )
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list action items: {str(e)}"
        )


@router.post("/{action_item_id}/done", response_model=MarkDoneResponse)
def mark_done(action_item_id: int, request: MarkDoneRequest) -> MarkDoneResponse:
    """
    Mark an action item as done or not done.
    
    Args:
        action_item_id: ID of the action item to update
        request: MarkDoneRequest with done status
        
    Returns:
        MarkDoneResponse with updated status
        
    Raises:
        HTTPException: If action item not found or update fails
    """
    try:
        # Verify action item exists by checking if any items match this ID
        items = db.list_action_items()
        item_exists = any(item["id"] == action_item_id for item in items)
        if not item_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Action item with id {action_item_id} not found"
            )
        
        db.mark_action_item_done(action_item_id, request.done)
        return MarkDoneResponse(id=action_item_id, done=request.done)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update action item: {str(e)}"
        )



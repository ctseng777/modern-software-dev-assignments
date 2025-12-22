"""
Pydantic schemas for API request/response models.

This module defines the data structures used for API contracts,
ensuring type safety and validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NoteBase(BaseModel):
    """Base schema for note data."""
    content: str = Field(..., min_length=1, description="The note content")


class NoteCreate(NoteBase):
    """Schema for creating a new note."""
    pass


class NoteResponse(NoteBase):
    """Schema for note response."""
    id: int = Field(..., description="Unique note identifier")
    created_at: str = Field(..., description="ISO timestamp of creation")

    class Config:
        from_attributes = True


class ActionItemBase(BaseModel):
    """Base schema for action item data."""
    text: str = Field(..., min_length=1, description="The action item text")


class ActionItemResponse(BaseModel):
    """Schema for action item response."""
    id: int = Field(..., description="Unique action item identifier")
    note_id: Optional[int] = Field(None, description="Associated note ID if any")
    text: str = Field(..., description="The action item text")
    done: bool = Field(False, description="Whether the action item is completed")
    created_at: str = Field(..., description="ISO timestamp of creation")

    class Config:
        from_attributes = True


class ExtractRequest(BaseModel):
    """Schema for action item extraction request."""
    text: str = Field(..., min_length=1, description="Text to extract action items from")
    save_note: bool = Field(False, description="Whether to save the text as a note")


class ExtractResponse(BaseModel):
    """Schema for action item extraction response."""
    note_id: Optional[int] = Field(None, description="ID of created note if save_note was True")
    items: list[ActionItemResponse] = Field(..., description="List of extracted action items")


class MarkDoneRequest(BaseModel):
    """Schema for marking an action item as done."""
    done: bool = Field(True, description="Whether to mark the item as done")


class MarkDoneResponse(BaseModel):
    """Schema for marking an action item as done response."""
    id: int = Field(..., description="Action item ID")
    done: bool = Field(..., description="New done status")


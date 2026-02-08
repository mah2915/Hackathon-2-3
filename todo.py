"""
Todo Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class TodoCreate(BaseModel):
    """Schema for creating a new todo."""
    title: str = Field(..., min_length=1, max_length=255, description="Todo title")
    description: Optional[str] = Field(None, description="Todo description (optional)")


class TodoUpdate(BaseModel):
    """Schema for updating an existing todo."""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Todo title")
    description: Optional[str] = Field(None, description="Todo description")


class TodoResponse(BaseModel):
    """Schema for todo response."""
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    email: EmailStr
    is_active: bool = True


class UserResponse(BaseModel):
    username: str
    email: EmailStr
    is_active: bool


class ExtractUserRequest(BaseModel):
    text: str = Field(min_length=1, description="Freeform text that contains user info")


class ExtractedUser(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr


class DocumentStatus(str, Enum):
    """Document processing status."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class Document(BaseModel):
    """Document model with metadata."""

    id: str
    filename: str
    file_path: str
    mime_type: str
    size: int
    status: DocumentStatus
    uploaded_at: datetime
    processed_at: datetime | None = None
    text_content: str | None = None
    error_message: str | None = None


class DocumentUploadResponse(BaseModel):
    """Response for document upload."""

    document: Document
    message: str = "Document uploaded successfully"


class DocumentListResponse(BaseModel):
    """Response for listing documents."""

    documents: list[Document]
    total: int

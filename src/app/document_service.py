"""Document management service for upload, processing, and storage."""

import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path

import pypdf
from fastapi import HTTPException, UploadFile

from .rag_service import RAGService
from .schemas import Document, DocumentStatus


class DocumentService:
    """Service for managing document uploads and processing."""

    ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}
    ALLOWED_MIME_TYPES = {"text/plain", "text/markdown", "text/x-markdown", "application/pdf"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self, upload_dir: str = "uploads", rag_service: RAGService | None = None):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.rag_service = rag_service
        # In-memory storage for demo - replace with DB in production
        self.documents: dict[str, Document] = {}

    async def validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file type and size."""
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {self.MAX_FILE_SIZE // 1024 // 1024}MB",
            )

        # Check file extension
        if file.filename:
            ext = Path(file.filename).suffix.lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=415,
                    detail=f"Unsupported file type. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}",
                )

        # Check MIME type using mimetypes (simpler than python-magic)
        guessed_type, _ = mimetypes.guess_type(file.filename)

        # Handle cases where mimetypes doesn't recognize .md files
        if file.filename and file.filename.endswith(".md") and guessed_type is None:
            guessed_type = "text/markdown"

        if guessed_type not in self.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=415, detail=f"Invalid file type. Detected: {guessed_type}"
            )

    async def extract_text(self, file_path: Path, mime_type: str) -> str:
        """Extract text content from uploaded file."""
        if mime_type == "application/pdf":
            return await self._extract_pdf_text(file_path)
        else:
            # Text/markdown files
            return file_path.read_text(encoding="utf-8")

    async def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        try:
            with open(file_path, "rb") as file:
                reader = pypdf.PdfReader(file)
                text_parts = []
                for page_num, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_parts.append(f"--- Page {page_num} ---\n{page_text}")
                return "\n\n".join(text_parts)
        except Exception as e:
            raise HTTPException(
                status_code=422, detail=f"Failed to extract text from PDF: {str(e)}"
            ) from e

    def generate_document_id(self, filename: str, content: bytes) -> str:
        """Generate unique document ID based on filename and content hash."""
        content_hash = hashlib.sha256(content).hexdigest()[:12]
        safe_filename = Path(filename).stem[:20]  # Truncate long names
        return f"{safe_filename}_{content_hash}"

    async def upload_document(self, file: UploadFile) -> Document:
        """Process uploaded document and create document record."""
        await self.validate_file(file)

        # Read file content
        content = await file.read()
        doc_id = self.generate_document_id(file.filename, content)

        # Check for duplicates
        if doc_id in self.documents:
            return self.documents[doc_id]

        # Save file to disk
        file_path = self.upload_dir / f"{doc_id}{Path(file.filename).suffix}"
        file_path.write_bytes(content)

        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(file.filename)
        # Handle .md files
        if file.filename and file.filename.endswith(".md") and mime_type is None:
            mime_type = "text/markdown"

        # Create document record
        document = Document(
            id=doc_id,
            filename=file.filename,
            file_path=str(file_path),
            mime_type=mime_type,
            size=len(content),
            status=DocumentStatus.UPLOADED,
            uploaded_at=datetime.utcnow(),
        )

        self.documents[doc_id] = document
        return document

    async def process_document(self, doc_id: str) -> Document:
        """Extract text and index document for RAG."""
        document = self.documents.get(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if document.status != DocumentStatus.UPLOADED:
            return document

        try:
            # Update status
            document.status = DocumentStatus.PROCESSING

            # Extract text
            text_content = await self.extract_text(Path(document.file_path), document.mime_type)
            document.text_content = text_content
            document.processed_at = datetime.utcnow()

            # Index for RAG if service available
            if self.rag_service:
                await self.rag_service.ingest_document(
                    doc_id,
                    text_content,
                    {
                        "filename": document.filename,
                        "mime_type": document.mime_type,
                        "uploaded_at": document.uploaded_at.isoformat(),
                        "size": document.size,
                    },
                )

            document.status = DocumentStatus.READY

        except Exception as e:
            document.status = DocumentStatus.ERROR
            document.error_message = str(e)
            msg = f"Failed to process document: {str(e)}"
            raise HTTPException(status_code=500, detail=msg) from e

        return document

    def get_document(self, doc_id: str) -> Document | None:
        """Get document by ID."""
        return self.documents.get(doc_id)

    def list_documents(self) -> list[Document]:
        """List all documents."""
        return list(self.documents.values())

    def delete_document(self, doc_id: str) -> bool:
        """Delete document and cleanup files."""
        document = self.documents.get(doc_id)
        if not document:
            return False

        # Remove file
        try:
            Path(document.file_path).unlink(missing_ok=True)
        except Exception:
            pass  # Continue even if file deletion fails

        # Remove from RAG if available
        if self.rag_service:
            try:
                self.rag_service.delete_document(doc_id)
            except Exception:
                pass

        # Remove from memory
        del self.documents[doc_id]
        return True

"""Document management routes for upload and processing."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from .dependencies import get_document_service
from .document_service import DocumentService
from .schemas import Document, DocumentListResponse, DocumentUploadResponse
from .tasks import process_document_task

router = APIRouter(prefix="/docs", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    background: bool = True,
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentUploadResponse:
    """Upload a document for processing."""
    try:
        # Upload and validate file
        document = await document_service.upload_document(file)

        if background:
            # Queue background processing
            task = process_document_task.delay(document.id)
            return DocumentUploadResponse(
                document=document,
                message=(
                    f"Document uploaded successfully. Processing queued with " f"task_id: {task.id}"
                ),
            )
        else:
            # Process immediately
            processed_doc = await document_service.process_document(document.id)
            return DocumentUploadResponse(
                document=processed_doc, message="Document uploaded and processed successfully"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    """List all uploaded documents."""
    documents = document_service.list_documents()
    return DocumentListResponse(documents=documents, total=len(documents))


@router.get("/{doc_id}", response_model=Document)
async def get_document(
    doc_id: str,
    document_service: DocumentService = Depends(get_document_service),
) -> Document:
    """Get document by ID."""
    document = document_service.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    document_service: DocumentService = Depends(get_document_service),
) -> JSONResponse:
    """Delete a document and its data."""
    success = document_service.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

    return JSONResponse(content={"message": "Document deleted successfully"}, status_code=200)


@router.post("/{doc_id}/reprocess")
async def reprocess_document(
    doc_id: str,
    background: bool = True,
    document_service: DocumentService = Depends(get_document_service),
) -> JSONResponse:
    """Reprocess a document."""
    document = document_service.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        if background:
            task = process_document_task.delay(doc_id)
            return JSONResponse(
                content={"message": "Document reprocessing queued", "task_id": task.id}
            )
        else:
            processed_doc = await document_service.process_document(doc_id)
            return JSONResponse(
                content={
                    "message": "Document reprocessed successfully",
                    "status": processed_doc.status,
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reprocessing failed: {str(e)}")

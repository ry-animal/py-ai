"""MongoDB adapter for document storage and retrieval."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)


class DocumentMetadata(BaseModel):
    """Document metadata schema."""

    title: str
    file_type: str
    file_size: int
    upload_date: datetime
    processing_status: str = "pending"  # pending, processing, completed, failed
    chunk_count: int = 0
    vector_status: str = "pending"  # pending, embedding, indexed, failed
    tags: list[str] = []
    user_id: str | None = None
    session_id: str | None = None


class StoredDocument(BaseModel):
    """Complete document model for MongoDB storage."""

    id: str  # document ID
    content: str
    metadata: DocumentMetadata
    chunks: list[dict] = []  # chunk metadata
    created_at: datetime
    updated_at: datetime


class MongoDBAdapter:
    """MongoDB adapter for document storage and management."""

    def __init__(self, connection_string: str = None):
        settings = get_settings()
        self.connection_string = connection_string or settings.mongodb_url
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None
        self.collection_name = "documents"

    async def connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client.py_ai_platform

            # Test connection
            await self.client.admin.command("ping")
            logger.info("Successfully connected to MongoDB")

            # Create indexes
            await self._create_indexes()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def _create_indexes(self) -> None:
        """Create necessary indexes for optimal performance."""
        collection = self.db[self.collection_name]

        # Create indexes
        indexes = [
            [("metadata.upload_date", -1)],  # Sort by upload date
            [("metadata.processing_status", 1)],  # Filter by status
            [("metadata.vector_status", 1)],  # Filter by vector status
            [("metadata.user_id", 1)],  # Filter by user
            [("metadata.session_id", 1)],  # Filter by session
            [("metadata.tags", 1)],  # Filter by tags
            [("metadata.file_type", 1)],  # Filter by file type
            [("content", "text")],  # Text search index
        ]

        for index in indexes:
            try:
                await collection.create_index(index)
            except Exception as e:
                logger.warning(f"Index creation failed: {e}")

    async def store_document(self, doc_id: str, content: str, metadata: DocumentMetadata) -> str:
        """Store a document in MongoDB."""
        if not self.db:
            await self.connect()

        collection = self.db[self.collection_name]

        document = StoredDocument(
            id=doc_id,
            content=content,
            metadata=metadata,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        try:
            await collection.insert_one(document.model_dump())
            logger.info(f"Stored document {doc_id} in MongoDB")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to store document {doc_id}: {e}")
            raise

    async def get_document(self, doc_id: str) -> StoredDocument | None:
        """Retrieve a document by ID."""
        if not self.db:
            await self.connect()

        collection = self.db[self.collection_name]

        try:
            doc_data = await collection.find_one({"id": doc_id})
            if doc_data:
                return StoredDocument(**doc_data)
            return None

        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            raise

    async def update_document_status(
        self,
        doc_id: str,
        processing_status: str = None,
        vector_status: str = None,
        chunk_count: int = None,
        chunks: list[dict] = None,
    ) -> bool:
        """Update document processing status."""
        if not self.db:
            await self.connect()

        collection = self.db[self.collection_name]

        update_data = {"updated_at": datetime.utcnow()}

        if processing_status:
            update_data["metadata.processing_status"] = processing_status
        if vector_status:
            update_data["metadata.vector_status"] = vector_status
        if chunk_count is not None:
            update_data["metadata.chunk_count"] = chunk_count
        if chunks is not None:
            update_data["chunks"] = chunks

        try:
            result = await collection.update_one({"id": doc_id}, {"$set": update_data})
            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            return False

    async def search_documents(
        self, query: str = None, filters: dict[str, Any] = None, limit: int = 100, skip: int = 0
    ) -> list[StoredDocument]:
        """Search documents with optional filters."""
        if not self.db:
            await self.connect()

        collection = self.db[self.collection_name]

        # Build MongoDB query
        mongo_query = {}

        # Text search
        if query:
            mongo_query["$text"] = {"$search": query}

        # Apply filters
        if filters:
            for key, value in filters.items():
                if key == "file_type":
                    mongo_query["metadata.file_type"] = value
                elif key == "processing_status":
                    mongo_query["metadata.processing_status"] = value
                elif key == "vector_status":
                    mongo_query["metadata.vector_status"] = value
                elif key == "user_id":
                    mongo_query["metadata.user_id"] = value
                elif key == "session_id":
                    mongo_query["metadata.session_id"] = value
                elif key == "tags":
                    mongo_query["metadata.tags"] = {
                        "$in": value if isinstance(value, list) else [value]
                    }
                elif key == "date_range" and ("start" in value or "end" in value):
                    date_query = {}
                    if "start" in value:
                        date_query["$gte"] = value["start"]
                    if "end" in value:
                        date_query["$lte"] = value["end"]
                    mongo_query["metadata.upload_date"] = date_query

        try:
            cursor = collection.find(mongo_query).skip(skip).limit(limit)

            # Sort by relevance if text search, otherwise by date
            if query:
                cursor = cursor.sort([("score", {"$meta": "textScore"})])
            else:
                cursor = cursor.sort([("metadata.upload_date", -1)])

            documents = []
            async for doc_data in cursor:
                documents.append(StoredDocument(**doc_data))

            return documents

        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []

    async def list_documents(
        self, user_id: str = None, session_id: str = None, limit: int = 50
    ) -> list[StoredDocument]:
        """List documents with optional user/session filtering."""
        filters = {}
        if user_id:
            filters["user_id"] = user_id
        if session_id:
            filters["session_id"] = session_id

        return await self.search_documents(filters=filters, limit=limit)

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from MongoDB."""
        if not self.db:
            await self.connect()

        collection = self.db[self.collection_name]

        try:
            result = await collection.delete_one({"id": doc_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted document {doc_id} from MongoDB")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False

    async def get_statistics(self) -> dict[str, Any]:
        """Get database statistics."""
        if not self.db:
            await self.connect()

        collection = self.db[self.collection_name]

        try:
            # Aggregate statistics
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_documents": {"$sum": 1},
                        "total_size": {"$sum": "$metadata.file_size"},
                        "avg_size": {"$avg": "$metadata.file_size"},
                        "status_counts": {"$push": "$metadata.processing_status"},
                        "file_types": {"$push": "$metadata.file_type"},
                    }
                }
            ]

            result = await collection.aggregate(pipeline).to_list(1)

            if result:
                stats = result[0]

                # Count statuses and file types
                from collections import Counter

                status_counts = Counter(stats.get("status_counts", []))
                file_type_counts = Counter(stats.get("file_types", []))

                return {
                    "total_documents": stats.get("total_documents", 0),
                    "total_size_bytes": stats.get("total_size", 0),
                    "average_size_bytes": stats.get("avg_size", 0),
                    "status_distribution": dict(status_counts),
                    "file_type_distribution": dict(file_type_counts),
                    "collection_name": self.collection_name,
                }

            return {
                "total_documents": 0,
                "total_size_bytes": 0,
                "average_size_bytes": 0,
                "status_distribution": {},
                "file_type_distribution": {},
                "collection_name": self.collection_name,
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


# Dependency injection
_mongodb_adapter: MongoDBAdapter | None = None


async def get_mongodb_adapter() -> MongoDBAdapter:
    """Get MongoDB adapter instance (dependency injection)."""
    global _mongodb_adapter

    if _mongodb_adapter is None:
        _mongodb_adapter = MongoDBAdapter()
        await _mongodb_adapter.connect()

    return _mongodb_adapter


async def close_mongodb_adapter() -> None:
    """Close MongoDB adapter connection."""
    global _mongodb_adapter

    if _mongodb_adapter:
        await _mongodb_adapter.disconnect()
        _mongodb_adapter = None

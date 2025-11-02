"""Multi-cloud vector database adapters."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class VectorDBType(str, Enum):
    """Supported vector database types."""

    VERTEX_AI = "vertex"
    SNOWFLAKE_CORTEX = "snowflake"
    MONGODB_VECTOR = "mongodb_vector"
    COCKROACHDB = "cockroach"
    CHROMADB = "chroma"  # fallback


class VectorSearchResult(BaseModel):
    """Vector search result model."""

    id: str
    content: str
    metadata: dict[str, Any]
    score: float
    distance: float | None = None


class VectorAdapter(ABC):
    """Abstract base class for vector database adapters."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector database connection."""
        pass

    @abstractmethod
    async def add_vectors(
        self, vectors: list[list[float]], metadatas: list[dict[str, Any]], ids: list[str]
    ) -> bool:
        """Add vectors to the database."""
        pass

    @abstractmethod
    async def similarity_search(
        self, query_vector: list[float], k: int = 4, filters: dict[str, Any] = None
    ) -> list[VectorSearchResult]:
        """Perform similarity search."""
        pass

    @abstractmethod
    async def delete_vectors(self, ids: list[str]) -> bool:
        """Delete vectors by IDs."""
        pass

    @abstractmethod
    async def get_collection_stats(self) -> dict[str, Any]:
        """Get collection statistics."""
        pass


class VertexAIAdapter(VectorAdapter):
    """Google Vertex AI Vector Search adapter."""

    def __init__(self, project_id: str, region: str, index_endpoint_id: str):
        self.project_id = project_id
        self.region = region
        self.index_endpoint_id = index_endpoint_id
        self.client = None

    async def initialize(self) -> None:
        """Initialize Vertex AI client."""
        try:
            from google.cloud import aiplatform

            aiplatform.init(project=self.project_id, location=self.region)
            self.client = aiplatform.MatchingEngineIndexEndpoint(
                index_endpoint_name=self.index_endpoint_id
            )
            logger.info("Initialized Vertex AI vector adapter")

        except ImportError:
            logger.error("google-cloud-aiplatform not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise

    async def add_vectors(
        self, vectors: list[list[float]], metadatas: list[dict[str, Any]], ids: list[str]
    ) -> bool:
        """Add vectors to Vertex AI index."""
        try:
            # Convert to Vertex AI format
            datapoints = []
            for _i, (vector, metadata, vector_id) in enumerate(
                zip(vectors, metadatas, ids, strict=False)
            ):
                datapoints.append(
                    {
                        "datapoint_id": vector_id,
                        "feature_vector": vector,
                        "restricts": [
                            {"namespace": k, "allow_list": [str(v)]} for k, v in metadata.items()
                        ],
                    }
                )

            # Batch upsert
            await self.client.upsert_datapoints(datapoints=datapoints)
            logger.info(f"Added {len(vectors)} vectors to Vertex AI")
            return True

        except Exception as e:
            logger.error(f"Failed to add vectors to Vertex AI: {e}")
            return False

    async def similarity_search(
        self, query_vector: list[float], k: int = 4, filters: dict[str, Any] = None
    ) -> list[VectorSearchResult]:
        """Search similar vectors in Vertex AI."""
        try:
            # Convert filters to Vertex AI format
            restricts = []
            if filters:
                for key, value in filters.items():
                    restricts.append(
                        {
                            "namespace": key,
                            "allow_list": [str(value)]
                            if not isinstance(value, list)
                            else [str(v) for v in value],
                        }
                    )

            response = await self.client.find_neighbors(
                deployed_index_id=self.index_endpoint_id,
                queries=[
                    {"feature_vector": query_vector, "neighbor_count": k, "restricts": restricts}
                ],
            )

            results = []
            for neighbor in response[0]:
                results.append(
                    VectorSearchResult(
                        id=neighbor.datapoint_id,
                        content=neighbor.restricts.get("content", [""])[0],
                        metadata={r.namespace: r.allow_list[0] for r in neighbor.restricts},
                        score=1 - neighbor.distance,  # Convert distance to similarity
                        distance=neighbor.distance,
                    )
                )

            return results

        except Exception as e:
            logger.error(f"Failed to search Vertex AI: {e}")
            return []

    async def delete_vectors(self, ids: list[str]) -> bool:
        """Delete vectors from Vertex AI."""
        try:
            await self.client.remove_datapoints(datapoint_ids=ids)
            logger.info(f"Deleted {len(ids)} vectors from Vertex AI")
            return True

        except Exception as e:
            logger.error(f"Failed to delete vectors from Vertex AI: {e}")
            return False

    async def get_collection_stats(self) -> dict[str, Any]:
        """Get Vertex AI index statistics."""
        try:
            # Vertex AI doesn't provide direct stats API
            # This would require custom implementation
            return {
                "provider": "vertex_ai",
                "project_id": self.project_id,
                "region": self.region,
                "index_endpoint_id": self.index_endpoint_id,
                "status": "active",
            }

        except Exception as e:
            logger.error(f"Failed to get Vertex AI stats: {e}")
            return {}


class SnowflakeAdapter(VectorAdapter):
    """Snowflake Cortex vector adapter."""

    def __init__(self, connection_params: dict[str, str]):
        self.connection_params = connection_params
        self.connection = None

    async def initialize(self) -> None:
        """Initialize Snowflake connection."""
        try:
            import snowflake.connector

            self.connection = snowflake.connector.connect(**self.connection_params)
            logger.info("Initialized Snowflake vector adapter")

        except ImportError:
            logger.error("snowflake-connector-python not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Snowflake: {e}")
            raise

    async def add_vectors(
        self, vectors: list[list[float]], metadatas: list[dict[str, Any]], ids: list[str]
    ) -> bool:
        """Add vectors to Snowflake table."""
        try:
            cursor = self.connection.cursor()

            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vector_embeddings (
                    id VARCHAR(255) PRIMARY KEY,
                    vector ARRAY,
                    metadata VARIANT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
                )
            """)

            # Insert vectors
            for vector, metadata, vector_id in zip(vectors, metadatas, ids, strict=False):
                cursor.execute(
                    """
                    MERGE INTO vector_embeddings t
                    USING (SELECT %s as id, %s as vector, %s as metadata) s
                    ON t.id = s.id
                    WHEN MATCHED THEN UPDATE SET vector = s.vector, metadata = s.metadata
                    WHEN NOT MATCHED THEN INSERT (id, vector, metadata) 
                        VALUES (s.id, s.vector, s.metadata)
                """,
                    (vector_id, vector, metadata),
                )

            logger.info(f"Added {len(vectors)} vectors to Snowflake")
            return True

        except Exception as e:
            logger.error(f"Failed to add vectors to Snowflake: {e}")
            return False

    async def similarity_search(
        self, query_vector: list[float], k: int = 4, filters: dict[str, Any] = None
    ) -> list[VectorSearchResult]:
        """Search similar vectors in Snowflake using Cortex."""
        try:
            cursor = self.connection.cursor()

            # Build filter conditions
            filter_conditions = ""
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        conditions.append(
                            f"metadata:{key}::STRING IN ({','.join(repr(v) for v in value)})"
                        )
                    else:
                        conditions.append(f"metadata:{key}::STRING = {repr(value)}")
                if conditions:
                    filter_conditions = "WHERE " + " AND ".join(conditions)

            # Use Snowflake Cortex vector similarity
            query = f"""
                SELECT 
                    id,
                    metadata:content::STRING as content,
                    metadata,
                    VECTOR_COSINE_SIMILARITY(vector, %s) as score
                FROM vector_embeddings
                {filter_conditions}
                ORDER BY score DESC
                LIMIT %s
            """

            cursor.execute(query, (query_vector, k))
            results = cursor.fetchall()

            return [
                VectorSearchResult(
                    id=row[0], content=row[1] or "", metadata=row[2] or {}, score=float(row[3])
                )
                for row in results
            ]

        except Exception as e:
            logger.error(f"Failed to search Snowflake: {e}")
            return []

    async def delete_vectors(self, ids: list[str]) -> bool:
        """Delete vectors from Snowflake."""
        try:
            cursor = self.connection.cursor()

            placeholders = ",".join(["%s"] * len(ids))
            cursor.execute(f"DELETE FROM vector_embeddings WHERE id IN ({placeholders})", ids)

            logger.info(f"Deleted {len(ids)} vectors from Snowflake")
            return True

        except Exception as e:
            logger.error(f"Failed to delete vectors from Snowflake: {e}")
            return False

    async def get_collection_stats(self) -> dict[str, Any]:
        """Get Snowflake table statistics."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM vector_embeddings")
            count = cursor.fetchone()[0]

            return {"provider": "snowflake_cortex", "total_vectors": count, "status": "active"}

        except Exception as e:
            logger.error(f"Failed to get Snowflake stats: {e}")
            return {}


class CockroachDBAdapter(VectorAdapter):
    """CockroachDB vector adapter - Bonus points! 🎯"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None

    async def initialize(self) -> None:
        """Initialize CockroachDB connection."""
        try:
            import asyncpg

            self.pool = await asyncpg.create_pool(self.connection_string)

            # Create vector extension and table
            async with self.pool.acquire() as conn:
                # Enable vector extension (if available)
                try:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                except Exception:
                    logger.warning("Vector extension not available, using array storage")

                # Create table with vector support
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS vector_embeddings (
                        id VARCHAR(255) PRIMARY KEY,
                        vector FLOAT8[],
                        metadata JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)

                # Create index for vector similarity (if extension available)
                try:
                    await conn.execute("""
                        CREATE INDEX IF NOT EXISTS vector_embeddings_vector_idx 
                        ON vector_embeddings USING ivfflat (vector vector_cosine_ops) 
                        WITH (lists = 100)
                    """)
                except Exception:
                    # Fallback: regular index on array
                    await conn.execute("""
                        CREATE INDEX IF NOT EXISTS vector_embeddings_vector_gin_idx 
                        ON vector_embeddings USING gin (vector)
                    """)

            logger.info("Initialized CockroachDB vector adapter")

        except ImportError:
            logger.error("asyncpg not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize CockroachDB: {e}")
            raise

    async def add_vectors(
        self, vectors: list[list[float]], metadatas: list[dict[str, Any]], ids: list[str]
    ) -> bool:
        """Add vectors to CockroachDB."""
        try:
            async with self.pool.acquire() as conn:
                # Batch insert with UPSERT
                for vector, metadata, vector_id in zip(vectors, metadatas, ids, strict=False):
                    await conn.execute(
                        """
                        UPSERT INTO vector_embeddings (id, vector, metadata)
                        VALUES ($1, $2, $3)
                    """,
                        vector_id,
                        vector,
                        metadata,
                    )

            logger.info(f"Added {len(vectors)} vectors to CockroachDB")
            return True

        except Exception as e:
            logger.error(f"Failed to add vectors to CockroachDB: {e}")
            return False

    async def similarity_search(
        self, query_vector: list[float], k: int = 4, filters: dict[str, Any] = None
    ) -> list[VectorSearchResult]:
        """Search similar vectors in CockroachDB."""
        try:
            async with self.pool.acquire() as conn:
                # Build filter conditions
                filter_conditions = ""
                params = [query_vector, k]

                if filters:
                    conditions = []
                    for key, value in filters.items():
                        if isinstance(value, list):
                            # Use JSONB array containment
                            conditions.append(f"metadata->'{key}' ?| ARRAY{value}")
                        else:
                            conditions.append(f"metadata->>'{key}' = ${len(params) + 1}")
                            params.append(str(value))

                    if conditions:
                        filter_conditions = "WHERE " + " AND ".join(conditions)

                # Use vector similarity (or fallback to array operations)
                try:
                    # Try with vector extension
                    query = f"""
                        SELECT 
                            id,
                            metadata->>'content' as content,
                            metadata,
                            1 - (vector <-> $1::vector) as score,
                            vector <-> $1::vector as distance
                        FROM vector_embeddings
                        {filter_conditions}
                        ORDER BY vector <-> $1::vector
                        LIMIT $2
                    """
                except:
                    # Fallback to manual cosine similarity
                    query = f"""
                        SELECT 
                            id,
                            metadata->>'content' as content,
                            metadata,
                            -- Manual cosine similarity calculation
                            (
                                SELECT SUM(a * b) / (
                                    SQRT(SUM(a * a)) * SQRT(SUM(b * b))
                                )
                                FROM (
                                    SELECT 
                                        vector[i] as a,
                                        ($1::FLOAT8[])[i] as b
                                    FROM generate_subscripts(vector, 1) i
                                ) sub
                            ) as score
                        FROM vector_embeddings
                        {filter_conditions}
                        ORDER BY score DESC
                        LIMIT $2
                    """

                results = await conn.fetch(query, *params)

                return [
                    VectorSearchResult(
                        id=row["id"],
                        content=row["content"] or "",
                        metadata=row["metadata"] or {},
                        score=float(row["score"] or 0),
                        distance=row.get("distance"),
                    )
                    for row in results
                ]

        except Exception as e:
            logger.error(f"Failed to search CockroachDB: {e}")
            return []

    async def delete_vectors(self, ids: list[str]) -> bool:
        """Delete vectors from CockroachDB."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    DELETE FROM vector_embeddings 
                    WHERE id = ANY($1::VARCHAR[])
                """,
                    ids,
                )

            logger.info(f"Deleted {len(ids)} vectors from CockroachDB")
            return True

        except Exception as e:
            logger.error(f"Failed to delete vectors from CockroachDB: {e}")
            return False

    async def get_collection_stats(self) -> dict[str, Any]:
        """Get CockroachDB statistics."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_vectors,
                        AVG(array_length(vector, 1)) as avg_dimensions,
                        MIN(created_at) as first_added,
                        MAX(created_at) as last_added
                    FROM vector_embeddings
                """)

                return {
                    "provider": "cockroachdb",
                    "total_vectors": result["total_vectors"],
                    "avg_dimensions": result["avg_dimensions"],
                    "first_added": result["first_added"],
                    "last_added": result["last_added"],
                    "status": "active",
                }

        except Exception as e:
            logger.error(f"Failed to get CockroachDB stats: {e}")
            return {}


class VectorAdapterFactory:
    """Factory for creating vector database adapters."""

    @staticmethod
    def create_adapter(db_type: VectorDBType, config: dict[str, Any]) -> VectorAdapter:
        """Create appropriate vector adapter based on type."""

        if db_type == VectorDBType.VERTEX_AI:
            return VertexAIAdapter(
                project_id=config["project_id"],
                region=config["region"],
                index_endpoint_id=config["index_endpoint_id"],
            )

        elif db_type == VectorDBType.SNOWFLAKE_CORTEX:
            return SnowflakeAdapter(config["connection_params"])

        elif db_type == VectorDBType.COCKROACHDB:
            return CockroachDBAdapter(config["connection_string"])

        elif db_type == VectorDBType.MONGODB_VECTOR:
            # MongoDB vector search implementation would go here
            raise NotImplementedError("MongoDB vector adapter not yet implemented")

        elif db_type == VectorDBType.CHROMADB:
            # Fallback to existing ChromaDB implementation
            raise NotImplementedError("ChromaDB adapter - use existing implementation")

        else:
            raise ValueError(f"Unsupported vector database type: {db_type}")


# Dependency injection
_vector_adapter: VectorAdapter | None = None


async def get_vector_adapter() -> VectorAdapter:
    """Get vector adapter instance (dependency injection)."""
    global _vector_adapter

    if _vector_adapter is None:
        from app.config import get_settings

        settings = get_settings()

        # Configuration based on environment
        if settings.vector_db_type == "vertex":
            config = {
                "project_id": settings.gcp_project_id,
                "region": settings.gcp_region,
                "index_endpoint_id": settings.vertex_index_endpoint_id,
            }
        elif settings.vector_db_type == "snowflake":
            config = {
                "connection_params": {
                    "account": settings.snowflake_account,
                    "user": settings.snowflake_user,
                    "password": settings.snowflake_password,
                    "database": settings.snowflake_database,
                    "schema": settings.snowflake_schema,
                }
            }
        elif settings.vector_db_type == "cockroach":
            config = {"connection_string": settings.cockroach_connection_string}
        else:
            # Fallback to ChromaDB
            from app.rag_service import RAGService

            return RAGService().vector_store  # Use existing implementation

        _vector_adapter = VectorAdapterFactory.create_adapter(
            VectorDBType(settings.vector_db_type), config
        )
        await _vector_adapter.initialize()

    return _vector_adapter

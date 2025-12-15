"""
MongoDB Repository Implementation

Concrete implementation of DatabaseRepository for MongoDB databases.
Follows SOLID principles with proper separation of concerns.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import motor.motor_asyncio
from pymongo import ASCENDING, DESCENDING
from bson import ObjectId
import json

from domain.repositories import DatabaseRepository
from domain.value_objects import DatabaseType, QueryResult


logger = logging.getLogger(__name__)


class MongoDBRepository(DatabaseRepository):
    """
    MongoDB repository implementation.

    This class implements the DatabaseRepository interface for MongoDB databases,
    providing async operations, connection pooling, and proper error handling.
    """

    def __init__(self,
                 connection_string: str = "",
                 database_name: str = "",
                 max_pool_size: int = 100,
                 min_pool_size: int = 10,
                 connection_timeout: int = 30000,
                 socket_timeout: int = 60000,
                 read_only: bool = True,
                 default_limit: int = 100,
                 max_limit: int = 1000):
        """
        Initialize MongoDB repository.

        Args:
            connection_string: MongoDB connection string
            database_name: Database name
            max_pool_size: Maximum connection pool size
            min_pool_size: Minimum connection pool size
            connection_timeout: Connection timeout in milliseconds
            socket_timeout: Socket timeout in milliseconds
            read_only: Whether to enforce read-only mode
            default_limit: Default query result limit
            max_limit: Maximum query result limit
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.connection_timeout = connection_timeout
        self.socket_timeout = socket_timeout
        self.read_only = read_only
        self.default_limit = default_limit
        self.max_limit = max_limit

        self._client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self._database: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        self._connected = False

    async def connect(self) -> None:
        """
        Establish connection to the database.

        Creates an async MongoDB client with connection pooling.
        """
        if self._connected:
            logger.warning("Already connected to MongoDB database")
            return

        try:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(
                self.connection_string,
                maxPoolSize=self.max_pool_size,
                minPoolSize=self.min_pool_size,
                connectTimeoutMS=self.connection_timeout,
                socketTimeoutMS=self.socket_timeout,
                serverSelectionTimeoutMS=self.connection_timeout
            )

            # Test connection
            await self._client.server_info()

            self._database = self._client[self.database_name]
            self._connected = True
            logger.info(f"Connected to MongoDB database: {self.database_name}")

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise ConnectionError(f"MongoDB connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """
        Close database connection.

        Properly closes the MongoDB client and releases resources.
        """
        if self._client:
            self._client.close()
            self._connected = False
            logger.info(f"Disconnected from MongoDB database: {self.database_name}")

    async def execute_query(self,
                           query: str,
                           params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a database query.

        For MongoDB, the query should be a JSON string representing:
        - A find query: {"collection": "users", "filter": {...}, "options": {...}}
        - An aggregation: {"collection": "users", "pipeline": [...]}

        Args:
            query: JSON string with MongoDB query
            params: Additional parameters (used for options)

        Returns:
            List of result dictionaries

        Raises:
            ValueError: If query is invalid or violates read-only mode
            ConnectionError: If not connected
            RuntimeError: If query execution fails
        """
        if not self._connected:
            await self.connect()

        try:
            # Parse query JSON
            query_obj = json.loads(query) if isinstance(query, str) else query

            collection_name = query_obj.get('collection')
            if not collection_name:
                raise ValueError("Collection name is required")

            collection = self._database[collection_name]

            # Handle different query types
            if 'pipeline' in query_obj:
                # Aggregation query
                return await self._execute_aggregation(
                    collection,
                    query_obj['pipeline'],
                    params or {}
                )
            else:
                # Find query
                filter_query = query_obj.get('filter', {})
                options = query_obj.get('options', {})
                if params:
                    options.update(params)
                return await self._execute_find(collection, filter_query, options)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid query JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise RuntimeError(f"Query execution failed: {str(e)}")

    async def execute_transaction(self,
                                 queries: List[tuple]) -> List[List[Dict[str, Any]]]:
        """
        Execute multiple queries in a transaction.

        Args:
            queries: List of (query, params) tuples

        Returns:
            List of results for each query

        Raises:
            ValueError: If operations violate read-only mode
            RuntimeError: If transaction fails
        """
        if self.read_only:
            raise ValueError("Transactions are not allowed in read-only mode")

        if not self._connected:
            await self.connect()

        results = []
        async with await self._client.start_session() as session:
            async with session.start_transaction():
                try:
                    for query, params in queries:
                        result = await self.execute_query(query, params)
                        results.append(result)

                    return results

                except Exception as e:
                    logger.error(f"Transaction failed: {str(e)}")
                    raise RuntimeError(f"Transaction failed: {str(e)}")

    async def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection is successful
        """
        try:
            if not self._connected:
                await self.connect()

            # Ping the server
            await self._client.admin.command('ping')
            return True

        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    async def _execute_find(self,
                           collection: motor.motor_asyncio.AsyncIOMotorCollection,
                           filter_query: Dict[str, Any],
                           options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute a find query.

        Args:
            collection: MongoDB collection
            filter_query: Query filter
            options: Query options (limit, sort, projection, etc.)

        Returns:
            List of documents
        """
        # Apply limit
        limit = min(
            options.get('limit', self.default_limit),
            self.max_limit
        )

        # Build cursor
        cursor = collection.find(filter_query)

        # Apply options
        if 'projection' in options:
            cursor = cursor.projection(options['projection'])

        if 'sort' in options:
            sort_spec = self._parse_sort(options['sort'])
            cursor = cursor.sort(sort_spec)

        if 'skip' in options:
            cursor = cursor.skip(options['skip'])

        cursor = cursor.limit(limit)

        # Execute and convert to list
        results = []
        async for doc in cursor:
            # Convert ObjectId to string for JSON serialization
            doc = self._convert_objectid(doc)
            results.append(doc)

        return results

    async def _execute_aggregation(self,
                                  collection: motor.motor_asyncio.AsyncIOMotorCollection,
                                  pipeline: List[Dict[str, Any]],
                                  options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute an aggregation pipeline.

        Args:
            collection: MongoDB collection
            pipeline: Aggregation pipeline
            options: Aggregation options

        Returns:
            List of aggregation results
        """
        # Add limit stage if not present and if specified in options
        if 'limit' in options and not any('$limit' in stage for stage in pipeline):
            limit = min(options['limit'], self.max_limit)
            pipeline.append({'$limit': limit})

        # Execute aggregation
        cursor = collection.aggregate(pipeline)

        results = []
        async for doc in cursor:
            doc = self._convert_objectid(doc)
            results.append(doc)

        return results

    async def list_collections(self) -> List[str]:
        """
        List all collections in the database.

        Returns:
            List of collection names
        """
        if not self._connected:
            await self.connect()

        return await self._database.list_collection_names()

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection statistics
        """
        if not self._connected:
            await self.connect()

        stats = await self._database.command('collStats', collection_name)
        return {
            'count': stats.get('count', 0),
            'size': stats.get('size', 0),
            'avgObjSize': stats.get('avgObjSize', 0),
            'storageSize': stats.get('storageSize', 0),
            'indexes': stats.get('nindexes', 0)
        }

    async def get_collection_count(self, collection_name: str, filter_query: Optional[Dict[str, Any]] = None) -> int:
        """
        Get document count for a collection.

        Args:
            collection_name: Name of the collection
            filter_query: Optional filter

        Returns:
            Number of documents
        """
        if not self._connected:
            await self.connect()

        collection = self._database[collection_name]
        return await collection.count_documents(filter_query or {})

    async def create_index(self, collection_name: str, index_spec: List[tuple], **kwargs):
        """
        Create an index on a collection.

        Args:
            collection_name: Name of the collection
            index_spec: Index specification
            **kwargs: Additional index options
        """
        if self.read_only:
            raise ValueError("Index creation not allowed in read-only mode")

        if not self._connected:
            await self.connect()

        collection = self._database[collection_name]
        return await collection.create_index(index_spec, **kwargs)

    async def insert_one(self, collection_name: str, document: Dict[str, Any]):
        """
        Insert a single document.

        Args:
            collection_name: Name of the collection
            document: Document to insert

        Returns:
            Inserted document ID
        """
        if self.read_only:
            raise ValueError("Insert operations not allowed in read-only mode")

        if not self._connected:
            await self.connect()

        collection = self._database[collection_name]
        result = await collection.insert_one(document)
        return str(result.inserted_id)

    async def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]):
        """
        Insert multiple documents.

        Args:
            collection_name: Name of the collection
            documents: Documents to insert

        Returns:
            List of inserted document IDs
        """
        if self.read_only:
            raise ValueError("Insert operations not allowed in read-only mode")

        if not self._connected:
            await self.connect()

        collection = self._database[collection_name]
        result = await collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]

    async def update_one(self, collection_name: str, filter_query: Dict[str, Any], update: Dict[str, Any]):
        """
        Update a single document.

        Args:
            collection_name: Name of the collection
            filter_query: Query filter
            update: Update operations

        Returns:
            Number of modified documents
        """
        if self.read_only:
            raise ValueError("Update operations not allowed in read-only mode")

        if not self._connected:
            await self.connect()

        collection = self._database[collection_name]
        result = await collection.update_one(filter_query, update)
        return result.modified_count

    async def delete_one(self, collection_name: str, filter_query: Dict[str, Any]):
        """
        Delete a single document.

        Args:
            collection_name: Name of the collection
            filter_query: Query filter

        Returns:
            Number of deleted documents
        """
        if self.read_only:
            raise ValueError("Delete operations not allowed in read-only mode")

        if not self._connected:
            await self.connect()

        collection = self._database[collection_name]
        result = await collection.delete_one(filter_query)
        return result.deleted_count

    def _parse_sort(self, sort_spec: Union[str, Dict[str, int], List[tuple]]) -> List[tuple]:
        """
        Parse sort specification into pymongo format.

        Args:
            sort_spec: Sort specification in various formats

        Returns:
            List of (field, direction) tuples
        """
        if isinstance(sort_spec, str):
            # Simple string: "field" or "-field"
            if sort_spec.startswith('-'):
                return [(sort_spec[1:], DESCENDING)]
            return [(sort_spec, ASCENDING)]

        elif isinstance(sort_spec, dict):
            # Dictionary: {"field1": 1, "field2": -1}
            return [(k, DESCENDING if v < 0 else ASCENDING) for k, v in sort_spec.items()]

        elif isinstance(sort_spec, list):
            # Already in correct format
            return sort_spec

        return []

    def _convert_objectid(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert ObjectId to string for JSON serialization.

        Args:
            doc: Document with potential ObjectIds

        Returns:
            Document with ObjectIds converted to strings
        """
        if isinstance(doc, dict):
            for key, value in doc.items():
                if isinstance(value, ObjectId):
                    doc[key] = str(value)
                elif isinstance(value, dict):
                    doc[key] = self._convert_objectid(value)
                elif isinstance(value, list):
                    doc[key] = [
                        self._convert_objectid(item) if isinstance(item, dict) else
                        str(item) if isinstance(item, ObjectId) else item
                        for item in value
                    ]
                elif isinstance(value, datetime):
                    doc[key] = value.isoformat()
        return doc

    @property
    def database_type(self) -> DatabaseType:
        """Get the database type."""
        return DatabaseType.MONGODB

    async def create_result(self,
                           data: List[Dict[str, Any]],
                           query: str,
                           execution_time_ms: float) -> QueryResult:
        """
        Create a QueryResult object.

        Args:
            data: Query result data
            query: Executed query
            execution_time_ms: Query execution time

        Returns:
            QueryResult value object
        """
        return QueryResult(
            data=data,
            count=len(data),
            is_success=True,
            error_message=None,
            execution_time_ms=execution_time_ms,
            database_type=self.database_type,
            query_executed=query
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"MongoDBRepository(database='{self.database_name}')"
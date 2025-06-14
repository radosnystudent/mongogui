import functools
import json
import re
from typing import Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from db.constants import (
    LIMIT_STAGE,
    MAX_QUERY_LIMIT,
    NOT_CONNECTED_MSG,
    SKIP_STAGE,
)
from db.query_preprocessor import query_preprocessor
from db.result import Result
from db.utils import convert_to_object_id


def require_connection(method: Any) -> Any:
    """
    Decorator to ensure MongoClientWrapper has an active connection before proceeding.
    Returns a Result error if not connected.
    """

    @functools.wraps(method)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if self.client is None:
            return Result.Err(NOT_CONNECTED_MSG)
        return method(self, *args, **kwargs)

    return wrapper


def require_connection_result(method: Any) -> Any:
    """
    Decorator to ensure MongoClientWrapper has an active connection and database before proceeding.
    Returns a Result error if not connected.
    """

    @functools.wraps(method)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if self.client is None or not self.current_db:
            return Result.Err(NOT_CONNECTED_MSG)
        return method(self, *args, **kwargs)

    return wrapper


class MongoClientWrapper:
    """
    Wrapper for PyMongo's MongoClient with additional logic for query execution, connection management,
    and error handling for the MongoDB GUI application.
    """

    def __init__(self) -> None:
        """
        Initialize the MongoClientWrapper instance.
        Sets up the client and current database state.
        """
        self.client: MongoClient[dict[str, Any]] | None = None
        self.current_db: str = ""

    def connect(
        self,
        ip: str,
        port: int,
        db: str,
        login: str | None,
        password: str | None,
        tls: bool,
    ) -> bool:
        """
        Connect to a MongoDB instance with or without authentication and TLS.

        Args:
            ip: Host IP address.
            port: Port number.
            db: Database name.
            login: Username (optional).
            password: Password (optional).
            tls: Whether to use TLS/SSL.
        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            if login and password:
                uri = f"mongodb://{login}:{password}@{ip}:{port}/{db}"
            else:
                uri = f"mongodb://{ip}:{port}/{db}"

            options: dict[str, Any] = {}
            if tls:
                options["tls"] = True

            self.client = MongoClient(uri, **options)
            self.current_db = db
            # Explicitly ping the server to verify connection (for test expectations)
            self.client.admin.command("ping")
            return True
        except PyMongoError:
            return False

    def _require_connection(self) -> bool:
        """Return True if connected and current_db is set, else False."""
        return self.client is not None and bool(self.current_db)

    def list_collections(self) -> list[str]:
        """
        List all collections in the current database.

        Returns:
            List of collection names, or empty list if not connected or error occurs.
        """
        if not self._require_connection():
            return []
        client = self.client
        dbname = self.current_db
        if client is None or not dbname:
            return []
        try:
            db = client[dbname]
            return db.list_collection_names()
        except Exception:
            return []

    @require_connection_result
    def execute_query(
        self, query_text: str, page: int = 0, page_size: int = 50, explain: bool = False
    ) -> Result[list[dict[str, Any]] | dict[str, Any], str]:
        """
        Execute a MongoDB query from text and return results. Supports server-side pagination.

        Args:
            query_text: The MongoDB query as a string.
            page: Page number for pagination.
            page_size: Number of documents per page.
            explain: Whether to return query plan/explain output.
        Returns:
            Result object containing query results or error message.
        """
        try:
            preprocessed_query = query_preprocessor.preprocess_query(query_text)
            if "find(" in preprocessed_query:
                result = self._execute_find_query(
                    preprocessed_query, page=page, page_size=page_size, explain=explain
                )
            elif "aggregate(" in preprocessed_query:
                result = self._execute_aggregate_query(
                    preprocessed_query, page=page, page_size=page_size, explain=explain
                )
            else:
                return Result.Err("Unsupported query type")
            if isinstance(result, str):
                return Result.Err(result)
            return Result.Ok(result)
        except Exception as e:
            return Result.Err(f"Query execution error: {str(e)}")

    def _execute_find_query(
        self, query_text: str, page: int = 0, page_size: int = 50, explain: bool = False
    ) -> list[dict[str, Any]] | dict[str, Any] | str:
        """
        Execute a find query with server-side pagination.

        Args:
            query_text: The MongoDB find query as a string.
            page: Page number for pagination.
            page_size: Number of documents per page.
            explain: Whether to return query plan/explain output.
        Returns:
            List of documents, explain output, or error message string.
        """
        if not self._require_connection():
            return NOT_CONNECTED_MSG
        client = self.client
        dbname = self.current_db
        if client is None or not dbname:
            return NOT_CONNECTED_MSG
        try:
            pattern = r"db\.(\w+)\.find\((.*)\)"
            match = re.search(pattern, query_text)
            if not match:
                return "Invalid find query format"
            collection_name = match.group(1)
            query_part = match.group(2).strip()
            if query_part == "{}" or query_part == "":
                query_dict = {}
            else:
                query_dict = json.loads(query_part)
            db = client[dbname]
            collection = db[collection_name]
            cursor = collection.find(query_dict)
            if not (SKIP_STAGE in query_dict or LIMIT_STAGE in query_dict):
                cursor = cursor.skip(page * page_size).limit(page_size)
            if explain:
                plan = cursor.explain()
                return plan
            else:
                results = list(cursor)
                return results
        except Exception as e:
            return f"Find query error: {str(e)}"

    def _execute_aggregate_query(
        self, query_text: str, page: int = 0, page_size: int = 50, explain: bool = False
    ) -> list[dict[str, Any]] | dict[str, Any] | str:
        """
        Execute an aggregate query with server-side pagination.

        Args:
            query_text: The MongoDB aggregate query as a string.
            page: Page number for pagination.
            page_size: Number of documents per page.
            explain: Whether to return query plan/explain output.
        Returns:
            List of documents, explain output, or error message string.
        """
        if not self._require_connection():
            return NOT_CONNECTED_MSG
        client = self.client
        dbname = self.current_db
        if client is None or not dbname:
            return NOT_CONNECTED_MSG
        try:
            pattern = r"db\.(\w+)\.aggregate\((.*)\)"
            match = re.search(pattern, query_text)
            if not match:
                return "Invalid aggregate query format"
            collection_name = match.group(1)
            pipeline_part = match.group(2).strip()
            pipeline = json.loads(pipeline_part)
            if not isinstance(pipeline, list):
                return "Pipeline must be a list"
            has_skip = any(
                isinstance(stage, dict) and SKIP_STAGE in stage for stage in pipeline
            )
            has_limit = any(
                isinstance(stage, dict) and LIMIT_STAGE in stage for stage in pipeline
            )
            paginated_pipeline = list(pipeline)
            if not has_skip:
                paginated_pipeline.append({SKIP_STAGE: page * page_size})
            if not has_limit:
                paginated_pipeline.append({LIMIT_STAGE: page_size})
            db = client[dbname]
            collection = db[collection_name]
            if explain:
                plan = db.command(
                    "explain",
                    {
                        "aggregate": collection_name,
                        "pipeline": paginated_pipeline,
                        "cursor": {"batchSize": page_size},
                    },
                )
                return plan
            else:
                results = list(collection.aggregate(paginated_pipeline))
                return results
        except Exception as e:
            return f"Aggregate query error: {str(e)}"

    def run_query(
        self, db_name: str, collection_name: str, query_dict: dict[str, Any]
    ) -> list[dict[str, Any]] | str:
        """
        Run a query with specified parameters.

        Args:
            db_name: The name of the database.
            collection_name: The name of the collection.
            query_dict: The query criteria as a dictionary.
        Returns:
            List of matching documents, or error message string.
        """
        client = self.client
        if client is None or not db_name:
            return NOT_CONNECTED_MSG
        try:
            db = client[db_name]
            collection = db[collection_name]
            results = list(collection.find(query_dict).limit(MAX_QUERY_LIMIT))
            return results
        except Exception as e:
            return str(e)

    def run_aggregate(
        self, db_name: str, collection_name: str, pipeline: list[dict[str, Any]]
    ) -> list[dict[str, Any]] | str:
        """
        Run an aggregation pipeline.

        Args:
            db_name: The name of the database.
            collection_name: The name of the collection.
            pipeline: The aggregation pipeline as a list of stages.
        Returns:
            List of documents resulting from the aggregation, or error message string.
        """
        client = self.client
        if client is None or not db_name:
            return NOT_CONNECTED_MSG
        try:
            db = client[db_name]
            collection = db[collection_name]
            results = list(collection.aggregate(pipeline))
            return results
        except Exception as e:
            return str(e)

    def update_document(
        self, collection_name: str, doc_id: Any, new_doc: dict[str, Any]
    ) -> bool:
        """
        Update a document by _id in the given collection.

        Args:
            collection_name: The name of the collection.
            doc_id: The _id of the document to update.
            new_doc: The new document data as a dictionary.
        Returns:
            True if the document was updated, False otherwise.
        """
        if not self._require_connection():
            return False
        client = self.client
        dbname = self.current_db
        if client is None or not dbname:
            return False
        try:
            db = client[dbname]
            collection = db[collection_name]
            doc_id = convert_to_object_id(doc_id)
            result = collection.replace_one({"_id": doc_id}, new_doc)
            return result.modified_count > 0
        except Exception:
            return False

    @require_connection
    def list_indexes(self, collection_name: str) -> Result[list[dict[str, Any]], str]:
        """
        List all indexes for a collection.

        Args:
            collection_name: The name of the collection.
        Returns:
            Result object containing a list of indexes or error message.
        """
        if not self._require_connection():
            return Result.Err(NOT_CONNECTED_MSG)
        client = self.client
        dbname = self.current_db
        if client is None or not dbname:
            return Result.Err(NOT_CONNECTED_MSG)
        try:
            db = client[dbname]
            collection = db[collection_name]
            # Cast to list[dict[str, Any]] for mypy compatibility
            indexes = [dict(idx) for idx in collection.list_indexes()]
            return Result.Ok(indexes)
        except Exception as e:
            return Result.Err(f"List indexes error: {str(e)}")

    @require_connection
    def create_index(
        self, collection_name: str, keys: Any, **kwargs: Any
    ) -> Result[str, str]:
        """
        Create an index on a collection. Keys is a list of (field, direction) tuples.

        Args:
            collection_name: The name of the collection.
            keys: The index keys and their directions.
            **kwargs: Additional index options.
        Returns:
            Result object containing the index name or error message.
        """
        if not self._require_connection():
            return Result.Err(NOT_CONNECTED_MSG)
        client = self.client
        dbname = self.current_db
        if client is None or not dbname:
            return Result.Err(NOT_CONNECTED_MSG)
        try:
            db = client[dbname]
            collection = db[collection_name]
            index_name = collection.create_index(keys, **kwargs)
            return Result.Ok(index_name)
        except Exception as e:
            return Result.Err(f"Create index error: {str(e)}")

    @require_connection
    def drop_index(self, collection_name: str, index_name: str) -> bool | str:
        """
        Drop an index by name from a collection.

        Args:
            collection_name: The name of the collection.
            index_name: The name of the index to drop.
        Returns:
            True if the index was dropped, error message string otherwise.
        """
        if not self._require_connection():
            return f"Drop index error: {NOT_CONNECTED_MSG}"
        client = self.client
        dbname = self.current_db
        if client is None or not dbname:
            return f"Drop index error: {NOT_CONNECTED_MSG}"
        try:
            db = client[dbname]
            collection = db[collection_name]
            collection.drop_index(index_name)
            return True
        except Exception as e:
            return f"Drop index error: {str(e)}"

    @require_connection
    def update_index(
        self, collection_name: str, index_name: str, keys: list[Any], **kwargs: Any
    ) -> str | Any:
        """
        Update an index by dropping and recreating it.

        Args:
            collection_name: The name of the collection.
            index_name: The name of the index to update.
            keys: The new index keys and their directions.
            **kwargs: Additional index options.
        Returns:
            Result object containing the new index name or error message.
        """
        drop_result = self.drop_index(collection_name, index_name)
        if drop_result is not True:
            return drop_result
        return self.create_index(collection_name, keys, **kwargs)

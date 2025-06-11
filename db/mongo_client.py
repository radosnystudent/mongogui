from typing import Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from db.constants import LIMIT_STAGE, SKIP_STAGE
from db.query_preprocessor import query_preprocessor
from db.utils import convert_to_object_id

NOT_CONNECTED_MSG = "Not connected to database"


class MongoClientWrapper:
    def __init__(self) -> None:
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
        try:
            if login and password:
                uri = f"mongodb://{login}:{password}@{ip}:{port}/{db}"
            else:
                uri = f"mongodb://{ip}:{port}/{db}"

            options: dict[str, Any] = {}
            if tls:
                options["tls"] = True

            self.client = MongoClient(uri, **options)
            self.current_db = db  # Test connection
            self.client.admin.command("ping")
            return True
        except PyMongoError:
            return False

    def list_collections(self) -> list[str]:
        """List all collections in the current database."""
        if self.client is None:
            return []

        try:
            db = self.client[self.current_db]
            return db.list_collection_names()
        except Exception:
            return []

    def execute_query(
        self, query_text: str, page: int = 0, page_size: int = 50, explain: bool = False
    ) -> list[dict[str, Any]] | dict[str, Any] | str:
        """Execute a MongoDB query from text and return results. Supports server-side pagination."""
        if self.client is None:
            return NOT_CONNECTED_MSG

        try:
            preprocessed_query = query_preprocessor.preprocess_query(query_text)
            if "find(" in preprocessed_query:
                return self._execute_find_query(
                    preprocessed_query, page=page, page_size=page_size, explain=explain
                )
            elif "aggregate(" in preprocessed_query:
                return self._execute_aggregate_query(
                    preprocessed_query, page=page, page_size=page_size, explain=explain
                )
            else:
                return "Unsupported query type"
        except Exception as e:
            return f"Query execution error: {str(e)}"

    def _execute_find_query(
        self, query_text: str, page: int = 0, page_size: int = 50, explain: bool = False
    ) -> list[dict[str, Any]] | dict[str, Any] | str:
        """Execute a find query with server-side pagination."""
        try:
            import json
            import re

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
            # Only apply skip/limit if not already present in the query dict
            if self.client is not None:
                db = self.client[self.current_db]
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
            else:
                return NOT_CONNECTED_MSG
        except Exception as e:
            return f"Find query error: {str(e)}"

    def _execute_aggregate_query(
        self, query_text: str, page: int = 0, page_size: int = 50, explain: bool = False
    ) -> list[dict[str, Any]] | dict[str, Any] | str:
        """Execute an aggregate query with server-side pagination."""
        try:
            import re

            pattern = r"db\.(\w+)\.aggregate\((.*)\)"
            match = re.search(pattern, query_text)
            if not match:
                return "Invalid aggregate query format"
            collection_name = match.group(1)
            pipeline_part = match.group(2).strip()
            import json

            pipeline = json.loads(pipeline_part)
            if not isinstance(pipeline, list):
                return "Pipeline must be a list"
            # Only append $skip/$limit if not already present
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
            if self.client is not None:
                db = self.client[self.current_db]
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
            else:
                return NOT_CONNECTED_MSG
        except Exception as e:
            return f"Aggregate query error: {str(e)}"

    def run_query(
        self, db_name: str, collection_name: str, query_dict: dict[str, Any]
    ) -> list[dict[str, Any]] | str:
        """Run a query with specified parameters."""
        try:
            if self.client is None:
                return NOT_CONNECTED_MSG

            db = self.client[db_name]
            collection = db[collection_name]
            results = list(collection.find(query_dict).limit(1000))
            return results
        except Exception as e:
            return str(e)

    def run_aggregate(
        self, db_name: str, collection_name: str, pipeline: list[dict[str, Any]]
    ) -> list[dict[str, Any]] | str:
        """Run an aggregation pipeline."""
        try:
            if self.client is None:
                return NOT_CONNECTED_MSG

            db = self.client[db_name]
            collection = db[collection_name]
            results = list(collection.aggregate(pipeline))
            return results
        except Exception as e:
            return str(e)

    def update_document(
        self, collection_name: str, doc_id: Any, new_doc: dict[str, Any]
    ) -> bool:
        """Update a document by _id in the given collection."""
        if self.client is None:
            return False
        try:
            db = self.client[self.current_db]
            collection = db[collection_name]

            # Convert doc_id to ObjectId if possible
            doc_id = convert_to_object_id(doc_id)
            result = collection.replace_one({"_id": doc_id}, new_doc)
            return result.modified_count > 0
        except Exception:
            return False

    def list_indexes(self, collection_name: str) -> list[dict[str, Any]] | str:
        """List all indexes for a collection."""
        if self.client is None:
            return NOT_CONNECTED_MSG
        try:
            db = self.client[self.current_db]
            collection = db[collection_name]
            # Convert each index info to dict explicitly
            return [dict(idx) for idx in collection.list_indexes()]
        except Exception as e:
            return f"List indexes error: {str(e)}"

    def create_index(
        self, collection_name: str, keys: list[Any], **kwargs: Any
    ) -> str | Any:
        """Create an index on a collection. Keys is a list of (field, direction) tuples."""
        if self.client is None:
            return NOT_CONNECTED_MSG
        try:
            db = self.client[self.current_db]
            collection = db[collection_name]
            name = collection.create_index(keys, **kwargs)
            return name
        except Exception as e:
            return f"Create index error: {str(e)}"

    def drop_index(self, collection_name: str, index_name: str) -> bool | str:
        """Drop an index by name from a collection."""
        if self.client is None:
            return NOT_CONNECTED_MSG
        try:
            db = self.client[self.current_db]
            collection = db[collection_name]
            collection.drop_index(index_name)
            return True
        except Exception as e:
            return f"Drop index error: {str(e)}"

    def update_index(
        self, collection_name: str, index_name: str, keys: list[Any], **kwargs: Any
    ) -> str | Any:
        """Update an index by dropping and recreating it."""
        drop_result = self.drop_index(collection_name, index_name)
        if drop_result is not True:
            return drop_result
        return self.create_index(collection_name, keys, **kwargs)

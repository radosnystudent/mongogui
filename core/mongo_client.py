from typing import Any, Dict, List, Optional, Union

from pymongo import MongoClient
from pymongo.errors import PyMongoError

NOT_CONNECTED_MSG = "Not connected to database"


class MongoClientWrapper:
    def __init__(self) -> None:
        self.client: Optional[MongoClient[Dict[str, Any]]] = None
        self.current_db: str = ""

    def connect(
        self,
        ip: str,
        port: int,
        db: str,
        login: Optional[str],
        password: Optional[str],
        tls: bool,
    ) -> bool:
        try:
            if login and password:
                uri = f"mongodb://{login}:{password}@{ip}:{port}/{db}"
            else:
                uri = f"mongodb://{ip}:{port}/{db}"

            options: Dict[str, Any] = {}
            if tls:
                options["tls"] = True

            self.client = MongoClient(uri, **options)
            self.current_db = db

            # Test connection
            self.client.admin.command("ping")
            return True
        except PyMongoError:
            return False

    def list_collections(self) -> List[str]:
        """List all collections in the current database."""
        if self.client is None:
            return []

        try:
            db = self.client[self.current_db]
            return db.list_collection_names()
        except Exception:
            return []

    def execute_query(self, query_text: str) -> Union[List[Dict[str, Any]], str]:
        """Execute a MongoDB query from text and return results."""
        if self.client is None:
            return NOT_CONNECTED_MSG

        try:
            # Simple query parsing - this is a basic implementation
            # In a real app, you'd want more sophisticated parsing
            if "find(" in query_text:
                return self._execute_find_query(query_text)
            elif "aggregate(" in query_text:
                return self._execute_aggregate_query(query_text)
            else:
                return "Unsupported query type"
        except Exception as e:
            return f"Query execution error: {str(e)}"

    def _execute_find_query(self, query_text: str) -> Union[List[Dict[str, Any]], str]:
        """Execute a find query."""
        try:
            # Extract collection name and query from text
            # This is a simplified parser
            import re

            # Pattern to match db.collection.find({...})
            pattern = r"db\.(\w+)\.find\((.*)\)"
            match = re.search(pattern, query_text)

            if not match:
                return "Invalid find query format"

            collection_name = match.group(1)
            query_part = match.group(2).strip()

            # Parse query (simplified - assumes valid JSON)
            if query_part == "{}" or query_part == "":
                query_dict = {}
            else:
                import json

                query_dict = json.loads(query_part)
            # Execute query
            if self.client is not None:
                db = self.client[self.current_db]
                collection = db[collection_name]
                results = list(
                    collection.find(query_dict).limit(1000)
                )  # Limit for safety
                return results
            else:
                return NOT_CONNECTED_MSG
        except Exception as e:
            return f"Find query error: {str(e)}"

    def _execute_aggregate_query(
        self, query_text: str
    ) -> Union[List[Dict[str, Any]], str]:
        """Execute an aggregate query."""
        try:
            # Extract collection name and pipeline from text
            import re

            # Pattern to match db.collection.aggregate([...])
            pattern = r"db\.(\w+)\.aggregate\((.*)\)"
            match = re.search(pattern, query_text)

            if not match:
                return "Invalid aggregate query format"

            collection_name = match.group(1)
            pipeline_part = match.group(2).strip()

            # Parse pipeline (simplified - assumes valid JSON)
            import json

            pipeline = json.loads(pipeline_part)
            # Execute query
            if self.client is not None:
                db = self.client[self.current_db]
                collection = db[collection_name]
                results = list(collection.aggregate(pipeline))
                return results
            else:
                return NOT_CONNECTED_MSG
        except Exception as e:
            return f"Aggregate query error: {str(e)}"

    def run_query(
        self, db_name: str, collection_name: str, query_dict: Dict[str, Any]
    ) -> Union[List[Dict[str, Any]], str]:
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
        self, db_name: str, collection_name: str, pipeline: List[Dict[str, Any]]
    ) -> Union[List[Dict[str, Any]], str]:
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
        self, collection_name: str, doc_id: Any, new_doc: Dict[str, Any]
    ) -> bool:
        """Update a document by _id in the given collection."""
        if self.client is None:
            return False
        try:
            db = self.client[self.current_db]
            collection = db[collection_name]
            # Convert doc_id to ObjectId if possible
            from core.utils import convert_to_object_id

            doc_id = convert_to_object_id(doc_id)
            result = collection.replace_one({"_id": doc_id}, new_doc)
            return result.modified_count > 0
        except Exception:
            return False

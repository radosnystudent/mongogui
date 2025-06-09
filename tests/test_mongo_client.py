from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from db.mongo_client import MongoClientWrapper


class TestMongoClientWrapper:
    """Test cases for MongoClientWrapper class."""

    @pytest.fixture
    def mongo_wrapper(self) -> MongoClientWrapper:
        """Create a MongoClientWrapper instance for testing."""
        return MongoClientWrapper()

    @patch("db.mongo_client.MongoClient")
    def test_connect_success_with_auth(
        self, mock_mongo_client: MagicMock, mongo_wrapper: MongoClientWrapper
    ) -> None:
        """Test successful connection with authentication."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_mongo_client.return_value = mock_client_instance
        mock_client_instance.admin.command.return_value = {"ok": 1}

        # Test connection
        result = mongo_wrapper.connect(
            "localhost", 27017, "test_db", "user", "pass", False
        )

        # Verify
        assert result is True
        mock_mongo_client.assert_called_once()
        mock_client_instance.admin.command.assert_called_once_with("ping")

    @patch("db.mongo_client.MongoClient")
    def test_connect_success_without_auth(
        self, mock_mongo_client: MagicMock, mongo_wrapper: MongoClientWrapper
    ) -> None:
        """Test successful connection without authentication."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_mongo_client.return_value = mock_client_instance
        mock_client_instance.admin.command.return_value = {"ok": 1}

        # Test connection
        result = mongo_wrapper.connect("localhost", 27017, "test_db", None, None, False)

        # Verify
        assert result is True
        mock_mongo_client.assert_called_once()

    @patch("db.mongo_client.MongoClient")
    def test_connect_failure(
        self, mock_mongo_client: MagicMock, mongo_wrapper: MongoClientWrapper
    ) -> None:
        """Test failed connection."""
        # Setup mock to raise exception
        from pymongo.errors import PyMongoError

        mock_mongo_client.side_effect = PyMongoError("Connection failed")

        # Test connection
        result = mongo_wrapper.connect("invalid", 27017, "test_db", None, None, False)

        # Verify
        assert result is False

    @patch("db.mongo_client.MongoClient")
    def test_list_collections_success(
        self, mock_mongo_client: MagicMock, mongo_wrapper: MongoClientWrapper
    ) -> None:
        """Test successful collection listing."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_mongo_client.return_value = mock_client_instance
        mock_client_instance.admin.command.return_value = {"ok": 1}

        mock_db = MagicMock()
        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.list_collection_names.return_value = ["collection1", "collection2"]

        # Connect and test
        mongo_wrapper.connect("localhost", 27017, "test_db", None, None, False)
        collections = mongo_wrapper.list_collections()

        # Verify
        assert collections == ["collection1", "collection2"]

    def test_list_collections_no_connection(
        self, mongo_wrapper: MongoClientWrapper
    ) -> None:
        """Test collection listing without connection."""
        collections = mongo_wrapper.list_collections()
        assert collections == []

    @patch("db.mongo_client.MongoClient")
    def test_execute_find_query(
        self, mock_mongo_client: MagicMock, mongo_wrapper: MongoClientWrapper
    ) -> None:
        """Test find query execution."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_mongo_client.return_value = mock_client_instance
        mock_client_instance.admin.command.return_value = {"ok": 1}

        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        mock_cursor = MagicMock()
        mock_cursor.limit.return_value = [{"_id": "1", "name": "test"}]
        mock_collection.find.return_value = mock_cursor

        # Connect and test
        mongo_wrapper.connect("localhost", 27017, "test_db", None, None, False)
        result = mongo_wrapper.execute_query("db.test_collection.find({})")

        # Verify
        assert isinstance(result, list)

    def test_execute_query_no_connection(
        self, mongo_wrapper: MongoClientWrapper
    ) -> None:
        """Test query execution without connection."""
        result = mongo_wrapper.execute_query("db.test.find({})")
        assert result == "Not connected to database"

    @patch("db.mongo_client.MongoClient")
    def test_run_query_success(
        self, mock_mongo_client: MagicMock, mongo_wrapper: MongoClientWrapper
    ) -> None:
        """Test run_query method."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_mongo_client.return_value = mock_client_instance
        mock_client_instance.admin.command.return_value = {"ok": 1}

        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        mock_cursor = MagicMock()
        mock_cursor.limit.return_value = [{"_id": "1", "data": "test"}]
        mock_collection.find.return_value = mock_cursor

        # Connect and test
        mongo_wrapper.connect("localhost", 27017, "test_db", None, None, False)
        result = mongo_wrapper.run_query("test_db", "test_collection", {"name": "test"})

        # Verify
        assert isinstance(result, list)

    def test_run_query_no_connection(self, mongo_wrapper: MongoClientWrapper) -> None:
        """Test run_query without connection."""
        result = mongo_wrapper.run_query("test_db", "test_collection", {})
        assert result == "Not connected to database"

    @patch("db.mongo_client.MongoClient")
    def test_run_aggregate_success(
        self, mock_mongo_client: MagicMock, mongo_wrapper: MongoClientWrapper
    ) -> None:
        """Test run_aggregate method."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_mongo_client.return_value = mock_client_instance
        mock_client_instance.admin.command.return_value = {"ok": 1}

        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        mock_collection.aggregate.return_value = [{"_id": "1", "count": 5}]

        # Connect and test
        mongo_wrapper.connect("localhost", 27017, "test_db", None, None, False)
        pipeline = [{"$group": {"_id": None, "count": {"$sum": 1}}}]
        result = mongo_wrapper.run_aggregate("test_db", "test_collection", pipeline)

        # Verify
        assert isinstance(result, list)

    def test_run_aggregate_no_connection(
        self, mongo_wrapper: MongoClientWrapper
    ) -> None:
        """Test run_aggregate without connection."""
        pipeline: list[dict[str, Any]] = []
        result = mongo_wrapper.run_aggregate("test_db", "test_collection", pipeline)
        assert result == "Not connected to database"

    @patch("db.mongo_client.MongoClient")
    def test_execute_invalid_query(
        self, mock_mongo_client: MagicMock, mongo_wrapper: MongoClientWrapper
    ) -> None:
        """Test execution of invalid query."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_mongo_client.return_value = mock_client_instance
        mock_client_instance.admin.command.return_value = {"ok": 1}

        # Connect and test
        mongo_wrapper.connect("localhost", 27017, "test_db", None, None, False)
        result = mongo_wrapper.execute_query("invalid query")

        # Verify
        assert isinstance(result, str)
        assert "Unsupported query type" in result

    @patch("db.mongo_client.MongoClient")
    def test_execute_aggregate_query(
        self, mock_mongo_client: MagicMock, mongo_wrapper: MongoClientWrapper
    ) -> None:
        """Test aggregate query execution."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_mongo_client.return_value = mock_client_instance
        mock_client_instance.admin.command.return_value = {"ok": 1}

        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        mock_collection.aggregate.return_value = [{"result": "aggregated"}]

        # Connect and test
        mongo_wrapper.connect("localhost", 27017, "test_db", None, None, False)
        result = mongo_wrapper.execute_query(
            'db.test_collection.aggregate([{"$match": {}}])'
        )

        # Verify
        assert isinstance(result, list)

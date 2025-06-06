from unittest.mock import MagicMock, patch

from core.mongo_client import MongoClientWrapper


@patch("core.mongo_client.MongoClient")
def test_explain_find_query(mock_mongo_client: MagicMock) -> None:
    mock_client_instance = MagicMock()
    mock_mongo_client.return_value = mock_client_instance
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_client_instance.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    mock_cursor = MagicMock()
    mock_cursor.limit.return_value.explain.return_value = {
        "queryPlanner": {"indexFilterSet": False}
    }
    mock_collection.find.return_value = mock_cursor
    wrapper = MongoClientWrapper()
    wrapper.client = mock_client_instance
    wrapper.current_db = "test_db"
    result = wrapper.execute_query("db.test.find({})", explain=True)
    assert isinstance(result, dict)
    assert "queryPlanner" in result


@patch("core.mongo_client.MongoClient")
def test_explain_aggregate_query(mock_mongo_client: MagicMock) -> None:
    mock_client_instance = MagicMock()
    mock_mongo_client.return_value = mock_client_instance
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_client_instance.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    mock_db.command.return_value = {"stages": [], "ok": 1.0}
    wrapper = MongoClientWrapper()
    wrapper.client = mock_client_instance
    wrapper.current_db = "test_db"
    result = wrapper.execute_query('db.test.aggregate([{"$match": {}}])', explain=True)
    assert isinstance(result, dict)
    assert "ok" in result

import random
import string
import typing

import pytest

from core.mongo_client import MongoClientWrapper


def random_collection_name() -> str:
    return "test_indexes_" + "".join(random.choices(string.ascii_lowercase, k=8))


@pytest.fixture(scope="module")
def mongo_client() -> typing.Generator[MongoClientWrapper]:
    wrapper = MongoClientWrapper()
    # Use test db, no auth, localhost
    wrapper.connect("localhost", 27017, "test", None, None, False)
    yield wrapper


def test_index_lifecycle(mongo_client: MongoClientWrapper) -> None:
    col = random_collection_name()
    assert mongo_client.client is not None
    db = mongo_client.client[mongo_client.current_db]
    db.create_collection(col)
    try:
        # Create index
        keys = [("field1", 1), ("field2", -1)]
        name = mongo_client.create_index(col, keys, name="myidx", unique=True)
        assert isinstance(name, str)
        # List indexes
        indexes = mongo_client.list_indexes(col)
        assert isinstance(indexes, list)
        assert any(
            isinstance(idx, dict) and idx.get("name") == "myidx" for idx in indexes
        )
        # Update index (drop and recreate)
        update_result = mongo_client.update_index(
            col, "myidx", [("field1", 1)], unique=False
        )
        assert isinstance(update_result, str)
        indexes2 = mongo_client.list_indexes(col)
        assert any(
            isinstance(idx, dict) and idx.get("name") == update_result
            for idx in indexes2
        )
        # Drop index
        drop_result = mongo_client.drop_index(col, update_result)
        assert drop_result is True
        indexes3 = mongo_client.list_indexes(col)
        assert not any(
            isinstance(idx, dict) and idx.get("name") == update_result
            for idx in indexes3
        )
    finally:
        db.drop_collection(col)

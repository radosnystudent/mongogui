import random
import string
import typing

import pytest

from db.mongo_client import MongoClientWrapper


def random_collection_name() -> str:
    return "test_indexes_" + "".join(random.choices(string.ascii_lowercase, k=8))


@pytest.fixture(scope="module")
def mongo_client() -> typing.Generator[MongoClientWrapper, None, None]:  # noqa: UP043
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
        name_result = mongo_client.create_index(col, keys, name="myidx", unique=True)
        assert not isinstance(name_result, str) and name_result.is_ok()
        name = name_result.unwrap()
        assert isinstance(name, str)
        # List indexes
        indexes_result = mongo_client.list_indexes(col)
        assert not isinstance(indexes_result, str) and indexes_result.is_ok()
        indexes = indexes_result.unwrap()
        assert isinstance(indexes, list)
        assert any(
            isinstance(idx, dict) and idx.get("name") == "myidx" for idx in indexes
        )
        # Update index (drop and recreate)
        update_result = mongo_client.update_index(
            col, "myidx", [("field1", 1)], unique=False
        )
        if isinstance(update_result, str):
            update_name = update_result
        else:
            assert update_result.is_ok()
            update_name = update_result.unwrap()
        assert isinstance(update_name, str)
        indexes2_result = mongo_client.list_indexes(col)
        assert not isinstance(indexes2_result, str) and indexes2_result.is_ok()
        indexes2 = indexes2_result.unwrap()
        assert any(
            isinstance(idx, dict) and idx.get("name") == update_name for idx in indexes2
        )
        # Drop index
        drop_result = mongo_client.drop_index(col, update_name)
        assert drop_result is True
        indexes3_result = mongo_client.list_indexes(col)
        assert not isinstance(indexes3_result, str) and indexes3_result.is_ok()
        indexes3 = indexes3_result.unwrap()
        assert not any(
            isinstance(idx, dict) and idx.get("name") == update_name for idx in indexes3
        )
    finally:
        db.drop_collection(col)

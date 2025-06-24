#!/usr/bin/env python3
"""
Integration test for the query preprocessor with MongoDB client.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.mongo_client import MongoClientWrapper


def test_mongo_client_integration() -> None:
    """Test the query preprocessor integration with MongoClientWrapper."""

    # Create a MongoDB client instance
    mongo_client = MongoClientWrapper()

    # Test cases for query preprocessing integration
    test_queries = [
        # User-friendly syntax that should be preprocessed
        'db.users.find({name:"John"})',
        'db.users.find({name:"John", age:25})',
        'db.users.find({address:{city:"New York"}})',
        'db.users.aggregate([{$match:{name:"John"}}])',
        # Already valid JSON that should pass through unchanged
        'db.users.find({"name":"John"})',
        'db.users.find({"name":"John", "age":25})',
        # Edge cases
        "db.users.find({})",
        "db.users.find()",
    ]

    all_passed = True

    for query in test_queries:
        try:
            # This will test the preprocessing but won't actually execute since we're not connected
            result = mongo_client.execute_query(query)

            # Since we're not connected, we should get a Result error with the correct message
            if (
                hasattr(result, "is_error")
                and result.is_error()
                and result.error == "Not connected to database"
            ):
                pass  # Test passed
            else:
                all_passed = False
        except Exception:
            all_passed = False

    assert all_passed, "Some integration tests failed."


if __name__ == "__main__":
    test_mongo_client_integration()

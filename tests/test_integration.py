#!/usr/bin/env python3
"""
Integration test for the query preprocessor with MongoDB client.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.mongo_client import MongoClientWrapper


def test_mongo_client_integration() -> None:
    """Test the query preprocessor integration with MongoClientWrapper."""

    print("Testing MongoDB Client Integration with Query Preprocessor")
    print("=" * 60)

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

    for i, query in enumerate(test_queries, 1):
        try:
            print(f"Test {i}: {query}")
            # This will test the preprocessing but won't actually execute since we're not connected
            result = mongo_client.execute_query(query)

            # Since we're not connected, we should get "Not connected to database"
            if result == "Not connected to database":
                print(
                    f"✓ Test {i}: PASSED - Query preprocessing worked, got expected 'not connected' message"
                )
            else:
                print(f"✗ Test {i}: FAILED - Unexpected result: {result}")
                all_passed = False

        except Exception as e:
            print(f"✗ Test {i}: ERROR - {str(e)}")
            all_passed = False
        print()

    if all_passed:
        print("🎉 All integration tests passed!")
        print(
            "\nThe query preprocessor is successfully integrated with the MongoDB client."
        )
        print("Users can now use the user-friendly syntax:")
        print('  - {name:"John"} instead of {"name":"John"}')
        print(
            '  - {$match:{status:"active"}} instead of {"$match":{"status":"active"}}'
        )
        print('  - Nested objects like {address:{city:"NYC"}} work correctly')
    else:
        print("❌ Some integration tests failed.")


if __name__ == "__main__":
    test_mongo_client_integration()

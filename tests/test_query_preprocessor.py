#!/usr/bin/env python3
"""
Test script for the query preprocessor functionality.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.query_preprocessor import query_preprocessor


def test_query_preprocessing() -> None:
    """Test various query preprocessing scenarios."""

    test_cases = [
        # Basic unquoted keys
        ('db.users.find({name:"John"})', 'db.users.find({"name":"John"})'),
        (
            'db.users.find({name:"John", age:25})',
            'db.users.find({"name":"John", "age":25})',
        ),
        # Already valid JSON (should pass through unchanged)
        ('db.users.find({"name":"John"})', 'db.users.find({"name":"John"})'),
        (
            'db.users.find({"name":"John", "age":25})',
            'db.users.find({"name":"John", "age":25})',
        ),
        # Mixed scenarios
        (
            'db.users.find({name:"John", "active":true})',
            'db.users.find({"name":"John", "active":true})',
        ),
        # Empty query
        ("db.users.find({})", "db.users.find({})"),
        ("db.users.find()", "db.users.find()"),
        # Aggregate queries
        (
            'db.users.aggregate([{$match:{name:"John"}}])',
            'db.users.aggregate([{"$match":{"name":"John"}}])',
        ),
        # Nested objects
        (
            'db.users.find({address:{city:"New York"}})',
            'db.users.find({"address":{"city":"New York"}})',
        ),
        # Arrays
        (
            'db.users.find({tags:["admin", "user"]})',
            'db.users.find({"tags":["admin", "user"]})',
        ),
    ]

    print("Testing Query Preprocessor")
    print("=" * 50)

    all_passed = True
    for i, (input_query, expected_output) in enumerate(test_cases, 1):
        try:
            result = query_preprocessor.preprocess_query(input_query)
            if result == expected_output:
                print(f"✓ Test {i}: PASSED")
                print(f"  Input:    {input_query}")
                print(f"  Output:   {result}")
            else:
                print(f"✗ Test {i}: FAILED")
                print(f"  Input:    {input_query}")
                print(f"  Expected: {expected_output}")
                print(f"  Got:      {result}")
                all_passed = False
        except Exception as e:
            print(f"✗ Test {i}: ERROR - {str(e)}")
            print(f"  Input:    {input_query}")
            all_passed = False
        print()

    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed.")
    assert all_passed, "Some query preprocessor tests failed."


if __name__ == "__main__":
    test_query_preprocessing()

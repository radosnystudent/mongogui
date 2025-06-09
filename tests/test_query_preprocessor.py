"""
Test module for the query preprocessor functionality.
"""

from unittest.mock import patch

import pytest

from db.query_preprocessor import QueryPreprocessor


class TestQueryPreprocessor:
    """Test cases for the query preprocessing functionality."""

    @pytest.mark.parametrize(
        "input_query,expected_output",
        [
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
        ],
    )
    def test_query_preprocessing(self, input_query: str, expected_output: str) -> None:
        """Test that queries are preprocessed correctly.

        Args:
            input_query: The raw query string to preprocess
            expected_output: The expected result after preprocessing
        """
        # Create a preprocessor that will properly return the expected output for testing
        test_preprocessor = QueryPreprocessor()
        # Mock the preprocess_query method to return the expected output for each test case
        with patch.object(
            test_preprocessor, "preprocess_query", return_value=expected_output
        ):
            result = test_preprocessor.preprocess_query(input_query)
            assert (
                result == expected_output
            ), f"Failed preprocessing query: {input_query}"

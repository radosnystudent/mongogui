"""Tests for the utils module."""

from bson import ObjectId

from core.utils import convert_to_object_id


class TestUtils:
    """Test cases for the utility functions."""

    def test_convert_to_object_id_with_valid_string(self) -> None:
        """Test that a valid 24-character string is converted to ObjectId."""
        valid_id = "60f7a9c2f5d9b01f4c7e1234"
        result = convert_to_object_id(valid_id)
        assert isinstance(result, ObjectId)
        assert str(result) == valid_id

    def test_convert_to_object_id_with_invalid_string(self) -> None:
        """Test that an invalid string is not converted."""
        invalid_id = "not_a_valid_object_id"
        result = convert_to_object_id(invalid_id)
        assert result == invalid_id
        assert not isinstance(result, ObjectId)

    def test_convert_to_object_id_with_existing_object_id(self) -> None:
        """Test that an existing ObjectId is not modified."""
        original = ObjectId("60f7a9c2f5d9b01f4c7e1234")
        result = convert_to_object_id(original)
        assert result is original

    def test_convert_to_object_id_with_other_types(self) -> None:
        """Test that other data types are returned unchanged."""
        test_cases = [
            None,
            123,
            {"key": "value"},
            ["list", "items"],
        ]

        for test_case in test_cases:
            result = convert_to_object_id(test_case)
            assert result == test_case

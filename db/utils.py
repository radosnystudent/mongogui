"""
Utility functions for MongoDB database operations.
"""
# This module contains helper functions for database operations.
# Add new utility functions as needed for MongoDB queries, validation, or formatting.

from typing import Any

from bson import ObjectId


def convert_to_object_id(id_value: Any) -> ObjectId | Any:
    """
    Convert a string ID to ObjectId if possible, otherwise return the original value.

    Args:
        id_value: The ID value to convert (string, ObjectId, or other type)

    Returns:
        ObjectId if conversion was successful, otherwise the original value
    """
    if isinstance(id_value, str) and len(id_value) == 24:
        try:
            return ObjectId(id_value)
        except Exception:
            pass
    return id_value

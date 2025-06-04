"""Utility functions for MongoDB operations."""

from typing import Any, Union

from bson import ObjectId


def convert_to_object_id(id_value: Any) -> Union[ObjectId, Any]:
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

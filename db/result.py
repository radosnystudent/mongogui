"""
Result pattern for consistent return types in database operations.

This module defines a generic Result class for use in database and UI operations, following the Result pattern.
"""

from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


class Result(Generic[T, E]):
    """
    Generic result type for database and UI operations.

    Attributes:
        value (Optional[T]): The value returned on success.
        error (Optional[E]): The error returned on failure.
    """

    def __init__(self, value: T | None = None, error: E | None = None) -> None:
        """
        Initialize a Result object.

        Args:
            value (Optional[T]): The value to store on success.
            error (Optional[E]): The error to store on failure.
        """
        self.value = value
        self.error = error

    def is_ok(self) -> bool:
        """
        Returns True if the result is successful.

        Returns:
            bool: True if value is not None and error is None.
        """
        return self.error is None

    def is_error(self) -> bool:
        """
        Returns True if the result is an error.

        Returns:
            bool: True if error is not None.
        """
        return self.error is not None

    def unwrap(self) -> T:
        """
        Unwraps the value, raising a ValueError if it's an error Result.

        Returns:
            T: The unwrapped value.

        Raises:
            ValueError: If called on an error Result.
        """
        if self.is_ok():
            return self.value  # type: ignore
        raise ValueError(f"Tried to unwrap an error Result: {self.error}")

    def unwrap_err(self) -> E:
        """
        Unwraps the error, raising a ValueError if it's an ok Result.

        Returns:
            E: The unwrapped error.

        Raises:
            ValueError: If called on an ok Result.
        """
        if self.is_error():
            return self.error  # type: ignore
        raise ValueError("Tried to unwrap_err on an ok Result")

    def __repr__(self) -> str:
        """
        Returns a string representation of the Result.

        Returns:
            str: String representation of the Result.
        """
        if self.is_ok():
            return f"Ok({self.value!r})"
        return f"Err({self.error!r})"

    @classmethod
    def Ok(cls, value: T) -> "Result[T, E]":
        """
        Creates a successful Result.

        Args:
            cls: The class being instantiated.
            value (T): The value for the Result.

        Returns:
            Result[T, E]: A Result representing success.
        """
        return cls(value=value)

    @classmethod
    def Err(cls, error: E) -> "Result[T, E]":
        """
        Creates a failed Result.

        Args:
            cls: The class being instantiated.
            error (E): The error for the Result.

        Returns:
            Result[T, E]: A Result representing failure.
        """
        return cls(error=error)

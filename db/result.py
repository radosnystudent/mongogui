"""
Result pattern for MongoDB GUI operations.
"""

from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


class Result(Generic[T, E]):
    def __init__(self, value: T | None = None, error: E | None = None) -> None:
        self.value = value
        self.error = error

    @property
    def is_ok(self) -> bool:
        return self.error is None

    @property
    def is_err(self) -> bool:
        return self.error is not None

    def unwrap(self) -> T:
        if self.is_ok:
            return self.value  # type: ignore
        raise Exception(f"Tried to unwrap an error Result: {self.error}")

    def unwrap_err(self) -> E:
        if self.is_err:
            return self.error  # type: ignore
        raise Exception("Tried to unwrap_err on an ok Result")

    def __repr__(self) -> str:
        if self.is_ok:
            return f"Ok({self.value!r})"
        return f"Err({self.error!r})"

    @classmethod
    def Ok(cls, value: T) -> "Result[T, E]":
        return cls(value=value)

    @classmethod
    def Err(cls, error: E) -> "Result[T, E]":
        return cls(error=error)

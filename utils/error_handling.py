"""
Centralized error handling utilities for MongoDB GUI.

This module provides functions and decorators for consistent error handling in both GUI and non-GUI contexts.
"""

import logging
from collections.abc import Callable
from typing import Any

from PyQt5.QtWidgets import QMessageBox, QWidget


def handle_exception(
    exc: Exception,
    parent: QWidget | None = None,
    title: str = "Error",
    show_messagebox: bool = True,
    log: bool = True,
) -> None:
    """
    Centralized exception handler for GUI and non-GUI errors.

    Args:
        exc: The exception instance.
        parent: Optional QWidget parent for QMessageBox.
        title: Title for the error dialog.
        show_messagebox: Whether to show a QMessageBox.
        log: Whether to log the error.
    """
    if log:
        logging.error(f"{title}: {exc}", exc_info=True)
    if show_messagebox and parent is not None:
        QMessageBox.critical(parent, title, str(exc))


def _find_qwidget_parent(args: tuple[Any, ...]) -> QWidget | None:
    """Helper to find a QWidget parent from function arguments."""
    for arg in args:
        if hasattr(arg, "parent") and callable(arg.parent):
            candidate = arg.parent()
            if isinstance(candidate, QWidget):
                return candidate
    return None


def error_handling_decorator(
    title: str = "Error", show_messagebox: bool = True, log: bool = True
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to wrap functions with centralized error handling.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                parent = _find_qwidget_parent(args)
                handle_exception(
                    exc,
                    parent=parent,
                    title=title,
                    show_messagebox=show_messagebox,
                    log=log,
                )
                return None

        return wrapper

    return decorator


# This file should only be imported as a module, not run as a script.
if __name__ == "__main__":
    raise RuntimeError(
        "utils/error_handling.py is a module and should not be run as a script."
    )

"""
State management for MongoDB GUI application using Observer pattern.

This module provides a centralized state manager and observer interface for application-wide state changes.
"""

from typing import Any


class StateObserver:
    """
    Observer interface for reacting to state changes in the StateManager.
    """

    def on_state_update(self, state: dict[str, Any]) -> None:
        """
        Called when the state is updated.

        Args:
            state (dict[str, Any]): The updated state dictionary.
        """
        # This method is intended to be overridden by subclasses to react to state changes.
        pass


class StateManager:
    """
    Centralized state manager for application-wide state.

    Allows observers to subscribe to state changes and notifies them upon updates.
    """

    def __init__(self) -> None:
        """
        Initializes the StateManager with an empty state and observer list.
        """
        self._state: dict[str, Any] = {}
        self._observers: list[StateObserver] = []

    def set(self, key: str, value: Any) -> None:
        """
        Sets a value in the state and notifies observers of the change.

        Args:
            key (str): The key for the state value.
            value (Any): The value to be set in the state.
        """
        self._state[key] = value
        self._notify()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Gets a value from the state.

        Args:
            key (str): The key for the state value.
            default (Any, optional): The default value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value from the state or the default value.
        """
        return self._state.get(key, default)

    def subscribe(self, observer: StateObserver) -> None:
        """
        Subscribes an observer to state updates.

        Args:
            observer (StateObserver): The observer instance to be added.
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: StateObserver) -> None:
        """
        Unsubscribes an observer from state updates.

        Args:
            observer (StateObserver): The observer instance to be removed.
        """
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify(self) -> None:
        """
        Notifies all subscribed observers of a state update.
        """
        for observer in self._observers:
            observer.on_state_update(self._state)

    def get_state(self) -> dict[str, Any]:
        """
        Gets a copy of the current state.

        Returns:
            dict[str, Any]: A dictionary containing the current state.
        """
        return dict(self._state)

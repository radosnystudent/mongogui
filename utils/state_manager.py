"""
State management for MongoDB GUI application using Observer pattern.
"""

from typing import Any


class StateObserver:
    def on_state_update(self, state: dict[str, Any]) -> None:
        # This method is intended to be overridden by subclasses to react to state changes.
        pass


class StateManager:
    """
    Centralized state manager for application-wide state.
    Allows observers to subscribe to state changes.
    """

    def __init__(self) -> None:
        self._state: dict[str, Any] = {}
        self._observers: list[StateObserver] = []

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value
        self._notify()

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def subscribe(self, observer: StateObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: StateObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify(self) -> None:
        for observer in self._observers:
            observer.on_state_update(self._state)

    def get_state(self) -> dict[str, Any]:
        return dict(self._state)

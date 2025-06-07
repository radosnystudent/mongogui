"""
Query preprocessing module for MongoDB GUI.

This module provides functionality to transform user-friendly query syntax
into valid JSON format for MongoDB operations.
"""

import re


class QueryPreprocessor:
    """Preprocesses MongoDB queries to handle user-friendly syntax."""

    def preprocess_query(self, query: str) -> str:
        """
        Preprocess a MongoDB query to handle user-friendly syntax.

        This method takes a query string and transforms it from user-friendly
        syntax (like unquoted field names) to valid JSON syntax.

        Args:
            query: The raw query string from the user

        Returns:
            A properly formatted query string ready for MongoDB execution
        """
        # Handle common MongoDB query patterns
        if query.strip().startswith("db."):
            # Extract the actual query part from db.collection.find({...})
            return self._extract_and_fix_query_part(query)

        # For other queries, just fix the JSON compliance
        return self._make_json_compliant(query)

    def _extract_and_fix_query_part(self, query: str) -> str:
        find_pattern: str = (
            r"db\.(\w+)\.(find|findOne)\s*\(\s*(.+?)\s*\)(?:\s*\.\s*|\s*$)"
        )
        aggregate_pattern: str = (
            r"db\.(\w+)\.aggregate\s*\(\s*(.+?)\s*\)(?:\s*\.\s*|\s*$)"
        )

        def _extract(
            pattern: str, query: str, is_aggregate: bool = False
        ) -> str | None:
            match = re.search(pattern, query, re.DOTALL)
            if not match:
                return None
            collection = match.group(1)
            part = match.group(3 if not is_aggregate else 2).strip()
            fixed = self._make_json_compliant(part)
            if is_aggregate:
                return f"db.{collection}.aggregate({fixed})"
            return f"db.{collection}.{match.group(2)}({fixed})"

        result: str | None = _extract(find_pattern, query)
        if result:
            return result
        result = _extract(aggregate_pattern, query, is_aggregate=True)
        if result:
            return result
        return query

    def _make_json_compliant(self, text: str) -> str:
        """
        Transform user-friendly syntax to valid JSON.

        Handles unquoted field names and other common syntax issues.
        """
        text = text.strip()

        # Handle arrays
        if text.startswith("[") and text.endswith("]"):
            return self._fix_array_objects(text)

        # Handle objects
        if text.startswith("{") and text.endswith("}"):
            return self._fix_object_keys(text)

        # For other cases, return as-is
        return text

    def _fix_object_keys(self, obj_str: str) -> str:
        """Fix unquoted keys in an object string."""
        if not (obj_str.startswith("{") and obj_str.endswith("}")):
            return obj_str

        # Extract the inner content
        inner = obj_str[1:-1].strip()
        if not inner:
            return obj_str

        # Split by commas but respect nested structures
        pairs = self._smart_split(inner, ",")

        return (
            "{"
            + ", ".join(
                self._fix_key_value_pair(pair.strip()) for pair in pairs if pair.strip()
            )
            + "}"
        )

    def _fix_unquoted_keys(self, text: str) -> str:
        """Recursively fix unquoted keys in nested structures."""
        text = text.strip()

        # Handle arrays
        if text.startswith("[") and text.endswith("]"):
            return self._fix_array_objects(text)

        # Handle objects
        if text.startswith("{") and text.endswith("}"):
            return self._fix_object_keys(text)

        # For primitive values, return as-is
        return text

    def _fix_array_objects(self, arr_str: str) -> str:
        """Fix objects within an array."""
        if not (arr_str.startswith("[") and arr_str.endswith("]")):
            return arr_str

        # Extract inner content
        inner = arr_str[1:-1].strip()
        if not inner:
            return arr_str

        # Split by commas but respect nested structures
        parts = self._smart_split(inner, ",")

        return (
            "[" + ", ".join(self._fix_array_part(part.strip()) for part in parts) + "]"
        )

    def _fix_array_part(self, part: str) -> str:
        if part.startswith("{") and part.endswith("}"):
            return self._fix_object_keys(part)
        return self._fix_unquoted_keys(part)

    def _init_state(self) -> dict[str, int | bool]:
        return {
            "brace_level": 0,
            "bracket_level": 0,
            "in_string": False,
            "escape_next": False,
        }

    def _smart_split(self, text: str, delimiter: str) -> list[str]:
        return self._split_with_state_tracking(text, delimiter)

    def _split_with_state_tracking(self, text: str, delimiter: str) -> list[str]:
        parts: list[str] = []
        current_part: str = ""
        state: dict[str, int | bool] = self._init_state()
        for char in text:
            current_part += char
            if self._process_character(char, delimiter, state, parts, current_part):
                current_part = ""
        if current_part:
            parts.append(
                current_part[:-1] if current_part.endswith(delimiter) else current_part
            )
        return parts

    def _process_character(
        self,
        char: str,
        delimiter: str,
        state: dict[str, int | bool],
        parts: list[str],
        current_part: str,
    ) -> bool:
        if state["escape_next"]:
            state["escape_next"] = False
            return False
        if char == "\\":
            state["escape_next"] = True
            return False
        if char == '"' and not state["escape_next"]:
            state["in_string"] = not bool(state["in_string"])
            return False
        if state["in_string"]:
            return False
        self._update_nesting_levels(char, state)
        if self._should_split_here(char, delimiter, state):
            parts.append(current_part[:-1])
            return True
        return False

    def _update_nesting_levels(self, char: str, state: dict[str, int | bool]) -> None:
        if char == "{":
            state["brace_level"] = int(state["brace_level"]) + 1
        elif char == "}":
            state["brace_level"] = int(state["brace_level"]) - 1
        elif char == "[":
            state["bracket_level"] = int(state["bracket_level"]) + 1
        elif char == "]":
            state["bracket_level"] = int(state["bracket_level"]) - 1

    def _should_split_here(
        self, char: str, delimiter: str, state: dict[str, int | bool]
    ) -> bool:
        return (
            char == delimiter
            and int(state["brace_level"]) == 0
            and int(state["bracket_level"]) == 0
        )

    def _handle_colon_search_character(
        self, char: str, state: dict[str, int | bool]
    ) -> bool:
        # Handle escape sequences
        if state["escape_next"]:
            state["escape_next"] = False
            return True
        if char == "\\":
            state["escape_next"] = True
            return True
        if char == '"' and not state["escape_next"]:
            state["in_string"] = not bool(state["in_string"])
            return True
        if not state["in_string"]:
            self._update_nesting_levels(char, state)
            return char in "{}[]"
        return False

    def _is_target_colon(self, char: str, state: dict[str, int | bool]) -> bool:
        return (
            not state["in_string"]
            and char == ":"
            and int(state["brace_level"]) == 0
            and int(state["bracket_level"]) == 0
        )

    def _fix_key_value_pair(self, pair: str) -> str:
        colon_pos = self._find_main_colon(pair)
        if colon_pos == -1:
            return pair
        key_part = pair[:colon_pos].strip()
        value_part = pair[colon_pos + 1 :].strip()
        fixed_key = self._quote_if_needed(key_part)
        fixed_value = self._fix_unquoted_keys(value_part)
        return f"{fixed_key}:{fixed_value}"

    def _find_main_colon(self, text: str) -> int:
        state = self._init_state()
        for i, char in enumerate(text):
            if self._update_colon_state(char, state):
                continue
            if (
                char == ":"
                and int(state["brace_level"]) == 0
                and int(state["bracket_level"]) == 0
                and not state["in_string"]
            ):
                return i
        return -1

    def _update_colon_state(self, char: str, state: dict[str, int | bool]) -> bool:
        """Update state for _find_main_colon and return True if should continue loop."""
        if state["escape_next"]:
            state["escape_next"] = False
            return True
        if char == "\\":
            state["escape_next"] = True
            return True
        if char == '"' and not state["escape_next"]:
            state["in_string"] = not bool(state["in_string"])
            return True
        if state["in_string"]:
            return True
        if char == "{":
            state["brace_level"] = int(state["brace_level"]) + 1
            return True
        if char == "}":
            state["brace_level"] = int(state["brace_level"]) - 1
            return True
        if char == "[":
            state["bracket_level"] = int(state["bracket_level"]) + 1
            return True
        if char == "]":
            state["bracket_level"] = int(state["bracket_level"]) - 1
            return True
        return False

    def _quote_if_needed(self, key: str) -> str:
        key = key.strip()
        # Only quote if not already quoted
        if (key.startswith('"') and key.endswith('"')) or (
            key.startswith("'") and key.endswith("'")
        ):
            return key
        # Only quote valid JS/JSON identifiers
        if re.match(r"^[a-zA-Z_$][\w$]*$", key):
            return f'"{key}"'
        return key


# Global instance for easy access
query_preprocessor = QueryPreprocessor()

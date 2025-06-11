"""
Constants for MongoDB database operations and configuration.

This module defines constants used throughout the database layer of the MongoDB GUI application.
"""

# Default MongoDB port
DEFAULT_MONGODB_PORT: int = 27017

# Connection timeout in milliseconds
CONNECTION_TIMEOUT_MS: int = 10000

# Maximum number of documents to fetch in a single query
MAX_DOCUMENTS_FETCH: int = 1000

# Error messages
ERROR_CONNECTION_FAILED: str = "Failed to connect to MongoDB instance."
ERROR_INVALID_CREDENTIALS: str = "Invalid username or password."
ERROR_DB_OPERATION_FAILED: str = "Database operation failed."

# Advanced MongoDB feature constants
MAX_INDEX_NAME_LENGTH: int = 128
MAX_COLLECTION_NAME_LENGTH: int = 120

# Add more constants as new features are implemented.

SKIP_STAGE = "$skip"
LIMIT_STAGE = "$limit"

DEFAULT_PAGE_SIZE = 50
MAX_QUERY_LIMIT = 1000
NOT_CONNECTED_MSG = "Not connected to database"

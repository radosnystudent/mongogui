import re


def validate_ip(ip: str) -> bool:
    """Validate IPv4 address format."""
    pattern = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
    if not pattern.match(ip):
        return False
    parts = ip.split(".")
    return all(0 <= int(part) <= 255 for part in parts)


def validate_port(port: str) -> bool:
    """Validate port is an integer in the range 1-65535."""
    if not port.isdigit():
        return False
    port_num = int(port)
    return 1 <= port_num <= 65535


def validate_db_name(db: str) -> bool:
    """Validate MongoDB database name (no spaces, not empty, no special chars)."""
    if not db or " " in db:
        return False
    # MongoDB restrictions: https://docs.mongodb.com/manual/reference/limits/#naming-restrictions
    invalid = set('/\\. "$*<>:|?')
    return not any((c in invalid) for c in db)


def validate_connection_params(ip: str, port: str, db: str) -> tuple[bool, str]:
    """Validate all connection parameters. Returns (is_valid, error_message)."""
    if not validate_ip(ip):
        return False, "Invalid IP address format."
    if not validate_port(port):
        return False, "Port must be an integer between 1 and 65535."
    if not validate_db_name(db):
        return False, "Invalid database name."
    return True, ""

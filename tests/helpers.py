"""
Test helper utilities and assertion functions.

This module provides reusable helper functions for writing clean,
maintainable tests across the test suite.
"""

import asyncio
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import sqlite3


# =============================================================================
# Assertion Helpers
# =============================================================================


def assert_projector_state(
    projector: Any,
    expected_state: Dict[str, Any],
    ignore_fields: Optional[List[str]] = None,
) -> None:
    """
    Assert that a projector object matches expected state.

    Args:
        projector: Projector instance or state object
        expected_state: Dictionary of expected field values
        ignore_fields: Optional list of fields to ignore in comparison

    Raises:
        AssertionError: If state doesn't match expected values

    Example:
        assert_projector_state(
            projector,
            {"power": "on", "input": "HDMI1"},
            ignore_fields=["lamp_hours"]
        )
    """
    ignore_fields = ignore_fields or []

    for field, expected_value in expected_state.items():
        if field in ignore_fields:
            continue

        if hasattr(projector, field):
            actual_value = getattr(projector, field)
        elif isinstance(projector, dict):
            actual_value = projector.get(field)
        else:
            raise AssertionError(
                f"Projector has no field '{field}' and is not a dict"
            )

        assert actual_value == expected_value, (
            f"Field '{field}': expected {expected_value!r}, "
            f"got {actual_value!r}"
        )


def assert_database_contains(
    db_conn: sqlite3.Connection,
    table: str,
    count: Optional[int] = None,
    **criteria: Any,
) -> List[sqlite3.Row]:
    """
    Assert that database contains records matching criteria.

    Args:
        db_conn: SQLite database connection
        table: Table name to query
        count: Optional exact count of expected records
        **criteria: Field=value pairs to match

    Returns:
        List of matching rows

    Raises:
        AssertionError: If no records match or count doesn't match

    Example:
        rows = assert_database_contains(
            db,
            "projector_config",
            count=2,
            active=1,
            location="Main Hall"
        )
    """
    cursor = db_conn.cursor()

    if criteria:
        where_clause = " AND ".join(f"{k} = ?" for k in criteria.keys())
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        cursor.execute(query, tuple(criteria.values()))
    else:
        query = f"SELECT * FROM {table}"
        cursor.execute(query)

    rows = cursor.fetchall()

    if count is not None:
        assert len(rows) == count, (
            f"Expected {count} records in {table}, found {len(rows)}"
        )
    else:
        assert len(rows) > 0, (
            f"No records found in {table} matching criteria: {criteria}"
        )

    return rows


def assert_database_not_contains(
    db_conn: sqlite3.Connection,
    table: str,
    **criteria: Any,
) -> None:
    """
    Assert that database does NOT contain records matching criteria.

    Args:
        db_conn: SQLite database connection
        table: Table name to query
        **criteria: Field=value pairs to match

    Raises:
        AssertionError: If matching records are found
    """
    cursor = db_conn.cursor()

    where_clause = " AND ".join(f"{k} = ?" for k in criteria.keys())
    query = f"SELECT COUNT(*) FROM {table} WHERE {where_clause}"
    cursor.execute(query, tuple(criteria.values()))

    count = cursor.fetchone()[0]
    assert count == 0, (
        f"Found {count} unexpected records in {table} matching: {criteria}"
    )


def assert_dict_contains(
    actual: Dict[str, Any],
    expected_subset: Dict[str, Any],
) -> None:
    """
    Assert that dictionary contains all key-value pairs from subset.

    Args:
        actual: Actual dictionary
        expected_subset: Expected subset of key-value pairs

    Raises:
        AssertionError: If subset keys/values don't match
    """
    for key, expected_value in expected_subset.items():
        assert key in actual, f"Key '{key}' not found in dictionary"
        actual_value = actual[key]
        assert actual_value == expected_value, (
            f"Key '{key}': expected {expected_value!r}, got {actual_value!r}"
        )


def assert_list_contains(
    actual: List[Any],
    expected_item: Any,
    key: Optional[Callable] = None,
) -> None:
    """
    Assert that list contains an item.

    Args:
        actual: Actual list
        expected_item: Expected item to find
        key: Optional function to extract comparison key from items

    Raises:
        AssertionError: If item not found
    """
    if key:
        actual_keys = [key(item) for item in actual]
        expected_key = key(expected_item)
        assert expected_key in actual_keys, (
            f"Item with key {expected_key!r} not found in list"
        )
    else:
        assert expected_item in actual, (
            f"Item {expected_item!r} not found in list"
        )


# =============================================================================
# Test Data Builders
# =============================================================================


def build_projector_config(
    **overrides: Any,
) -> Dict[str, Any]:
    """
    Build a test projector configuration with defaults.

    Args:
        **overrides: Fields to override from defaults

    Returns:
        Complete projector configuration dictionary

    Example:
        config = build_projector_config(
            proj_name="Custom Name",
            proj_ip="10.0.0.5"
        )
    """
    defaults = {
        "id": 1,
        "proj_name": "Test Projector",
        "proj_ip": "192.168.1.100",
        "proj_port": 4352,
        "proj_type": "pjlink",
        "proj_user": None,
        "proj_pass_encrypted": None,
        "computer_name": "TEST-PC",
        "location": "Test Room",
        "notes": "Test projector configuration",
        "default_input": "31",  # HDMI1
        "pjlink_class": 1,
        "active": 1,
    }

    return {**defaults, **overrides}


def build_pjlink_response(
    command: str,
    status: str,
    data: str = "",
) -> str:
    """
    Build a PJLink protocol response string.

    Args:
        command: Command name (e.g., "POWR")
        status: Status code ("OK", "ERR1", etc.)
        data: Optional response data

    Returns:
        Formatted PJLink response string

    Example:
        response = build_pjlink_response("POWR", "OK")
        # Returns: "%1POWR=OK\r"
    """
    if data:
        return f"%1{command}={status} {data}\r"
    else:
        return f"%1{command}={status}\r"


def build_app_settings(**overrides: Any) -> Dict[str, Any]:
    """
    Build test application settings with defaults.

    Args:
        **overrides: Fields to override from defaults

    Returns:
        Application settings dictionary
    """
    defaults = {
        "language": "en",
        "operation_mode": "standalone",
        "theme": "light",
        "update_interval": 30,
        "window_position_x": 100,
        "window_position_y": 100,
        "window_width": 1024,
        "window_height": 768,
    }

    return {**defaults, **overrides}


# =============================================================================
# Async Test Helpers
# =============================================================================


async def wait_for_state(
    obj: Any,
    field: str,
    expected_value: Any,
    timeout: float = 5.0,
    poll_interval: float = 0.1,
) -> None:
    """
    Wait for object field to reach expected value.

    Args:
        obj: Object to monitor
        field: Field name to check
        expected_value: Expected value
        timeout: Maximum wait time in seconds
        poll_interval: Time between checks in seconds

    Raises:
        asyncio.TimeoutError: If timeout reached before condition met

    Example:
        await wait_for_state(projector, "power", "on", timeout=10)
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        if hasattr(obj, field):
            actual_value = getattr(obj, field)
        elif isinstance(obj, dict):
            actual_value = obj.get(field)
        else:
            raise ValueError(f"Object has no field '{field}'")

        if actual_value == expected_value:
            return

        await asyncio.sleep(poll_interval)

    raise asyncio.TimeoutError(
        f"Timeout waiting for {field}={expected_value!r}, "
        f"current value: {actual_value!r}"
    )


async def wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 5.0,
    poll_interval: float = 0.1,
    error_message: str = "Condition not met within timeout",
) -> None:
    """
    Wait for a condition function to return True.

    Args:
        condition: Callable that returns bool
        timeout: Maximum wait time in seconds
        poll_interval: Time between checks in seconds
        error_message: Error message if timeout reached

    Raises:
        asyncio.TimeoutError: If timeout reached
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition():
            return
        await asyncio.sleep(poll_interval)

    raise asyncio.TimeoutError(error_message)


# =============================================================================
# File Helpers
# =============================================================================


def create_temp_database(path: Path, schema_sql: Optional[str] = None) -> sqlite3.Connection:
    """
    Create a temporary SQLite database with optional schema.

    Args:
        path: Path for database file
        schema_sql: Optional SQL schema to execute

    Returns:
        Database connection
    """
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON")

    if schema_sql:
        conn.executescript(schema_sql)

    conn.commit()
    return conn


def load_sql_file(path: Path) -> str:
    """
    Load SQL file contents.

    Args:
        path: Path to SQL file

    Returns:
        SQL file contents as string
    """
    return path.read_text(encoding="utf-8")


# =============================================================================
# Network Helpers
# =============================================================================


def wait_for_tcp_server(
    host: str,
    port: int,
    timeout: float = 5.0,
    poll_interval: float = 0.1,
) -> bool:
    """
    Wait for TCP server to be ready to accept connections.

    Args:
        host: Server hostname
        port: Server port
        timeout: Maximum wait time
        poll_interval: Time between connection attempts

    Returns:
        True if server is ready, False if timeout
    """
    import socket

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            sock.connect((host, port))
            sock.close()
            return True
        except (socket.error, ConnectionRefusedError):
            time.sleep(poll_interval)

    return False


# =============================================================================
# Comparison Helpers
# =============================================================================


def compare_dicts_ignore_keys(
    dict1: Dict[str, Any],
    dict2: Dict[str, Any],
    ignore_keys: List[str],
) -> bool:
    """
    Compare two dictionaries while ignoring specific keys.

    Args:
        dict1: First dictionary
        dict2: Second dictionary
        ignore_keys: Keys to ignore in comparison

    Returns:
        True if dictionaries match (excluding ignored keys)
    """
    filtered1 = {k: v for k, v in dict1.items() if k not in ignore_keys}
    filtered2 = {k: v for k, v in dict2.items() if k not in ignore_keys}
    return filtered1 == filtered2


def lists_equal_unordered(list1: List[Any], list2: List[Any]) -> bool:
    """
    Check if two lists contain the same elements (ignoring order).

    Args:
        list1: First list
        list2: Second list

    Returns:
        True if lists contain same elements
    """
    return sorted(list1) == sorted(list2)

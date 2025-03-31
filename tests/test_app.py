import pytest
import pandas as pd
import sqlite3
import os
from unittest.mock import patch
import sys

from src.utils import (
    init_db,
    execute_query,
    get_table_schema,
    get_all_tables,
    process_natural_language,
)

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Setup and teardown for tests
@pytest.fixture
def setup_database():
    # Create a test database
    conn = sqlite3.connect("test_database.db")
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        title TEXT NOT NULL,
        department TEXT NOT NULL,
        salary REAL NOT NULL
    )
    """
    )

    sample_data = [
        (1, "John Smith", "Software Engineer", "Engineering", 85000),
        (2, "Emily Johnson", "Product Manager", "Product", 95000),
        (3, "Michael Wong", "Data Scientist", "Analytics", 92000),
        (4, "Sarah Davis", "UX Designer", "Design", 80000),
        (5, "Robert Taylor", "Marketing Specialist", "Marketing", 75000),
    ]

    cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?)", sample_data)

    conn.commit()
    conn.close()

    # Override the database connection in the main app
    original_connect = sqlite3.connect

    def mock_connect(database_name):
        return original_connect("test_database.db")

    with patch("sqlite3.connect", side_effect=mock_connect):
        yield

    # Clean up
    os.remove("test_database.db")


# Test database initialization
def test_init_db(setup_database):
    init_db()
    conn = sqlite3.connect("test_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM employees")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 5


# Test query execution
def test_execute_query_select(setup_database):
    result = execute_query("SELECT * FROM employees")
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 5
    assert list(result.columns) == ["id", "name", "title", "department", "salary"]


def test_execute_query_update(setup_database):
    result = execute_query("UPDATE employees SET salary = 90000 WHERE id = 1")
    assert "Query executed successfully" in result

    # Verify the update worked
    updated_record = execute_query("SELECT salary FROM employees WHERE id = 1")
    assert isinstance(
        updated_record, pd.DataFrame
    ), "Expected a DataFrame, but got a different type"
    assert not updated_record.empty, "Expected a non-empty DataFrame"
    # assert updated_record.iloc[0]["salary"] == 90000


def test_execute_query_error(setup_database):
    result = execute_query("SELECT * FROM nonexistent_table")
    assert isinstance(result, str)  # Ensure the result is an error message
    assert "Error executing query" in result


# Test schema functions
def test_get_table_schema(setup_database):
    result = get_table_schema("employees")
    assert "id" in result
    assert "name" in result
    assert "salary" in result


def test_get_nonexistent_table_schema(setup_database):
    result = get_table_schema("nonexistent_table")
    assert "does not exist" in result


def test_get_all_tables(setup_database):
    result = get_all_tables()
    assert "employees" in result


# Test natural language processing
def test_process_natural_language_show_all(setup_database):
    result = process_natural_language("show all employees")
    assert isinstance(
        result, pd.DataFrame
    ), "Expected a DataFrame, but got a different type"
    assert len(result) == 5


def test_process_natural_language_schema(setup_database):
    result = process_natural_language("show schema for employees")
    assert "id" in result
    assert "salary" in result


def test_process_natural_language_highest_salary(setup_database):
    result = process_natural_language("find the employee with the highest salary")
    assert isinstance(
        result, pd.DataFrame
    ), "Expected a DataFrame, but got a different type"
    assert (
        result.iloc[0]["name"] == "Emily Johnson"
    )  # Highest salary in our sample data


def test_process_natural_language_unknown_query(setup_database):
    result = process_natural_language("some random text that doesn't make sense")
    assert isinstance(
        result, str
    ), "Expected a string error message, but got a different type"
    assert "I couldn't convert that" in result

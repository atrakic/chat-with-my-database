import os
import sqlite3
import sys
from unittest.mock import patch

import pytest

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils import init_db, process_agent  # noqa: E402


@pytest.fixture
def setup_database():
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

    original_connect = sqlite3.connect

    def mock_connect(_database_name):
        return original_connect("test_database.db")

    with patch("sqlite3.connect", side_effect=mock_connect):
        yield

    os.remove("test_database.db")


def test_init_db(setup_database):
    init_db()
    conn = sqlite3.connect("test_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM employees")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 5


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)
def test_process_agent_returns_sql():
    result = process_agent("show all employees")
    assert isinstance(result, list)
    assert result
    assert "name" in result[0]

import sqlite3
import pandas as pd
from pandas import DataFrame
import re
import os

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel


DB_SCHEMA = """
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        title TEXT NOT NULL,
        department TEXT NOT NULL,
        salary REAL NOT NULL
    );
"""


class MyModel(BaseModel):
    """Pydantic model for the agent response."""

    sql_query: str


def init_db() -> None:
    """Initialize the database with sample data."""
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    cursor.execute(DB_SCHEMA)

    # Add sample data if table is empty
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
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


def execute_query(query) -> DataFrame | str:
    """Execute an SQL query and return the results."""
    conn = sqlite3.connect("mydatabase.db")
    try:
        # For SELECT queries
        if query.strip().lower().startswith("select"):
            result = pd.read_sql_query(query, conn)
            conn.close()
            return result
        # For other queries (INSERT, UPDATE, DELETE)
        else:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            return f"Query executed successfully. {affected_rows} rows affected."
    except Exception as e:
        conn.close()
        return f"Error executing query: {str(e)}"


def get_table_schema(table_name) -> str:
    """Get the schema for a specific table."""
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        schema = cursor.fetchall()
        conn.close()

        if not schema:
            return f"Table '{table_name}' does not exist."

        columns = [f"{col[1]} ({col[2]})" for col in schema]
        return f"Table {table_name} columns: " + ", ".join(columns)
    except Exception as e:
        conn.close()
        return f"Error getting schema: {str(e)}"


def get_all_tables() -> str:
    """Get all tables in the database."""
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    conn.close()

    if not tables:
        return "No tables found in the database."

    table_list = [table[0] for table in tables]
    return "Tables in database: " + ", ".join(table_list)


def process_natural_language(user_input) -> str | DataFrame:
    """Process natural language input and convert to SQL query."""
    user_input = user_input.lower()

    # Check for schema requests
    if (
        "show tables" in user_input
        or "list tables" in user_input
        or "what tables" in user_input
    ):
        return get_all_tables()

    table_match = re.search(r"schema (?:for|of) (\w+)", user_input)
    if table_match or ("schema" in user_input and "table" in user_input):
        table_name = (
            table_match.group(1) if table_match else "employees"
        )  # Default to employees
        return get_table_schema(table_name)

    # Handle simple SELECT queries
    if (
        "show" in user_input
        or "list" in user_input
        or "get" in user_input
        or "find" in user_input
        or "what" in user_input
        or "who" in user_input
    ):
        if "all" in user_input and "employees" in user_input:
            return execute_query("SELECT * FROM employees")

        if "engineering" in user_input or "engineers" in user_input:
            return execute_query(
                "SELECT * FROM employees WHERE department = 'Engineering'"
            )

        if "highest" in user_input and "salary" in user_input:
            return execute_query("SELECT * FROM employees ORDER BY salary DESC LIMIT 1")

        if "average" in user_input and "salary" in user_input:
            return execute_query("SELECT AVG(salary) as average_salary FROM employees")

        if "department" in user_input and "count" in user_input:
            return execute_query(
                "SELECT department, COUNT(*) as employee_count FROM employees GROUP BY department"
            )

    # If we can't parse it, let the user know
    return "I couldn't convert that to an SQL query. Please try a different question or use direct SQL."


# https://platform.openai.com/settings/organization/usage
def process_agent(user_input):
    """Process agent."""
    user_input = user_input.lower()

    model_name = os.getenv("PYDANTIC_AI_MODEL", "gpt-4o")
    model = OpenAIModel(
        model_name=model_name,
    )
    print(f"Using AI model: {model_name}")

    # Include database schema and dependencies in the system prompt
    agent = Agent(
        model=model,
        result_type=MyModel,
        system_prompt="""
        You are an agent that can execute SQL queries on a SQLite database.
        Based on the user input and database schema below, your job is to write a SQL query that would answer the user's question.

        Database schema:
        {DB_SCHEMA}
        """,
    )

    # Run the agent with the user input
    try:
        response = agent.run_sync(user_input)
        print(response.usage())
        return response.data
    except Exception as e:
        return f"Error processing input: {str(e)}"

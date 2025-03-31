import sqlite3
import pandas as pd
import re

# from typing import Dict, List, Optional
# from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel


def init_db():
    """Initialize the database with sample data."""
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    # Create tables
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


def execute_query(query):
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


def get_table_schema(table_name):
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


def get_all_tables():
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


def process_natural_language(user_input):
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

    model = OpenAIModel("gpt-4o")

    # Define a PydanticAI Agent
    agent = Agent(
        model=model,
        system_prompt="You are a helpful customer support agent. Be concise and friendly.",
    )

    # Run the agent with the user input
    try:
        response = agent.run_sync(
            user_input,
        )
        return response.data
    except Exception as e:
        return f"Error processing input: {str(e)}"

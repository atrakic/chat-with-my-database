import asyncio
import os
import sqlite3

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel


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


def _execute_sql(query: str) -> list[dict[str, object]]:
    conn = sqlite3.connect("mydatabase.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# https://platform.openai.com/settings/organization/usage
def process_agent(user_input: str) -> list[dict[str, object]] | str:
    """Process agent, run SQL, and return query results."""
    model_name = os.getenv("PYDANTIC_AI_MODEL", "gpt-4o")
    model = OpenAIChatModel(model_name=model_name)

    agent = Agent(
        model=model,
        output_type=MyModel,
        system_prompt=f"""
        You are an agent that can write SQL queries for a SQLite database.
        Based on the user input and database schema below, write a SQL query
        that would answer the user's question.

        Database schema:
        {DB_SCHEMA}
        """,
    )

    async def _run_agent() -> MyModel:
        response = await agent.run(user_input)
        return response.output

    try:
        output = asyncio.run(_run_agent())
        sql_query = output.sql_query.strip()
        if not sql_query.lower().startswith("select"):
            return "Only SELECT queries are allowed."
        if ";" in sql_query[:-1]:
            return "Only single SELECT statements are allowed."
        results = _execute_sql(sql_query)
        if not results:
            return "No results found."
        return results
    except Exception as e:
        return f"Error processing input: {str(e)}"

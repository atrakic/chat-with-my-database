import argparse
import sqlite3


def insert_record(name, title, department, salary):
    """Insert a record into the employees table."""
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO employees (name, title, department, salary) VALUES (?, ?, ?, ?)",
            (name, title, department, salary),
        )
        conn.commit()
        print(f"Record inserted: {name}, {title}, {department}, {salary}")
    except Exception as e:
        print(f"Error inserting record: {str(e)}")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        prog="DatabaseCLI",
        description="CLI for interacting with the SQLite database",
        epilog="Use this tool to query or modify the database.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Subparser for inserting a record
    insert_parser = subparsers.add_parser(
        "insert", help="Insert a record into the database"
    )
    insert_parser.add_argument("name", type=str, help="Name of the employee")
    insert_parser.add_argument("title", type=str, help="Job title of the employee")
    insert_parser.add_argument(
        "department", type=str, help="Department of the employee"
    )
    insert_parser.add_argument("salary", type=float, help="Salary of the employee")

    # Parse arguments
    args = parser.parse_args()

    # Handle commands
    if args.command == "insert":
        insert_record(args.name, args.title, args.department, args.salary)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

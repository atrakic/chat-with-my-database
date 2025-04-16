import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from utils import (
    init_db,
    execute_query,
    process_natural_language,
    process_agent,
)


load_dotenv()


def main() -> None:
    st.set_page_config(page_title="Chat with my database", page_icon=":speech_balloon:")
    st.title("Chat with my Database")

    # Initialize database on first run
    if "db_initialized" not in st.session_state:
        init_db()
        st.session_state.db_initialized = True

    # Chat input
    user_input = st.text_input(
        "Ask a question about your data or enter an SQL query:",
        placeholder="Example: Show all employees or SELECT * FROM employees",
    )

    # Mode selection
    mode = st.radio("Mode:", ("Natural Language", "SQL Query"), horizontal=True)

    if user_input:
        st.subheader("Result:")

        if mode == "Natural Language":
            if os.getenv("OPENAI_API_KEY"):
                result = process_agent(user_input)
            else:
                result = process_natural_language(user_input)
        else:  # SQL Query mode
            result = execute_query(user_input)

        # Display results
        if isinstance(result, pd.DataFrame):
            st.dataframe(result)
        else:
            st.write(result)

    # Help section
    with st.expander("Help & Examples"):
        st.markdown(
            """
        ### Natural Language Examples:
        - Show all employees
        - List employees in Engineering
        - Find the employee with the highest salary
        - What's the average salary?
        - Show employee count by department
        - Show schema for employees
        - List all tables

        ### SQL Query Examples:
        - SELECT * FROM employees
        - SELECT * FROM employees WHERE department = 'Engineering'
        - SELECT * FROM employees ORDER BY salary DESC LIMIT 1
        - SELECT AVG(salary) FROM employees
        - SELECT department, COUNT(*) FROM employees GROUP BY department
        """
        )


if __name__ == "__main__":
    # See: https://bartbroere.eu/2023/06/17/adding-a-main-to-streamlit/
    if "__streamlitmagic__" not in locals():
        import streamlit.web.bootstrap

        streamlit.web.bootstrap.run(__file__, False, [], {})

    main()

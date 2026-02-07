import os
import streamlit as st
from dotenv import load_dotenv

from utils import init_db, process_agent

load_dotenv()


def main() -> None:
    st.set_page_config(page_title="Chat with my database", page_icon=":speech_balloon:")
    st.title("Chat with my database")
    st.caption(
        "Use natural language to query SQLite database. Powered by OpenAI's GPT models and Pydantic AI."
    )

    if not os.getenv("OPENAI_API_KEY"):
        api_key_input = st.text_input(
            "OpenAI API key",
            type="password",
            placeholder="sk-...",
            help="Stored only for this session.",
        )
        if api_key_input:
            os.environ["OPENAI_API_KEY"] = api_key_input

    if "db_initialized" not in st.session_state:
        init_db()
        st.session_state.db_initialized = True

    user_input = st.text_input(
        "Ask a question about my data:",
        placeholder="Example: Show all employees",
    )

    if user_input:
        if not os.getenv("OPENAI_API_KEY"):
            st.error("OPENAI_API_KEY is not set.")
            st.stop()

        st.subheader("Result:")
        result = process_agent(user_input)
        st.dataframe(result, use_container_width=True)

    with st.expander("Help & Examples"):
        st.markdown(
            """
        ### Natural Language Examples:
        - Show schema for all tables
        - List all tables
        """
        )


if __name__ == "__main__":
    # See: https://bartbroere.eu/2023/06/17/adding-a-main-to-streamlit/
    if "__streamlitmagic__" not in locals():
        import streamlit.web.bootstrap

        streamlit.web.bootstrap.run(__file__, False, [], {})

    main()

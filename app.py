import os
from pathlib import Path
import tempfile

import streamlit as st

from graph import build_graph


st.set_page_config(page_title="Agentic Data Assistant", page_icon="📊", layout="wide")
st.title("Agentic Data Analysis Assistant")
st.caption("MCP-grounded analysis with LangGraph reflection and pluggable execution.")

with st.sidebar:
    st.header("Configuration")
    backend = st.selectbox("Execution backend", ["local", "e2b"], index=0)
    max_attempts = st.slider("Maximum attempts", 1, 5, 3)
    uploaded = st.file_uploader("Upload CSV, Excel, JSON, or SQLite", type=["csv", "xlsx", "xls", "json", "db", "sqlite", "sqlite3"])

if uploaded:
    suffix = Path(uploaded.name).suffix
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.write(uploaded.getvalue())
    temp_file.close()
    data_path = temp_file.name
else:
    data_path = "data.csv"

question = st.chat_input("Ask a question about your data")
if question:
    os.environ["ANALYSIS_EXECUTOR"] = backend
    initial_state = {
        "question": question,
        "data_path": data_path,
        "columns": [],
        "dtypes": {},
        "sample_rows": "",
        "plan": [],
        "code": "",
        "result": None,
        "error": None,
        "attempts": 0,
        "max_attempts": max_attempts,
        "narration": None,
        "chart_path": None,
        "execution_output": "",
    }
    with st.chat_message("assistant"):
        with st.spinner("Analysing your data..."):
            final_state = build_graph().invoke(initial_state)
        if final_state["narration"]:
            st.write(final_state["narration"])
        elif final_state["result"] is not None:
            st.write(final_state["result"])
        if final_state["chart_path"] and Path(final_state["chart_path"]).exists():
            st.image(final_state["chart_path"])
        with st.expander("Analysis details"):
            st.write(f"Attempts: {final_state['attempts']}")
            st.write(f"Plan: {final_state['plan']}")
            st.code(final_state["code"], language="python")
            if final_state["error"]:
                st.error(final_state["error"])

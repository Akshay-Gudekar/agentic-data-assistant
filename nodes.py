import pandas as pd
import re
from agent_state import AgentState

def ask_ollama(prompt, model="llama3.2"):
    import requests
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False}
    )
    return response.json()["response"]

def generate_node(state: AgentState) -> AgentState:
    error_context = ""
    if state.get("error"):
        error_context = f"""
Your previous attempt failed with this error: {state['error']}
Your previous code was:
{state['code']}
Fix the issue and try again.
"""

    prompt = f"""You are a data analyst. Given a pandas DataFrame called 'df' with columns: {state['columns']}

Write Python pandas code to answer this question: "{state['question']}"

Rules:
- Assume 'df' already exists, do not reload it
- Store your final answer in a variable called 'result'
- Only output code, no explanation, no markdown fences, no comments about what the code does
- If the question cannot be answered with the available data, set result to a string explaining why
{error_context}

Code:"""
    code = ask_ollama(prompt, model="codellama")
    code = re.sub(r"```python|```", "", code).strip()

    state["code"] = code
    state["attempts"] = state.get("attempts", 0) + 1
    return state

def execute_node(state: AgentState) -> AgentState:
    df = pd.read_csv("data.csv")
    local_vars = {"df": df, "pd": pd}

    # Strip lines that try to reload data or reimport pandas — df and pd already exist
    code_lines = state["code"].split("\n")
    clean_lines = [
        line for line in code_lines
        if "read_csv" not in line and "import pandas" not in line
    ]
    clean_code = "\n".join(clean_lines)

    try:
        exec(clean_code, {}, local_vars)
        state["result"] = str(local_vars.get("result", "No 'result' variable was set"))
        state["error"] = None
    except Exception as e:
        state["error"] = str(e)
        state["result"] = None
        print(f"[Attempt {state['attempts']}] FAILED: {state['error']}")
    return state

def reflect_node(state: AgentState) -> str:
    if state["error"] is None:
        return "success"
    if state["attempts"] >= state["max_attempts"]:
        return "give_up"
    return "retry"
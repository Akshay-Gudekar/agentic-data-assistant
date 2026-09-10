import pandas as pd
import re
import os
from dotenv import load_dotenv
from agent_state import AgentState
from e2b_code_interpreter import Sandbox
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client



load_dotenv(override=True)

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
    code_lines = state["code"].split("\n")
    clean_lines = [
        line for line in code_lines
        if "read_csv" not in line and "import pandas" not in line
    ]
    clean_code = "\n".join(clean_lines)

    sandbox = Sandbox.create(api_key=os.environ.get("E2B_API_KEY"))
    try:
        with open("data.csv", "rb") as f:
            sandbox.files.write("/home/user/data.csv", f.read())

        full_code = f"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

df = pd.read_csv('/home/user/data.csv')
{clean_code}

if 'plt' in dir() and plt.get_fignums():
    plt.savefig('/home/user/chart.png', bbox_inches='tight')
    print("CHART_SAVED")

print("RESULT:", result)
"""
        execution = sandbox.run_code(full_code)

        if execution.error:
            state["error"] = f"{execution.error.name}: {execution.error.value}"
            state["result"] = None
            state["chart_path"] = None
            print(f"[Attempt {state['attempts']}] FAILED: {state['error']}")
        else:
            output = "\n".join(execution.logs.stdout)
            state["error"] = None

            if "CHART_SAVED" in output:
                chart_bytes = sandbox.files.read("/home/user/chart.png", format="bytes")
                local_path = f"chart_{state['attempts']}.png"
                with open(local_path, "wb") as f:
                    f.write(chart_bytes)
                state["chart_path"] = local_path
                state["result"] = f"A chart was generated to answer: '{state['question']}'. See the attached image."
                print(f"[Chart saved locally as {local_path}]")
    finally:
        sandbox.kill()
    return state

def reflect_node(state: AgentState) -> str:
    if state["error"] is None:
        return "success"
    if state["attempts"] >= state["max_attempts"]:
        return "give_up"
    return "retry"

async def _fetch_schema_async(csv_path: str) -> dict:
    server_params = StdioServerParameters(command="python", args=["mcp_server.py"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_schema", {"csv_path": csv_path})
            import json
            return json.loads(result.content[0].text)

def mcp_fetch_node(state: AgentState) -> AgentState:
    schema = asyncio.run(_fetch_schema_async("data.csv"))
    state["columns"] = schema["columns"]
    print(f"[MCP] Fetched schema via MCP: {schema['columns']}")
    return state

def narrate_node(state: AgentState) -> AgentState:
    prompt = f"""You are a data analyst explaining findings to a non-technical person.

Original question: "{state['question']}"
Raw output from the analysis: {state['result']}

Write a short, plain-English answer (2-3 sentences max) that directly answers the question using the actual numbers from the output. Do not mention code, dataframes, or technical terms like "correlation coefficient" without explaining what it means in plain terms. Be direct and specific with numbers.

Answer:"""
    narration = ask_ollama(prompt, model="llama3.2")
    state["narration"] = narration.strip()
    return state
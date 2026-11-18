import pandas as pd
import os
import json
from dotenv import load_dotenv
from agent_state import AgentState
from code_utils import extract_python_code, parse_result
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client



load_dotenv(override=True)

def ask_ollama(prompt, model="llama3.2"):
    import requests
    response = requests.post(
        os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=int(os.environ.get("OLLAMA_TIMEOUT", "120")),
    )
    response.raise_for_status()
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
Column types: {state.get('dtypes', {})}
Sample rows: {state.get('sample_rows', '')}
Analysis plan: {state.get('plan', [])}

Write Python pandas code to answer this question: "{state['question']}"

Rules:
- Assume 'df' already exists, do not reload it
- Store your final answer in a variable called 'result'
- Only output code, no explanation, no markdown fences, no comments about what the code does
- If the question cannot be answered with the available data, set result to a string explaining why
{error_context}

Code:"""
    response = ask_ollama(prompt, model="codellama")
    try:
        state["code"] = extract_python_code(response)
        state["error"] = None
    except ValueError as exc:
        state["code"] = ""
        state["error"] = str(exc)
    state["attempts"] = state.get("attempts", 0) + 1
    return state

def execute_node(state: AgentState) -> AgentState:
    if not state["code"]:
        state["result"] = None
        state["execution_output"] = ""
        return state

    from execution import get_executor
    try:
        executor = get_executor(os.environ.get("ANALYSIS_EXECUTOR", "local"))
        execution = executor.execute(state["code"], state["data_path"])
        state["execution_output"] = execution.output
        if execution.error:
            state["error"] = execution.error
            state["result"] = None
            state["chart_path"] = None
            print(f"[Attempt {state['attempts']}] FAILED: {state['error']}")
        else:
            output = execution.output
            state["error"] = None
            state["result"] = parse_result(output)

            if execution.chart_bytes:
                local_path = f"chart_{state['attempts']}.png"
                with open(local_path, "wb") as f:
                    f.write(execution.chart_bytes)
                state["chart_path"] = local_path
                state["result"] = f"A chart was generated to answer: '{state['question']}'. See the attached image."
                print(f"[Chart saved locally as {local_path}]")
            elif state["result"] is None:
                state["error"] = "The generated code completed without producing a result."
                print(f"[Attempt {state['attempts']}] FAILED: {state['error']}")
    except Exception as exc:
        state["error"] = f"{type(exc).__name__}: {exc}"
        state["result"] = None
        state["chart_path"] = None
        print(f"[Attempt {state['attempts']}] FAILED: {state['error']}")
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
            return json.loads(result.content[0].text)

def mcp_fetch_node(state: AgentState) -> AgentState:
    schema = asyncio.run(_fetch_schema_async(state["data_path"]))
    state["columns"] = schema["columns"]
    state["dtypes"] = schema.get("dtypes", {})
    state["sample_rows"] = json.dumps(schema.get("sample_rows", []), default=str)
    print(f"[MCP] Fetched schema via MCP: {schema['columns']}")
    return state

def plan_node(state: AgentState) -> AgentState:
    question = state["question"].lower()
    steps = ["Inspect the relevant columns and missing values."]
    if any(word in question for word in ("plot", "chart", "graph", "histogram", "trend")):
        steps.append("Create the requested visualization.")
    if any(word in question for word in ("average", "mean", "count", "sum", "top", "maximum", "minimum")):
        steps.append("Calculate the requested aggregate using the available data.")
    if any(word in question for word in ("correlation", "relationship", "distribution")):
        steps.append("Compute the requested statistical summary.")
    steps.append("Store the final answer in result.")
    state["plan"] = steps
    return state

def narrate_node(state: AgentState) -> AgentState:
    prompt = f"""You are a data analyst explaining findings to a non-technical person.

Original question: "{state['question']}"
Raw output from the analysis: {state['result']}

Write a short, plain-English answer (2-3 sentences max) that directly answers the question using the actual numbers from the output. Do not mention code, dataframes, or technical terms like "correlation coefficient" without explaining what it means in plain terms. Be direct and specific with numbers.

Answer:"""
    try:
        narration = ask_ollama(prompt, model="llama3.2")
        state["narration"] = narration.strip()
    except Exception as exc:
        state["narration"] = (
            f"Analysis completed with result: {state['result']}. "
            f"Plain-language narration was unavailable ({type(exc).__name__})."
        )
    return state
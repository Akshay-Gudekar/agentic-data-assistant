# Agentic Data Analysis Assistant

This project turns plain-English questions into grounded pandas analysis. The
LangGraph flow fetches dataset metadata through the MCP file connector, creates
a lightweight plan, generates code with Ollama, executes it through a
pluggable backend, retries failures, and narrates the result.

## Run locally

The local executor is enabled by default and does not require E2B:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Ollama must be running with `codellama` and `llama3.2` available. Set
`OLLAMA_URL` or `OLLAMA_TIMEOUT` if needed.

## Connect E2B

Set `E2B_API_KEY` and select `e2b` in the Streamlit sidebar, or run the
benchmark with `--backend e2b`. The E2B integration is isolated in
`execution.py`; no graph changes are required.

## Benchmark

```powershell
python benchmark.py benchmark_tasks.json --backend local
```

Task files may be JSON or CSV. Each task needs `question` and may specify
`data_path` and `max_attempts`.

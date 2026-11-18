import csv
import json
import time
from pathlib import Path
from typing import Any

from graph import build_graph


def load_tasks(path: str) -> list[dict[str, Any]]:
    source = Path(path)
    if source.suffix.lower() == ".json":
        return json.loads(source.read_text(encoding="utf-8"))
    with source.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def run_benchmark(tasks_path: str, backend: str = "local") -> list[dict[str, Any]]:
    import os

    os.environ["ANALYSIS_EXECUTOR"] = backend
    results = []
    for task in load_tasks(tasks_path):
        started = time.perf_counter()
        state = {
            "question": task["question"],
            "data_path": task.get("data_path", "data.csv"),
            "columns": [],
            "dtypes": {},
            "sample_rows": "",
            "plan": [],
            "code": "",
            "result": None,
            "error": None,
            "attempts": 0,
            "max_attempts": int(task.get("max_attempts", 3)),
            "narration": None,
            "chart_path": None,
            "execution_output": "",
        }
        final = build_graph().invoke(state)
        results.append({
            "id": task.get("id", len(results) + 1),
            "question": task["question"],
            "success": final["error"] is None,
            "attempts": final["attempts"],
            "latency_seconds": round(time.perf_counter() - started, 3),
            "result": final["result"],
            "error": final["error"],
        })
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the analysis benchmark.")
    parser.add_argument("tasks", help="Path to a JSON or CSV task file")
    parser.add_argument("--backend", choices=("local", "e2b"), default="local")
    args = parser.parse_args()
    print(json.dumps(run_benchmark(args.tasks, args.backend), indent=2, default=str))

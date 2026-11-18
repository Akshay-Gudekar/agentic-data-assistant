from dataclasses import dataclass
import io
import os
from pathlib import Path
from contextlib import redirect_stdout
from typing import Any, Optional


@dataclass
class ExecutionResult:
    output: str
    error: Optional[str] = None
    chart_bytes: Optional[bytes] = None


class LocalExecutor:
    """Development executor. Use E2BExecutor in production."""

    def execute(self, code: str, data_path: str) -> ExecutionResult:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import pandas as pd

        output = io.StringIO()
        namespace: dict[str, Any] = {"pd": pd, "plt": plt}
        try:
            from data_sources import load_dataframe
            namespace["df"] = load_dataframe(data_path)
            with redirect_stdout(output):
                exec(compile(code, "<generated-analysis>", "exec"), namespace)
                print("RESULT:", repr(namespace.get("result")))
            chart_bytes = None
            if plt.get_fignums():
                chart_buffer = io.BytesIO()
                plt.savefig(chart_buffer, format="png", bbox_inches="tight")
                chart_bytes = chart_buffer.getvalue()
            return ExecutionResult(output.getvalue(), chart_bytes=chart_bytes)
        except Exception as exc:
            return ExecutionResult(output.getvalue(), f"{type(exc).__name__}: {exc}")
        finally:
            plt.close("all")


class E2BExecutor:
    """E2B-backed executor boundary. Configure E2B_API_KEY when ready."""

    def execute(self, code: str, data_path: str) -> ExecutionResult:
        from e2b_code_interpreter import Sandbox

        api_key = os.environ.get("E2B_API_KEY")
        if not api_key:
            raise RuntimeError("E2B_API_KEY is required for the E2B executor.")

        sandbox = Sandbox.create(api_key=api_key)
        try:
            source_path = Path(data_path)
            sandbox.files.write(f"/home/user/data{source_path.suffix}", source_path.read_bytes())
            if source_path.suffix.lower() == ".csv":
                load_expression = "pd.read_csv('/home/user/data.csv')"
            elif source_path.suffix.lower() in {".xlsx", ".xls"}:
                load_expression = "pd.read_excel('/home/user/data" + source_path.suffix + "')"
            elif source_path.suffix.lower() == ".json":
                load_expression = "pd.read_json('/home/user/data.json')"
            else:
                raise ValueError("E2B currently supports CSV, Excel, and JSON datasets.")
            source = f"""
import io
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

df = {load_expression}
{code}
if plt.get_fignums():
    plt.savefig('/home/user/chart.png', format='png', bbox_inches='tight')
    print("CHART_SAVED")
print("RESULT:", repr(result))
"""
            execution = sandbox.run_code(source)
            if execution.error:
                return ExecutionResult(
                    "\n".join(execution.logs.stdout),
                    f"{execution.error.name}: {execution.error.value}",
                )
            chart = None
            if any("CHART" in line for line in execution.logs.stdout):
                chart = sandbox.files.read("/home/user/chart.png", format="bytes")
            return ExecutionResult("\n".join(execution.logs.stdout), chart_bytes=chart)
        finally:
            sandbox.kill()


def get_executor(name: str):
    if name == "e2b":
        return E2BExecutor()
    if name == "local":
        return LocalExecutor()
    raise ValueError(f"Unknown execution backend: {name}")

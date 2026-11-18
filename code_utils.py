import ast
import re


def extract_python_code(response: str) -> str:
    """Extract executable Python from a model response."""
    fenced_blocks = re.findall(
        r"```(?:python|py)?\s*(.*?)```",
        response,
        re.DOTALL | re.IGNORECASE,
    )
    candidates = fenced_blocks or [response]

    for candidate in candidates:
        candidate = candidate.strip()
        if candidate:
            try:
                ast.parse(candidate)
                return candidate
            except SyntaxError:
                pass

    lines = response.splitlines()
    for start in range(len(lines)):
        for end in range(len(lines), start, -1):
            candidate = "\n".join(lines[start:end]).strip()
            if not candidate:
                continue
            try:
                ast.parse(candidate)
                return candidate
            except SyntaxError:
                continue

    raise ValueError("The model response did not contain valid Python code.")


def parse_result(output: str) -> str | None:
    """Return the value printed after the execution result marker."""
    marker = "RESULT:"
    result_lines = [line for line in output.splitlines() if line.startswith(marker)]
    if not result_lines:
        return None

    raw_result = result_lines[-1][len(marker):].strip()
    try:
        return str(ast.literal_eval(raw_result))
    except (SyntaxError, ValueError):
        return raw_result

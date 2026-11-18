from typing import Any, Optional, TypedDict

class AgentState(TypedDict):
    question: str
    data_path: str
    columns: list
    dtypes: dict
    sample_rows: str
    plan: list
    code: str
    result: Optional[Any]
    error: Optional[str]
    attempts: int
    max_attempts: int
    narration: Optional[str]
    chart_path: Optional[str]
    execution_output: str
from typing import TypedDict, Optional

class AgentState(TypedDict):
    question: str
    columns: list
    code: str
    result: Optional[str]
    error: Optional[str]
    attempts: int
    max_attempts: int
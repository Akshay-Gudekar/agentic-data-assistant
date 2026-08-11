from dotenv import load_dotenv
load_dotenv()
from langgraph.graph import StateGraph, END
from agent_state import AgentState
from nodes import generate_node, execute_node, reflect_node

def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("generate", generate_node)
    workflow.add_node("execute", execute_node)

    workflow.set_entry_point("generate")
    workflow.add_edge("generate", "execute")

    workflow.add_conditional_edges(
        "execute",
        reflect_node,
        {
            "success": END,
            "retry": "generate",
            "give_up": END
        }
    )

    return workflow.compile()

if __name__ == "__main__":
    graph = build_graph()

    initial_state = {
        "question": "What percentage of passengers survived?",
        "columns": ["PassengerId", "Survived", "Pclass", "Name", "Sex", "Age",
                    "SibSp", "Parch", "Ticket", "Fare", "Cabin", "Embarked"],
        "code": "",
        "result": None,
        "error": None,
        "attempts": 0,
        "max_attempts": 3
    }

    final_state = graph.invoke(initial_state)

    print("--- Final code ---")
    print(final_state["code"])
    print("--- Attempts used ---")
    print(final_state["attempts"])
    print("--- Result ---")
    print(final_state["result"])
    print("--- Error ---")
    print(final_state["error"])
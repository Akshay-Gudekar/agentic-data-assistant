from langgraph.graph import StateGraph, END
from agent_state import AgentState
from nodes import mcp_fetch_node, generate_node, execute_node, reflect_node, narrate_node

def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("mcp_fetch", mcp_fetch_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("narrate", narrate_node)

    workflow.set_entry_point("mcp_fetch")
    workflow.add_edge("mcp_fetch", "generate")
    workflow.add_edge("generate", "execute")

    workflow.add_conditional_edges(
        "execute",
        reflect_node,
        {"success": "narrate", "retry": "generate", "give_up": END}
    )

    workflow.add_edge("narrate", END)

    return workflow.compile()

if __name__ == "__main__":
    graph = build_graph()

    initial_state = {
        "question": "Plot a histogram of passenger ages",
        "columns": [],
        "code": "",
        "result": None,
        "error": None,
        "attempts": 0,
        "max_attempts": 3,
        "narration": None,
        "chart_path": None
    }

    final_state = graph.invoke(initial_state)

    print("--- Final code ---")
    print(final_state["code"])
    print("--- Attempts used ---")
    print(final_state["attempts"])
    print("--- Raw result ---")
    print(final_state["result"])
    print("--- Narration ---")
    print(final_state["narration"])
    print("--- Chart path ---")
    print(final_state["chart_path"])
    print("--- Error ---")
    print(final_state["error"])
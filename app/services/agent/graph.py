from langgraph.graph import END, StateGraph

from app.services.agent.nodes import AgentNodes
from app.services.agent.state import AgentState
from app.services.rag.service import RAGService
from app.services.research.agent import ResearchAgent
from app.services.sql.agent import SQLAgent


def create_rag_graph(rag_service: RAGService, sql_agent: SQLAgent, research_agent: ResearchAgent):
    nodes = AgentNodes(rag_service, sql_agent, research_agent)
    workflow = StateGraph(AgentState)

    # Define Nodes
    workflow.add_node("classify", nodes.classify_query)
    workflow.add_node("retrieve_rag", nodes.retrieve_rag)
    workflow.add_node("retrieve_sql", nodes.retrieve_sql)
    workflow.add_node("retrieve_web", nodes.retrieve_web)
    workflow.add_node("synthesize", nodes.synthesize_answer)
    workflow.add_node("critic", nodes.criticize_answer)
    workflow.add_node("validate", nodes.validate_citations)

    # Entry Point
    workflow.set_entry_point("classify")

    # Dynamic Routing from Classify to Tools
    def route_to_tools(state: AgentState):
        tools = state.get("tools_to_use", [])
        if not tools:
            return "synthesize"

        # In LangGraph, to run tools in parallel, we can return a list of nodes
        # However, simple StateGraph edges are 1-to-1. For parallel execution,
        # we use a fan-out pattern.
        return tools

    # We add edges from classify to each tool
    workflow.add_conditional_edges(
        "classify",
        route_to_tools,
        {
            "rag": "retrieve_rag",
            "sql": "retrieve_sql",
            "web": "retrieve_web"
        }
    )

    # Tool nodes then flow into synthesis
    # (Since we are using a simplified sequential-ish parallel flow)
    workflow.add_edge("retrieve_rag", "synthesize")
    workflow.add_edge("retrieve_sql", "synthesize")
    workflow.add_edge("retrieve_web", "synthesize")

    workflow.add_edge("synthesize", "critic")

    # Critic logic
    def decide_after_critic(state: AgentState):
        if state.get("critic_feedback") == "approved":
            return "validate"
        # Simple bounded retry: synthesis is the only step we'd retry here
        return "synthesize"

    workflow.add_conditional_edges(
        "critic",
        decide_after_critic,
        {
            "validate": "validate",
            "synthesize": "synthesize"
        }
    )

    workflow.add_edge("validate", END)

    return workflow.compile()

"""
Automaton Auditor - LangGraph Infrastructure

Production-grade LangGraph implementation for multi-agent forensic evidence collection.
Graph structure: START → ContextBuilder → [RepoInvestigator || DocAnalyst] → EvidenceAggregator → END
"""

from langgraph.graph import StateGraph, END

from .nodes.detectives import (
    context_builder,
    doc_analyst,
    evidence_aggregator,
    repo_investigator,
)
from .state import AgentState, create_initial_state


def create_audit_graph() -> StateGraph:
    """
    Create and compile the Automaton Auditor LangGraph.
    
    Graph structure:
    START → ContextBuilder → [RepoInvestigator || DocAnalyst] → EvidenceAggregator → END
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the StateGraph with our typed state
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("context_builder", context_builder)
    workflow.add_node("repo_investigator", repo_investigator)
    workflow.add_node("doc_analyst", doc_analyst)
    workflow.add_node("evidence_aggregator", evidence_aggregator)
    
    # Set entry point
    workflow.set_entry_point("context_builder")
    
    # Add edges
    # ContextBuilder → Parallel Detectives (fan-out)
    workflow.add_edge("context_builder", "repo_investigator")
    workflow.add_edge("context_builder", "doc_analyst")
    
    # Parallel Detectives → EvidenceAggregator (fan-in)
    # Both must complete before aggregation
    workflow.add_edge("repo_investigator", "evidence_aggregator")
    workflow.add_edge("doc_analyst", "evidence_aggregator")
    
    # EvidenceAggregator → END
    workflow.add_edge("evidence_aggregator", END)
    
    # Compile the graph
    compiled_graph = workflow.compile()
    
    return compiled_graph


def run_audit(
    repo_url: str | None = None,
    doc_path: str | None = None,
    graph_path: str | None = None
) -> AgentState:
    """
    Run the complete audit workflow.
    
    Args:
        repo_url: URL of repository to audit
        doc_path: Path to documentation file
        graph_path: Path to graph.py (optional, for local analysis)
        
    Returns:
        Final agent state with all evidence
    """
    # Create initial state
    initial_state = create_initial_state(
        repo_url=repo_url,
        doc_path=doc_path,
        graph_path=graph_path
    )
    
    # Create and run the graph
    graph = create_audit_graph()
    
    # Execute with stream for progress tracking
    final_state = None
    for state in graph.stream(initial_state):
        final_state = state
    
    return final_state if final_state else initial_state


def run_audit_with_trace(
    repo_url: str | None = None,
    doc_path: str | None = None,
    graph_path: str | None = None
) -> tuple[AgentState, list[str]]:
    """
    Run audit with execution trace.
    
    Args:
        repo_url: URL of repository to audit
        doc_path: Path to documentation file
        graph_path: Path to graph.py
        
    Returns:
        Tuple of (final state, execution trace)
    """
    initial_state = create_initial_state(
        repo_url=repo_url,
        doc_path=doc_path,
        graph_path=graph_path
    )
    
    graph = create_audit_graph()
    
    final_state = None
    for state in graph.stream(initial_state):
        final_state = state
    
    # Extract trace from final state
    trace = []
    if final_state and isinstance(final_state, dict):
        trace = final_state.get("execution_trace", [])
    
    return final_state if final_state else initial_state, trace


# Export commonly used items
__all__ = [
    "AgentState",
    "create_audit_graph",
    "create_initial_state",
    "run_audit",
    "run_audit_with_trace",
]

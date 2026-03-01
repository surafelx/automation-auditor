"""
Automaton Auditor - LangGraph Infrastructure

Production-grade LangGraph implementation for multi-agent forensic evidence collection.
Complete graph structure with parallel detectives, parallel judges, and Chief Justice synthesis.

Graph structure:
    START → ContextBuilder 
           → [RepoInvestigator || DocAnalyst || VisionInspector] (parallel fan-out)
           → EvidenceAggregator (fan-in)
           → [Prosecutor || Defense || TechLead] (parallel fan-out)
           → JudgesAggregator (fan-in)
           → ChiefJustice
           → END
"""

from langgraph.graph import StateGraph, END
from typing import Optional

from .nodes.detectives import (
    context_builder,
    doc_analyst,
    evidence_aggregator,
    repo_investigator,
    vision_inspector,
)
from .nodes.judges import (
    defense_judge,
    judges_aggregator,
    prosecutor_judge,
    tech_lead_judge,
)
from .nodes.justice import chief_justice
from .state import AgentState, create_initial_state


def create_audit_graph() -> StateGraph:
    """
    Create and compile the complete Automaton Auditor LangGraph.
    
    Uses a sequential approach to avoid parallel write conflicts.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the StateGraph with our typed state
    workflow = StateGraph(AgentState)
    
    # === DETECTIVE LAYER ===
    
    # Add detective nodes
    workflow.add_node("context_builder", context_builder)
    workflow.add_node("repo_investigator", repo_investigator)
    workflow.add_node("doc_analyst", doc_analyst)
    workflow.add_node("vision_inspector", vision_inspector)
    workflow.add_node("evidence_aggregator", evidence_aggregator)
    
    # === JUDICIAL LAYER ===
    
    # Add judge nodes
    workflow.add_node("prosecutor_judge", prosecutor_judge)
    workflow.add_node("defense_judge", defense_judge)
    workflow.add_node("tech_lead_judge", tech_lead_judge)
    workflow.add_node("judges_aggregator", judges_aggregator)
    
    # === SUPREME COURT ===
    
    # Add Chief Justice node
    workflow.add_node("chief_justice", chief_justice)
    
    # === WIRE THE GRAPH ===
    # Using sequential wiring to avoid parallel write conflicts
    
    # Set entry point
    workflow.set_entry_point("context_builder")
    
    # Detective Layer (sequential to avoid parallel conflicts)
    workflow.add_edge("context_builder", "repo_investigator")
    workflow.add_edge("repo_investigator", "doc_analyst")
    workflow.add_edge("doc_analyst", "vision_inspector")
    workflow.add_edge("vision_inspector", "evidence_aggregator")
    
    # Judicial Layer (sequential for same reason)
    workflow.add_edge("evidence_aggregator", "prosecutor_judge")
    workflow.add_edge("prosecutor_judge", "defense_judge")
    workflow.add_edge("defense_judge", "tech_lead_judge")
    workflow.add_edge("tech_lead_judge", "judges_aggregator")
    
    # Supreme Court
    workflow.add_edge("judges_aggregator", "chief_justice")
    workflow.add_edge("chief_justice", END)
    
    # Compile the graph
    compiled_graph = workflow.compile()
    
    return compiled_graph


def run_audit(
    repo_url: Optional[str] = None,
    doc_path: Optional[str] = None,
    graph_path: Optional[str] = None
) -> AgentState:
    """
    Run the complete audit workflow.
    
    Args:
        repo_url: URL of repository to audit
        doc_path: Path to documentation file
        graph_path: Path to graph.py (optional, for local analysis)
        
    Returns:
        Final agent state with audit report
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
    # LangGraph's stream yields {node_name: state_update} for each node
    final_state = initial_state.copy()
    for state_package in graph.stream(initial_state):
        # state_package is {node_name: state_update}
        for node_name, state_update in state_package.items():
            if isinstance(state_update, dict):
                for key, value in state_update.items():
                    if key in final_state:
                        # For list types, extend rather than replace
                        if isinstance(final_state[key], list) and isinstance(value, list):
                            final_state[key].extend(value)
                        elif isinstance(final_state[key], dict) and isinstance(value, dict):
                            final_state[key].update(value)
                        else:
                            final_state[key] = value
                    else:
                        final_state[key] = value
    
    return final_state


def run_audit_with_trace(
    repo_url: Optional[str] = None,
    doc_path: Optional[str] = None,
    graph_path: Optional[str] = None
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
    
    # Accumulate state from each node
    final_state = initial_state.copy()
    for state_package in graph.stream(initial_state):
        # state_package is {node_name: state_update}
        for node_name, state_update in state_package.items():
            if isinstance(state_update, dict):
                for key, value in state_update.items():
                    if key in final_state:
                        # For list types, extend rather than replace
                        if isinstance(final_state[key], list) and isinstance(value, list):
                            final_state[key].extend(value)
                        elif isinstance(final_state[key], dict) and isinstance(value, dict):
                            final_state[key].update(value)
                        else:
                            final_state[key] = value
                    else:
                        final_state[key] = value
    
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

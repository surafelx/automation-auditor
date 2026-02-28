"""
Automaton Auditor - LangGraph Infrastructure

Production-grade LangGraph implementation for multi-agent forensic evidence collection.
Complete graph structure with parallel detectives, parallel judges, and Chief Justice synthesis.
With conditional error handling for robustness.

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
from langgraph.prebuilt import ToolNode
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


def should_run_repo_investigator(state: AgentState) -> bool:
    """Determine if repo investigator should run based on state."""
    return bool(state.get("repo_url"))


def should_run_doc_analyst(state: AgentState) -> bool:
    """Determine if doc analyst should run based on state."""
    return bool(state.get("doc_path"))


def should_run_vision_inspector(state: AgentState) -> bool:
    """Determine if vision inspector should run based on state."""
    # Run if doc_path exists (can extract images from PDF)
    return bool(state.get("doc_path"))


def create_audit_graph() -> StateGraph:
    """
    Create and compile the complete Automaton Auditor LangGraph.
    
    Graph structure:
    START → ContextBuilder 
           → [RepoInvestigator || DocAnalyst || VisionInspector] (conditional fan-out)
           → EvidenceAggregator (fan-in)
           → [Prosecutor || Defense || TechLead] (parallel fan-out)
           → JudgesAggregator (fan-in)
           → ChiefJustice
           → END
    
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
    
    # Set entry point
    workflow.set_entry_point("context_builder")
    
    # === CONDITIONAL DETECTIVE FAN-OUT ===
    # ContextBuilder → Conditional Detectives (fan-out)
    # Use conditional edges to handle missing inputs gracefully
    workflow.add_conditional_edges(
        "context_builder",
        should_run_repo_investigator,
        {
            True: "repo_investigator",
            False: "__end__"
        }
    )
    
    workflow.add_conditional_edges(
        "context_builder",
        should_run_doc_analyst,
        {
            True: "doc_analyst",
            False: "__end__"
        }
    )
    
    workflow.add_conditional_edges(
        "context_builder", 
        should_run_vision_inspector,
        {
            True: "vision_inspector",
            False: "__end__"
        }
    )
    
    # === DETECTIVE ERROR HANDLING ===
    # Add error handling: if any detective fails, still proceed to aggregation
    # The detectives already handle their own errors internally
    
    # === DETECTIVE FAN-IN ===
    # All detectives that ran → EvidenceAggregator (fan-in)
    # Use conditional edges: if node ran, go to aggregator
    workflow.add_conditional_edges(
        "repo_investigator",
        lambda x: "evidence_aggregator",
        {
            "evidence_aggregator": "evidence_aggregator"
        }
    )
    
    workflow.add_conditional_edges(
        "doc_analyst",
        lambda x: "evidence_aggregator",
        {
            "evidence_aggregator": "evidence_aggregator"
        }
    )
    
    workflow.add_conditional_edges(
        "vision_inspector",
        lambda x: "evidence_aggregator",
        {
            "evidence_aggregator": "evidence_aggregator"
        }
    )
    
    # Simplified: Connect all detectives to aggregator (they'll add empty lists if skipped)
    workflow.add_edge("repo_investigator", "evidence_aggregator")
    workflow.add_edge("doc_analyst", "evidence_aggregator")
    workflow.add_edge("vision_inspector", "evidence_aggregator")
    
    # === JUDICIAL FAN-OUT ===
    # EvidenceAggregator → Parallel Judges (fan-out)
    workflow.add_edge("evidence_aggregator", "prosecutor_judge")
    workflow.add_edge("evidence_aggregator", "defense_judge")
    workflow.add_edge("evidence_aggregator", "tech_lead_judge")
    
    # === JUDICIAL ERROR HANDLING ===
    # Each judge handles its own errors gracefully
    
    # === JUDICIAL FAN-IN ===
    # All judges must complete before aggregation
    workflow.add_edge("prosecutor_judge", "judges_aggregator")
    workflow.add_edge("defense_judge", "judges_aggregator")
    workflow.add_edge("tech_lead_judge", "judges_aggregator")
    
    # === SUPREME COURT ===
    # JudgesAggregator → ChiefJustice → END
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
    final_state = None
    for state in graph.stream(initial_state):
        final_state = state
    
    return final_state if final_state else initial_state


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

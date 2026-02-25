"""
Automaton Auditor - Detective Nodes

LangGraph nodes for evidence collection.
Contains RepoInvestigator and DocAnalyst detectives that run in parallel.
"""

import shutil
import uuid
from pathlib import Path
from typing import Any

from ..state import AgentState, Evidence
from ..tools import repo_tools, doc_tools


def context_builder(state: AgentState) -> AgentState:
    """
    Context Builder Node - Prepares context for parallel detectives.
    
    This node runs first and sets up the context for the parallel
    RepoInvestigator and DocAnalyst nodes.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with context information
    """
    state["execution_trace"].append("ContextBuilder: Building context for detectives")
    
    # Validate inputs
    if not state.get("repo_url") and not state.get("doc_path"):
        state["errors"].append("ContextBuilder: No repo_url or doc_path provided")
    
    state["context_built"] = True
    state["execution_trace"].append("ContextBuilder: Context built successfully")
    
    return state


def repo_investigator(state: AgentState) -> AgentState:
    """
    Repo Investigator Detective - Analyzes repository structure and git history.
    
    Responsibilities:
    - Clone repo in sandbox (temp directory)
    - Run git log --oneline --reverse
    - Extract commit messages + timestamps
    - Parse src/graph.py via AST
    - Detect StateGraph instantiation, add_edge usage, parallel branching
    
    Returns Evidence under keys:
    - git_forensic_analysis
    - graph_orchestration
    - state_management_rigor
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with evidence
    """
    state["execution_trace"].append("RepoInvestigator: Starting repository investigation")
    
    repo_url = state.get("repo_url")
    if not repo_url:
        state["errors"].append("RepoInvestigator: No repo_url provided")
        state["execution_trace"].append("RepoInvestigator: Aborted - no repo_url")
        return state
    
    evidence_id = str(uuid.uuid4())[:8]
    temp_repo_path: str | None = None
    
    try:
        # Clone repository to temporary directory
        state["execution_trace"].append(f"RepoInvestigator: Cloning {repo_url}")
        
        temp_repo_path = repo_tools.clone_repo_to_temp(repo_url)
        
        if not temp_repo_path:
            raise RuntimeError("Failed to clone repository")
        
        state["repo_cloned"] = True
        state["execution_trace"].append(f"RepoInvestigator: Repository cloned to {temp_repo_path}")
        
        # Get git log
        git_log = repo_tools.get_git_log(temp_repo_path, reverse=True)
        state["execution_trace"].append(f"RepoInvestigator: Found {len(git_log)} commits")
        
        # Analyze graph structure
        graph_analysis = repo_tools.analyze_graph_structure(temp_repo_path)
        state["execution_trace"].append(f"RepoInvestigator: Graph analysis complete")
        
        # Create evidence
        evidence_list = repo_tools.create_git_evidence(
            evidence_id=evidence_id,
            repo_url=repo_url,
            git_log=git_log,
            graph_analysis=graph_analysis
        )
        
        # Distribute evidence to appropriate keys
        for evidence in evidence_list:
            state["evidence"].append(evidence)
            
            if evidence.evidence_type == "git_forensic_analysis":
                state["git_forensic_analysis"].append(evidence)
            elif evidence.evidence_type == "graph_orchestration":
                state["graph_orchestration"].append(evidence)
            elif evidence.evidence_type == "state_management_rigor":
                state["state_management_rigor"].append(evidence)
        
        state["execution_trace"].append(f"RepoInvestigator: Evidence collected - {len(evidence_list)} items")
        
    except Exception as e:
        error_msg = f"RepoInvestigator error: {str(e)}"
        state["errors"].append(error_msg)
        state["execution_trace"].append(f"RepoInvestigator: {error_msg}")
        
        # Create error evidence
        error_evidence = repo_tools.create_git_evidence(
            evidence_id=evidence_id,
            repo_url=repo_url,
            git_log=[],
            graph_analysis={"found": False},
            error_message=str(e)
        )
        
        for evidence in error_evidence:
            state["evidence"].append(evidence)
            if evidence.evidence_type == "git_forensic_analysis":
                state["git_forensic_analysis"].append(evidence)
    
    finally:
        # Cleanup temp directory
        if temp_repo_path and Path(temp_repo_path).exists():
            try:
                shutil.rmtree(temp_repo_path)
                state["execution_trace"].append("RepoInvestigator: Temp directory cleaned up")
            except Exception as cleanup_error:
                state["execution_trace"].append(
                    f"RepoInvestigator: Cleanup warning - {str(cleanup_error)}"
                )
    
    return state


def doc_analyst(state: AgentState) -> AgentState:
    """
    Document Analyst Detective - Analyzes documentation for theoretical depth.
    
    Responsibilities:
    - Parse PDF documents
    - Chunk content
    - Search for:
      - Dialectical Synthesis
      - Fan-In / Fan-Out
      - Metacognition
      - State Synchronization
    - Determine whether terms are explained or are buzzwords
    
    Returns Evidence under keys:
    - theoretical_depth
    - report_accuracy
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with evidence
    """
    state["execution_trace"].append("DocAnalyst: Starting document analysis")
    
    doc_path = state.get("doc_path")
    if not doc_path:
        state["errors"].append("DocAnalyst: No doc_path provided")
        state["execution_trace"].append("DocAnalyst: Aborted - no doc_path")
        return state
    
    evidence_id = str(uuid.uuid4())[:8]
    
    try:
        state["execution_trace"].append(f"DocAnalyst: Analyzing {doc_path}")
        
        # Perform document analysis
        analysis_result = doc_tools.analyze_document(doc_path)
        
        if analysis_result.get("error"):
            raise RuntimeError(analysis_result["error"])
        
        state["docs_analyzed"] = True
        state["execution_trace"].append(
            f"DocAnalyst: Analysis complete - found {len(analysis_result.get('terms_found', {}))} term categories"
        )
        
        # Create evidence
        evidence_list = doc_tools.create_document_evidence(
            evidence_id=evidence_id,
            doc_path=doc_path,
            analysis_result=analysis_result
        )
        
        # Distribute evidence to appropriate keys
        for evidence in evidence_list:
            state["evidence"].append(evidence)
            
            if evidence.evidence_type == "theoretical_depth":
                state["theoretical_depth"].append(evidence)
            elif evidence.evidence_type == "report_accuracy":
                state["report_accuracy"].append(evidence)
        
        state["execution_trace"].append(f"DocAnalyst: Evidence collected - {len(evidence_list)} items")
        
    except Exception as e:
        error_msg = f"DocAnalyst error: {str(e)}"
        state["errors"].append(error_msg)
        state["execution_trace"].append(f"DocAnalyst: {error_msg}")
        
        # Create error evidence
        error_evidence = doc_tools.create_document_evidence(
            evidence_id=evidence_id,
            doc_path=doc_path,
            analysis_result={},
            error_message=str(e)
        )
        
        for evidence in error_evidence:
            state["evidence"].append(evidence)
            if evidence.evidence_type == "theoretical_depth":
                state["theoretical_depth"].append(evidence)
    
    return state


def evidence_aggregator(state: AgentState) -> AgentState:
    """
    Evidence Aggregator Node - Merges evidence from parallel detectives.
    
    This node receives evidence from both RepoInvestigator and DocAnalyst
    (which run in parallel) and merges them without overwriting.
    
    Args:
        state: Current agent state with evidence from both detectives
        
    Returns:
        Updated state with aggregated evidence
    """
    state["execution_trace"].append("EvidenceAggregator: Starting evidence aggregation")
    
    # Count evidence from each source
    git_count = len(state.get("git_forensic_analysis", []))
    graph_count = len(state.get("graph_orchestration", []))
    state_mgmt_count = len(state.get("state_management_rigor", []))
    theory_count = len(state.get("theoretical_depth", []))
    accuracy_count = len(state.get("report_accuracy", []))
    
    total_evidence = len(state.get("evidence", []))
    
    state["execution_trace"].append(
        f"EvidenceAggregator: Aggregated {total_evidence} evidence items"
    )
    state["execution_trace"].append(
        f"EvidenceAggregator: - Git forensic: {git_count}, Graph: {graph_count}, "
        f"State: {state_mgmt_count}, Theory: {theory_count}, Accuracy: {accuracy_count}"
    )
    
    # Check for any errors
    errors = state.get("errors", [])
    if errors:
        state["execution_trace"].append(
            f"EvidenceAggregator: Warning - {len(errors)} errors encountered"
        )
        for error in errors:
            state["execution_trace"].append(f"  - {error}")
    
    state["execution_trace"].append("EvidenceAggregator: Aggregation complete")
    
    return state

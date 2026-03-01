"""
Automaton Auditor - State Management Module

This module defines the typed state for the LangGraph multi-agent evidence collection system.
Uses Pydantic BaseModel for evidence structures and TypedDict for agent state.
"""

import operator
from datetime import datetime
from enum import Enum
from typing import Annotated, Optional, TypedDict

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Types of evidence that can be collected by detectives."""
    GIT_FORENSIC = "git_forensic_analysis"
    GRAPH_ORCHESTRATION = "graph_orchestration"
    STATE_MANAGEMENT = "state_management_rigor"
    THEORETICAL_DEPTH = "theoretical_depth"
    REPORT_ACCURACY = "report_accuracy"
    SWARM_VISUAL = "swarm_visual"
    GENERAL = "general"


class Evidence(BaseModel):
    """Structured evidence collected by detectives."""
    
    evidence_id: str = Field(..., description="Unique identifier for this evidence")
    evidence_type: EvidenceType = Field(..., description="Type of evidence")
    content: str = Field(..., description="The actual evidence content")
    source: str = Field(..., description="Source file or location")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When evidence was collected")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    
    class Config:
        use_enum_values = True


class JudicialOpinion(BaseModel):
    """
    Judicial opinion on the audit results.
    This model represents the verdict on LangGraph implementation quality.
    """
    
    opinion_id: str = Field(..., description="Unique identifier for this opinion")
    verdict: str = Field(..., description="Verdict: APPROVED, CONDITIONAL, REJECTED")
    rationale: str = Field(..., description="Detailed reasoning for the verdict")
    precedents_cited: list[str] = Field(default_factory=list, description="Precedents or patterns cited")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in opinion")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When opinion was rendered")


class CriterionResult(BaseModel):
    """Result of evaluating a specific audit criterion."""
    
    criterion_name: str = Field(..., description="Name of the criterion evaluated")
    passed: bool = Field(..., description="Whether the criterion was met")
    score: float = Field(ge=1.0, le=5.0, description="Score for this criterion (1-5 scale)")
    findings: list[str] = Field(default_factory=list, description="Key findings")
    evidence_refs: list[str] = Field(default_factory=list, description="References to supporting evidence")


class AuditReport(BaseModel):
    """Complete audit report with all findings and opinions."""
    
    report_id: str = Field(..., description="Unique identifier for this audit report")
    title: str = Field(..., description="Title of the audit report")
    summary: str = Field(..., description="Executive summary of findings")
    criterion_results: list[CriterionResult] = Field(default_factory=list, description="Results for each criterion")
    evidence_collected: dict[str, list[Evidence]] = Field(default_factory=dict, description="All evidence by type")
    judicial_opinion: Optional[JudicialOpinion] = Field(default=None, description="Final judicial opinion")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Report generation time")
    graph_path: str = Field(..., description="Path to the audited graph")
    
    class Config:
        use_enum_values = True


# List reducer using operator.add for merging lists
def _merge_lists(existing: list, new: list) -> list:
    """Merge two lists, preserving order and avoiding duplicates where appropriate."""
    if not existing:
        return new
    if not new:
        return existing
    # Simple merge - in production could use more sophisticated deduplication
    return existing + new


# Dict reducer using operator.ior for merging dicts
def _merge_dicts(existing: dict, new: dict) -> dict:
    """Merge two dicts, with new values taking precedence for same keys."""
    if not existing:
        return new
    if not new:
        return existing
    merged = existing.copy()
    merged.update(new)
    return merged


class AgentState(TypedDict):
    """
    Typed state for the LangGraph agent.
    
    This is the central state that flows through the graph.
    Uses Annotated types with reducers for proper fan-in/fan-out handling.
    """
    
    # Context information
    repo_url: Optional[str]
    doc_path: Optional[str]
    graph_path: Optional[str]
    
    # Evidence collected by detectives (list reducer for parallel merging)
    evidence: Annotated[list[Evidence], operator.add]
    
    # Structured evidence by category (dict reducer for merging)
    git_forensic_analysis: Annotated[list[Evidence], operator.add]
    graph_orchestration: Annotated[list[Evidence], operator.add]
    state_management_rigor: Annotated[list[Evidence], operator.add]
    theoretical_depth: Annotated[list[Evidence], operator.add]
    report_accuracy: Annotated[list[Evidence], operator.add]
    swarm_visual: Annotated[list[Evidence], operator.add]
    
    # Audit results
    audit_report: Optional[AuditReport]
    
    # Execution metadata
    errors: Annotated[list[str], operator.add]
    execution_trace: Annotated[list[str], operator.add]
    
    # Status flags
    context_built: bool
    repo_cloned: bool
    docs_analyzed: bool
    
    # Judicial opinions from all three judges
    judicial_opinions: Annotated[list[JudicialOpinion], operator.add]


def create_initial_state(
    repo_url: Optional[str] = None,
    doc_path: Optional[str] = None,
    graph_path: Optional[str] = None
) -> AgentState:
    """
    Factory function to create initial agent state.
    
    Args:
        repo_url: URL of the repository to audit
        doc_path: Path to documentation to analyze
        graph_path: Path to the graph.py file to inspect
        
    Returns:
        Initial AgentState with proper typing
    """
    return {
        "repo_url": repo_url,
        "doc_path": doc_path,
        "graph_path": graph_path,
        "evidence": [],
        "git_forensic_analysis": [],
        "graph_orchestration": [],
        "state_management_rigor": [],
        "theoretical_depth": [],
        "report_accuracy": [],
        "swarm_visual": [],
        "audit_report": None,
        "errors": [],
        "execution_trace": [],
        "context_built": False,
        "repo_cloned": False,
        "docs_analyzed": False,
        "judicial_opinions": [],
    }

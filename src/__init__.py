"""
Automaton Auditor - Forensic Multi-Agent Evidence Collection System

A production-grade LangGraph infrastructure for auditing LangGraph implementations.
"""

from .graph import create_audit_graph, run_audit, run_audit_with_trace
from .state import (
    AgentState,
    AuditReport,
    CriterionResult,
    Evidence,
    EvidenceType,
    JudicialOpinion,
    create_initial_state,
)

__version__ = "0.1.0"

__all__ = [
    # Graph
    "create_audit_graph",
    "run_audit",
    "run_audit_with_trace",
    # State
    "AgentState",
    "AuditReport",
    "CriterionResult",
    "Evidence",
    "EvidenceType",
    "JudicialOpinion",
    "create_initial_state",
]

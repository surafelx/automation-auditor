"""
Automaton Auditor - Nodes Package

LangGraph node implementations:
- Detectives: Evidence collection layer
- Judges: Judicial deliberation layer
- Justice: Supreme Court synthesis
"""

from . import detectives
from . import judges
from . import justice

__all__ = ["detectives", "judges", "justice"]

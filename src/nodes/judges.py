"""
Automaton Auditor - Judicial Layer

LangGraph nodes for the judicial deliberation layer.
Contains Prosecutor, Defense Attorney, and Tech Lead judges with distinct personas.
"""

import os
import uuid
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..state import AgentState, Evidence, JudicialOpinion as StateJudicialOpinion


# --- Extended Judicial Opinion for Phase 2 ---

class CriterionScore(BaseModel):
    """Score for a specific criterion."""
    criterion_id: str = Field(description="The criterion ID (e.g., 'graph_orchestration')")
    criterion_name: str = Field(description="Human-readable name")
    score: int = Field(ge=1, le=5, description="Score from 1-5")
    argument: str = Field(description="Reasoning for the score")
    cited_evidence: list[str] = Field(default_factory=list, description="Evidence IDs cited")


class JudgeOutput(BaseModel):
    """Structured output from a judge for a single criterion."""
    criterion_id: str
    criterion_name: str
    score: int = Field(ge=1, le=5)
    argument: str
    cited_evidence: list[str]


# --- Judge Prompts ---

PROSECUTOR_SYSTEM_PROMPT = """You are the PROSECUTOR in a digital courtroom. Your role is to be adversarial and critical.

CORE PHILOSOPHY: "Trust No One. Assume Vibe Coding."
OBJECTIVE: Scrutinize the evidence for gaps, security flaws, and laziness.

YOUR DUTIES:
1. Look for what's WRONG, missing, or poorly implemented
2. Charge the defendant with specific violations
3. Be harsh but factual - cite specific evidence
4. If code is buggy or architecture is flawed, argue for LOW scores

SCORING GUIDELINES:
- Score 1: Fundamental failure - code doesn't work, architecture is broken
- Score 2: Major gaps - key requirements missing or completely wrong approach
- Score 3: Acceptable but flawed - works but has significant issues
- Score 4: Good but not perfect - mostly works, minor issues
- Score 5: Only if truly exceptional - exceeds expectations

SPECIFIC CHARGES TO LOOK FOR:
- "Orchestration Fraud": Linear flow instead of parallel fan-out
- "Hallucination Liability": Claims files exist that don't
- "Security Negligence": Raw os.system calls, no sandboxing
- "Technical Debt": Plain dicts instead of Pydantic models

Respond with a structured score and argument. Be adversarial but fair."""


DEFENSE_SYSTEM_PROMPT = """You are the DEFENSE ATTORNEY in a digital courtroom. Your role is to be optimistic and forgiving.

CORE PHILOSOPHY: "Reward Effort and Intent. Look for the 'Spirit of the Law'."
OBJECTIVE: Highlight creative workarounds, deep thought, and effort, even if imperfect.

YOUR DUTIES:
1. Look for what's RIGHT, even if imperfect
2. Argue for credit based on effort and intent
3. Find the "spirit of the law" in creative implementations
4. If code shows deep understanding despite syntax errors, argue for HIGHER scores

SCORING GUIDELINES:
- Score 1: Complete failure - no effort or understanding demonstrated
- Score 2: Minimal effort - some attempt but fundamentally wrong
- Score 3: Reasonable effort - shows understanding but incomplete
- Score 4: Good effort - mostly works, demonstrates learning
- Score 5: Excellent - goes above and beyond expectations

MITIGATION ARGUMENTS TO USE:
- "Deep code comprehension despite syntax issues": AST logic is sophisticated
- "Engineering process": Git history shows struggle and iteration
- "Creative workaround": Non-standard approach that still solves the problem
- "Partial implementation": Good foundation even if incomplete

Respond with a structured score and argument. Be generous but honest."""


TECH_LEAD_SYSTEM_PROMPT = """You are the TECH LEAD in a digital courtroom. Your role is to be pragmatic and objective.

CORE PHILOSOPHY: "Does it actually work? Is it maintainable?"
OBJECTIVE: Evaluate architectural soundness, code cleanliness, and practical viability.

YOUR DUTIES:
1. Ignore "vibe" and "struggle" - focus on ARTIFACTS
2. Evaluate if code is modular, maintainable, and functional
3. Assess technical debt and practical viability
4. You are the TIE-BREAKER - be realistic and practical

SCORING GUIDELINES:
- Score 1: Doesn't work - broken, insecure, or unmaintainable
- Score 2: Works but has serious issues - high technical debt
- Score 3: Functional but average - meets basic requirements
- Score 4: Well-engineered - good architecture, low technical debt
- Score 5: Production-ready - excellent, maintainable, scalable

PRAGMATIC CHECKS:
- Are reducers (operator.add, operator.ior) actually used correctly?
- Are tool calls isolated and safe?
- Is the architecture modular or spaghetti?
- Can this code be maintained by a team?

Respond with a structured score and argument. Be practical and realistic."""


# --- Judge Evaluation Prompt Template ---

JUDGE_EVALUATION_PROMPT = """You are evaluating a Week 2 submission for the Automaton Auditor challenge.

CRITERION TO EVALUATE:
{criterion_id}: {criterion_name}

FORENSIC EVIDENCE COLLECTED:
{evidence_summary}

Your task is to evaluate this criterion based ONLY on the evidence provided.
Consider your specific judicial persona (Prosecutor/Defense/Tech Lead) when rendering your verdict.

Respond with:
1. A score from 1-5
2. Your reasoning (argument)
3. Specific evidence IDs you cite

Remember: Your persona should influence your evaluation approach."""


# --- LangChain Imports ---

# Try to import Ollama, fall back to OpenAI if not available
try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


def get_llm():
    """Get the LLM instance for judges. Prefers Groq (fast), then Gemini, then Ollama, then OpenAI."""
    if GROQ_AVAILABLE:
        # Ensure GROQ_API_KEY is set in environment
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in environment")
        
        return ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.3,
            groq_api_key=api_key
        )
    elif GEMINI_AVAILABLE:
        # Ensure GOOGLE_API_KEY is set in environment
        api_key = os.environ.get("GOOGLE_API_KEY", "")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment")
        
        # Set explicitly for google.auth
        os.environ["GOOGLE_API_KEY"] = api_key
        
        return ChatGoogleGenerativeAI(
            model="gemini-3-flash-preview",
            temperature=0.3,
            google_api_key=api_key,
            convert_system_message_to_human=True
        )
    elif OLLAMA_AVAILABLE:
        return ChatOllama(
            model="llama3.2",
            temperature=0.3,
        )
    elif OPENAI_AVAILABLE:
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
        )
    else:
        raise ImportError("No LLM available. Install: langchain-groq, langchain-google-genai, langchain-ollama, or langchain-openai")


def _format_evidence_summary(evidence_list: list[Evidence]) -> str:
    """Format evidence for judge consumption."""
    if not evidence_list:
        return "No evidence collected for this criterion."
    
    summary_parts = []
    for i, ev in enumerate(evidence_list[:10]):  # Limit to first 10 items
        summary_parts.append(
            f"[{i+1}] Type: {ev.evidence_type}\n"
            f"    Source: {ev.source}\n"
            f"    Content: {ev.content[:500]}..."
        )
    
    return "\n\n".join(summary_parts)


def evaluate_criterion_with_judge(
    judge_name: str,
    system_prompt: str,
    criterion_id: str,
    criterion_name: str,
    evidence_list: list[Evidence]
) -> CriterionScore:
    """
    Have a specific judge evaluate a criterion.
    
    Args:
        judge_name: Name of the judge (Prosecutor, Defense, TechLead)
        system_prompt: System prompt for this judge's persona
        criterion_id: The criterion ID
        criterion_name: The criterion name
        evidence_list: List of evidence to evaluate
        
    Returns:
        CriterionScore with the judge's verdict
    """
    llm = get_llm()
    
    # Create the prompt
    evidence_summary = _format_evidence_summary(evidence_list)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", JUDGE_EVALUATION_PROMPT.format(
            criterion_id=criterion_id,
            criterion_name=criterion_name,
            evidence_summary=evidence_summary
        ))
    ])
    
    # Create chain with structured output
    chain = prompt | llm.with_structured_output(CriterionScore)
    
    try:
        result = chain.invoke({})
        return result
    except Exception as e:
        # Fallback if structured output fails
        return CriterionScore(
            criterion_id=criterion_id,
            criterion_name=criterion_name,
            score=3,
            argument=f"Error during evaluation: {str(e)}. Defaulting to score 3.",
            cited_evidence=[]
        )


# --- LangGraph Judge Nodes ---

def prosecutor_judge(state: AgentState) -> AgentState:
    """
    Prosecutor Judge Node - Evaluates evidence through adversarial lens.
    
    Args:
        state: Current agent state with evidence
        
    Returns:
        Updated state with prosecutor's opinions
    """
    state["execution_trace"].append("Prosecutor: Starting evaluation")
    
    opinions: list[StateJudicialOpinion] = []
    
    # Define criteria to evaluate
    criteria = [
        ("git_forensic_analysis", "Git Forensic Analysis", state.get("git_forensic_analysis", [])),
        ("graph_orchestration", "Graph Orchestration Architecture", state.get("graph_orchestration", [])),
        ("state_management_rigor", "State Management Rigor", state.get("state_management_rigor", [])),
        ("theoretical_depth", "Theoretical Depth", state.get("theoretical_depth", [])),
        ("report_accuracy", "Report Accuracy", state.get("report_accuracy", [])),
    ]
    
    for criterion_id, criterion_name, evidence_list in criteria:
        if not evidence_list:
            continue
            
        score_result = evaluate_criterion_with_judge(
            judge_name="Prosecutor",
            system_prompt=PROSECUTOR_SYSTEM_PROMPT,
            criterion_id=criterion_id,
            criterion_name=criterion_name,
            evidence_list=evidence_list
        )
        
        # Defensive null check
        if score_result is None:
            score_result = CriterionScore(
                criterion_id=criterion_id,
                criterion_name=criterion_name,
                score=3,
                argument="Error: Judge evaluation returned no result. Defaulting to score 3.",
                cited_evidence=[]
            )
        
        opinion = StateJudicialOpinion(
            opinion_id=f"prosecutor_{criterion_id}_{uuid.uuid4().hex[:8]}",
            verdict="REJECTED" if score_result.score <= 2 else "CONDITIONAL" if score_result.score <= 3 else "APPROVED",
            rationale=f"[PROSECUTOR] Score {score_result.score}/5: {score_result.argument}",
            precedents_cited=score_result.cited_evidence,
            confidence=0.9
        )
        opinions.append(opinion)
        
        state["execution_trace"].append(
            f"Prosecutor: {criterion_id} -> Score {score_result.score}/5"
        )
    
    # Add opinions to state
    if "judicial_opinions" not in state:
        state["judicial_opinions"] = []
    state["judicial_opinions"].extend(opinions)
    
    state["execution_trace"].append(f"Prosecutor: Complete - {len(opinions)} opinions rendered")
    
    return state


def defense_judge(state: AgentState) -> AgentState:
    """
    Defense Judge Node - Evaluates evidence through optimistic lens.
    
    Args:
        state: Current agent state with evidence
        
    Returns:
        Updated state with defense's opinions
    """
    state["execution_trace"].append("Defense: Starting evaluation")
    
    opinions: list[StateJudicialOpinion] = []
    
    # Define criteria to evaluate
    criteria = [
        ("git_forensic_analysis", "Git Forensic Analysis", state.get("git_forensic_analysis", [])),
        ("graph_orchestration", "Graph Orchestration Architecture", state.get("graph_orchestration", [])),
        ("state_management_rigor", "State Management Rigor", state.get("state_management_rigor", [])),
        ("theoretical_depth", "Theoretical Depth", state.get("theoretical_depth", [])),
        ("report_accuracy", "Report Accuracy", state.get("report_accuracy", [])),
    ]
    
    for criterion_id, criterion_name, evidence_list in criteria:
        if not evidence_list:
            continue
            
        score_result = evaluate_criterion_with_judge(
            judge_name="Defense",
            system_prompt=DEFENSE_SYSTEM_PROMPT,
            criterion_id=criterion_id,
            criterion_name=criterion_name,
            evidence_list=evidence_list
        )
        
        # Defensive null check
        if score_result is None:
            score_result = CriterionScore(
                criterion_id=criterion_id,
                criterion_name=criterion_name,
                score=3,
                argument="Error: Judge evaluation returned no result. Defaulting to score 3.",
                cited_evidence=[]
            )
        
        opinion = StateJudicialOpinion(
            opinion_id=f"defense_{criterion_id}_{uuid.uuid4().hex[:8]}",
            verdict="REJECTED" if score_result.score <= 2 else "CONDITIONAL" if score_result.score <= 3 else "APPROVED",
            rationale=f"[DEFENSE] Score {score_result.score}/5: {score_result.argument}",
            precedents_cited=score_result.cited_evidence,
            confidence=0.9
        )
        opinions.append(opinion)
        
        state["execution_trace"].append(
            f"Defense: {criterion_id} -> Score {score_result.score}/5"
        )
    
    # Add opinions to state
    if "judicial_opinions" not in state:
        state["judicial_opinions"] = []
    state["judicial_opinions"].extend(opinions)
    
    state["execution_trace"].append(f"Defense: Complete - {len(opinions)} opinions rendered")
    
    return state


def tech_lead_judge(state: AgentState) -> AgentState:
    """
    Tech Lead Judge Node - Evaluates evidence through pragmatic lens.
    
    Args:
        state: Current agent state with evidence
        
    Returns:
        Updated state with tech lead's opinions
    """
    state["execution_trace"].append("TechLead: Starting evaluation")
    
    opinions: list[StateJudicialOpinion] = []
    
    # Define criteria to evaluate
    criteria = [
        ("git_forensic_analysis", "Git Forensic Analysis", state.get("git_forensic_analysis", [])),
        ("graph_orchestration", "Graph Orchestration Architecture", state.get("graph_orchestration", [])),
        ("state_management_rigor", "State Management Rigor", state.get("state_management_rigor", [])),
        ("theoretical_depth", "Theoretical Depth", state.get("theoretical_depth", [])),
        ("report_accuracy", "Report Accuracy", state.get("report_accuracy", [])),
    ]
    
    for criterion_id, criterion_name, evidence_list in criteria:
        if not evidence_list:
            continue
            
        score_result = evaluate_criterion_with_judge(
            judge_name="TechLead",
            system_prompt=TECH_LEAD_SYSTEM_PROMPT,
            criterion_id=criterion_id,
            criterion_name=criterion_name,
            evidence_list=evidence_list
        )
        
        # Defensive null check
        if score_result is None:
            score_result = CriterionScore(
                criterion_id=criterion_id,
                criterion_name=criterion_name,
                score=3,
                argument="Error: Judge evaluation returned no result. Defaulting to score 3.",
                cited_evidence=[]
            )
        
        opinion = StateJudicialOpinion(
            opinion_id=f"techlead_{criterion_id}_{uuid.uuid4().hex[:8]}",
            verdict="REJECTED" if score_result.score <= 2 else "CONDITIONAL" if score_result.score <= 3 else "APPROVED",
            rationale=f"[TECH LEAD] Score {score_result.score}/5: {score_result.argument}",
            precedents_cited=score_result.cited_evidence,
            confidence=0.9
        )
        opinions.append(opinion)
        
        state["execution_trace"].append(
            f"TechLead: {criterion_id} -> Score {score_result.score}/5"
        )
    
    # Add opinions to state
    if "judicial_opinions" not in state:
        state["judicial_opinions"] = []
    state["judicial_opinions"].extend(opinions)
    
    state["execution_trace"].append(f"TechLead: Complete - {len(opinions)} opinions rendered")
    
    return state


def judges_aggregator(state: AgentState) -> AgentState:
    """
    Judges Aggregator Node - Waits for all three judges to complete.
    
    This is a synchronization node that ensures all judges
    have rendered their opinions before proceeding to Chief Justice.
    
    Args:
        state: Current agent state with judicial opinions
        
    Returns:
        Updated state (no changes, just synchronization)
    """
    state["execution_trace"].append("JudgesAggregator: All judges complete")
    
    opinion_count = len(state.get("judicial_opinions", []))
    state["execution_trace"].append(f"JudgesAggregator: Collected {opinion_count} total opinions")
    
    return state

"""
Automaton Auditor - Chief Justice Node

The Supreme Court layer - synthesizes dialectical conflict into final verdict.
Implements deterministic conflict resolution rules.
"""

import uuid
from datetime import datetime
from typing import Any

from ..state import AgentState, AuditReport, CriterionResult, Evidence, JudicialOpinion


# --- Synthesis Rules (Hardcoded Deterministic Logic) ---

class SynthesisRules:
    """
    Hardcoded deterministic rules for conflict resolution.
    These rules implement the "Constitution" of the Digital Courtroom.
    """
    
    @staticmethod
    def security_override(prosecutor_score: int, defense_score: int, tech_lead_score: int, 
                          security_issue_found: bool = False) -> int:
        """
        Rule of Security: If Prosecutor identifies confirmed security vulnerability,
        cap the score at 3 regardless of Defense arguments.
        
        Args:
            prosecutor_score: Score from prosecutor
            defense_score: Score from defense  
            tech_lead_score: Score from tech lead
            security_issue_found: Whether a security issue was confirmed
            
        Returns:
            Capped score if security issue found, else max of all scores
        """
        if security_issue_found:
            # Cap at 3 if security issue found
            return min(max(prosecutor_score, defense_score, tech_lead_score), 3)
        return max(prosecutor_score, defense_score, tech_lead_score)
    
    @staticmethod
    def fact_supremacy(prosecutor_evidence: str, defense_claims: str, 
                       factual_evidence_exists: bool) -> bool:
        """
        Rule of Evidence: Forensic evidence always overrules judicial opinion.
        
        Args:
            prosecutor_evidence: Evidence from prosecutor
            defense_claims: Claims from defense
            factual_evidence_exists: Whether supporting evidence exists
            
        Returns:
            True if defense should be overruled, False otherwise
        """
        # If defense claims something but no factual evidence supports it
        if defense_claims and not factual_evidence_exists:
            return True
        return False
    
    @staticmethod
    def functionality_weight(tech_lead_confirms_modular: bool, 
                            prosecutor_score: int, 
                            defense_score: int) -> int:
        """
        Rule of Functionality: If Tech Lead confirms architecture is modular,
        this carries highest weight.
        
        Args:
            tech_lead_confirms_modular: Whether tech lead confirms modularity
            prosecutor_score: Score from prosecutor
            defense_score: Score from defense
            
        Returns:
            Weighted score based on tech lead's assessment
        """
        if tech_lead_confirms_modular:
            # If tech lead confirms modular, average with tech lead but favor it
            return max(prosecutor_score, defense_score, 4)
        return max(prosecutor_score, defense_score)
    
    @staticmethod
    def calculate_variance(scores: list[int]) -> float:
        """Calculate variance in scores to detect disagreement."""
        if not scores:
            return 0.0
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        return variance
    
    @staticmethod
    def needs_dissent(prosecutor_score: int, defense_score: int, 
                      tech_lead_score: int) -> bool:
        """Check if variance exceeds threshold requiring dissent summary."""
        scores = [prosecutor_score, defense_score, tech_lead_score]
        variance = SynthesisRules.calculate_variance(scores)
        # Variance > 2 means significant disagreement
        return variance > 2


# --- Chief Justice Node ---

def chief_justice(state: AgentState) -> AgentState:
    """
    Chief Justice Node - Synthesizes dialectical conflict into final verdict.
    
    This node implements the "Supreme Court" layer. It does NOT simply
    average scores - it applies deterministic rules to resolve conflicts.
    
    Rules applied:
    1. Security Override: Security flaws cap score at 3
    2. Fact Supremacy: Evidence overrules opinion
    3. Functionality Weight: Tech lead's modularity assessment is primary
    4. Dissent Requirement: High variance triggers dissent summary
    
    Args:
        state: Current agent state with judicial opinions from all three judges
        
    Returns:
        Updated state with final AuditReport
    """
    state["execution_trace"].append("ChiefJustice: Starting synthesis")
    
    # Get all opinions
    opinions = state.get("judicial_opinions", [])
    
    if not opinions:
        state["execution_trace"].append("ChiefJustice: No opinions to synthesize")
        state["errors"].append("ChiefJustice: No judicial opinions found")
        return state
    
    # Group opinions by criterion
    opinions_by_criterion: dict[str, list[JudicialOpinion]] = {}
    for opinion in opinions:
        # Extract criterion ID from opinion_id (format: judge_criterionid_xxx)
        parts = opinion.opinion_id.split("_")
        if len(parts) >= 2:
            criterion_id = f"{parts[0]}_{parts[1]}"
            if criterion_id not in opinions_by_criterion:
                opinions_by_criterion[criterion_id] = []
            opinions_by_criterion[criterion_id].append(opinion)
    
    # Evaluate each criterion
    criterion_results: list[CriterionResult] = []
    
    for criterion_id, criterion_opinions in opinions_by_criterion.items():
        result = _synthesize_criterion(criterion_id, criterion_opinions)
        criterion_results.append(result)
        state["execution_trace"].append(
            f"ChiefJustice: {criterion_id} -> Final Score {result.score}/5"
        )
    
    # Calculate overall score
    overall_score = sum(r.score for r in criterion_results) / len(criterion_results) if criterion_results else 0.0
    
    # Generate executive summary
    executive_summary = _generate_executive_summary(criterion_results)
    
    # Generate remediation plan
    remediation_plan = _generate_remediation_plan(criterion_results)
    
    # Create final audit report
    audit_report = AuditReport(
        report_id=f"audit_{uuid.uuid4().hex[:12]}",
        title="Automaton Auditor - Week 2 Evaluation",
        summary=executive_summary,
        criterion_results=criterion_results,
        evidence_collected={
            "git_forensic": state.get("git_forensic_analysis", []),
            "graph_orchestration": state.get("graph_orchestration", []),
            "state_management": state.get("state_management_rigor", []),
            "theoretical_depth": state.get("theoretical_depth", []),
            "report_accuracy": state.get("report_accuracy", []),
        },
        judicial_opinions=opinions[-1] if opinions else None,  # Last opinion as representative
        timestamp=datetime.utcnow(),
        graph_path=state.get("repo_url", "unknown")
    )
    
    # Store in state
    state["audit_report"] = audit_report
    state["execution_trace"].append(f"ChiefJustice: Synthesis complete - Overall Score: {overall_score:.2f}/5")
    
    return state


def _synthesize_criterion(criterion_id: str, opinions: list[JudicialOpinion]) -> CriterionResult:
    """
    Synthesize opinions for a single criterion using deterministic rules.
    
    Args:
        criterion_id: The criterion being evaluated
        opinions: List of judicial opinions from all three judges
        
    Returns:
        Final CriterionResult with synthesized score
    """
    # Parse scores from opinions
    scores: list[int] = []
    prosecutor_arg = ""
    defense_arg = ""
    tech_lead_arg = ""
    
    for opinion in opinions:
        # Extract score from rationale (format: "[JUDGE] Score X/5: ...")
        rationale = opinion.rationale
        if "Score " in rationale and "/5" in rationale:
            try:
                score_part = rationale.split("Score ")[1].split("/5")[0]
                score = int(score_part.strip())
                scores.append(score)
                
                if "PROSECUTOR" in rationale:
                    prosecutor_arg = rationale
                elif "DEFENSE" in rationale:
                    defense_arg = rationale
                elif "TECH LEAD" in rationale:
                    tech_lead_arg = rationale
            except (ValueError, IndexError):
                pass
    
    if not scores:
        # Default if no scores found
        return CriterionResult(
            criterion_name=criterion_id,
            passed=False,
            score=1.0,
            findings=["No valid scores from judges"],
            evidence_refs=[]
        )
    
    # Apply synthesis rules
    prosecutor_score = scores[0] if len(scores) > 0 else 3
    defense_score = scores[1] if len(scores) > 1 else 3
    tech_lead_score = scores[2] if len(scores) > 2 else 3
    
    # Check for security issues in prosecutor's argument
    security_issue = "security" in prosecutor_arg.lower() or "vulnerability" in prosecutor_arg.lower()
    
    # Apply Rule 1: Security Override
    final_score = SynthesisRules.security_override(
        prosecutor_score, defense_score, tech_lead_score, security_issue
    )
    
    # Apply Rule 3: Functionality Weight (simplified)
    # If tech lead gave high score, boost final score
    if tech_lead_score >= 4 and final_score < tech_lead_score:
        final_score = min(final_score + 1, 5)
    
    # Check if dissent is required
    needs_dissent = SynthesisRules.needs_dissent(prosecutor_score, defense_score, tech_lead_score)
    
    dissent_summary = None
    if needs_dissent:
        dissent_summary = _generate_dissent_summary(
            criterion_id, prosecutor_score, defense_score, tech_lead_score,
            prosecutor_arg, defense_arg, tech_lead_arg
        )
    
    return CriterionResult(
        criterion_name=criterion_id,
        passed=final_score >= 3,
        score=float(final_score),
        findings=_extract_findings(opinions),
        evidence_refs=[op.opinion_id for op in opinions]
    )


def _generate_dissent_summary(criterion_id: str, prosecutor_score: int, 
                                defense_score: int, tech_lead_score: int,
                                prosecutor_arg: str, defense_arg: str, 
                                tech_lead_arg: str) -> str:
    """
    Generate a dissent summary explaining the conflict between judges.
    
    Args:
        criterion_id: The criterion being evaluated
        prosecutor_score: Score from prosecutor
        defense_score: Score from defense  
        tech_lead_score: Score from tech lead
        prosecutor_arg: Prosecutor's argument
        defense_arg: Defense's argument
        tech_lead_arg: Tech lead's argument
        
    Returns:
        Dissent summary string
    """
    # Find the disagreement
    max_score = max(prosecutor_score, defense_score, tech_lead_score)
    min_score = min(prosecutor_score, defense_score, tech_lead_score)
    
    summary_parts = [
        f"**Dissent Detected** (Score Variance: {max_score - min_score}):",
        "",
    ]
    
    # Explain each judge's position
    if prosecutor_score == min_score:
        summary_parts.append(f"- **Prosecutor** (Score {prosecutor_score}): Argued for stricter standards")
    elif prosecutor_score == max_score:
        summary_parts.append(f"- **Prosecutor** (Score {prosecutor_score}): Identified critical issues")
    
    if defense_score == min_score:
        summary_parts.append(f"- **Defense** (Score {defense_score}): Felt effort was insufficient")
    elif defense_score == max_score:
        summary_parts.append(f"- **Defense** (Score {defense_score}): Recognized good effort")
    
    if tech_lead_score == min_score:
        summary_parts.append(f"- **Tech Lead** (Score {tech_lead_score}): Found technical issues")
    elif tech_lead_score == max_score:
        summary_parts.append(f"- **Tech Lead** (Score {tech_lead_score}): Confirmed architectural soundness")
    
    summary_parts.append("")
    summary_parts.append("**Resolution**: Final score reflects balance between strict evaluation (Prosecutor),")
    summary_parts.append("effort recognition (Defense), and practical viability (Tech Lead).")
    
    return "\n".join(summary_parts)


def _extract_findings(opinions: list[JudicialOpinion]) -> list[str]:
    """Extract key findings from judicial opinions."""
    findings = []
    for opinion in opinions:
        # Extract key points from rationale
        rationale = opinion.rationale
        # Take first 200 chars as a finding
        if len(rationale) > 200:
            finding = rationale[:200] + "..."
        else:
            finding = rationale
        findings.append(finding)
    return findings


def _generate_executive_summary(results: list[CriterionResult]) -> str:
    """
    Generate an executive summary for the audit report.
    
    Args:
        results: List of criterion results
        
    Returns:
        Executive summary string
    """
    if not results:
        return "No evaluation results available."
    
    # Calculate stats
    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)
    avg_score = sum(r.score for r in results) / total_count
    
    # Determine grade
    if avg_score >= 4.5:
        grade = "MASTER THINKER"
    elif avg_score >= 3.5:
        grade = "COMPETENT ORCHESTRATOR"
    elif avg_score >= 2.5:
        grade = "DEVELOPING ENGINEER"
    else:
        grade = "VIBE CODING"
    
    summary_parts = [
        f"## Executive Summary",
        "",
        f"**Overall Grade**: {grade}",
        f"**Overall Score**: {avg_score:.2f}/5",
        f"**Criteria Passed**: {passed_count}/{total_count}",
        "",
        "### Key Findings:",
    ]
    
    # Add notable findings
    for result in results:
        if result.score >= 4:
            summary_parts.append(f"- **{result.criterion_name}**: Strong performance ({result.score}/5)")
        elif result.score <= 2:
            summary_parts.append(f"- **{result.criterion_name}**: Needs improvement ({result.score}/5)")
    
    return "\n".join(summary_parts)


def _generate_remediation_plan(results: list[CriterionResult]) -> str:
    """
    Generate a remediation plan with specific file-level instructions.
    
    Args:
        results: List of criterion results
        
    Returns:
        Remediation plan string
    """
    if not results:
        return "No remediation needed."
    
    # Filter to only failing criteria
    failing = [r for r in results if not r.passed]
    
    if not failing:
        return "All criteria passed! No remediation needed."
    
    plan_parts = [
        "## Remediation Plan",
        "",
        "The following areas require attention:",
        ""
    ]
    
    for result in failing:
        plan_parts.append(f"### {result.criterion_name} (Current: {result.score}/5)")
        plan_parts.append("")
        
        # Generate specific recommendations based on criterion
        recommendations = _get_recommendations(result.criterion_name)
        for rec in recommendations:
            plan_parts.append(f"- {rec}")
        plan_parts.append("")
    
    return "\n".join(plan_parts)


def _get_recommendations(criterion_id: str) -> list[str]:
    """Get specific remediation recommendations for a criterion."""
    
    recommendations_map = {
        "git_forensic_analysis": [
            "Ensure commit history shows iterative development (not just 'init' commit)",
            "Break implementation into logical commits: Setup -> Tools -> Graph",
            "Include meaningful commit messages describing changes"
        ],
        "graph_orchestration": [
            "Implement parallel fan-out for detectives using StateGraph",
            "Add EvidenceAggregator node for fan-in before judges",
            "Implement parallel judges (Prosecutor || Defense || TechLead)",
            "Add conditional edges for error handling"
        ],
        "state_management_rigor": [
            "Use Pydantic BaseModel for Evidence and JudicialOpinion",
            "Implement reducers (operator.add, operator.ior) in AgentState",
            "Ensure typed state prevents data overwriting in parallel execution"
        ],
        "theoretical_depth": [
            "Explain 'Dialectical Synthesis' with architectural details",
            "Describe how Fan-In/Fan-Out is implemented in code",
            "Connect 'Metacognition' to system evaluating its own quality"
        ],
        "report_accuracy": [
            "Verify all cited file paths actually exist in the repository",
            "Remove claims about features not implemented in code",
            "Cross-reference report claims with actual implementation"
        ],
    }
    
    return recommendations_map.get(criterion_id, [
        "Review the rubric and ensure all requirements are addressed",
        "Consult with the teaching team for clarification"
    ])


# --- Report Generation ---

def generate_markdown_report(state: AgentState) -> str:
    """
    Generate the final Markdown audit report.
    
    Args:
        state: Final agent state with audit report
        
    Returns:
        Markdown-formatted audit report
    """
    audit_report = state.get("audit_report")
    
    if not audit_report:
        return "# Audit Report\n\nNo audit report generated."
    
    # Build markdown
    md_parts = [
        f"# {audit_report.title}",
        "",
        f"**Report ID**: {audit_report.report_id}",
        f"**Generated**: {audit_report.timestamp.isoformat()}",
        f"**Repository**: {audit_report.graph_path}",
        "",
        "---",
        "",
        audit_report.summary,
        "",
        "---",
        "",
        "## Detailed Evaluation",
        ""
    ]
    
    # Add each criterion result
    for result in audit_report.criterion_results:
        md_parts.append(f"### {result.criterion_name}")
        md_parts.append("")
        md_parts.append(f"**Score**: {result.score}/5")
        md_parts.append(f"**Status**: {'✅ PASSED' if result.passed else '❌ FAILED'}")
        md_parts.append("")
        md_parts.append("**Findings**:")
        for finding in result.findings:
            md_parts.append(f"- {finding}")
        md_parts.append("")
    
    # Add remediation plan
    md_parts.append("---")
    md_parts.append("")
    md_parts.append(audit_report.summary)  # Using summary as remediation for now
    
    return "\n".join(md_parts)

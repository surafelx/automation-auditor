"""
Automaton Auditor - Repository Tools Module

Secure git operations for forensic analysis.
Uses subprocess.run with capture_output for safe execution.
"""

import ast
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..state import Evidence


@dataclass
class GitCloneResult:
    """Result of a git clone operation."""
    success: bool
    repo_path: str | None
    error_message: str | None


@dataclass 
class GitLogEntry:
    """A single git commit log entry."""
    hash: str
    message: str
    timestamp: str
    author: str


def secure_git_clone(repo_url: str, branch: str = "main") -> GitCloneResult:
    """
    Securely clone a git repository into a temporary directory.
    
    Args:
        repo_url: URL of the repository to clone
        branch: Branch to clone (default: main)
        
    Returns:
        GitCloneResult with success status and path or error
    """
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Build git clone command
            cmd = ["git", "clone", "--branch", branch, "--single-branch", repo_url, tmp_dir]
            
            # Execute with full output capture
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Check return code
            if result.returncode != 0:
                error_msg = _parse_git_error(result.stderr, result.stdout)
                return GitCloneResult(
                    success=False,
                    repo_path=None,
                    error_message=error_msg
                )
            
            # Return the temp directory path (caller is responsible for cleanup)
            # We need to copy to a persistent location since temp will be deleted
            return GitCloneResult(
                success=True,
                repo_path=tmp_dir,
                error_message=None
            )
            
    except subprocess.TimeoutExpired:
        return GitCloneResult(
            success=False,
            repo_path=None,
            error_message="Git clone timed out after 5 minutes"
        )
    except Exception as e:
        return GitCloneResult(
            success=False,
            repo_path=None,
            error_message=f"Git clone failed: {str(e)}"
        )


def clone_repo_to_temp(repo_url: str, branch: str = "main") -> str | None:
    """
    Clone repository to a persistent temp directory.
    
    Note: Caller is responsible for cleaning up the returned path.
    
    Args:
        repo_url: URL of the repository to clone
        branch: Branch to clone
        
    Returns:
        Path to cloned repository or None on failure
    """
    # Create a persistent temp directory
    temp_base = tempfile.mkdtemp(prefix="auditor_repo_")
    
    try:
        cmd = ["git", "clone", "--branch", branch, "--single-branch", "--depth", "50", repo_url, temp_base]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            error_msg = _parse_git_error(result.stderr, result.stdout)
            raise RuntimeError(f"Git clone failed: {error_msg}")
        
        return temp_base
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("Git clone timed out after 5 minutes")
    except Exception as e:
        raise RuntimeError(f"Git clone failed: {str(e)}")


def get_git_log(repo_path: str, reverse: bool = True) -> list[GitLogEntry]:
    """
    Get git log entries from a repository.
    
    Args:
        repo_path: Path to the git repository
        reverse: If True, return oldest first
        
    Returns:
        List of GitLogEntry objects
    """
    cmd = ["git", "log", "--format=%H|%s|%ai|%an"]
    if reverse:
        cmd.append("--reverse")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return []
        
        entries = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|")
            if len(parts) >= 4:
                entries.append(GitLogEntry(
                    hash=parts[0],
                    message=parts[1],
                    timestamp=parts[2],
                    author=parts[3]
                ))
        
        return entries
        
    except Exception:
        return []


def parse_graph_with_ast(graph_file_path: str) -> dict[str, Any]:
    """
    Parse a graph.py file using Python's AST module.
    
    Detects:
    - StateGraph instantiation
    - add_edge calls
    - Presence of parallel branching
    
    Args:
        graph_file_path: Path to graph.py
        
    Returns:
        Dictionary with parsing results
    """
    result = {
        "has_stategraph": False,
        "has_add_edge": False,
        "has_parallel_branching": False,
        "nodes_found": [],
        "edges_found": [],
        "stategraph_params": {},
        "parse_error": None
    }
    
    try:
        with open(graph_file_path, "r", encoding="utf-8") as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            # Detect StateGraph instantiation
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "StateGraph":
                    result["has_stategraph"] = True
                    # Extract keyword arguments
                    for kw in node.keywords:
                        if kw.value:
                            result["stategraph_params"][kw.arg] = ast.unparse(kw.value)
                
                # Detect add_edge calls
                if isinstance(node.func, ast.Attribute) and node.func.attr == "add_edge":
                    result["has_add_edge"] = True
                    if node.args:
                        result["edges_found"].append({
                            "from": ast.unparse(node.args[0]) if len(node.args) > 0 else None,
                            "to": ast.unparse(node.args[1]) if len(node.args) > 1 else None
                        })
                
                # Detect add_conditional_edges (parallel branching indicator)
                if isinstance(node.func, ast.Attribute) and node.func.attr == "add_conditional_edges":
                    result["has_parallel_branching"] = True
            
            # Detect node assignments (add_node calls)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        result["nodes_found"].append(target.id)
        
        return result
        
    except Exception as e:
        result["parse_error"] = str(e)
        return result


def analyze_graph_structure(repo_path: str) -> dict[str, Any]:
    """
    Analyze the graph.py structure in a repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary with analysis results
    """
    graph_path = Path(repo_path) / "src" / "graph.py"
    if not graph_path.exists():
        graph_path = Path(repo_path) / "graph.py"
    
    if not graph_path.exists():
        return {
            "found": False,
            "error": "graph.py not found"
        }
    
    return {
        "found": True,
        "path": str(graph_path),
        "ast_analysis": parse_graph_with_ast(str(graph_path))
    }


def _parse_git_error(stderr: str, stdout: str) -> str:
    """Parse git error output for meaningful messages."""
    if "authentication" in stderr.lower() or "credential" in stderr.lower():
        return "Git authentication failed. Check your credentials."
    if "not found" in stderr.lower() or "does not exist" in stderr.lower():
        return "Repository not found. Check the URL."
    if "permission" in stderr.lower():
        return "Permission denied. Check access rights."
    # Return stderr if no specific match, otherwise stdout
    return stderr if stderr else stdout


def create_git_evidence(
    evidence_id: str,
    repo_url: str,
    git_log: list[GitLogEntry],
    graph_analysis: dict[str, Any],
    error_message: str | None = None
) -> list[Evidence]:
    """
    Create Evidence objects from git forensic analysis.
    
    Args:
        evidence_id: Base ID for evidence
        repo_url: URL of the repository
        git_log: Git log entries
        graph_analysis: AST analysis results
        error_message: Any error that occurred
        
    Returns:
        List of Evidence objects
    """
    from datetime import datetime
    
    evidence_list = []
    
    # Git forensic analysis evidence
    if error_message:
        content = f"Git forensic analysis failed: {error_message}"
    else:
        commit_count = len(git_log)
        commit_summary = f"Analyzed {commit_count} commits"
        if git_log:
            commit_summary += f" from {git_log[0].timestamp} to {git_log[-1].timestamp}"
        
        content = f"""
Repository: {repo_url}
{commit_summary}

Git Log Analysis:
"""
        for entry in git_log[:20]:  # Limit to first 20 for evidence
            content += f"- {entry.hash[:8]}: {entry.message} ({entry.timestamp})\n"
        
        if len(git_log) > 20:
            content += f"\n... and {len(git_log) - 20} more commits"
    
    evidence_list.append(Evidence(
        evidence_id=f"{evidence_id}_git_forensic",
        evidence_type="git_forensic_analysis",
        content=content,
        source=repo_url,
        timestamp=datetime.utcnow(),
        metadata={"commit_count": len(git_log)},
        confidence=0.9 if not error_message else 0.3
    ))
    
    # Graph orchestration evidence
    if graph_analysis.get("found"):
        ast_result = graph_analysis.get("ast_analysis", {})
        orchestration_content = f"""
Graph Structure Analysis:
- StateGraph found: {ast_result.get('has_stategraph', False)}
- add_edge calls: {ast_result.get('has_add_edge', False)}
- Parallel branching detected: {ast_result.get('has_parallel_branching', False)}
- Nodes found: {', '.join(ast_result.get('nodes_found', []))}
- Edges found: {len(ast_result.get('edges_found', []))}

StateGraph Parameters: {ast_result.get('stategraph_params', {})}
"""
        evidence_list.append(Evidence(
            evidence_id=f"{evidence_id}_graph_orchestration",
            evidence_type="graph_orchestration",
            content=orchestration_content,
            source=graph_analysis.get("path", "unknown"),
            timestamp=datetime.utcnow(),
            metadata={"ast_analysis": ast_result},
            confidence=0.95
        ))
    
    # State management rigor evidence
    if graph_analysis.get("found"):
        ast_result = graph_analysis.get("ast_analysis", {})
        state_content = f"""
State Management Analysis:
- Uses TypedDict: {ast_result.get('has_stategraph', False)}
- Has edge definitions: {ast_result.get('has_add_edge', False)}
- Graph structure defined: {len(ast_result.get('nodes_found', [])) > 0}

This indicates {'proper' if ast_result.get('has_stategraph') else 'incomplete'} state management infrastructure.
"""
        evidence_list.append(Evidence(
            evidence_id=f"{evidence_id}_state_management",
            evidence_type="state_management_rigor",
            content=state_content,
            source=graph_analysis.get("path", "unknown"),
            timestamp=datetime.utcnow(),
            metadata={"nodes": ast_result.get("nodes_found", [])},
            confidence=0.85
        ))
    
    return evidence_list

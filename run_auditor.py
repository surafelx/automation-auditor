#!/usr/bin/env python3
"""
Automaton Auditor - Main Entry Point

Run the complete audit workflow against a GitHub repository and PDF report.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.graph import run_audit, run_audit_with_trace
from src.nodes.justice import generate_markdown_report


def main():
    parser = argparse.ArgumentParser(
        description="Automaton Auditor - Multi-Agent Code Review System"
    )
    parser.add_argument(
        "--repo-url",
        type=str,
        help="GitHub repository URL to audit"
    )
    parser.add_argument(
        "--doc-path",
        type=str,
        help="Path to PDF report to analyze"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="audit_report.md",
        help="Output path for the audit report (default: audit_report.md)"
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Show execution trace"
    )
    parser.add_argument(
        "--self-audit",
        action="store_true",
        help="Run self-audit on the current repository"
    )
    
    args = parser.parse_args()
    
    # Handle self-audit mode
    if args.self_audit:
        # Get the current repo URL from git
        import subprocess
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            repo_url = result.stdout.strip()
            print(f"Self-audit mode: Using repository {repo_url}")
        except Exception as e:
            print(f"Error getting repository URL: {e}")
            repo_url = None
        
        # Find the PDF report
        doc_path = None
        for path in ["reports/final_report.pdf", "reports/interim_report.pdf"]:
            if os.path.exists(path):
                doc_path = path
                break
        
        if not doc_path:
            print("Warning: No PDF report found")
        
        args.repo_url = repo_url
        args.doc_path = doc_path
    
    # Validate inputs
    if not args.repo_url and not args.doc_path:
        print("Error: Must provide either --repo-url or --doc-path (or use --self-audit)")
        parser.print_help()
        sys.exit(1)
    
    print("=" * 60)
    print("AUTOMATON AUDITOR - Digital Courtroom")
    print("=" * 60)
    print(f"Repository: {args.repo_url or 'N/A'}")
    print(f"Document: {args.doc_path or 'N/A'}")
    print("=" * 60)
    
    # Run the audit
    print("\n[1/4] Initializing audit workflow...")
    
    print("[2/4] Running detectives (parallel evidence collection)...")
    if args.trace:
        final_state, trace = run_audit_with_trace(
            repo_url=args.repo_url,
            doc_path=args.doc_path
        )
        print("\n--- Execution Trace ---")
        for t in trace:
            print(f"  → {t}")
    else:
        final_state = run_audit(
            repo_url=args.repo_url,
            doc_path=args.doc_path
        )
    
    print("[3/4] Judges deliberating (dialectical synthesis)...")
    print("[4/4] Chief Justice rendering verdict...")
    
    # Generate markdown report
    print("\n" + "=" * 60)
    print("FINAL VERDICT")
    print("=" * 60)
    
    # Get the audit report from final state
    if isinstance(final_state, dict):
        audit_report = final_state.get("audit_report")
        if audit_report:
            print(f"\nReport ID: {audit_report.report_id}")
            print(f"Summary: {audit_report.summary[:500]}...")
            
            # Generate markdown
            md_report = generate_markdown_report(final_state)
            
            # Write to file
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(md_report)
            
            print(f"\n✓ Full report saved to: {args.output}")
        else:
            print("Error: No audit report generated")
            print("Final state keys:", list(final_state.keys()) if isinstance(final_state, dict) else "Not a dict")
    else:
        print("Error: Invalid final state")
    
    print("\n" + "=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()

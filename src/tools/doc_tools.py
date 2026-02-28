"""
Automaton Auditor - Document Tools Module

PDF parsing and analysis for theoretical depth assessment.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

# Try to import PyPDF2, fall back to other methods if not available
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from ..state import Evidence


# Key terms to search for in documents
KEY_TERMS = {
    "dialectical_synthesis": [
        "dialectical synthesis",
        "dialectical",
        "synthesis",
    ],
    "fan_in_out": [
        "fan-in",
        "fan-out",
        "fan in",
        "fan out",
        "parallel execution",
        "parallel branching",
    ],
    "metacognition": [
        "metacognition",
        "meta-cognition",
        "self-awareness",
        "self-reflection",
    ],
    "state_synchronization": [
        "state synchronization",
        "state sync",
        "synchronizing state",
        "state consistency",
    ],
}


@dataclass
class DocumentChunk:
    """A chunk of document content with metadata."""
    content: str
    page_number: Optional[int]
    chunk_index: int
    word_count: int


@dataclass
class TermOccurrence:
    """A found term with context."""
    term: str
    normalized_term: str
    context: str
    page_number: Optional[int]
    is_explained: bool  # True if appears to be explained, not just mentioned


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text content
    """
    if not PDF_AVAILABLE:
        raise ImportError("PyPDF2 is required for PDF parsing. Install with: pip install pypdf")
    
    text_parts = []
    
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                text_parts.append(f"[Page {page_num + 1}]\n{text}")
    
    return "\n\n".join(text_parts)


def chunk_document(text: str, chunk_size: int = 2000, overlap: int = 200) -> list[DocumentChunk]:
    """
    Split document into overlapping chunks.
    
    Args:
        text: Full document text
        chunk_size: Target size for each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of DocumentChunk objects
    """
    chunks = []
    start = 0
    index = 0
    
    # Extract page numbers from text markers
    page_pattern = re.compile(r'\[Page (\d+)\]')
    
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]
        
        # Find page number for this chunk
        page_match = page_pattern.search(chunk_text)
        page_number = int(page_match.group(1)) if page_match else None
        
        # Check if term appears to be explained (follows definition pattern)
        word_count = len(chunk_text.split())
        
        chunks.append(DocumentChunk(
            content=chunk_text,
            page_number=page_number,
            chunk_index=index,
            word_count=word_count
        ))
        
        start += chunk_size - overlap
        index += 1
    
    return chunks


def search_for_terms(
    chunks: list[DocumentChunk],
    terms_dict: dict[str, list[str]] = KEY_TERMS
) -> dict[str, list[TermOccurrence]]:
    """
    Search document chunks for key terms.
    
    Args:
        chunks: Document chunks to search
        terms_dict: Dictionary of term categories and their variations
        
    Returns:
        Dictionary mapping term categories to occurrences
    """
    results: dict[str, list[TermOccurrence]] = {key: [] for key in terms_dict}
    
    for chunk in chunks:
        content_lower = chunk.content.lower()
        
        for term_category, term_variations in terms_dict.items():
            for term in term_variations:
                term_lower = term.lower()
                if term_lower in content_lower:
                    # Find the term in context
                    idx = content_lower.find(term_lower)
                    context_start = max(0, idx - 100)
                    context_end = min(len(chunk.content), idx + len(term) + 100)
                    context = chunk.content[context_start:context_end]
                    
                    # Check if this looks like an explanation
                    # Patterns: "X is defined as", "X refers to", "X means"
                    is_explained = bool(re.search(
                        r'(is defined as|refers to|means|is a|represents|describes)',
                        context[:50].lower()
                    ))
                    
                    results[term_category].append(TermOccurrence(
                        term=term,
                        normalized_term=term_category,
                        context=context,
                        page_number=chunk.page_number,
                        is_explained=is_explained
                    ))
    
    return results


def analyze_theoretical_depth(term_occurrences: dict[str, list[TermOccurrence]]) -> dict[str, Any]:
    """
    Analyze the theoretical depth of document coverage.
    
    Args:
        term_occurrences: Found term occurrences
        
    Returns:
        Analysis results with depth assessment
    """
    analysis = {
        "terms_found": {},
        "explanation_quality": {},
        "overall_depth_score": 0.0,
        "issues": []
    }
    
    total_terms = 0
    explained_terms = 0
    
    for term_category, occurrences in term_occurrences.items():
        count = len(occurrences)
        total_terms += count
        
        explained = sum(1 for occ in occurrences if occ.is_explained)
        explained_terms += explained
        
        analysis["terms_found"][term_category] = {
            "count": count,
            "pages": list(set(occ.page_number for occ in occurrences if occ.page_number))
        }
        
        # Score explanation quality
        if count > 0:
            quality = explained / count
            analysis["explanation_quality"][term_category] = {
                "score": quality,
                "status": "well_explained" if quality > 0.5 else "mentioned_only" if quality > 0 else "not_found"
            }
        else:
            analysis["explanation_quality"][term_category] = {
                "score": 0.0,
                "status": "not_found"
            }
        
        # Track issues
        if count == 0:
            analysis["issues"].append(f"Term category '{term_category}' not found in document")
        elif explained == 0:
            analysis["issues"].append(f"Term category '{term_category}' mentioned but not explained")
    
    # Calculate overall depth score
    if total_terms > 0:
        analysis["overall_depth_score"] = explained_terms / total_terms
    
    return analysis


def create_document_evidence(
    evidence_id: str,
    doc_path: str,
    analysis_result: dict[str, Any],
    error_message: Optional[str] = None
) -> list[Evidence]:
    """
    Create Evidence objects from document analysis.
    
    Args:
        evidence_id: Base ID for evidence
        doc_path: Path to the document
        analysis_result: Results from document analysis
        error_message: Any error that occurred
        
    Returns:
        List of Evidence objects
    """
    from datetime import datetime
    
    evidence_list = []
    
    # Theoretical depth evidence
    if error_message:
        content = f"Document analysis failed: {error_message}"
        confidence = 0.1
    else:
        depth = analysis_result.get("theoretical_depth", {})
        terms = depth.get("terms_found", {})
        quality = depth.get("explanation_quality", {})
        
        content = f"""
Theoretical Depth Analysis for: {doc_path}

Overall Depth Score: {depth.get('overall_depth_score', 0):.2f}

Term Coverage:
"""
        for term_cat, info in terms.items():
            quality_info = quality.get(term_cat, {})
            content += f"\n{term_cat}:\n"
            content += f"  - Occurrences: {info.get('count', 0)}\n"
            content += f"  - Pages: {info.get('pages', [])}\n"
            content += f"  - Quality: {quality_info.get('status', 'unknown')}\n"
            content += f"  - Score: {quality_info.get('score', 0):.2f}\n"
        
        issues = depth.get("issues", [])
        if issues:
            content += f"\nIssues Found:\n"
            for issue in issues:
                content += f"  - {issue}\n"
        
        confidence = min(0.9, 0.3 + (depth.get("overall_depth_score", 0) * 0.6))
    
    evidence_list.append(Evidence(
        evidence_id=f"{evidence_id}_theoretical_depth",
        evidence_type="theoretical_depth",
        content=content,
        source=doc_path,
        timestamp=datetime.utcnow(),
        metadata=analysis_result.get("theoretical_depth", {}),
        confidence=confidence
    ))
    
    # Report accuracy evidence
    if not error_message:
        accuracy_content = f"""
Report Accuracy Assessment for: {doc_path}

Analysis performed:
- PDF parsing: {'Success' if analysis_result.get("parsing_success") else 'Failed'}
- Term extraction: {'Success' if analysis_result.get("terms_found") else 'Failed'}
- Depth evaluation: {'Success' if analysis_result.get("theoretical_depth", {}).get("overall_depth_score", 0) > 0 else 'Incomplete'}

The document {'appears to provide substantive theoretical content' if analysis_result.get("theoretical_depth", {}).get("overall_depth_score", 0) > 0.5 else 'may lack detailed theoretical explanations'}.
"""
    else:
        accuracy_content = f"Report accuracy could not be determined: {error_message}"
    
    evidence_list.append(Evidence(
        evidence_id=f"{evidence_id}_report_accuracy",
        evidence_type="report_accuracy",
        content=accuracy_content,
        source=doc_path,
        timestamp=datetime.utcnow(),
        metadata={"analysis_complete": not bool(error_message)},
        confidence=0.85 if not error_message else 0.3
    ))
    
    return evidence_list


def analyze_document(doc_path: str) -> dict[str, Any]:
    """
    Perform complete document analysis.
    
    Args:
        doc_path: Path to the document (PDF or text)
        
    Returns:
        Complete analysis results
    """
    result = {
        "doc_path": doc_path,
        "parsing_success": False,
        "text_extracted": False,
        "chunks_created": False,
        "terms_found": {},
        "theoretical_depth": {},
        "error": None
    }
    
    try:
        path = Path(doc_path)
        
        if not path.exists():
            result["error"] = f"Document not found: {doc_path}"
            return result
        
        # Extract text based on file type
        if path.suffix.lower() == ".pdf":
            if not PDF_AVAILABLE:
                result["error"] = "PDF support requires PyPDF2. Install with: pip install pypdf"
                return result
            text = extract_text_from_pdf(doc_path)
        else:
            # Assume text file
            with open(doc_path, "r", encoding="utf-8") as f:
                text = f.read()
        
        result["text_extracted"] = True
        result["parsing_success"] = True
        
        # Chunk document
        chunks = chunk_document(text)
        result["chunks_created"] = True
        result["chunk_count"] = len(chunks)
        
        # Search for terms
        term_occurrences = search_for_terms(chunks)
        result["terms_found"] = {
            k: [{"term": occ.term, "page": occ.page_number, "explained": occ.is_explained}
                for occ in v]
            for k, v in term_occurrences.items()
        }
        
        # Analyze theoretical depth
        depth_analysis = analyze_theoretical_depth(term_occurrences)
        result["theoretical_depth"] = depth_analysis
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

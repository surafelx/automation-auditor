# Automaton Auditor

Production-grade forensic multi-agent evidence collection system using LangGraph.

## Overview

The Automaton Auditor is a sophisticated LangGraph-based system designed to audit and analyze LangGraph implementations. It employs parallel agents ("detectives") to collect evidence about repository structure, graph orchestration patterns, and theoretical depth of documentation.

## Architecture

```
START → ContextBuilder → [RepoInvestigator || DocAnalyst] → EvidenceAggregator → END
```

### Components

- **ContextBuilder**: Prepares context for parallel detectives
- **RepoInvestigator**: Clones repository, analyzes git history, parses graph.py via AST
- **DocAnalyst**: Analyzes documentation for theoretical depth
- **EvidenceAggregator**: Merges evidence from parallel agents without overwriting

## Installation

### Using uv (Recommended)

```bash
# Install dependencies
uv pip install -e .

# Install dev dependencies
uv pip install -e ".[dev]"
```

### Using pip

```bash
pip install -e .
```

## Usage

### Basic Usage

```python
from src import run_audit

# Run audit with repository
result = run_audit(
    repo_url="https://github.com/langchain-ai/langgraph",
    doc_path="./docs/theory.pdf"
)

# Access evidence
print(f"Evidence collected: {len(result['evidence'])} items")
```

### Using the Graph Directly

```python
from src import create_audit_graph, create_initial_state

# Create graph
graph = create_audit_graph()

# Create initial state
initial_state = create_initial_state(
    repo_url="https://github.com/example/repo",
    doc_path="./docs/analysis.pdf"
)

# Run with streaming
for state in graph.stream(initial_state):
    print(state)
```

## Evidence Types

### RepoInvestigator Outputs

| Key | Description |
|-----|-------------|
| `git_forensic_analysis` | Git commit history analysis |
| `graph_orchestration` | StateGraph instantiation detection |
| `state_management_rigor` | Edge definitions and state structure |

### DocAnalyst Outputs

| Key | Description |
|-----|-------------|
| `theoretical_depth` | Analysis of key terms (Dialectical Synthesis, Fan-In/Fan-Out, etc.) |
| `report_accuracy` | Assessment of documentation quality |

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

## Development

### Running Tests

```bash
pytest
```

### Type Checking

```bash
mypy src
```

### Linting

```bash
ruff check src
```

## Project Structure

```
src/
├── __init__.py          # Package exports
├── state.py             # Typed state definitions
├── graph.py             # LangGraph infrastructure
├── nodes/
│   ├── __init__.py
│   └── detectives.py    # Detective nodes
└── tools/
    ├── __init__.py
    ├── repo_tools.py    # Git operations
    └── doc_tools.py     # PDF analysis
```

## Security

- Git operations use `subprocess.run` with `capture_output=True`
- Repositories are cloned to temporary directories
- No secrets are stored in the repository
- Authentication errors are handled gracefully

## Extensibility

The architecture supports future extensions:

- **Judge Nodes**: For evaluating evidence quality
- **ChiefJustice Synthesis**: For final verdict generation
- **Conditional Edges**: For complex routing logic
- **Error Handling**: Comprehensive error management

## License

MIT

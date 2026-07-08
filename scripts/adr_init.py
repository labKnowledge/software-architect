#!/usr/bin/env python3
"""
adr_init.py — Initialize an ADR (Architectural Decision Records) directory
in a project with template and index file.

Usage:
    python adr_init.py /path/to/project
    python adr_init.py /path/to/project --dir docs/decisions
"""

import argparse
import sys
from pathlib import Path


ADR_TEMPLATE = """# ADR-{number}: {title}

## Status

Proposed

## Date

{date}

## Decision Drivers

- {{Driver 1}}
- {{Driver 2}}

## Considered Options

1. {{Option A}}
2. {{Option B}}

## Decision Outcome

**Chosen option**: "{{Option X}}", because {{justification}}.

### Positive Consequences

- {{consequence}}

### Negative Consequences

- {{consequence}}

## Validation

{{How will we verify this decision remains correct? Metrics, fitness functions, observability.}}
"""

ADR_INDEX = """# Architecture Decision Records

This directory contains Architectural Decision Records (ADRs) for the project.
Each ADR captures a single architecturally significant decision, its context, and consequences.

## Guidelines

- Use the MADR format (see `ADR-0000-template.md`)
- ADRs are numbered sequentially; never renumber
- When changing a decision, create a new ADR and mark the old one as "Superseded by ADR-XXXX"
- Reference ADRs in code with comments: `// See ADR-XXXX for rationale` or `# See ADR-XXXX for rationale`
- Never delete ADRs — even deprecated ones provide historical context

## Active Decisions

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| — | No decisions recorded yet | — | — |

## Superseded Decisions

| ADR | Title | Superseded By | Original Date |
|-----|-------|---------------|---------------|
| — | No superseded decisions | — | — |
"""


def init_adr_directory(project_path: str, adr_dir: str = "docs/adr") -> None:
    """Initialize the ADR directory structure."""
    root = Path(project_path).resolve()

    if not root.exists():
        print(f"Error: Project path {root} does not exist")
        sys.exit(1)

    adr_path = root / adr_dir

    if adr_path.exists():
        print(f"ADR directory already exists at {adr_path}")
        # Check if template and index exist
        template_path = adr_path / "ADR-0000-template.md"
        index_path = adr_path / "README.md"

        if not template_path.exists():
            template_path.write_text(ADR_TEMPLATE.strip() + "\n")
            print(f"Created ADR template at {template_path}")

        if not index_path.exists():
            index_path.write_text(ADR_INDEX.strip() + "\n")
            print(f"Created ADR index at {index_path}")

        return

    # Create directory
    adr_path.mkdir(parents=True, exist_ok=True)
    print(f"Created ADR directory at {adr_path}")

    # Create template
    template_path = adr_path / "ADR-0000-template.md"
    template_path.write_text(ADR_TEMPLATE.strip() + "\n")
    print(f"Created ADR template at {template_path}")

    # Create index
    index_path = adr_path / "README.md"
    index_path.write_text(ADR_INDEX.strip() + "\n")
    print(f"Created ADR index at {index_path}")

    # Create first ADR placeholder (example)
    first_adr = adr_path / "ADR-0001-example-architecture-decision.md"
    example_content = ADR_TEMPLATE.format(
        number="0001",
        title="Example Architecture Decision",
        date="YYYY-MM-DD",
    )
    first_adr.write_text(example_content.strip() + "\n")
    print(f"Created example ADR at {first_adr}")
    print(f"\nNote: ADR-0001 is an example. Replace it with your first real decision.")


def main():
    parser = argparse.ArgumentParser(
        description='Initialize an ADR directory in a project'
    )
    parser.add_argument('path', help='Root path of the project')
    parser.add_argument('--dir', default='docs/adr',
                        help='ADR directory path relative to project root (default: docs/adr)')
    args = parser.parse_args()

    init_adr_directory(args.path, args.dir)
    print("\nADR directory initialized! Next steps:")
    print("1. Replace ADR-0001 with your first real architectural decision")
    print("2. Update the index table in docs/adr/README.md")
    print("3. Reference ADRs in your code with comments like: # See ADR-0001 for rationale")


if __name__ == '__main__':
    main()

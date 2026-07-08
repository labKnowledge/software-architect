# Architectural Decision Records (ADRs) — Complete Guide

## What Are ADRs?

An Architectural Decision Record captures a single architecturally significant decision, its context, and consequences. ADRs are the primary mechanism for maintaining an architecture decision log that survives personnel changes and enables informed evolution.

**Key definitions:**
- **Architectural Decision (AD)**: A justified design choice that addresses a functional or non-functional requirement that is architecturally significant.
- **Architecturally Significant Requirement (ASR)**: A requirement that has a measurable effect on the architecture and quality of a software system.
- **ADR**: A document capturing a single AD and its rationale.

## When to Write an ADR

| Trigger | Example |
|---------|---------|
| Choosing a fundamental technology | "Use PostgreSQL vs MongoDB" |
| Defining a structural boundary | "Adopt hexagonal architecture for payment service" |
| Establishing a cross-cutting concern | "All inter-service communication via events" |
| Rejecting a popular alternative | "Why we chose monorepo over polyrepo" |
| Changing a previous decision | "Migrating from REST to gRPC for internal APIs" |
| Resolving a significant trade-off | "Accept eventual consistency for performance" |

**Rule of thumb**: If the decision would cost more than a week to reverse, or affects more than one team/module, write an ADR.

## ADR Lifecycle

```
Proposed → Accepted → [Deprecated | Superseded]
```

- **Proposed**: Under discussion, not yet approved.
- **Accepted**: Approved and in effect.
- **Deprecated**: No longer in effect, but kept for historical reference.
- **Superseded**: Replaced by a newer ADR (link to the superseding ADR).

**Important**: Never delete ADRs. Even deprecated ones provide valuable historical context.

## ADR Format Templates

### Template 1: Nygard Format (Lightweight)

Best for: Small teams, quick decisions, when formality is counterproductive.

```markdown
# ADR-{NNNN}: {Title}

## Status

{Proposed | Accepted | Deprecated | Superseded by ADR-XXXX}

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?
```

### Template 2: MADR (Markdown Any Decision Records — Structured)

Best for: Most situations. Provides enough structure for informed decisions without excessive ceremony.

```markdown
# ADR-{NNNN}: {Title}

## Status

{Proposed | Accepted | Deprecated | Superseded by ADR-XXXX}

## Date

{YYYY-MM-DD}

## Decision Drivers

- {Driver 1, e.g., latency requirements}
- {Driver 2, e.g., team expertise}
- {Driver 3, e.g., regulatory compliance}

## Considered Options

1. {Option A}
2. {Option B}
3. {Option C}

## Decision Outcome

**Chosen option**: "{Option X}", because {justification}.

### Positive Consequences

- {consequence}

### Negative Consequences

- {consequence}

## Pros and Cons of the Options

### {Option A}

- Good, because {argument}
- Bad, because {argument}

### {Option B}

- Good, because {argument}
- Bad, because {argument}

## Validation

{How will we know the decision was correct? Metrics, fitness functions, observability.}
```

### Template 3: Y-Statement (Concise)

Best for: Quick decisions, supplementary documentation, when full MADR is overkill.

```markdown
# ADR-{NNNN}: {Title}

In the context of {CONTEXT},
facing {DECISION DRIVERS},
we decided for {OPTION}
to achieve {QUALITY ATTRIBUTES},
accepting {DOWNSIDES / TRADE-OFFS}.
```

## ADR Maintenance Best Practices

1. **Store in version control** alongside code in `docs/adr/` directory.
2. **Number sequentially** — never renumber; use `Superseded by ADR-XXXX` links for supersessions.
3. **Never delete** — even deprecated ADRs provide historical context that prevents revisiting settled decisions.
4. **Reference in code** — use comments like `// See ADR-0012 for rationale` at decision implementation points.
5. **Review in PRs** — require ADR updates when architectural changes are made. Add to PR template.
6. **Maintain an index** — keep `docs/adr/README.md` with a summary table of all ADRs.
7. **Template enforcement** — use a linter or CI check to validate ADR format.
8. **Link between ADRs** — when one decision depends on another, use explicit cross-references.

## ADR Index Template

Maintain this as `docs/adr/README.md`:

```markdown
# Architecture Decision Records

## Active Decisions

| ADR | Title | Status | Date | Impact |
|-----|-------|--------|------|--------|
| ADR-0001 | Use PostgreSQL as primary data store | Accepted | 2024-01-15 | All data access |
| ADR-0002 | Adopt hexagonal architecture for core services | Accepted | 2024-02-01 | Module structure |
| ADR-0003 | Use event-driven communication between services | Accepted | 2024-03-10 | Integration |

## Superseded Decisions

| ADR | Title | Superseded By | Original Date | Reason |
|-----|-------|---------------|---------------|--------|
| ADR-0004 | REST for external APIs, gRPC for internal | ADR-0008 | 2024-04-01 | gRPC not needed at current scale |

## Guidelines
- All new ADRs should use the MADR format (see `templates/adr-template.md`)
- ADRs are numbered sequentially; never renumber
- When changing a decision, create a new ADR and mark the old one as "Superseded by ADR-XXXX"
- Reference ADRs in code with comments: `// See ADR-XXXX for rationale`
```

## ADR Examples

### Example: Choosing a Database

```markdown
# ADR-0001: Use PostgreSQL as Primary Data Store

## Status

Accepted

## Date

2024-01-15

## Decision Drivers

- Need ACID compliance for financial transactions
- Team has deep PostgreSQL expertise (5+ years)
- Requires complex queries with joins and aggregations
- Must support JSON columns for flexible metadata

## Considered Options

1. PostgreSQL
2. MongoDB
3. MySQL

## Decision Outcome

**Chosen option**: "PostgreSQL", because it provides ACID compliance, excellent JSON support (avoiding the need for a separate document store), and the team already has operational expertise.

### Positive Consequences

- Strong consistency guarantees for financial data
- JSON columns provide schema flexibility where needed
- Team can operate it without additional training
- Excellent tooling for monitoring and backup

### Negative Consequences

- Horizontal scaling requires more effort than MongoDB
- Schema migrations need careful planning
- Connection pooling is more complex than with simpler databases

## Pros and Cons of the Options

### PostgreSQL

- Good, because ACID compliance ensures data integrity
- Good, because JSONB columns provide document-store flexibility
- Good, because team expertise reduces operational risk
- Bad, because horizontal scaling requires Citus or manual sharding

### MongoDB

- Good, because horizontal scaling is built-in
- Good, because schema-less approach allows rapid iteration
- Bad, because eventual consistency by default conflicts with financial requirements
- Bad, because team lacks operational experience

### MySQL

- Good, because widely supported and well-understood
- Bad, because JSON support is less mature than PostgreSQL's
- Bad, because fewer advanced query features

## Validation

- All financial transactions must pass ACID compliance tests
- Query performance must stay under 50ms for 95th percentile
- Monthly review of connection pool utilization
```

### Example: Adopting Clean Architecture

```markdown
# ADR-0005: Adopt Clean Architecture for Order Processing Module

## Status

Accepted

## Date

2024-06-01

## Decision Drivers

- Order processing logic is currently tangled with framework code
- Business rules are duplicated across controllers and services
- Testing business logic requires database and HTTP server
- Framework migration (Express → Fastify) would require rewriting business logic

## Considered Options

1. Clean Architecture (dependency rule)
2. Hexagonal Architecture (ports and adapters)
3. Keep current structure with better separation

## Decision Outcome

**Chosen option**: "Clean Architecture", because the dependency rule is the simplest to explain and enforce. The domain layer has zero framework imports, making it independently testable and framework-agnostic.

### Positive Consequences

- Business logic can be tested without any infrastructure
- Framework changes only affect the infrastructure layer
- Clear separation between use cases makes the codebase navigable
- New developers can understand the architecture from the directory structure

### Negative Consequences

- More files and interfaces to maintain
- Simple CRUD operations require more boilerplate
- Need to train team on dependency inversion pattern

## Validation

- Fitness function: domain layer must have zero infrastructure imports
- Fitness function: all use cases must be testable without database
- Code review checklist: new PRs must respect layer boundaries
```

## Integrating ADRs with CI/CD

Add ADR validation to your CI pipeline:

```yaml
# .github/workflows/architecture.yml
name: Architecture Checks
on: [pull_request]

jobs:
  adr-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check ADR format
        run: |
          for f in docs/adr/ADR-*.md; do
            if ! grep -q "## Status" "$f"; then
              echo "ADR $f missing Status section"
              exit 1
            fi
            if ! grep -q "## Decision" "$f" || ! grep -q "## Context" "$f"; then
              echo "ADR $f missing required sections"
              exit 1
            fi
          done

      - name: Architecture validation
        run: python scripts/architecture_validator.py .
```

This ensures that ADRs are properly formatted and architectural rules are enforced on every pull request.

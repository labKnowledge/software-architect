# Code Analysis Techniques — Coupling, Cohesion, and Dependency Metrics

## Overview

Quantitative analysis of a codebase reveals architectural issues that code review alone might miss. This guide covers the key metrics, how to calculate them, and what they tell you about your architecture.

---

## Coupling Metrics

### Afferent Coupling (Ca) — "Who depends on me?"

The number of modules that depend on this module. High Ca means the module is **responsible** — many other modules rely on it. Changes to it have wide impact.

**Interpretation**:
- High Ca: This module is a foundation. It should be **stable** (rarely changes), **abstract** (defined by interfaces), and **well-tested**.
- Low Ca: This module is independent. It can change freely without affecting others.

### Efferent Coupling (Ce) — "Who do I depend on?"

The number of modules this module depends on. High Ce means the module is **dependent** — it relies on many others and is sensitive to their changes.

**Interpretation**:
- High Ce: This module is fragile. Changes in any of its dependencies could break it.
- Low Ce: This module is self-contained. It's resilient to external changes.

### Instability (I) — "How hard is this to change?"

```
I = Ce / (Ca + Ce)
```

- **I = 0**: Maximally stable (many depend on it, it depends on nothing). Hard to change but many rely on it.
- **I = 1**: Maximally unstable (nothing depends on it, it depends on many). Easy to change, safe to modify.

**Rule**: Stable modules (low I) should be abstract (defined by interfaces). Unstable modules (high I) should be concrete (implementations). This is the **Dependency Inversion Principle** in metric form.

### Abstractness (A) — "How abstract is this module?"

```
A = Number of abstract types / Total number of types
```

Abstract types: interfaces, abstract classes, protocols, type aliases.
Concrete types: classes with implementation, concrete functions.

- **A = 1**: Completely abstract (only interfaces/protocols)
- **A = 0**: Completely concrete (only implementations)

### Distance from Main Sequence (D) — "Is this module well-balanced?"

```
D = |A + I - 1|
```

The "Main Sequence" is the ideal relationship between abstractness and instability: highly stable modules should be abstract, and highly unstable modules should be concrete.

- **D ≈ 0**: Well-balanced. The module's abstractness matches its instability.
- **D ≈ 1**: Problem zone:
  - **Zone of Pain** (A ≈ 0, I ≈ 0): Stable but concrete. Hard to change because many depend on it, and there's no abstraction to allow variation. Example: a concrete utility class used everywhere.
  - **Zone of Uselessness** (A ≈ 1, I ≈ 1): Abstract but nobody depends on it. Wasted abstraction. Example: an interface with no clients.

**Visualization**:
```
A (Abstractness)
1 │         Zone of Uselessness
  │    *  (abstract but unused)
  │
  │              Main Sequence
  │           ╲  (ideal line A + I = 1)
  │             ╲
  │              ╲
  │    Zone of Pain
  │    * (concrete but heavily depended upon)
0 └────────────────────────── I (Instability)
  0                          1
```

---

## Cohesion Metrics

### LCOM4 (Lack of Cohesion of Methods)

Measures how cohesive a class's methods are — do they operate on the same data, or are they unrelated?

**Calculation**: Build a graph where methods are connected if they access the same instance variables. Count the number of connected components.

- **LCOM4 = 1**: Perfect cohesion — all methods work on the same data.
- **LCOM4 > 1**: The class has multiple responsibilities. Consider splitting it.

**Rule of thumb**: If LCOM4 > 2, the class should probably be split.

### Relational Cohesion

```
RC = (Number of internal relationships) / (Number of types)
```

Where internal relationships are: inheritance, composition, aggregation, and association between types within the module.

- **RC > 1.0**: Good cohesion — types in the module are well-connected.
- **RC < 0.5**: Low cohesion — types are grouped arbitrarily.

---

## Dependency Analysis

### Circular Dependencies

A circular dependency occurs when Module A depends on Module B, and Module B also depends on Module A (directly or transitively).

**Why circular dependencies are bad**:
- Impossible to understand one module without understanding the other
- Can't test modules in isolation
- Can't deploy modules independently
- Changes propagate unpredictably

**Detection**: Run `python $SKILL_DIR/scripts/dependency_analyzer.py /path/to/project` to find cycles.

**Remediation**:
1. Extract the shared dependency into a separate module
2. Use the **Observer** or **Event** pattern to break the cycle
3. Apply the **Dependency Inversion Principle** — both modules depend on an interface, not on each other

### Layer Violations

A layer violation occurs when code in one architectural layer imports from a layer it shouldn't.

**Common violations**:
- Domain importing infrastructure (database, framework)
- UI importing database directly
- Infrastructure depending on UI code

**Detection**: Run `python $SKILL_DIR/scripts/architecture_validator.py /path/to/project`

### Dependency Direction

In a well-structured application, dependencies should flow in one direction:
```
Presentation → Application → Domain ← Infrastructure
```

Domain is at the center and depends on nothing. Everything else depends on Domain (directly or transitively). Infrastructure depends on Domain's interfaces and implements them.

---

## Static Analysis Approach

Follow this 6-step approach when analyzing a codebase:

### Step 1: Identify the Technology Stack
- Read package.json, pyproject.toml, go.mod, or equivalent
- Identify languages, frameworks, ORMs, databases, messaging systems
- Check for conflicting dependencies (multiple ORMs, multiple state management libraries)

### Step 2: Map the Directory Structure
- Read the top-level directory layout
- Identify whether the code is organized by layer (controllers/, models/, services/) or by feature (orders/, billing/, auth/)
- Look for architectural config files (architecture.config.json, .importlinter)

### Step 3: Build the Dependency Graph
- Use `scripts/dependency_analyzer.py` for Python projects
- Use `dependency-cruiser` for JavaScript/TypeScript projects
- For other languages, analyze import statements manually

### Step 4: Calculate Metrics
- Afferent/Efferent coupling per module
- Instability per module
- Abstractness per module
- Distance from Main Sequence
- LCOM4 for large classes

### Step 5: Detect Violations
- Circular dependencies
- Layer violations
- Mixed data access patterns
- Framework coupling in domain
- Excessive coupling (modules with Ce > 10)

### Step 6: Generate Report
Use the Diagnostic Report format from SKILL.md.

---

## Tool Matrix by Ecosystem

| Ecosystem | Dependency Analysis | Architecture Testing | Import Linting |
|-----------|-------------------|---------------------|---------------|
| **Python** | `scripts/dependency_analyzer.py` | `scripts/architecture_validator.py` + pytest | import-linter |
| **TypeScript/JS** | dependency-cruiser | Jest + custom fitness functions | eslint-plugin-boundaries |
| **Java** | ArchUnit | ArchUnit | ArchUnit |
| **.NET** | NetArchTest | NetArchTest | NetArchTest |
| **Go** | Custom analysis | Custom tests | govet + custom linters |
| **Rust** | cargo-deny | Custom tests | Custom linters |

---

## Metrics Thresholds

These are general guidelines. Adjust based on your project's specific needs.

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Circular Dependencies | 0 | 1-2 | 3+ |
| Afferent Coupling (per module) | < 10 | 10-20 | > 20 |
| Efferent Coupling (per module) | < 10 | 10-15 | > 15 |
| Distance from Main Sequence | < 0.3 | 0.3-0.5 | > 0.5 |
| LCOM4 (per class) | 1 | 2 | > 2 |
| Relational Cohesion (per module) | > 1.0 | 0.5-1.0 | < 0.5 |
| Files > 300 lines | < 5% | 5-10% | > 10% |

When metrics cross from Warning to Critical, it's time to refactor. When they cross from Healthy to Warning, it's time to discuss (and possibly write an ADR about how to handle the trend).

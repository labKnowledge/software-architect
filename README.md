# Software Architect

**Repository:** [github.com/eligapris/software-architect](https://github.com/eligapris/software-architect)

An agent skill for **Cursor**, **Claude Code**, **Codex**, **Qwen Code**, and any skills-compatible agent. It acts as a senior software architecture consultant — analyzes your application holistically, recommends sustainable patterns, enforces consistency across features, and documents decisions so future sessions build on prior work instead of contradicting it.

## What it does

- **Architecture reviews** — assess patterns, coupling, consistency, and technical debt
- **Feature integration** — decide where new features belong and how they should connect
- **Technology decisions** — compare options against your existing stack and constraints
- **ADR workflow** — capture significant decisions in Architectural Decision Records
- **Fitness functions** — suggest tests and validation rules that enforce architectural boundaries
- **Project scripts** — dependency analysis, structure validation, and ADR scaffolding for your repos

The skill follows a five-step workflow: **Discover → Diagnose → Decide → Document → Defend**.

## Requirements

| Component | Requirement |
|-----------|-------------|
| Agent | Cursor, Claude Code, Codex, Qwen Code, or any skills-compatible agent |
| Scripts | Python 3.8+ (stdlib only — no pip install needed) |
| Your project | Optional: `docs/adr/` and `architecture.config.json` for full validation |

## Installation

### Recommended — Skills CLI (`npx skills`)

The fastest way to install for Cursor, Claude Code, Codex, Qwen Code, and other supported agents:

```bash
npx skills add eligapris/software-architect -g -y
```

| Flag | Purpose |
|------|---------|
| `-g` | Install globally (user-level, all projects) |
| `-y` | Skip confirmation prompts |

**Verify / update:**

```bash
npx skills check                       # check for updates
npx skills update                      # update installed skills
```

**Listing page:** [skills.sh/eligapris/software-architect/software-architect](https://skills.sh/eligapris/software-architect/software-architect)

> Install with the `npx skills add` command above. `npx skills find` only surfaces skills after skills.sh has indexed install telemetry — use the direct `add` / page URL until then.

> **Scripts note:** `npx skills add` installs the agent skill (`SKILL.md`) for chat use. For the Python tooling (`scripts/`, `templates/`, `references/`), clone the full repository (below).

### Full install — git clone (includes scripts)

Use this when you want ADR scaffolding, dependency analysis, and architecture validation on your projects:

**Cursor**

```bash
git clone https://github.com/eligapris/software-architect.git ~/.cursor/skills/software-architect
```

**Claude Code**

```bash
git clone https://github.com/eligapris/software-architect.git ~/.claude/skills/software-architect
```

**Codex**

```bash
git clone https://github.com/eligapris/software-architect.git ~/.codex/skills/software-architect
```

**Qwen Code**

```bash
git clone https://github.com/eligapris/software-architect.git ~/.qwen/skills/software-architect
```

### Project-level (team shared)

```bash
git clone https://github.com/eligapris/software-architect.git .cursor/skills/software-architect
```

Commit `.cursor/skills/software-architect/` so teammates get the same guidance.

### Manual copy

```bash
git clone https://github.com/eligapris/software-architect.git /tmp/software-architect
cp -r /tmp/software-architect ~/.cursor/skills/software-architect
```

### Verify installation

Restart the agent or start a new chat. The skill should appear in available skills when its trigger terms match your request (see [Usage](#usage) below).

> **Note:** Do not install skills under `~/.cursor/skills-cursor/` — that directory is reserved for Cursor built-in skills.

## Usage

### In chat (primary)

The agent loads this skill automatically when you ask architecture-related questions. You can also be explicit:

```
Use the software-architect skill to review my project structure.
```

```
How should I integrate a notifications feature into this modular monolith?
```

```
Should I add GraphQL here, or stay with REST? Check against our existing ADRs.
```

**Trigger phrases** that typically invoke the skill:

- system design, architecture decisions, feature integration strategy
- technology choices, migration planning, technical debt
- ADR, bounded contexts, clean/hexagonal architecture
- microservices, modular monolith, coupling, cohesion, fitness functions

### What the agent does when invoked

1. Reads `SKILL.md` for the core workflow
2. Loads reference files as needed (`references/patterns.md`, `references/anti-patterns.md`, etc.)
3. Inspects your project (structure, config files, existing ADRs)
4. Delivers a structured report, integration plan, or ADR draft
5. Recommends fitness functions and validation rules to enforce decisions

### Project tooling (run on your codebase)

Scripts live in `scripts/` and are meant to be run **against your application repo**, not the skill folder itself.

Set a convenience variable (requires the **full git clone**, not `npx skills` alone):

```bash
export SKILL_DIR=~/.cursor/skills/software-architect   # or ~/.codex/skills/software-architect
```

#### Initialize ADR documentation

Creates `docs/adr/` with a template and index:

```bash
python "$SKILL_DIR/scripts/adr_init.py" /path/to/your-project
python "$SKILL_DIR/scripts/adr_init.py" /path/to/your-project --dir docs/decisions
```

#### Analyze Python dependencies

Detects cycles, layer violations, and coupling metrics:

```bash
python "$SKILL_DIR/scripts/dependency_analyzer.py" /path/to/your-project
python "$SKILL_DIR/scripts/dependency_analyzer.py" /path/to/your-project --format json
python "$SKILL_DIR/scripts/dependency_analyzer.py" /path/to/your-project \
  --check-layers \
  --layers '{"domain":[],"application":["domain"],"infrastructure":["domain","application"]}'
```

#### Validate project structure

Checks module boundaries and architectural rules (Python and TypeScript/JavaScript):

```bash
# Copy and customize the template first
cp "$SKILL_DIR/templates/architecture-config.json" /path/to/your-project/architecture.config.json

python "$SKILL_DIR/scripts/architecture_validator.py" /path/to/your-project
python "$SKILL_DIR/scripts/architecture_validator.py" /path/to/your-project --config architecture.config.json
python "$SKILL_DIR/scripts/architecture_validator.py" /path/to/your-project --language typescript
```

## Skill layout

```
software-architect/
├── SKILL.md                          # Core workflow and routing (always loaded first)
├── README.md                         # This file
├── references/
│   ├── adr-guide.md                  # ADR lifecycle and templates
│   ├── patterns.md                   # Architecture patterns and selection guide
│   ├── anti-patterns.md              # Detection and remediation catalog
│   ├── analysis.md                   # Coupling/cohesion analysis techniques
│   └── fitness-functions.md          # Test examples for architectural rules
├── scripts/
│   ├── adr_init.py                   # Scaffold ADR directory in a project
│   ├── dependency_analyzer.py        # Python dependency and cycle analysis
│   └── architecture_validator.py     # Structure validation against config rules
└── templates/
    ├── adr-template.md               # MADR-format ADR template
    └── architecture-config.json      # Default validator configuration
```

## Example workflows

### New project

1. Ask the agent: *"I'm starting a new Next.js app with a 2-person team — what architecture should I use?"*
2. Run `adr_init.py` in the project
3. Write ADR-0001 documenting the chosen pattern
4. Copy `architecture-config.json`, adjust paths, add to CI

### Add a feature to an existing app

1. Ask: *"Where should user preferences live in this codebase?"*
2. Agent checks existing ADRs and module boundaries
3. You get a **Feature Integration Plan** with module assignment, data flow, and consistency checks

### Fix architectural drift

1. Run `dependency_analyzer.py` and `architecture_validator.py`
2. Ask: *"My codebase has mixed ORM usage — help me consolidate"*
3. Agent identifies the dominant pattern, plans migration, and suggests linter/CI rules

### Full architecture review

Ask:

```
Review the architecture of this repo. Check consistency, document gaps,
and list ADRs and fitness functions I should add.
```

You receive an **Architecture Review Report** with critical issues, warnings, and prioritized recommendations.

## Session continuity

The skill is designed so decisions survive across agent sessions:

- Store ADRs in `docs/adr/` (or your chosen directory)
- Keep `architecture.config.json` aligned with enforced rules
- Reference ADR numbers in code comments (`// See ADR-0003`)
- On new sessions, the agent reads existing ADRs before recommending changes

## Core principles

1. **Consistency over novelty** — one coherent approach beats a better pattern used halfway
2. **Boundaries over flexibility** — clear module limits prevent architectural decay
3. **Explicit over implicit** — decisions live in ADRs, not tribal knowledge
4. **Incremental over revolutionary** — prefer Strangler Fig migrations over big rewrites
5. **Validate with code** — fitness functions turn rules into enforceable guarantees

## License

See the repository root for license terms, if applicable.

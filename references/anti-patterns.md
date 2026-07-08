# Anti-Patterns Catalog — Detection, Consequences, and Remediation

## Overview

Anti-patterns are recurring architectural mistakes that seem like good ideas at the time but create significant problems as the codebase grows. This catalog helps you detect them early and provides concrete remediation strategies.

---

## 1. Big Ball of Mud

**What it is**: A system with no discernible architecture. Code is tangled, dependencies go in every direction, and there are no clear boundaries between modules.

**Detection heuristics**:
- Import graph shows high connectivity with no clear layer structure
- Changes in one module unpredictably break unrelated modules
- Developers can't explain which module owns what functionality
- No directory structure convention is followed

**Consequences**: Changes are risky and expensive. Fear of change leads to workarounds, which make the problem worse. New developers take months to become productive.

**Remediation**:
1. Identify natural module boundaries (group related functionality)
2. Create module API surfaces (public interfaces)
3. Move cross-cutting code to shared modules
4. Add fitness functions to enforce boundaries
5. Evolve incrementally — don't try to fix everything at once

---

## 2. Mixed Data Management

**What it is**: Using multiple data access approaches without clear boundaries. E.g., Prisma for some queries, raw SQL for others, a different ORM for yet another feature.

**Detection heuristics**:
- Multiple ORM packages in dependencies
- Some code uses repository pattern, other code queries the database directly
- Different features use different caching strategies
- Same entity type accessed through different abstractions

**Consequences**: Bypassed invariants (ORM lifecycle hooks skipped), inconsistent caching, data integrity violations, schema changes require updating multiple access patterns.

**Remediation**:
1. Adopt the **Repository Abstraction Layer** pattern — domain code never sees the ORM
2. If raw SQL is needed for performance, encapsulate it within a repository method
3. One ORM per project — if you need a different approach, it goes through a separate bounded context
4. Document the canonical data access pattern in an ADR
5. Add architecture validation rule to detect mixed imports

---

## 3. Framework Coupling in Domain

**What it is**: Domain entities and business logic depend on framework-specific decorators, types, or APIs.

**Detection heuristics**:
```typescript
// BAD: Domain entity using framework decorator
@Entity()
export class Order {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  status: string;
}
```
- Domain files import framework packages (e.g., `@nestjs/common`, `@prisma/client`, `typeorm`)
- Business logic only works within the framework's runtime
- Can't test business rules without bootstrapping the framework

**Consequences**: Can't change frameworks without rewriting business logic. Can't test business rules in isolation. Domain model is polluted with infrastructure concerns.

**Remediation**:
1. Domain entities should be plain objects (POJOs/POCOs) with no framework imports
2. Use the **Dependency Inversion Principle** — domain defines interfaces, infrastructure implements them
3. Keep ORM mapping in the infrastructure layer (separate from domain entities)
4. Add fitness function: domain layer must have zero framework imports

---

## 4. Scattered Business Logic

**What it is**: Business rules are distributed across controllers, services, middleware, and UI code instead of being centralized in the domain layer.

**Detection heuristics**:
- Validation logic appears in API controllers AND frontend AND database constraints
- The same business rule is implemented differently in different places
- Changing a business rule requires modifying multiple files
- No single place to look for "what are the rules for X?"

**Consequences**: Rules are inconsistent. Bugs appear because one implementation of a rule differs from another. Fear of changing rules because you might miss one.

**Remediation**:
1. Centralize business rules in the domain layer
2. Use **Domain Services** for rules that span multiple entities
3. Use **Specification Pattern** for complex, composable rules
4. API controllers should only: validate input format, call use case, return response
5. UI should only: validate format, call API, display result

---

## 5. Premature Distribution

**What it is**: Adopting microservices when the team size, domain complexity, or operational maturity doesn't justify it.

**Detection heuristics**:
- 2-3 developers maintaining 10+ services
- Most service-to-service calls are synchronous
- Deploying a feature requires coordinating changes across 3+ services
- Distributed debugging is the norm, not the exception

**Consequences**: Operational overhead drowns the team. Simple changes require deploying multiple services. Network latency and reliability issues dominate. Developer productivity drops.

**Remediation**:
1. Consolidate related services into a **Modular Monolith**
2. Keep independent services only where justified (different scale, different team, different deployment cadence)
3. Use the **Strangler Fig** pattern to merge services back into a monolith

---

## 6. Distributed Monolith

**What it is**: A "microservices" architecture where services are tightly coupled — they share databases, require synchronized deployments, or can't function independently.

**Detection heuristics**:
- Services share a database
- A change to one service requires deploying others simultaneously
- Services call each other's internal APIs synchronously
- No team can independently deploy their service

**Consequences**: All the complexity of microservices with none of the benefits. Harder to develop, deploy, and debug than a monolith would be.

**Remediation**:
1. Give each service its own database (database-per-service pattern)
2. Replace synchronous calls with asynchronous events where possible
3. If services must be deployed together, merge them
4. Define clear API contracts between services

---

## 7. Golden Hammer

**What it is**: Using a familiar technology or pattern for every problem, regardless of fit.

**Detection heuristics**:
- "We always use X" for technology decisions
- Every feature is built the same way regardless of requirements
- Technology choices are based on familiarity, not fitness for purpose
- Resistance to evaluating alternatives

**Consequences**: Suboptimal solutions. Over-engineering simple problems. Under-engineering complex ones.

**Remediation**:
1. Evaluate each technology decision against specific requirements
2. Use the **Considered Options** section of ADRs to document alternatives
3. Proof-of-concept before committing to a technology
4. Time-box evaluation periods to avoid analysis paralysis

---

## 8. Architecture by Implication

**What it is**: Architectural decisions are made implicitly — nobody writes them down, and they're understood through code patterns rather than explicit documentation.

**Detection heuristics**:
- No ADRs or architecture documentation
- New developers learn architecture through code archaeology
- "That's how we've always done it" is the explanation for decisions
- Different developers have different understandings of the architecture

**Consequences**: Architecture is fragile and inconsistent. Decisions are revisited because the rationale isn't documented. New team members make contradictory choices.

**Remediation**:
1. Initialize ADR directory and document existing implicit decisions
2. Write ADRs for the 5 most important architectural decisions
3. Require ADRs for new architectural decisions
4. Add architecture documentation to onboarding

---

## 9. Resume-Driven Development

**What it is**: Choosing technologies based on what's trendy or impressive rather than what solves the problem.

**Detection heuristics**:
- Technology choices justified by "it's modern" or "everyone's using it"
- Complex infrastructure for a simple application
- More time spent on tooling than on features
- Team struggles to operate the chosen stack

**Consequences**: Operational instability. Team burnout. Solutions that are over-engineered for the problem at hand.

**Remediation**:
1. Evaluate technologies against specific requirements (use ADR Considered Options)
2. Prefer boring technology — choose the least interesting solution that meets requirements
3. If you want to learn a new technology, do it in a side project or proof-of-concept, not in production
4. Require operational readiness criteria before adopting new infrastructure

---

## 10. Copy-Paste Architecture

**What it is**: Copying code or patterns from one module to another without understanding or adapting them, leading to divergent implementations of the same concept.

**Detection heuristics**:
- Nearly identical code in multiple modules with minor variations
- Same pattern implemented slightly differently in each occurrence
- Bug fixes need to be applied in multiple places
- No shared abstractions for common patterns

**Consequences**: Bug fixes and feature additions need to be duplicated. Implementations drift apart over time. Code size grows unnecessarily.

**Remediation**:
1. Extract common patterns into shared modules or libraries
2. Use **Template Method** or **Strategy** patterns for variations
3. Create linter rules to detect significant code duplication
4. When you find yourself copying code, stop and extract the shared abstraction first

---

## 11. Shotgun Surgery

**What it is**: A single conceptual change requires modifying many files across the codebase because the related functionality isn't grouped together.

**Detection heuristics**:
- Adding a simple field requires changes in 5+ files
- Related concerns are scattered across different directories
- Every feature touches the same set of files
- Developers dread certain types of changes because they're always complex

**Consequences**: Changes are slow and error-prone. High risk of forgetting to update one of the scattered locations. Merge conflicts are frequent.

**Remediation**:
1. Reorganize by feature/module rather than by technical layer
2. Group related concerns together using **Bounded Contexts**
3. Use the **Single Responsibility Principle** at the module level
4. Each module should encapsulate a complete vertical slice of functionality

---

## 12. Vendor Lock-In

**What it is**: The application is so tightly coupled to a specific vendor's APIs, data formats, or services that switching becomes prohibitively expensive.

**Detection heuristics**:
- Business logic directly calls vendor-specific APIs
- Data is stored in vendor-specific formats
- No abstraction layer between your code and vendor services
- Migration to another vendor requires rewriting core functionality

**Consequences**: Can't negotiate pricing. Can't switch to a better solution. Vendor outages directly impact your users.

**Remediation**:
1. Use the **Anti-Corruption Layer** pattern for all vendor integrations
2. Define your own interfaces; implement adapters for each vendor
3. Keep vendor-specific code in the infrastructure layer
4. Document vendor dependencies in ADRs

---

## 13. Lava Flow

**What it is**: Dead code, abandoned experiments, and obsolete patterns that are left in the codebase because nobody is sure if they're still needed.

**Detection heuristics**:
- Code with no tests and no references
- Commented-out code blocks
- Features that are "deprecated" but never removed
- Configuration for services that no longer exist

**Consequences**: Confusion about what's active and what's not. Fear of removing code because it might break something. Increased codebase size without increased functionality.

**Remediation**:
1. Use version control — deleted code can always be recovered
2. Add dead code detection to CI (e.g., tools that find unreferenced exports)
3. Remove code aggressively; rely on tests to catch breakage
4. If unsure, deprecation markers with dates are better than leaving code indefinitely

---

## 14. Analysis Paralysis

**What it is**: Spending so much time evaluating options that no decision is made, or the decision is made too late to be useful.

**Detection heuristics**:
- Weeks spent on architecture documents with no code written
- Endless comparison tables with no clear winner
- "We need to research more" used to avoid making a choice
- Decision meetings that produce action items for more research

**Consequences**: Time-to-market increases. Team morale decreases. The competition ships while you're still deciding.

**Remediation**:
1. Time-box decisions (e.g., "We'll decide by Friday")
2. Use **Reversibility** as a guide — for easily-reversed decisions, decide fast and adjust
3. Use **Proof of Concept** instead of analysis — build a small prototype instead of comparing features
4. Apply the **2-Way Door** principle: if you can go back, decide quickly; if you can't, deliberate carefully

---

## Anti-Pattern Detection Quick Reference

| Anti-Pattern | Quick Detection | Primary Remedy |
|-------------|----------------|----------------|
| Big Ball of Mud | No directory convention, tangled imports | Define module boundaries |
| Mixed Data Management | Multiple ORMs in dependencies | Repository pattern + one ORM |
| Framework Coupling | Domain imports framework packages | Dependency Inversion |
| Scattered Logic | Same rule in 3+ places | Centralize in domain layer |
| Premature Distribution | Small team, many services | Consolidate to Modular Monolith |
| Distributed Monolith | Services share database | Database per service |
| Golden Hammer | "We always use X" | Evaluate alternatives per decision |
| Architecture by Implication | No ADRs, no architecture docs | Write ADRs |
| Resume-Driven Dev | "It's modern/trendy" | Evaluate against requirements |
| Copy-Paste Architecture | Significant code duplication | Extract shared abstractions |
| Shotgun Surgery | One change touches 5+ files | Organize by feature/module |
| Vendor Lock-In | Direct vendor API calls in business logic | Anti-Corruption Layer |
| Lava Flow | Dead code, commented-out blocks | Delete aggressively |
| Analysis Paralysis | Weeks of docs, no code | Time-box decisions |

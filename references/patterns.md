# Architecture Patterns — Comparison and Implementation Guide

## Pattern Comparison Matrix

| Pattern | Core Principle | Best For | Complexity | Key Risk |
|---------|---------------|----------|------------|----------|
| **Clean Architecture** | Dependency rule: dependencies point inward only | Applications needing long-term maintainability | Medium | Over-engineering for simple apps |
| **Hexagonal (Ports & Adapters)** | Isolate domain from infrastructure via ports | Domain-centric apps, testability | Medium | Port/interface explosion |
| **DDD** | Ubiquitous language, bounded contexts | Complex business domains | High | Over-modeling simple domains |
| **CQRS** | Separate read and write models | High-read/high-write asymmetry | High | Eventual consistency complexity |
| **Event-Driven** | Asynchronous communication via events | Loose coupling, real-time processing | High | Debugging, event ordering |
| **Microservices** | Independently deployable services | Large teams, independent scaling | Very High | Distributed system complexity |
| **Monolithic** | Single deployable unit | Small teams, early-stage products | Low | Can become a big ball of mud |
| **Modular Monolith** | Monolith with strict module boundaries | Growing systems, team boundaries | Medium | Requires discipline to maintain boundaries |

---

## Clean Architecture (Uncle Bob)

**Core Rule**: Dependencies must point **inward**. Outer layers can depend on inner layers; inner layers never depend on outer layers.

```
┌─────────────────────────────────────┐
│           Frameworks & Drivers       │  ← Web, DB, External APIs
│  ┌─────────────────────────────┐    │
│  │     Interface Adapters       │    │  ← Controllers, Gateways, Presenters
│  │  ┌─────────────────────┐    │    │
│  │  │ Application Business │    │    │  ← Use Cases
│  │  │    Rules              │    │    │
│  │  │  ┌─────────────┐    │    │    │
│  │  │  │  Enterprise  │    │    │    │  ← Entities / Domain
│  │  │  │  Business    │    │    │    │
│  │  │  │  Rules       │    │    │    │
│  │  │  └─────────────┘    │    │    │
│  │  └─────────────────────┘    │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

**When to use**: Medium-to-large applications where business logic must be protected from framework/infrastructure churn. Ideal when the domain is stable but infrastructure changes frequently.

**Implementation checklist**:
- Domain entities have zero framework imports
- Use cases define interfaces (ports) for data access
- Controllers call use cases, not domain directly
- Infrastructure implements domain-defined interfaces
- All dependencies cross boundaries via dependency injection

**Directory structure example**:
```
src/
├── domain/              # Enterprise business rules
│   ├── entities/        # Business objects with rules
│   ├── value-objects/   # Immutable, identity-less objects
│   └── interfaces/      # Repository & service interfaces
├── application/         # Application business rules
│   ├── use-cases/       # Single-responsibility use cases
│   └── dtos/            # Data transfer objects
├── infrastructure/      # Frameworks & drivers
│   ├── repositories/    # Implement domain interfaces
│   ├── database/        # ORM config, migrations
│   └── external-apis/   # Third-party integrations
└── presentation/        # Interface adapters
    ├── controllers/     # HTTP handlers
    ├── presenters/      # Response formatting
    └── routes/          # Route definitions
```

---

## Hexagonal Architecture (Ports & Adapters)

**Core Principle**: The domain is at the center. All communication with the outside world happens through **ports** (interfaces) and **adapters** (implementations).

```
                    ┌──────────────┐
     REST API ────→ │   Driving    │
     CLI ─────────→ │   Adapter    │
     gRPC ────────→ │              │
                    └──────┬───────┘
                           │ (calls)
                    ┌──────▼───────┐
                    │    PORT      │ (interface)
                    │  (inbound)   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │    DOMAIN    │  ← Core business logic
                    │   (hexagon)  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │    PORT      │ (interface)
                    │  (outbound)  │
                    └──────┬───────┘
                           │ (implemented by)
                    ┌──────▼───────┐
     PostgreSQL ←── │   Driven     │
     Redis ───────→ │   Adapter    │
     S3 ──────────→ │              │
                    └──────────────┘
```

**Key difference from Clean Architecture**: Hexagonal focuses on the concept of ports/adapters explicitly. Clean Architecture emphasizes the dependency rule across layers. In practice, they're often combined — use Clean Architecture's layer structure with Hexagonal's explicit port/adapter terminology.

**When to use**: When testability is paramount, when you need to swap infrastructure without touching business logic, when the domain is the most valuable part of the system.

---

## Domain-Driven Design (DDD)

**Core Concepts**:

| Concept | Definition |
|---------|-----------|
| **Ubiquitous Language** | Shared vocabulary between domain experts and developers, used in code, docs, and conversation |
| **Bounded Context** | A boundary within which a particular domain model and ubiquitous language apply consistently |
| **Aggregate** | A cluster of domain objects treated as a single unit for data changes |
| **Aggregate Root** | The entry point and guardian of an aggregate's invariants |
| **Domain Event** | Something that happened in the domain that domain experts care about |
| **Repository** | An abstraction that provides collection-like access to aggregates |
| **Value Object** | An immutable object defined by its attributes, not identity |
| **Entity** | An object defined by its identity, not its attributes |
| **Domain Service** | A stateless operation that doesn't belong to any entity or value object |

**Bounded Context Pattern**:
```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Orders Context  │     │   Billing Context │     │  Shipping Context │
│                   │     │                   │     │                   │
│ Order (entity)    │────→│ Invoice (entity)  │────→│ Shipment (entity) │
│ OrderLine (VO)    │     │ Payment (entity)  │     │ Package (entity)  │
│ OrderPlaced (event)│    │ PaymentProcessed  │     │ ShipmentDispatched│
│                   │     │   (event)         │     │   (event)         │
└──────────────────┘     └──────────────────┘     └──────────────────┘
  "Order" = purchase      "Order" = billing item   "Order" = shipment
   request                 reference                request
```

**When to use**: Complex business domains where the language matters as much as the code. When different parts of the business use the same words to mean different things. When the domain model IS the competitive advantage.

**Pitfall**: Over-modeling. Not every application needs aggregates, domain events, and bounded contexts. A CRUD app with simple business rules doesn't need DDD — it needs clean code and good separation of concerns.

---

## CQRS (Command Query Responsibility Segregation)

**Principle**: Separate the read model from the write model.

```
         ┌──────────┐
Command →│  Command  │──→ Write Model (optimized for writes)
         │  Handler  │       (normalized, strict validation)
         └─────┬─────┘
               │
          Domain Event
               │
         ┌─────▼─────┐
         │  Event    │──→ Read Model (optimized for queries)
         │  Handler  │       (denormalized, fast reads)
         └───────────┘
               ↑
         Query ────────────→ Read Model
```

**When to use**:
- Read/write ratio is highly asymmetric (>10:1)
- Complex business rules for writes but simple queries
- Different scaling requirements for reads vs writes
- Event sourcing is needed for auditability

**Pitfalls**:
- Eventual consistency between write and read models
- Increased system complexity (two models to maintain)
- Event replay infrastructure needed
- Debugging becomes harder (which model has the bug?)

**When NOT to use**: If your application is predominantly CRUD with balanced read/write patterns. The overhead of maintaining two models isn't justified.

---

## Event-Driven Architecture

**Patterns**:

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Event Notification** | "Something happened" — minimal data, receiver queries for details | Decoupling systems |
| **Event-Carried State Transfer** | Event includes all data the receiver needs | Reducing callbacks |
| **Event Sourcing** | All state changes stored as immutable events | Audit trails, temporal queries |
| **CQRS + Events** | Write model publishes events that update read models | High-performance reads |

**Event design principles**:
- Events should be named in past tense (`OrderPlaced`, not `PlaceOrder`)
- Events should be immutable once published
- Include enough data to be self-contained (avoid callback necessity)
- Version your event schemas (use schema registry)
- Design for backward compatibility

---

## Microservices

**When justified**:
- Multiple teams (8+ developers) working on the same product
- Independent deployment cadence needed across features
- Different scaling requirements per service
- Technology diversity is required (polyglot persistence, etc.)

**When NOT justified**:
- Small team (< 5 developers)
- Early-stage product where domain boundaries are unclear
- No independent scaling requirements
- Team lacks DevOps maturity

**Service design principles**:
- Each service owns its data (no shared databases)
- Services communicate via well-defined APIs or events
- Each service is independently deployable
- Design for failure (circuit breakers, retries, timeouts)

---

## Monolithic Architecture

**When justified**:
- Small team, early-stage product
- Domain is simple and well-understood
- Time-to-market is the priority
- Infrastructure simplicity is valued

**Evolution path**: Monolith → Modular Monolith → Microservices (only when justified)

---

## Modular Monolith

**The sweet spot for many growing systems.** A single deployable unit with strictly enforced module boundaries.

```
┌──────────────────────────────────────────────┐
│                 Monolith                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ Module A  │ │ Module B  │ │ Module C │     │
│  │ (Orders)  │ │ (Billing) │ │ (Auth)   │     │
│  │           │ │           │ │          │     │
│  │ - API     │ │ - API     │ │ - API    │     │
│  │ - Domain  │ │ - Domain  │ │ - Domain │     │
│  │ - Data    │ │ - Data    │ │ - Data   │     │
│  │   Access  │ │   Access  │ │   Access │     │
│  └─────┬─────┘ └─────┬─────┘ └────┬─────┘     │
│        │             │             │            │
│        └─────────────┴─────────────┘            │
│              Internal Bus / DI                  │
│                                                │
│  ┌──────────────────────────────────────────┐  │
│  │           Shared Infrastructure           │  │
│  │  (Database Connection, Message Bus, etc.) │  │
│  └──────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

**Key discipline**: Modules MUST NOT access each other's internal classes. All cross-module communication goes through public API surfaces (interfaces).

**When to use**: 2-8 developer teams building a growing application. You want clear boundaries for future microservice extraction, but don't need the operational complexity yet.

**How to enforce boundaries**:
1. Each module has a public `index.ts` (or `__init__.py`) that exports only the public API
2. Linter rules prevent importing from module internals
3. Fitness functions verify no cross-module internal access
4. Each module has its own database schema or table namespace

---

## Pattern Evolution Paths

A system rarely stays at one pattern forever. Here are common evolution paths:

```
Monolith → Modular Monolith → (if justified) → Microservices
                                      ↘ Extract high-scale services only
                                      
Monolith → Clean Architecture (refactor internally)

Modular Monolith → DDD (add bounded contexts when domain becomes complex)

Modular Monolith → Event-Driven (add events for cross-module communication)

Clean Architecture + CQRS (when read/write asymmetry becomes significant)
```

**Key insight**: You can combine patterns. Modular Monolith + Clean Architecture + DDD is a powerful combination that gives you clear boundaries, domain protection, and a single deployment unit. Only extract to microservices when a specific module has independent scaling or deployment needs.

---

## Choosing a Pattern: Decision Tree

```
How large is the team?
├── 1-2 developers
│   └── How complex is the domain?
│       ├── Simple CRUD → Monolith
│       └── Complex business rules → Monolith + Clean Architecture
├── 3-8 developers
│   └── How many distinct feature areas?
│       ├── < 5 features → Monolith + Clean Architecture
│       ├── 5-15 features → Modular Monolith
│       └── 15+ features → Modular Monolith + DDD
└── 9+ developers
    └── Do features need independent deployment?
        ├── No → Modular Monolith + DDD
        └── Yes → Microservices (start with 2-3, not 20)
```

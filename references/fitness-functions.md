# Architecture Fitness Functions — Enforcing Architectural Rules with Code

## What Are Fitness Functions?

A fitness function is an automated test or check that evaluates whether an architectural characteristic still meets its defined criteria. They turn architectural aspirations into enforceable guarantees.

**Core idea**: If an architecture rule can't be tested, it's not a rule — it's a suggestion. Fitness functions make rules testable.

---

## Categories of Fitness Functions

| Category | What It Tests | Example |
|----------|--------------|---------|
| **Structural** | Module boundaries, layer dependencies | "Domain must not import infrastructure" |
| **Behavioral** | Response time, throughput, availability | "API response time < 200ms at 95th percentile" |
| **Resilience** | Failure handling, recovery | "System recovers from DB failure within 30s" |
| **Compliance** | Security, regulatory requirements | "All PII fields must be encrypted at rest" |

---

## Fitness Function Examples

### TypeScript: Layer Dependency Rules

```typescript
// tests/architecture/layer-dependencies.spec.ts
import * as fs from 'fs';
import * as path from 'path';

const MODULE_BOUNDARIES = {
  domain: {
    path: 'src/domain',
    forbiddenPatterns: [
      /prisma/, /typeorm/, /sequelize/, /mongoose/,
      /express/, /fastify/, /@nestjs/,
      /kafkajs/, /redis/, /aws-sdk/,
      /axios/, /node-fetch/,
    ],
  },
  application: {
    path: 'src/application',
    forbiddenPatterns: [
      /prisma/, /typeorm/, /sequelize/, /mongoose/,
      /express/, /fastify/, /@nestjs/,
      /kafkajs/, /redis/,
    ],
  },
  presentation: {
    path: 'src/presentation',
    forbiddenPatterns: [
      /prisma/, /typeorm/, /sequelize/, /mongoose/,
    ],
  },
  infrastructure: {
    path: 'src/infrastructure',
    forbiddenPatterns: [], // infrastructure can import anything
  },
};

function getFilesRecursively(dir: string, ext = '.ts'): string[] {
  if (!fs.existsSync(dir)) return [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files: string[] = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
      files.push(...getFilesRecursively(fullPath, ext));
    } else if (entry.name.endsWith(ext) && !entry.name.endsWith('.d.ts')) {
      files.push(fullPath);
    }
  }
  return files;
}

function extractImports(filePath: string): string[] {
  const content = fs.readFileSync(filePath, 'utf-8');
  const importRegex = /import\s+.*?from\s+['"](.+?)['"]/g;
  const imports: string[] = [];
  let match;
  while ((match = importRegex.exec(content)) !== null) {
    imports.push(match[1]);
  }
  return imports;
}

describe('Architecture Fitness Functions', () => {
  describe('Domain layer must not import infrastructure', () => {
    const domainFiles = getFilesRecursively(MODULE_BOUNDARIES.domain.path);

    it.each(domainFiles)('Domain file %s must not import infrastructure', (file) => {
      const imports = extractImports(file);
      const violations = imports.filter((imp) =>
        MODULE_BOUNDARIES.domain.forbiddenPatterns.some((pattern) =>
          pattern.test(imp)
        )
      );
      expect(violations, `Domain file ${file} has forbidden imports: ${violations.join(', ')}`).toHaveLength(0);
    });
  });

  describe('Application layer must not import infrastructure', () => {
    const appFiles = getFilesRecursively(MODULE_BOUNDARIES.application.path);

    it.each(appFiles)('Application file %s must not import infrastructure', (file) => {
      const imports = extractImports(file);
      const violations = imports.filter((imp) =>
        MODULE_BOUNDARIES.application.forbiddenPatterns.some((pattern) =>
          pattern.test(imp)
        )
      );
      expect(violations, `Application file ${file} has forbidden imports: ${violations.join(', ')}`).toHaveLength(0);
    });
  });

  describe('No circular dependencies between modules', () => {
    it('Module dependency graph must be acyclic', () => {
      // Build adjacency list from imports
      const modules = ['domain', 'application', 'infrastructure', 'presentation'];
      const adj: Record<string, string[]> = {
        domain: [],
        application: ['domain'],
        infrastructure: ['domain', 'application'],
        presentation: ['application'],
      };

      // DFS cycle detection
      function hasCycle(node: string, visited: Set<string>, recStack: Set<string>): boolean {
        visited.add(node);
        recStack.add(node);
        for (const neighbor of adj[node] || []) {
          if (!visited.has(neighbor)) {
            if (hasCycle(neighbor, visited, recStack)) return true;
          } else if (recStack.has(neighbor)) {
            return true;
          }
        }
        recStack.delete(node);
        return false;
      }

      const visited = new Set<string>();
      for (const module of modules) {
        if (!visited.has(module)) {
          if (hasCycle(module, visited, new Set())) {
            fail('Circular dependency detected in module graph');
          }
        }
      }
    });
  });
});
```

### Python: Architecture Rule Testing with pytest

```python
# tests/test_architecture.py
"""Architecture fitness functions - tests that enforce architectural rules."""
import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
import pytest


class DependencyAnalyzer:
    """Analyzes Python module dependencies and calculates coupling metrics."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self._cache: Dict[str, List[str]] = {}

    def get_imports(self, file_path: Path) -> List[str]:
        """Extract all import statements from a Python file."""
        if str(file_path) in self._cache:
            return self._cache[str(file_path)]

        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
        except (SyntaxError, FileNotFoundError):
            return []

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        self._cache[str(file_path)] = imports
        return imports

    def build_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build a module-level dependency graph."""
        graph: Dict[str, Set[str]] = {}

        for py_file in self.root_path.rglob('*.py'):
            module = self._path_to_module(py_file)
            imports = self.get_imports(py_file)

            internal_deps = set()
            for imp in imports:
                if imp.startswith(str(self.root_path.name)) or imp.startswith('src.'):
                    internal_deps.add(imp)

            if internal_deps:
                graph[module] = internal_deps

        return graph

    def _path_to_module(self, path: Path) -> str:
        rel = path.relative_to(self.root_path.parent)
        return str(rel).replace(os.sep, '.').replace('.py', '')

    def find_circular_dependencies(self) -> List[List[str]]:
        """Find all circular dependency chains."""
        graph = self.build_dependency_graph()
        cycles = []

        def dfs(node: str, path: List[str], visited: Set[str]):
            if node in path:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            if node in visited:
                return

            visited.add(node)
            path.append(node)

            for dep in graph.get(node, set()):
                dfs(dep, path, visited)

            path.pop()

        for module in graph:
            dfs(module, [], set())

        return cycles


class TestArchitectureRules:
    """Fitness functions that enforce architectural invariants."""

    @pytest.fixture
    def analyzer(self):
        return DependencyAnalyzer('src')

    def test_domain_has_no_infrastructure_imports(self, analyzer):
        """Domain layer must not import from infrastructure layer."""
        infrastructure_patterns = [
            'infrastructure', 'adapters', 'framework',
            'sqlalchemy', 'django', 'flask', 'fastapi',
            'redis', 'celery', 'boto3',
        ]

        domain_path = analyzer.root_path / 'domain'
        if not domain_path.exists():
            pytest.skip('No domain directory found')

        violations = []
        for py_file in domain_path.rglob('*.py'):
            imports = analyzer.get_imports(py_file)
            for imp in imports:
                for pattern in infrastructure_patterns:
                    if pattern in imp.lower():
                        violations.append(f'{py_file}: imports {imp}')

        assert len(violations) == 0, (
            f'Domain layer has infrastructure imports:\n' +
            '\n'.join(violations)
        )

    def test_no_circular_dependencies(self, analyzer):
        """Modules must not have circular import dependencies."""
        cycles = analyzer.find_circular_dependencies()
        assert len(cycles) == 0, (
            f'Circular dependencies found:\n' +
            '\n'.join(' -> '.join(c) for c in cycles)
        )
```

### Python: import-linter Configuration

```ini
# .importlinter contract file

[importlinter:contract:1]
name = Domain must not import infrastructure
type = forbidden
source_modules =
    src.domain
forbidden_modules =
    src.infrastructure
    src.adapters
    src.framework

[importlinter:contract:2]
name = Application must not import infrastructure
type = forbidden
source_modules =
    src.application
forbidden_modules =
    src.infrastructure
    src.adapters

[importlinter:contract:3]
name = Modules must not have circular imports
type = layers
layers =
    domain
    application
    infrastructure
    presentation
```

---

## CI Integration

### GitHub Actions

```yaml
# .github/workflows/architecture.yml
name: Architecture Checks
on: [pull_request]

jobs:
  fitness-functions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install pytest import-linter

      - name: Run architecture fitness functions
        run: pytest tests/test_architecture.py -v

      - name: Run import linting
        run: lint-imports

      - name: Run architecture validator
        run: python scripts/architecture_validator.py .
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: architecture-check
        name: Architecture Validation
        entry: python scripts/architecture_validator.py .
        language: system
        pass_filenames: false
        stages: [pre-commit]
```

---

## Writing Effective Fitness Functions

### Principles

1. **Test what matters** — Don't test trivia. Focus on rules that, when violated, cause real pain (layer violations, circular deps, mixed data access).
2. **Fail fast** — Fitness functions should run quickly. Structural checks (import analysis) are fast; behavioral checks (load tests) are slow. Run structural checks on every PR, behavioral checks on schedule.
3. **Clear failure messages** — When a fitness function fails, the message should tell you exactly what's wrong and where. "Domain file src/domain/order.py imports prisma" is useful. "Architecture rule violated" is not.
4. **Version your rules** — As architecture evolves, fitness functions must evolve too. Track them in the same repository as the code they test.
5. **Don't over-constrain** — Too many fitness functions makes the codebase rigid. Focus on the boundaries that matter and allow flexibility within them.

### When to Add a Fitness Function

| Trigger | Fitness Function |
|---------|-----------------|
| Write an ADR about a layer boundary | Test that imports respect the boundary |
| Fix a circular dependency bug | Test that no circular dependencies exist |
| Choose an ORM/data access approach | Test that no other ORM is imported |
| Define module boundaries | Test that modules don't access each other's internals |
| Set performance targets | Test that response times stay within bounds |

### Fitness Function to ADR Mapping

Every fitness function should reference the ADR that established the rule it's testing:

```python
def test_domain_no_infrastructure_imports():
    """Enforces ADR-0005: Adopt Clean Architecture for Order Processing Module."""
    ...
```

This creates a traceable link between decisions and their enforcement.

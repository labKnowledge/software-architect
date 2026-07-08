#!/usr/bin/env python3
"""
architecture_validator.py — Validate project structure against architectural rules.

Supports both Python and TypeScript/JavaScript projects.

Usage:
    python architecture_validator.py /path/to/project
    python architecture_validator.py /path/to/project --config custom-config.json
    python architecture_validator.py /path/to/project --language typescript
"""

import ast
import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class Violation:
    rule: str
    file: str
    message: str
    severity: str  # 'error' or 'warning'


# Default architecture configuration
DEFAULT_CONFIG = {
    "moduleBoundaries": [
        {
            "name": "domain",
            "path": "src/domain",
            "allowedImports": ["src/domain"],
            "forbiddenPatterns": [
                "prisma", "typeorm", "sequelize", "mongoose",
                "express", "fastify", "@nestjs",
                "kafkajs", "redis", "aws-sdk",
                "axios", "node-fetch", "fetch",
                "sqlalchemy", "django", "flask", "fastapi",
                "psycopg2", "pymongo", "redis",
                "boto3", "requests", "httpx",
            ],
        },
        {
            "name": "application",
            "path": "src/application",
            "allowedImports": ["src/domain", "src/application"],
            "forbiddenPatterns": [
                "prisma", "typeorm", "sequelize", "mongoose",
                "express", "fastify", "@nestjs",
                "kafkajs", "redis",
                "sqlalchemy", "django", "flask", "fastapi",
                "psycopg2", "pymongo", "redis",
            ],
        },
        {
            "name": "infrastructure",
            "path": "src/infrastructure",
            "allowedImports": ["src/domain", "src/application", "src/infrastructure"],
            "forbiddenPatterns": [],
        },
        {
            "name": "presentation",
            "path": "src/presentation",
            "allowedImports": ["src/domain", "src/application", "src/presentation"],
            "forbiddenPatterns": [
                "prisma", "typeorm", "sequelize", "mongoose",
                "sqlalchemy", "psycopg2", "pymongo",
            ],
        },
    ],
    "maxMetrics": {
        "circularDependencies": 0,
        "maxEfferentCoupling": 10,
        "maxFileLength": 300,
        "maxFunctionLength": 50,
    },
    "dataAccessConsistency": {
        "ormPatterns": [
            "prisma", "typeorm", "sequelize", "mongoose", "@prisma/client",
            "sqlalchemy", "django.db", "flask_sqlalchemy", "tortoise",
        ],
        "rawPatterns": [
            "pg", "mysql2", "mongodb", "oracledb", "better-sqlite3",
            "psycopg2", "pymongo", "aiomysql", "asyncpg",
        ],
    },
    "frameworkCouplingPatterns": [
        "@Injectable", "@Controller", "@Module", "@Component",
        "@Entity", "@Column", "@Table", "@Schema",
        "@Inject", "@Autowired",
    ],
}


class ArchitectureValidator:
    """Validates project structure against architectural rules."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or DEFAULT_CONFIG
        self.violations: List[Violation] = []
        self.language: str = "python"  # detected or specified

    def validate(self, project_root: str, language: Optional[str] = None) -> List[Violation]:
        """Run all validation checks."""
        self.violations = []

        root = Path(project_root).resolve()

        # Detect language if not specified
        if language:
            self.language = language
        else:
            self.language = self._detect_language(root)

        # Determine file extension and import extraction method
        if self.language == "typescript":
            ext = ".ts"
            import_extractor = self._extract_ts_imports
        elif self.language == "javascript":
            ext = ".js"
            import_extractor = self._extract_ts_imports
        else:
            ext = ".py"
            import_extractor = self._extract_py_imports

        # 1. Check module boundaries (forbidden imports)
        self._check_module_boundaries(root, ext, import_extractor)

        # 2. Check dependency direction
        self._check_dependency_direction(root, ext, import_extractor)

        # 3. Check file length limits
        self._check_file_length(root, ext)

        # 4. Check for mixed data access patterns
        self._check_data_access_consistency(root, ext, import_extractor)

        # 5. Check for framework coupling in domain
        self._check_framework_coupling(root, ext)

        # 6. Check for circular dependencies (simplified)
        self._check_circular_dependencies(root, ext, import_extractor)

        return self.violations

    def _detect_language(self, root: Path) -> str:
        """Detect the primary language of the project."""
        if (root / "package.json").exists():
            tsconfig = root / "tsconfig.json"
            if tsconfig.exists():
                return "typescript"
            # Check if .ts files exist
            for f in root.rglob("*.ts"):
                if not f.name.endswith(".d.ts"):
                    return "typescript"
            return "javascript"
        elif (root / "pyproject.toml").exists() or (root / "setup.py").exists():
            return "python"
        elif (root / "go.mod").exists():
            return "go"
        else:
            # Count file types
            py_count = sum(1 for _ in root.rglob("*.py"))
            ts_count = sum(1 for _ in root.rglob("*.ts"))
            if ts_count > py_count:
                return "typescript"
            return "python"

    def _get_source_files(self, root: Path, ext: str) -> List[Path]:
        """Get all source files in the project."""
        files = []
        src_path = root / "src"
        base = src_path if src_path.exists() else root

        for f in base.rglob(f"*{ext}"):
            # Skip common non-source directories
            parts = f.relative_to(base).parts
            if any(p in ('node_modules', '__pycache__', '.git', 'venv', '.venv', 'dist', 'build')
                   for p in parts):
                continue
            if self.language == "typescript" and f.name.endswith(".d.ts"):
                continue
            if f.name.startswith("."):
                continue
            files.append(f)

        return files

    def _extract_py_imports(self, content: str) -> List[str]:
        """Extract import statements from Python code."""
        imports = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except SyntaxError:
            # Fallback to regex
            for match in re.finditer(r'^(?:from\s+(\S+)\s+)?import\s+(.+)$', content, re.MULTILINE):
                if match.group(1):
                    imports.append(match.group(1))
                else:
                    imports.append(match.group(2).split(',')[0].strip())
        return imports

    def _extract_ts_imports(self, content: str) -> List[str]:
        """Extract import statements from TypeScript/JavaScript code."""
        imports = []
        # ES6 imports
        for match in re.finditer(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content):
            imports.append(match.group(1))
        # CommonJS require
        for match in re.finditer(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content):
            imports.append(match.group(1))
        return imports

    def _check_module_boundaries(self, root: Path, ext: str, import_extractor) -> None:
        """Check that modules don't import forbidden packages."""
        boundaries = self.config.get("moduleBoundaries", [])

        for boundary in boundaries:
            module_path = root / boundary["path"]
            if not module_path.exists():
                continue

            forbidden = boundary.get("forbiddenPatterns", [])
            if not forbidden:
                continue

            for f in module_path.rglob(f"*{ext}"):
                if f.name.startswith(".") or (self.language == "typescript" and f.name.endswith(".d.ts")):
                    continue

                try:
                    content = f.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    continue

                file_imports = import_extractor(content)
                for imp in file_imports:
                    imp_lower = imp.lower()
                    for pattern in forbidden:
                        if pattern.lower() in imp_lower:
                            self.violations.append(Violation(
                                rule='module-boundary',
                                file=str(f.relative_to(root)),
                                message=f'{boundary["name"]} module imports forbidden dependency: {pattern} (from {imp})',
                                severity='error',
                            ))

    def _check_dependency_direction(self, root: Path, ext: str, import_extractor) -> None:
        """Check that dependencies flow in the correct direction."""
        boundaries = self.config.get("moduleBoundaries", [])

        for boundary in boundaries:
            module_path = root / boundary["path"]
            if not module_path.exists():
                continue

            allowed = boundary.get("allowedImports", [])

            for f in module_path.rglob(f"*{ext}"):
                if f.name.startswith(".") or (self.language == "typescript" and f.name.endswith(".d.ts")):
                    continue

                try:
                    content = f.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    continue

                file_imports = import_extractor(content)
                for imp in file_imports:
                    # Check if this import goes to a disallowed module
                    for other_boundary in boundaries:
                        if other_boundary["name"] == boundary["name"]:
                            continue
                        other_path = other_boundary["path"]
                        if other_path in imp or imp.startswith(other_path.replace('/', '.')):
                            if other_path not in allowed and other_boundary["path"] not in allowed:
                                self.violations.append(Violation(
                                    rule='dependency-direction',
                                    file=str(f.relative_to(root)),
                                    message=f'{boundary["name"]} imports from {other_boundary["name"]}, violating dependency direction',
                                    severity='error',
                                ))

    def _check_file_length(self, root: Path, ext: str) -> None:
        """Check that files don't exceed maximum length."""
        max_length = self.config.get("maxMetrics", {}).get("maxFileLength", 300)

        files = self._get_source_files(root, ext)
        for f in files:
            try:
                line_count = sum(1 for _ in f.open(encoding='utf-8'))
            except UnicodeDecodeError:
                continue

            if line_count > max_length:
                self.violations.append(Violation(
                    rule='file-length',
                    file=str(f.relative_to(root)),
                    message=f'File has {line_count} lines (max: {max_length})',
                    severity='warning',
                ))

    def _check_data_access_consistency(self, root: Path, ext: str, import_extractor) -> None:
        """Check that modules don't mix ORM and raw database driver imports."""
        da_config = self.config.get("dataAccessConsistency", DEFAULT_CONFIG["dataAccessConsistency"])
        orm_patterns = da_config.get("ormPatterns", [])
        raw_patterns = da_config.get("rawPatterns", [])

        files = self._get_source_files(root, ext)
        for f in files:
            try:
                content = f.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                continue

            imports = import_extractor(content)
            import_str = ' '.join(imports).lower()

            has_orm = any(p.lower() in import_str for p in orm_patterns)
            has_raw = any(p.lower() in import_str for p in raw_patterns)

            if has_orm and has_raw:
                self.violations.append(Violation(
                    rule='data-access-consistency',
                    file=str(f.relative_to(root)),
                    message='File mixes ORM and raw database driver imports. Use repository pattern to separate concerns.',
                    severity='warning',
                ))

    def _check_framework_coupling(self, root: Path, ext: str) -> None:
        """Check that domain files don't use framework-specific decorators."""
        framework_patterns = self.config.get("frameworkCouplingPatterns", [])
        if not framework_patterns:
            return

        # Look for domain directory
        domain_path = root / "src" / "domain"
        if not domain_path.exists():
            domain_path = root / "domain"
        if not domain_path.exists():
            return

        for f in domain_path.rglob(f"*{ext}"):
            if f.name.startswith("."):
                continue

            try:
                content = f.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                continue

            for pattern in framework_patterns:
                if pattern in content:
                    self.violations.append(Violation(
                        rule='framework-coupling',
                        file=str(f.relative_to(root)),
                        message=f'Domain file uses framework decorator/pattern: {pattern}. Domain should be framework-agnostic.',
                        severity='error',
                    ))

    def _check_circular_dependencies(self, root: Path, ext: str, import_extractor) -> None:
        """Simplified circular dependency check at module level."""
        # Build module-level dependency graph
        boundaries = self.config.get("moduleBoundaries", [])
        if not boundaries:
            return

        # Check for circular deps between boundary modules
        dep_graph: Dict[str, Set[str]] = {}
        for boundary in boundaries:
            deps = set()
            for allowed in boundary.get("allowedImports", []):
                for other in boundaries:
                    # Skip self-references (a module importing from itself is not a cycle)
                    if other["name"] == boundary["name"]:
                        continue
                    if other["path"] == allowed or other["path"] in allowed:
                        deps.add(other["name"])
            dep_graph[boundary["name"]] = deps

        # DFS cycle detection
        cycles = []
        visited = set()

        def dfs(node: str, path: List[str], path_set: Set[str]):
            if node in path_set:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            if node in visited:
                return

            path.append(node)
            path_set.add(node)

            for dep in dep_graph.get(node, set()):
                dfs(dep, path, path_set)

            path.pop()
            path_set.discard(node)
            visited.add(node)

        for module in dep_graph:
            visited.discard(module)
            dfs(module, [], set())

        if cycles:
            for cycle in cycles:
                self.violations.append(Violation(
                    rule='circular-dependency',
                    file='',
                    message=f'Circular dependency detected: {" -> ".join(cycle)}',
                    severity='error',
                ))

    def generate_report(self, project_root: str) -> str:
        """Generate a formatted validation report."""
        lines = ['=' * 70, 'ARCHITECTURE VALIDATION REPORT', '=' * 70, '']
        lines.append(f'Project: {project_root}')
        lines.append(f'Language: {self.language}')
        lines.append('')

        errors = [v for v in self.violations if v.severity == 'error']
        warnings = [v for v in self.violations if v.severity == 'warning']

        if not self.violations:
            lines.append('No architecture violations found!')
            return '\n'.join(lines)

        # Group by rule
        by_rule: Dict[str, List[Violation]] = {}
        for v in self.violations:
            by_rule.setdefault(v.rule, []).append(v)

        for rule, violations in by_rule.items():
            icon = 'ERROR' if violations[0].severity == 'error' else 'WARNING'
            lines.append(f'[{icon}] {rule.upper()} ({len(violations)} issues)')
            lines.append('-' * 70)
            for v in violations:
                file_info = f'{v.file}: ' if v.file else ''
                lines.append(f'  {file_info}{v.message}')
            lines.append('')

        lines.append('=' * 70)
        lines.append(f'Total: {len(errors)} errors, {len(warnings)} warnings')

        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Validate project structure against architectural rules'
    )
    parser.add_argument('path', help='Root path of the project')
    parser.add_argument('--config', type=str, help='Path to architecture config JSON file')
    parser.add_argument('--language', choices=['python', 'typescript', 'javascript'],
                        help='Force language detection')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()

    if not Path(args.path).exists():
        print(f'Error: Path {args.path} does not exist')
        sys.exit(1)

    # Load config
    config = DEFAULT_CONFIG
    config_file = args.config
    if not config_file:
        # Try to find architecture.config.json in project root
        project_config = Path(args.path) / 'architecture.config.json'
        if project_config.exists():
            config_file = str(project_config)

    if config_file:
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f'Loaded architecture config from {config_file}')
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f'Warning: Could not load config file: {e}')
            print('Using default architecture configuration')

    validator = ArchitectureValidator(config)
    violations = validator.validate(args.path, args.language)

    if args.json:
        result = {
            'project': str(Path(args.path).resolve()),
            'language': validator.language,
            'total_violations': len(violations),
            'errors': [
                {'rule': v.rule, 'file': v.file, 'message': v.message}
                for v in violations if v.severity == 'error'
            ],
            'warnings': [
                {'rule': v.rule, 'file': v.file, 'message': v.message}
                for v in violations if v.severity == 'warning'
            ],
        }
        print(json.dumps(result, indent=2))
    else:
        print(validator.generate_report(args.path))

    # Exit with error code if there are errors
    errors = [v for v in violations if v.severity == 'error']
    if errors:
        sys.exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
dependency_analyzer.py — Analyze module dependencies, detect violations,
and calculate coupling/cohesion metrics for Python projects.

Usage:
    python dependency_analyzer.py /path/to/project
    python dependency_analyzer.py /path/to/project --format json
    python dependency_analyzer.py /path/to/project --check-layers --layers '{"domain":[],"application":["domain"],"infrastructure":["domain","application"]}'
"""

import ast
import argparse
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


@dataclass
class ModuleInfo:
    name: str
    path: str
    imports: List[str] = field(default_factory=list)
    imported_by: List[str] = field(default_factory=list)
    efferent_coupling: int = 0  # outgoing dependencies
    afferent_coupling: int = 0  # incoming dependencies
    instability: float = 0.0
    abstract_types: int = 0
    concrete_types: int = 0
    abstractness: float = 0.0
    distance_from_main: float = 0.0


class DependencyAnalyzer:
    """Comprehensive dependency analysis for Python projects."""

    # Common infrastructure patterns that domain should not import
    INFRA_PATTERNS = [
        'sqlalchemy', 'django', 'flask', 'fastapi', 'celery',
        'redis', 'boto3', 'psycopg2', 'pymongo', 'motor',
        'aiomysql', 'asyncpg', 'databases', 'tortoise',
        'requests', 'httpx', 'aiohttp',
    ]

    def __init__(self, root_path: str, source_root: str = 'src'):
        self.root_path = Path(root_path).resolve()
        self.source_root = source_root
        self.modules: Dict[str, ModuleInfo] = {}
        self._import_cache: Dict[str, List[str]] = {}

    def analyze(self) -> Dict[str, ModuleInfo]:
        """Run full analysis and return module information."""
        self._discover_modules()
        self._extract_all_imports()
        self._build_dependency_graph()
        self._calculate_metrics()
        return self.modules

    def _discover_modules(self):
        """Find all Python modules in the project."""
        src_path = self.root_path / self.source_root
        if not src_path.exists():
            src_path = self.root_path

        for py_file in src_path.rglob('*.py'):
            if py_file.name.startswith('__'):
                continue
            module_name = self._path_to_module(py_file, src_path)
            self.modules[module_name] = ModuleInfo(
                name=module_name,
                path=str(py_file)
            )

    def _path_to_module(self, path: Path, base: Path) -> str:
        """Convert file path to dotted module name."""
        rel = path.relative_to(base)
        parts = list(rel.parts)
        parts[-1] = parts[-1].replace('.py', '')
        return '.'.join(parts)

    def _extract_imports_from_file(self, file_path: str) -> List[str]:
        """Parse a Python file and extract all import statements."""
        if file_path in self._import_cache:
            return self._import_cache[file_path]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
        except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
            return []

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        self._import_cache[file_path] = imports
        return imports

    def _extract_all_imports(self):
        """Extract imports for all discovered modules."""
        for name, info in self.modules.items():
            raw_imports = self._extract_imports_from_file(info.path)

            # Filter to only internal imports (belonging to our project)
            internal_imports = [
                imp for imp in raw_imports
                if any(mod.startswith(imp.split('.')[0]) for mod in self.modules)
            ]
            info.imports = internal_imports

    def _build_dependency_graph(self):
        """Build the reverse dependency map (imported_by)."""
        for name, info in self.modules.items():
            for imp in info.imports:
                for other_name, other_info in self.modules.items():
                    if other_name.startswith(imp) or imp.startswith(other_name):
                        other_info.imported_by.append(name)

    def _calculate_metrics(self):
        """Calculate coupling and cohesion metrics for each module."""
        for name, info in self.modules.items():
            # Efferent coupling (outgoing)
            info.efferent_coupling = len(set(info.imports))

            # Afferent coupling (incoming)
            info.afferent_coupling = len(set(info.imported_by))

            # Instability = Ce / (Ca + Ce)
            total = info.efferent_coupling + info.afferent_coupling
            if total > 0:
                info.instability = info.efferent_coupling / total

            # Count abstract vs concrete types
            info.abstract_types, info.concrete_types = self._count_types(info.path)

            # Abstractness = Na / Nt
            total_types = info.abstract_types + info.concrete_types
            if total_types > 0:
                info.abstractness = info.abstract_types / total_types

            # Distance from main sequence = |A + I - 1|
            info.distance_from_main = abs(info.abstractness + info.instability - 1)

    def _count_types(self, file_path: str) -> Tuple[int, int]:
        """Count abstract (ABC, Protocol) and concrete types in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
        except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
            return 0, 0

        abstract = 0
        concrete = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                is_abstract = False
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id in ('ABC', 'Protocol', 'Interface'):
                        is_abstract = True
                    elif isinstance(base, ast.Attribute) and base.attr in ('ABC', 'Protocol'):
                        is_abstract = True

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        for decorator in item.decorator_list:
                            if isinstance(decorator, ast.Name) and decorator.id == 'abstractmethod':
                                is_abstract = True

                if is_abstract:
                    abstract += 1
                else:
                    concrete += 1

        return abstract, concrete

    def find_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependency chains."""
        cycles = []
        visited_global = set()

        def dfs(node: str, path: List[str], path_set: Set[str]):
            if node in path_set:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            if node in visited_global:
                return

            path.append(node)
            path_set.add(node)

            info = self.modules.get(node)
            if info:
                for dep in info.imports:
                    resolved = self._resolve_module(dep)
                    if resolved:
                        dfs(resolved, path, path_set)

            path.pop()
            path_set.discard(node)
            visited_global.add(node)

        for name in self.modules:
            visited_global.discard(name)
            dfs(name, [], set())

        return cycles

    def _resolve_module(self, import_name: str) -> Optional[str]:
        """Resolve an import name to an actual module in our project."""
        for name in self.modules:
            if name == import_name or name.startswith(import_name + '.'):
                return name
        # Partial match
        for name in self.modules:
            if import_name.startswith(name.split('.')[0]):
                return name
        return None

    def find_layer_violations(
        self,
        layers: Dict[str, List[str]]
    ) -> List[Tuple[str, str, str]]:
        """
        Find violations of layer dependency rules.

        Args:
            layers: Dict mapping layer name to list of allowed dependency layers.
                    e.g., {'domain': [], 'application': ['domain'],
                           'infrastructure': ['domain', 'application']}

        Returns:
            List of (source_module, target_module, violation_description)
        """
        violations = []

        for name, info in self.modules.items():
            source_layer = self._get_layer(name)
            if not source_layer:
                continue

            allowed_layers = layers.get(source_layer, [])
            if not allowed_layers and source_layer not in layers:
                continue

            for imp in info.imports:
                target_layer = self._get_layer(imp)
                if not target_layer or target_layer == source_layer:
                    continue

                if target_layer not in allowed_layers:
                    violations.append((
                        name, imp,
                        f'{source_layer} layer cannot import from {target_layer} layer'
                    ))

        return violations

    def find_infra_in_domain(self) -> List[Tuple[str, str]]:
        """Find domain files that import infrastructure packages."""
        violations = []

        for name, info in self.modules.items():
            if 'domain' not in name.split('.'):
                continue

            raw_imports = self._extract_imports_from_file(info.path)
            for imp in raw_imports:
                imp_lower = imp.lower()
                for pattern in self.INFRA_PATTERNS:
                    if pattern in imp_lower:
                        violations.append((name, imp))

        return violations

    def _get_layer(self, module_name: str) -> Optional[str]:
        """Determine which architectural layer a module belongs to."""
        layer_names = ['domain', 'application', 'infrastructure', 'presentation', 'api']
        for layer in layer_names:
            if f'.{layer}.' in module_name or module_name.endswith(f'.{layer}'):
                return layer
        return None

    def generate_report(self, format: str = 'text') -> str:
        """Generate an analysis report."""
        if format == 'json':
            return self._json_report()
        return self._text_report()

    def _text_report(self) -> str:
        lines = ['=' * 70, 'DEPENDENCY ANALYSIS REPORT', '=' * 70, '']

        # Module metrics
        lines.append('MODULE METRICS')
        lines.append('-' * 70)
        lines.append(f'{"Module":<40} {"Ce":>4} {"Ca":>4} {"I":>6} {"A":>6} {"D":>6}')
        lines.append('-' * 70)

        for name, info in sorted(self.modules.items()):
            display_name = name[:38] if len(name) > 38 else name
            lines.append(
                f'{display_name:<40} {info.efferent_coupling:>4} {info.afferent_coupling:>4} '
                f'{info.instability:>6.2f} {info.abstractness:>6.2f} '
                f'{info.distance_from_main:>6.2f}'
            )

        # Circular dependencies
        cycles = self.find_circular_dependencies()
        if cycles:
            lines.append('')
            lines.append('CIRCULAR DEPENDENCIES')
            lines.append('-' * 70)
            for cycle in cycles:
                lines.append('  ' + ' -> '.join(cycle))

        # Infrastructure in domain
        infra_violations = self.find_infra_in_domain()
        if infra_violations:
            lines.append('')
            lines.append('INFRASTRUCTURE IN DOMAIN')
            lines.append('-' * 70)
            for module, imp in infra_violations:
                lines.append(f'  {module}: imports {imp}')

        # Summary
        lines.append('')
        lines.append('SUMMARY')
        lines.append('-' * 70)
        lines.append(f'Total modules: {len(self.modules)}')
        lines.append(f'Circular dependencies: {len(cycles)}')
        lines.append(f'Infra in domain violations: {len(infra_violations)}')

        # Warnings
        high_coupling = [
            (name, info) for name, info in self.modules.items()
            if info.efferent_coupling > 10
        ]
        if high_coupling:
            lines.append(f'Modules with high efferent coupling (>10): {len(high_coupling)}')
            for name, info in high_coupling:
                lines.append(f'  {name}: Ce={info.efferent_coupling}')

        pain_zone = [
            (name, info) for name, info in self.modules.items()
            if info.distance_from_main > 0.5 and info.instability < 0.3
        ]
        if pain_zone:
            lines.append(f'Modules in "Zone of Pain": {len(pain_zone)}')
            for name, info in pain_zone:
                lines.append(f'  {name}: D={info.distance_from_main:.2f}, I={info.instability:.2f}')

        return '\n'.join(lines)

    def _json_report(self) -> str:
        data = {
            'modules': {
                name: {
                    'path': info.path,
                    'efferent_coupling': info.efferent_coupling,
                    'afferent_coupling': info.afferent_coupling,
                    'instability': round(info.instability, 3),
                    'abstractness': round(info.abstractness, 3),
                    'distance_from_main': round(info.distance_from_main, 3),
                    'imports': info.imports,
                    'imported_by': info.imported_by,
                }
                for name, info in self.modules.items()
            },
            'circular_dependencies': self.find_circular_dependencies(),
            'infrastructure_in_domain': [
                {'module': mod, 'import': imp}
                for mod, imp in self.find_infra_in_domain()
            ],
        }
        return json.dumps(data, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze Python project dependencies and calculate architecture metrics'
    )
    parser.add_argument('path', help='Root path of the project')
    parser.add_argument('--source-root', default='src', help='Source root directory (default: src)')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    parser.add_argument('--check-layers', action='store_true',
                        help='Check for layer violations')
    parser.add_argument('--layers', type=str,
                        help='Layer config as JSON, e.g. \'{"domain":[],"application":["domain"]}\'')
    args = parser.parse_args()

    if not Path(args.path).exists():
        print(f'Error: Path {args.path} does not exist')
        sys.exit(1)

    analyzer = DependencyAnalyzer(args.path, args.source_root)
    analyzer.analyze()

    if args.check_layers and args.layers:
        layers = json.loads(args.layers)
        violations = analyzer.find_layer_violations(layers)
        if violations:
            print('LAYER VIOLATIONS FOUND:')
            for source, target, desc in violations:
                print(f'  {source} -> {target}: {desc}')
            sys.exit(1)
        else:
            print('No layer violations found.')
        print()

    print(analyzer.generate_report(args.format))


if __name__ == '__main__':
    main()

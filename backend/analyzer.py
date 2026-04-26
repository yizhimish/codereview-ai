"""
CodeReview AI - Code Analysis Engine

Uses Python ast module for deep Python analysis and regex patterns
for JavaScript/TypeScript, Java, Go, Rust, and C++.

All checks return findings with:
  type, severity, category, message, line, suggestion
"""

import ast
import re
import time
from typing import List, Dict, Any, Optional, Set, Tuple

Finding = Dict[str, Any]


def _make_finding(
    ftype: str,
    severity: str,
    category: str,
    message: str,
    line: int,
    suggestion: str = "",
) -> Finding:
    return {
        "type": ftype,
        "severity": severity,
        "category": category,
        "message": message,
        "line": line,
        "suggestion": suggestion,
    }


SEVERITY_DEDUCTIONS = {
    "critical": 15,
    "high": 8,
    "medium": 4,
    "low": 2,
}


def calculate_score(results: List[Finding]) -> int:
    score = 100
    for r in results:
        score -= SEVERITY_DEDUCTIONS.get(r.get("severity", "low"), 2)
    return max(0, score)


def build_summary(results: List[Finding], elapsed_ms: float) -> Dict[str, Any]:
    by_severity: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    by_category: Dict[str, int] = {}
    for r in results:
        s = r.get("severity", "low")
        c = r.get("category", "bug")
        by_severity[s] = by_severity.get(s, 0) + 1
        by_category[c] = by_category.get(c, 0) + 1
    return {
        "total_issues": len(results),
        "by_severity": by_severity,
        "by_category": by_category,
        "score": calculate_score(results),
        "analysis_time_ms": round(elapsed_ms, 1),
    }


_SENSITIVE_REGEX = re.compile(
    r"(?i)(password|passwd|pwd|secret|token|api[_-]?key|apikey|"
    r"private[_-]?key|access[_-]?key)"
    r"\s*[:=]\s*['\"]([^'\"]+)['\"]",
)


def _get_call_name(node: ast.Call) -> Optional[str]:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _count_lines(node: ast.AST) -> int:
    try:
        start = node.lineno
        end = node.end_lineno or start
        return end - start + 1
    except AttributeError:
        return 1


def _camel_to_snake(name: str) -> str:
    s1 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    s2 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s1)
    return s2.lower()

# ════════════════════════════════════════════════════════════════
#  BUG DETECTION
# ════════════════════════════════════════════════════════════════

def check_undefined_variables(tree: ast.AST) -> List[Finding]:
    defined: set = set()
    findings: list = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined.add(node.name)
            # Add function parameters
            for arg in node.args.args:
                defined.add(arg.arg)
            if node.args.vararg:
                defined.add(node.args.vararg.arg)
            if node.args.kwarg:
                defined.add(node.args.kwarg.arg)
            for arg in node.args.kwonlyargs:
                defined.add(arg.arg)
            for arg in node.args.posonlyargs:
                defined.add(arg.arg)
        elif isinstance(node, ast.ClassDef):
            defined.add(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                defined.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                defined.add(alias.asname or alias.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    defined.add(t.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                defined.add(node.target.id)
        elif isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Name):
                defined.add(node.target.id)
        elif isinstance(node, ast.For):
            if isinstance(node.target, ast.Name):
                defined.add(node.target.id)
            elif isinstance(node.target, ast.Tuple):
                for el in node.target.elts:
                    if isinstance(el, ast.Name):
                        defined.add(el.id)
        elif isinstance(node, ast.comprehension):
            if isinstance(node.target, ast.Name):
                defined.add(node.target.id)
            elif isinstance(node.target, ast.Tuple):
                for el in node.target.elts:
                    if isinstance(el, ast.Name):
                        defined.add(el.id)
        elif isinstance(node, ast.ListComp) or isinstance(node, ast.SetComp) or isinstance(node, ast.DictComp) or isinstance(node, ast.GeneratorExp):
            for gen in node.generators:
                if isinstance(gen.target, ast.Name):
                    defined.add(gen.target.id)
                elif isinstance(gen.target, ast.Tuple):
                    for el in gen.target.elts:
                        if isinstance(el, ast.Name):
                            defined.add(el.id)
            for if_clause in gen.ifs:
                if isinstance(if_clause, ast.Name):
                    pass

    builtins = {
        "print", "len", "range", "int", "str", "float", "bool", "list", "dict",
        "set", "tuple", "type", "open", "input", "isinstance", "hasattr",
        "getattr", "setattr", "enumerate", "zip", "map", "filter", "sorted",
        "reversed", "min", "max", "sum", "abs", "all", "any", "chr", "ord",
        "hex", "oct", "bin", "round", "pow", "divmod", "repr", "ascii",
        "staticmethod", "classmethod", "property", "super", "__import__",
        "ValueError", "TypeError", "KeyError", "IndexError", "RuntimeError",
        "AttributeError", "NameError", "ZeroDivisionError", "FileNotFoundError",
        "IOError", "OSError", "object", "NotImplemented", "memoryview",
        "bytearray", "bytes", "callable", "compile", "dir", "eval", "exec", "format",
        "frozenset", "globals", "hash", "help", "id", "issubclass",
        "iter", "locals", "next", "vars", "delattr", "Exception", "StopIteration",
        "True", "False", "None",
    }

    seen: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            var = node.id
            if var not in defined and var not in builtins and (var, node.lineno) not in seen:
                seen.add((var, node.lineno))
                findings.append(
                    _make_finding(
                        "error", "high", "bug",
                        f"Undefined variable: '{var}' is used before being defined",
                        node.lineno,
                        f"Define the variable '{var}' or check the spelling",
                    )
                )
    return findings


def _is_inside_try(tree: ast.AST, target: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Try, ast.TryStar)):
            for child in ast.walk(node):
                if child is target:
                    return True
    return False


def check_bugs(tree: ast.AST, source: str) -> List[Finding]:
    findings: list = []

    # 1. Undefined variables
    findings.extend(check_undefined_variables(tree))

    # 2. None comparison (== None vs is None)
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for c, comp in zip(node.ops, node.comparators):
                if isinstance(c, ast.Eq) and isinstance(comp, ast.Constant) and comp.value is None:
                    findings.append(
                        _make_finding(
                            "warning", "low", "bug",
                            "Using == to compare with None, use 'is None' instead",
                            node.lineno,
                            "Replace '== None' with 'is None'",
                        )
                    )

    # 3. Bare except clause
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            findings.append(
                _make_finding(
                    "warning", "medium", "bug",
                    "Bare except clause: no exception type specified",
                    node.lineno,
                    "Specify the exception type to catch, e.g.: except ValueError:",
                )
            )

    # 4. while True without break
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
                if not has_break:
                    findings.append(
                        _make_finding(
                            "warning", "medium", "bug",
                            "Potential infinite loop: while True without a break statement",
                            node.lineno,
                            "Add a break condition or loop counter to avoid infinite loop",
                        )
                    )

    # 5. Dangerous calls without try-except
    dangerous = {"int", "float", "open", "eval", "exec", "compile"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in dangerous and not _is_inside_try(tree, node):
                findings.append(
                    _make_finding(
                        "warning", "high", "bug",
                        f"Potential exception: {node.func.id}() call is not wrapped in try-except",
                        node.lineno,
                        f"Wrap {node.func.id}() in a try-except block",
                    )
                )

    # 6. Attribute access on None constant
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Constant) and node.value.value is None:
            findings.append(
                _make_finding(
                    "error", "critical", "bug",
                    "Accessing attribute on None: attempting to access an attribute of a None object",
                    node.lineno,
                    "Ensure the object is not None before accessing its attributes: if obj is not None",
                )
            )

    return findings


# ════════════════════════════════════════════════════════════════
#  SECURITY SCANNER
# ════════════════════════════════════════════════════════════════

_SQL_QUERY_PATTERN = re.compile(
    r"(?i)(execute|executemany|query|raw_query)\s*\(\s*[f'\"]"
    r".*?(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE)"
)
_SHELL_PATTERN = re.compile(r"(?i)shell\s*=\s*True")
_EVAL_PATTERN = re.compile(r"(?<![.\w])eval\(|(?<![.\w])exec\(")


def check_security(source: str) -> List[Finding]:
    findings: list = []

    # 1. Hardcoded secrets
    for match in _SENSITIVE_REGEX.finditer(source):
        line_num = source[:match.start()].count("\n") + 1
        findings.append(
            _make_finding(
                "error", "critical", "security",
                "Suspected hardcoded secret/password/Token detected",
                line_num,
                "Use environment variables or a secret management service",
            )
        )

    # 2. eval/exec usage
    for match in _EVAL_PATTERN.finditer(source):
        line_num = source[:match.start()].count("\n") + 1
        findings.append(
            _make_finding(
                "error", "critical", "security",
                "Use of unsafe eval()/exec() function",
                line_num,
                "Avoid eval()/exec(), use ast.literal_eval() or other safe alternatives",
            )
        )

    # 3. shell=True
    for match in _SHELL_PATTERN.finditer(source):
        line_num = source[:match.start()].count("\n") + 1
        findings.append(
            _make_finding(
                "error", "critical", "security",
                "Unsafe subprocess call: shell=True",
                line_num,
                "Avoid shell=True, use explicit argument lists: subprocess.run(['ls', '-l'])",
            )
        )

    # 4. SQL injection risk
    seen_sql: set = set()
    for match in _SQL_QUERY_PATTERN.finditer(source):
        line_num = source[:match.start()].count("\n") + 1
        if line_num not in seen_sql:
            seen_sql.add(line_num)
            findings.append(
                _make_finding(
                    "error", "critical", "security",
                    "Possible SQL injection risk: raw SQL string concatenation detected",
                    line_num,
                    "Use parameterized queries or an ORM framework",
                )
            )

    # 5. Pickle usage
    for match in re.finditer(r"import pickle", source):
        line_num = source[:match.start()].count("\n") + 1
        findings.append(
            _make_finding(
                "warning", "high", "security",
                "Deserialization risk: pickle can lead to remote code execution",
                line_num,
                "Use JSON or MessagePack instead of pickle",
            )
        )

    # 6. requests without timeout
    for match in re.finditer(r"requests\.(get|post|put|delete|patch)\([^)]*\)", source):
        line_num = source[:match.start()].count("\n") + 1
        if "timeout" not in match.group():
            findings.append(
                _make_finding(
                    "warning", "medium", "security",
                    "HTTP request without timeout",
                    line_num,
                    "Add timeout parameter: requests.get(url, timeout=10)",
                )
            )

    # 7. Path traversal
    for match in re.finditer(r'open\(\s*[\'"][^\'"]*\.\.[/\\\\]', source):
        line_num = source[:match.start()].count("\n") + 1
        findings.append(
            _make_finding(
                "warning", "high", "security",
                "Path traversal risk detected",
                line_num,
                "Use os.path.abspath() or pathlib to ensure path safety, filter out '..'",
            )
        )

    return findings

# ════════════════════════════════════════════════════════════════
#  PERFORMANCE ANALYSIS
# ════════════════════════════════════════════════════════════════

def check_performance(tree: ast.AST) -> List[Finding]:
    findings: list = []

    for node in ast.walk(tree):
        # 1. for loop with .append -> list comprehension
        if isinstance(node, ast.For):
            body = node.body
            if len(body) == 1 and isinstance(body[0], ast.Expr):
                inner = body[0].value
                if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute):
                    if inner.func.attr == "append":
                        findings.append(
                            _make_finding(
                                "info", "low", "performance",
                                "Can use a list comprehension instead of an explicit for loop + append",
                                node.lineno,
                                "Use [x for x in items if condition] instead of for x in items: list.append(x)",
                            )
                        )

        # 2. Multiple len() inside loop
        if isinstance(node, ast.For):
            count = 0
            for n in ast.walk(node):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "len":
                    count += 1
            if count > 2:
                findings.append(
                    _make_finding(
                        "warning", "medium", "performance",
                        "Multiple len() calls inside loop, hoist to outside the loop",
                        node.lineno,
                        "Save len() result to a variable outside the loop: n = len(items)",
                    )
                )

        # 3. copy() call
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "copy":
            findings.append(
                _make_finding(
                    "info", "low", "performance",
                    "copy() call detected, large object copies may impact performance",
                    node.lineno,
                    "If a fully independent copy is not necessary, consider shallow copy or reference",
                )
            )

        # 4. sum([list comprehension]) -> sum(genexpr)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "sum":
            if node.args and isinstance(node.args[0], ast.ListComp):
                findings.append(
                    _make_finding(
                        "info", "medium", "performance",
                        "sum() should use a generator expression instead of a list comprehension",
                        node.lineno,
                        "Use sum(x for x in items) instead of sum([x for x in items])",
                    )
                )

        # 5. any/all with list comprehension
        for n in node.iter_child_nodes() if hasattr(node, 'iter_child_nodes') else []:
            pass
        # Proper walk
        for subnode in ast.walk(node) if isinstance(node, ast.Module) else (node,):
            pass  # handled separately

    # 5 (separate pass): any/all with list comprehension
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("any", "all"):
            if node.args and isinstance(node.args[0], ast.ListComp):
                findings.append(
                    _make_finding(
                        "info", "low", "performance",
                        f"Use a generator expression instead of list comprehension for {node.func.id}()",
                        node.lineno,
                        f"Use {node.func.id}(x for x in items if condition) to save memory",
                    )
                )

        # 6. in [list] -> in {set}
        if isinstance(node, ast.Compare):
            for op, comp in zip(node.ops, node.comparators):
                if isinstance(op, ast.In) and isinstance(comp, ast.List):
                    findings.append(
                        _make_finding(
                            "info", "low", "performance",
                            "List lookup (in list) is O(n); consider using a set for O(1) lookup",
                            node.lineno,
                            "Replace list with set: if x in my_set:",
                        )
                    )

    return findings


# ════════════════════════════════════════════════════════════════
#  STYLE / CODE QUALITY
# ════════════════════════════════════════════════════════════════

def check_style(tree: ast.AST, source: str) -> List[Finding]:
    findings: list = []
    lines = source.split("\n")

    # 1. Naming conventions + docstrings
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name
            if re.match(r"^[a-z]+[A-Z]", name):
                snake = _camel_to_snake(name)
                if name != snake:
                    findings.append(
                        _make_finding(
                            "warning", "low", "style",
                            f"Function '{name}' uses camelCase, Python recommends snake_case",
                            node.lineno,
                            f"Rename '{name}' to '{snake}'",
                        )
                    )
            if (len(node.body) == 0
                or not isinstance(node.body[0], ast.Expr)
                or not isinstance(node.body[0].value, ast.Constant)
                or not isinstance(node.body[0].value.value, str)):
                findings.append(
                    _make_finding(
                        "warning", "medium", "style",
                        f"Function '{name}' is missing a docstring",
                        node.lineno,
                        "Add a triple-quoted docstring after the function definition",
                    )
                )

        if isinstance(node, ast.ClassDef):
            if (len(node.body) == 0
                or not isinstance(node.body[0], ast.Expr)
                or not isinstance(node.body[0].value, ast.Constant)
                or not isinstance(node.body[0].value.value, str)):
                findings.append(
                    _make_finding(
                        "warning", "medium", "style",
                        f"Class '{node.name}' is missing a docstring",
                        node.lineno,
                        "Add a class docstring",
                    )
                )

    # 2. Function too long
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            length = _count_lines(node)
            if length > 50:
                findings.append(
                    _make_finding(
                        "warning", "medium", "style",
                        f"Function '{node.name}' is too long ({length} lines, max 50 recommended)",
                        node.lineno,
                        "Split the function into smaller functions, each doing one thing",
                    )
                )

    # 3. Too many parameters
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            n = len(node.args.args)
            if n > 5:
                findings.append(
                    _make_finding(
                        "warning", "medium", "style",
                        f"Function '{node.name}' has too many parameters ({n}, max 5 recommended)",
                        node.lineno,
                        "Group related parameters into a data class or use **kwargs",
                    )
                )

    # 4. Unused imports
    used: set = set()
    imports: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                imports[name] = node.lineno
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname or alias.name
                imports[name] = node.lineno
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            used.add(node.value.id)

    for name, line in imports.items():
        if name not in used:
            findings.append(
                _make_finding(
                    "info", "low", "style",
                    f"Unused import: '{name}'",
                    line,
                    f"Remove unused import {name}",
                )
            )

    # 5. Line too long
    for i, line in enumerate(lines, 1):
        stripped = line.rstrip("\n").rstrip("\r")
        if len(stripped) > 100:
            findings.append(
                _make_finding(
                    "info", "low", "style",
                    f"Line {i} is too long ({len(stripped)} chars, max 100 recommended)",
                    i,
                    "Split the long line into multiple lines or use implicit line continuation",
                )
            )

    # 6. Too many consecutive blank lines
    blank = 0
    for i, line in enumerate(lines, 1):
        if not line.strip():
            blank += 1
        else:
            if blank > 2:
                findings.append(
                    _make_finding(
                        "info", "low", "style",
                        f"Too many consecutive blank lines ({blank}, max 2 recommended)",
                        i - blank,
                        "Reduce consecutive blank lines to keep code compact",
                    )
                )
            blank = 0

    return findings


# ════════════════════════════════════════════════════════════════
#  BEST PRACTICES
# ════════════════════════════════════════════════════════════════

def check_best_practices(tree: ast.AST) -> List[Finding]:
    findings: list = []

    for node in ast.walk(tree):
        # 1. Mutable default arguments
        if isinstance(node, ast.FunctionDef):
            for default in node.args.defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    findings.append(
                        _make_finding(
                            "warning", "high", "best_practice",
                            f"Function '{node.name}' uses a mutable object as default argument",
                            node.lineno,
                            "Use None as default, then initialize inside the function: "
                            "def func(items=None): if items is None: items = []",
                        )
                    )

        # 2. == True / == False
        if isinstance(node, ast.Compare):
            for op, comp in zip(node.ops, node.comparators):
                if isinstance(op, ast.Eq):
                    if isinstance(comp, ast.Constant) and comp.value is True:
                        findings.append(
                            _make_finding(
                                "info", "low", "best_practice",
                                "Use 'if x is True:' instead of 'if x == True:'",
                                node.lineno,
                                "Use 'is True' instead of '== True'",
                            )
                        )
                    elif isinstance(comp, ast.Constant) and comp.value is False:
                        findings.append(
                            _make_finding(
                                "info", "low", "best_practice",
                                "Use 'if not x:' or 'if x is False:' instead of '== False'",
                                node.lineno,
                                "Use 'if not x' instead of 'if x == False'",
                            )
                        )

    return findings


# ════════════════════════════════════════════════════════════════
#  NON-PYTHON ANALYZER (regex-based)
# ════════════════════════════════════════════════════════════════

_LANG_CONFIGS = {
    "javascript": {},
    "typescript": {},
    "java": {},
    "go": {},
    "rust": {},
    "cpp": {},
}

_JS_EVAL = re.compile(r"(?<!\.)\beval\(|new\s+Function\(|setTimeout\(\s*['\"]")
_NONPY_SQL = re.compile(r"(?i)(execute|query|raw)\s*\(.*?(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE)")
_NONPY_SHELL = re.compile(r"(?i)shell\s*[:=]\s*true")
_TODO = re.compile(r"(?i)(TODO|FIXME|XXX|HACK)")


def _analyse_non_python(source: str, language: str) -> List[Finding]:
    findings: list = []
    lines = source.split("\n")
    lang_map = {
        "javascript": "js", "typescript": "ts",
        "java": "java", "go": "go", "rust": "rust",
        "c++": "cpp", "cpp": "cpp", "c": "cpp",
    }

    canonical = lang_map.get(language.lower(), "")
    if not canonical:
        return findings

    # 1. Hardcoded secrets
    for match in _SENSITIVE_REGEX.finditer(source):
        line_num = source[:match.start()].count("\n") + 1
        findings.append(
            _make_finding(
                "error", "critical", "security",
                "Suspected hardcoded secret/password/Token detected",
                line_num,
                "Use environment variables or a secret management service",
            )
        )

    # 2. eval/Function() (JS/TS)
    if canonical in ("js", "ts"):
        for match in _JS_EVAL.finditer(source):
            line_num = source[:match.start()].count("\n") + 1
            findings.append(
                _make_finding(
                    "error", "critical", "security",
                    "Use of unsafe eval() or dynamic code execution",
                    line_num,
                    "Avoid eval(), use JSON.parse() or other safe alternatives",
                )
            )

    # 3. SQL injection
    for match in _NONPY_SQL.finditer(source):
        line_num = source[:match.start()].count("\n") + 1
        findings.append(
            _make_finding(
                "error", "critical", "security",
                "Possible SQL injection risk",
                line_num,
                "Use parameterized queries or an ORM framework",
            )
        )

    # 4. shell=true
    for match in _NONPY_SHELL.finditer(source):
        line_num = source[:match.start()].count("\n") + 1
        findings.append(
            _make_finding(
                "error", "critical", "security",
                "Unsafe shell=true detected",
                line_num,
                "Avoid shell=True, use explicit argument lists",
            )
        )

    # 5. Line too long
    for i, line in enumerate(lines, 1):
        stripped = line.rstrip("\n").rstrip("\r")
        if len(stripped) > 100:
            findings.append(
                _make_finding(
                    "info", "low", "style",
                    f"Line {i} is too long ({len(stripped)} chars, max 100 recommended)",
                    i,
                    "Split the long line into multiple lines",
                )
            )

    # 6. TODO/FIXME
    for match in _TODO.finditer(source):
        line_num = source[:match.start()].count("\n") + 1
        findings.append(
            _make_finding(
                "info", "low", "best_practice",
                f"Code contains '{match.group(1).upper()}' marker",
                line_num,
                f"Complete the work marked by '{match.group(1).upper()}' then remove the comment",
            )
        )

    return findings

# ════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ════════════════════════════════════════════════════════════════

def analyze(code: str, language: str = "python", progress_callback=None) -> Dict[str, Any]:
    """
    Analyze code and return results with summary.

    Args:
        code: Source code string
        language: Programming language
        progress_callback: Optional async callable(stage, progress) for WS progress

    Returns:
        dict with status, results, summary
    """
    start_time = time.time()
    all_findings: list = []

    def _report(stage: str, progress: int):
        if progress_callback:
            try:
                import asyncio
                asyncio.ensure_future(progress_callback(stage, progress))
            except Exception:
                pass

    _report("parsing", 5)
    lang = language.lower() if language else "python"

    if lang == "python":
        _report("parsing_ast", 10)
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            all_findings.append(
                _make_finding(
                    "error", "high", "bug",
                    f"Syntax error: {e.msg}",
                    e.lineno or 1,
                    f"Fix syntax: {e.msg}",
                )
            )
            _report("error", 100)
            return {
                "status": "completed",
                "results": all_findings,
                "summary": build_summary(all_findings, (time.time() - start_time) * 1000),
            }

        _report("bugs", 25)
        all_findings.extend(check_bugs(tree, code))

        _report("security", 40)
        all_findings.extend(check_security(code))

        _report("performance", 55)
        all_findings.extend(check_performance(tree))

        _report("style", 70)
        all_findings.extend(check_style(tree, code))

        _report("best_practices", 85)
        all_findings.extend(check_best_practices(tree))

    else:
        _report("security", 25)
        all_findings.extend(check_security(code))

        _report("analysis", 50)
        all_findings.extend(_analyse_non_python(code, lang))

        _report("style", 75)

    _report("dedup", 90)
    seen: set = set()
    unique: list = []
    for f in all_findings:
        key = (f.get("line", 0), f.get("message", ""))
        if key not in seen:
            seen.add(key)
            unique.append(f)

    elapsed_ms = (time.time() - start_time) * 1000
    summary = build_summary(unique, elapsed_ms)

    _report("complete", 100)

    return {
        "status": "completed",
        "results": unique,
        "summary": summary,
    }

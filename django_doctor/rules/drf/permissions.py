from __future__ import annotations

import ast

from django_doctor.core.context import ScanContext
from django_doctor.core.diagnostics import Diagnostic
from django_doctor.rules.base import Rule


class AllowAnyPermissionRule(Rule):
    id = "django/drf/allow-any-permission"
    title = "AllowAny permission used"
    category = "drf"
    default_severity = "info"
    tags = ["drf", "permissions", "api"]

    def check(self, context: ScanContext) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        if context.rule_setting("check_drf_permissions", True) is False:
            return diagnostics
        for file in context.python_files():
            content = context.read_file(file)
            if content is None or "AllowAny" not in content:
                continue
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if _is_permission_assignment(node) and _contains_allow_any(_assignment_value(node)):
                    diagnostics.append(
                        self.diagnostic(
                            message="permission_classes contains AllowAny.",
                            file=file,
                            line=getattr(node, "lineno", 1),
                            recommendation="Ensure this endpoint is intentionally public.",
                            why="AllowAny disables authentication requirements for the view.",
                            confidence="medium",
                        )
                    )
        return diagnostics


def _is_permission_assignment(node: ast.AST) -> bool:
    if isinstance(node, ast.Assign):
        return any(_is_permission_target(target) for target in node.targets)
    if isinstance(node, ast.AnnAssign):
        return _is_permission_target(node.target)
    return False


def _is_permission_target(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "permission_classes"
    if isinstance(node, ast.Attribute):
        return node.attr == "permission_classes"
    return False


def _assignment_value(node: ast.AST) -> ast.AST | None:
    if isinstance(node, ast.Assign):
        return node.value
    if isinstance(node, ast.AnnAssign):
        return node.value
    return None


def _contains_allow_any(node: ast.AST | None) -> bool:
    if node is None:
        return False
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id == "AllowAny":
            return True
        if isinstance(child, ast.Attribute) and child.attr == "AllowAny":
            return True
    return False

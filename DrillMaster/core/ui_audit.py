"""Static safety audit for Qt signal connections (no QGIS dependency)."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class UiAuditIssue:
    file: str
    line: int
    code: str
    message: str


def audit_ui_connections(paths) -> list[UiAuditIssue]:
    """Find missing callbacks and accidental Qt bool capture.

    QPushButton.clicked and QAction.triggered emit a boolean. Qt can discard it
    for a zero-argument slot, but a method with an optional semantic argument
    may accidentally receive ``False`` (the cause of the component-dialog
    regression). Such methods must be wrapped in a lambda or accept ``*args``.
    """
    issues = []
    for raw_path in paths:
        path = Path(raw_path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as error:
            issues.append(UiAuditIssue(
                str(path), getattr(error, "lineno", 0) or 0,
                "UNREADABLE_UI_MODULE", str(error)))
            continue

        for class_node in (
                node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
            methods = {
                node.name: node for node in class_node.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            for call in ast.walk(class_node):
                if (not isinstance(call, ast.Call)
                        or not isinstance(call.func, ast.Attribute)
                        or call.func.attr != "connect"
                        or not call.args):
                    continue
                callback = call.args[0]
                if not (isinstance(callback, ast.Attribute)
                        and isinstance(callback.value, ast.Name)
                        and callback.value.id == "self"):
                    continue
                method = methods.get(callback.attr)
                if method is None:
                    if callback.attr in {
                            "accept", "reject", "close", "deleteLater"}:
                        continue
                    issues.append(UiAuditIssue(
                        str(path), call.lineno, "MISSING_CALLBACK",
                        f"{class_node.name}.{callback.attr} n’existe pas."))
                    continue
                signal = call.func.value
                signal_name = signal.attr if isinstance(signal, ast.Attribute) else ""
                if signal_name not in {"clicked", "triggered"}:
                    continue
                positional = method.args.args[1:]  # self excluded
                if positional and method.args.vararg is None:
                    issues.append(UiAuditIssue(
                        str(path), call.lineno, "QT_BOOL_CAPTURE",
                        f"{class_node.name}.{callback.attr} peut recevoir le booléen "
                        f"émis par {signal_name}; utilisez une lambda ou *args."))
    return issues

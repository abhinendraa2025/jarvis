"""
Calculator module for JARVIS.

Evaluates mathematical expressions extracted from user input.
Uses a safe parser instead of eval().
"""

from __future__ import annotations

import ast
import logging
import operator
import re
from typing import Union

logger = logging.getLogger(__name__)

# Allowed operators in the safe evaluator
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node: ast.AST) -> Union[int, float]:
    """Recursively evaluate an AST node using only safe arithmetic ops."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value!r}")
    if isinstance(node, ast.BinOp):
        op_fn = _OPERATORS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        # Guard against division by zero
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and right == 0:
            raise ZeroDivisionError("Division by zero")
        return op_fn(left, right)
    if isinstance(node, ast.UnaryOp):
        op_fn = _OPERATORS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op_fn(_safe_eval(node.operand))
    raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def evaluate_expression(expression: str) -> str:
    """
    Evaluate a mathematical *expression* string and return the result.

    Args:
        expression: A string like ``"2 + 2"`` or ``"(10 / 2) ** 3"``.

    Returns:
        A string describing the result or an error message.
    """
    expression = expression.strip()
    if not expression:
        return "Please provide a mathematical expression."

    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)
        # Format nicely: drop ".0" for whole-number floats
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"{expression} = {result}"
    except ZeroDivisionError:
        return "I cannot divide by zero."
    except (ValueError, TypeError, SyntaxError) as exc:
        logger.debug("Expression parse error '%s': %s", expression, exc)
        return f"I couldn't evaluate that expression. Please use standard operators: +, -, *, /, **"
    except Exception as exc:
        logger.error("Calculator error: %s", exc)
        return "An error occurred during calculation."


def _extract_expression(text: str) -> str:
    """Pull the mathematical part out of a user utterance."""
    # Try to grab everything after common command words
    pattern = r"(?:calculate|compute|solve|math|what is|what's)\s+(.+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Otherwise try to grab a standalone numeric expression
    expr_match = re.search(r"([\d\s\.\+\-\*\/\%\^\(\)]+)", text)
    if expr_match:
        return expr_match.group(1).strip()
    return text.strip()


def handle_calculate(text: str) -> str:
    """
    Handler called by JARVIS when a 'calculate' intent is detected.

    Args:
        text: Raw user utterance.

    Returns:
        Calculation result string.
    """
    expression = _extract_expression(text)
    # Normalise '^' to '**' for power
    expression = expression.replace("^", "**")
    logger.info("Evaluating expression: %s", expression)
    return evaluate_expression(expression)

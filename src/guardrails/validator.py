from dataclasses import dataclass
from typing import List

import sqlglot
from sqlglot import exp


@dataclass
class ValidationResult:
    allowed: bool
    checks: List[str]
    errors: List[str]


BLOCKED_NODES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Create,
    exp.Drop,
    exp.Alter,
)


def validate_sql(sql: str) -> ValidationResult:
    """
    Deterministically validate LLM-generated SQL before execution.

    Policy:
    - Exactly one statement
    - SQLite-compatible syntax
    - Read-only SELECT / CTE queries only
    - No destructive DML/DDL
    """

    checks = []
    errors = []

    # --------------------------------------------------
    # 1. Basic validation
    # --------------------------------------------------

    if not sql or not sql.strip():
        return ValidationResult(
            allowed=False,
            checks=[],
            errors=["empty_sql"],
        )

    sql = sql.strip()

    # --------------------------------------------------
    # 2. Parse SQL and reject multiple statements
    # --------------------------------------------------

    try:
        statements = sqlglot.parse(
            sql,
            read="sqlite",
        )
    except Exception as exc:
        return ValidationResult(
            allowed=False,
            checks=[],
            errors=[f"syntax_error: {exc}"],
        )

    if len(statements) != 1:
        errors.append("multiple_statements_not_allowed")
    else:
        checks.append("single_statement")

    if errors:
        return ValidationResult(
            allowed=False,
            checks=checks,
            errors=errors,
        )

    tree = statements[0]
    # Check SELECT structure
    if isinstance(tree, exp.Select):
        if not tree.expressions:
            errors.append("select_has_no_expressions")
        else:
            checks.append("valid_select_structure")

    # --------------------------------------------------
    # 3. Read-only operation check
    # --------------------------------------------------

    blocked = tree.find(*BLOCKED_NODES)

    if blocked is not None:
        errors.append(
            f"blocked_operation: {blocked.key}"
        )
    else:
        checks.append("read_only")

    # --------------------------------------------------
    # 4. Root query type
    # --------------------------------------------------

    if isinstance(tree, exp.Select):
        checks.append("select_query")

    elif isinstance(tree, exp.Union):
        checks.append("select_query")

    else:
        errors.append(
            f"unsupported_query_type: {tree.key}"
        )

    # --------------------------------------------------
    # Final result
    # --------------------------------------------------

    return ValidationResult(
        allowed=len(errors) == 0,
        checks=checks,
        errors=errors,
    )
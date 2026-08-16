from src.guardrails.validator import validate_sql


def test_select_allowed():
    result = validate_sql(
        "SELECT * FROM deliveries"
    )

    assert result.allowed is True


def test_cte_allowed():
    result = validate_sql(
        """
        WITH runs AS (
            SELECT batter, SUM(runs_batter) AS runs
            FROM deliveries
            GROUP BY batter
        )
        SELECT *
        FROM runs
        ORDER BY runs DESC
        """
    )

    assert result.allowed is True


def test_drop_blocked():
    result = validate_sql(
        "DROP TABLE deliveries"
    )

    assert result.allowed is False


def test_delete_blocked():
    result = validate_sql(
        "DELETE FROM deliveries"
    )

    assert result.allowed is False


def test_update_blocked():
    result = validate_sql(
        "UPDATE deliveries SET runs_batter = 0"
    )

    assert result.allowed is False


def test_insert_blocked():
    result = validate_sql(
        "INSERT INTO deliveries VALUES (1, 2, 3)"
    )

    assert result.allowed is False


def test_alter_blocked():
    result = validate_sql(
        "ALTER TABLE deliveries ADD COLUMN test TEXT"
    )

    assert result.allowed is False


def test_create_blocked():
    result = validate_sql(
        "CREATE TABLE evil (id INTEGER)"
    )

    assert result.allowed is False


def test_multiple_statements_blocked():
    result = validate_sql(
        """
        SELECT * FROM deliveries;
        DROP TABLE deliveries;
        """
    )

    assert result.allowed is False


def test_invalid_sql_blocked():
    result = validate_sql(
        "SELECT FROM deliveries"
    )

    assert result.allowed is False
    
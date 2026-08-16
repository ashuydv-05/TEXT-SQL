import time

from main import load_schema, make_client, generate_sql, run_sql
from src.guardrails.validator import validate_sql


MODEL_SLUG = "openai/gpt-oss-20b:free"
DB_PATH = "ipl_2021_2024.db"


class QueryService:

    def process(self, question: str) -> dict:
        start_time = time.perf_counter()

        # -----------------------------------------
        # 1. Basic request validation
        # -----------------------------------------
        if not question or not question.strip():
            return {
                "question": question,
                "sql": None,
                "verification": {
                    "status": "FAIL",
                    "checks": [],
                    "errors": ["empty_question"],
                },
                "result": [],
                "explanation": "Please provide a question.",
                "latency_ms": self._latency(start_time),
            }

        try:
            # -----------------------------------------
            # 2. Load database schema
            # -----------------------------------------
            schema = load_schema()

            # -----------------------------------------
            # 3. Generate SQL using GPT-5.1
            # -----------------------------------------
            client = make_client()

            sql = generate_sql(
                question,
                schema,
                client,
                MODEL_SLUG,
            )

            if not sql:
                return {
                    "question": question,
                    "sql": None,
                    "verification": {
                        "status": "FAIL",
                        "checks": [],
                        "errors": ["empty_generated_sql"],
                    },
                    "result": [],
                    "explanation": "The model did not generate a SQL query.",
                    "latency_ms": self._latency(start_time),
                }

            # -----------------------------------------
            # 4. SQL Guardrail
            # -----------------------------------------
            validation = validate_sql(sql)

            if not validation.allowed:
                return {
                    "question": question,
                    "sql": sql,
                    "verification": {
                        "status": "FAIL",
                        "checks": validation.checks,
                        "errors": validation.errors,
                    },
                    "result": [],
                    "explanation": (
                        "The generated SQL was rejected by the "
                        "SQL safety guardrail."
                    ),
                    "latency_ms": self._latency(start_time),
                }

            # -----------------------------------------
            # 5. Execute SQL
            # -----------------------------------------
            import sqlite3

            conn = sqlite3.connect(DB_PATH)

            try:
                result_df = run_sql(conn, sql)
            finally:
                conn.close()

            # -----------------------------------------
            # 6. Execution verification
            # -----------------------------------------
            if result_df is None:
                return {
                    "question": question,
                    "sql": sql,
                    "verification": {
                        "status": "FAIL",
                        "checks": validation.checks,
                        "errors": ["sql_execution_failed"],
                    },
                    "result": [],
                    "explanation": (
                        "The generated SQL passed the safety checks "
                        "but could not be executed successfully."
                    ),
                    "latency_ms": self._latency(start_time),
                }

            # -----------------------------------------
            # 7. Result conversion
            # -----------------------------------------
            result = result_df.to_dict(orient="records")

            checks = validation.checks.copy()
            checks.append("execution_success")

            if result:
                checks.append("result_available")
            else:
                checks.append("empty_result")

            # -----------------------------------------
            # 8. Final response
            # -----------------------------------------
            return {
                "question": question,
                "sql": sql,
                "verification": {
                    "status": "PASS",
                    "checks": checks,
                    "errors": [],
                },
                "result": result,
                "explanation": self._explain_result(
                    question,
                    result,
                ),
                "latency_ms": self._latency(start_time),
            }

        except Exception as exc:
            return {
                "question": question,
                "sql": None,
                "verification": {
                    "status": "FAIL",
                    "checks": [],
                    "errors": [f"pipeline_error: {str(exc)}"],
                },
                "result": [],
                "explanation": (
                    "The query could not be processed successfully."
                ),
                "latency_ms": self._latency(start_time),
            }

    @staticmethod
    def _latency(start_time: float) -> float:
        return round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

    @staticmethod
    def _explain_result(question: str, result: list[dict]) -> str:
        if not result:
            return (
                "The query executed successfully, but no matching "
                "records were found."
            )

        return (
            f"The query was generated and executed successfully "
            f"for: '{question}'. "
            f"The database returned {len(result)} result row(s)."
        )


query_service = QueryService()
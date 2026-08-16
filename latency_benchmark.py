import os
import re
import time
import sqlite3
import statistics
import pandas as pd

from dotenv import load_dotenv
from openai import OpenAI

from evaluator import evaluate_one


load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

DB_PATH = "ipl_2021_2024.db"
SCHEMA_PATH = "schema.sql"
GOLDEN_PATH = "golden_dataset.csv"

MODELS = [
    ("GPT-5.1", "openai/gpt-5.1"),
    ("Claude Sonnet 4.5", "anthropic/claude-sonnet-4.5"),
    ("Qwen3 Coder", "qwen/qwen3-coder"),
]


def load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return f.read().strip()


def clean_sql(raw):
    if not raw:
        return ""

    text = raw.strip()

    fence = re.search(
        r"```(?:sql)?\s*(.*?)```",
        text,
        re.DOTALL | re.IGNORECASE
    )

    if fence:
        text = fence.group(1).strip()

    text = re.sub(
        r"^\s*sql\s*\n",
        "",
        text,
        flags=re.IGNORECASE
    )

    match = re.search(
        r"\b(SELECT|WITH)\b",
        text,
        re.IGNORECASE
    )

    if match:
        text = text[match.start():]

    return text.strip().strip("`").rstrip(";").strip("`").strip()


def generate_sql(question, schema, client, slug):
    system_msg = (
        "You are a text-to-SQL generator. "
        "Given a database schema and a question, "
        "return a single SQL query that answers it. "
        "Use SQLite syntax. "
        "Return only the SQL query."
    )

    user_msg = (
        f"Schema:\n{schema}\n\n"
        f"Question: {question}\n\n"
        "SQL:"
    )

    start = time.perf_counter()

    response = client.chat.completions.create(
        model=slug,
        temperature=0,
        max_tokens=800,
        messages=[
            {
                "role": "system",
                "content": system_msg
            },
            {
                "role": "user",
                "content": user_msg
            },
        ],
    )

    latency_ms = (time.perf_counter() - start) * 1000

    raw = response.choices[0].message.content
    sql = clean_sql(raw)

    return sql, latency_ms


def run_sql(conn, sql):
    try:
        return pd.read_sql_query(sql, conn)
    except Exception:
        return None


def main():

    if not API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY missing from .env"
        )

    schema = load_schema()
    golden = pd.read_csv(GOLDEN_PATH)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY,
    )

    conn = sqlite3.connect(DB_PATH)

    results = []

    for model_name, model_slug in MODELS:

        print("\n" + "=" * 70)
        print(f"MODEL: {model_name}")
        print("=" * 70)

        latencies = []
        correct_count = 0
        generation_failures = 0
        sql_failures = 0

        for _, row in golden.iterrows():

            question_id = row["id"]
            question = row["q"]

            print(
                f"\n[{model_name}] "
                f"Question {question_id}/20"
            )

            try:

                sql, latency_ms = generate_sql(
                    question,
                    schema,
                    client,
                    model_slug
                )

                latencies.append(latency_ms)

                print(
                    f"  Generation latency: "
                    f"{latency_ms:.0f} ms"
                )

            except Exception as e:

                generation_failures += 1

                print(
                    f"  GENERATION ERROR: {e}"
                )

                results.append({
                    "model": model_name,
                    "question_id": question_id,
                    "latency_ms": None,
                    "generation_success": False,
                    "sql_success": False,
                    "correct": False,
                    "error": str(e),
                })

                continue

            gold_df = run_sql(
                conn,
                row["sql"]
            )

            generated_df = run_sql(
                conn,
                sql
            )

            if generated_df is None:
                sql_failures += 1
                correct = False
                reason = "sql_error"

            else:
                verdict = evaluate_one(
                    gold_df,
                    generated_df
                )

                correct = verdict["correct"]
                reason = verdict["reason"]

                if correct:
                    correct_count += 1

            results.append({
                "model": model_name,
                "question_id": question_id,
                "latency_ms": round(latency_ms, 2),
                "generation_success": True,
                "sql_success": generated_df is not None,
                "correct": correct,
                "error": reason,
            })

            print(
                f"  Result: "
                f"{'✓' if correct else '✗'} "
                f"{reason}"
            )

        if latencies:

            avg_latency = statistics.mean(latencies)
            median_latency = statistics.median(latencies)

            sorted_latencies = sorted(latencies)

            p95_index = min(
                len(sorted_latencies) - 1,
                int(len(sorted_latencies) * 0.95)
            )

            p95_latency = sorted_latencies[p95_index]

            print("\nRESULT")
            print("-" * 40)
            print(
                f"Accuracy: "
                f"{correct_count}/20 "
                f"({correct_count / 20 * 100:.1f}%)"
            )
            print(
                f"Average latency: "
                f"{avg_latency:.0f} ms"
            )
            print(
                f"Median latency: "
                f"{median_latency:.0f} ms"
            )
            print(
                f"P95 latency: "
                f"{p95_latency:.0f} ms"
            )
            print(
                f"Fastest: "
                f"{min(latencies):.0f} ms"
            )
            print(
                f"Slowest: "
                f"{max(latencies):.0f} ms"
            )
            print(
                f"Generation failures: "
                f"{generation_failures}"
            )
            print(
                f"SQL failures: "
                f"{sql_failures}"
            )

    conn.close()

    output = pd.DataFrame(results)

    output.to_csv(
        "latency_benchmark_results.csv",
        index=False
    )

    print(
        "\nSaved → latency_benchmark_results.csv"
    )


if __name__ == "__main__":
    main()
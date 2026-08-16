"""
main.py - controls the entire eval flow through OpenRouter.

For each model:
  1. load the model client
  2. run the golden dataset (generate SQL for each question)
  3. run the gold SQL and generated SQL on the DB
  4. evaluate (compare to gold, using evaluator.py)
  5. log the score

Files it depends on:
  - schema.sql             (the schema, for the prompt)
  - golden_dataset.csv     (id + diff + q + sql)
  - model_openrouter_slug.py  (models under test -> MODELS)
  - evaluator.py           (the comparison logic)

Setup:
  pip install openai python-dotenv pandas
  .env file with:  OPENROUTER_API_KEY=sk-or-...
"""

import os
import re
import sqlite3
import pandas as pd
from dotenv import load_dotenv

from openai import OpenAI, RateLimitError

from model_openrouter_slug import MODELS
from evaluator import evaluate_one


# ---------- CONFIG ----------
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

DB_PATH = "ipl_2021_2024.db"
SCHEMA_PATH = "schema.sql"
GOLDEN_PATH = "golden_dataset.csv"
RESULTS_PATH = "eval_results.csv"
# ----------------------------


# ---------- helpers ----------

def load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return f.read().strip()


def load_golden():
    golden = pd.read_csv(GOLDEN_PATH)

    expected = {"id", "diff", "q", "sql"}
    missing = expected - set(golden.columns)

    if missing:
        raise ValueError(
            f"{GOLDEN_PATH} is missing columns: {sorted(missing)}"
        )

    return golden


def make_client():
    """Create an OpenRouter client using OpenAI's compatible SDK."""
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY,
    )


def clean_sql(raw):
    """Extract only plausible executable SQL."""

    if not raw:
        return ""

    text = raw.strip()

    # Remove markdown code fences if present
    fence = re.search(
        r"```(?:sql)?\s*(.*?)```",
        text,
        re.DOTALL | re.IGNORECASE,
    )

    if fence:
        text = fence.group(1).strip()

    # Find SELECT or WITH
    match = re.search(
        r"\b(SELECT|WITH)\b",
        text,
        re.IGNORECASE,
    )

    if not match:
        return ""

    candidate = text[match.start():].strip()

    # Basic sanity check:
    # executable SQL should contain FROM for our Text-to-SQL use case
    if not re.search(r"\bFROM\b", candidate, re.IGNORECASE):
        return ""

    # Reject obvious prose
    if "\nWe " in candidate or "\nThe " in candidate:
        return ""

    return candidate.rstrip(";").strip()


def generate_sql(question, schema, client, slug):
    """Ask one model for SQL via OpenRouter. Returns cleaned SQL string."""

    system_msg = (
        """You are a SQLite Text-to-SQL generator.
Your ONLY task is to output ONE executable SQLite SQL query.

STRICT RULES:
1. Before returning the SQL, ensure:
- all required clauses are complete
- all WHERE expressions have values
- GROUP BY is included when aggregation is used
- ORDER BY is included when ranking is requested
- all referenced tables/columns exist in the schema
2. Do NOT explain your reasoning.
3. Do NOT describe the approach.
4. Do NOT write analysis.
5. Do NOT write comments.
6. Do NOT write markdown.
7. Do NOT write ```sql fences.
8. Do NOT repeat the question.
9. The first token of your response MUST be SELECT or WITH.
10. The final output must be directly executable by SQLite.

Use ONLY tables and columns present in the provided schema.
If the question requires multiple steps, use a CTE with WITH.

Schema:"""
    )

    user_msg = (
        f"Schema:\n{schema}\n\n"
        f"Question: {question}\n\n"
        f"SQL:"
    )

    response = client.chat.completions.create(
        model=slug,
        temperature=0,
        max_tokens=800,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
    )

    # ---------- DEBUG: RAW MODEL OUTPUT ----------

    raw = response.choices[0].message.content

    print("\n=========== RAW MODEL OUTPUT ===========")
    print(repr(raw))
    print("========================================\n")

    # ---------- CLEAN SQL ----------

    cleaned = clean_sql(raw)

    # ---------- DEBUG: CLEANED SQL ----------

    print("=========== CLEANED SQL ================")
    print(repr(cleaned))
    print("========================================")

    return cleaned


def append_result(
    all_rows,
    model,
    qid,
    difficulty,
    correct,
    reason,
    sql=""
):
    all_rows.append(
        dict(
            model=model,
            id=qid,
            difficulty=difficulty,
            correct=correct,
            reason=reason,
            sql=sql,
        )
    )


def run_sql(conn, sql):
    """Run SQL on the DB. Returns a DataFrame, or None if it errored."""

    try:
        return pd.read_sql_query(sql, conn)

    except Exception:
        return None


# ---------- the main flow ----------

def run_eval():

    schema = load_schema()
    golden = load_golden()
    client = make_client()

    conn = sqlite3.connect(DB_PATH)

    all_rows = []
    scoreboard = {}

    for name, slug in MODELS:

        print(
            f"\n{'=' * 60}\n"
            f"MODEL: {name}  ({slug})\n"
            f"{'=' * 60}"
        )

        correct = 0
        skip_model = False

        for _, g in golden.iterrows():

            qid = g["id"]
            difficulty = g["diff"]
            question = g["q"]

            order_sensitive = False

            if skip_model:

                append_result(
                    all_rows,
                    name,
                    qid,
                    difficulty,
                    False,
                    "skipped_rate_limit",
                )

                continue

            # 1. Run GOLD SQL
            gold_df = run_sql(conn, g["sql"])

            if gold_df is None:

                print(
                    f"  #{qid:2} "
                    f"[{difficulty:6}] "
                    f"GOLD-SQL-ERROR"
                )

                append_result(
                    all_rows,
                    name,
                    qid,
                    difficulty,
                    False,
                    "gold_sql_error",
                )

                continue

            # 2. Generate SQL
            try:

                sql = generate_sql(
                    question,
                    schema,
                    client,
                    slug,
                )

            except RateLimitError as e:

                print(
                    f"  #{qid:2} "
                    f"[{difficulty:6}] "
                    f"RATE-LIMIT: {e.message}"
                )

                append_result(
                    all_rows,
                    name,
                    qid,
                    difficulty,
                    False,
                    "rate_limited",
                )

                skip_model = True
                continue

            except Exception as e:

                print(
                    f"  #{qid:2} "
                    f"[{difficulty:6}] "
                    f"GEN-ERROR: {e}"
                )

                append_result(
                    all_rows,
                    name,
                    qid,
                    difficulty,
                    False,
                    "gen_error",
                )

                continue

            # 3. Run generated SQL on DB
            gen_df = run_sql(conn, sql)

            # 4. Evaluate
            verdict = evaluate_one(
                gold_df,
                gen_df,
                order_sensitive,
            )

            if verdict["correct"]:
                correct += 1

            mark = "OK " if verdict["correct"] else "XX "

            print(
                f"  #{qid:2} "
                f"[{difficulty:6}] "
                f"{mark} "
                f"{verdict['reason']}"
            )

            append_result(
                all_rows,
                name,
                qid,
                difficulty,
                verdict["correct"],
                verdict["reason"],
                sql,
            )

        # Model score
        total = len(golden)

        scoreboard[name] = correct

        print(
            f"\n  SCORE: "
            f"{correct}/{total} = "
            f"{100 * correct / total:.1f}%"
        )

    conn.close()

    # 5. Log final scores

    print(
        f"\n{'=' * 60}\n"
        f"FINAL SCOREBOARD (execution accuracy)\n"
        f"{'=' * 60}"
    )

    total = len(golden)

    for name, _ in MODELS:

        c = scoreboard[name]

        print(
            f"  {name:18s} "
            f"{c:2}/{total}  "
            f"= {100 * c / total:5.1f}%"
        )

    # Save detailed results
    pd.DataFrame(all_rows).to_csv(
        RESULTS_PATH,
        index=False,
    )

    print(
        f"\nDetailed results saved -> "
        f"{RESULTS_PATH}"
    )


if __name__ == "__main__":

    if not API_KEY:

        print(
            "Missing OPENROUTER_API_KEY - "
            "add it to your .env file"
        )

    else:

        run_eval()
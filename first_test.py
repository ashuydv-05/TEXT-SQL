"""
First test: send ONE question to ONE model via OpenRouter, print the raw SQL.
No loop, no scoring, no cleaning.

Setup:
  pip install openai python-dotenv
  Put OPENROUTER_API_KEY in .env.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ---------- FILL THESE IN ----------
MODEL   = "openai/gpt-oss-20b:free"          # OpenRouter model slug
# -----------------------------------

# 1. Read the schema from disk
with open("schema.sql", encoding="utf-8") as f:
    schema = f.read().strip()

# 2. The one question we're testing
question = "Who scored the most runs in 2024?"

# 3. Build the prompt (schema + question)
system_msg = (
    "You are a text-to-SQL generator. "
    "Given a database schema and a question, return a single SQL query that answers it. "
    "Use SQLite syntax. Return only the SQL query."
)
user_msg = f"Schema:\n{schema}\n\nQuestion: {question}\n\nSQL:"

# 4. Connect via OpenRouter's OpenAI-compatible API
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise RuntimeError("Missing OPENROUTER_API_KEY in .env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# 5. Send it and print what comes back
response = client.chat.completions.create(
    model=MODEL,
    temperature=0,
    max_tokens=300,
    messages=[
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ],
)

raw_sql = response.choices[0].message.content

print("=" * 60)
print("QUESTION:", question)
print("=" * 60)
print("RAW MODEL OUTPUT:")
print(raw_sql)
print("=" * 60)

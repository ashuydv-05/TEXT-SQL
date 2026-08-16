"""
Free OpenRouter models for the Text-to-SQL eval.
Kept as a list of (display_name, slug) so output tables show friendly names.

Checked against OpenRouter's models API on 2026-08-12.
"""

# Recommended subset for Text-to-SQL generation.
#
# These are the free models that actually produced usable SQL in the local
# 20-question eval. The broader ALL_FREE_MODELS list below includes models
# that are free but performed poorly or failed generation in this task.
MODELS = [
    ("NVIDIA Nemotron 3 Ultra Free", "nvidia/nemotron-3-ultra-550b-a55b:free"),
    ("OpenAI gpt-oss 20B Free", "openai/gpt-oss-20b:free"),
    ("Qwen3 Coder", "qwen/qwen3-coder"),
    ("Claude Sonnet 4.5", "anthropic/claude-sonnet-4.5"),
    ("GPT-5.1", "openai/gpt-5.1"),
]

# All currently free text-output OpenRouter options I found. Some are less
# useful for Text-to-SQL evals, but this gives you a complete reference list.
ALL_FREE_MODELS = [
    ("LiquidAI LFM2.5 2.6B",             "liquid/lfm-2.5-2.6b:free"),
    ("NVIDIA Nemotron 3.5 Lightning",    "nvidia/nemotron-3.5-lightning:free"),
    ("inclusionAI Ling 3.0 Tiny",        "inclusionai/ling-3.0-tiny:free"),
    ("Poolside Laguna S 2.1",            "poolside/laguna-s-2.1:free"),
    ("Poolside Laguna XS 2.1",           "poolside/laguna-xs-2.1:free"),
    ("Cohere North Mini Code",           "cohere/north-mini-code:free"),
    ("NVIDIA Nemotron 3.5 Content Safety","nvidia/nemotron-3.5-content-safety:free"),
    ("NVIDIA Nemotron 3 Ultra",          "nvidia/nemotron-3-ultra-550b-a55b:free"),
    ("NVIDIA Nemotron 3 Nano Omni",      "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"),
    ("Google Gemma 4 26B A4B",           "google/gemma-4-26b-a4b-it:free"),
    ("Google Gemma 4 31B",               "google/gemma-4-31b-it:free"),
    ("NVIDIA Nemotron 3 Super",          "nvidia/nemotron-3-super-120b-a12b:free"),
    ("OpenRouter Free Router",           "openrouter/free"),
    ("NVIDIA Nemotron 3 Nano 30B A3B",   "nvidia/nemotron-3-nano-30b-a3b:free"),
    ("NVIDIA Nemotron Nano 12B 2 VL",    "nvidia/nemotron-nano-12b-v2-vl:free"),
    ("NVIDIA Nemotron Nano 9B V2",       "nvidia/nemotron-nano-9b-v2:free"),
    ("OpenAI gpt-oss 20B",               "openai/gpt-oss-20b:free"),
]

if __name__ == "__main__":
    print(f"{len(MODELS)} models under test:")
    for name, slug in MODELS:
        print(f"  {name:18s} -> {slug}")

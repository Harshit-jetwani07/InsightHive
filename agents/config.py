"""Shared deterministic generation settings for reproducible routing."""

import os

from google.genai import types

# Pin a predictable, quota-efficient model instead of the moving `*-latest`
# alias. Deployments can override this without code changes.
MODEL_NAME = os.getenv("ADK_MODEL", "gemini-2.5-flash").strip()


def deterministic_config() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(temperature=0)

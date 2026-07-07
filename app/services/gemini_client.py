import asyncio
import logging
from typing import Any

import google.generativeai as genai

from app.core.db import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def generate_analysis(prompt: str) -> str | None:
    analysis, _ = await generate_analysis_with_usage(prompt)
    return analysis


async def generate_analysis_with_usage(prompt: str) -> tuple[str | None, dict[str, Any] | None]:
    if not settings.gemini_api_key or settings.gemini_api_key == "your-gemini-api-key":
        return None, None

    def _generate() -> tuple[str, dict[str, Any] | None]:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        response = model.generate_content(prompt)

        usage_metadata = getattr(response, "usage_metadata", None)
        usage = None
        if usage_metadata is not None:
            usage = {
                "input_tokens": getattr(usage_metadata, "prompt_token_count", None),
                "output_tokens": getattr(usage_metadata, "candidates_token_count", None),
                "total_tokens": getattr(usage_metadata, "total_token_count", None),
                "source": "api",
            }
            logger.info(
                "Gemini usage | input_tokens=%s output_tokens=%s total_tokens=%s",
                usage["input_tokens"],
                usage["output_tokens"],
                usage["total_tokens"],
            )

        return response.text or "", usage

    return await asyncio.to_thread(_generate)

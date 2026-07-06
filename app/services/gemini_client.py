import asyncio

import google.generativeai as genai

from app.core.db import settings


async def generate_analysis(prompt: str) -> str | None:
    if not settings.gemini_api_key or settings.gemini_api_key == "your-gemini-api-key":
        return None

    def _generate() -> str:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        response = model.generate_content(prompt)
        return response.text or ""

    return await asyncio.to_thread(_generate)

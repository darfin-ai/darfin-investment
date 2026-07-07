import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.gemini_client import generate_analysis_with_usage


class GeminiClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_analysis_with_usage_returns_usage_metadata(self) -> None:
        response = SimpleNamespace(
            text="분석 결과",
            usage_metadata=SimpleNamespace(
                prompt_token_count=10,
                candidates_token_count=4,
                total_token_count=14,
            ),
        )

        with patch("app.services.gemini_client.genai.configure"), patch(
            "app.services.gemini_client.genai.GenerativeModel"
        ) as model_cls, patch("app.services.gemini_client.settings") as settings:
            settings.gemini_api_key = "test-key"
            settings.gemini_model = "gemini-1.5-flash"
            model_cls.return_value.generate_content.return_value = response

            analysis, usage = await generate_analysis_with_usage("프롬프트")

        self.assertEqual(analysis, "분석 결과")
        self.assertEqual(
            usage,
            {
                "input_tokens": 10,
                "output_tokens": 4,
                "total_tokens": 14,
                "source": "api",
            },
        )

    async def test_generate_analysis_with_usage_returns_none_when_api_fails(self) -> None:
        with patch("app.services.gemini_client.genai.configure"), patch(
            "app.services.gemini_client.genai.GenerativeModel"
        ) as model_cls, patch("app.services.gemini_client.settings") as settings:
            settings.gemini_api_key = "test-key"
            settings.gemini_model = "gemini-1.5-flash"
            model_cls.return_value.generate_content.side_effect = RuntimeError("api failed")

            analysis, usage = await generate_analysis_with_usage("프롬프트")

        self.assertIsNone(analysis)
        self.assertIsNone(usage)


if __name__ == "__main__":
    unittest.main()

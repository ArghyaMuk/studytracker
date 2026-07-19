"""
LLM client for AI-powered quiz generation.

Implements a dual-provider fallback chain:
  1. Google Gemini (primary) – fast and high-quality but has quota limits.
  2. OpenRouter (fallback)  – aggregator that proxies many open models.

If neither provider has valid API keys configured, the client returns
mock/placeholder questions so the system remains functional for demos.
"""

import json
import logging
from abc import ABC, abstractmethod

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class QuizGeneratorInterface(ABC):
    """Abstract interface for quiz generation – swap providers without changing API."""

    @abstractmethod
    async def generate_mcq_questions(
        self,
        topic: str,
        context: str,
        count: int,
        difficulty: str,
    ) -> list[dict]:
        """Generate MCQ questions. Returns list of {question, options, correct_answer, difficulty}."""
        ...

    @abstractmethod
    async def generate_viva_questions(
        self,
        topic: str,
        context: str,
        count: int,
    ) -> list[dict]:
        """Generate viva Q&A. Returns list of {question, correct_answer}."""
        ...


class LLMClient(QuizGeneratorInterface):
    """Multi-provider LLM client with automatic failover.

    Provider priority:
      Gemini → OpenRouter → Mock (no-key fallback)

    Each provider is tried only if a valid API key is present. A key starting
    with "your-" is treated as an unconfigured placeholder.
    """

    def __init__(self):
        self.gemini_api_key = settings.gemini_api_key
        self.openrouter_api_key = settings.openrouter_api_key

    async def generate_mcq_questions(
        self,
        topic: str,
        context: str,
        count: int,
        difficulty: str,
    ) -> list[dict]:
        """Generate MCQ questions. Tries Gemini first, falls back to OpenRouter."""
        prompt = self._build_mcq_prompt(topic, context, count, difficulty)

        # ── Primary provider: Google Gemini ──
        if self.gemini_api_key and not self.gemini_api_key.startswith("your-"):
            try:
                result = await self._call_gemini(prompt)
                if result:
                    return result
            except Exception as e:
                error_msg = str(e)
                # 429 = rate limit; switch to fallback instead of raising
                if "429" in error_msg or "quota" in error_msg.lower():
                    logger.warning("Gemini quota exceeded, trying OpenRouter fallback...")
                else:
                    logger.error(f"Gemini error: {e}")

        # ── Fallback provider: OpenRouter ──
        if self.openrouter_api_key and not self.openrouter_api_key.startswith("your-"):
            try:
                result = await self._call_openrouter(prompt)
                if result:
                    logger.info("Quiz generated via OpenRouter fallback")
                    return result
            except Exception as e:
                logger.error(f"OpenRouter error: {e}")
                raise RuntimeError(
                    "Both Gemini and OpenRouter failed. "
                    "Please try again later or create questions manually."
                )

        # ── No valid keys: return placeholder questions for demo purposes ──
        if (not self.gemini_api_key or self.gemini_api_key.startswith("your-")) and \
           (not self.openrouter_api_key or self.openrouter_api_key.startswith("your-")):
            logger.info("No LLM API keys configured, using mock questions")
            return self._mock_mcq(topic, count, difficulty)

        raise RuntimeError(
            "Gemini AI quota exceeded and no OpenRouter fallback configured. "
            "Please try again later or ask admin to create a custom quiz."
        )

    async def generate_viva_questions(
        self,
        topic: str,
        context: str,
        count: int,
    ) -> list[dict]:
        """Generate viva-style Q&A. Same fallback chain as MCQ generation."""
        prompt = self._build_viva_prompt(topic, context, count)

        # ── Primary: Gemini ──
        if self.gemini_api_key and not self.gemini_api_key.startswith("your-"):
            try:
                result = await self._call_gemini(prompt)
                if result:
                    return result
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    logger.warning("Gemini quota exceeded, trying OpenRouter fallback...")
                else:
                    logger.error(f"Gemini error: {e}")

        # ── Fallback: OpenRouter ──
        if self.openrouter_api_key and not self.openrouter_api_key.startswith("your-"):
            try:
                result = await self._call_openrouter(prompt)
                if result:
                    logger.info("Viva generated via OpenRouter fallback")
                    return result
            except Exception as e:
                logger.error(f"OpenRouter error: {e}")
                raise RuntimeError(
                    "Both Gemini and OpenRouter failed. "
                    "Please try again later or create questions manually."
                )

        # ── No valid keys: mock fallback ──
        if (not self.gemini_api_key or self.gemini_api_key.startswith("your-")) and \
           (not self.openrouter_api_key or self.openrouter_api_key.startswith("your-")):
            logger.info("No LLM API keys configured, using mock questions")
            return self._mock_viva(topic, count)

        raise RuntimeError(
            "Gemini AI quota exceeded and no OpenRouter fallback configured. "
            "Please try again later or ask admin to create a custom quiz."
        )

    # ── Provider Implementations ──

    async def _call_gemini(self, prompt: str) -> list[dict] | None:
        """Call Google Gemini API.

        Uses run_in_executor because the google-generativeai SDK is synchronous.
        """
        import asyncio
        import google.generativeai as genai

        def _sync_call():
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            return response.text

        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, _sync_call)
        return self._parse_json_response(text)

    async def _call_openrouter(self, prompt: str) -> list[dict] | None:
        """Call OpenRouter API – a unified gateway to many open-source LLMs.

        Currently configured to use Llama 3.1 8B Instruct for cost efficiency.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:3000",  # Required by OpenRouter TOS
                    "X-Title": "StudyPilot",
                },
                json={
                    "model": "meta-llama/llama-3.1-8b-instruct",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    "temperature": 0.7,  # Moderate creativity for diverse questions
                },
            )

            if response.status_code != 200:
                raise RuntimeError(f"OpenRouter API error: {response.status_code} {response.text}")

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return self._parse_json_response(content)

    # ── Prompt Builders ──

    def _build_mcq_prompt(self, topic: str, context: str, count: int, difficulty: str) -> str:
        """Construct the MCQ generation prompt with strict JSON output format."""
        return f"""Generate {count} multiple-choice questions on the topic: {topic}
Difficulty level: {difficulty}
Context/syllabus: {context}

Return a JSON array where each element has:
- "question": the question text
- "options": array of 4 options (A, B, C, D)
- "correct_answer": the correct option letter (A, B, C, or D)
- "difficulty": "{difficulty}"

Return ONLY the JSON array, no other text or markdown formatting."""

    def _build_viva_prompt(self, topic: str, context: str, count: int) -> str:
        """Construct the viva question prompt expecting concise answer outlines."""
        return f"""Generate {count} viva/oral examination questions on: {topic}
Context: {context}

Return a JSON array where each element has:
- "question": the viva question
- "correct_answer": expected answer outline (50-200 words)

Return ONLY the JSON array, no other text or markdown formatting."""

    def _parse_json_response(self, text: str) -> list[dict] | None:
        """Parse JSON from LLM response, stripping markdown code fences if present."""
        text = text.strip()
        # LLMs often wrap JSON in ```json ... ``` blocks – strip those
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3].strip()
        try:
            result = json.loads(text)
            if isinstance(result, list) and len(result) > 0:
                return result
        except (json.JSONDecodeError, ValueError):
            logger.error(f"Failed to parse LLM JSON response: {text[:200]}")
        return None

    # ── Mock Fallbacks (no-key mode) ──

    def _mock_mcq(self, topic: str, count: int, difficulty: str) -> list[dict]:
        """Generate placeholder MCQ data when no LLM API keys are configured."""
        return [
            {
                "question": f"[No API key] {difficulty.title()} question {i+1} about {topic}",
                "options": [
                    f"Option A for Q{i+1}",
                    f"Option B for Q{i+1}",
                    f"Option C for Q{i+1}",
                    f"Option D for Q{i+1}",
                ],
                "correct_answer": "A",
                "difficulty": difficulty,
            }
            for i in range(count)
        ]

    def _mock_viva(self, topic: str, count: int) -> list[dict]:
        """Generate placeholder viva data when no LLM API keys are configured."""
        return [
            {
                "question": f"[No API key] Explain concept {i+1} related to {topic}",
                "correct_answer": f"Write the expected answer for concept {i+1} in {topic} here.",
            }
            for i in range(count)
        ]

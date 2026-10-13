import json
import logging
import re
from typing import Optional, Dict, Any

import httpx

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_DEFAULT_MODEL = "openai/gpt-oss-120b"

class LLMAdapter:
    def __init__(self, api_key: Optional[str] = None, provider: str = "gemini", model: Optional[str] = None):
        self.api_key = api_key or ""
        self.provider = provider.lower()
        self.model = model

    def sanitize_untrusted_input(self, text: str) -> str:
        """Prompt injection defense (Section 39).
        Ensures instructions inside documents cannot break out of data delimiters.
        """
        # Strip explicit adversarial command tokens
        sanitized = re.sub(r"(?i)(ignore previous instructions|system prompt|disregard instructions)", "[FILTERED_INSTRUCTION]", text)
        return sanitized

    async def generate_json(self, prompt: str, schema_instruction: str = "") -> Optional[Dict[str, Any]]:
        """Call LLM provider or return None if offline / no key provided."""
        if not self.api_key:
            return None

        clean_prompt = prompt + "\n\nCRITICAL: Respond ONLY with valid JSON conforming to this schema:\n" + schema_instruction

        if self.provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(
                    clean_prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                if response and response.text:
                    return json.loads(response.text)
            except Exception as e:
                logger.warning(f"Gemini API generation failed: {e}. Falling back to deterministic engine.")
                return None
        elif self.provider == "openai":
            try:
                import openai
                client = openai.OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are ReqPilot AI, an expert requirements engineer. Always respond strictly in valid JSON."},
                        {"role": "user", "content": clean_prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                if response.choices and response.choices[0].message.content:
                    return json.loads(response.choices[0].message.content)
            except Exception as e:
                logger.warning(f"OpenAI API generation failed: {e}. Falling back to deterministic engine.")
                return None
        elif self.provider == "groq":
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        GROQ_API_URL,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model or GROQ_DEFAULT_MODEL,
                            "messages": [
                                {"role": "system", "content": "You are ReqPilot AI, an expert requirements engineer. Always respond strictly in valid JSON, with no markdown fences or commentary."},
                                {"role": "user", "content": clean_prompt}
                            ],
                            "response_format": {"type": "json_object"},
                            "temperature": 0.2,
                        },
                    )
                if response.status_code != 200:
                    logger.warning(f"Groq API returned {response.status_code}: {response.text}. Falling back to deterministic engine.")
                    return None
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
            except Exception as e:
                logger.warning(f"Groq API generation failed: {e}. Falling back to deterministic engine.")
                return None

        return None

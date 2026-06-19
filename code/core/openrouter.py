import os
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
async def call_model(model: str, messages: list[dict], temperature: float = 0.1) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            BASE_URL,
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
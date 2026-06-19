import json
import os
import asyncio

import httpx


async def call_model(model: str, messages: list, temperature: float = 0.1,
                     max_retries: int = 3, json_response: bool = True) -> str:
    """
    Call an OpenRouter LLM.

    Args:
        model:        OpenRouter model identifier.
        messages:     Chat messages (text-only or multimodal).
        temperature:  Sampling temperature.
        max_retries:  Exponential back-off retry count.
        json_response: Set response_format=json_object.
                       Set False for multimodal calls where the model may not
                       support the response_format parameter.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if json_response:
        payload["response_format"] = {"type": "json_object"}

    last_error = None
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
    raise last_error

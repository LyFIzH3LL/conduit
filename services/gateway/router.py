import hashlib
import os
import re
import httpx
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(title="Conduit Inference Gateway")
cache = redis.from_url("redis://redis:6379", decode_responses=True)

LLM_API_URL = os.getenv("LLM_API_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")


PII_PATTERNS = [
    (re.compile(r"\b[\w.-]+@[\w.-]+\.\w+\b"), "[EMAIL_REDACTED]"),

    (
        re.compile(
            r"(?:\+880|880|0)1[3-9]\d{2}[-.\s]?\d{6}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
        ),
        "[PHONE REDACTED]"
    )
]


class CompletionRequest(BaseModel):
    prompt: str
    model: str = "llama-3.1-8b-instant"
    use_cache: bool = True


def scrub_pii(text: str) -> str:
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


@app.post("/v1/generate")
async def generate(req: CompletionRequest):
    clean_prompt = scrub_pii(req.prompt)
    cache_key = f"llm:{req.model}:{hashlib.sha256(clean_prompt.encode()).hexdigest()}"

    if req.use_cache and (cached := await cache.get(cache_key)):
        return {"text": cached, "source": "cache"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(
            LLM_API_URL,
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            json={
                "model": req.model,
                "messages": [{"role": "user", "content": clean_prompt}]
            }
        )

    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code, detail=res.text)
    output = res.json()["choices"][0]["message"]["content"]

    if req.use_cache:
        await cache.setex(cache_key, 3600, output)

    return {"text": output, "source": "cloud"}

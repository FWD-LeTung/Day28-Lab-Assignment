# api-gateway/main.py
from fastapi import FastAPI, Request, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
import httpx, os, time

app = FastAPI(title="AI Platform API Gateway")
Instrumentator().instrument(app).expose(app)  # Integration 9: Prometheus

VLLM_URL = os.environ["VLLM_URL"]
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")

@app.post("/api/v1/chat")
async def chat(request: Request):
    body = await request.json()

    if "query" not in body:
        raise HTTPException(status_code=422, detail="Missing required field: query")

    query = body["query"]
    start = time.time()

    # 1. Vector search
    async with httpx.AsyncClient() as client:
        search_resp = await client.post(f"{QDRANT_URL}/collections/documents/points/search", json={
            "vector": body.get("embedding", [0.0] * 384),
            "limit": 3
        })
        context = search_resp.json().get("result", [])

    # 2. LLM inference with fallback
    prompt = f"Context: {context}\n\nQuery: {query}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            llm_resp = await client.post(f"{VLLM_URL}/v1/chat/completions", json={
                "model": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
                "messages": [{"role": "user", "content": prompt}]
            })

        if llm_resp.status_code != 200:
            return {
                "answer": f"Mock response for: {query}. LLM service unavailable.",
                "latency_ms": round((time.time() - start) * 1000, 2),
                "model": "mock"
            }
        result = llm_resp.json()
        answer = result["choices"][0]["message"]["content"]
        model = result["model"]
    except Exception as e:
        answer = f"Mock response for: {query}. LLM service error: {str(e)}"
        model = "mock"

    latency = (time.time() - start) * 1000

    return {
        "answer": answer,
        "latency_ms": round(latency, 2),
        "model": model
    }

@app.get("/health")
def health():
    return {"status": "ok"}

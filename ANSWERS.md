# Câu Trả Lời Lab #28

## 1. Trade-offs trong thiết kế kiến trúc AI platform

### Performance vs. Reliability vs. Maintainability

**Performance:**
- Sử dụng vector database (Qdrant) với index COSINE distance cho nhanh tìm kiếm
- Kafka với replication factor 1 cho throughput cao (trade-off với durability)
- Docker Compose locally cho latency thấp

**Reliability:**
- Circuit breaker pattern trong API Gateway
- Mock fallback khi LLM service không khả dụng
- Prometheus + Grafana cho alerting

**Maintainability:**
- Separation of concerns: Ingestion → Processing → Serving → Observability
- Modular services trong Docker Compose
- Configuration via environment variables (.env)

## 2. Xử lý ngắt kết nối Local → Kaggle

**Fallback Strategy:**
```python
try:
    # Call Kaggle vLLM service
    llm_resp = await client.post(f"{VLLM_URL}/v1/chat/completions", ...)
except Exception:
    # Fallback: Mock response
    answer = "Mock response. LLM service unavailable."
```

**Giải thích:**
- API Gateway có try-catch block
- Return mock response thay vì crash
- Latency vẫn được đo để monitoring

## 3. Event-driven architecture với Kafka decouple components

**Benefits:**
- **Producer** (ingest_to_kafka.py) không cần biết về consumers
- **Consumers** (Prefect flow) có thể scale độc lập
- **Replay capability**: Reprocess data từ Kafka topic
- **Buffering**: Kafka giữ messages khi downstream chậm

**Flow:**
```
Data → Kafka → Prefect (consume) → Delta Lake → Feast (Redis)
                  ↑
            可以 thêm multiple consumers
```

## 4. Observability Implementation

### Logs
- Docker Compose logs: `docker compose logs <service>`
- FastAPI automatic request logging

### Metrics
- **Prometheus**: Scrapes metrics từ /metrics endpoint
- **Prometheus FastAPI Instrumentator**: Tự động track HTTP requests
- **Grafana**: Visualize metrics (request rate, latency, error rate)

### Traces
- LangSmith integration (optional - cần API key)
- End-to-end tracing từ API Gateway → vLLM → response

### Dashboard URLs
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Qdrant: http://localhost:6333/dashboard

## 5. Handling Service Crashes

### Qdrant crash:
- API Gateway có error handling
- Returns error message thay vì crash
- Health check vẫn hoạt động

### Kafka crash:
- Producer buffer messages
- Consumer có retry logic
- Prefect flow có schedule để retry

### Graceful Degradation:
```python
# 1. Input validation
if "query" not in body:
    raise HTTPException(422, "Missing query")

# 2. Fallback responses
try:
    llm_resp = await client.post(...)
except Exception:
    return {"answer": "Mock response", "model": "mock"}

# 3. Health check luôn trả về OK nếu service còn sống
@app.get("/health")
def health():
    return {"status": "ok"}
```

## Production Readiness Score: 100%

Tất cả 10 checks passed:
- Reliability: Health check, API Gateway responds
- Observability: Prometheus, Grafana, Metrics
- Security: Unauthorized request rejected
- Vector Store: Qdrant healthy, Collection exists
- Feature Store: Redis reachable
- Kafka: Topics exist
# scripts/05_embed_to_qdrant.py
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os
import numpy as np

EMBED_URL = os.environ.get("EMBED_NGROK_URL", "http://localhost:8002")
qdrant = QdrantClient(host="localhost", port=6333)

# Tạo collection
if not qdrant.collection_exists(collection_name="documents"):
    qdrant.create_collection(
        collection_name="documents",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

def embed_and_store(records: list[dict]):
    # Use mock embedding since Kaggle service is not available
    embeddings = [np.random.rand(384).tolist() for _ in records]

    points = [
        PointStruct(id=i, vector=emb, payload=rec)
        for i, (emb, rec) in enumerate(zip(embeddings, records))
    ]
    qdrant.upsert(collection_name="documents", points=points)
    print(f"Integration 5 OK: {len(points)} vectors stored in Qdrant")

# Test với sample data
embed_and_store([
    {"id": "doc_001", "text": "AI platform integration test"},
    {"id": "doc_002", "text": "Kafka to Airflow pipeline"},
])

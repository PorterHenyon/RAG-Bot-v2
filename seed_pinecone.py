import os
import requests
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

api_url = os.environ["DATA_API_URL"]
index_name = os.environ["PINECONE_INDEX_NAME"]

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index(index_name)
model = SentenceTransformer("all-MiniLM-L6-v2")

data = requests.get(api_url, timeout=15).json()
vectors = []
for entry in data.get("ragEntries", []):
    eid = entry.get("id")
    if not eid:
        continue
    text = f"{entry.get('title','')}\n{' '.join(entry.get('keywords', []))}\n{entry.get('content','')[:500]}"
    vec = model.encode(text).tolist()
    vectors.append({
        "id": eid,
        "values": vec,
        "metadata": {
            "title": entry.get("title","")[:1000],
            "content": entry.get("content","")[:1000],
            "keywords": " ".join(entry.get("keywords", []))[:500],
            "entry_id": eid
        }
    })

for i in range(0, len(vectors), 100):
    index.upsert(vectors=vectors[i:i+100])

print(f"Upserted {len(vectors)} vectors to Pinecone")
print("Stats:", index.describe_index_stats())


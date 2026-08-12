import os
import chromadb
from chromadb.utils import embedding_functions

# 1. Resolve paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

db_path = os.path.join(script_dir, "ziad_chroma_db")
if not os.path.exists(db_path):
    db_path = os.path.join(project_root, "ziad_chroma_db")

# 2. Load Embedding Function
arabic_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# 3. Connect to ChromaDB
client = chromadb.PersistentClient(path=db_path)
collection = client.get_collection(
    name="ziad_rahbani_archive",
    embedding_function=arabic_ef
)

# 4. User Question
query_text = "ما هي أبرز المحطات الفنية لزياد الرحباني؟"

# 5. Perform Vector Search (Retrieve top 3 relevant chunks)
results = collection.query(
    query_texts=[query_text],
    n_results=3
)

# 6. Display Retrieved Chunks
print(f"--- Question: {query_text} ---\n")
for i, doc in enumerate(results["documents"][0]):
    meta = results["metadatas"][0][i]
    print(f"Result {i+1}:")
    print(f"Content: {doc}")
    print(f"Source: {meta.get('file_source', 'Unknown')}")
    print("-" * 50)
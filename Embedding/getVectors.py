import os
import chromadb
from chromadb.utils import embedding_functions

# 1. Resolve database path (checks both Embedding folder and project root)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

db_path = os.path.join(script_dir, "ziad_chroma_db")
if not os.path.exists(db_path):
    db_path = os.path.join(project_root, "ziad_chroma_db")

# 2. Load the Arabic Embedding Model
arabic_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# 3. Connect to ChromaDB with the embedding function
client = chromadb.PersistentClient(path=db_path)
collection = client.get_collection(
    name="ziad_rahbani_archive",
    embedding_function=arabic_ef
)

# 4. Retrieve the first chunk with its embeddings
data = collection.get(limit=1, include=["embeddings", "documents", "metadatas"])

# 5. Print results
print("--- Original Document ---")
print(data["documents"][0])

print("\n--- Vector Representation (First 10 values out of 384) ---")
print(data["embeddings"][0][:10])

print("\n--- Vector Dimensions ---")
print(len(data["embeddings"][0]))
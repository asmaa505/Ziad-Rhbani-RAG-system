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

# 4. Main Search Function
def search_chroma(query_text: str, top_k: int = 3):
    """
    Takes a query string, searches ChromaDB for relevant chunks,
    and returns a list of document strings.
    """
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k
    )
    # Return only the list of retrieved text documents
    return results["documents"][0]

# 5. Local Script Testing
if __name__ == "__main__":
    test_query = "ما هي أبرز المحطات الفنية لزياد الرحباني؟"
    retrieved_docs = search_chroma(test_query, top_k=3)
    
    print(f"--- Question: {test_query} ---\n")
    for i, doc in enumerate(retrieved_docs, 1):
        print(f"Result {i}:")
        print(doc)
        print("-" * 30)
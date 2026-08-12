import os
import json
import chromadb
from chromadb.utils import embedding_functions

# 1. Define folder paths automatically
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
chunking_dir = os.path.join(project_root, "chunking")
db_path = os.path.join(project_root, "ziad_chroma_db")

# 2. Load the Arabic Embedding Model
arabic_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# 3. Initialize or connect to ChromaDB
client = chromadb.PersistentClient(path=db_path)
collection = client.get_or_create_collection(
    name="ziad_rahbani_archive",
    embedding_function=arabic_ef
)

documents = []
metadatas = []
ids = []
global_counter = 1

# 4. Iterate through all JSON files and extract all chunks
if os.path.exists(chunking_dir):
    for filename in os.listdir(chunking_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(chunking_dir, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Handle both List and Dict structures
                items = data if isinstance(data, list) else [data]
                
                for item in items:
                    if isinstance(item, dict):
                        # Extract text regardless of key naming
                        text = item.get("text") or item.get("content") or item.get("chunk") or str(item)
                        meta = item.get("metadata", {})
                        if not isinstance(meta, dict):
                            meta = {"info": str(meta)}
                        meta["file_source"] = filename
                    else:
                        text = str(item)
                        meta = {"file_source": filename}
                    
                    documents.append(text)
                    metadatas.append(meta)
                    ids.append(f"chunk_{global_counter}")
                    global_counter += 1

    # 5. Upload all chunks to ChromaDB at once
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Successfully processed and uploaded all chunks! Total: {len(documents)} chunks.")
    else:
        print("No text data found inside the JSON files.")
else:
    print(f"Directory not found: {chunking_dir}")
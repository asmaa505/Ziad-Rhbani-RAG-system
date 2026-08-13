import os
import sys
from dotenv import load_dotenv
from google import genai

# 1. Path Setup: Allow Python to import modules from the project root directory
current_dir = os.path.dirname(os.path.abspath(__file__))  # RAG Generation folder
project_root = os.path.dirname(current_dir)                 # Root (RAG) folder

if project_root not in sys.path:
    sys.path.append(project_root)

# 2. Import search function from Embedding/query.py
from Embedding.query import search_chroma

# 3. Load environment variables from .env file inside RAG Generation folder
env_path = os.path.join(current_dir, ".env")
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(f"GEMINI_API_KEY not found in {env_path}! Please check your .env file.")

# 4. Initialize Gemini Client
client = genai.Client(api_key=api_key)

def generate_answer(user_query: str):
    # Retrieve relevant context chunks from ChromaDB
    context_chunks = search_chroma(user_query, top_k=3)
    context_text = "\n\n---\n\n".join(context_chunks)

    # Construct the RAG Prompt
    prompt = f"""
You are an expert assistant specialized in Ziad Rahbani's archive and work.
Use ONLY the following provided context to answer the user's question accurately, concisely, and naturally in Arabic.
If the answer is not contained in the context, state clearly that the information is not available in the archive.

Context:
{context_text}

Question:
{user_query}

Answer:
"""

    # Generate content using Gemini model
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text

# --- Execution & Testing ---
if __name__ == "__main__":
    test_question = "ما هي أبرز المحطات الفنية لزياد الرحباني؟"
    print(f" Question: {test_question}\n")
    print(" Searching database and generating response with Gemini...\n")
    
    answer = generate_answer(test_question)
    
    print("🤖 Gemini RAG Answer:")
    print("=" * 50)
    print(answer)
    print("=" * 50)
import truststore
truststore.inject_into_ssl()

import os
import sys
import time
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

# 4. Initialize Gemini Client with standard 30s timeout
client = genai.Client(api_key=api_key, http_options={"timeout": 30000})

def get_fallback_response(user_query: str, context_text: str, error_msg: str) -> str:
    """
    Generates a high-quality custom fallback response using the local context retrieved from ChromaDB
    when the Gemini API is unavailable (503), rate-limited (429), or fails.
    """
    fallback_header = (
        "⚠️ **ملاحظة:** يواجه نظام التوليد الذكي حالياً ضغطاً كبيراً أو عطلاً مؤقتاً في الاتصال بخادم Gemini. "
        "حرصاً على تقديم الخدمة، تم استرجاع المعلومات التالية مباشرة من قاعدة البيانات الأرشيفية المحلية ذات الصلة بسؤالك:\n\n"
    )
    
    if not context_text.strip():
        return (
            fallback_header +
            "عذراً، لم نتمكن من الاتصال بالنموذج الذكي لتوليد إجابة مخصصة، "
            "ولم نتمكن من العثور على نصوص كافية في الأرشيف المحلي للإجابة على سؤالك مباشرة."
        )
    
    # Extract relevant retrieved text chunks and format them nicely
    formatted_context = "### نصوص مسترجعة مباشرة من أرشيف زياد رحباني:\n"
    chunks = context_text.split("\n\n---\n\n")
    for idx, chunk in enumerate(chunks, 1):
        if chunk.strip():
            formatted_context += f"- **المرجع {idx}:** {chunk.strip()}\n\n"
        
    return fallback_header + formatted_context

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

    # Robust Retry Logic (Exponential Backoff) & Handling 429/503 states
    max_retries = 3
    base_delay = 2.0  # seconds (delay increases to 4.0s, then 8.0s)
    
    for attempt in range(max_retries):
        try:
            # Generate content using Gemini model
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            # Detect retryable server errors (503 Service Unavailable, 429 Rate Limit/Quota Exceeded, or connection timeouts)
            is_retryable = (
                "503" in error_msg or 
                "429" in error_msg or 
                "rate limit" in error_msg.lower() or 
                "unavailable" in error_msg.lower() or 
                "timeout" in error_msg.lower()
            )
            
            if is_retryable and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"[RAG Generation] Gemini API connection issue: {error_msg}. Retrying in {delay}s (Attempt {attempt+1}/{max_retries})...")
                time.sleep(delay)
            else:
                # Retries exhausted or non-retryable critical API failure
                print(f"[RAG Generation ERROR] Terminal Gemini API failure after {attempt+1} attempt(s): {error_msg}")
                # Seamless user experience fallback to local vector database chunks
                return get_fallback_response(user_query, context_text, error_msg)

# --- Execution & Testing ---
if __name__ == "__main__":
    test_question = "ما هي أبرز المحطات الفنية لزياد الرحباني؟"
    print(f" Question: {test_question}\n")
    print(" Searching database and generating response with Gemini...\n")
    
    answer = generate_answer(test_question)
    
    print(" Gemini RAG Answer:")
    print("=" * 50)
    print(answer)
    print("=" * 50)
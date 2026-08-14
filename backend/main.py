import os
import sys
import importlib.util
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

# 1. Path Setup: Load the RAG Generation/generate.py module dynamically
# This approach handles folder names with spaces gracefully
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # backend folder
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)               # Root (RAG) folder

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

RAG_SCRIPT_PATH = os.path.join(PROJECT_ROOT, "RAG Generation", "generate.py")

if not os.path.exists(RAG_SCRIPT_PATH):
    raise FileNotFoundError(f"RAG script not found at {RAG_SCRIPT_PATH}!")

# Load generate.py dynamically
spec = importlib.util.spec_from_file_location("generate", RAG_SCRIPT_PATH)
generate_module = importlib.util.module_from_spec(spec)
sys.modules["generate"] = generate_module
spec.loader.exec_module(generate_module)

# Retrieve the generate_answer function
generate_answer = generate_module.generate_answer

# 2. FastAPI Application Setup
app = FastAPI(
    title="Ziad Rahbani Archive RAG API",
    description="Backend API server for retrieving and generating answers from Ziad Rahbani's archive",
    version="1.0.0"
)

# 3. Enable CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Request & Response Schemas
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    status: str

# 5. API Endpoint for RAG Queries
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="السؤال لا يمكن أن يكون فارغاً.")

    print(f"[API Server] Received query: {question}")
    
    try:
        # Call the RAG generation pipeline
        answer = generate_answer(question)
        print(f"[API Server] Generated response successfully.")
        return ChatResponse(answer=answer, status="success")
    except Exception as e:
        print(f"[API Server ERROR] Failed to generate answer: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"حدث خطأ أثناء معالجة السؤال وتوليد الإجابة: {str(e)}"
        )

# 6. Serve static Frontend files
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    
    # Redirect root URL to static index.html
    @app.get("/")
    async def redirect_to_frontend():
        return RedirectResponse(url="/static/index.html")
else:
    print(f"[Warning] Frontend directory not found at {FRONTEND_DIR}. API will run without static page hosting.")

# 7. Server Execution Entry Point
if __name__ == "__main__":
    import uvicorn
    # Run server on port 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

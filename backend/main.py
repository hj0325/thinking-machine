from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from .models import AnalysisRequest, AnalysisResponse
from .logic import ThinkingAgent

app = FastAPI()

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agent
# Ensure OPENAI_API_KEY is set in environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("WARNING: OPENAI_API_KEY not found in environment variables.")

agent = ThinkingAgent(api_key=api_key)

@app.get("/")
def read_root():
    return {"message": "Visual Thinking Machine Backend is running"}

@app.post("/analyze", response_model=AnalysisResponse)
def analyze_endpoint(request: AnalysisRequest):
    try:
        if not api_key:
             raise HTTPException(status_code=500, detail="OpenAI API Key is missing on server.")
        
        result = agent.process_idea(request.text, request.history)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from .models import AnalysisRequest, AnalysisResponse, ChatRequest, ChatResponse, ChatToNodesRequest
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


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API Key is missing on server.")
        reply = agent.chat_with_suggestion(
            suggestion_title=request.suggestion_title,
            suggestion_content=request.suggestion_content,
            suggestion_category=request.suggestion_category,
            suggestion_phase=request.suggestion_phase,
            messages=request.messages,
            user_message=request.user_message,
        )
        return ChatResponse(reply=reply)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat-to-nodes", response_model=AnalysisResponse)
def chat_to_nodes_endpoint(request: ChatToNodesRequest):
    try:
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API Key is missing on server.")
        result = agent.chat_to_nodes(
            suggestion_title=request.suggestion_title,
            suggestion_content=request.suggestion_content,
            suggestion_category=request.suggestion_category,
            suggestion_phase=request.suggestion_phase,
            messages=request.messages,
            existing_nodes=request.existing_nodes,
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


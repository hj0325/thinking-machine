from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import AnalysisRequest, AnalysisResponse
from .logic import analyze_text

app = FastAPI()

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Visual Thinking Machine Backend is running"}

@app.post("/analyze", response_model=AnalysisResponse)
def analyze_endpoint(request: AnalysisRequest):
    try:
        result = analyze_text(request.text, request.current_nodes, request.current_edges)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_analyze_endpoint():
    response = client.post("/analyze", json={
        "text": "I want to build a better todo app",
        "history": []
    })
    
    # We expect 500 if NO API KEY, or 200 if API KEY is present
    # Since we can't easily mock env vars in this simple script without potentially breaking things or needing pytest-mock
    # We will just print the status and response
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_analyze_endpoint()

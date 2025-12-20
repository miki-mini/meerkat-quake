import uvicorn
from app.main import app

# This allows running with: uvicorn main:app --reload
# Or simply: python main.py

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
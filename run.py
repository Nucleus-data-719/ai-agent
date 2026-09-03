import uvicorn
import os
import sys
from pathlib import Path

# Add the backend folder to Python's import path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Change to backend directory so relative paths work
os.chdir(backend_path)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
import os
import sys
import subprocess
import time
from loguru import logger
from dotenv import load_dotenv

def check_environment():
    load_dotenv()
    if not os.getenv("GEMINI_API_KEYS") and not os.getenv("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEYS is not set in .env")
        sys.exit(1)
        
    # Check for required directories
    os.makedirs("./data/corpus/speeches", exist_ok=True)
    os.makedirs("./data/corpus/papers", exist_ok=True)
    os.makedirs("./data/corpus/interviews", exist_ok=True)
    os.makedirs("./data/corpus/institutional", exist_ok=True)
    os.makedirs("./chroma_db", exist_ok=True)

def start_backend():
    logger.info("Starting FastAPI backend on port 8000...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    return backend

def run_system():
    check_environment()
    
    backend_proc = None

    
    try:
        backend_proc = start_backend()

        
        # Wait for both processes
        logger.info("System is running. Press Ctrl+C to stop.")
        logger.info("Backend: http://localhost:8000")

        logger.info("Health: http://localhost:8000/health")
        backend_proc.wait()

        
    except KeyboardInterrupt:
        logger.info("Shutting down system...")
    finally:
        if backend_proc:
            backend_proc.terminate()

            
if __name__ == "__main__":
    run_system()

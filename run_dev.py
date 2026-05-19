import subprocess
import sys
import os
import time
import signal

def run_dev():
    print("--- Starting Bible-RAG Development Environment ---")
    
    # 1. Start Backend
    print("Launching Backend (FastAPI)...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload"],
        stdout=None,
        stderr=None
    )
    
    # 2. Start Frontend
    print("Launching Frontend (Vite)...")
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=os.path.join(os.getcwd(), "frontend"),
        stdout=None,
        stderr=None
    )
    
    print("\n" + "="*50)
    print("SYSTEMS RUNNING")
    print("Backend: http://localhost:8000")
    print("Frontend: http://localhost:5173")
    print("="*50)
    print("\nPress Ctrl+C to stop both servers safely.\n")

    try:
        # Keep the script running while processes are alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping servers...")
        # Send termination signal to both processes
        backend_process.terminate()
        frontend_process.terminate()
        
        # Wait for them to close
        backend_process.wait()
        frontend_process.wait()
        print("Done. Goodbye!")

if __name__ == "__main__":
    run_dev()

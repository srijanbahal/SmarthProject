#!/usr/bin/env python3
"""
Project Samarth - Startup Script
This script helps you get the system running quickly
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed"""
    try:
        import fastapi
        import streamlit
        import groq
        import pandas
        import sqlalchemy
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists and has GROQ key"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("Please create a .env file with your GROQ_API_KEY")
        return False
    
    with open(env_file) as f:
        content = f.read()
        
    if "GROQ_API_KEY=" not in content or "your_" in content:
        print("❌ GROQ_API_KEY not found or not set in .env")
        return False
    
    print("✅ Environment variables configured")
    return True

# --- NEW FUNCTION ---
def check_database_exists():
    """Check if the database file was created by seed_data.py"""
    db_file = Path("project_samarth.db")
    if not db_file.exists():
        print(f"❌ Database not found: {db_file.resolve()}")
        print("This file should be in your main project folder.")
        print("Please re-run: python seed_data.py (as Administrator)")
        return False
    
    print("✅ Database file found.")
    return True

def start_backend():
    """Start the FastAPI backend"""
    print("\n🚀 Starting FastAPI backend...")
    try:
        # Change to backend directory
        os.chdir("backend")
        
        # Start the server
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"
        ])
        
        print("✅ FastAPI backend started on http://localhost:8000")
        print("📚 API docs available at http://localhost:8000/docs")
        return process
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return None

def start_frontend():
    """Start the Streamlit frontend"""
    print("\n🎨 Starting Streamlit frontend...")
    try:
        # Change to frontend directory
        os.chdir("../frontend")
        
        # Start Streamlit
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app.py", "--server.port", "8501"
        ])
        
        print("✅ Streamlit frontend started on http://localhost:8501")
        return process
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        return None

def main():
    """Main startup function"""
    print("🌾 Project Samarth - Startup Script")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        return
    
    # Check environment
    if not check_env_file():
        return
    
    # --- MODIFIED: Check for DB, don't create it ---
    if not check_database_exists():
        return
    
    # --- REMOVED: Redundant seed_sample_data() call ---
    
    print("\n🎯 Starting Project Samarth...")
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        return
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        return
    
    print("\n🎉 Project Samarth is now running!")
    print("\n📱 Access Points:")
    print("   Frontend: http://localhost:8501")
    print("   API Docs: http://localhost:8000/docs")
    print("   Health Check: http://localhost:8000/api/health")
    
    print("\n🛑 To stop the system:")
    print("   Press Ctrl+C in this terminal")
    
    try:
        # Wait for processes
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping Project Samarth...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ System stopped")

if __name__ == "__main__":
    main()
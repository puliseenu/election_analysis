#!/usr/bin/env python
"""
PUBLIC ACCESS LAUNCHER
Starts dashboard and creates public ngrok URL for external access
"""
import subprocess
import sys
import time
import os
from pathlib import Path

def get_python():
    """Get virtual environment Python executable"""
    venv_python = Path(".venv/Scripts/python.exe" if os.name == 'nt' 
                       else ".venv/bin/python")
    return str(venv_python) if venv_python.exists() else sys.executable

def start_app():
    """Start the main dashboard app"""
    print("\n" + "=" * 70)
    print("  STARTING ELECTION ANALYTICS DASHBOARD")
    print("=" * 70)
    
    app_process = subprocess.Popen(
        [get_python(), 'app.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print(f"  Dashboard started (PID: {app_process.pid})")
    print("  Waiting for server to initialize...")
    time.sleep(3)
    
    return app_process

def start_ngrok():
    """Start ngrok tunnel for public access"""
    try:
        print("\n" + "=" * 70)
        print("  CONFIGURING PUBLIC ACCESS (NGROK)")
        print("=" * 70)
        
        # Start ngrok
        ngrok_process = subprocess.Popen(
            ['ngrok', 'http', '8050', '--log=stdout'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"  Ngrok tunnel started (PID: {ngrok_process.pid})")
        print("  Retrieving public URL...")
        time.sleep(2)
        
        return ngrok_process
    except FileNotFoundError:
        print("  ERROR: ngrok not found. Install with: pip install pyngrok")
        print("  Or download from: https://ngrok.com/download")
        return None

def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("  ELECTION ANALYTICS - PUBLIC ACCESS SETUP")
    print("=" * 70)
    
    # Start dashboard
    app_proc = start_app()
    
    # Start ngrok
    ngrok_proc = start_ngrok()
    
    print("\n" + "=" * 70)
    print("  ACCESS INFORMATION")
    print("=" * 70)
    print("  Local Access:")
    print("    • http://127.0.0.1:8050")
    print("    • http://192.168.0.165:8050")
    print()
    print("  Public Access:")
    print("    • Check terminal or ngrok dashboard for public URL")
    print("    • URL: https://<tunnel-id>.ngrok.io")
    print()
    print("  Login Credentials:")
    print("    • Username: admin")
    print("    • Password: admin1432")
    print("=" * 70)
    print("\nPress Ctrl+C to stop all services\n")
    
    try:
        # Monitor both processes
        while True:
            if app_proc.poll() is not None:
                print("ERROR: Dashboard process ended")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        app_proc.terminate()
        if ngrok_proc:
            ngrok_proc.terminate()
        app_proc.wait()
        if ngrok_proc:
            ngrok_proc.wait()
        print("Services stopped")

if __name__ == '__main__':
    main()

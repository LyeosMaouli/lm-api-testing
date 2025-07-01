# scripts/dev_server.py
"""
Development server script for the API Testing Platform.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def setup_directories():
    """Create necessary directories for development."""
    directories = [
        "data",
        "data/credentials", 
        "data/history",
        "data/collections",
        "data/logs",
        "config",
        "config/services"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def create_sample_env():
    """Create .env file if it doesn't exist."""
    env_file = Path(".env")
    if not env_file.exists():
        env_example = Path(".env.example")
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("✓ Created .env file from .env.example")
        else:
            print("⚠ .env.example not found, please create .env manually")

def install_dependencies():
    """Install Python dependencies."""
    print("Installing Python dependencies...")
    
    # Try minimal requirements first
    requirements_files = [
        "backend/requirements-minimal.txt",
        "backend/requirements.txt"
    ]
    
    for req_file in requirements_files:
        if os.path.exists(req_file):
            try:
                print(f"Trying to install from {req_file}...")
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", req_file
                ], check=True)
                print(f"✓ Dependencies installed from {req_file}")
                return
            except subprocess.CalledProcessError as e:
                print(f"⚠ Failed to install from {req_file}: {e}")
                continue
    
    # If all files fail, try installing core packages individually
    print("Trying to install core packages individually...")
    core_packages = [
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0", 
        "pydantic>=2.5.0",
        "httpx>=0.25.0",
        "cryptography",
        "pyyaml>=6.0.0",
        "python-dotenv>=1.0.0"
    ]
    
    failed_packages = []
    for package in core_packages:
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True)
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError:
            failed_packages.append(package)
            print(f"⚠ Failed to install {package}")
    
    if failed_packages:
        print(f"\n⚠ Some packages failed to install: {failed_packages}")
        print("The platform may still work with reduced functionality.")
    else:
        print("✓ Core dependencies installed successfully")

def run_server(host="127.0.0.1", port=8000, reload=True):
    """Run the development server."""
    print(f"Starting development server on http://{host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    # Change to backend directory
    os.chdir("backend")
    
    # Run uvicorn
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", host,
        "--port", str(port),
        "--log-level", "info"
    ]
    
    if reload:
        cmd.append("--reload")
        
    subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser(description="API Testing Platform Development Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--setup-only", action="store_true", help="Only setup directories and exit")
    
    args = parser.parse_args()
    
    print("🚀 API Testing Platform Development Setup")
    print("=" * 50)
    
    # Setup directories
    setup_directories()
    
    # Create .env file
    create_sample_env()
    
    if args.setup_only:
        print("✓ Setup complete!")
        return
    
    # Install dependencies
    try:
        install_dependencies()
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Run server
    try:
        run_server(
            host=args.host,
            port=args.port,
            reload=not args.no_reload
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
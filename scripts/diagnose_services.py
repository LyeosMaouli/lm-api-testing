# scripts/diagnose_services.py
"""
Diagnostic script to debug service discovery issues.
"""

import os
import sys
import importlib
from pathlib import Path

# Add backend to path
backend_path = Path("backend").absolute()
sys.path.insert(0, str(backend_path))

def check_file_structure():
    """Check if all required files exist."""
    print("📁 Checking file structure...")
    
    required_files = [
        "backend/app/services/__init__.py",
        "backend/app/services/base.py", 
        "backend/app/services/brevo/__init__.py",
        "backend/app/services/brevo/client.py",
        "config/services/brevo.yaml",
        "config/services.yaml"
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} MISSING")
    
    return all(Path(f).exists() for f in required_files)

def test_imports():
    """Test importing the service modules."""
    print("\n🔄 Testing imports...")
    
    try:
        # Test base service import
        from app.services.base import BaseService
        print("✅ BaseService imported successfully")
        
        # Test brevo service import
        from app.services.brevo.client import BrevoService
        print("✅ BrevoService imported successfully")
        
        # Check if BrevoService has the marker
        if hasattr(BrevoService, '_is_service_class'):
            print("✅ BrevoService has _is_service_class marker")
        else:
            print("❌ BrevoService missing _is_service_class marker")
            
        # Test creating an instance
        config = {
            "service_name": "brevo",
            "environment": "test",
            "base_url": "https://api.brevo.com/v3"
        }
        service = BrevoService(config)
        print("✅ BrevoService instance created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_service_discovery():
    """Test the service discovery mechanism."""
    print("\n🔍 Testing service discovery...")
    
    try:
        from app.core.config_manager import ConfigManager
        from app.core.service_discovery import ServiceRegistry
        
        # Initialize components
        config_manager = ConfigManager("./config")
        service_registry = ServiceRegistry("backend/app/services", config_manager)
        
        # Test discovery
        discovered = service_registry.discover_services()
        print(f"🔍 Discovered services: {discovered}")
        
        if "brevo" in discovered:
            print("✅ Brevo service discovered")
            
            # Try to load the service
            try:
                service_class = service_registry.load_service_module("brevo")
                print(f"✅ Brevo service loaded: {service_class.__name__}")
                
                # Try to get service info
                service_info = service_registry.get_service_info("brevo")
                print(f"✅ Brevo service info retrieved")
                
                return True
                
            except Exception as e:
                print(f"❌ Error loading Brevo service: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("❌ Brevo service not discovered")
            return False
            
    except Exception as e:
        print(f"❌ Service discovery error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main diagnostic function."""
    print("🔧 Service Discovery Diagnostic")
    print("=" * 40)
    
    # Change to project directory
    os.chdir(Path(__file__).parent.parent)
    print(f"📂 Working directory: {os.getcwd()}")
    
    # Run checks
    structure_ok = check_file_structure()
    imports_ok = test_imports() if structure_ok else False
    discovery_ok = test_service_discovery() if imports_ok else False
    
    print("\n" + "=" * 40)
    if all([structure_ok, imports_ok, discovery_ok]):
        print("🎉 All checks passed! Service discovery should work.")
    else:
        print("❌ Some checks failed. Review the errors above.")
        
        if not structure_ok:
            print("💡 Try running: python scripts/setup_files.py")
        elif not imports_ok:
            print("💡 Check the Python import paths and file contents")
        elif not discovery_ok:
            print("💡 Check the service discovery configuration")

if __name__ == "__main__":
    main()
# scripts/debug_config.py
"""
Debug configuration loading issues.
"""

import sys
import os
from pathlib import Path
import yaml

# Add backend to path
backend_path = Path("backend").absolute()
sys.path.insert(0, str(backend_path))

def check_config_files():
    """Check all configuration files."""
    print("🔍 Checking configuration files...")
    
    # Check main services.yaml
    services_yaml = Path("config/services.yaml")
    print(f"\n📄 Main services registry: {services_yaml}")
    print(f"   Exists: {services_yaml.exists()}")
    
    if services_yaml.exists():
        try:
            with open(services_yaml, 'r') as f:
                content = f.read()
                print(f"   Content length: {len(content)} chars")
                data = yaml.safe_load(content)
                print(f"   Services defined: {list(data.get('services', {}).keys()) if data else 'None'}")
        except Exception as e:
            print(f"   Error reading: {e}")
    
    # Check brevo.yaml
    brevo_yaml = Path("config/services/brevo.yaml")
    print(f"\n📄 Brevo service config: {brevo_yaml}")
    print(f"   Exists: {brevo_yaml.exists()}")
    
    if brevo_yaml.exists():
        try:
            with open(brevo_yaml, 'r') as f:
                content = f.read()
                print(f"   Content length: {len(content)} chars")
                data = yaml.safe_load(content)
                if data:
                    print(f"   Service name: {data.get('name', 'Not found')}")
                    print(f"   Display name: {data.get('display_name', 'Not found')}")
                    print(f"   Has endpoints: {len(data.get('endpoints', {}))}")
                else:
                    print("   YAML parsed to None!")
        except Exception as e:
            print(f"   Error reading: {e}")

def test_config_manager():
    """Test the config manager directly."""
    print("\n🔧 Testing ConfigManager...")
    
    try:
        from app.core.config_manager import ConfigManager
        
        config_manager = ConfigManager("./config")
        
        # Test listing services
        available = config_manager.list_available_services()
        print(f"   Available services: {available}")
        
        # Test loading brevo config
        if "brevo" in available:
            try:
                brevo_config = config_manager.load_service_config("brevo")
                print(f"   Brevo config loaded: {brevo_config.name}")
            except Exception as e:
                print(f"   Error loading brevo config: {e}")
        
    except Exception as e:
        print(f"   Error with ConfigManager: {e}")

def test_service_registry():
    """Test the service registry directly."""
    print("\n🔧 Testing ServiceRegistry...")
    
    try:
        from app.core.config_manager import ConfigManager
        from app.core.service_discovery import ServiceRegistry
        
        config_manager = ConfigManager("./config")
        service_registry = ServiceRegistry("backend/app/services", config_manager)
        
        # Test discovery
        discovered = service_registry.discover_services()
        print(f"   Discovered services: {discovered}")
        
        # Test list_available_services
        available = service_registry.list_available_services()
        print(f"   Available services count: {len(available)}")
        for service in available:
            print(f"     - {service.get('name', 'unknown')}: {service.get('loaded', 'unknown')}")
            if service.get('error'):
                print(f"       Error: {service['error']}")
        
    except Exception as e:
        print(f"   Error with ServiceRegistry: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main debug function."""
    print("🐛 Configuration Loading Debug")
    print("=" * 50)
    
    os.chdir(Path(__file__).parent.parent)
    print(f"📂 Working directory: {os.getcwd()}")
    
    check_config_files()
    test_config_manager()
    test_service_registry()
    
    print("\n" + "=" * 50)
    print("💡 If issues found:")
    print("   1. Check file locations and content")
    print("   2. Restart the server: python scripts/dev_server.py")
    print("   3. Run: python scripts/setup_files.py")

if __name__ == "__main__":
    main()
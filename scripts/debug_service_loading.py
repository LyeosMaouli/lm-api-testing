# scripts/debug_service_loading.py
"""
Debug specific service loading issues.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path("backend").absolute()
sys.path.insert(0, str(backend_path))

def test_service_loading():
    """Test loading the Brevo service specifically."""
    print("🔧 Testing Brevo Service Loading")
    print("=" * 40)
    
    try:
        from app.core.config_manager import ConfigManager
        from app.core.service_discovery import ServiceRegistry
        
        config_manager = ConfigManager("./config")
        service_registry = ServiceRegistry("backend/app/services", config_manager)
        
        print("✅ Managers initialized")
        
        # Try to load the service module
        print("\n🔄 Attempting to load Brevo service module...")
        try:
            service_class = service_registry.load_service_module("brevo")
            print(f"✅ Service class loaded: {service_class.__name__}")
            print(f"   Module: {service_class.__module__}")
            print(f"   Has marker: {hasattr(service_class, '_is_service_class')}")
            
            # Try to create an instance
            print("\n🔄 Attempting to create service instance...")
            env_config = config_manager.get_service_environment_config("brevo", "production")
            print(f"✅ Environment config loaded: {len(env_config)} keys")
            
            instance = service_class(config=env_config, credentials=None)
            print(f"✅ Service instance created: {type(instance).__name__}")
            
            # Try to test connection (sync version for now)
            print("\n🔄 Testing service connection...")
            try:
                # For now, just test that the method exists
                print(f"✅ Service has test_connection method: {hasattr(instance, 'test_connection')}")
                print(f"✅ Service has get_supported_endpoints method: {hasattr(instance, 'get_supported_endpoints')}")
                
                if hasattr(instance, 'get_supported_endpoints'):
                    endpoints = instance.get_supported_endpoints()
                    print(f"✅ Supported endpoints: {len(endpoints)} endpoints")
                
            except Exception as e:
                print(f"⚠️  Error testing methods: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading service: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Error with managers: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_import():
    """Test importing the service class directly."""
    print("\n🔄 Testing direct service import...")
    
    try:
        from app.services.brevo.client import BrevoService
        print("✅ BrevoService imported directly")
        
        # Check the class
        print(f"   Class name: {BrevoService.__name__}")
        print(f"   Module: {BrevoService.__module__}")
        print(f"   Has marker: {hasattr(BrevoService, '_is_service_class')}")
        
        # Try to create instance with minimal config
        config = {
            "service_name": "brevo",
            "environment": "production",
            "base_url": "https://api.brevo.com/v3"
        }
        
        instance = BrevoService(config)
        print("✅ Instance created with minimal config")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    import os
    os.chdir(Path(__file__).parent.parent)
    
    # Test direct import first
    direct_ok = test_direct_import()
    
    if direct_ok:
        # Test service loading through registry
        loading_ok = test_service_loading()
        
        if loading_ok:
            print("\n🎉 All tests passed! The service should work.")
        else:
            print("\n❌ Service loading through registry failed.")
    else:
        print("\n❌ Direct import failed. Check the service implementation.")

if __name__ == "__main__":
    main()
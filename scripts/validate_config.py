"""
Validate YAML configuration files.
"""

import yaml
from pathlib import Path

def validate_yaml_file(file_path):
    """Validate a YAML file."""
    print(f"📄 Validating {file_path}...")
    
    if not Path(file_path).exists():
        print(f"❌ File does not exist: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"📝 File content length: {len(content)} characters")
            
            if len(content.strip()) == 0:
                print("❌ File is empty")
                return False
            
            # Parse YAML
            data = yaml.safe_load(content)
            
            if data is None:
                print("❌ YAML file parsed to None (likely empty or invalid)")
                print("📄 File content preview:")
                print(content[:200] + "..." if len(content) > 200 else content)
                return False
            
            print(f"✅ YAML parsed successfully")
            print(f"📊 Data type: {type(data)}")
            
            if isinstance(data, dict):
                print(f"🔑 Keys: {list(data.keys())}")
            
            return True
            
    except yaml.YAMLError as e:
        print(f"❌ YAML parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def main():
    """Validate all configuration files."""
    print("🔧 Configuration Validation")
    print("=" * 40)
    
    config_files = [
        "config/services.yaml",
        "config/services/brevo.yaml"
    ]
    
    all_valid = True
    
    for config_file in config_files:
        if not validate_yaml_file(config_file):
            all_valid = False
        print()
    
    if all_valid:
        print("🎉 All configuration files are valid!")
    else:
        print("❌ Some configuration files have issues.")
        print("💡 Try running: python scripts/setup_files.py")

if __name__ == "__main__":
    main()
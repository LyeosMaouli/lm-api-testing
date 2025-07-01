# scripts/fix_imports.py
"""
Fix missing __init__.py files and import issues.
"""

from pathlib import Path

def create_init_files():
    """Create all missing __init__.py files."""
    print("📁 Creating missing __init__.py files...")
    
    init_files = [
        "backend/app/__init__.py",
        "backend/app/core/__init__.py", 
        "backend/app/api/__init__.py",
        "backend/app/services/__init__.py",
        "backend/app/services/brevo/__init__.py",
        "backend/app/models/__init__.py"
    ]
    
    for init_file in init_files:
        init_path = Path(init_file)
        init_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not init_path.exists():
            with open(init_path, 'w') as f:
                f.write(f'"""{"Package" if init_path.name == "__init__.py" else "Module"} {init_path.parent.name}."""\n')
            print(f"✅ Created: {init_file}")
        else:
            print(f"✅ Exists: {init_file}")

def main():
    """Main function."""
    print("🔧 Fixing Import Issues")
    print("=" * 30)
    
    create_init_files()
    
    print("\n🎉 Import structure fixed!")
    print("Now restart VS Code or the Python interpreter to pick up the changes.")

if __name__ == "__main__":
    main()
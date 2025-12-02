#!/usr/bin/env python3
"""
Verify that all dependencies are installed correctly.
Run this after installing dependencies to ensure everything works.
"""

import sys

def test_import(module_name, display_name=None):
    """Test importing a module and return success status."""
    if display_name is None:
        display_name = module_name
    
    try:
        __import__(module_name)
        print(f"✅ {display_name}: OK")
        return True
    except ImportError as e:
        print(f"❌ {display_name}: FAILED - {e}")
        return False
    except Exception as e:
        print(f"⚠️  {display_name}: WARNING - {e}")
        return True  # Module imported but had other issues

def get_version(module_name, attr='__version__'):
    """Get version of a module."""
    try:
        module = __import__(module_name)
        version = getattr(module, attr, 'unknown')
        return version
    except:
        return 'unknown'

def main():
    print("=" * 60)
    print("CCTV People Counter - Dependency Verification")
    print("=" * 60)
    print()
    
    all_ok = True
    
    # Core dependencies
    print("📦 Core Dependencies:")
    print("-" * 60)
    all_ok &= test_import('numpy', 'NumPy')
    all_ok &= test_import('cv2', 'OpenCV')
    all_ok &= test_import('ultralytics', 'Ultralytics (YOLOv8)')
    all_ok &= test_import('torch', 'PyTorch')
    all_ok &= test_import('torchvision', 'TorchVision')
    print()
    
    # Tracking dependencies
    print("🎯 Tracking Dependencies:")
    print("-" * 60)
    all_ok &= test_import('filterpy', 'FilterPy')
    all_ok &= test_import('scipy', 'SciPy')
    print()
    
    # Face recognition dependencies
    print("👤 Face Recognition Dependencies:")
    print("-" * 60)
    all_ok &= test_import('insightface', 'InsightFace')
    all_ok &= test_import('onnx', 'ONNX')
    all_ok &= test_import('onnxruntime', 'ONNX Runtime')
    print()
    
    # Database dependencies
    print("🗄️  Database Dependencies:")
    print("-" * 60)
    all_ok &= test_import('psycopg2', 'PostgreSQL (psycopg2)')
    all_ok &= test_import('sqlalchemy', 'SQLAlchemy')
    all_ok &= test_import('pgvector', 'pgvector')
    print()
    
    # Utility dependencies
    print("🔧 Utility Dependencies:")
    print("-" * 60)
    all_ok &= test_import('flask', 'Flask')
    all_ok &= test_import('flask_cors', 'Flask-CORS')
    all_ok &= test_import('yaml', 'PyYAML')
    all_ok &= test_import('dotenv', 'python-dotenv')
    all_ok &= test_import('PIL', 'Pillow')
    all_ok &= test_import('matplotlib', 'Matplotlib')
    all_ok &= test_import('plotly', 'Plotly')
    print()
    
    # Version information
    print("=" * 60)
    print("📊 Version Information:")
    print("=" * 60)
    
    import numpy
    import cv2
    import onnxruntime
    
    print(f"NumPy:        {numpy.__version__}")
    print(f"OpenCV:       {cv2.__version__}")
    print(f"ONNX Runtime: {onnxruntime.__version__}")
    print(f"PyTorch:      {get_version('torch')}")
    print(f"InsightFace:  {get_version('insightface')}")
    print()
    
    # Final result
    print("=" * 60)
    if all_ok:
        print("🎉 SUCCESS! All dependencies are installed correctly!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Setup PostgreSQL: python3 setup_database.py --password your_password")
        print("2. Configure .env:   cp .env.example .env && nano .env")
        print("3. Add organization: python3 manage_organizations.py add --name 'Company A'")
        print("4. Add camera:       python3 manage_cameras.py add --camera-id entrance ...")
        print("5. Run system:       python3 run_cameras.py")
        return 0
    else:
        print("❌ FAILED! Some dependencies are missing or broken.")
        print("=" * 60)
        print()
        print("Try reinstalling:")
        print("  ./install_dependencies.sh")
        print()
        print("Or manually:")
        print("  pip install -r requirements.txt")
        print("  pip install -r requirements_face.txt")
        return 1

if __name__ == '__main__':
    sys.exit(main())


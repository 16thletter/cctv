#!/usr/bin/env python3
"""
CCTV System Diagnostic Tool
Checks GPU, database, face recognition, and system status
"""
import os
import sys
import subprocess

def print_header(title):
    """Print section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_gpu():
    """Check GPU availability"""
    print_header("🎮 GPU Status")
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', 
                               '--format=csv,noheader'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ GPU: {result.stdout.strip()}")
            return True
        else:
            print("❌ GPU not available")
            return False
    except Exception as e:
        print(f"❌ GPU check failed: {e}")
        return False

def check_cuda_libraries():
    """Check CUDA libraries"""
    print_header("📚 CUDA Libraries")
    try:
        import torch
        print(f"✅ PyTorch CUDA: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   Device: {torch.cuda.get_device_name(0)}")
            print(f"   CUDA Version: {torch.version.cuda}")
        
        import onnxruntime as ort
        providers = ort.get_available_providers()
        print(f"✅ ONNX Runtime Providers: {', '.join(providers)}")
        
        if 'CUDAExecutionProvider' in providers:
            print("   ✅ GPU acceleration available for face recognition")
        else:
            print("   ⚠️  GPU acceleration not available (using CPU)")
        
        return True
    except Exception as e:
        print(f"❌ CUDA library check failed: {e}")
        return False

def check_database():
    """Check database connection"""
    print_header("🗄️  Database")
    try:
        from src.database_pg import PostgreSQLDatabase
        from src.utils import load_config
        
        config = load_config('config/config.yaml')
        db = PostgreSQLDatabase(config)
        
        if db.session:
            print("✅ Database connected")
            
            # Check persons
            persons = db.get_all_persons()
            print(f"   Persons enrolled: {len(persons)}")
            
            # Check embeddings
            embeddings = db.get_all_face_embeddings()
            print(f"   Face embeddings: {len(embeddings)}")
            
            # Check organizations
            orgs = db.get_all_organizations()
            print(f"   Organizations: {len(orgs)}")
            
            db.close()
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def check_face_recognition():
    """Check face recognition system"""
    print_header("👤 Face Recognition")
    try:
        from src.face_recognition import FaceRecognizer
        from src.utils import load_config
        
        config = load_config('config/config.yaml')
        fr = FaceRecognizer(config)
        
        if fr.is_enabled():
            print("✅ Face recognition enabled")
            print(f"   Model: {config.get('face_recognition', {}).get('model', 'N/A')}")
            print(f"   Providers: {config.get('face_recognition', {}).get('providers', [])}")
            print(f"   Detection size: {config.get('face_recognition', {}).get('det_size', 'N/A')}")
            return True
        else:
            print("❌ Face recognition disabled")
            return False
    except Exception as e:
        print(f"❌ Face recognition check failed: {e}")
        return False

def check_cameras():
    """Check camera configuration"""
    print_header("📹 Cameras")
    try:
        from src.database_pg import PostgreSQLDatabase
        from src.utils import load_config
        
        config = load_config('config/config.yaml')
        db = PostgreSQLDatabase(config)
        
        if db.session:
            cameras = db.session.query(db.Camera).filter_by(is_active=True).all()
            print(f"✅ Active cameras: {len(cameras)}")
            for cam in cameras:
                print(f"   - {cam.camera_id}: {cam.location}")
            db.close()
            return True
        else:
            return False
    except Exception as e:
        print(f"❌ Camera check failed: {e}")
        return False

def show_summary(results):
    """Show diagnostic summary"""
    print_header("📊 Summary")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nTests passed: {passed}/{total}")
    print("\nStatus:")
    for check, status in results.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {check}")
    
    if passed == total:
        print("\n🎉 All systems operational!")
        print("\nNext steps:")
        print("  • Run cameras: ./run_with_gpu.sh --camera-id entrance")
        print("  • Enroll person: ./run_manage_persons.sh --enroll --name 'Name' --webcam")
        print("  • View dashboard: python3 dashboard.py")
    else:
        print("\n⚠️  Some systems need attention. Check errors above.")

def main():
    """Main diagnostic function"""
    print("\n" + "="*60)
    print("  🔍 CCTV System Diagnostic Tool")
    print("="*60)
    
    results = {}
    
    # Run all checks
    results['GPU'] = check_gpu()
    results['CUDA Libraries'] = check_cuda_libraries()
    results['Database'] = check_database()
    results['Face Recognition'] = check_face_recognition()
    results['Cameras'] = check_cameras()
    
    # Show summary
    show_summary(results)
    
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    main()


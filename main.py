#!/usr/bin/env python3
"""
CCTV Analytics System - Main Entry Point
Production-ready entry point replacing shell scripts

Usage:
    python main.py run                    # Run all cameras
    python main.py run --camera-id entrance  # Run specific camera
    python main.py run --org-id 1         # Run cameras for organization
    python main.py api                    # Start API server
    python main.py list-cameras           # List available cameras
    python main.py health                 # Health check
"""
import argparse
import sys
import os
import signal
import logging
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from cctv.config.config_manager import ConfigManager
from cctv.utils.utils import setup_logging
from cctv.managers.camera_manager import CameraManager
from cctv.services.webhook_service import WebhookService


# Global references for signal handling
camera_manager = None
webhook_service = None


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    print("\n\n🛑 Shutting down CCTV system...")
    
    if camera_manager:
        camera_manager.stop_all_cameras()
    
    if webhook_service:
        webhook_service.stop()
    
    sys.exit(0)


def run_cameras(args):
    """Run camera processing system"""
    global camera_manager, webhook_service
    
    # Load configuration
    config_manager = ConfigManager(args.config)
    config = config_manager.get_all()
    
    # Setup logging
    logger = setup_logging(config)
    logger.info("=" * 80)
    logger.info("🎥 CCTV Analytics System - Starting")
    logger.info("=" * 80)
    
    # Initialize webhook service
    webhook_service = WebhookService(config, logger)
    
    # Initialize camera manager
    camera_manager = CameraManager(config)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Import camera worker (lazy import to avoid circular dependencies)
    from scripts.run_cameras import camera_process_worker
    
    # Start cameras
    if args.camera_id:
        cameras = camera_manager.get_active_cameras()
        camera_config = next((c for c in cameras if c['id'] == args.camera_id), None)
        
        if not camera_config:
            logger.error(f"Camera '{args.camera_id}' not found")
            sys.exit(1)
        
        logger.info(f"Starting camera: {args.camera_id}")
        camera_manager.start_camera_process(camera_config, camera_process_worker)
    else:
        logger.info(f"Starting cameras (org_id={args.org_id})")
        camera_manager.start_all_cameras(camera_process_worker, args.org_id)
    
    # Keep running
    logger.info("\n✓ System running. Press Ctrl+C to stop.\n")
    
    try:
        import time
        while True:
            time.sleep(1)
            running = camera_manager.get_running_cameras()
            if not running:
                logger.warning("All cameras stopped")
                break
    except KeyboardInterrupt:
        pass
    finally:
        camera_manager.close()
        if webhook_service:
            webhook_service.stop()
        logger.info("Shutdown complete")


def start_api(args):
    """Start REST API server"""
    from cctv.api.server import app
    
    config_manager = ConfigManager(args.config)
    config = config_manager.get_all()
    
    logger = setup_logging(config)
    logger.info("Starting API server...")
    
    host = args.host or config.get('api', {}).get('host', '0.0.0.0')
    port = args.port or config.get('api', {}).get('port', 5000)
    
    app.run(host=host, port=port, debug=args.debug)


def list_cameras(args):
    """List available cameras"""
    config_manager = ConfigManager(args.config)
    config = config_manager.get_all()
    
    camera_manager = CameraManager(config)
    cameras = camera_manager.get_active_cameras(args.org_id)
    
    print("\n📹 Available Cameras:")
    print("=" * 80)
    for cam in cameras:
        print(f"  • ID: {cam['id']}")
        print(f"    Location: {cam.get('location', 'N/A')}")
        print(f"    Organization ID: {cam.get('organization_id', 'N/A')}")
        print(f"    Active: {cam.get('is_active', False)}")
        print()
    
    print(f"Total: {len(cameras)} camera(s)")


def health_check(args):
    """Perform system health check"""
    from scripts.debug.diagnose import run_diagnostics
    
    config_manager = ConfigManager(args.config)
    config = config_manager.get_all()
    
    logger = setup_logging(config)
    
    print("\n🏥 System Health Check")
    print("=" * 80)
    
    run_diagnostics(config)
    
    print("\n✓ Health check complete")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='CCTV Analytics System - Production Entry Point',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py run                          # Run all cameras
  python main.py run --camera-id entrance     # Run specific camera
  python main.py run --org-id 1               # Run cameras for org
  python main.py api                          # Start API server
  python main.py list-cameras                 # List cameras
  python main.py health                       # Health check
        """
    )
    
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run camera processing system')
    run_parser.add_argument('--camera-id', help='Run specific camera by ID')
    run_parser.add_argument('--org-id', type=int, help='Run cameras for organization ID')
    
    # API command
    api_parser = subparsers.add_parser('api', help='Start REST API server')
    api_parser.add_argument('--host', help='API host (default: 0.0.0.0)')
    api_parser.add_argument('--port', type=int, help='API port (default: 5000)')
    api_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # List cameras command
    list_parser = subparsers.add_parser('list-cameras', help='List available cameras')
    list_parser.add_argument('--org-id', type=int, help='Filter by organization ID')
    
    # Health check command
    health_parser = subparsers.add_parser('health', help='System health check')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == 'run':
        run_cameras(args)
    elif args.command == 'api':
        start_api(args)
    elif args.command == 'list-cameras':
        list_cameras(args)
    elif args.command == 'health':
        health_check(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()



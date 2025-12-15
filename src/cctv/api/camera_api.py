#!/usr/bin/env python3
"""
Camera Management REST API
Manage cameras dynamically via HTTP API
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
from dotenv import load_dotenv

import sys
import os

from cctv.utils.utils import load_config
from cctv.database.database_pg import PostgreSQLDatabase

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load configuration
config = load_config()
db = PostgreSQLDatabase(config)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/api/cameras', methods=['GET'])
def get_cameras():
    """Get all cameras or filter by organization"""
    org_id = request.args.get('organization_id', type=int)
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    
    if org_id:
        cameras = db.get_cameras_by_organization(org_id, active_only)
    else:
        cameras = db.get_all_cameras(active_only)
    
    return jsonify({
        'success': True,
        'count': len(cameras),
        'cameras': [
            {
                'id': cam.id,
                'camera_id': cam.camera_id,
                'organization_id': cam.organization_id,
                'location': cam.location,
                'description': cam.description,
                'rtsp_url_env': cam.rtsp_url_env,
                'is_active': cam.is_active,
                'created_at': cam.created_at.isoformat() if cam.created_at else None
            }
            for cam in cameras
        ]
    })


@app.route('/api/cameras', methods=['POST'])
def add_camera():
    """Add a new camera"""
    data = request.json
    
    required_fields = ['camera_id', 'rtsp_url_env']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}'
            }), 400
    
    # Verify environment variable exists
    rtsp_url = os.getenv(data['rtsp_url_env'])
    if not rtsp_url:
        return jsonify({
            'success': False,
            'error': f"Environment variable '{data['rtsp_url_env']}' not found"
        }), 400
    
    camera_id = db.add_camera(
        camera_id=data['camera_id'],
        rtsp_url_env=data['rtsp_url_env'],
        location=data.get('location'),
        organization_id=data.get('organization_id'),
        description=data.get('description')
    )
    
    if camera_id:
        return jsonify({
            'success': True,
            'camera_id': camera_id,
            'message': 'Camera added successfully'
        }), 201
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to add camera'
        }), 500


@app.route('/api/cameras/<camera_id>', methods=['GET'])
def get_camera(camera_id):
    """Get specific camera by ID"""
    camera = db.get_camera(camera_id)
    
    if not camera:
        return jsonify({
            'success': False,
            'error': 'Camera not found'
        }), 404
    
    return jsonify({
        'success': True,
        'camera': {
            'id': camera.id,
            'camera_id': camera.camera_id,
            'organization_id': camera.organization_id,
            'location': camera.location,
            'description': camera.description,
            'rtsp_url_env': camera.rtsp_url_env,
            'is_active': camera.is_active,
            'created_at': camera.created_at.isoformat() if camera.created_at else None
        }
    })


@app.route('/api/organizations', methods=['GET'])
def get_organizations():
    """Get all organizations"""
    orgs = db.get_all_organizations()
    
    return jsonify({
        'success': True,
        'count': len(orgs),
        'organizations': [
            {
                'id': org.id,
                'name': org.name,
                'code': org.code,
                'is_active': org.is_active
            }
            for org in orgs
        ]
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'database': 'connected' if db.session else 'disconnected'
    })


@app.route('/api/test-camera/<camera_id>', methods=['GET'])
def test_camera(camera_id):
    """Test if camera RTSP URL is accessible"""
    import cv2
    
    camera = db.get_camera(camera_id)
    if not camera:
        return jsonify({
            'success': False,
            'error': 'Camera not found'
        }), 404
    
    # Get RTSP URL from environment
    rtsp_url = os.getenv(camera.rtsp_url_env)
    if not rtsp_url:
        return jsonify({
            'success': False,
            'error': f"Environment variable '{camera.rtsp_url_env}' not found"
        }), 400
    
    # Try to open camera
    cap = cv2.VideoCapture(rtsp_url)
    is_accessible = cap.isOpened()
    cap.release()
    
    return jsonify({
        'success': True,
        'camera_id': camera_id,
        'accessible': is_accessible,
        'rtsp_url_env': camera.rtsp_url_env
    })


if __name__ == '__main__':
    logger.info("Starting Camera Management API")
    logger.info("API Documentation: http://localhost:5000/api/cameras")
    app.run(host='0.0.0.0', port=5000, debug=True)


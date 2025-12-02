#!/usr/bin/env python3
"""
Dynamic Camera Manager
Loads camera configurations from database and manages multiple camera processes
"""
import os
import logging
import multiprocessing as mp
from typing import List, Dict, Optional
from dotenv import load_dotenv

from src.database_pg import PostgreSQLDatabase


class CameraManager:
    """Manages multiple camera instances dynamically from database"""
    
    def __init__(self, config: dict):
        """
        Initialize camera manager
        
        Args:
            config: Application configuration (for database connection)
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db = PostgreSQLDatabase(config)
        self.processes: Dict[str, mp.Process] = {}
        
        # Load environment variables
        load_dotenv()
    
    def get_active_cameras(self, organization_id: Optional[int] = None) -> List[Dict]:
        """
        Get active cameras from database
        
        Args:
            organization_id: Optional filter by organization
            
        Returns:
            List of camera configurations
        """
        if not self.db.session:
            self.logger.error("Database connection not available")
            return []
        
        # Get cameras from database
        if organization_id:
            cameras = self.db.get_cameras_by_organization(organization_id, active_only=True)
        else:
            cameras = self.db.get_all_cameras(active_only=True)
        
        # Convert to configuration dictionaries
        camera_configs = []
        for cam in cameras:
            # Get RTSP URL from environment variable
            rtsp_url = None
            if cam.rtsp_url_env:
                rtsp_url = os.getenv(cam.rtsp_url_env)
                if not rtsp_url:
                    self.logger.warning(
                        f"Environment variable '{cam.rtsp_url_env}' not found for camera '{cam.camera_id}'"
                    )
                    continue

            camera_config = {
                'id': cam.camera_id,
                'source': rtsp_url,
                'organization_id': cam.organization_id,
                'location': cam.location,
                'description': cam.description,
                'db_id': cam.id
            }

            # Add camera-specific counting line configuration if set
            # If NULL in database, will use defaults from config.yaml
            if cam.outside_line_x1 is not None:
                camera_config['counting_line'] = {
                    'outside_line': [
                        cam.outside_line_x1,
                        cam.outside_line_y1,
                        cam.outside_line_x2,
                        cam.outside_line_y2
                    ],
                    'inside_line': [
                        cam.inside_line_x1,
                        cam.inside_line_y1,
                        cam.inside_line_x2,
                        cam.inside_line_y2
                    ],
                    'in_direction': cam.in_direction,
                    'color': [cam.line_color_r, cam.line_color_g, cam.line_color_b],
                    'thickness': cam.line_thickness,
                    'cooldown_frames': cam.cooldown_frames,
                    'min_track_length': cam.min_track_length
                }

            camera_configs.append(camera_config)

        self.logger.info(f"Loaded {len(camera_configs)} active camera(s) from database")
        return camera_configs
    
    def start_camera_process(self, camera_config: dict, process_func):
        """
        Start a camera processing instance
        
        Args:
            camera_config: Camera configuration dictionary
            process_func: Function to run for camera processing (e.g., main loop)
        """
        camera_id = camera_config['id']
        
        if camera_id in self.processes and self.processes[camera_id].is_alive():
            self.logger.warning(f"Camera '{camera_id}' is already running")
            return
        
        # Create process
        process = mp.Process(
            target=process_func,
            args=(camera_config, self.config),
            name=f"Camera-{camera_id}"
        )
        
        # Start process
        process.start()
        self.processes[camera_id] = process
        
        self.logger.info(f"Started camera process: {camera_id} (PID: {process.pid})")
    
    def stop_camera_process(self, camera_id: str, timeout: int = 5):
        """
        Stop a camera processing instance
        
        Args:
            camera_id: Camera identifier
            timeout: Timeout in seconds to wait for process to terminate
        """
        if camera_id not in self.processes:
            self.logger.warning(f"Camera '{camera_id}' is not running")
            return
        
        process = self.processes[camera_id]
        
        if process.is_alive():
            self.logger.info(f"Stopping camera process: {camera_id}")
            process.terminate()
            process.join(timeout=timeout)
            
            if process.is_alive():
                self.logger.warning(f"Force killing camera process: {camera_id}")
                process.kill()
                process.join()
        
        del self.processes[camera_id]
        self.logger.info(f"Stopped camera process: {camera_id}")
    
    def start_all_cameras(self, process_func, organization_id: Optional[int] = None):
        """
        Start all active cameras from database
        
        Args:
            process_func: Function to run for each camera
            organization_id: Optional filter by organization
        """
        cameras = self.get_active_cameras(organization_id)
        
        if not cameras:
            self.logger.warning("No active cameras found in database")
            return
        
        for camera_config in cameras:
            self.start_camera_process(camera_config, process_func)
        
        self.logger.info(f"Started {len(cameras)} camera process(es)")
    
    def stop_all_cameras(self):
        """Stop all running camera processes"""
        camera_ids = list(self.processes.keys())
        
        for camera_id in camera_ids:
            self.stop_camera_process(camera_id)
        
        self.logger.info("All camera processes stopped")
    
    def get_running_cameras(self) -> List[str]:
        """Get list of currently running camera IDs"""
        return [
            camera_id for camera_id, process in self.processes.items()
            if process.is_alive()
        ]
    
    def close(self):
        """Cleanup resources"""
        self.stop_all_cameras()
        if self.db:
            self.db.close()


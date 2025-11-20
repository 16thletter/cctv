"""
Utility functions for the people counter system
"""
import yaml
import logging
import colorlog
from pathlib import Path
import numpy as np
import os
from dotenv import load_dotenv


def load_config(config_path="config/config.yaml"):
    """Load configuration from YAML file and override with environment variables"""
    # Load environment variables from .env file
    load_dotenv()

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Override camera source with environment variable if set
    rtsp_url = os.getenv('RTSP_URL')
    if rtsp_url:
        config['camera']['source'] = rtsp_url

    return config


def setup_logging(config):
    """Setup logging with color support"""
    log_level = getattr(logging, config['logging']['level'])
    
    # Create logs directory if it doesn't exist
    log_file = config['logging']['file']
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatter
    formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # Setup console handler
    if config['logging']['console']:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logging.root.addHandler(console_handler)
    
    # Setup file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logging.root.addHandler(file_handler)
    
    logging.root.setLevel(log_level)
    
    return logging.getLogger(__name__)


def line_intersection(p1, p2, p3, p4, return_point=False):
    """
    Check if line segment p1-p2 intersects with line segment p3-p4

    Args:
        p1, p2: First line segment endpoints
        p3, p4: Second line segment endpoints
        return_point: If True, return (True, intersection_point) or (False, None)

    Returns:
        If return_point=False: True if they intersect, False otherwise
        If return_point=True: (bool, point) tuple
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if abs(denom) < 1e-10:
        return (False, None) if return_point else False

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    intersects = 0 <= t <= 1 and 0 <= u <= 1

    if return_point and intersects:
        # Calculate intersection point
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        return (True, (ix, iy))

    return (False, None) if return_point else intersects


def get_direction(p1, p2, line_start, line_end):
    """
    Determine which side of the line the movement is crossing from/to
    Uses cross product to determine if crossing from above/below or left/right
    Returns: 'up', 'down', 'left', 'right', or None
    """
    # Calculate line vector (from start to end)
    line_vec = np.array([line_end[0] - line_start[0], line_end[1] - line_start[1]])

    # Calculate position vectors relative to line start
    p1_vec = np.array([p1[0] - line_start[0], p1[1] - line_start[1]])
    p2_vec = np.array([p2[0] - line_start[0], p2[1] - line_start[1]])

    # Calculate cross products to determine which side of line each point is on
    # Positive cross product = point is on right side of line vector
    # Negative cross product = point is on left side of line vector
    cross1 = np.cross(line_vec, p1_vec)
    cross2 = np.cross(line_vec, p2_vec)

    # Determine primary direction based on line orientation
    if abs(line_vec[0]) > abs(line_vec[1]):  # Horizontal line
        # For horizontal line, check if crossing from top to bottom or bottom to top
        if cross1 < 0 and cross2 >= 0:
            # Crossing from top (negative side) to bottom (positive side)
            return 'down'
        elif cross1 > 0 and cross2 <= 0:
            # Crossing from bottom (positive side) to top (negative side)
            return 'up'
    else:  # Vertical line
        # For vertical line, check if crossing from left to right or right to left
        if cross1 < 0 and cross2 >= 0:
            # Crossing from left to right
            return 'right'
        elif cross1 > 0 and cross2 <= 0:
            # Crossing from right to left
            return 'left'

    return None


def convert_line_coords(coords, frame_width, frame_height):
    """
    Convert normalized coordinates (0-1) to pixel coordinates
    """
    x1 = int(coords[0] * frame_width)
    y1 = int(coords[1] * frame_height)
    x2 = int(coords[2] * frame_width)
    y2 = int(coords[3] * frame_height)
    return (x1, y1, x2, y2)


def create_directories():
    """Create necessary directories for the project"""
    directories = ['models', 'logs', 'output', 'data']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep for models directory
    (Path('models') / '.gitkeep').touch()


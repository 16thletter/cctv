"""
Configuration Manager
Centralized configuration loading and validation
"""
import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv


class ConfigManager:
    """
    Manages application configuration
    
    Features:
    - Loads YAML configuration files
    - Merges with environment variables
    - Validates configuration
    - Provides type-safe access
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration YAML file
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or self._find_config_file()
        self.config: Dict[str, Any] = {}
        
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        self._load_config()
        self._merge_env_vars()
    
    def _find_config_file(self) -> str:
        """Find configuration file in standard locations"""
        possible_paths = [
            'config/config.yaml',
            'config/config_dynamic.yaml',
            os.path.join(os.path.dirname(__file__), '../../config/config.yaml')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        raise FileNotFoundError("Configuration file not found")
    
    def _load_config(self):
        """Load YAML configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
            self.logger.info(f"Configuration loaded from: {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _merge_env_vars(self):
        """Merge environment variables into configuration"""
        # Database credentials
        if 'POSTGRES_HOST' in os.environ:
            self.config.setdefault('database', {})['host'] = os.environ['POSTGRES_HOST']
        if 'POSTGRES_PORT' in os.environ:
            self.config.setdefault('database', {})['port'] = int(os.environ['POSTGRES_PORT'])
        if 'POSTGRES_DB' in os.environ:
            self.config.setdefault('database', {})['database'] = os.environ['POSTGRES_DB']
        if 'POSTGRES_USER' in os.environ:
            self.config.setdefault('database', {})['user'] = os.environ['POSTGRES_USER']
        if 'POSTGRES_PASSWORD' in os.environ:
            self.config.setdefault('database', {})['password'] = os.environ['POSTGRES_PASSWORD']
        
        # Webhook base URL
        if 'WEBHOOK_BASE_URL' in os.environ:
            self.config.setdefault('webhooks', {})['base_url'] = os.environ['WEBHOOK_BASE_URL']
        
        # Camera RTSP URLs (loaded dynamically from .env)
        # These are referenced by environment variable names in database
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports dot notation)
        
        Args:
            key: Configuration key (e.g., 'database.host' or 'webhooks.enabled')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_detector_config(self, detector_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific detector
        
        Args:
            detector_type: Type of detector (e.g., 'person', 'fire')
            
        Returns:
            Detector-specific configuration dictionary
        """
        detector_configs = self.config.get('detectors', {})
        return detector_configs.get(detector_type, {})
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration dictionary"""
        return self.config.copy()
    
    def validate(self) -> bool:
        """
        Validate configuration
        
        Returns:
            True if valid, False otherwise
        """
        required_keys = [
            'database.host',
            'database.database',
            'database.user'
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                self.logger.error(f"Missing required configuration: {key}")
                return False
        
        return True


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to load configuration
    
    BACKWARD COMPATIBILITY: This function maintains the same interface
    as the old utils.load_config() function.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        Configuration dictionary
    """
    # Try new config manager first
    try:
        manager = ConfigManager(config_path)
        return manager.get_all()
    except Exception:
        # Fallback to old method for backward compatibility
        import yaml
        import os
        from dotenv import load_dotenv
        
        if config_path is None:
            config_path = "config/config.yaml"
        
        load_dotenv()
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        # Override with environment variables (old behavior)
        if 'database' in config:
            if os.getenv('POSTGRES_HOST'):
                config['database']['host'] = os.getenv('POSTGRES_HOST')
            if os.getenv('POSTGRES_PORT'):
                config['database']['port'] = int(os.getenv('POSTGRES_PORT'))
            if os.getenv('POSTGRES_DB'):
                config['database']['database'] = os.getenv('POSTGRES_DB')
            if os.getenv('POSTGRES_USER'):
                config['database']['user'] = os.getenv('POSTGRES_USER')
            if os.getenv('POSTGRES_PASSWORD'):
                config['database']['password'] = os.getenv('POSTGRES_PASSWORD')
        
        return config



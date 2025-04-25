import os
from dataclasses import dataclass
from typing import Literal


@dataclass
class ConfigManager:
    """Configuration manager for market simulation."""
    storage_type: Literal['local', 'gcs']
    local_storage_path: str
    default_drift: float
    default_volatility: float
    default_jump_intensity: float
    default_jump_mean: float
    default_jump_volatility: float
    log_level: str
    log_format: str

    def __init__(self):
        """Initialize configuration from environment variables."""
        self.storage_type = self._get_storage_type()
        self.local_storage_path = self._get_required_str('LOCAL_STORAGE_PATH')
        
        # Validate volatility must be positive
        vol = self._get_required_float('DEFAULT_VOLATILITY')
        if vol <= 0:
            raise ValueError("Volatility must be positive")
        self.default_volatility = vol
        
        # Get drift
        self.default_drift = self._get_required_float('DEFAULT_DRIFT')
        
        # Optional parameters with validation
        intensity = self._get_float('DEFAULT_JUMP_INTENSITY', 1.0)
        if intensity < 0:
            raise ValueError("Jump intensity must be non-negative")
        self.default_jump_intensity = intensity
        
        self.default_jump_mean = self._get_float('DEFAULT_JUMP_MEAN', 0.0)
        
        jump_vol = self._get_float('DEFAULT_JUMP_VOLATILITY', 0.2)
        if jump_vol <= 0:
            raise ValueError("Jump volatility must be positive")
        self.default_jump_volatility = jump_vol
        
        self.log_level = self._get_str('LOG_LEVEL', 'INFO')
        self.log_format = self._get_str('LOG_FORMAT', 
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _get_storage_type(self) -> Literal['local', 'gcs']:
        """Get and validate storage type from environment."""
        storage_type = os.getenv('STORAGE_TYPE')
        if not storage_type:
            raise ValueError("Missing required configuration: STORAGE_TYPE")
        
        storage_type = storage_type.lower()
        if storage_type not in ('local', 'gcs'):
            raise ValueError(f"Invalid storage type: {storage_type}")
        return storage_type

    def _get_required_str(self, key: str) -> str:
        """Get required string value from environment."""
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Missing required configuration: {key}")
        return value

    def _get_str(self, key: str, default: str) -> str:
        """Get optional string value from environment."""
        return os.getenv(key, default)

    def _get_required_float(self, key: str) -> float:
        """Get required float value from environment."""
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Missing required configuration: {key}")
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Invalid numeric value for {key}: {value}")

    def _get_float(self, key: str, default: float) -> float:
        """Get optional float value from environment."""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Invalid numeric value for {key}: {value}")
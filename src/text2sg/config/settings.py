"""Settings management using Pydantic.

Provides type-safe configuration loading from environment variables and files.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import lru_cache

from pydantic import BaseSettings, Field, validator
from pydantic_settings import BaseSettings as PydanticBaseSettings


class APISettings(BaseSettings):
    """API-related settings."""
    
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    
    # Request settings
    max_retries: int = Field(3, env="API_MAX_RETRIES")
    timeout: int = Field(30, env="API_TIMEOUT")
    rate_limit_delay: float = Field(1.0, env="API_RATE_LIMIT_DELAY")
    
    class Config:
        env_prefix = "TEXT2SG_API_"


class ProcessingSettings(BaseSettings):
    """Data processing settings."""
    
    batch_size: int = Field(10, env="BATCH_SIZE")
    max_workers: int = Field(4, env="MAX_WORKERS")
    chunk_size: int = Field(1000, env="CHUNK_SIZE")
    
    # CSV settings
    csv_encoding: str = Field("utf-8", env="CSV_ENCODING")
    csv_delimiter: str = Field(",", env="CSV_DELIMITER")
    create_backups: bool = Field(True, env="CREATE_BACKUPS")
    
    # JSON settings
    json_indent: int = Field(2, env="JSON_INDENT")
    json_ensure_ascii: bool = Field(False, env="JSON_ENSURE_ASCII")
    
    class Config:
        env_prefix = "TEXT2SG_PROCESSING_"


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    level: str = Field("INFO", env="LOG_LEVEL")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    file_path: Optional[str] = Field(None, env="LOG_FILE")
    max_file_size: int = Field(10 * 1024 * 1024, env="LOG_MAX_FILE_SIZE")  # 10MB
    backup_count: int = Field(5, env="LOG_BACKUP_COUNT")
    
    # Console logging
    console_enabled: bool = Field(True, env="LOG_CONSOLE_ENABLED")
    console_level: str = Field("INFO", env="LOG_CONSOLE_LEVEL")
    
    # Rich logging
    rich_enabled: bool = Field(True, env="LOG_RICH_ENABLED")
    rich_traceback: bool = Field(True, env="LOG_RICH_TRACEBACK")
    
    @validator('level', 'console_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    class Config:
        env_prefix = "TEXT2SG_LOG_"


class PathSettings(BaseSettings):
    """Path-related settings."""
    
    data_dir: Path = Field(Path("data"), env="DATA_DIR")
    output_dir: Path = Field(Path("output"), env="OUTPUT_DIR")
    cache_dir: Path = Field(Path(".cache"), env="CACHE_DIR")
    temp_dir: Path = Field(Path(".temp"), env="TEMP_DIR")
    
    # Ensure directories exist
    create_dirs: bool = Field(True, env="CREATE_DIRS")
    
    @validator('data_dir', 'output_dir', 'cache_dir', 'temp_dir')
    def convert_to_path(cls, v):
        return Path(v) if not isinstance(v, Path) else v
    
    class Config:
        env_prefix = "TEXT2SG_PATH_"


class Settings(PydanticBaseSettings):
    """Main settings class combining all configuration sections."""
    
    # Application info
    app_name: str = Field("Text2SG", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    
    # Sub-settings
    api: APISettings = Field(default_factory=APISettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    
    # Custom settings from file
    custom_settings: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        env_prefix = "TEXT2SG_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create directories if needed
        if self.paths.create_dirs:
            self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories."""
        for dir_path in [self.paths.data_dir, self.paths.output_dir, 
                        self.paths.cache_dir, self.paths.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_file(cls, config_file: Path) -> "Settings":
        """Load settings from a configuration file."""
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            if config_file.suffix.lower() == '.json':
                config_data = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_file.suffix}")
        
        return cls(**config_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return self.dict()
    
    def save_to_file(self, config_file: Path):
        """Save current settings to a file."""
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            if config_file.suffix.lower() == '.json':
                json.dump(self.to_dict(), f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported config file format: {config_file.suffix}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider."""
        provider_key_map = {
            'gemini': self.api.gemini_api_key,
            'openai': self.api.openai_api_key,
            'anthropic': self.api.anthropic_api_key,
        }
        return provider_key_map.get(provider.lower())
    
    def update_custom_setting(self, key: str, value: Any):
        """Update a custom setting."""
        self.custom_settings[key] = value
    
    def get_custom_setting(self, key: str, default: Any = None) -> Any:
        """Get a custom setting value."""
        return self.custom_settings.get(key, default)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    # Try to load from config file first
    config_file = Path("config.json")
    if config_file.exists():
        return Settings.from_file(config_file)
    
    # Otherwise load from environment
    return Settings()


def reload_settings() -> Settings:
    """Reload settings (clears cache)."""
    get_settings.cache_clear()
    return get_settings()
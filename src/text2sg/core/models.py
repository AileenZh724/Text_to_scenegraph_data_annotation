"""Core models for text2sg package.

Contains configuration classes and core data models used across the package.
"""

from typing import Optional
from pydantic import BaseModel, Field


class GenerationConfig(BaseModel):
    """Configuration for text generation and scene graph generation.
    
    This class holds configuration parameters used by various providers
    and services throughout the text2sg package.
    """
    
    api_key: str = Field(..., description="API key for the provider")
    max_retries: int = Field(3, description="Maximum number of retries per request")
    batch_size: int = Field(10, description="Batch size for processing")
    temperature: float = Field(0.7, description="Temperature for generation (higher = more creative)")
    timeout: int = Field(30, description="Timeout in seconds for API requests")
    model: Optional[str] = Field(None, description="Model name to use (provider-specific)")
    
    class Config:
        """Pydantic configuration."""
        
        arbitrary_types_allowed = True
"""Base generator interface for scene graph generation providers."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import time
import logging

from ..models import SceneGraph, GenerationResult


logger = logging.getLogger(__name__)


class BaseGenerator(ABC):
    """Abstract base class for scene graph generators.
    
    This class defines the interface that all scene graph generation providers
    must implement. It follows the Strategy pattern to allow pluggable providers.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the generator with configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.name = self.__class__.__name__.replace('Provider', '').lower()
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup provider-specific logging."""
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
    
    @abstractmethod
    def generate(self, text: str, **kwargs) -> GenerationResult:
        """Generate a scene graph from input text.
        
        Args:
            text: Input text description
            **kwargs: Additional generation parameters
            
        Returns:
            GenerationResult containing the generated scene graph or error
        """
        pass

    @abstractmethod
    def generate_with_colors(self, text: str, **kwargs) -> str:
        """Enrich text description with color information.
        
        Args:
            text: Input text description without color information
            **kwargs: Additional generation parameters
            
        Returns:
            Text description enriched with color information
        """
        pass
    
    def batch_generate(
        self, 
        texts: List[str], 
        max_retries: int = 3,
        delay_between_requests: float = 0.0,
        **kwargs
    ) -> List[GenerationResult]:
        """Generate scene graphs for multiple texts.
        
        Args:
            texts: List of input text descriptions
            max_retries: Maximum number of retries per text
            delay_between_requests: Delay between requests in seconds
            **kwargs: Additional generation parameters
            
        Returns:
            List of GenerationResult objects
        """
        results = []
        
        for i, text in enumerate(texts):
            self.logger.info(f"Processing text {i+1}/{len(texts)}")
            
            # Add delay between requests if specified
            if delay_between_requests > 0 and i > 0:
                time.sleep(delay_between_requests)
            
            result = self._generate_with_retry(
                text, 
                max_retries=max_retries, 
                **kwargs
            )
            results.append(result)
            
            # Log result
            if result.success:
                self.logger.info(f"Successfully generated scene graph for text {i+1}")
            else:
                self.logger.error(f"Failed to generate scene graph for text {i+1}: {result.error}")
        
        return results
    
    def _generate_with_retry(
        self, 
        text: str, 
        max_retries: int = 3, 
        **kwargs
    ) -> GenerationResult:
        """Generate with retry logic.
        
        Args:
            text: Input text description
            max_retries: Maximum number of retries
            **kwargs: Additional generation parameters
            
        Returns:
            GenerationResult
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.info(f"Retry attempt {attempt}/{max_retries} for text: {text[:50]}...")
                    # Exponential backoff
                    time.sleep(2 ** (attempt - 1))
                
                result = self.generate(text, **kwargs)
                
                # Update retry count
                result.retry_count = attempt
                
                return result
                
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                
                if attempt == max_retries:
                    # Final attempt failed
                    return GenerationResult(
                        success=False,
                        scenegraph=None,
                        error=f"Failed after {max_retries + 1} attempts: {last_error}",
                        provider=self.name,
                        input_text=text,
                        generation_time=0.0,
                        retry_count=attempt
                    )
        
        # Should never reach here, but just in case
        return GenerationResult(
            success=False,
            scenegraph=None,
            error=f"Unexpected error after retries: {last_error}",
            provider=self.name,
            input_text=text,
            generation_time=0.0,
            retry_count=max_retries
        )
    
    @abstractmethod
    def _validate_config(self) -> bool:
        """Validate the provider configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about this provider.
        
        Returns:
            Dictionary containing provider information
        """
        return {
            'name': self.name,
            'class': self.__class__.__name__,
            'config_valid': self._validate_config(),
            'config_keys': list(self.config.keys()) if self.config else []
        }
    
    def test_connection(self) -> bool:
        """Test if the provider can connect to its service.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to generate a simple test scene graph
            test_text = "A simple test scene with one object."
            result = self.generate(test_text)
            return result.success
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', config={self.config})"


class ProviderRegistry:
    """Registry for managing scene graph generation providers."""
    
    def __init__(self):
        self._providers: Dict[str, type] = {}
    
    def register(self, name: str, provider_class: type):
        """Register a provider class.
        
        Args:
            name: Provider name
            provider_class: Provider class that inherits from BaseGenerator
        """
        if not issubclass(provider_class, BaseGenerator):
            raise ValueError(f"Provider class must inherit from BaseGenerator")
        
        self._providers[name.lower()] = provider_class
        logger.info(f"Registered provider: {name}")
    
    def get_provider(self, name: str, config: Optional[Dict[str, Any]] = None) -> BaseGenerator:
        """Get a provider instance by name.
        
        Args:
            name: Provider name
            config: Optional configuration for the provider
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If provider is not found
        """
        name_lower = name.lower()
        if name_lower not in self._providers:
            available = ', '.join(self._providers.keys())
            raise ValueError(f"Provider '{name}' not found. Available providers: {available}")
        
        provider_class = self._providers[name_lower]
        return provider_class(config=config)
    
    def list_providers(self) -> List[str]:
        """List all registered provider names.
        
        Returns:
            List of provider names
        """
        return list(self._providers.keys())
    
    def is_registered(self, name: str) -> bool:
        """Check if a provider is registered.
        
        Args:
            name: Provider name
            
        Returns:
            True if provider is registered, False otherwise
        """
        return name.lower() in self._providers


# Global provider registry
registry = ProviderRegistry()
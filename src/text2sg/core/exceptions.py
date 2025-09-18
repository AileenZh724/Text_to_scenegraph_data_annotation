"""Custom exceptions for Text2SG.

Provides specific exception types for different error scenarios.
"""

from typing import Optional, Dict, Any


class Text2SGError(Exception):
    """Base exception for all Text2SG errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'context': self.context
        }


class ConfigurationError(Text2SGError):
    """Raised when there's a configuration issue."""
    pass


class ValidationError(Text2SGError):
    """Raised when data validation fails."""
    pass


class FileProcessingError(Text2SGError):
    """Raised when file processing fails."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, 
                 line_number: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.file_path = file_path
        self.line_number = line_number
        if file_path:
            self.context['file_path'] = file_path
        if line_number:
            self.context['line_number'] = line_number


class CSVError(FileProcessingError):
    """Raised when CSV processing fails."""
    pass


class JSONError(FileProcessingError):
    """Raised when JSON processing fails."""
    pass


class APIError(Text2SGError):
    """Raised when API requests fail."""
    
    def __init__(self, message: str, provider: Optional[str] = None,
                 status_code: Optional[int] = None, response_data: Optional[Dict] = None,
                 **kwargs):
        super().__init__(message, **kwargs)
        self.provider = provider
        self.status_code = status_code
        self.response_data = response_data
        
        if provider:
            self.context['provider'] = provider
        if status_code:
            self.context['status_code'] = status_code
        if response_data:
            self.context['response_data'] = response_data


class RateLimitError(APIError):
    """Raised when API rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after
        if retry_after:
            self.context['retry_after'] = retry_after


class AuthenticationError(APIError):
    """Raised when API authentication fails."""
    pass


class QuotaExceededError(APIError):
    """Raised when API quota is exceeded."""
    pass


class GenerationError(Text2SGError):
    """Raised when scene graph generation fails."""
    
    def __init__(self, message: str, input_text: Optional[str] = None,
                 provider: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.input_text = input_text
        self.provider = provider
        
        if input_text:
            self.context['input_text'] = input_text[:200] + '...' if len(input_text) > 200 else input_text
        if provider:
            self.context['provider'] = provider


class ParseError(GenerationError):
    """Raised when parsing generated content fails."""
    
    def __init__(self, message: str, raw_content: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.raw_content = raw_content
        if raw_content:
            self.context['raw_content'] = raw_content[:500] + '...' if len(raw_content) > 500 else raw_content


class ServiceError(Text2SGError):
    """Raised when service operations fail."""
    
    def __init__(self, message: str, service_name: Optional[str] = None,
                 operation: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.service_name = service_name
        self.operation = operation
        
        if service_name:
            self.context['service_name'] = service_name
        if operation:
            self.context['operation'] = operation


class PipelineError(Text2SGError):
    """Raised when pipeline execution fails."""
    
    def __init__(self, message: str, step: Optional[str] = None,
                 completed_steps: Optional[list] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.step = step
        self.completed_steps = completed_steps or []
        
        if step:
            self.context['failed_step'] = step
        if completed_steps:
            self.context['completed_steps'] = completed_steps


# Error handling utilities
def handle_file_error(func):
    """Decorator to handle file-related errors."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            raise FileProcessingError(
                f"File not found: {e.filename}",
                file_path=e.filename,
                error_code="FILE_NOT_FOUND"
            )
        except PermissionError as e:
            raise FileProcessingError(
                f"Permission denied: {e.filename}",
                file_path=e.filename,
                error_code="PERMISSION_DENIED"
            )
        except OSError as e:
            raise FileProcessingError(
                f"OS error: {e}",
                error_code="OS_ERROR"
            )
    return wrapper


def handle_api_error(func):
    """Decorator to handle API-related errors."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Convert common HTTP errors to APIError
            if hasattr(e, 'response'):
                status_code = getattr(e.response, 'status_code', None)
                if status_code == 401:
                    raise AuthenticationError(
                        "API authentication failed",
                        status_code=status_code,
                        error_code="AUTH_FAILED"
                    )
                elif status_code == 429:
                    retry_after = getattr(e.response.headers, 'retry-after', None)
                    raise RateLimitError(
                        "API rate limit exceeded",
                        status_code=status_code,
                        retry_after=int(retry_after) if retry_after else None,
                        error_code="RATE_LIMIT"
                    )
                elif status_code == 403:
                    raise QuotaExceededError(
                        "API quota exceeded",
                        status_code=status_code,
                        error_code="QUOTA_EXCEEDED"
                    )
                else:
                    raise APIError(
                        f"API request failed: {e}",
                        status_code=status_code,
                        error_code="API_ERROR"
                    )
            else:
                raise APIError(f"API error: {e}", error_code="UNKNOWN_API_ERROR")
    return wrapper


def create_error_context(operation: str, **kwargs) -> Dict[str, Any]:
    """Create standardized error context."""
    context = {
        'operation': operation,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }
    context.update(kwargs)
    return context
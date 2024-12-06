from typing import Optional, Dict, Any, Type, Callable
from datetime import datetime
from .policies import RetryPolicy, ExponentialBackoff

class ErrorHandler:
    """Base class for error handling.
    
    Provides consistent error handling, logging, and recovery.
    """
    
    def __init__(self):
        self.errors: list[Dict[str, Any]] = []
        
    def handle(self, error: Exception, context: Dict[str, Any]) -> None:
        """Handle an error with context.
        
        Args:
            error: The error that occurred
            context: Error context (state, step, etc)
        """
        error_info = {
            "type": type(error).__name__,
            "message": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        self.errors.append(error_info)
        
    def get_errors(self) -> list[Dict[str, Any]]:
        """Get list of handled errors."""
        return self.errors
        
    def clear_errors(self) -> None:
        """Clear error history."""
        self.errors = []

class RetryHandler(ErrorHandler):
    """Error handler with retry capabilities.
    
    Supports different retry policies and backoff strategies.
    """
    
    def __init__(
        self,
        retry_policy: Optional[RetryPolicy] = None,
        max_retries: int = 3
    ):
        """Initialize retry handler.
        
        Args:
            retry_policy: Policy for retry behavior
            max_retries: Maximum number of retries
        """
        super().__init__()
        self.retry_policy = retry_policy or ExponentialBackoff()
        self.max_retries = max_retries
        self.retry_counts: Dict[str, int] = {}
        
    def should_retry(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> bool:
        """Determine if operation should be retried.
        
        Args:
            error: The error that occurred
            context: Error context
            
        Returns:
            Whether to retry the operation
        """
        # Get unique operation identifier
        op_id = self._get_operation_id(context)
        current_retries = self.retry_counts.get(op_id, 0)
        
        # Check if we should retry
        if current_retries >= self.max_retries:
            return False
            
        if not self.retry_policy.is_retryable(error):
            return False
            
        # Update retry count
        self.retry_counts[op_id] = current_retries + 1
        return True
        
    def get_delay(self, context: Dict[str, Any]) -> float:
        """Get delay before next retry.
        
        Args:
            context: Error context
            
        Returns:
            Delay in seconds
        """
        op_id = self._get_operation_id(context)
        retry_number = self.retry_counts.get(op_id, 0)
        return self.retry_policy.get_delay(retry_number)
        
    def _get_operation_id(self, context: Dict[str, Any]) -> str:
        """Get unique identifier for operation from context."""
        return f"{context.get('step', '')}_{context.get('node', '')}"
from abc import ABC, abstractmethod
from typing import Type, Set, Optional
import time

class RetryPolicy(ABC):
    """Base class for retry policies.
    
    Defines how and when operations should be retried.
    """
    
    def __init__(
        self,
        retryable_exceptions: Optional[Set[Type[Exception]]] = None
    ):
        """Initialize retry policy.
        
        Args:
            retryable_exceptions: Set of exceptions that can be retried
        """
        self.retryable_exceptions = retryable_exceptions or {
            TimeoutError,
            ConnectionError,
            ValueError  # For testing
        }
    
    def is_retryable(self, error: Exception) -> bool:
        """Check if error is retryable.
        
        Args:
            error: The error to check
            
        Returns:
            Whether error can be retried
        """
        return any(
            isinstance(error, exc)
            for exc in self.retryable_exceptions
        )
    
    @abstractmethod
    def get_delay(self, retry_number: int) -> float:
        """Get delay before next retry.
        
        Args:
            retry_number: Number of retries so far
            
        Returns:
            Delay in seconds
        """
        pass

class ExponentialBackoff(RetryPolicy):
    """Exponential backoff retry policy.
    
    Increases delay exponentially between retries.
    """
    
    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_exceptions: Optional[Set[Type[Exception]]] = None
    ):
        """Initialize exponential backoff policy.
        
        Args:
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential calculation
            retryable_exceptions: Set of retryable exceptions
        """
        super().__init__(retryable_exceptions)
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def get_delay(self, retry_number: int) -> float:
        """Calculate exponential backoff delay.
        
        Args:
            retry_number: Number of retries so far
            
        Returns:
            Delay in seconds
        """
        delay = self.base_delay * (self.exponential_base ** retry_number)
        return min(delay, self.max_delay)

class LinearBackoff(RetryPolicy):
    """Linear backoff retry policy.
    
    Increases delay linearly between retries.
    """
    
    def __init__(
        self,
        base_delay: float = 1.0,
        increment: float = 1.0,
        max_delay: float = 60.0,
        retryable_exceptions: Optional[Set[Type[Exception]]] = None
    ):
        """Initialize linear backoff policy.
        
        Args:
            base_delay: Initial delay in seconds
            increment: Delay increment per retry
            max_delay: Maximum delay in seconds
            retryable_exceptions: Set of retryable exceptions
        """
        super().__init__(retryable_exceptions)
        self.base_delay = base_delay
        self.increment = increment
        self.max_delay = max_delay
    
    def get_delay(self, retry_number: int) -> float:
        """Calculate linear backoff delay.
        
        Args:
            retry_number: Number of retries so far
            
        Returns:
            Delay in seconds
        """
        delay = self.base_delay + (self.increment * retry_number)
        return min(delay, self.max_delay)
import os
import threading
from loguru import logger
from time import sleep

class KeyRotator:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(KeyRotator, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        keys_str = os.getenv("GEMINI_API_KEYS", "")
        self.keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        
        # Fallback to legacy single key if array is empty
        if not self.keys:
            single_key = os.getenv("GEMINI_API_KEY", "")
            if single_key:
                self.keys = [single_key]
                
        if not self.keys:
            logger.warning("No GEMINI_API_KEYS or GEMINI_API_KEY found in environment!")
            
        self.current_index = 0
        self.rotation_lock = threading.Lock()

    def get_current_key(self):
        with self.rotation_lock:
            if not self.keys:
                return None
            return self.keys[self.current_index]

    def advance_key(self):
        with self.rotation_lock:
            if not self.keys:
                return
            self.current_index = (self.current_index + 1) % len(self.keys)
            logger.info(f"API Key rotated. Switched to key index: {self.current_index}")

# Singleton instance
rotator = KeyRotator()

def with_retry(client_factory, execute_func, max_retries=3):
    """
    Orchestrates execution of an API call with automatic 429 failover.
    
    :param client_factory: A lambda/function that instantiates a new client with `rotator.get_current_key()`
    :param execute_func: A lambda/function that takes the client and performs the network call
    :param max_retries: Maximum number of attempts before throwing an exception
    """
    attempts = 0
    last_error = None
    
    while attempts < max_retries:
        client = client_factory()
        
        # Ensure os.environ['GOOGLE_API_KEY'] is set to current key because some LangChain modules check it under the hood
        os.environ['GOOGLE_API_KEY'] = rotator.get_current_key() or ""
        
        try:
            return execute_func(client)
        except Exception as e:
            error_str = str(e).upper()
            last_error = e
            
            # Identify rate limit exhaustion (429 / RESOURCE_EXHAUSTED)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "RATE_LIMIT_EXCEEDED" in error_str:
                attempts += 1
                logger.warning(f"Rate limit hit! Rotating API key and retrying... (Attempt {attempts}/{max_retries})")
                rotator.advance_key()
                sleep(1.0) # Graceful backoff
            else:
                # If it's a different error, raise immediately
                raise e
                
    logger.error("Max retries reached due to consistent API Rate Limits.")
    raise last_error

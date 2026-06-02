import os
import re
import threading
from loguru import logger
from time import sleep

# Ordered list of models to try. Each has its own separate quota pool.
FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash",
]

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
        
        if not self.keys:
            single_key = os.getenv("GEMINI_API_KEY", "")
            if single_key:
                self.keys = [single_key]
                
        if not self.keys:
            logger.warning("No GEMINI_API_KEYS or GEMINI_API_KEY found in environment!")
            
        self.current_index = 0
        self.rotation_lock = threading.Lock()
        
        # Track which models are exhausted for the current minute
        self._exhausted_models = set()

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
            logger.info(f"API Key rotated → index {self.current_index}")

    def mark_model_exhausted(self, model_name: str):
        self._exhausted_models.add(model_name)
        
    def get_fallback_model(self, current_model: str) -> str | None:
        """Return the next model in the fallback chain that isn't exhausted."""
        for m in FALLBACK_MODELS:
            if m != current_model and m not in self._exhausted_models:
                return m
        return None

# Singleton instance
rotator = KeyRotator()

MAX_WAIT_SECONDS = 5

def with_retry(client_factory, execute_func, max_retries=3):
    """
    Orchestrates execution with key rotation and model fallback.
    Fast-fails if all keys are exhausted to avoid user-visible delays.
    """
    attempts = 0
    last_error = None
    
    while attempts < max_retries:
        client = client_factory()
        os.environ['GOOGLE_API_KEY'] = rotator.get_current_key() or ""
        
        try:
            return execute_func(client)
        except Exception as e:
            error_str = str(e).upper()
            last_error = e
            
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "RATE_LIMIT_EXCEEDED" in error_str:
                attempts += 1
                logger.warning(f"Rate limit hit! Rotating key (Attempt {attempts}/{max_retries})")
                rotator.advance_key()
                sleep(min(2.0, MAX_WAIT_SECONDS))
            else:
                raise e
                
    logger.error("All retries exhausted. Raising last error.")
    raise last_error


def with_model_fallback(model_name: str, build_and_call, max_retries=3):
    """
    Try the primary model. If its quota is exhausted, automatically
    fall back to the next model in FALLBACK_MODELS.
    
    :param model_name: The primary model to use (e.g. 'gemini-2.0-flash')
    :param build_and_call: A function(model_name) that builds the client and executes the call.
                           It should raise on failure.
    :param max_retries: retries per model before falling back
    """
    current_model = model_name
    tried_models = set()
    
    while current_model and current_model not in tried_models:
        tried_models.add(current_model)
        attempts = 0
        last_error = None
        
        while attempts < max_retries:
            os.environ['GOOGLE_API_KEY'] = rotator.get_current_key() or ""
            try:
                return build_and_call(current_model)
            except Exception as e:
                error_str = str(e).upper()
                last_error = e
                
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "RATE_LIMIT_EXCEEDED" in error_str:
                    attempts += 1
                    rotator.advance_key()
                    sleep(min(2.0, MAX_WAIT_SECONDS))
                else:
                    raise e
        
        # This model is exhausted, try fallback
        logger.warning(f"Model '{current_model}' quota exhausted. Trying fallback...")
        rotator.mark_model_exhausted(current_model)
        current_model = rotator.get_fallback_model(current_model)
        if current_model:
            logger.info(f"Falling back to model: {current_model}")
    
    logger.error("All models and retries exhausted.")
    raise last_error

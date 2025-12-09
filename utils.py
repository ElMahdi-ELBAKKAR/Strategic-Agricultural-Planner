import time
import logging
import random
import os

# --- 1. Professional Logging Setup ---
def setup_logger(name, log_file='app.log', level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger('AgriDigest')

# --- 2. Rate Limit Handler Class ---
class RateLimitHandler:
    def __init__(self, base_delay=5, max_delay=120):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.last_request_time = 0

    def wait_for_slot(self):
        """Enforces a minimum delay between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.base_delay:
            sleep_time = self.base_delay - elapsed
            logger.info(f"⏳ Rate Limiter: Pausing {sleep_time:.1f}s...")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def handle_429(self, attempt):
        """Exponential backoff with jitter for 429 errors."""
        delay = min(self.max_delay, self.base_delay * (2 ** attempt))
        # Add jitter to prevent synchronized retries
        jitter = random.uniform(0, 0.1 * delay)
        total_delay = delay + jitter
        
        logger.warning(f"⚠️ Rate Limit Hit (429). Backing off for {total_delay:.1f}s...")
        time.sleep(total_delay)

# Global instance
rate_limiter = RateLimitHandler()
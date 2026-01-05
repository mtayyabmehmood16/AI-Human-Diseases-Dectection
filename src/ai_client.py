import google.generativeai as genai
import time
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self, api_key=None, model_name="gemini-2.5-flash"):
        self.api_key = api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
        
        self.model_name = model_name
        self.model = self._get_model()

    def _get_model(self):
        try:
            return genai.GenerativeModel(self.model_name)
        except Exception as e:
            logger.error(f"Error initializing model {self.model_name}: {e}")
            return None

    def generate_content(self, content, retries=3, backoff_factor=2):
        """
        Generates content with automatic retries for rate limit errors (429).
        Content can be a string (prompt) or a list [prompt, image].
        """
        if not self.model:
            return "AI Client Error: Model not initialized."

        delay = 1
        for attempt in range(retries):
            try:
                response = self.model.generate_content(content)
                return response.text.strip()
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower():
                    logger.warning(f"Rate limit hit (attempt {attempt + 1}/{retries}). Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= backoff_factor
                else:
                    logger.error(f"AI Generation Error: {e}")
                    # For non-retriable errors, break and return friendly message
                    return f"AI Error: {str(e)}"
        
        return "AI Unreachable: Rate limit exceeded. Please try again later."

import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from tqdm import tqdm
from loguru import logger
from google.genai.errors import APIError
from utils.api_rotator import rotator, with_retry

class Embedder:
    def __init__(self):
        load_dotenv()
        self.model = os.getenv('EMBEDDING_MODEL', 'text-embedding-004')

    def _get_client(self):
        return genai.Client(api_key=rotator.get_current_key() or "")
    
    def embed_text(self, text: str) -> list[float]:
        """Embed for document storage. Use RETRIEVAL_DOCUMENT task_type."""
        result = with_retry(
            self._get_client,
            lambda client: client.models.embed_content(
                model=self.model,
                contents=text,
                config=types.EmbedContentConfig(task_type='RETRIEVAL_DOCUMENT')
            )
        )
        return result.embeddings[0].values
    
    def embed_query(self, query: str) -> list[float]:
        """Embed for query. Use RETRIEVAL_QUERY task_type."""
        result = with_retry(
            self._get_client,
            lambda client: client.models.embed_content(
                model=self.model,
                contents=query,
                config=types.EmbedContentConfig(task_type='RETRIEVAL_QUERY')
            )
        )
        return result.embeddings[0].values
    
    def embed_batch(self, texts: list[str], batch_size: int = 50) -> list[list[float]]:
        """Process embeddings sequentially with retry logic."""
        all_embeddings = []
        for text in tqdm(texts, desc="Embedding chunks"):
            try:
                emb = self.embed_text(text)
                all_embeddings.append(emb)
            except Exception as ex:
                logger.error(f"Failed to embed text: {ex}")
                all_embeddings.append([0.0]*768) # Placeholder to maintain list alignment
        return all_embeddings

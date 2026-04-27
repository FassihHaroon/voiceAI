"""
Supabase client singleton.
Import `get_db()` in services/routers to get the shared client instance.
"""
from functools import lru_cache
from supabase import create_client, Client
from .config import get_settings
import logging

logger = logging.getLogger(__name__)


@lru_cache
def get_db() -> Client:
    """
    Create and cache a single Supabase client for the lifetime of the process.
    Uses lru_cache so the client is instantiated exactly once.
    """
    settings = get_settings()
    logger.info("Initialising Supabase client → %s", settings.supabase_url)
    client = create_client(settings.supabase_url, settings.supabase_key)
    return client

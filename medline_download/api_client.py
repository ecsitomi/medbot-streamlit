# =============================================================================
# medline_download/api_client.py
# =============================================================================
"""
Medline API kliens teljes tartalom letöltéshez
"""
import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
from .config import MEDLINE_DOWNLOAD_CONFIG

class MedlineFullContentClient:
    """
    Medline API kliens teljes topic tartalom letöltéshez
    """
    
    def __init__(self):
        self.config = MEDLINE_DOWNLOAD_CONFIG["api"]
        self.base_url = self.config["base_url"]
        self.rate_limiter = RateLimiter(self.config["rate_limit"])
        
    async def fetch_topic_content(self, search_term: str, language: str = "en") -> Optional[str]:
        """
        Teljes topic tartalom lekérése XML formátumban
        
        Args:
            search_term: Keresési kifejezés
            language: Nyelv (en/es)
            
        Returns:
            XML string vagy None
        """
        db = "healthTopics" if language == "en" else "healthTopicsSpanish"
        
        params = {
            "db": db,
            "term": search_term,
            "retmax": "1",
            "rettype": "topic",  # Teljes tartalom!
            "tool": self.config["tool_name"],
            "email": self.config["email"]
        }
        
        url = f"{self.base_url}?{urlencode(params)}"
        
        async with aiohttp.ClientSession() as session:
            for attempt in range(self.config["retries"]):
                try:
                    # Rate limiting
                    await self.rate_limiter.acquire()
                    
                    async with session.get(
                        url, 
                        timeout=aiohttp.ClientTimeout(total=self.config["timeout"])
                    ) as response:
                        if response.status == 200:
                            return await response.text()
                        else:
                            print(f"API hiba: {response.status}")
                            
                except asyncio.TimeoutError:
                    print(f"Timeout - próbálkozás {attempt + 1}/{self.config['retries']}")
                except Exception as e:
                    print(f"Hiba: {e}")
                
                if attempt < self.config["retries"] - 1:
                    await asyncio.sleep(2 ** attempt)  # exponential backoff
        
        return None
    
    async def fetch_multiple_topics(self, search_terms: List[str], language: str = "en") -> Dict[str, str]:
        """
        Több topic párhuzamos letöltése
        
        Args:
            search_terms: Keresési kifejezések listája
            language: Nyelv
            
        Returns:
            Dict: {search_term: xml_content}
        """
        tasks = []
        for term in search_terms:
            task = self.fetch_topic_content(term, language)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        return {
            term: content 
            for term, content in zip(search_terms, results) 
            if content is not None
        }

class RateLimiter:
    """Egyszerű rate limiter"""
    
    def __init__(self, max_per_minute: int):
        self.max_per_minute = max_per_minute
        self.calls = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Várakozás ha szükséges a rate limit miatt"""
        async with self.lock:
            now = time.time()
            # Régi hívások eltávolítása
            self.calls = [t for t in self.calls if now - t < 60]
            
            if len(self.calls) >= self.max_per_minute:
                # Várni kell
                sleep_time = 60 - (now - self.calls[0]) + 0.1
                await asyncio.sleep(sleep_time)
                now = time.time()
                self.calls = [t for t in self.calls if now - t < 60]
            
            self.calls.append(now)
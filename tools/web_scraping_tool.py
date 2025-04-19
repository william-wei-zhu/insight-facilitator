from typing import Optional
import requests
from bs4 import BeautifulSoup
import json
from crewai.tools import BaseTool
from utils.retry_utils import retry_on_exception

class EnhancedScrapeWebsiteTool(BaseTool):
    """Tool for scraping website content."""
    
    def __init__(self, 
                 name: Optional[str] = "Enhanced Web Scraping Tool",
                 description: Optional[str] = "Scrape content from a website URL. Use this to get the content of a specific website.",
                 max_content_length: int = 4000):
        # Initialize with the provided parameters
        super().__init__(name=name, description=description)
        # Store max_content_length as an instance attribute
        self._max_content_length = max_content_length
    
    @retry_on_exception(max_retries=1, initial_delay=1.0, backoff_factor=1.5,
                      exception_types=(requests.RequestException,),
                      retry_on_message_patterns=["timeout", "connection", "too many requests"])
    def _run(self, url: str, max_length: Optional[int] = None) -> str:
        """Scrape website content from the URL.
        
        Args:
            url: The URL to scrape content from.
            max_length: Optional override for the maximum content length.
                       If None, uses the instance's max_content_length.
        
        Returns:
            The scraped content as a string.
        """
        # Use the provided max_length or fall back to the instance's max_content_length
        max_content_length = max_length if max_length is not None else self._max_content_length
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Process the text to make it more readable
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Limit the text length to avoid overwhelming the model
            if len(text) > max_content_length:
                text = text[:max_content_length] + "\n\n[Content truncated due to length...]\n"
            
            return f"Content from {url}:\n\n{text}"
            
        except Exception as e:
            return f"Error scraping the website: {str(e)}"
    
    # CrewAI doesn't require an async implementation

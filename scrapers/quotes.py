# scrapers/quotes.py
"""
Scraper for http://quotes.toscrape.com
This site demonstrates pagination and basic structure.
"""

from .base import BaseScraper
from typing import List, Dict, Any
from core.models import Product
from datetime import datetime

class QuotesScraper(BaseScraper):
    """
    Scrapes quotes from Quotes to Scrape.
    Different structure than books - shows adaptability.
    """
    
    def __init__(self):
        super().__init__(headless=True, slow_mo=100)
        self.base_url = "http://quotes.toscrape.com"
        self.site_name = "quotes.toscrape.com"
    
    async def parse_quote(self, quote_element) -> Dict[str, Any]:
        """
        Extract data from a single quote element.
        Each quote is in a <div class="quote"> element.
        """
        try:
            # Extract quote text
            text_element = await quote_element.query_selector(".text")
            text = await text_element.inner_text() if text_element else ""
            # Remove the surrounding quotes
            text = text.strip('“”')
            
            # Extract author
            author_element = await quote_element.query_selector(".author")
            author = await author_element.inner_text() if author_element else "Unknown"
            
            # Extract tags
            tag_elements = await quote_element.query_selector_all(".tag")
            tags = []
            for tag_element in tag_elements:
                tag = await tag_element.inner_text()
                tags.append(tag)
            
            # Extract detail page URL
            about_link = await quote_element.query_selector("a")
            if about_link:
                href = await about_link.get_attribute("href")
                url = f"{self.base_url}{href}"
            else:
                url = ""
            
            # Create a product-like structure (for consistency)
            product = {
                'title': f"Quote by {author}",  # Fake title for compatibility
                'price': 0.0,  # Quotes are free :)
                'url': url,
                'availability': 'Available',
                'rating': len(tags),  # Use tag count as "rating"
                'image_url': None,
                'quote_text': text,  # Additional field
                'author': author,
                'tags': tags,
                'site_name': self.site_name,
                'timestamp': datetime.now()
            }
            
            return product
            
        except Exception as e:
            self.logger.error(f"Error parsing quote: {e}")
            return None
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Main scraping method - handles pagination.
        """
        all_quotes = []
        
        try:
            await self.start_browser()
            
            url = self.base_url
            
            while True:
                self.logger.info(f"Scraping: {url}")
                
                # Navigate to page
                success = await self.safe_goto(url)
                if not success:
                    break
                
                # Wait for quotes to load
                await self.random_delay(1, 2)
                
                # Find all quote elements
                quote_elements = await self.safe_find_elements(".quote")
                
                if not quote_elements:
                    self.logger.info("No quotes found")
                    break
                
                # Parse each quote
                for element in quote_elements:
                    quote = await self.parse_quote(element)
                    if quote:
                        all_quotes.append(quote)
                
                self.logger.info(f"Found {len(quote_elements)} quotes on page")
                
                # Find next page link
                next_element = await self.safe_find_element(".next a")
                if not next_element:
                    self.logger.info("No next page - finished")
                    break
                
                # Get next page URL
                next_href = await next_element.get_attribute("href")
                url = f"{self.base_url}{next_href}"
                
                await self.random_delay(2, 3)
            
            return all_quotes
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            return all_quotes
        finally:
            await self.close_browser()
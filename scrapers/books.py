# scrapers/books.py
"""
Scraper for http://books.toscrape.com
This is a practice site specifically for learning scraping.
"""

from .base import BaseScraper
from typing import List, Dict, Any
from core.models import Product
from datetime import datetime

class BooksScraper(BaseScraper):
    """
    Scrapes book information from Books to Scrape.
    This site is static (no JavaScript) - good for learning.
    """
    
    def __init__(self):
        super().__init__(headless=True, slow_mo=100)
        self.base_url = "http://books.toscrape.com"
        self.site_name = "books.toscrape.com"
    
    async def parse_book(self, book_element) -> Dict[str, Any]:
        """
        Extract data from a single book element.
        Each book is in an <article class="product_pod"> element.
        """
        try:
            # Extract title from h3 > a tag
            title_element = await book_element.query_selector("h3 a")
            title = await title_element.get_attribute("title") if title_element else "No title"
            
            # Extract relative URL and make absolute
            relative_url = await title_element.get_attribute("href") if title_element else ""
            if relative_url:
                # Handle both relative and absolute URLs
                if relative_url.startswith('catalogue/'):
                    url = f"{self.base_url}/{relative_url}"
                else:
                    url = f"{self.base_url}/catalogue/{relative_url}"
            else:
                url = ""
            
            # Extract price
            price_element = await book_element.query_selector(".price_color")
            price_text = await price_element.inner_text() if price_element else "0"
            # Price comes as "£51.77" - extract number
            price = float(price_text.replace('£', '')) if price_text else 0.0
            
            # Extract availability
            avail_element = await book_element.query_selector(".instock.availability")
            availability = "In stock" if avail_element else "Unknown"
            
            # Extract rating (class like "star-rating Three")
            rating_element = await book_element.query_selector(".star-rating")
            if rating_element:
                class_attr = await rating_element.get_attribute("class")
                # Get the second word (e.g., "Three" from "star-rating Three")
                rating_word = class_attr.split()[1] if len(class_attr.split()) > 1 else "Zero"
                # Convert words to numbers
                rating_map = {"Zero": 0, "One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
                rating = rating_map.get(rating_word, 0)
            else:
                rating = 0
            
            # Get image URL
            img_element = await book_element.query_selector("img")
            img_url = await img_element.get_attribute("src") if img_element else ""
            if img_url and not img_url.startswith("http"):
                img_url = f"{self.base_url}/{img_url}"
            
            # Create product dictionary
            product = {
                'title': title.strip(),
                'price': price,
                'url': url,
                'availability': availability,
                'rating': rating,
                'image_url': img_url,
                'site_name': self.site_name,
                'timestamp': datetime.now()
            }
            
            # Validate with Pydantic
            validated = Product(**product)
            return validated.dict()
            
        except Exception as e:
            self.logger.error(f"Error parsing book: {e}")
            return None
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Main scraping method - navigates through all pages.
        """
        all_products = []
        page_num = 1
        
        try:
            await self.start_browser()
            
            while True:
                # Construct page URL
                if page_num == 1:
                    url = f"{self.base_url}/catalogue/page-1.html"
                else:
                    url = f"{self.base_url}/catalogue/page-{page_num}.html"
                
                self.logger.info(f"Scraping page {page_num}: {url}")
                
                # Navigate to page
                success = await self.safe_goto(url)
                if not success:
                    self.logger.info(f"No more pages - reached page {page_num}")
                    break
                
                # Wait for books to load
                await self.random_delay(2, 4)
                
                # Find all book elements
                book_elements = await self.safe_find_elements("article.product_pod")
                
                if not book_elements:
                    self.logger.info(f"No books found on page {page_num}")
                    break
                
                # Parse each book
                for element in book_elements:
                    product = await self.parse_book(element)
                    if product:
                        all_products.append(product)
                
                self.logger.info(f"Found {len(book_elements)} books on page {page_num}")
                
                # Check if there's a next page
                next_button = await self.safe_find_element(".next a")
                if not next_button:
                    self.logger.info("No next button found - last page")
                    break
                
                page_num += 1
                await self.random_delay(1, 2)
            
            return all_products
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            return all_products
        finally:
            await self.close_browser()
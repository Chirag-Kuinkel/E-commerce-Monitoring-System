# scrapers/base.py
"""
Base class that all scrapers inherit from.
Contains common functionality like browser management and error handling.
"""

from playwright.async_api import async_playwright
import asyncio
import random
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)

class BaseScraper:
    """
    Abstract base scraper. Don't use this directly - inherit from it.
    """
    
    def __init__(self, headless=True, slow_mo=50):
        """
        Initialize scraper with settings.
        
        Args:
            headless: Run browser without GUI (faster)
            slow_mo: Slow down operations by ms (helps with detection)
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.logger = logging.getLogger(self.__class__.__name__)
        self.browser = None
        self.context = None
        self.page = None
    
    async def start_browser(self):
        """Launch browser and create new page."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        
        # Set default timeout
        self.page.set_default_timeout(30000)  # 30 seconds
    
    async def close_browser(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def random_delay(self, min_seconds=1, max_seconds=3):
        """Random delay to avoid detection."""
        delay = random.uniform(min_seconds, max_seconds)
        self.logger.info(f"Waiting {delay:.2f} seconds...")
        await asyncio.sleep(delay)
    
    async def safe_goto(self, url: str, retries: int = 3) -> bool:
        """
        Navigate to URL with retry logic.
        Returns True if successful, False otherwise.
        """
        for attempt in range(retries):
            try:
                self.logger.info(f"Navigating to {url} (attempt {attempt + 1})")
                
                # Go to page and wait for network idle
                await self.page.goto(url, wait_until='networkidle')
                
                # Take screenshot for debugging
                await self.page.screenshot(path=f"logs/debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                
                return True
                
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    self.logger.info(f"Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"All {retries} attempts failed for {url}")
                    return False
        
        return False
    
    async def safe_find_element(self, selector: str, timeout: int = 5000):
        """
        Find element with timeout.
        Returns element or None if not found.
        """
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            return element
        except:
            self.logger.warning(f"Element not found: {selector}")
            return None
    
    async def safe_find_elements(self, selector: str):
        """Find all matching elements."""
        try:
            elements = await self.page.query_selector_all(selector)
            return elements
        except Exception as e:
            self.logger.error(f"Error finding elements with {selector}: {e}")
            return []
    
    async def extract_text(self, element, selector: str, default: str = ""):
        """Safely extract text from element."""
        try:
            child = await element.query_selector(selector)
            if child:
                return await child.inner_text()
        except:
            pass
        return default
    
    async def extract_attribute(self, element, selector: str, attribute: str, default: str = ""):
        """Safely extract attribute from element."""
        try:
            child = await element.query_selector(selector)
            if child:
                return await child.get_attribute(attribute)
        except:
            pass
        return default
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Main scraping method - override this in child classes.
        """
        raise NotImplementedError("Subclasses must implement scrape()")
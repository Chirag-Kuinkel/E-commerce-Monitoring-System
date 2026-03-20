# core/models.py
"""
Data models using Pydantic for validation.
Pydantic ensures our data is clean and consistent.
"""

from pydantic import BaseModel, validator, Field
from datetime import datetime
from typing import Optional, List
import re

class Product(BaseModel):
    """
    Represents a product from any e-commerce site.
    All fields are validated when creating a Product.
    """
    # Required fields (must exist)
    title: str = Field(..., min_length=1, description="Product name")
    price: float = Field(..., gt=0, description="Price in USD")
    url: str = Field(..., description="Product page URL")
    
    # Optional fields (might be missing)
    availability: Optional[str] = "Unknown"
    rating: Optional[float] = None
    image_url: Optional[str] = None
    
    # Metadata (we add this)
    site_name: str = Field(..., description="Source website")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @validator('price', pre=True)
    def clean_price(cls, v):
        """
        Convert messy price strings to float.
        Examples: "$29.99" -> 29.99, "1,299 USD" -> 1299.0
        """
        if isinstance(v, (int, float)):
            return float(v)
        
        # Remove currency symbols, commas, and extra text
        cleaned = re.sub(r'[^\d.,]', '', str(v))
        cleaned = cleaned.replace(',', '')
        return float(cleaned)
    
    @validator('rating', pre=True)
    def clean_rating(cls, v):
        """
        Convert rating text to number.
        Example: "4.5 out of 5" -> 4.5
        """
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        
        # Extract first number found
        numbers = re.findall(r'\d+\.?\d*', str(v))
        return float(numbers[0]) if numbers else None

class ScrapeResult(BaseModel):
    """
    Tracks how a scraping run went.
    Useful for monitoring and debugging.
    """
    site_name: str
    success: bool
    products_found: int
    errors: List[str] = []
    execution_time: float
    timestamp: datetime = datetime.now()

class StructureChange(BaseModel):
    """
    Alerts when a website changes its layout.
    This is crucial for maintenance.
    """
    site_name: str
    change_percentage: float
    affected_selectors: List[str]
    suggested_fixes: Optional[str] = None
    timestamp: datetime = datetime.now()
# core/qa_checks.py
"""
Quality Assurance checks that run after scraping.
These catch data issues automatically.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta

class QAChecker:
    def __init__(self, storage):
        self.storage = storage
    
    def check_completeness(self, products: List[Dict]) -> List[str]:
        """
        Ensure all required fields are present.
        Returns list of issues found.
        """
        issues = []
        required_fields = ['title', 'price', 'url']
        
        for i, product in enumerate(products):
            missing = [f for f in required_fields if f not in product]
            if missing:
                issues.append(f"Product {i} missing fields: {missing}")
        
        return issues
    
    def check_price_types(self, products: List[Dict]) -> List[str]:
        """
        Verify prices are valid numbers.
        """
        issues = []
        for product in products:
            price = product.get('price')
            if price is None:
                issues.append(f"Missing price: {product.get('url')}")
            elif not isinstance(price, (int, float)):
                issues.append(f"Invalid price type: {price} at {product.get('url')}")
            elif price <= 0:
                issues.append(f"Non-positive price: {price}")
        
        return issues
    
    def check_duplicates(self, products: List[Dict]) -> List[str]:
        """
        Look for duplicate URLs in the same batch.
        """
        issues = []
        urls_seen = set()
        
        for product in products:
            url = product.get('url')
            if url in urls_seen:
                issues.append(f"Duplicate URL in same batch: {url}")
            urls_seen.add(url)
        
        return issues
    
    def check_price_variance(self, site_name: str, products: List[Dict]) -> List[str]:
        """
        Compare prices with historical data.
        Massive price changes might indicate scraping errors.
        """
        issues = []
        
        # Get yesterday's products
        yesterday = datetime.now() - timedelta(days=1)
        historical = self.storage.get_recent_products(site_name, limit=50)
        
        if not historical:
            return issues  # No historical data yet
        
        # Calculate average price from yesterday
        historical_prices = [p['price'] for p in historical if p.get('price')]
        if not historical_prices:
            return issues
        
        avg_price = sum(historical_prices) / len(historical_prices)
        
        # Check each product's price
        for product in products:
            price = product.get('price')
            if price and avg_price:
                # If price is 10x different from average
                if price > avg_price * 10 or price < avg_price * 0.1:
                    issues.append(
                        f"Unusual price for {product.get('title')}: "
                        f"${price} vs historical avg ${avg_price:.2f}"
                    )
        
        return issues
    
    def run_all_checks(self, site_name: str, products: List[Dict]) -> Dict:
        """
        Run all QA checks and return results.
        """
        issues = []
        
        # Run each check
        issues.extend(self.check_completeness(products))
        issues.extend(self.check_price_types(products))
        issues.extend(self.check_duplicates(products))
        issues.extend(self.check_price_variance(site_name, products))
        
        return {
            'passed': len(issues) == 0,
            'issues': issues,
            'total_products': len(products),
            'timestamp': datetime.now()
        }
# tests/test_qa.py
"""
Pytest tests to verify data quality.
Run with: pytest tests/ -v
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.models import Product
from core.qa_checks import QAChecker
from core.storage import Storage
from datetime import datetime, timedelta

class TestDataQuality:
    """
    Test suite for data quality assurance.
    """
    
    def setup_method(self):
        """Run before each test."""
        self.storage = Storage(":memory:")  # Use in-memory DB for tests
        self.checker = QAChecker(self.storage)
    
    def test_product_validation(self):
        """Test that Product model validates correctly."""
        # Valid product should work
        valid_product = {
            'title': 'Test Book',
            'price': 29.99,
            'url': 'http://example.com/book1',
            'site_name': 'test_site',
            'timestamp': datetime.now()
        }
        
        product = Product(**valid_product)
        assert product.title == 'Test Book'
        assert product.price == 29.99
        
        # Invalid price should be caught
        with pytest.raises(Exception):
            invalid_product = valid_product.copy()
            invalid_product['price'] = 'not a price'
            Product(**invalid_product)
    
    def test_price_cleaning(self):
        """Test that price cleaning works."""
        test_cases = [
            ('$29.99', 29.99),
            ('£51.77', 51.77),
            ('1,299.99', 1299.99),
            ('1.299,99', 1299.99),  # European format
            ('Price: 49.95 USD', 49.95),
            ('49', 49.0),
        ]
        
        for raw_price, expected in test_cases:
            # Create product with raw price
            product = Product(
                title='Test',
                price=raw_price,
                url='http://test.com',
                site_name='test',
                timestamp=datetime.now()
            )
            assert product.price == expected
    
    def test_rating_cleaning(self):
        """Test that rating cleaning works."""
        test_cases = [
            ('4.5 out of 5 stars', 4.5),
            ('5 stars', 5.0),
            ('Rating: 3.8/5', 3.8),
            ('Three', None),  # Should handle words
            (4.5, 4.5),
            (None, None),
        ]
        
        for raw_rating, expected in test_cases:
            if expected is None:
                # Should be okay with None
                product = Product(
                    title='Test',
                    price=10.0,
                    url='http://test.com',
                    rating=raw_rating,
                    site_name='test',
                    timestamp=datetime.now()
                )
                assert product.rating is None
            else:
                product = Product(
                    title='Test',
                    price=10.0,
                    url='http://test.com',
                    rating=raw_rating,
                    site_name='test',
                    timestamp=datetime.now()
                )
                assert product.rating == expected
    
    def test_qa_completeness_check(self):
        """Test that completeness check catches missing fields."""
        products = [
            {'title': 'Product 1', 'price': 10.0, 'url': 'http://url1.com'},
            {'title': 'Product 2', 'price': None, 'url': 'http://url2.com'},  # Missing price
            {'title': 'Product 3', 'url': 'http://url3.com'},  # Missing price entirely
        ]
        
        issues = self.checker.check_completeness(products)
        assert len(issues) == 2  # Two products have issues
        assert 'price' in issues[0] or 'price' in issues[1]
    
    def test_qa_price_types(self):
        """Test that price type check works."""
        products = [
            {'title': 'Product 1', 'price': 10.0, 'url': 'http://url1.com'},
            {'title': 'Product 2', 'price': -5.0, 'url': 'http://url2.com'},  # Negative
            {'title': 'Product 3', 'price': 'free', 'url': 'http://url3.com'},  # Not a number
            {'title': 'Product 4', 'url': 'http://url4.com'},  # Missing
        ]
        
        issues = self.checker.check_price_types(products)
        assert len(issues) >= 3  # Should find 3+ issues
    
    def test_qa_duplicate_check(self):
        """Test that duplicate detection works."""
        products = [
            {'title': 'Product 1', 'price': 10.0, 'url': 'http://same.com'},
            {'title': 'Product 2', 'price': 20.0, 'url': 'http://same.com'},  # Duplicate URL
            {'title': 'Product 3', 'price': 30.0, 'url': 'http://unique.com'},
        ]
        
        issues = self.checker.check_duplicates(products)
        assert len(issues) == 1
        assert 'Duplicate URL' in issues[0]
    
    def test_qa_price_variance(self):
        """Test that price variance detection works."""
        # First, save some historical data
        historical = [
            {'title': 'Product 1', 'price': 100.0, 'url': 'http://p1.com', 
             'site_name': 'test_site', 'timestamp': datetime.now() - timedelta(days=1)},
            {'title': 'Product 2', 'price': 110.0, 'url': 'http://p2.com',
             'site_name': 'test_site', 'timestamp': datetime.now() - timedelta(days=1)},
            {'title': 'Product 3', 'price': 90.0, 'url': 'http://p3.com',
             'site_name': 'test_site', 'timestamp': datetime.now() - timedelta(days=1)},
        ]
        
        for p in historical:
            self.storage.save_products([p])
        
        # Now test with new data
        current = [
            {'title': 'Product 1', 'price': 2000.0, 'url': 'http://p1.com',  # 20x increase!
             'site_name': 'test_site', 'timestamp': datetime.now()},
        ]
        
        issues = self.checker.check_price_variance('test_site', current)
        assert len(issues) >= 1
        assert 'Unusual price' in issues[0]
    
    def test_full_qa_run(self):
        """Test running all checks together."""
        products = [
            {'title': 'Product 1', 'price': 10.0, 'url': 'http://url1.com'},
            {'title': 'Product 2', 'price': 20.0, 'url': 'http://url2.com'},
        ]
        
        results = self.checker.run_all_checks('test_site', products)
        assert 'passed' in results
        assert 'issues' in results
        assert 'total_products' in results
        assert results['total_products'] == 2

if __name__ == '__main__':
    pytest.main(['-v', __file__])
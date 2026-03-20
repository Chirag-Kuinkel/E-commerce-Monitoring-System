# core/storage.py
"""
Handles all database operations using SQLite.
SQLite is perfect for projects like this - no server needed.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from core.models import ScrapeResult

class Storage:
    def __init__(self, db_path="data/scraper.db"):
        """
        Initialize database connection.
        Creates the database file if it doesn't exist.
        """
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """
        Create tables if they don't exist.
        This runs once when Storage is first created.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    price REAL NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    availability TEXT,
                    rating REAL,
                    image_url TEXT,
                    site_name TEXT NOT NULL,
                    timestamp DATETIME NOT NULL
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_site_timestamp 
                ON products(site_name, timestamp)
            """)
            
            # Scrape runs table (for monitoring)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scrape_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_name TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    products_found INTEGER,
                    errors TEXT,
                    execution_time REAL,
                    timestamp DATETIME NOT NULL
                )
            """)
            
            conn.commit()
    
    def save_products(self, products: List[Dict[str, Any]]) -> int:
        """
        Save multiple products to database.
        Returns number of products saved.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            saved_count = 0
            
            for product in products:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO products 
                        (title, price, url, availability, rating, 
                         image_url, site_name, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product['title'],
                        product['price'],
                        product['url'],
                        product.get('availability', 'Unknown'),
                        product.get('rating'),
                        product.get('image_url'),
                        product['site_name'],
                        product['timestamp']
                    ))
                    if cursor.rowcount > 0:
                        saved_count += 1
                except Exception as e:
                    print(f"Error saving product {product.get('url')}: {e}")
            
            conn.commit()
            return saved_count
    
    def save_scrape_run(self, result: ScrapeResult):
        """Save metrics about a scraping run."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scrape_runs 
                (site_name, success, products_found, errors, execution_time, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                result.site_name,
                result.success,
                result.products_found,
                json.dumps(result.errors),  # Store list as JSON
                result.execution_time,
                result.timestamp
            ))
            conn.commit()
    
    def get_recent_products(self, site_name: str, limit: int = 100) -> List[Dict]:
        """Get most recent products from a site."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # This lets us access columns by name
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM products 
                WHERE site_name = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (site_name, limit))
            
            return [dict(row) for row in cursor.fetchall()]
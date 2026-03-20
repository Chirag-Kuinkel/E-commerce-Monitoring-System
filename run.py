# run.py
"""
Main entry point - runs all scrapers and QA checks.
"""

import asyncio
import argparse
from datetime import datetime
import json
from pathlib import Path

from scrapers.books import BooksScraper
from scrapers.quotes import QuotesScraper
from core.storage import Storage
from core.qa_checks import QAChecker
from core.detector import StructureDetector
from core.models import ScrapeResult

async def run_scraper(scraper_class, name):
    """
    Run a single scraper and return results.
    """
    print(f"\n{'='*50}")
    print(f"Starting {name} scraper...")
    print(f"{'='*50}")
    
    scraper = scraper_class()
    start_time = datetime.now()
    
    try:
        products = await scraper.scrape()
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ {name} scraper finished")
        print(f"Found: {len(products)} items")
        print(f"Time: {execution_time:.2f} seconds")
        
        return {
            'success': True,
            'products': products,
            'execution_time': execution_time,
            'errors': []
        }
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        print(f"\n❌ {name} scraper failed: {e}")
        
        return {
            'success': False,
            'products': [],
            'execution_time': execution_time,
            'errors': [str(e)]
        }

async def main():
    """
    Main function that orchestrates everything.
    """
    parser = argparse.ArgumentParser(description='Run e-commerce scrapers')
    parser.add_argument('--scraper', choices=['books', 'quotes', 'all'], 
                       default='all', help='Which scraper to run')
    parser.add_argument('--save-baseline', action='store_true',
                       help='Save HTML baseline for structure detection')
    args = parser.parse_args()
    
    # Initialize components
    storage = Storage()
    qa_checker = QAChecker(storage)
    
    # Define which scrapers to run
    scrapers_to_run = []
    if args.scraper in ['books', 'all']:
        scrapers_to_run.append(('Books', BooksScraper))
    if args.scraper in ['quotes', 'all']:
        scrapers_to_run.append(('Quotes', QuotesScraper))
    
    # Run scrapers
    all_results = []
    for name, scraper_class in scrapers_to_run:
        result = await run_scraper(scraper_class, name)
        all_results.append((name, result))
        
        # Save products if successful
        if result['success'] and result['products']:
            saved = storage.save_products(result['products'])
            print(f"Saved {saved} new items to database")
            
            # Run QA checks
            qa_results = qa_checker.run_all_checks(name, result['products'])
            print(f"\nQA Check Results for {name}:")
            print(f"  Passed: {qa_results['passed']}")
            if qa_results['issues']:
                print(f"  Issues ({len(qa_results['issues'])}):")
                for issue in qa_results['issues'][:5]:  # Show first 5
                    print(f"    - {issue}")
        
        # Save scrape run record
        scrape_result = ScrapeResult(
            site_name=name,
            success=result['success'],
            products_found=len(result['products']),
            errors=result['errors'],
            execution_time=result['execution_time']
        )
        storage.save_scrape_run(scrape_result)
    
    # Print summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    
    total_products = sum(len(r['products']) for _, r in all_results)
    total_time = sum(r['execution_time'] for _, r in all_results)
    
    print(f"Total products: {total_products}")
    print(f"Total time: {total_time:.2f} seconds")
    
    # Check database stats
    for name, _ in scrapers_to_run:
        recent = storage.get_recent_products(name.lower(), limit=5)
        print(f"\nRecent {name} items in database: {len(recent)}")

if __name__ == "__main__":
    asyncio.run(main())
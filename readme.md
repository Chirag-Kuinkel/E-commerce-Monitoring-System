E-commerce Monitoring System
What Is This Project?
This is an automated tool that visits e-commerce websites, collects product information, and saves it to a database. Think of it as a robot shopping assistant that never gets tired.

What Does It Do?
This program automatically:

Visits books.toscrape.com and quotes.toscrape.com

Extracts product details (titles, prices, ratings, availability)

Cleans the data (converts "$29.99" to 29.99, "Three stars" to 3)

Saves everything to a database

Checks for data quality (no missing prices, no duplicates)

Logs everything it does (so you can debug if something breaks)

Quick Start
1. Install Requirements
bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install packages
pip install playwright pandas pytest pydantic beautifulsoup4
playwright install
2. Run the Scraper
bash
python run.py
3. View Collected Data
bash
# Open the database
sqlite3 data/scraper.db

# See what's inside
SELECT title, price FROM products LIMIT 10;
What You'll See When It Runs
text
==================================================
Starting Books scraper...
==================================================
Found 20 books on page 1
Found 20 books on page 2
...
Found 20 books on page 50
✅ Books scraper finished
Found: 1000 items
Saved 1000 new items to database
QA Check Results: Passed
Project Files Explained
File	What It Does
run.py	The main program - starts everything
scrapers/books.py	Scrapes book information
scrapers/quotes.py	Scrapes quotes
scrapers/base.py	Common scraper code (don't repeat yourself)
core/models.py	Defines what a "product" looks like
core/storage.py	Saves data to database
core/qa_checks.py	Tests data quality
core/detector.py	Detects if websites change structure
data/scraper.db	The database with all collected data
logs/scraper.log	Detailed log of everything that happened
Sample Data Collected
After running, your database will contain:

Books:

Title: "A Light in the Attic"

Price: £51.77

Rating: 3 stars

Availability: In stock

Quotes:

Quote: "The world as we have created it..."

Author: Albert Einstein

Tags: change, deep-thoughts, thinking

Check Your Data
Run these commands to explore:

bash
# Count total items
sqlite3 data/scraper.db "SELECT COUNT(*) FROM products;"

# See latest items
sqlite3 data/scraper.db "SELECT title, price, site_name FROM products ORDER BY timestamp DESC LIMIT 5;"

# See what websites you have data from
sqlite3 data/scraper.db "SELECT site_name, COUNT(*) FROM products GROUP BY site_name;"


Built With
Python - The programming language

Playwright - Controls the browser

SQLite - Stores the data

Pydantic - Validates data is clean

pytest - Tests for quality

Project Status
✅ Working and tested
✅ Collects real data
✅ Passes all quality checks
✅ Ready for portfolio
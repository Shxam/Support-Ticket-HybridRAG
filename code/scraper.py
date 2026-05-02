"""
Web scraper for support documentation.

Crawls support pages from HackerRank, Claude, and Visa domains.
Saves each page as a text file tagged with its domain.
"""

import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, List
from config import (
    DOMAIN_URLS,
    DATA_DIR,
    SCRAPER_MAX_PAGES,
    SCRAPER_TIMEOUT,
    DOMAINS
)


def is_valid_url(url: str, base_domain: str) -> bool:
    """
    Check if URL is valid and belongs to the base domain.
    
    Args:
        url: URL to validate
        base_domain: Base domain to check against
        
    Returns:
        True if URL is valid and within domain
    """
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and base_domain in parsed.netloc
    except:
        return False


def extract_text_from_page(html: str) -> str:
    """
    Extract clean text content from HTML.
    
    Args:
        html: Raw HTML content
        
    Returns:
        Cleaned text content
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.decompose()
    
    # Get text
    text = soup.get_text()
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text


def extract_links(html: str, base_url: str) -> List[str]:
    """
    Extract all links from HTML page.
    
    Args:
        html: Raw HTML content
        base_url: Base URL for resolving relative links
        
    Returns:
        List of absolute URLs
    """
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    
    for link in soup.find_all('a', href=True):
        absolute_url = urljoin(base_url, link['href'])
        links.append(absolute_url)
    
    return links


def crawl_domain(domain_name: str, start_url: str, max_pages: int = SCRAPER_MAX_PAGES) -> int:
    """
    Crawl a support domain and save pages as text files.
    
    Args:
        domain_name: Name of domain (hackerrank, claude, visa)
        start_url: Starting URL for crawl
        max_pages: Maximum number of pages to crawl
        
    Returns:
        Number of pages successfully scraped
    """
    print(f"\n[SCRAPER] Starting crawl for {domain_name}")
    print(f"[SCRAPER] Start URL: {start_url}")
    
    # Create output directory
    output_dir = os.path.join(DATA_DIR, domain_name)
    os.makedirs(output_dir, exist_ok=True)
    
    visited: Set[str] = set()
    to_visit: List[str] = [start_url]
    pages_scraped = 0
    
    # Extract base domain for validation
    base_domain = urlparse(start_url).netloc
    
    while to_visit and pages_scraped < max_pages:
        url = to_visit.pop(0)
        
        # Skip if already visited
        if url in visited:
            continue
        
        # Skip if not valid domain
        if not is_valid_url(url, base_domain):
            continue
        
        try:
            print(f"[SCRAPER] Fetching ({pages_scraped + 1}/{max_pages}): {url[:80]}...")
            
            # Fetch page
            response = requests.get(url, timeout=SCRAPER_TIMEOUT, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            visited.add(url)
            
            # Extract text content
            text_content = extract_text_from_page(response.text)
            
            # Skip if page has too little content
            if len(text_content) < 100:
                continue
            
            # Save to file
            filename = f"page_{pages_scraped:04d}.txt"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write(f"DOMAIN: {domain_name}\n")
                f.write("=" * 80 + "\n\n")
                f.write(text_content)
            
            pages_scraped += 1
            
            # Extract and queue new links
            if pages_scraped < max_pages:
                links = extract_links(response.text, url)
                for link in links:
                    if link not in visited and link not in to_visit:
                        to_visit.append(link)
            
            # Be polite - rate limit
            time.sleep(0.5)
        
        except Exception as e:
            print(f"[SCRAPER] Error fetching {url}: {str(e)}")
            continue
    
    print(f"[SCRAPER] Completed {domain_name}: {pages_scraped} pages scraped")
    return pages_scraped


def scrape_all_domains():
    """
    Scrape all configured support domains.
    
    Main entry point for scraping process.
    """
    print("=" * 80)
    print("SUPPORT DOCUMENTATION SCRAPER")
    print("=" * 80)
    
    total_pages = 0
    
    for domain in DOMAINS:
        if domain in DOMAIN_URLS:
            start_url = DOMAIN_URLS[domain]
            pages = crawl_domain(domain, start_url)
            total_pages += pages
        else:
            print(f"[SCRAPER] Warning: No URL configured for domain '{domain}'")
    
    print("\n" + "=" * 80)
    print(f"SCRAPING COMPLETE: {total_pages} total pages scraped")
    print("=" * 80)


if __name__ == "__main__":
    scrape_all_domains()

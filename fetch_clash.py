#!/usr/bin/env python3
"""Fetch latest Clash Meta config from yudou789.top and save as clash.yaml"""

import requests
import re
import yaml
from datetime import datetime, timedelta
from pathlib import Path

YUDOU_URL = "https://www.yudou789.top/category/jiedian"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch_article_links():
    """Fetch article links from yudou789.top"""
    resp = requests.get(YUDOU_URL, headers=HEADERS, timeout=30)
    resp.encoding = 'utf-8'
    # Find article links like /1234.html
    links = re.findall(r'href="https://www\.yudou789\.top/(\d+)\.html"', resp.text)
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for l in links:
        if l not in seen:
            seen.add(l)
            unique.append(l)
    print(f"Found {len(unique)} articles")
    return unique

def extract_clash_url(article_id):
    """Extract Clash Meta YAML URL from an article page"""
    url = f"https://www.yudou789.top/{article_id}.html"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.encoding = 'utf-8'
    # Find YAML subscription URL
    # Pattern: https://hh.yudou226.top/YYYYMM/YYYYMMDDxxx.yaml
    yaml_urls = re.findall(r'https://hh\.yudou226\.top/\d{6}/\w+\.yaml', resp.text)
    if yaml_urls:
        print(f"Article {article_id}: Found YAML URL: {yaml_urls[0]}")
        return yaml_urls[0]
    print(f"Article {article_id}: No YAML URL found")
    return None

def download_config(yaml_url):
    """Download and validate Clash config"""
    resp = requests.get(yaml_url, headers=HEADERS, timeout=60)
    resp.encoding = 'utf-8'
    text = resp.text
    
    # Validate it's a proper Clash config
    if 'proxies:' not in text or 'proxy-groups:' not in text:
        print(f"Warning: Config might be invalid (missing proxies or proxy-groups)")
        return None
    
    # Count nodes
    try:
        cfg = yaml.safe_load(text)
        proxies = cfg.get('proxies', [])
        types = {}
        for p in proxies:
            t = p.get('type', '?')
            types[t] = types.get(t, 0) + 1
        print(f"Config valid: {len(proxies)} nodes - {types}")
    except Exception as e:
        print(f"YAML parse warning: {e}")
    
    # Ensure UTF-8
    output = text.encode('utf-8').decode('utf-8')
    return output

def main():
    print(f"=== Fetch Clash Config {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    
    # Step 1: Get article links
    articles = fetch_article_links()
    if not articles:
        print("ERROR: No articles found")
        return False
    
    # Step 2: Try articles in order (newest first) to find a working config
    for article_id in articles[:5]:  # Try up to 5 articles
        yaml_url = extract_clash_url(article_id)
        if not yaml_url:
            continue
        
        config = download_config(yaml_url)
        if config and len(config) > 1000:
            # Save to file
            Path("clash.yaml").write_text(config, encoding='utf-8')
            print(f"SUCCESS: Saved clash.yaml ({len(config)} bytes)")
            return True
        else:
            print(f"Article {article_id}: Config too small or invalid, trying next...")
    
    print("ERROR: Could not find a valid config from any article")
    return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)

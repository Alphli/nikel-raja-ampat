# -*- coding: utf-8 -*-
"""
Script Crawling Berita v8.4 - Test Mode (1 Article per Keyword)
"""

import pandas as pd
import time
import os
import logging
from newspaper import Article, Config
import nltk
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from typing import List, Dict, Optional
import hashlib
from tqdm import tqdm
from pygooglenews import GoogleNews

# --- Import Selenium ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

# --- Setup Logging ---
os.makedirs('data/logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/crawler.log', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Inisialisasi NLTK ---
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("Downloading NLTK 'punkt' package...")
    nltk.download('punkt', quiet=True)

# --- Import Keywords ---
try:
    from keywords import SEARCH_KEYWORDS
except ImportError:
    logger.error("File 'keywords.py' tidak ditemukan!")
    exit()

# ==============================================================================
# === KONFIGURASI UTAMA ===
# ==============================================================================
START_DATE = "2023-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")
BASE_DELAY = 3
MAX_DELAY = 30
NAMA_FILE_OUTPUT = "hasil_crawling_test"
MAX_WORKERS = 3
BATCH_SIZE = 10
MAX_RETRIES = 3
TIMEOUT = 30
MIN_TEXT_LENGTH = 150
ENABLE_JAVASCRIPT = True

# --- PERUBAHAN: Tambahkan limit artikel per keyword ---
LIMIT_ARTICLES_PER_KEYWORD = 100
# ==============================================================================

# Konfigurasi untuk newspaper4k
NP_CONFIG = Config()
NP_CONFIG.fetch_images = False
NP_CONFIG.memoize_articles = False
NP_CONFIG.request_timeout = 15

# --- DECORATOR & HELPER FUNCTIONS ---
def retry_with_backoff(max_retries=MAX_RETRIES, backoff_base=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Max retries reached for {func.__name__}: {e}")
                        return None
                    wait_time = min(backoff_base ** attempt + random.uniform(0, 1), MAX_DELAY)
                    logger.warning(f"Attempt {attempt + 1} for {func.__name__} failed, retrying in {wait_time:.2f}s...")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator

def create_driver() -> webdriver.Chrome:
    """Membuat instance driver Chrome baru dengan setelan optimal."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.page_load_strategy = 'eager'
    if not ENABLE_JAVASCRIPT:
        chrome_options.add_argument("--disable-javascript")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(TIMEOUT)
    return driver

def generate_content_hash(text: str) -> str:
    """Generate hash for content deduplication."""
    return hashlib.md5(text.encode()).hexdigest()

def validate_article_data(article_data: Dict) -> bool:
    """Validate if article data meets minimum requirements."""
    if not article_data: return False
    text = article_data.get('teks_berita', '')
    title = article_data.get('judul', '')
    if len(text) < MIN_TEXT_LENGTH or not title: return False
    if text and len(text) > 100 and text.count(text[:100]) > 2: return False
    return True

# --- MAIN FUNCTIONS ---

@retry_with_backoff(max_retries=2)
def scout_with_pygooglenews(keyword: str, start_date: str, end_date: str) -> List[Dict]:
    """Phase 1: Scout news using pygooglenews with retry logic."""
    logger.info(f"Searching for keyword: '{keyword}'...")
    gn = GoogleNews(lang='id', country='ID')
    
    search_result = gn.search(keyword, from_=start_date, to_=end_date)
    
    if not search_result.get('entries'):
        logger.info(f"No results found for '{keyword}'")
        return []
    
    articles = []
    # --- PERUBAHAN: Terapkan limit dengan slicing [:LIMIT_ARTICLES_PER_KEYWORD] ---
    for entry in search_result['entries'][:LIMIT_ARTICLES_PER_KEYWORD]:
        article = {
            'title': entry.title,
            'source': entry.source.get('title', 'Unknown'),
            'date': entry.published,
            'url': entry.link,
            'keyword': keyword
        }
        articles.append(article)
    
    logger.info(f"Found {len(articles)} articles for '{keyword}' (limited to {LIMIT_ARTICLES_PER_KEYWORD})")
    return articles

def analyze_article_with_selenium(article_info: Dict) -> Optional[Dict]:
    """Phase 2 & 3: Use Selenium to download and newspaper4k to parse."""
    url = article_info['url']
    driver = None
    try:
        driver = create_driver()
        logger.debug(f"Visiting: {url[:70]}...")
        driver.get(url)
        time.sleep(random.uniform(1, 3))
        html = driver.page_source
        
        article = Article(url, config=NP_CONFIG)
        article.html = html
        article.parse()
        
        result = {
            'keyword_pencarian': article_info['keyword'],
            'sumber': article_info['source'],
            'tanggal_publikasi': article.publish_date or article_info['date'],
            'judul': article.title or article_info['title'],
            'penulis': ', '.join(article.authors) if article.authors else '',
            'url': url,
            'teks_berita': article.text,
            'content_hash': generate_content_hash(article.text or '')
        }
        
        if not validate_article_data(result):
            logger.warning(f"Article failed validation: {url[:70]}")
            return None
        
        logger.info(f"Successfully processed: {url[:70]}")
        return result
    except TimeoutException:
        logger.error(f"Timeout loading: {url[:70]}")
        return None
    except Exception as e:
        logger.error(f"Error processing {url[:70]}: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def process_articles_batch(articles: List[Dict], max_workers: int = MAX_WORKERS) -> List[Dict]:
    """Process articles in parallel with ThreadPoolExecutor."""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_article = {executor.submit(analyze_article_with_selenium, article): article for article in articles}
        with tqdm(total=len(articles), desc="Processing articles") as pbar:
            for future in as_completed(future_to_article):
                try:
                    result = future.result(timeout=TIMEOUT + 10)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"A task in the batch failed: {e}")
                finally:
                    pbar.update(1)
    return results

def deduplicate_results(results: List[Dict]) -> List[Dict]:
    """Remove duplicate articles based on content hash and URL."""
    seen_hashes, seen_urls, unique_results = set(), set(), []
    for result in results:
        content_hash, url = result.get('content_hash'), result.get('url')
        if content_hash not in seen_hashes and url not in seen_urls:
            seen_hashes.add(content_hash)
            seen_urls.add(url)
            unique_results.append(result)
        else:
            logger.debug(f"Duplicate removed: {url[:70]}")
    return unique_results

def save_checkpoint(data: List[Dict], checkpoint_name: str = "checkpoint"):
    """Save intermediate results as checkpoint."""
    if data:
        df = pd.DataFrame(data)
        output_dir = os.path.join('data', 'raw')
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{checkpoint_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        logger.info(f"Checkpoint saved: {filepath}")

# =================================================
# MAIN SCRIPT
# =================================================
if __name__ == "__main__":
    start_time = time.time()
    logger.info("="*60)
    logger.info("Starting Optimized News Crawler v8.4 (Test Mode)")
    logger.info(f"Date range: {START_DATE} to {END_DATE}")
    logger.info(f"Keywords: {len(SEARCH_KEYWORDS)}")
    logger.info(f"Article limit per keyword: {LIMIT_ARTICLES_PER_KEYWORD}")
    logger.info("="*60)
    
    # PHASE 1: Scouting
    all_potential_articles = []
    for i, keyword in enumerate(SEARCH_KEYWORDS):
        results = scout_with_pygooglenews(keyword, START_DATE, END_DATE)
        if results:
            all_potential_articles.extend(results)
        if i < len(SEARCH_KEYWORDS) - 1:
            delay = random.uniform(BASE_DELAY, BASE_DELAY + 2)
            logger.debug(f"Waiting {delay:.2f} seconds before next search...")
            time.sleep(delay)
    
    logger.info(f"Phase 1 complete: Found {len(all_potential_articles)} potential articles")
    
    unique_articles_map = {article['url']: article for article in all_potential_articles}
    unique_articles_list = list(unique_articles_map.values())
    logger.info(f"After URL deduplication: {len(unique_articles_list)} unique articles")
    
    # PHASE 2 & 3: Analysis
    if not unique_articles_list:
        logger.warning("No articles to process. Exiting...")
        exit()
    
    logger.info("Starting article analysis phase...")
    final_results = []
    
    for i in range(0, len(unique_articles_list), BATCH_SIZE):
        batch = unique_articles_list[i:i+BATCH_SIZE]
        logger.info(f"Processing batch {i//BATCH_SIZE + 1}/{(len(unique_articles_list)-1)//BATCH_SIZE + 1}")
        
        batch_results = process_articles_batch(batch, max_workers=MAX_WORKERS)
        final_results.extend(batch_results)
        
        if (i//BATCH_SIZE + 1) % 5 == 0:
            save_checkpoint(final_results, "batch_checkpoint")
    
    # PHASE 4: Final deduplication and saving
    logger.info("Performing final deduplication...")
    final_results = deduplicate_results(final_results)
    
    if not final_results:
        logger.error("No articles successfully processed")
    else:
        for result in final_results:
            result.pop('content_hash', None)
        
        df = pd.DataFrame(final_results)
        
        # --- PERBAIKAN DI SINI ---
        # 1. Konversi semua tanggal ke UTC (menyeragamkan data)
        # 2. Hapus informasi timezone agar bisa disimpan ke Excel
        df['tanggal_publikasi'] = pd.to_datetime(df['tanggal_publikasi'], errors='coerce', utc=True).dt.tz_localize(None)
        # -------------------------
        
        # Lanjutkan dengan mengurutkan data
        df = df.sort_values(by='tanggal_publikasi', ascending=False)
        
        output_dir = os.path.join('data', 'raw')
        os.makedirs(output_dir, exist_ok=True)
        
        csv_path = os.path.join(output_dir, f"{NAMA_FILE_OUTPUT}.csv")
        excel_path = os.path.join(output_dir, f"{NAMA_FILE_OUTPUT}.xlsx")

        # Save to CSV
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # Save to Excel
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Articles', index=False)
            worksheet = writer.sheets['Articles']
            for column in df:
                column_length = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_length + 2, 50)
        
        logger.info("="*60)
        logger.info(f"✅ SUCCESS! Processed {len(df)} articles")
        logger.info(f"📁 Saved to: {csv_path} and {excel_path}")
        
        print("\n📊 Summary Statistics:")
        print(f"  - Total articles: {len(df)}")
        print(f"  - Articles by source: \n{df['sumber'].value_counts().head(10)}")
        print(f"  - Articles by keyword: \n{df['keyword_pencarian'].value_counts()}")
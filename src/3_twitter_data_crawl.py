# -*- coding: utf-8 -*-
"""
Twitter Crawler v2.1
- Mampu memproses beberapa kata kunci dalam satu kali jalan.
- Perbaikan untuk 'tweets_data is not defined'.
"""
import pandas as pd
import time
import os
import random
from datetime import datetime

# --- Import Selenium ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- Impor Konfigurasi ---
try:
    from config_x import TWITTER_USERNAME, TWITTER_PASSWORD
    from keywords_twitter import SEARCH_QUERIES 
except ImportError:
    print("❌ Error: Pastikan file 'config_x.py' dan 'keywords_twitter.py' sudah ada.")
    exit()

# ==============================================================================
# === KONFIGURASI UTAMA ===
# ==============================================================================
MAX_TWEETS_TO_SCRAPE = 250
DELAY_PER_SCROLL = 15
NAMA_FILE_OUTPUT = "hasil_crawling_twitter_multi"
# ==============================================================================

def create_driver() -> webdriver.Chrome:
    """Mempersiapkan dan membuat instance Chrome Driver."""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login(driver: webdriver.Chrome, username: str, password: str) -> bool:
    """Membuka browser dan melakukan login otomatis yang andal."""
    print("🚀 Memulai proses login...")
    try:
        driver.get("https://twitter.com/login")
        
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "text"))
        )
        username_field.send_keys(username)
        driver.find_element(By.XPATH, "//span[contains(text(),'Next')]").click()
        
        password_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys(password)
        driver.find_element(By.XPATH, "//span[contains(text(),'Log in')]").click()
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-testid="SideNav_NewTweet_Button"]'))
        )
        print("✅ Login Berhasil!")
        return True
    except TimeoutException:
        print("❌ Gagal login: Waktu tunggu habis saat mencari elemen login.")
        return False
    except Exception as e:
        print(f"❌ Gagal login: Terjadi error tak terduga - {e}")
        return False

def scrape_tweets(driver: webdriver.Chrome, query: str, max_tweets: int, delay: int) -> list:
    """Logika utama untuk mencari, scrolling, dan ekstraksi data tweet."""
    print(f"\n🔎 Memulai pencarian untuk: '{query}'")
    search_url = f"https://twitter.com/search?q={query.replace(' ', '%20')}&src=typed_query&f=live"
    driver.get(search_url)

    # --- PERBAIKAN: Inisialisasi variabel di sini ---
    tweets_data = []
    # ---------------------------------------------
    seen_tweets = set()
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    print(f"Mengumpulkan hingga {max_tweets} tweet. Jeda antar scroll: {delay} detik.")
    
    while len(tweets_data) < max_tweets:
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
            )
        except TimeoutException:
            print("🟡 Tidak ada tweet yang dimuat setelah scroll. Mungkin sudah mencapai akhir.")
            break

        tweet_elements = driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
        
        new_tweets_found = 0
        for tweet in tweet_elements:
            try:
                tweet_text_element = tweet.find_element(By.CSS_SELECTOR, 'div[data-testid="tweetText"]')
                tweet_text = tweet_text_element.text
                
                if tweet_text not in seen_tweets:
                    seen_tweets.add(tweet_text)
                    new_tweets_found += 1
                    
                    user_handle_element = tweet.find_element(By.CSS_SELECTOR, 'div[data-testid="User-Name"] span')
                    
                    tweets_data.append({
                        "username": user_handle_element.text,
                        "timestamp": tweet.find_element(By.TAG_NAME, 'time').get_attribute('datetime'),
                        "text": tweet_text,
                    })
                    
                    if len(tweets_data) >= max_tweets:
                        break
            except:
                continue

        if len(tweets_data) >= max_tweets:
            print(f"Target {max_tweets} tweet telah tercapai.")
            break
            
        print(f"   -> Ditemukan {new_tweets_found} tweet baru. Total terkumpul: {len(tweets_data)}. Scrolling ke bawah...")
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("Telah mencapai akhir halaman hasil pencarian.")
            break
        last_height = new_height
        
    return tweets_data

# =================================================
# SCRIPT UTAMA
# =================================================
if __name__ == "__main__":
    start_time = time.time()
    driver = create_driver()
    
    try:
        if login(driver, TWITTER_USERNAME, TWITTER_PASSWORD):
            all_scraped_data = []
            
            for i, query in enumerate(SEARCH_QUERIES):
                print(f"\n{'='*60}")
                print(f"MEMPROSES KEYWORD {i+1}/{len(SEARCH_QUERIES)}: '{query}'")
                print(f"{'='*60}")
                
                scraped_data = scrape_tweets(driver, query, MAX_TWEETS_TO_SCRAPE, DELAY_PER_SCROLL)
                
                for row in scraped_data:
                    row['keyword_pencarian'] = query
                
                all_scraped_data.extend(scraped_data)
                
                if i < len(SEARCH_QUERIES) - 1:
                    delay_antar_keyword = random.uniform(20, 40)
                    print(f"\n--- Jeda {delay_antar_keyword:.2f} detik sebelum lanjut ke keyword berikutnya ---")
                    time.sleep(delay_antar_keyword)

            if all_scraped_data:
                df = pd.DataFrame(all_scraped_data)
                df = df[['keyword_pencarian', 'username', 'timestamp', 'text']]
                output_dir = os.path.join('data', 'raw')
                os.makedirs(output_dir, exist_ok=True)
                filename = f"{NAMA_FILE_OUTPUT}_{datetime.now().strftime('%Y%m%d')}.csv"
                output_path = os.path.join(output_dir, filename)
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
                print(f"\n✅ Selesai! Total {len(df)} tweet dari {len(SEARCH_QUERIES)} keyword disimpan di: '{output_path}'")
            else:
                print("\n❌ Tidak ada tweet yang berhasil dikumpulkan dari semua keyword.")

    finally:
        print("\nMenutup browser...")
        if driver:
            driver.quit()
        
        end_time = time.time()
        print(f"⏱️ Total waktu eksekusi: {end_time - start_time:.2f} detik.")
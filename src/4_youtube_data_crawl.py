# -*- coding: utf-8 -*-
"""
Script untuk Crawling Komentar YouTube menggunakan YouTube Data API v3.
Versi 2.1 - Membaca API Key dari file config_yt.py.
"""
import pandas as pd
import os
from tqdm import tqdm
import time
from datetime import datetime

# --- Import Library Google API ---
import googleapiclient.discovery
import googleapiclient.errors

# --- Impor Konfigurasi & Keywords ---
try:
    # --- PERBAIKAN: Mengimpor dari file config_yt.py ---
    from config_yt import YOUTUBE_API_KEY
    # ---------------------------------------------------
    from keywords import NEGATIVE_KEYWORDS, POSITIVE_KEYWORDS, NEUTRAL_KEYWORDS
except ImportError:
    print("❌ Error: Pastikan file 'config_yt.py' dan 'keywords.py' ada dan berisi variabel yang dibutuhkan.")
    exit()

# ==============================================================================
# === KONFIGURASI ===
# ==============================================================================
# Masukkan ID Video YouTube yang ingin Anda crawl komentarnya.
VIDEO_IDS = [
    "qN3axfU1Geo", # Project Multatuli - Nikel Waigeo
    "JgF-A4rA1s8", # KOMPASTV - Polemik Tambang Nikel
    "mjxZeyIYeNo" 
]

NAMA_FILE_OUTPUT = "hasil_crawling_youtube_filtered"

# Menggabungkan SEMUA keyword (positif, negatif, dan netral) untuk filter relevansi
RELEVANT_KEYWORDS = set(NEGATIVE_KEYWORDS + POSITIVE_KEYWORDS + NEUTRAL_KEYWORDS)
# ==============================================================================

def is_comment_relevant(comment_text: str, relevant_keywords: set) -> bool:
    """Memeriksa apakah sebuah komentar relevan berdasarkan keyword."""
    if not comment_text:
        return False
    words_in_comment = set(comment_text.lower().split())
    return bool(words_in_comment.intersection(relevant_keywords))

def get_video_comments(api_key: str, video_id: str, relevant_keywords: set) -> list:
    """Mengambil semua komentar level atas dari satu video YouTube dengan filter relevansi."""
    print(f"\n🔎 Mengambil komentar dari video ID: {video_id}...")
    
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"
    
    try:
        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey=api_key)
    except Exception as e:
        print(f"❌ Gagal terhubung ke YouTube API: {e}")
        return []

    comments = []
    skipped_comments = 0
    next_page_token = None

    while True:
        try:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100, 
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response['items']:
                comment_snippet = item['snippet']['topLevelComment']['snippet']
                comment_text = comment_snippet['textOriginal']
                
                if is_comment_relevant(comment_text, relevant_keywords):
                    comments.append({
                        'video_id': video_id,
                        'penulis': comment_snippet['authorDisplayName'],
                        'tanggal': comment_snippet['publishedAt'],
                        'like_count': comment_snippet['likeCount'],
                        'teks': comment_text
                    })
                else:
                    skipped_comments += 1

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 403:
                print("   -> 🟡 Peringatan: Komentar dinonaktifkan untuk video ini atau kuota API habis.")
            else:
                print(f"   -> 💥 Error saat mengambil komentar: {e}")
            break

    print(f"   -> Ditemukan {len(comments)} komentar yang relevan.")
    if skipped_comments > 0:
        print(f"   -> Dilewati {skipped_comments} komentar (tidak relevan/spam).")
    return comments

# =================================================
# SCRIPT UTAMA
# =================================================
if __name__ == "__main__":
    start_time = time.time()
    print("🚀 Memulai Proses Crawling Komentar YouTube dengan Filter Relevansi...")
    
    all_comments_data = []
    
    for video_id in tqdm(VIDEO_IDS, desc="Memproses Video"):
        comments = get_video_comments(YOUTUBE_API_KEY, video_id, RELEVANT_KEYWORDS)
        all_comments_data.extend(comments)
    
    if not all_comments_data:
        print("\n❌ Tidak ada komentar relevan yang berhasil dikumpulkan.")
    else:
        df = pd.DataFrame(all_comments_data)
        df['tanggal'] = pd.to_datetime(df['tanggal'])
        df = df.sort_values(by='tanggal', ascending=False)
        
        output_dir = os.path.join('data', 'raw')
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{NAMA_FILE_OUTPUT}_{datetime.now().strftime('%Y%m%d')}.csv"
        output_path = os.path.join(output_dir, filename)
        
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ Selesai! Total {len(df)} komentar relevan dari {len(VIDEO_IDS)} video berhasil dikumpulkan.")
        print(f"💾 Data telah disimpan di: '{output_path}'")

    end_time = time.time()
    print(f"⏱️ Total waktu eksekusi: {time.time() - start_time:.2f} detik.")


# -*- coding: utf-8 -*-
"""
Script untuk Data Preprocessing dan Analisis Sentimen v5.0 (DIPERBAIKI)
- Menggunakan model yang SUDAH di-fine-tuned untuk sentimen Indonesia
- Perbaikan truncation dan error handling
"""

import pandas as pd
import re
import os
from tqdm import tqdm
from transformers import pipeline
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# === KONFIGURASI ===
# ==============================================================================
FILE_BERITA = "data/raw/hasil_crawling_portal_berita.csv"
FILE_TWITTER = "data/raw/hasil_crawling_twitter.csv"
FILE_YOUTUBE = "data/raw/hasil_crawling_youtube.csv"
LIMIT_YOUTUBE_ROWS = 5000

FILE_OUTPUT = "data/processed/hasil_analisis_sentimen_final.csv"

# PILIHAN MODEL (pilih salah satu):
# 1. Model Indonesia BERT (Recommended)
MODEL_NAME = "mdhugol/indonesia-bert-sentiment-classification"
# 2. Model RoBERTa Indonesia (Alternatif)
# MODEL_NAME = "w11wo/indonesian-roberta-base-sentiment-classifier"
# 3. Model IndoNLU (Alternatif lain)
# MODEL_NAME = "StevenLimcorn/indonesian-roberta-base-sentiment-analysis"

# ==============================================================================

print("Memuat model AI untuk analisis sentimen...")
print(f"Model yang digunakan: {MODEL_NAME}")
try:
    # ✅ PERBAIKAN: Menggunakan model yang SUDAH dilatih untuk sentimen
    sentiment_analyzer = pipeline(
        "text-classification",
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
        truncation=True,  # Otomatis truncate ke 512 token
        max_length=512
    )
    print("✅ Model berhasil dimuat dan siap digunakan.\n")
except Exception as e:
    print(f"❌ Gagal memuat model: {e}")
    print("Pastikan Anda terhubung ke internet untuk mengunduh model.")
    print("Atau coba model alternatif yang tersedia di konfigurasi.")
    exit()

def clean_text(text):
    """Membersihkan teks dari URL, mention, hashtag, dan karakter khusus."""
    if not isinstance(text, str):
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Hapus URL
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Hapus mention (@username) untuk Twitter
    text = re.sub(r'@\w+', '', text)
    
    # Hapus hashtag (#topic) tapi pertahankan teksnya
    text = re.sub(r'#(\w+)', r'\1', text)
    
    # Hapus karakter khusus tapi pertahankan huruf, angka, dan spasi
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Hapus spasi berlebih
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def analyze_sentiment_robust(text: str) -> str:
    """
    Analisis sentimen dengan validasi dan error handling yang lebih baik.
    
    Returns:
        str: 'Positif', 'Negatif', atau 'Netral'
    """
    # Validasi input minimal
    if not text or len(text.strip()) < 3:
        return "Netral"
    
    try:
        # Model akan otomatis truncate ke 512 token
        result = sentiment_analyzer(text)[0]
        
        # ✅ PERBAIKAN: Mapping label yang lebih robust
        label = result['label'].lower()
        score = result['score']
        
        # Mapping berbagai format label yang mungkin
        if 'positive' in label or 'pos' in label or label == 'label_2':
            predicted_sentiment = 'Positif'
        elif 'negative' in label or 'neg' in label or label == 'label_0':
            predicted_sentiment = 'Negatif'
        elif 'neutral' in label or 'netral' in label or label == 'label_1':
            predicted_sentiment = 'Netral'
        else:
            # Fallback: jika label tidak dikenali
            predicted_sentiment = 'Netral'
        
        # ✅ TAMBAHAN: Confidence threshold
        # Jika model tidak yakin (score < 0.5), anggap netral
        if score < 0.5:
            return 'Netral'
        
        return predicted_sentiment
        
    except Exception as e:
        print(f"⚠️ Error saat analisis: {str(e)[:50]}...")
        return "Netral"

def validate_dataframe(df, source_name):
    """Validasi dan standarisasi kolom dataframe."""
    required_cols = ['teks']
    
    # Cek kolom teks ada
    if 'teks' not in df.columns:
        text_cols = ['text', 'teks_berita', 'ringkasan_berita', 'comment']
        for col in text_cols:
            if col in df.columns:
                df = df.rename(columns={col: 'teks'})
                break
    
    # Standarisasi kolom tanggal
    date_cols = ['tanggal_publikasi', 'timestamp', 'tanggal', 'date']
    for col in date_cols:
        if col in df.columns and 'tanggal_publikasi' not in df.columns:
            df = df.rename(columns={col: 'tanggal_publikasi'})
            break
    
    return df

# =================================================
# SCRIPT UTAMA
# =================================================
if __name__ == "__main__":
    print("🚀 Memulai proses preprocessing dan analisis sentimen...\n")

    # --- 1. MEMUAT & MENGGABUNGKAN DATA ---
    print("[Langkah 1] Memuat dan menggabungkan file CSV...")
    
    dataframes = []

    # Load Portal Berita
    try:
        df_berita = pd.read_csv(FILE_BERITA)
        df_berita = validate_dataframe(df_berita, 'berita')
        df_berita['sumber'] = 'Portal Berita'
        dataframes.append(df_berita)
        print(f"   ✅ Berhasil memuat {len(df_berita):,} baris dari Portal Berita")
    except FileNotFoundError:
        print(f"   ⚠️ File '{FILE_BERITA}' tidak ditemukan, dilewati.")
    except Exception as e:
        print(f"   ❌ Error memuat berita: {e}")

    # Load Twitter
    try:
        df_twitter = pd.read_csv(FILE_TWITTER)
        df_twitter = validate_dataframe(df_twitter, 'twitter')
        df_twitter['sumber'] = 'Twitter'
        dataframes.append(df_twitter)
        print(f"   ✅ Berhasil memuat {len(df_twitter):,} baris dari Twitter")
    except FileNotFoundError:
        print(f"   ⚠️ File '{FILE_TWITTER}' tidak ditemukan, dilewati.")
    except Exception as e:
        print(f"   ❌ Error memuat Twitter: {e}")

    # Load YouTube
    try:
        df_youtube = pd.read_csv(FILE_YOUTUBE, nrows=LIMIT_YOUTUBE_ROWS)
        df_youtube = validate_dataframe(df_youtube, 'youtube')
        df_youtube['sumber'] = 'YouTube'
        dataframes.append(df_youtube)
        print(f"   ✅ Berhasil memuat {len(df_youtube):,} baris dari YouTube (dibatasi)")
    except FileNotFoundError:
        print(f"   ⚠️ File '{FILE_YOUTUBE}' tidak ditemukan, dilewati.")
    except Exception as e:
        print(f"   ❌ Error memuat YouTube: {e}")

    # Validasi ada data
    if not dataframes:
        print("\n❌ TIDAK ADA DATA UNTUK DIPROSES!")
        print("Pastikan minimal 1 file CSV tersedia di folder data/raw/")
        exit()

    # Gabungkan semua data
    df = pd.concat(dataframes, ignore_index=True)
    print(f"\n   📊 Total {len(df):,} baris data digabungkan")
    
    # Hapus baris tanpa teks
    df_before = len(df)
    df.dropna(subset=['teks'], inplace=True)
    df = df[df['teks'].str.strip() != '']
    print(f"   🧹 {df_before - len(df):,} baris kosong dihapus")
    print(f"   ✅ Sisa {len(df):,} baris untuk diproses\n")
    
    # --- 2. PREPROCESSING TEKS ---
    print("[Langkah 2] Membersihkan teks...")
    tqdm.pandas(desc="   🧼 Cleaning")
    df['teks_bersih'] = df['teks'].progress_apply(clean_text)
    
    # Hapus teks yang terlalu pendek setelah cleaning
    df = df[df['teks_bersih'].str.len() >= 3]
    print(f"   ✅ Preprocessing selesai, {len(df):,} baris valid\n")
    
    # --- 3. ANALISIS SENTIMEN ---
    print("[Langkah 3] Melakukan analisis sentimen...")
    print("   ⏳ Proses ini membutuhkan waktu, harap bersabar...")
    
    tqdm.pandas(desc="   🤖 Analyzing")
    df['sentimen'] = df['teks_bersih'].progress_apply(analyze_sentiment_robust)
    print("   ✅ Analisis sentimen selesai!\n")

    # --- 4. MENYIMPAN HASIL ---
    print("[Langkah 4] Menyimpan hasil...")
    output_dir = os.path.dirname(FILE_OUTPUT)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Pilih kolom yang relevan
    final_columns = ['sumber', 'tanggal_publikasi', 'teks', 'teks_bersih', 'sentimen']
    existing_columns = [col for col in final_columns if col in df.columns]
    df_final = df[existing_columns]
    
    # Simpan hasil
    df_final.to_csv(FILE_OUTPUT, index=False, encoding='utf-8-sig')
    print(f"   💾 Data disimpan di: '{FILE_OUTPUT}'\n")

    # --- 5. RINGKASAN HASIL ---
    print("="*60)
    print("📊 RINGKASAN HASIL ANALISIS SENTIMEN")
    print("="*60)
    
    sentiment_counts = df_final['sentimen'].value_counts()
    total = len(df_final)
    
    for sentiment, count in sentiment_counts.items():
        percentage = (count / total) * 100
        bar = "█" * int(percentage / 2)
        print(f"{sentiment:10s}: {count:5,} ({percentage:5.1f}%) {bar}")
    
    print("="*60)
    
    # Breakdown per sumber
    if 'sumber' in df_final.columns:
        print("\n📈 Breakdown per Sumber:")
        print("-" * 60)
        for sumber in df_final['sumber'].unique():
            df_sumber = df_final[df_final['sumber'] == sumber]
            print(f"\n{sumber}:")
            print(df_sumber['sentimen'].value_counts().to_string())
    
    print("\n✅ PROSES SELESAI!")
    print(f"Total data yang dianalisis: {total:,} baris")
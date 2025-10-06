Analisis Sentimen Multi-Platform: Isu Tambang Nikel di Raja Ampat
Repositori ini berisi serangkaian skrip Python untuk mengumpulkan, memproses, dan menganalisis sentimen publik dari berbagai platform digital (Portal Berita, Twitter, YouTube) mengenai isu kontroversial pertambangan nikel di Raja Ampat.

https://nikel-raja-ampat-q5gyrkl9khyytskzjd95aa.streamlit.app/

<img width="1919" height="945" alt="image" src="https://github.com/user-attachments/assets/5c4fb1c5-50d9-45f8-9eb9-ec8033d49b41" />

Latar Belakang
Rencana dan operasi pertambangan nikel di Raja Ampat, sebuah kawasan dengan keanekaragaman hayati laut kelas dunia, telah memicu diskursus publik yang luas. Proyek ini bertujuan untuk menangkap dan menganalisis narasi yang berkembang di media online dan platform sosial untuk memahami sentimen publik secara kuantitatif.

Arsitektur & Metodologi
Proses ini dibagi menjadi tiga tahap utama yang dieksekusi oleh skrip yang berbeda:

1. Pengumpulan Data (Data Crawling)
Portal Berita (1_data_crawling.py): Menggunakan kombinasi pygooglenews untuk pencarian berita yang luas dan undetected-chromedriver (Selenium) yang digabungkan dengan newspaper4k untuk mengekstraksi konten secara andal dari berbagai situs berita modern yang dilindungi JavaScript.

Twitter (twitter_crawler.py): Menggunakan Selenium untuk meniru perilaku pengguna, melakukan login, mencari tweet berdasarkan kata kunci, dan melakukan scrolling untuk mengumpulkan data percakapan.

YouTube (3_youtube_comment_crawler.py): Memanfaatkan YouTube Data API v3 resmi dari Google untuk mengumpulkan ribuan komentar dari video-video yang relevan secara efisien dan stabil.

2. Pemrosesan & Analisis Sentimen (2_data_processing.py)
Penggabungan: Menggabungkan data mentah dari ketiga file .csv (berita, Twitter, YouTube) menjadi satu dataset terpadu.

Pembersihan Teks: Melakukan pembersihan dasar pada teks, seperti menghapus URL dan mengubah teks menjadi huruf kecil.

Analisis Sentimen dengan AI: Menggunakan model IndoBERT (w11wo/indonesian-roberta-base-sentiment-classifier) dari Hugging Face Transformers untuk mengklasifikasikan setiap teks ke dalam tiga kategori: Positive, Negative, atau Neutral. Pendekatan ini dipilih untuk akurasi yang lebih tinggi dalam memahami konteks kalimat dibandingkan metode berbasis kata kunci.

3. Visualisasi Data (deploy.py)
Dashboard Interaktif: Data yang telah diolah dan dilabeli sentimennya disajikan dalam sebuah dashboard web interaktif yang dibangun menggunakan Streamlit.

Fitur Visualisasi: Termasuk metrik ringkasan, distribusi sentimen (Pie Chart), tren sentimen dari waktu ke waktu (Line Chart), perbandingan sentimen per sumber (Bar Chart), dan Word Cloud untuk kata-kata yang paling dominan.

Struktur Folder
/
├── data/
│   ├── logs/             # Menyimpan log dari proses crawling
│   ├── raw/              # Hasil mentah dari setiap script crawling (.csv)
│   └── processed/        # Hasil akhir setelah preprocessing & analisis sentimen
├── src/
│   ├── 1_data_crawling.py
│   ├── twitter_crawler.py
│   ├── 3_youtube_comment_crawler.py
│   ├── 2_data_processing.py
│   ├── deploy.py
│   ├── keywords.py
│   ├── config_x.py
│   └── config_yt.py
├── requirements.txt
└── README.md

Cara Menjalankan
1. Persyaratan
Python 3.9+

Google Chrome

2. Instalasi
Clone repositori ini dan instal semua library yang dibutuhkan.

git clone [URL_REPOSITORI_ANDA]
cd [NAMA_FOLDER_REPOSITORI]
pip install -r requirements.txt

3. Konfigurasi
Sebelum menjalankan, pastikan Anda telah mengisi file konfigurasi di dalam folder src/:

keywords.py: Isi dengan kata kunci pencarian Anda.

config_x.py: Masukkan kredensial akun Twitter Anda.

config_yt.py: Masukkan kunci API YouTube Data v3 Anda.

4. Eksekusi Skrip
Jalankan skrip secara berurutan dari direktori utama.

# Langkah 1: Crawling Berita, Twitter, dan YouTube
python src/1_data_crawling.py
python src/twitter_crawler.py
python src/3_youtube_comment_crawler.py

# Langkah 2: Preprocessing & Analisis Sentimen
python src/2_data_processing.py

# Langkah 3: Menjalankan Dashboard (Lokal)
streamlit run src/deploy.py

Kontributor
[Nama Anda] - [Link ke profil LinkedIn atau GitHub Anda]


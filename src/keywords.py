# -*- coding: utf-8 -*-
"""
File Master Keywords v2.2 (Diperkaya)

STRATEGI: "Jaring Lebar & Tombak Tajam"
- SEARCH_KEYWORDS (Jaring): Untuk pencarian awal yang luas.
- SENTIMENT KEYWORDS (Tombak): Diperkaya untuk akurasi analisis yang lebih tinggi.
"""

# ==============================================================================
# KEYWORDS UNTUK CRAWLING (Jaring Lebar)
# ==============================================================================
SEARCH_KEYWORDS = [
    "nikel papua",
    "tambang waigeo",
    "izin tambang",
    "konsesi nikel",
    "dampak nikel",
]

# ==============================================================================
# KEYWORDS UNTUK ANALISIS SENTIMEN (Tombak Tajam)
# ==============================================================================

# --- SENTIMEN NEGATIF ---
NEGATIVE_KEYWORDS = [
    # Dampak Lingkungan
    "rusak", "perusakan", "hancur", "kerusakan lingkungan", "cemar", "pencemaran laut", "polusi",
    "limbah", "tailing", "deforestasi", "hutan gundul", "air keruh",
    "sedimentasi", "terumbu karang", "ekosistem terancam", "bencana ekologis", "dampak buruk", "dampak negatif",
    # -- TAMBAHAN --
    "tercemar", "terkontaminasi", "degradasi", "erosi", "longsor", "banjir", "hilangnya habitat",
    "ancaman ekologis", "krisis iklim", "racun", "beracun",

    # Dampak Sosial & Ekonomi
    "korban", "masyarakat adat", "sengsara", "ikan hilang", "nelayan teriak",
    "pencaharian hilang", "tanah adat", "tanah dirampas", "konflik sosial",
    "kriminalisasi", "intimidasi", "tekanan", "pariwisata hancur", "wisata rusak", "homestay sepi",
    "ancam pariwisata", "surga hilang", "surga dirusak",
    # -- TAMBAHAN --
    "tergusur", "penggusuran", "resah", "keresahan warga", "gejolak sosial", "ketidakadilan", "ancaman",
    "melarat", "jatuh miskin",
    
    # Aksi Penolakan
    "tolak", "menolak", "penolakan", "protes", "demo", "demonstrasi", "unjuk rasa", "petisi",
    "gugat", "gugatan hukum", "melawan", "selamatkan", "#SaveRajaAmpat", "jaga", "lindungi",
    "#JagaRajaAmpat", "stop", "hentikan", "#StopTambangNikel", "aliansi", "koalisi",
    # -- TAMBAHAN --
    "perlawanan", "menentang", "kecaman", "kritik tajam", "boikot", "somasi", "walkout",

    # Kritik & Masalah Tata Kelola
    "korporasi jahat", "perusahaan perusak", "oligarki", "cukong", "mafia tambang", "eksploitasi",
    "izin bermasalah", "IUP ilegal", "pelanggaran", "langgar aturan", "tidak transparan",
    "kongkalikong", "pemerintah abai", "negara absen", "tutup mata", "kebijakan salah", "greenwashing",
    # -- TAMBAHAN --
    "cacat hukum", "maladministrasi", "pembiaran", "kerugian negara", "tidak bertanggung jawab",
    "konspirasi", "manipulatif", "menyesatkan"
]

# --- SENTIMEN POSITIF ---
POSITIVE_KEYWORDS = [
    # Ekonomi & Pembangunan
    "pembangunan", "kemajuan", "membangun daerah", "ekonomi tumbuh", "pertumbuhan ekonomi",
    "investasi", "investor", "lapangan kerja", "buka lowongan", "serap tenaga",
    "kesejahteraan", "rakyat sejahtera", "PAD", "pendapatan negara",
    "hilirisasi", "industri baterai", "kendaraan listrik", "EV", "komoditas strategis",
    "pemberdayaan masyarakat", "pemberdayaan ekonomi",
    # -- TAMBAHAN --
    "nilai tambah", "devisa negara", "daya saing", "peluang ekonomi", "pertumbuhan inklusif",
    "modernisasi", "swasembada", "berkontribusi", "kontribusi positif",

    # Program & CSR
    "CSR", "program bantuan", "beasiswa",
    "bangun sekolah", "bangun puskesmas", "mitra pemerintah", "sinergi", "komitmen",
    "bertanggung jawab", "praktik baik", "reklamasi", "pascatambang",
    # -- TAMBAHAN --
    "pembinaan", "kemitraan", "kolaborasi", "pendampingan", "keberlanjutan", "ramah lingkungan",
    "penghijauan", "pemberdayaan", "tanggung jawab sosial",

    # Dukungan & Apresiasi
    "mendukung", "dukungan", "apresiasi", "terima kasih", "solusi", "prospek cerah",
    "bermanfaat", "kemakmuran", "indonesia maju",
    # -- TAMBAHAN --
    "optimis", "potensi besar", "langkah maju", "positif", "berdampak baik", "sukses",
    "solusi inovatif", "efektif", "efisien", "meningkatkan"
]

# --- SENTIMEN NETRAL (tidak diubah, sudah sangat baik) ---
NEUTRAL_KEYWORDS = [
    "IUP", "izin pertambangan", "konsesi", "AMDAL", "studi kelayakan", "cadangan nikel",
    "smelter", "kontrak karya", "evaluasi", "pengawasan", "pemerintah pusat", "pemda raja ampat",
    "kementerian esdm", "kementerian lhk", "kemenko marves", "bkpm", "dprd", "unesco geopark",
    "polemik", "pro kontra", "diskusi", "webinar", "regulasi", "kebijakan", "industri nikel"
]
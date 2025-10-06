import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import re
from datetime import datetime, timedelta
import numpy as np

# ============================================================================
# KONFIGURASI PAGE
# ============================================================================
st.set_page_config(
    page_title="Dashboard Analisis Sentimen",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNGSI HELPER
# ============================================================================

@st.cache_data
def load_data(file_path):
    """Load data dengan caching"""
    try:
        df = pd.read_csv(file_path)
        # Parsing tanggal jika ada
        if 'tanggal_publikasi' in df.columns:
            df['tanggal_publikasi'] = pd.to_datetime(df['tanggal_publikasi'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def extract_keywords(text_series, top_n=20, stopwords=None):
    """Ekstrak kata-kata yang paling sering muncul"""
    if stopwords is None:
        stopwords = set([
            'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'pada', 'dengan', 'adalah',
            'ini', 'itu', 'tidak', 'ada', 'akan', 'juga', 'saya', 'kamu', 'kami',
            'mereka', 'atau', 'bisa', 'sudah', 'belum', 'karena', 'jika', 'lebih',
            'sangat', 'hanya', 'dalam', 'oleh', 'telah', 'dapat', 'agar', 'masih',
            'saat', 'seperti', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for'
        ])
    
    all_words = []
    for text in text_series.dropna():
        if isinstance(text, str):
            words = re.findall(r'\b[a-z]{3,}\b', text.lower())
            words = [w for w in words if w not in stopwords and len(w) > 2]
            all_words.extend(words)
    
    return Counter(all_words).most_common(top_n)

def create_sentiment_pie(df):
    """Buat pie chart sentimen"""
    sentiment_counts = df['sentimen'].value_counts()
    
    colors = {
        'Positif': '#2ecc71',
        'Negatif': '#e74c3c',
        'Netral': '#95a5a6'
    }
    color_list = [colors.get(s, '#3498db') for s in sentiment_counts.index]
    
    fig = go.Figure(data=[go.Pie(
        labels=sentiment_counts.index,
        values=sentiment_counts.values,
        hole=0.4,
        marker=dict(colors=color_list),
        textposition='inside',
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Jumlah: %{value}<br>Persentase: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title="Distribusi Sentimen Keseluruhan",
        showlegend=True,
        height=400,
        font=dict(size=14)
    )
    return fig

def create_sentiment_bar_by_source(df):
    """Bar chart sentimen per sumber"""
    if 'sumber' not in df.columns:
        return None
    
    sentiment_by_source = df.groupby(['sumber', 'sentimen']).size().reset_index(name='count')
    
    fig = px.bar(
        sentiment_by_source,
        x='sumber',
        y='count',
        color='sentimen',
        barmode='group',
        title="Perbandingan Sentimen per Sumber Data",
        color_discrete_map={
            'Positif': '#2ecc71',
            'Negatif': '#e74c3c',
            'Netral': '#95a5a6'
        },
        labels={'count': 'Jumlah', 'sumber': 'Sumber'}
    )
    
    fig.update_layout(height=400, font=dict(size=12))
    return fig

def create_trend_chart(df):
    """Tren sentimen berdasarkan waktu"""
    if 'tanggal_publikasi' not in df.columns:
        return None
    
    df_trend = df.dropna(subset=['tanggal_publikasi']).copy()
    df_trend['tanggal'] = df_trend['tanggal_publikasi'].dt.date
    
    daily_sentiment = df_trend.groupby(['tanggal', 'sentimen']).size().reset_index(name='count')
    
    fig = px.line(
        daily_sentiment,
        x='tanggal',
        y='count',
        color='sentimen',
        title="Tren Sentimen dari Waktu ke Waktu",
        color_discrete_map={
            'Positif': '#2ecc71',
            'Negatif': '#e74c3c',
            'Netral': '#95a5a6'
        },
        labels={'count': 'Jumlah', 'tanggal': 'Tanggal'}
    )
    
    fig.update_layout(height=400, hovermode='x unified')
    return fig

def create_wordcloud(text_series, sentiment_filter=None, colormap='viridis'):
    """Generate word cloud"""
    if sentiment_filter:
        text_series = text_series[text_series.index.isin(
            text_series.reset_index().query(f"sentimen == '{sentiment_filter}'").index
        )]
    
    text = ' '.join(text_series.dropna().astype(str))
    
    if not text.strip():
        return None
    
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        colormap=colormap,
        max_words=100,
        relative_scaling=0.5,
        min_font_size=10
    ).generate(text)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    plt.tight_layout(pad=0)
    return fig

def create_hourly_heatmap(df):
    """Heatmap aktivitas per jam dan hari"""
    if 'tanggal_publikasi' not in df.columns:
        return None
    
    df_time = df.dropna(subset=['tanggal_publikasi']).copy()
    df_time['hour'] = df_time['tanggal_publikasi'].dt.hour
    df_time['day_name'] = df_time['tanggal_publikasi'].dt.day_name()
    
    # Order hari
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    heatmap_data = df_time.groupby(['day_name', 'hour']).size().reset_index(name='count')
    heatmap_pivot = heatmap_data.pivot(index='day_name', columns='hour', values='count').fillna(0)
    heatmap_pivot = heatmap_pivot.reindex(days_order)
    
    fig = px.imshow(
        heatmap_pivot,
        labels=dict(x="Jam", y="Hari", color="Jumlah"),
        title="Heatmap Aktivitas Posting (Jam vs Hari)",
        color_continuous_scale='YlOrRd',
        aspect='auto'
    )
    
    fig.update_layout(height=400)
    return fig

def create_text_length_analysis(df):
    """Analisis panjang teks per sentimen"""
    df_copy = df.copy()
    df_copy['text_length'] = df_copy['teks_bersih'].fillna('').str.len()
    
    fig = px.box(
        df_copy,
        x='sentimen',
        y='text_length',
        color='sentimen',
        title="Distribusi Panjang Teks per Sentimen",
        color_discrete_map={
            'Positif': '#2ecc71',
            'Negatif': '#e74c3c',
            'Netral': '#95a5a6'
        },
        labels={'text_length': 'Panjang Karakter', 'sentimen': 'Sentimen'}
    )
    
    fig.update_layout(height=400, showlegend=False)
    return fig

def sentiment_comparison_stacked(df):
    """Stacked percentage bar per sumber"""
    if 'sumber' not in df.columns:
        return None
    
    sentiment_pct = df.groupby(['sumber', 'sentimen']).size().reset_index(name='count')
    sentiment_pct['percentage'] = sentiment_pct.groupby('sumber')['count'].transform(lambda x: x / x.sum() * 100)
    
    fig = px.bar(
        sentiment_pct,
        x='sumber',
        y='percentage',
        color='sentimen',
        title="Persentase Sentimen per Sumber (%)",
        color_discrete_map={
            'Positif': '#2ecc71',
            'Negatif': '#e74c3c',
            'Netral': '#95a5a6'
        },
        labels={'percentage': 'Persentase (%)', 'sumber': 'Sumber'}
    )
    
    fig.update_layout(height=400, barmode='stack')
    return fig

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header
    st.markdown('<h1 class="main-header">📊 Dashboard Analisis Sentimen</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/github/explore/80688e429a7d4ef2fca1e82350fe8e3517d3494d/topics/sentiment-analysis/sentiment-analysis.png", width=200)
        st.title("⚙️ Pengaturan")
        
        uploaded_file = st.file_uploader(
            "Upload file CSV hasil analisis sentimen",
            type=['csv'],
            help="Upload file hasil_analisis_sentimen_final.csv"
        )
        
        st.markdown("---")
        st.markdown("### 📁 Atau gunakan path default:")
        use_default = st.checkbox("Gunakan path default", value=True)
        
        if use_default:
            file_path = "data/processed/hasil_analisis_sentimen_final.csv"
        else:
            file_path = st.text_input("Path file CSV:", "")
    
    # Load data
    if uploaded_file is not None:
        df = load_data(uploaded_file)
    elif use_default or file_path:
        df = load_data(file_path)
    else:
        st.warning("⚠️ Silakan upload file atau masukkan path file CSV")
        st.stop()
    
    if df is None or df.empty:
        st.error("❌ Tidak dapat memuat data. Pastikan file tersedia dan format benar.")
        st.stop()
    
    # Validasi kolom
    required_cols = ['sentimen', 'teks_bersih']
    if not all(col in df.columns for col in required_cols):
        st.error(f"❌ File harus memiliki kolom: {', '.join(required_cols)}")
        st.stop()
    
    # ========================================================================
    # OVERVIEW METRICS
    # ========================================================================
    st.markdown("## 📈 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Data", f"{len(df):,}")
    
    with col2:
        positif_count = len(df[df['sentimen'] == 'Positif'])
        positif_pct = (positif_count / len(df) * 100)
        st.metric("Sentimen Positif", f"{positif_count:,}", f"{positif_pct:.1f}%")
    
    with col3:
        negatif_count = len(df[df['sentimen'] == 'Negatif'])
        negatif_pct = (negatif_count / len(df) * 100)
        st.metric("Sentimen Negatif", f"{negatif_count:,}", f"{negatif_pct:.1f}%")
    
    with col4:
        netral_count = len(df[df['sentimen'] == 'Netral'])
        netral_pct = (netral_count / len(df) * 100)
        st.metric("Sentimen Netral", f"{netral_count:,}", f"{netral_pct:.1f}%")
    
    st.markdown("---")
    
    # ========================================================================
    # TABS
    # ========================================================================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Visualisasi Sentimen",
        "☁️ Word Cloud",
        "📅 Analisis Tren",
        "🔍 Analisis Mendalam",
        "📋 Data Explorer"
    ])
    
    # ========================================================================
    # TAB 1: Visualisasi Sentimen
    # ========================================================================
    with tab1:
        st.markdown("### 🎯 Distribusi Sentimen")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pie = create_sentiment_pie(df)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            fig_bar = create_sentiment_bar_by_source(df)
            if fig_bar:
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Kolom 'sumber' tidak tersedia untuk perbandingan")
        
        st.markdown("### 📊 Persentase Sentimen per Sumber")
        fig_stacked = sentiment_comparison_stacked(df)
        if fig_stacked:
            st.plotly_chart(fig_stacked, use_container_width=True)
    
    # ========================================================================
    # TAB 2: Word Cloud
    # ========================================================================
    with tab2:
        st.markdown("### ☁️ Word Cloud - Kata yang Paling Sering Muncul")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            sentiment_option = st.selectbox(
                "Filter Sentimen:",
                ['Semua', 'Positif', 'Negatif', 'Netral']
            )
            
            colormap_option = st.selectbox(
                "Skema Warna:",
                ['viridis', 'plasma', 'inferno', 'magma', 'cividis', 'RdYlGn', 'coolwarm']
            )
        
        with col2:
            sentiment_filter = None if sentiment_option == 'Semua' else sentiment_option
            
            # Filter data untuk wordcloud
            if sentiment_filter:
                text_data = df[df['sentimen'] == sentiment_filter]['teks_bersih']
            else:
                text_data = df['teks_bersih']
            
            fig_wc = create_wordcloud(text_data, colormap=colormap_option)
            if fig_wc:
                st.pyplot(fig_wc)
            else:
                st.warning("Tidak cukup data untuk membuat word cloud")
        
        st.markdown("### 🔤 Top 20 Kata yang Paling Sering Muncul")
        
        col1, col2, col3 = st.columns(3)
        
        for idx, (col, sentiment) in enumerate(zip([col1, col2, col3], ['Positif', 'Negatif', 'Netral'])):
            with col:
                st.markdown(f"**{sentiment}**")
                text_data = df[df['sentimen'] == sentiment]['teks_bersih']
                keywords = extract_keywords(text_data, top_n=20)
                
                if keywords:
                    keywords_df = pd.DataFrame(keywords, columns=['Kata', 'Frekuensi'])
                    st.dataframe(keywords_df, height=400, use_container_width=True)
                else:
                    st.info(f"Tidak ada data untuk sentimen {sentiment}")
    
    # ========================================================================
    # TAB 3: Analisis Tren
    # ========================================================================
    with tab3:
        st.markdown("### 📅 Tren Sentimen dari Waktu ke Waktu")
        
        fig_trend = create_trend_chart(df)
        if fig_trend:
            st.plotly_chart(fig_trend, use_container_width=True)
            
            st.markdown("### 🔥 Heatmap Aktivitas Posting")
            fig_heatmap = create_hourly_heatmap(df)
            if fig_heatmap:
                st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.warning("⚠️ Kolom 'tanggal_publikasi' tidak tersedia atau tidak valid untuk analisis tren")
            st.info("Pastikan file CSV memiliki kolom 'tanggal_publikasi' dengan format tanggal yang valid")
    
    # ========================================================================
    # TAB 4: Analisis Mendalam
    # ========================================================================
    with tab4:
        st.markdown("### 🔍 Analisis Mendalam")
        
        # Analisis panjang teks
        st.markdown("#### 📏 Distribusi Panjang Teks per Sentimen")
        fig_length = create_text_length_analysis(df)
        st.plotly_chart(fig_length, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Statistik Panjang Teks")
            df_stats = df.copy()
            df_stats['text_length'] = df_stats['teks_bersih'].fillna('').str.len()
            stats = df_stats.groupby('sentimen')['text_length'].describe()[['mean', 'min', 'max', 'std']]
            stats.columns = ['Rata-rata', 'Min', 'Max', 'Std Dev']
            st.dataframe(stats.round(2), use_container_width=True)
        
        with col2:
            st.markdown("#### 📈 Distribusi per Sumber")
            if 'sumber' in df.columns:
                source_dist = df.groupby('sumber').size().reset_index(name='Jumlah')
                source_dist['Persentase'] = (source_dist['Jumlah'] / source_dist['Jumlah'].sum() * 100).round(2)
                st.dataframe(source_dist, use_container_width=True)
        
        # Contoh teks per sentimen
        st.markdown("#### 💬 Contoh Teks per Sentimen (Random Sample)")
        
        col1, col2, col3 = st.columns(3)
        
        for col, sentiment, color in zip(
            [col1, col2, col3],
            ['Positif', 'Negatif', 'Netral'],
            ['#d4edda', '#f8d7da', '#d1ecf1']
        ):
            with col:
                st.markdown(f"**{sentiment}**")
                sample = df[df['sentimen'] == sentiment].sample(min(3, len(df[df['sentimen'] == sentiment])))
                
                for idx, row in sample.iterrows():
                    text = row['teks'][:150] + "..." if len(row['teks']) > 150 else row['teks']
                    st.markdown(f"""
                    <div style="background-color: {color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    {text}
                    </div>
                    """, unsafe_allow_html=True)
    
    # ========================================================================
    # TAB 5: Data Explorer
    # ========================================================================
    with tab5:
        st.markdown("### 📋 Data Explorer")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sentiment_filter = st.multiselect(
                "Filter Sentimen:",
                options=df['sentimen'].unique(),
                default=df['sentimen'].unique()
            )
        
        with col2:
            if 'sumber' in df.columns:
                source_filter = st.multiselect(
                    "Filter Sumber:",
                    options=df['sumber'].unique(),
                    default=df['sumber'].unique()
                )
            else:
                source_filter = None
        
        with col3:
            search_text = st.text_input("🔍 Cari kata kunci:", "")
        
        # Apply filters
        df_filtered = df[df['sentimen'].isin(sentiment_filter)]
        
        if source_filter and 'sumber' in df.columns:
            df_filtered = df_filtered[df_filtered['sumber'].isin(source_filter)]
        
        if search_text:
            df_filtered = df_filtered[df_filtered['teks_bersih'].str.contains(search_text, case=False, na=False)]
        
        st.markdown(f"**Menampilkan {len(df_filtered):,} dari {len(df):,} baris**")
        
        # Display columns selection
        all_columns = df_filtered.columns.tolist()
        default_cols = ['sumber', 'tanggal_publikasi', 'teks', 'sentimen'] if 'sumber' in df.columns else ['teks', 'sentimen']
        display_cols = st.multiselect(
            "Pilih kolom yang ditampilkan:",
            options=all_columns,
            default=[col for col in default_cols if col in all_columns]
        )
        
        if display_cols:
            st.dataframe(df_filtered[display_cols], use_container_width=True, height=500)
        
        # Download button
        csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Download Data Terfilter (CSV)",
            data=csv,
            file_name="data_filtered.csv",
            mime="text/csv"
        )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
    Dashboard dibuat dengan ❤️ menggunakan Streamlit | Data: Hasil Analisis Sentimen IndoBERT
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
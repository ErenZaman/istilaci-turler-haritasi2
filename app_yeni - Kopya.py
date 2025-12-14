import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap
import requests
from urllib.parse import quote
import time

# --- Sayfa Ayarları ---
st.set_page_config(
    page_title="İstilacı Türler Veri Tabanı - Türkiye", 
    layout="wide", 
    page_icon="🌿",
    initial_sidebar_state="expanded"
)

# --- CSS ile Geliştirilmiş Tasarım ---
st.markdown("""
    <style>
    /* Ana Başlık Alanı */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white !important;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
        font-weight: 800;
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.95;
        color: #f0f2f6 !important;
        font-weight: 500;
    }
    
    /* İstatistik Kartları */
    .stat-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
        border-left: 5px solid #667eea;
        transition: transform 0.2s;
    }
    .stat-card:hover {
        transform: translateY(-5px);
    }
    .stat-number {
        font-size: 2.2rem;
        font-weight: 700;
        color: #764ba2;
    }
    .stat-label {
        color: #4a5568;
        font-size: 1rem;
        margin-top: 0.5rem;
        font-weight: 600;
    }

    /* Taksonomi Kartları (Okunabilirlik Düzeltmesi) */
    .taxonomy-card {
        background-color: #f8f9fa; /* Açık gri arka plan */
        border: 1px solid #e2e8f0;
        padding: 1.2rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #764ba2;
    }
    .taxonomy-card h4 {
        color: #2d3748 !important; /* Koyu başlık rengi */
        margin-top: 0;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    
    /* Taksonomi Satırları */
    .tax-row {
        background-color: #ffffff;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 6px;
        border: 1px solid #edf2f7;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .tax-label {
        color: #4a5568 !important; /* Koyu gri etiket */
        font-weight: 700;
    }
    .tax-value {
        color: #2d3748 !important; /* Çok koyu gri değer */
        font-weight: 500;
    }

    /* Sekme Tasarımı */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        border-bottom: 2px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: pre-wrap;
        border-radius: 8px 8px 0 0;
        padding: 0 1.5rem;
        font-weight: 600;
        color: #4a5568;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e2e8f0;
        color: #764ba2;
        border-bottom: 3px solid #764ba2;
    }

    /* Genel Metin İyileştirmeleri */
    h1, h2, h3 {
        color: #2d3748;
    }
    .stMarkdown p {
        color: #4a5568;
        line-height: 1.6;
    }
    
    /* Uyarı ve Bilgi Kutuları */
    .stAlert {
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. Veri Yükleme ---
@st.cache_data
def load_data(file):
    """CSV veya Excel dosyasını yükler"""
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        # Boş değerleri temizle
        df = df.fillna('')
        
        # Sütun isimlerini standardize et
        df.columns = df.columns.str.strip()
        
        return df
    except Exception as e:
        st.error(f"Veri yükleme hatası: {e}")
        return None

# --- 2. API Yardımcı Fonksiyonları ---
def get_gbif_key(species_name):
    """GBIF türü anahtar numarasını alır"""
    clean_name = species_name.split('(')[0].split(',')[0].strip()
    try:
        response = requests.get(
            f"https://api.gbif.org/v1/species/match?name={clean_name}", 
            timeout=5
        )
        return response.json().get('usageKey')
    except:
        return None

@st.cache_data
def get_gbif_data(species_name, limit=200):
    """GBIF'ten tür kayıtlarını çeker"""
    usage_key = get_gbif_key(species_name)
    if not usage_key:
        return []
    try:
        url = f"https://api.gbif.org/v1/occurrence/search?taxonKey={usage_key}&limit={limit}&hasCoordinate=true"
        response = requests.get(url, timeout=10)
        return response.json().get('results', [])
    except:
        return []

@st.cache_data
def get_inaturalist_data(species_name, limit=200):
    """iNaturalist'ten tür kayıtlarını çeker"""
    clean_name = species_name.split('(')[0].split(',')[0].strip()
    try:
        # İlk olarak tür ID'sini bul
        search_url = f"https://api.inaturalist.org/v1/taxa?q={quote(clean_name)}&rank=species"
        search_response = requests.get(search_url, timeout=5)
        search_data = search_response.json()
        
        if search_data.get('results'):
            taxon_id = search_data['results'][0]['id']
            
            # Gözlem verilerini al
            obs_url = f"https://api.inaturalist.org/v1/observations?taxon_id={taxon_id}&per_page={limit}&has[]=geo"
            obs_response = requests.get(obs_url, timeout=10)
            return obs_response.json().get('results', [])
    except:
        pass
    return []

@st.cache_data
def get_species_image(species_name):
    """GBIF'ten tür fotoğrafı alır"""
    usage_key = get_gbif_key(species_name)
    if not usage_key:
        return None
    try:
        url = f"https://api.gbif.org/v1/occurrence/search?taxonKey={usage_key}&mediaType=StillImage&limit=1"
        results = requests.get(url, timeout=5).json().get('results', [])
        if results:
            for media in results[0].get('media', []):
                if media.get('type') == 'StillImage':
                    return media.get('identifier')
    except:
        pass
    return None

@st.cache_data
def get_scientific_papers_semantic(species_name, limit=10):
    """Semantic Scholar API ile makaleleri çeker"""
    clean_name = species_name.split('(')[0].split(',')[0].strip()
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": f"{clean_name} invasive species",
        "limit": limit,
        "fields": "title,url,year,venue,abstract,authors,citationCount"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get('data', [])
    except:
        pass
    return []

def create_google_scholar_link(species_name):
    """Google Scholar arama linki oluşturur"""
    clean_name = species_name.split('(')[0].split(',')[0].strip()
    query = quote(f"{clean_name} invasive species")
    return f"https://scholar.google.com/scholar?q={query}"

# --- 3. Lokasyon Koordinat Sözlüğü (Genişletilmiş) ---
# Eksik yerler eklendi ve mevcutlar korundu.
location_coords = {
    # Marmara & Trakya
    "İstanbul": [41.0082, 28.9784], "İstanbul Boğazı": [41.1000, 29.0500], "Büyükada": [40.8741, 29.1293], 
    "Haliç": [41.0289, 28.9697], "Büyükçekmece Körfezi": [40.9922, 28.5671], "Marmara Denizi": [40.7500, 28.2500], "Marmara": [40.7000, 28.2000],
    "Çanakkale": [40.153, 26.405], "Çanakkale Boğazı": [40.2000, 26.4000], "Abide": [40.0503, 26.2192], 
    "Kilitbahir": [40.1472, 26.3797], "Eceabat": [40.1850, 26.3575], "Gelibolu": [40.4100, 26.6700], 
    "Lapseki": [40.3444, 26.6853], "Yapıldak": [40.2078, 26.5492], "Kepez": [40.1000, 26.4000],
    "Şevketiye": [40.3955, 26.8716], "Burhanlı Mevkii": [40.3069, 26.5593], "Ayazma Mevkii": [39.8120, 26.0090], 
    "Alaybey Mevkii": [39.8280, 26.0150], "Seyit Onbaşı Anıtı Mevkii": [40.1457, 26.3779], "Havuzlar Mevkii": [40.1460, 26.3780],
    "Gökçeada": [40.1889, 25.9044], "Bozcaada": [39.8322, 26.0719],
    "Balıkesir": [39.6484, 27.8826], "Bandırma": [40.3533, 27.9708], "Bandırma Körfezi": [40.3800, 27.9500],
    "Edremit Körfezi": [39.5333, 26.8500], "Ayvalık": [39.3190, 26.6960],
    "Bursa": [40.1885, 29.0610], "Yalova": [40.6549, 29.2842], "Hersek Lagünü": [40.7239, 29.5046],
    "Kocaeli": [40.8533, 29.8815], "İzmit": [40.7654, 29.9408], "İzmit Körfezi": [40.7300, 29.7000],
    "Sakarya": [40.7569, 30.3783], "Tekirdağ": [40.9780, 27.5110], "Uçmakdere": [40.8025, 27.3653],
    "Edirne": [41.6772, 26.5557], "Kırklareli": [41.7355, 27.2244], "Bilecik": [40.1419, 29.9793],

    # Ege
    "İzmir": [38.4237, 27.1428], "İzmir Körfezi": [38.4500, 26.9000], "Alsancak Limanı": [38.4410, 27.1480],
    "Levent Marina": [38.4090, 27.0850], "Pasaport Marina": [38.4289, 27.1325], "Aliağa": [38.7994, 26.9723],
    "Karaburun": [38.6394, 26.5125], "Karaburun Yarımadası": [38.6394, 26.5125], "Ildır": [38.3842, 26.4764], "Çeşme": [38.3232, 26.3039],
    "Çeşme-Dalyan Marina": [38.3560, 26.3130], "Seferihisar": [38.2047, 26.8378], "Seferihisar-Sığacık Limanı": [38.1950, 26.7860],
    "Sığacık": [38.2000, 26.7800], "Urla": [38.3229, 26.7635], "Urla-İskele": [38.3600, 26.7650],
    "Mordoğan Balıkçı Barınağı": [38.5180, 26.6300], "Özdere-Menderes": [38.0160, 27.0830], "Güzelbahçe": [38.3350, 26.8910],
    "Dikili": [39.0717, 26.8872], "Dikili Açıkları": [39.0700, 26.8500], "Foça": [38.6669, 26.7550],
    "Muğla": [37.2154, 28.3636], "Gökova Körfezi": [36.9500, 28.1000], "Akyaka": [37.0536, 28.3264],
    "Marmaris": [36.8550, 28.2742], "Marmaris Körfezi": [36.8000, 28.3000], "Bodrum": [37.0344, 27.4305], 
    "Salih Adası": [37.1530, 27.5140], "Salih Adası-Bodrum": [37.1530, 27.5140], "Güllük Körfezi": [37.2400, 27.6000],
    "Fethiye": [36.6217, 29.1164], "Fethiye Körfezi": [36.6500, 29.0500], "Göcek": [36.7550, 28.9380], "Göcek-Fethiye Körfezi": [36.7550, 28.9380],
    "Sarsala": [36.6614, 28.8579], "İnlice": [36.7160, 29.0500], "Ekincik Körfezi": [36.8250, 28.5500],
    "Dalyan": [36.8350, 28.6430], "İztuzu": [36.7900, 28.6100], "İztuzu-Dalyan": [36.7900, 28.6100], "Datça Yarımadası": [36.7300, 27.6800],
    "Kuşadası": [37.8579, 27.2610], "Kuşadası Körfezi": [37.9000, 27.2000],
    "Aydın": [37.8444, 27.8458], "Manisa": [38.6191, 27.4289], "Denizli": [37.7765, 29.0864], "Uşak": [38.6823, 29.4082], "Kütahya": [39.4167, 29.9833], "Afyon": [38.7569, 30.5386], "Afyonkarahisar": [38.7569, 30.5386],

    # Akdeniz
    "Antalya": [36.8969, 30.7133], "Antalya Körfezi": [36.7500, 30.8000], "Belek": [36.8622, 31.0556],
    "Kemer": [36.5969, 30.5597], "Kaş": [36.2000, 29.6333], "Kaş Yarımadası": [36.1800, 29.6200], "Kalkan": [36.2650, 29.4130],
    "Finike": [36.2944, 30.1464], "Finike Körfezi": [36.2500, 30.2000], "Alanya": [36.5437, 31.9998], "Okurcalar": [36.6490, 31.7040], "Üç Adalar": [36.4550, 30.5480],
    "Mersin": [36.8121, 34.6415], "Mersin Körfezi": [36.7500, 34.7000], "Anamur": [36.0750, 32.8358], "Silifke": [36.3778, 33.9278],
    "Paradeniz": [36.2940, 33.9980], "Aydıncık": [36.1450, 33.3250], "Taşucu": [36.3200, 33.8800],
    "Adana": [37.0000, 35.3213], "Seyhan": [36.9950, 35.3200], "Karataş": [36.5700, 35.3800], "Yumurtalık": [36.7720, 35.7930], "Yumurtalık-Adana": [36.7720, 35.7930], "Ceyhan-Adana": [37.0200, 35.8100],
    "Hatay": [36.2023, 36.1606], "İskenderun": [36.5867, 36.1642], "İskenderun Körfezi": [36.6660, 35.9550], "Antakya Körfezi": [36.0500, 35.9000],
    "Arsuz": [36.4100, 35.8800], "Samandağ": [36.0833, 35.9667], "Meydan Köy": [36.0300, 35.9500], "Yayladağı": [35.9031, 36.0603],
    "Isparta": [37.7648, 30.5567], "Burdur": [37.7203, 30.2908], "Kahramanmaraş": [37.5753, 36.9228], "K.Maraş": [37.5753, 36.9228], "Osmaniye": [37.0742, 36.2467],

    # Karadeniz
    "Karadeniz": [42.0, 32.0], "Trabzon": [41.0027, 39.7168], "Rize": [41.0201, 40.5234], "Artvin": [41.1828, 41.8183],
    "Giresun": [40.9128, 38.3895], "Ordu": [40.9839, 37.8764], "Fatsa": [41.0300, 37.5000], "Samsun": [41.2867, 36.3300],
    "Sinop": [42.0231, 35.1531], "Sinop Körfezi": [42.0100, 35.1500], "Zonguldak": [41.4564, 31.7936], "Ereğli": [41.2800, 31.4300],
    "Bartın": [41.6344, 32.3375], "Kastamonu": [41.3887, 33.7827], "Bolu": [40.7350, 31.6061], "Düzce": [40.8438, 31.1565], "Akçakoca": [41.0870, 31.1240],
    "Karabük": [41.2061, 32.6204], "Gümüşhane": [40.4600, 39.4700], "Bayburt": [40.2552, 40.2249], "Çorum": [40.5506, 34.9556], 
    "Amasya": [40.6500, 35.8300], "Tokat": [40.3167, 36.5500],

    # İç Anadolu
    "Ankara": [39.9334, 32.8597], "Eskişehir": [39.7667, 30.5256], "Konya": [37.8667, 32.4800], "Karaman": [37.1759, 33.2287],
    "Kayseri": [38.7312, 35.4787], "Sivas": [39.7477, 37.0163], "Aksaray": [38.3687, 34.0370], "Niğde": [37.9667, 34.6857],
    "Nevşehir": [38.6244, 34.7144], "Kırşehir": [39.1425, 34.1709], "Yozgat": [39.8181, 34.8147], "Çankırı": [40.6013, 33.6134],
    "Kırıkkale": [39.8468, 33.5153],

    # Doğu & Güneydoğu
    "Erzurum": [39.9043, 41.2691], "Van": [38.4891, 43.4089], "Elazığ": [38.6810, 39.2264], "Erzincan": [39.7500, 39.5000],
    "Malatya": [38.3552, 38.3095], "Diyarbakır": [37.9144, 40.2306], "Şanlıurfa": [37.1591, 38.7969],
    "Gaziantep": [37.0662, 37.3833], "Iğdır": [39.9237, 44.0450], "Kars": [40.6013, 43.0975], "Ardahan": [41.1105, 42.7022],
    "Ağrı": [39.7191, 43.0503], "Muş": [38.7432, 41.4910], "Bitlis": [38.4006, 42.1095], "Bingöl": [38.8847, 40.4939],
    "Tunceli": [39.1083, 39.5471], "Siirt": [37.9333, 41.9500], "Batman": [37.8812, 41.1351], "Mardin": [37.3212, 40.7245],
    "Şırnak": [37.5164, 42.4611], "Hakkari": [37.5744, 43.7408], "Adıyaman": [37.7641, 38.2762], "Kilis": [36.7184, 37.1212]
}

# --- ANA UYGULAMA ---
def main():
    # Başlık
    st.markdown("""
        <div class='main-header'>
            <h1>🌿 İstilacı Türler Veri Tabanı</h1>
            <p>Türkiye'deki İstilacı Türlerin Detaylı Bilgi ve Coğrafi Dağılım Platformu</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Yan Panel - Dosya Yükleme
    with st.sidebar:
        st.header("📁 Veri Yükleme")
        uploaded_file = st.file_uploader(
            "CSV veya Excel dosyası yükleyin",
            type=["csv", "xlsx"],
            help="İstilacı türler listesini içeren dosyayı yükleyin"
        )
    
    if uploaded_file is None:
        st.info("👈 Lütfen sol menüden veri dosyanızı yükleyin.")
        st.markdown("""
        ### 📋 Platform Özellikleri
        - 🗺️ **İnteraktif Harita**: Türlerin coğrafi dağılımını görüntüleyin
        - 🔬 **Taksonomik Bilgiler**: Detaylı sınıflandırma bilgileri
        - 📚 **Akademik Kaynaklar**: Semantic Scholar ve Google Scholar entegrasyonu
        - 🌍 **Küresel Veriler**: GBIF ve iNaturalist veri kaynakları
        - 📊 **Detaylı Filtreler**: Sistem, sınıf, takım, aile bazında filtreleme
        """)
        return
    
    # Veriyi yükle
    df = load_data(uploaded_file)
    if df is None:
        return
    
    # --- İSTATİSTİKLER ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{len(df)}</div>
                <div class='stat-label'>Toplam Tür</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        sistem_count = df['Sistem'].nunique() if 'Sistem' in df.columns else 0
        st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{sistem_count}</div>
                <div class='stat-label'>Sistem</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        class_count = df['Sınıf'].nunique() if 'Sınıf' in df.columns else 0
        st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{class_count}</div>
                <div class='stat-label'>Sınıf</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        family_count = df['Aile'].nunique() if 'Aile' in df.columns else 0
        st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{family_count}</div>
                <div class='stat-label'>Aile</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # --- YAN PANEL FİLTRELEME ---
    with st.sidebar:
        st.header("🔍 Filtreleme Seçenekleri")
        
        # Sistem Filtresi
        if 'Sistem' in df.columns:
            sistem_options = sorted([s for s in df['Sistem'].unique() if s])
            selected_sistem = st.multiselect(
                "Sistem",
                sistem_options,
                default=sistem_options,
                help="Karasal, Sucul vb."
            )
        else:
            selected_sistem = []
        
        # Diğer filtreler...
        if 'Alem' in df.columns:
            alem_options = sorted([a for a in df['Alem'].unique() if a])
            selected_alem = st.multiselect("Alem (Kingdom)", alem_options, default=alem_options)
        else: selected_alem = []
        
        if 'Şube' in df.columns:
            sube_options = sorted([s for s in df['Şube'].unique() if s])
            selected_sube = st.multiselect("Şube (Phylum)", sube_options, default=sube_options)
        else: selected_sube = []
        
        if 'Sınıf' in df.columns:
            sinif_options = sorted([s for s in df['Sınıf'].unique() if s])
            selected_sinif = st.multiselect("Sınıf (Class)", sinif_options, default=sinif_options)
        else: selected_sinif = []
        
        if 'Takım' in df.columns:
            takim_options = sorted([t for t in df['Takım'].unique() if t])
            selected_takim = st.multiselect("Takım (Order)", takim_options, default=takim_options)
        else: selected_takim = []
        
        if 'Aile' in df.columns:
            aile_options = sorted([a for a in df['Aile'].unique() if a])
            selected_aile = st.multiselect("Aile (Family)", aile_options, default=aile_options)
        else: selected_aile = []
    
    # Filtreleme uygula
    filtered_df = df.copy()
    if 'Sistem' in df.columns and selected_sistem:
        filtered_df = filtered_df[filtered_df['Sistem'].isin(selected_sistem)]
    if 'Alem' in df.columns and selected_alem:
        filtered_df = filtered_df[filtered_df['Alem'].isin(selected_alem)]
    if 'Şube' in df.columns and selected_sube:
        filtered_df = filtered_df[filtered_df['Şube'].isin(selected_sube)]
    if 'Sınıf' in df.columns and selected_sinif:
        filtered_df = filtered_df[filtered_df['Sınıf'].isin(selected_sinif)]
    if 'Takım' in df.columns and selected_takim:
        filtered_df = filtered_df[filtered_df['Takım'].isin(selected_takim)]
    if 'Aile' in df.columns and selected_aile:
        filtered_df = filtered_df[filtered_df['Aile'].isin(selected_aile)]
    
    # Tür Seçimi
    with st.sidebar:
        st.markdown("---")
        st.header("🎯 Tür Seçimi")
        
        if len(filtered_df) == 0:
            st.warning("Seçili filtrelere uygun tür bulunamadı!")
            return
        
        species_list = sorted(filtered_df['Tür'].unique())
        target_species = st.selectbox(
            f"Tür seçin ({len(species_list)} tür)",
            species_list,
            help="İncelemek istediğiniz türü seçin"
        )
    
    # Seçili türün verilerini al
    if target_species:
        species_row = filtered_df[filtered_df['Tür'] == target_species].iloc[0]
        
        # Sol panelde tür özeti
        with st.sidebar:
            st.markdown("---")
            
            # Fotoğraf
            with st.spinner("Fotoğraf yükleniyor..."):
                img_url = get_species_image(target_species)
                if img_url:
                    st.image(img_url, caption=target_species, use_container_width=True)
                else:
                    st.info("📷 Fotoğraf bulunamadı")
            
            # Taksonomik Hiyerarşi (Sidebar - Sade)
            st.markdown("### 🧬 Taksonomik Hiyerarşi")
            taxonomy_items = [('Alem', 'Alem'), ('Şube', 'Şube'), ('Sınıf', 'Sınıf'), ('Takım', 'Takım'), ('Aile', 'Aile')]
            
            for label, col in taxonomy_items:
                if col in species_row and species_row[col]:
                    # Beyaz üzerine beyaz sorununu çözmek için normal st.write veya markdown kullanıyoruz, HTML rengi vermiyoruz
                    st.markdown(f"**{label}:** {species_row[col]}")
        
        # Ana İçerik Sekmeleri
        tab_map, tab_details, tab_papers, tab_taxonomy = st.tabs([
            "🗺️ Coğrafi Dağılım",
            "📋 Tür Bilgileri",
            "📚 Akademik Yayınlar",
            "🧬 Taksonomik Detaylar"
        ])
        
        # --- SEKME 1: COĞRAFİ DAĞILIM ---
        with tab_map:
            st.subheader(f"🗺️ {target_species} - Coğrafi Dağılım")
            
            col_map1, col_map2 = st.columns([3, 1])
            
            with col_map2:
                st.markdown("#### Veri Kaynakları")
                show_local = st.checkbox("📍 Yerel Kayıtlar", value=True)
                show_gbif = st.checkbox("🌍 GBIF Verileri", value=False)
                show_inaturalist = st.checkbox("🦋 iNaturalist Verileri", value=False)
                
                if show_gbif or show_inaturalist:
                    st.info("Küresel veriler yükleniyor...")
            
            with col_map1:
                m = folium.Map(location=[39.0, 35.0], zoom_start=6, tiles="CartoDB positron")
                
                if show_local and 'Yerler' in species_row:
                    local_layer = MarkerCluster(name="📍 Yerel Kayıtlar")
                    locations = str(species_row['Yerler']).split('\n')
                    found_locs = False
                    for loc in locations:
                        loc = loc.strip()
                        # Yer adında gereksiz boşluk veya tire temizliği
                        clean_loc = loc.replace(" - ", "-").strip()
                        
                        if clean_loc:
                            # Önce tam eşleşme ara
                            coords = location_coords.get(clean_loc)
                            
                            # Bulunamazsa 'İlçe, İl' formatını ayırıp dene
                            if not coords and ',' in clean_loc:
                                parts = clean_loc.split(',')
                                coords = location_coords.get(parts[0].strip())
                            
                            # Yine bulunamazsa tire ile ayrılmış olabilir
                            if not coords and '-' in clean_loc:
                                parts = clean_loc.split('-')
                                coords = location_coords.get(parts[0].strip())

                            if coords:
                                folium.Marker(
                                    location=coords,
                                    popup=f"<b>{target_species}</b><br>{clean_loc}",
                                    icon=folium.Icon(color="blue", icon="info-sign"),
                                    tooltip=clean_loc
                                ).add_to(local_layer)
                                found_locs = True
                    
                    if found_locs:
                        local_layer.add_to(m)
                    else:
                        st.warning("⚠️ Bu tür için haritada gösterilebilecek yerel konum verisi bulunamadı veya eşleştirilemedi.")

                # GBIF verileri
                if show_gbif:
                    gbif_results = get_gbif_data(target_species)
                    if gbif_results:
                        gbif_layer = folium.FeatureGroup(name="🌍 GBIF")
                        for rec in gbif_results:
                            if 'decimalLatitude' in rec and 'decimalLongitude' in rec:
                                folium.CircleMarker(
                                    location=[rec['decimalLatitude'], rec['decimalLongitude']],
                                    radius=4, color="red", fill=True, fill_opacity=0.6,
                                    popup=f"GBIF: {rec.get('year', 'Tarih yok')}", tooltip="GBIF"
                                ).add_to(gbif_layer)
                        gbif_layer.add_to(m)
                
                # iNaturalist verileri
                if show_inaturalist:
                    inat_results = get_inaturalist_data(target_species)
                    if inat_results:
                        inat_layer = folium.FeatureGroup(name="🦋 iNaturalist")
                        for obs in inat_results:
                            if obs.get('location'):
                                coords = obs['location'].split(',')
                                if len(coords) == 2:
                                    try:
                                        lat, lon = float(coords[0]), float(coords[1])
                                        folium.CircleMarker(
                                            location=[lat, lon],
                                            radius=4, color="green", fill=True, fill_opacity=0.6,
                                            popup=f"iNaturalist: {obs.get('observed_on', 'Tarih yok')}", tooltip="iNaturalist"
                                        ).add_to(inat_layer)
                                    except: pass
                        inat_layer.add_to(m)
                
                folium.LayerControl().add_to(m)
                st_folium(m, width=900, height=600)
        
        # --- SEKME 2: TÜR BİLGİLERİ ---
        with tab_details:
            st.subheader(f"📋 {target_species} - Detaylı Bilgiler")
            if 'Genel Adı' in species_row and species_row['Genel Adı']:
                st.markdown(f"### {species_row['Genel Adı']}")
            
            if 'Özet' in species_row and species_row['Özet']:
                st.info(species_row['Özet'])
            
            col_det1, col_det2 = st.columns(2)
            with col_det1:
                if 'Tür Tanımı' in species_row and species_row['Tür Tanımı']:
                    st.markdown("#### 🔬 Tür Tanımı")
                    st.write(species_row['Tür Tanımı'])
                if 'Yaşam Alanı' in species_row and species_row['Yaşam Alanı']:
                    st.markdown("#### 🌍 Yaşam Alanı")
                    st.write(species_row['Yaşam Alanı'])
                if 'Beslenme Bilgisi' in species_row and species_row['Beslenme Bilgisi']:
                    st.markdown("#### 🍽️ Beslenme")
                    st.write(species_row['Beslenme Bilgisi'])
            
            with col_det2:
                if 'Üreme Bilgisi' in species_row and species_row['Üreme Bilgisi']:
                    st.markdown("#### 👶 Üreme")
                    st.write(species_row['Üreme Bilgisi'])
                if 'Yaşam Döngüsü' in species_row and species_row['Yaşam Döngüsü']:
                    st.markdown("#### ⏰ Yaşam Döngüsü")
                    st.write(species_row['Yaşam Döngüsü'])
            
            st.markdown("---")
            if 'Genel Etki Bilgisi' in species_row and species_row['Genel Etki Bilgisi']:
                st.markdown("#### ⚠️ Genel Etkileri")
                st.warning(species_row['Genel Etki Bilgisi'])
            if 'Genel Yönetim Bilgisi' in species_row and species_row['Genel Yönetim Bilgisi']:
                st.markdown("#### 🛠️ Yönetim ve Kontrol")
                st.success(species_row['Genel Yönetim Bilgisi'])
            if 'Genel Giriş Yolu Bilgisi' in species_row and species_row['Genel Giriş Yolu Bilgisi']:
                st.markdown("#### 🚪 Giriş Yolu")
                st.write(species_row['Genel Giriş Yolu Bilgisi'])
            if 'Notlar' in species_row and species_row['Notlar']:
                st.markdown("#### 📝 Notlar")
                st.info(species_row['Notlar'])
        
        # --- SEKME 3: AKADEMİK YAYINLAR ---
        with tab_papers:
            st.subheader(f"📚 {target_species} - Akademik Yayınlar")
            google_scholar_url = create_google_scholar_link(target_species)
            st.markdown(f"""
                <a href='{google_scholar_url}' target='_blank' 
                   style='display: inline-block; padding: 0.5rem 1.5rem; 
                          background: linear-gradient(135deg, #4285f4 0%, #34a853 100%);
                          color: white !important; text-decoration: none; border-radius: 5px; 
                          font-weight: 600; margin-bottom: 1rem;'>
                    🔍 Google Scholar'da Ara
                </a>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 📖 Semantic Scholar Makaleleri")
            
            with st.spinner("Makaleler aranıyor..."):
                papers = get_scientific_papers_semantic(target_species)
                if papers:
                    for i, paper in enumerate(papers, 1):
                        with st.expander(f"{i}. {paper.get('title', 'Başlıksız')} ({paper.get('year', 'Tarihsiz')})"):
                            st.write(f"**Yayın:** {paper.get('venue', '-')}")
                            st.write(f"**Yazarlar:** {', '.join([a.get('name', '') for a in paper.get('authors', [])[:3]])}")
                            if paper.get('abstract'):
                                st.write(f"**Özet:** {paper['abstract'][:300]}...")
                            if paper.get('url'):
                                st.markdown(f"[🔗 Makaleyi Oku]({paper['url']})")
                else:
                    st.warning("⚠️ Makale bulunamadı.")

        # --- SEKME 4: TAKSONOMİK DETAYLAR ---
        with tab_taxonomy:
            st.subheader(f"🧬 {target_species} - Taksonomik Detaylar")
            
            # Kart Başlığı
            st.markdown("""
                <div class='taxonomy-card'>
                    <h4>📊 Taksonomik Sınıflandırma</h4>
                </div>
            """, unsafe_allow_html=True)
            
            col_tax1, col_tax2 = st.columns(2)
            
            with col_tax1:
                taxonomy_levels = [
                    ('🌍 Sistem', 'Sistem'),
                    ('👑 Alem (Kingdom)', 'Alem'),
                    ('🌿 Şube (Phylum)', 'Şube'),
                    ('🦎 Sınıf (Class)', 'Sınıf')
                ]
                for label, col in taxonomy_levels:
                    if col in species_row and species_row[col]:
                        st.markdown(f"""
                            <div class='tax-row'>
                                <span class='tax-label'>{label}:</span> 
                                <span class='tax-value'>{species_row[col]}</span>
                            </div>
                        """, unsafe_allow_html=True)
            
            with col_tax2:
                taxonomy_levels2 = [
                    ('📋 Takım (Order)', 'Takım'),
                    ('👨‍👩‍👧‍👦 Aile (Family)', 'Aile'),
                    ('🔬 Tür (Species)', 'Tür'),
                    ('📝 Genel Adı', 'Genel Adı')
                ]
                for label, col in taxonomy_levels2:
                    if col in species_row and species_row[col]:
                        st.markdown(f"""
                            <div class='tax-row'>
                                <span class='tax-label'>{label}:</span> 
                                <span class='tax-value'>{species_row[col]}</span>
                            </div>
                        """, unsafe_allow_html=True)
            
            if 'Sinonim' in species_row and species_row['Sinonim']:
                st.markdown("---")
                st.markdown("### 🔄 Sinonimler (Eş Anlamlılar)")
                st.info(species_row['Sinonim'])

if __name__ == "__main__":
    main()
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
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.95;
    }
    .category-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border-radius: 20px;
        font-weight: 600;
        margin: 0.3rem;
        font-size: 0.9rem;
    }
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 4px solid #667eea;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    .stat-label {
        color: #666;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    .taxonomy-card {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #667eea;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
        background-color: #f8f9fa;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
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

# --- 3. Lokasyon Koordinat Sözlüğü ---
location_coords = {
    "İstanbul": [41.0082, 28.9784], "Büyükada": [40.8741, 29.1293], "Haliç": [41.0289, 28.9697],
    "Büyükçekmece Körfezi": [40.9922, 28.5671], "Marmara Denizi": [40.7500, 28.2500],
    "Çanakkale": [40.153, 26.405], "Çanakkale Boğazı": [40.2000, 26.4000],
    "Abide": [40.0503, 26.2192], "Kilitbahir": [40.1472, 26.3797], "Eceabat": [40.1850, 26.3575],
    "Gelibolu": [40.4100, 26.6700], "Lapseki": [40.3444, 26.6853], "Yapıldak": [40.2078, 26.5492],
    "Şevketiye": [40.3955, 26.8716], "Burhanlı Mevkii": [40.3069, 26.5593],
    "Gökçeada": [40.1889, 25.9044], "Bozcaada": [39.8322, 26.0719],
    "Balıkesir": [39.6484, 27.8826], "Bandırma": [40.3533, 27.9708], "Bandırma Körfezi": [40.3800, 27.9500],
    "Edremit Körfezi": [39.5333, 26.8500], "Ayvalık": [39.3190, 26.6960],
    "Bursa": [40.1885, 29.0610], "Yalova": [40.6549, 29.2842], "Hersek Lagünü": [40.7239, 29.5046],
    "Kocaeli": [40.8533, 29.8815], "İzmit": [40.7654, 29.9408], "İzmit Körfezi": [40.7300, 29.7000],
    "Sakarya": [40.7569, 30.3783], "Tekirdağ": [40.9780, 27.5110], "Edirne": [41.6772, 26.5557],
    "Kırklareli": [41.7355, 27.2244], "Bilecik": [40.1419, 29.9793],
    "İzmir": [38.4237, 27.1428], "İzmir Körfezi": [38.4500, 26.9000], "Alsancak Limanı": [38.4410, 27.1480],
    "Levent Marina": [38.4090, 27.0850], "Aliağa": [38.7994, 26.9723],
    "Karaburun": [38.6394, 26.5125], "Ildır": [38.3842, 26.4764], "Çeşme": [38.3232, 26.3039],
    "Seferihisar": [38.2047, 26.8378], "Sığacık": [38.2000, 26.7800], "Urla": [38.3229, 26.7635],
    "Dikili": [39.0717, 26.8872], "Dikili Açıkları": [39.0700, 26.8500],
    "Muğla": [37.2154, 28.3636], "Gökova Körfezi": [36.9500, 28.1000], "Akyaka": [37.0536, 28.3264],
    "Marmaris": [36.8550, 28.2742], "Bodrum": [37.0344, 27.4305],
    "Fethiye": [36.6217, 29.1164], "Fethiye Körfezi": [36.6500, 29.0500],
    "Göcek": [36.7550, 28.9380], "Dalyan": [36.8350, 28.6430],
    "İztuzu": [36.7900, 28.6100], "Datça Yarımadası": [36.7300, 27.6800],
    "Kuşadası": [37.8579, 27.2610], "Kuşadası Körfezi": [37.9000, 27.2000],
    "Aydın": [37.8444, 27.8458], "Manisa": [38.6191, 27.4289], "Denizli": [37.7765, 29.0864],
    "Antalya": [36.8969, 30.7133], "Antalya Körfezi": [36.7500, 30.8000], "Belek": [36.8622, 31.0556],
    "Kemer": [36.5969, 30.5597], "Kaş": [36.2000, 29.6333], "Kalkan": [36.2650, 29.4130],
    "Finike": [36.2944, 30.1464], "Alanya": [36.5437, 31.9998],
    "Mersin": [36.8121, 34.6415], "Anamur": [36.0750, 32.8358], "Silifke": [36.3778, 33.9278],
    "Adana": [37.0000, 35.3213], "Karataş": [36.5700, 35.3800], "Yumurtalık": [36.7720, 35.7930],
    "Hatay": [36.2023, 36.1606], "İskenderun": [36.5867, 36.1642], "İskenderun Körfezi": [36.6660, 35.9550],
    "Arsuz": [36.4100, 35.8800], "Samandağ": [36.0833, 35.9667],
    "Trabzon": [41.0027, 39.7168], "Rize": [41.0201, 40.5234], "Artvin": [41.1828, 41.8183],
    "Giresun": [40.9128, 38.3895], "Ordu": [40.9839, 37.8764], "Samsun": [41.2867, 36.3300],
    "Sinop": [42.0231, 35.1531], "Zonguldak": [41.4564, 31.7936], "Bartın": [41.6344, 32.3375],
    "Kastamonu": [41.3887, 33.7827], "Bolu": [40.7350, 31.6061], "Düzce": [40.8438, 31.1565],
    "Ankara": [39.9334, 32.8597], "Eskişehir": [39.7667, 30.5256], "Konya": [37.8667, 32.4800],
    "Kayseri": [38.7312, 35.4787], "Sivas": [39.7477, 37.0163],
    "Erzurum": [39.9043, 41.2691], "Van": [38.4891, 43.4089], "Elazığ": [38.6810, 39.2264],
    "Malatya": [38.3552, 38.3095], "Diyarbakır": [37.9144, 40.2306], "Şanlıurfa": [37.1591, 38.7969],
    "Gaziantep": [37.0662, 37.3833], "Iğdır": [39.9237, 44.0450]
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
        
        # Alem Filtresi
        if 'Alem' in df.columns:
            alem_options = sorted([a for a in df['Alem'].unique() if a])
            selected_alem = st.multiselect(
                "Alem (Kingdom)",
                alem_options,
                default=alem_options
            )
        else:
            selected_alem = []
        
        # Şube Filtresi
        if 'Şube' in df.columns:
            sube_options = sorted([s for s in df['Şube'].unique() if s])
            selected_sube = st.multiselect(
                "Şube (Phylum)",
                sube_options,
                default=sube_options
            )
        else:
            selected_sube = []
        
        # Sınıf Filtresi
        if 'Sınıf' in df.columns:
            sinif_options = sorted([s for s in df['Sınıf'].unique() if s])
            selected_sinif = st.multiselect(
                "Sınıf (Class)",
                sinif_options,
                default=sinif_options
            )
        else:
            selected_sinif = []
        
        # Takım Filtresi
        if 'Takım' in df.columns:
            takim_options = sorted([t for t in df['Takım'].unique() if t])
            selected_takim = st.multiselect(
                "Takım (Order)",
                takim_options,
                default=takim_options
            )
        else:
            selected_takim = []
        
        # Aile Filtresi
        if 'Aile' in df.columns:
            aile_options = sorted([a for a in df['Aile'].unique() if a])
            selected_aile = st.multiselect(
                "Aile (Family)",
                aile_options,
                default=aile_options
            )
        else:
            selected_aile = []
    
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
            
            # Taksonomik Hiyerarşi
            st.markdown("### 🧬 Taksonomik Hiyerarşi")
            taxonomy_items = [
                ('Alem', 'Alem'),
                ('Şube', 'Şube'),
                ('Sınıf', 'Sınıf'),
                ('Takım', 'Takım'),
                ('Aile', 'Aile')
            ]
            
            for label, col in taxonomy_items:
                if col in species_row and species_row[col]:
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
                    st.info("Küresel veriler yükleniyor... Bu işlem birkaç saniye sürebilir.")
            
            with col_map1:
                # Harita oluştur
                m = folium.Map(
                    location=[39.0, 35.0],
                    zoom_start=6,
                    tiles="CartoDB positron"
                )
                
                # Yerel veriler
                if show_local and 'Yerler' in species_row:
                    local_layer = MarkerCluster(name="📍 Yerel Kayıtlar")
                    
                    locations = str(species_row['Yerler']).split('\n')
                    for loc in locations:
                        loc = loc.strip()
                        if loc and loc in location_coords:
                            coords = location_coords[loc]
                            folium.Marker(
                                location=coords,
                                popup=f"<b>{target_species}</b><br>{loc}",
                                icon=folium.Icon(color="blue", icon="info-sign"),
                                tooltip=loc
                            ).add_to(local_layer)
                    
                    local_layer.add_to(m)
                
                # GBIF verileri
                if show_gbif:
                    with st.spinner("GBIF verileri yükleniyor..."):
                        gbif_results = get_gbif_data(target_species)
                        if gbif_results:
                            gbif_layer = folium.FeatureGroup(name="🌍 GBIF")
                            for rec in gbif_results:
                                if 'decimalLatitude' in rec and 'decimalLongitude' in rec:
                                    folium.CircleMarker(
                                        location=[rec['decimalLatitude'], rec['decimalLongitude']],
                                        radius=4,
                                        color="red",
                                        fill=True,
                                        fill_opacity=0.6,
                                        popup=f"GBIF: {rec.get('year', 'Tarih yok')}",
                                        tooltip="GBIF Kaydı"
                                    ).add_to(gbif_layer)
                            gbif_layer.add_to(m)
                            st.success(f"✅ {len(gbif_results)} GBIF kaydı yüklendi")
                
                # iNaturalist verileri
                if show_inaturalist:
                    with st.spinner("iNaturalist verileri yükleniyor..."):
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
                                                radius=4,
                                                color="green",
                                                fill=True,
                                                fill_opacity=0.6,
                                                popup=f"iNaturalist: {obs.get('observed_on', 'Tarih yok')}",
                                                tooltip="iNaturalist Gözlemi"
                                            ).add_to(inat_layer)
                                        except:
                                            pass
                            inat_layer.add_to(m)
                            st.success(f"✅ {len(inat_results)} iNaturalist gözlemi yüklendi")
                
                # Katman kontrolü ekle
                folium.LayerControl().add_to(m)
                
                # Haritayı göster
                st_folium(m, width=900, height=600)
        
        # --- SEKME 2: TÜR BİLGİLERİ ---
        with tab_details:
            st.subheader(f"📋 {target_species} - Detaylı Bilgiler")
            
            # Genel Ad
            if 'Genel Adı' in species_row and species_row['Genel Adı']:
                st.markdown(f"### {species_row['Genel Adı']}")
            
            # Özet
            if 'Özet' in species_row and species_row['Özet']:
                st.info(species_row['Özet'])
            
            # Detaylar
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
            
            # Etki ve Yönetim
            st.markdown("---")
            
            if 'Genel Etki Bilgisi' in species_row and species_row['Genel Etki Bilgisi']:
                st.markdown("#### ⚠️ Genel Etkileri")
                st.warning(species_row['Genel Etki Bilgisi'])
            
            if 'Genel Yönetim Bilgisi' in species_row and species_row['Genel Yönetim Bilgisi']:
                st.markdown("#### 🛠️ Yönetim ve Kontrol")
                st.success(species_row['Genel Yönetim Bilgisi'])
            
            # Giriş Yolu
            if 'Genel Giriş Yolu Bilgisi' in species_row and species_row['Genel Giriş Yolu Bilgisi']:
                st.markdown("#### 🚪 Giriş Yolu")
                st.write(species_row['Genel Giriş Yolu Bilgisi'])
            
            # Notlar
            if 'Notlar' in species_row and species_row['Notlar']:
                st.markdown("#### 📝 Notlar")
                st.info(species_row['Notlar'])
        
        # --- SEKME 3: AKADEMİK YAYINLAR ---
        with tab_papers:
            st.subheader(f"📚 {target_species} - Akademik Yayınlar")
            
            # Google Scholar Linki
            google_scholar_url = create_google_scholar_link(target_species)
            st.markdown(f"""
                <a href='{google_scholar_url}' target='_blank' 
                   style='display: inline-block; padding: 0.5rem 1.5rem; 
                          background: linear-gradient(135deg, #4285f4 0%, #34a853 100%);
                          color: white; text-decoration: none; border-radius: 5px; 
                          font-weight: 600; margin-bottom: 1rem;'>
                    🔍 Google Scholar'da Ara
                </a>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Semantic Scholar Makaleleri
            st.markdown("### 📖 Semantic Scholar Makaleleri")
            
            with st.spinner("Makaleler aranıyor..."):
                papers = get_scientific_papers_semantic(target_species)
                
                if papers:
                    for i, paper in enumerate(papers, 1):
                        with st.expander(
                            f"{i}. {paper.get('title', 'Başlıksız')} ({paper.get('year', 'Tarihsiz')})",
                            expanded=(i==1)
                        ):
                            # Yayın bilgileri
                            col_p1, col_p2 = st.columns([3, 1])
                            
                            with col_p1:
                                if paper.get('venue'):
                                    st.markdown(f"**📄 Yayın:** {paper['venue']}")
                                
                                if paper.get('authors'):
                                    authors = ", ".join([a.get('name', '') for a in paper['authors'][:5]])
                                    if len(paper['authors']) > 5:
                                        authors += f" ve diğerleri ({len(paper['authors'])} yazar)"
                                    st.markdown(f"**✍️ Yazarlar:** {authors}")
                            
                            with col_p2:
                                if paper.get('citationCount'):
                                    st.metric("📊 Atıf Sayısı", paper['citationCount'])
                            
                            # Özet
                            if paper.get('abstract'):
                                st.markdown("**📝 Özet:**")
                                st.write(paper['abstract'][:500] + "..." if len(paper['abstract']) > 500 else paper['abstract'])
                            
                            # Link
                            if paper.get('url'):
                                st.markdown(f"[🔗 Makaleyi Oku]({paper['url']})")
                else:
                    st.warning("⚠️ Semantic Scholar'da makale bulunamadı.")
                    st.info(f"💡 Daha fazla sonuç için [Google Scholar]({google_scholar_url}) üzerinden arama yapabilirsiniz.")
        
        # --- SEKME 4: TAKSONOMİK DETAYLAR ---
        with tab_taxonomy:
            st.subheader(f"🧬 {target_species} - Taksonomik Detaylar")
            
            # Taksonomik Hiyerarşi Kartı
            st.markdown("""
                <div class='taxonomy-card'>
                    <h4 style='margin-top: 0;'>📊 Taksonomik Sınıflandırma</h4>
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
                            <div style='padding: 0.8rem; margin: 0.5rem 0; 
                                        background: #f8f9fa; border-left: 3px solid #667eea;
                                        border-radius: 5px;'>
                                <strong>{label}:</strong> {species_row[col]}
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
                            <div style='padding: 0.8rem; margin: 0.5rem 0; 
                                        background: #f8f9fa; border-left: 3px solid #764ba2;
                                        border-radius: 5px;'>
                                <strong>{label}:</strong> {species_row[col]}
                            </div>
                        """, unsafe_allow_html=True)
            
            # Sinonim Bilgisi
            if 'Sinonim' in species_row and species_row['Sinonim']:
                st.markdown("---")
                st.markdown("### 🔄 Sinonimler (Eş Anlamlılar)")
                st.info(species_row['Sinonim'])

if __name__ == "__main__":
    main()

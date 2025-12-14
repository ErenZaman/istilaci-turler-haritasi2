# 🌿 İstilacı Türler Veri Tabanı - Kullanım Kılavuzu

## 📋 Genel Bakış

Bu uygulama, Türkiye'deki istilacı türlerin detaylı bilgilerini, coğrafi dağılımını ve akademik kaynaklarını tek bir platformda sunan gelişmiş bir veri tabanı sistemidir.

## ✨ Yeni Özellikler

### 🎨 Geliştirilmiş Tasarım
- **Modern Gradient Renkler**: Göz alıcı mor-mavi gradient tasarım
- **İnteraktif Kartlar**: İstatistik kartları ve taksonomik kartlar
- **Responsive Layout**: Farklı ekran boyutlarına uyumlu tasarım
- **Geliştirilmiş Sekmeler**: Daha profesyonel görünümlü sekme yapısı

### 🔬 Taksonomik Özellikler
Artık her tür için tam taksonomik hiyerarşi görüntülenebiliyor:
- **Sistem**: Karasal / Sucul
- **Alem** (Kingdom): Animalia, Plantae, vb.
- **Şube** (Phylum): Chordata, Spermatophyta, vb.
- **Sınıf** (Class): Aves, Dicotyledonae, vb.
- **Takım** (Order): Passeriformes, Euphorbiales, vb.
- **Aile** (Family): Sturnidae, Euphorbiaceae, vb.
- **Tür** (Species): Bilimsel tür adı

### 📚 Geliştirilmiş Literatür Tarama
1. **Semantic Scholar API**: Akademik makalelerin otomatik taranması
   - Makale başlığı, özet ve yazarlar
   - Yayın yeri ve yılı
   - Atıf sayısı
   - Direkt makale linki

2. **Google Scholar Entegrasyonu**: 
   - Tek tıkla Google Scholar'da arama
   - Otomatik sorgu oluşturma
   - Yeni sekmede açılma

### 🗺️ Geliştirilmiş Harita Özellikleri

#### Veri Kaynakları:
1. **📍 Yerel Kayıtlar** (Mavi işaretler)
   - Türkiye'deki kayıtlı lokasyonlar
   - Kümelenmiş görünüm
   - Detaylı popup bilgileri

2. **🌍 GBIF Verileri** (Kırmızı işaretler)
   - Global Biodiversity Information Facility
   - Dünya çapında kayıtlar
   - Yıl bilgisi ile birlikte

3. **🦋 iNaturalist Verileri** (Yeşil işaretler)
   - Vatandaş bilimi gözlemleri
   - Tarih bilgisi ile birlikte
   - Doğrulanmış kayıtlar

#### Harita Kontrolleri:
- Katman seçici ile veri kaynaklarını göster/gizle
- Her kaynak için ayrı renk kodlaması
- Popup bilgiler ile detaylı kayıt bilgileri
- Marker clustering ile performans optimizasyonu

### 🔍 Gelişmiş Filtreleme Sistemi

Artık tüm taksonomik seviyelerde filtreleme yapabilirsiniz:
- **Sistem**: Karasal / Sucul
- **Alem**: Kingdom seviyesi
- **Şube**: Phylum seviyesi
- **Sınıf**: Class seviyesi
- **Takım**: Order seviyesi
- **Aile**: Family seviyesi

Her filtre bağımsız çalışır ve birden fazla seçim yapılabilir.

### 📊 İstatistikler Paneli

Ana sayfada görünen istatistik kartları:
- Toplam tür sayısı
- Benzersiz sistem sayısı
- Benzersiz sınıf sayısı
- Benzersiz aile sayısı

### 📋 Detaylı Tür Bilgileri

Her tür için aşağıdaki bilgiler mevcut:
- **Genel Bilgiler**: Tür tanımı, özet, genel adı
- **Yaşam Alanı**: Habitat tercihleri ve coğrafi dağılım
- **Biyoloji**: Üreme, beslenme, yaşam döngüsü
- **Etkiler**: Genel etki bilgisi
- **Yönetim**: Kontrol ve yönetim stratejileri
- **Giriş Yolu**: Türkiye'ye giriş yolları
- **Notlar**: Ek bilgiler ve önemli notlar
- **Sinonimler**: Bilimsel eş anlamlılar

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler

```bash
pip install streamlit pandas folium streamlit-folium requests openpyxl
```

### Çalıştırma

```bash
streamlit run app_yeni.py
```

Uygulama varsayılan olarak `http://localhost:8501` adresinde açılacaktır.

## 📁 Veri Formatı

Uygulama aşağıdaki sütunları içeren CSV veya Excel dosyalarını kabul eder:

### Zorunlu Sütunlar:
- **Tür**: Bilimsel tür adı
- **Sistem**: Karasal / Sucul

### İsteğe Bağlı Sütunlar:
- **Alem**: Kingdom
- **Şube**: Phylum
- **Sınıf**: Class
- **Takım**: Order
- **Aile**: Family
- **Sinonim**: Eş anlamlı türler
- **Genel Adı**: Türkçe genel adı
- **Özet**: Kısa özet
- **Tür Tanımı**: Detaylı tanım
- **Yaşam Alanı**: Habitat bilgileri
- **Üreme Bilgisi**: Üreme özellikleri
- **Yaşam Döngüsü**: Yaşam evresi bilgileri
- **Beslenme Bilgisi**: Beslenme alışkanlıkları
- **Genel Etki Bilgisi**: Ekosistem etkileri
- **Genel Yönetim Bilgisi**: Kontrol stratejileri
- **Genel Giriş Yolu Bilgisi**: Giriş yolları
- **Notlar**: Ek bilgiler
- **Yerler**: Lokasyon listesi (satır başı ile ayrılmış)

## 🗺️ Lokasyon Sistemı

Uygulama, Türkiye'nin tüm illerini ve önemli bölgelerini içeren kapsamlı bir koordinat sözlüğü kullanır. "Yerler" sütununda belirtilen lokasyonlar otomatik olarak haritada işaretlenir.

### Desteklenen Lokasyonlar:
- Tüm iller
- Önemli körfezler ve kıyı bölgeleri
- Milli parklar ve koruma alanları
- Önemli su kaynakları

## 🎯 Kullanım Senaryoları

### 1. Araştırmacılar için:
- Türlerin detaylı taksonomik sınıflandırması
- Akademik kaynaklara hızlı erişim
- Coğrafi dağılım analizi
- İlgili makaleleri bulma

### 2. Yöneticiler için:
- Türlerin etki alanlarını görüntüleme
- Yönetim stratejilerini inceleme
- Yayılım haritalarını analiz etme
- İstila riski taşıyan alanları belirleme

### 3. Eğitimciler için:
- Görsel öğretim materyali
- Taksonomik hiyerarşi öğretimi
- Ekosistem etkilerini gösterme
- İnteraktif sunum aracı

### 4. Vatandaşlar için:
- İstilacı türleri tanıma
- Bölgesel dağılımı öğrenme
- Etkileri anlama
- Gözlem paylaşımı (iNaturalist entegrasyonu)

## 🔧 Teknik Özellikler

### API Entegrasyonları:
1. **GBIF API**: Global tür kayıtları
2. **iNaturalist API**: Vatandaş bilimi gözlemleri
3. **Semantic Scholar API**: Akademik makaleler

### Performans Optimizasyonları:
- `@st.cache_data` ile veri önbellekleme
- Asenkron API çağrıları
- Marker clustering ile harita performansı
- Lazy loading ile hızlı sayfa yükleme

### Görselleştirme Araçları:
- **Folium**: İnteraktif haritalar
- **Streamlit**: Modern web arayüzü
- **Custom CSS**: Özel gradient tasarımlar
- **Responsive Design**: Mobil uyumlu

## 📊 Veri Kaynaklarını Anlama

### GBIF (Global Biodiversity Information Facility)
- Dünya çapında en büyük biyoçeşitlilik veri tabanı
- Müzeler, herbaryumlar ve araştırma kurumlarından veriler
- Koordinatları doğrulanmış kayıtlar
- Yıl bilgisi ile tarihsel analiz

### iNaturalist
- Vatandaş bilimi platformu
- Fotoğraflı gözlemler
- Uzman doğrulaması
- Gerçek zamanlı veriler

### Semantic Scholar
- Yapay zeka destekli akademik arama
- Atıf analizi
- Açık erişim makaleler
- Özet ve yazar bilgileri

## 🎨 Renk Kodları

- **Mavi**: Yerel kayıtlar (Türkiye)
- **Kırmızı**: GBIF kayıtları (Küresel)
- **Yeşil**: iNaturalist gözlemleri
- **Mor Gradient**: Ana tema rengi

## 💡 İpuçları

1. **Filtreleme**: Birden fazla filtre aynı anda kullanılabilir
2. **Harita**: Katman kontrolü ile veri kaynaklarını yönetin
3. **Akademik Arama**: Her iki kaynağı da kontrol edin (Semantic Scholar + Google Scholar)
4. **Taksonomik Detaylar**: Tam hiyerarşi için ayrı sekmeyi kullanın
5. **Fotoğraflar**: GBIF'ten otomatik olarak çekilir
6. **Performans**: Tüm küresel verileri aynı anda açmayın

## 🐛 Bilinen Sınırlamalar

1. **API Rate Limits**: API'ler günlük istek limitlerine sahiptir
2. **Fotoğraf Erişimi**: Bazı türler için fotoğraf bulunamayabilir
3. **Koordinat Eşleşmesi**: Sadece tanımlı lokasyonlar haritada görünür
4. **Veri Güncelliği**: API verileri gerçek zamanlı değildir

## 📞 Destek ve Katkı

Bu uygulama açık kaynak mantığıyla geliştirilmiştir. Önerileriniz ve katkılarınız için:
- Hata bildirimleri
- Yeni özellik önerileri
- Veri ekleme talepleri
- Tasarım iyileştirmeleri

## 📝 Lisans

Bu uygulama eğitim ve araştırma amaçlı geliştirilmiştir.

## 🙏 Teşekkürler

- GBIF veri sağlayıcılarına
- iNaturalist topluluğuna
- Semantic Scholar ekibine
- Streamlit topluluğuna

---

**Son Güncelleme**: Aralık 2024
**Versiyon**: 2.0 - Yeni Geliştirilmiş Sürüm

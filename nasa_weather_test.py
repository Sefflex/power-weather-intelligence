import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="NASA POWER API Test",
    layout="wide"
)

# Modern tasarım
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 30px;
        color: white;
    }
    .coord-display {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 20px 0;
        border: 2px solid rgba(255,255,255,0.3);
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    }
    .location-info {
        background: rgba(255,255,255,0.1);
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        border-left: 5px solid #00b09b;
    }
    .success-box {
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        margin: 15px 0;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    .error-box {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        margin: 15px 0;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    .input-card {
        background: rgba(255,255,255,0.95);
        padding: 25px;
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    .stButton>button {
        border-radius: 10px;
        height: 50px;
        font-weight: 600;
        margin: 8px 0;
        transition: all 0.3s ease;
        border: none;
    }
    .primary-btn {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%) !important;
        color: white !important;
        font-size: 1.1em !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🔬 NASA POWER API TEST UYGULAMASI</h1><p>Enlem-Boylam ile Gerçek Hava Verilerini Çekin</p></div>', unsafe_allow_html=True)

# NASA POWER API fonksiyonları
def get_nasa_power_data(lat, lon, start_date, end_date, data_type="daily"):
    """
    NASA POWER API'den veri çeker
    """
    if data_type == "daily":
        url = "https://power.larc.nasa.gov/api/temporal/daily/point"
        params = {
            'parameters': 'T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M,ALLSKY_SFC_SW_DWN',
            'community': 'RE',
            'longitude': lon,
            'latitude': lat,
            'start': start_date.strftime("%Y%m%d"),
            'end': end_date.strftime("%Y%m%d"),
            'format': 'JSON'
        }
    else:
        url = "https://power.larc.nasa.gov/api/temporal/climatology/point"
        params = {
            'parameters': 'T2M,PRECTOTCORR,RH2M,WS2M',
            'community': 'RE',
            'longitude': lon,
            'latitude': lat,
            'start': start_date,
            'end': end_date,
            'format': 'JSON'
        }
    
    try:
        st.info(f"🌍 NASA POWER API'ye istek gönderiliyor...")
        
        with st.expander("🔧 API İstek Detayları"):
            st.write(f"**URL:** `{url}`")
            st.write(f"**Parametreler:**")
            st.json(params)
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'properties' in data and 'parameter' in data['properties']:
                st.success("✅ Veriler başarıyla alındı!")
                return {
                    'status': 'success',
                    'data': data,
                    'message': 'Veri başarıyla çekildi'
                }
            else:
                return {
                    'status': 'error',
                    'data': None,
                    'message': 'API yanıtı beklenen formatta değil'
                }
        else:
            return {
                'status': 'error', 
                'data': None,
                'message': f'API hatası: {response.status_code} - {response.text}'
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'data': None,
            'message': f'Bağlantı hatası: {str(e)}'
        }

def parse_nasa_data(raw_data, data_type="daily"):
    """NASA verilerini işle ve DataFrame'e dönüştür"""
    if not raw_data or 'properties' not in raw_data:
        return None
    
    parameters = raw_data['properties']['parameter']
    
    if data_type == "daily":
        dfs = []
        for param_name, param_data in parameters.items():
            dates = []
            values = []
            for date_str, value in param_data.items():
                date_obj = datetime.strptime(date_str, '%Y%m%d')
                dates.append(date_obj)
                values.append(value)
            
            df_param = pd.DataFrame({
                'date': dates,
                'parameter': param_name,
                'value': values
            })
            dfs.append(df_param)
        
        if dfs:
            final_df = pd.concat(dfs, ignore_index=True)
            param_names = {
                'T2M': 'Sıcaklık (°C)',
                'T2M_MAX': 'Max Sıcaklık (°C)',
                'T2M_MIN': 'Min Sıcaklık (°C)',
                'PRECTOTCORR': 'Yağış (mm/gün)',
                'RH2M': 'Nem (%)',
                'WS2M': 'Rüzgar Hızı (m/s)',
                'ALLSKY_SFC_SW_DWN': 'Güneş Radyasyonu (kW-h/m²/gün)'
            }
            final_df['parameter_name'] = final_df['parameter'].map(param_names)
            final_df['parameter_name'] = final_df['parameter_name'].fillna(final_df['parameter'])
            return final_df
    else:
        climate_data = []
        months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        for param_name, param_data in parameters.items():
            for month in months:
                if month in param_data:
                    climate_data.append({
                        'parameter': param_name,
                        'month': month,
                        'value': param_data[month]
                    })
        
        if climate_data:
            df = pd.DataFrame(climate_data)
            param_names = {
                'T2M': 'Ortalama Sıcaklık (°C)',
                'PRECTOTCORR': 'Ortalama Yağış (mm/gün)',
                'RH2M': 'Ortalama Nem (%)',
                'WS2M': 'Ortalama Rüzgar Hızı (m/s)'
            }
            df['parameter_name'] = df['parameter'].map(param_names)
            df['parameter_name'] = df['parameter_name'].fillna(df['parameter'])
            month_order = {month: i for i, month in enumerate(months)}
            df['month_order'] = df['month'].map(month_order)
            df = df.sort_values('month_order')
            return df
    
    return None

# Session State başlatma
if 'lat' not in st.session_state:
    st.session_state.lat = 39.9334
if 'lon' not in st.session_state:
    st.session_state.lon = 32.8597
if 'selected_city' not in st.session_state:
    st.session_state.selected_city = "Ankara"

# ANA ARAYÜZ
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📍 Konum Bilgileri")
    
    # Koordinat Giriş Kartı
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    
    # Hızlı şehir seçimi
    cities = {
        "İstanbul": (41.0082, 28.9784),
        "Ankara": (39.9334, 32.8597),
        "İzmir": (38.4237, 27.1428),
        "Antalya": (36.8969, 30.7133),
        "Trabzon": (41.0027, 39.7168),
        "Bodrum": (37.0384, 27.4293),
        "New York": (40.7128, -74.0060),
        "Tokyo": (35.6762, 139.6503),
        "Londra": (51.5074, -0.1278)
    }
    
    selected_city = st.selectbox(
        "🏙️ Hızlı Şehir Seçin", 
        list(cities.keys()),
        index=list(cities.keys()).index(st.session_state.selected_city)
    )
    
    # Şehir seçildiyse koordinatları güncelle
    if selected_city and selected_city != st.session_state.selected_city:
        st.session_state.lat, st.session_state.lon = cities[selected_city]
        st.session_state.selected_city = selected_city
    
    st.markdown("**📍 Manuel Koordinat Girişi:**")
    
    coord_col1, coord_col2 = st.columns(2)
    with coord_col1:
        manual_lat = st.number_input(
            "Enlem (Latitude)", 
            min_value=-90.0, 
            max_value=90.0, 
            value=st.session_state.lat, 
            format="%.6f",
            help="Kuzey için pozitif, Güney için negatif (-90 ile +90 arası)"
        )
    with coord_col2:
        manual_lon = st.number_input(
            "Boylam (Longitude)", 
            min_value=-180.0, 
            max_value=180.0, 
            value=st.session_state.lon, 
            format="%.6f",
            help="Doğu için pozitif, Batı için negatif (-180 ile +180 arası)"
        )
    
    # Manuel koordinat güncelleme butonu
    if st.button("📍 Koordinatları Ayarla", use_container_width=True):
        st.session_state.lat = manual_lat
        st.session_state.lon = manual_lon
        st.session_state.selected_city = "Özel Konum"
        st.success("✅ Koordinatlar güncellendi!")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown("### 📅 Tarih Aralığı")
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    
    data_type = st.radio(
        "**📊 Veri Tipi Seçin:**",
        ["Günlük Veri", "İklim Verisi"],
        horizontal=True
    )
    
    if data_type == "Günlük Veri":
        today = datetime.now().date()
        start_date = st.date_input(
            "Başlangıç Tarihi", 
            value=today - timedelta(days=30),
            max_value=today
        )
        end_date = st.date_input(
            "Bitiş Tarihi", 
            value=today,
            max_value=today
        )
        
        if start_date > end_date:
            st.error("❌ Başlangıç tarihi bitiş tarihinden sonra olamaz!")
        elif (end_date - start_date).days > 365:
            st.warning("⚠️ 1 yıldan uzun süreler için İklim Verisi kullanmanız önerilir")
        
    else:
        col_year1, col_year2 = st.columns(2)
        with col_year1:
            start_year = st.number_input(
                "Başlangıç Yılı", 
                min_value=1984, 
                max_value=2023, 
                value=2018,
                help="NASA verileri 1984'ten itibaren mevcut"
            )
        with col_year2:
            end_year = st.number_input(
                "Bitiş Yılı", 
                min_value=1984, 
                max_value=2023, 
                value=2023
            )
        
        if start_year > end_year:
            st.error("❌ Başlangıç yılı bitiş yılından sonra olamaz!")
    
    st.markdown('</div>', unsafe_allow_html=True)

# SEÇİLEN KONUM BİLGİSİ
st.markdown(f"""
<div class="coord-display">
    <h3>🎯 SEÇİLEN KONUM BİLGİLERİ</h3>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 15px 0;">
        <div style="text-align: center;">
            <h4 style="margin: 0; color: #ffeb3b;">ENLEM</h4>
            <p style="font-size: 2em; margin: 5px 0; font-weight: bold;">{st.session_state.lat:.6f}°</p>
            <small>{'Kuzey' if st.session_state.lat >= 0 else 'Güney'} Yarımküre</small>
        </div>
        <div style="text-align: center;">
            <h4 style="margin: 0; color: #ffeb3b;">BOYLAM</h4>
            <p style="font-size: 2em; margin: 5px 0; font-weight: bold;">{st.session_state.lon:.6f}°</p>
            <small>{'Doğu' if st.session_state.lon >= 0 else 'Batı'} Yarımküre</small>
        </div>
    </div>
    <p style="margin: 10px 0 0 0; font-size: 1.1em;">
        <strong>📍 Konum:</strong> {st.session_state.selected_city} | 
        <strong>🌍 Koordinat Sistemi:</strong> WGS84
    </p>
</div>
""", unsafe_allow_html=True)

# VERİ ÇEKME BUTONU
st.markdown("---")
if st.button("🚀 NASA VERİLERİNİ ÇEK", type="primary", use_container_width=True, key="fetch_data"):
    
    with st.spinner("NASA POWER API'den veriler çekiliyor..."):
        if data_type == "Günlük Veri":
            result = get_nasa_power_data(
                st.session_state.lat, 
                st.session_state.lon, 
                start_date, 
                end_date,
                "daily"
            )
        else:
            result = get_nasa_power_data(
                st.session_state.lat,
                st.session_state.lon,
                str(start_year),
                str(end_year), 
                "climatology"
            )
    
    # Sonuçları göster
    if result['status'] == 'success':
        st.markdown(f'<div class="success-box"><h3>✅ VERİLER BAŞARIYLA ÇEKİLDİ!</h3><p>{result["message"]}</p></div>', unsafe_allow_html=True)
        
        # Verileri işle
        df = parse_nasa_data(result['data'], "daily" if data_type == "Günlük Veri" else "climatology")
        
        if df is not None:
            st.session_state.nasa_data = df
            st.session_state.raw_data = result['data']
            st.session_state.data_type = data_type
        else:
            st.error("❌ Veri işleme hatası!")
            
    else:
        st.markdown(f'<div class="error-box"><h3>❌ HATA OLUŞTU!</h3><p>{result["message"]}</p></div>', unsafe_allow_html=True)

# VERİLERİ GÖSTERME
if 'nasa_data' in st.session_state and st.session_state.nasa_data is not None:
    df = st.session_state.nasa_data
    
    st.markdown("---")
    st.markdown("## 📊 NASA POWER VERİ ANALİZİ")
    
    # Konum bilgisi
    st.markdown(f"""
    <div class="location-info">
        <h4>📍 ANALİZ EDİLEN KONUM</h4>
        <p><strong>Enlem:</strong> {st.session_state.lat:.6f}° | <strong>Boylam:</strong> {st.session_state.lon:.6f}°</p>
        <p><strong>Yer:</strong> {st.session_state.selected_city} | <strong>Veri Tipi:</strong> {st.session_state.data_type}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Ham veri gösterimi
    with st.expander("🔍 HAM JSON VERİSİNİ GÖSTER"):
        st.json(st.session_state.raw_data)
    
    if st.session_state.data_type == "Günlük Veri":
        # Günlük veri analizi
        st.markdown("### 📈 Zaman Serisi Grafikleri")
        
        parameters = df['parameter_name'].unique()
        selected_params = st.multiselect(
            "Grafikte Gösterilecek Parametreler", 
            parameters, 
            default=parameters[:3] if len(parameters) >= 3 else parameters
        )
        
        if selected_params:
            filtered_df = df[df['parameter_name'].isin(selected_params)]
            
            # Çizgi grafiği
            fig = px.line(
                filtered_df, 
                x='date', 
                y='value', 
                color='parameter_name',
                title=f'NASA POWER - {st.session_state.selected_city} Zaman Serisi Verileri',
                labels={'value': 'Değer', 'date': 'Tarih', 'parameter_name': 'Parametre'}
            )
            fig.update_layout(
                height=500,
                hovermode='x unified',
                title_x=0.5
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Veri tablosu
        st.markdown("### 📋 HAM VERİ TABLOSU")
        pivot_df = df.pivot_table(
            index='date', 
            columns='parameter_name', 
            values='value'
        ).reset_index()
        
        st.dataframe(pivot_df, use_container_width=True)
        
        # İstatistikler
        st.markdown("### 📊 İSTATİSTİKSEL ÖZET")
        stats_df = df.groupby('parameter_name')['value'].describe()
        st.dataframe(stats_df.style.format("{:.2f}"), use_container_width=True)
        
    else:
        # İklim verisi analizi
        st.markdown("### 📊 AYLIK İKLİM ORTALAMALARI")
        
        climate_param = st.selectbox("Grafik Parametresi", df['parameter_name'].unique())
        
        if climate_param:
            param_df = df[df['parameter_name'] == climate_param]
            
            fig = px.bar(
                param_df,
                x='month',
                y='value',
                title=f'{st.session_state.selected_city} - {climate_param} Aylık Ortalamaları ({start_year}-{end_year})',
                labels={'value': 'Değer', 'month': 'Ay'},
                color='value',
                color_continuous_scale='viridis'
            )
            fig.update_layout(height=500, title_x=0.5)
            st.plotly_chart(fig, use_container_width=True)
        
        # İklim verisi tablosu
        st.markdown("### 📋 İKLİM VERİ TABLOSU")
        climate_pivot = df.pivot_table(
            index='month',
            columns='parameter_name', 
            values='value'
        ).reset_index()
        
        st.dataframe(climate_pivot.style.format("{:.2f}"), use_container_width=True)

# BİLGİ KUTULARI
col_info1, col_info2 = st.columns(2)

with col_info1:
    with st.expander("ℹ️ KOORDİNAT SİSTEMİ BİLGİSİ"):
        st.markdown("""
        **WGS84 Koordinat Sistemi:**
        - **Enlem (Latitude):** -90° (Güney) ile +90° (Kuzey) arası
        - **Boylam (Longitude):** -180° (Batı) ile +180° (Doğu) arası
        
        **Türkiye Koordinat Aralıkları:**
        - Enlem: 36°K - 42°K
        - Boylam: 26°D - 45°D
        
        **Örnek Koordinatlar:**
        - İstanbul: 41.0082°K, 28.9784°D
        - Ankara: 39.9334°K, 32.8597°D
        """)

with col_info2:
    with st.expander("🔧 NASA POWER API BİLGİSİ"):
        st.markdown("""
        **NASA POWER API Özellikleri:**
        - **Çözünürlük:** 1° x 1° (≈111km)
        - **Veri Kaynağı:** Satellite + Yer istasyonları
        - **Kapsam:** Global, 1984'ten günümüze
        - **Güncelleme:** Gerçek zamanlı
        
        **Parametre Açıklamaları:**
        - **T2M:** 2m yükseklikte sıcaklık
        - **PRECTOTCORR:** Düzeltilmiş yağış
        - **RH2M:** Bağıl nem
        - **WS2M:** Rüzgar hızı
        """)

# TEST KOORDİNATLARI
with st.expander("🧪 TEST İÇİN ÖRNEK KOORDİNATLAR"):
    test_coords = {
        "Sahra Çölü": (23.8061, 11.2881),
        "Amazon Yağmur Ormanı": (-3.4653, -62.2159),
        "Himalayalar": (27.9881, 86.9250),
        "Kutup Dairesi": (66.5636, 0.0000),
        "Büyük Okyanus": (0.0000, -150.0000)
    }
    
    cols = st.columns(len(test_coords))
    for idx, (name, coords) in enumerate(test_coords.items()):
        with cols[idx]:
            if st.button(f"📍 {name}", key=f"test_{name}", use_container_width=True):
                st.session_state.lat = coords[0]
                st.session_state.lon = coords[1]
                st.session_state.selected_city = name
                st.success(f"{name} koordinatları yüklendi!")

st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#666;">
    <p>🔬 NASA POWER API Test Uygulaması | 🌍 Gerçek Zamanlı İklim Verileri | 📍 Enlem-Boylam Bazlı Analiz</p>
</div>
""", unsafe_allow_html=True)
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="DSS Portofolio Saham Syariah (JII)", layout="wide")

# --- KUSTOMISASI CSS WARNA PASTEL COKLAT (EARTH TONE) ---
st.markdown("""
<style>
    :root {
        --background-color: #FDFBF7 !important;
        --secondary-background-color: #F4ECE1 !important;
        --text-color: #4A3B32 !important;
    }

    .stApp, 
    [data-testid="stAppViewContainer"], 
    [data-testid="stHeader"], 
    [data-testid="stToolbar"],
    section.main {
        background-color: #FDFBF7 !important;
        color: #4A3B32 !important;
    }
    
    [data-testid="stSidebar"], 
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {
        background-color: #F4ECE1 !important;
    }
    
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #4A3B32 !important;
    }

    .streamlit-expanderHeader {
        background-color: #EFE6D8 !important;
        color: #4A3B32 !important;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- JUDUL UTAMA APLIKASI ---
st.title("🕌 Sistem Pendukung Keputusan (DSS) Portofolio Saham Syariah (JII)")
st.markdown(
    "Aplikasi analisis portofolio syariah lengkap dengan **rumus, angka, penjelasan rinci, dan kesimpulan** "
    "di setiap 6 Sheet dengan opsi **Data Otomatis (Yahoo Finance)** atau **Upload File Mandiri**."
)

# --- 1. DAFTAR RESMI SAHAM JII ---
DAFTAR_SAHAM_JII = {
    "BRIS.JK": "BRIS - Bank Syariah Indonesia Tbk.",
    "CTRA.JK": "CTRA - Ciputra Development Tbk.",
    "TLKM.JK": "TLKM - Telkom Indonesia (Persero) Tbk.",
    "AADI.JK": "AADI - Adaro Andalan Indonesia Tbk.",
    "ADRO.JK": "ADRO - Alamtri Resources Indonesia Tbk.",
    "ANTM.JK": "ANTM - Aneka Tambang Tbk.",
    "CPIN.JK": "CPIN - Charoen Pokphand Indonesia Tbk.",
    "ICBP.JK": "ICBP - Indofood CBP Sukses Makmur Tbk.",
    "INDF.JK": "INDF - Indofood Sukses Makmur Tbk.",
    "KLBF.JK": "KLBF - Kalbe Farma Tbk.",
    "UNTR.JK": "UNTR - United Tractors Tbk.",
    "UNVR.JK": "UNVR - Unilever Indonesia Tbk."
}

# --- 2. SIDEBAR: SUMBER DATA & PENGATURAN ---
st.sidebar.header("⚙️ Pengaturan & Sumber Data")

sumber_data = st.sidebar.radio(
    "Pilih Sumber Data:",
    options=["Otomatis (Yahoo Finance)", "Upload File Sendiri (Excel/CSV)"]
)

df_harga_display = None

if sumber_data == "Upload File Sendiri (Excel/CSV)":
    uploaded_file = st.sidebar.file_uploader("Unggah file data harga Close (.xlsx / .csv):", type=["xlsx", "csv"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_uploaded = pd.read_csv(uploaded_file)
            else:
                df_uploaded = pd.read_excel(uploaded_file)
            
            # Deteksi kolom Tanggal
            kolom_tanggal = [c for c in df_uploaded.columns if "tanggal" in c.lower() or "date" in c.lower()]
            if kolom_tanggal:
                df_uploaded[kolom_tanggal[0]] = pd.to_datetime(df_uploaded[kolom_tanggal[0]])
                df_uploaded = df_uploaded.set_index(kolom_tanggal[0])
            
            # Bersihkan nama kolom harga
            df_harga_display = df_uploaded.select_dtypes(include=[np.number])
            if "No" in df_harga_display.columns:
                df_harga_display = df_harga_display.drop(columns=["No"])
            st.sidebar.success("✅ File berhasil dimuat!")
        except Exception as e:
            st.sidebar.error(f"Gagal membaca file: {e}")
            st.stop()
    else:
        st.info("👈 Silakan unggah file Excel/CSV Anda melalui panel di sebelah kiri.")
        st.stop()

else:
    saham_terpilih = st.sidebar.multiselect(
        "1. Pilih Saham Konstituen JII (Min. 2):",
        options=list(DAFTAR_SAHAM_JII.keys()),
        default=["BRIS.JK", "CTRA.JK", "TLKM.JK"],
        format_func=lambda x: DAFTAR_SAHAM_JII[x]
    )

    if len(saham_terpilih) < 2:
        st.warning("⚠️ Silakan pilih minimal **2 saham JII** di menu sebelah kiri.")
        st.stop()

    pilihan_mode_waktu = st.sidebar.radio(
        "2. Mode Filter Waktu:",
        options=["Pilih Tahun Spesifik", "Rentang Tanggal Custom"]
    )

    if pilihan_mode_waktu == "Pilih Tahun Spesifik":
        tahun_pilihan = st.sidebar.selectbox("Pilih Tahun:", options=[2026, 2025, 2024, 2023, 2022], index=0)
        tanggal_mulai = pd.to_datetime(f"{tahun_pilihan}-01-01")
        tanggal_selesai = pd.to_datetime(f"{tahun_pilihan}-12-31")
        if tahun_pilihan == 2026:
            tanggal_selesai = pd.Timestamp.today()
        periode_yf = "max"
    else:
        rentang_tanggal = st.sidebar.date_input(
            "Pilih Rentang Tanggal Mulai & Akhir:",
            value=(pd.to_datetime("2026-01-01"), pd.Timestamp.today().date())
        )
        if len(rentang_tanggal) == 2:
            tanggal_mulai, tanggal_selesai = pd.to_datetime(rentang_tanggal[0]), pd.to_datetime(rentang_tanggal[1])
        else:
            tanggal_mulai, tanggal_selesai = pd.to_datetime("2026-01-01"), pd.Timestamp.today()
        periode_yf = "max"

    @st.cache_data(ttl=3600)
    def ambil_data_saham(tickers, period):
        df_download = yf.download(tickers, period=period, progress=False)
        if isinstance(df_download.columns, pd.MultiIndex):
            data = df_download["Close"]
        else:
            data = df_download[["Close"]] if "Close" in df_download.columns else df_download

        if isinstance(data, pd.Series):
            data = data.to_frame(name=tickers[0])
        return data.dropna()

    with st.spinner("Mengambil data real-time saham JII dari Yahoo Finance..."):
        df_raw = ambil_data_saham(saham_terpilih, periode_yf)

    if df_raw.empty:
        df_raw = yf.download(saham_terpilih, period="2y", progress=False)["Close"]

    df_raw = df_raw[saham_terpilih]
    df_raw.index = pd.to_datetime(df_raw.index)
    df_filtered = df_raw[(df_raw.index >= tanggal_mulai) & (df_raw.index <= tanggal_selesai)]

    if df_filtered.empty:
        df_filtered = df_raw.tail(100)

    periode_hitung = st.sidebar.selectbox(
        "3. Pilih Frekuensi Perhitungan:",
        options=["Mingguan", "Harian", "Bulanan", "Semester (6 Bulan)", "Tahunan"]
    )

    aturan_periode = {
        "Harian": {"rule": None, "faktor": 252, "label_faktor": "252 hari bursa"},
        "Mingguan": {"rule": "W-FRI", "faktor": 52, "label_faktor": "52 minggu"},
        "Bulanan": {"rule": "ME", "faktor": 12, "label_faktor": "12 bulan"},
        "Semester (6 Bulan)": {"rule": "2QE", "faktor": 2, "label_faktor": "2 semester (faktor 2)"},
        "Tahunan": {"rule": "YE", "faktor": 1, "label_faktor": "1 tahun"}
    }

    faktor_waktu = aturan_periode[periode_hitung]["faktor"]
    label_faktor_teks = aturan_periode[periode_hitung]["label_faktor"]

    if periode_hitung == "Harian":
        df_harga = df_filtered.dropna()
    else:
        rule_terpilih = aturan_periode[periode_hitung]["rule"]
        df_harga = df_filtered.resample(rule_terpilih).last().dropna()

    df_harga_display = df_harga.copy()
    df_harga_display.columns = [c.replace(".JK", "") for c in df_harga_display.columns]

# Pengaturan Umum untuk Perhitungan
if sumber_data == "Upload File Sendiri (Excel/CSV)":
    periode_hitung = "Periode Upload"
    faktor_waktu = 52
    label_faktor_teks = "52 minggu (standar)"

saham_terpilih_list = list(df_harga_display.columns)

# Return & Statistik
df_return = df_harga_display.pct_change().fillna(0)
df_return_stats = df_harga_display.pct_change().dropna()
if df_return_stats.empty:
    df_return_stats = df_return

mean_return_stats = df_return_stats.mean()
cov_matrix_stats = df_return_stats.cov()
std_stats = df_return_stats.std()

# Sidebar Bobot & Parameter Kinerja
st.sidebar.subheader("⚖️ Atur Bobot Investasi (%)")
mode_bobot = st.sidebar.radio(
    "Metode Penentuan Bobot:",
    options=["Manual (Slider)", "Bobot Berimbang (Equal Weight)"]
)

bobot_input = []
for saham in saham_terpilih_list:
    val_default = int(round(100 / len(saham_terpilih_list)))
    if mode_bobot == "Bobot Berimbang (Equal Weight)":
        val_default = int(round(100 / len(saham_terpilih_list)))
    nilai = st.sidebar.slider(f"Bobot {saham} (%)", min_value=0, max_value=100, value=val_default)
    bobot_input.append(nilai)

total_bobot = sum(bobot_input)
if total_bobot == 0:
    total_bobot = 1
weights = np.array(bobot_input) / total_bobot

st.sidebar.subheader("📈 Parameter Kinerja (Benchmark & Rf)")
risk_free_rate = st.sidebar.number_input("Bunga Bebas Risiko (Rf - Tahunan)", value=0.06, step=0.005, format="%.3f")
market_return = st.sidebar.number_input("Expected Return Pasar (Rm - Tahunan)", value=0.10, step=0.005, format="%.3f")

WARNA_PASTEL = ["#B08968", "#D4A373", "#CCD5AE", "#99582A", "#6F4E37", "#BC6C25", "#E6CCB2"]


# =====================================================================
# STRUKTUR 6 SHEET LENGKAP DENGAN RUMUS, ANGKA, PENJELASAN & KESIMPULAN
# =====================================================================

# --- SHEET 1: HARGA CLOSE ---
st.header(f"1️⃣ Sheet 1: Harga Close ({periode_hitung})")
df_sheet1 = df_harga_display.reset_index()
if 'Tanggal' in df_sheet1.columns:
    df_sheet1 = df_sheet1.rename(columns={'Tanggal': 'Periode/Tanggal'})
else:
    df_sheet1.rename(columns={df_sheet1.columns[0]: 'Periode/Tanggal'}, inplace=True)

df_sheet1.insert(0, "No", range(1, len(df_sheet1) + 1))
st.dataframe

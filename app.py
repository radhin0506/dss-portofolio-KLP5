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
    "Aplikasi analisis portofolio syariah berdasarkan konstituen **Jakarta Islamic Index (JII)** "
    "di Bursa Efek Indonesia (BEI) secara *real-time*."
)

# --- 1. DAFTAR RESMI 30 SAHAM KONSTITUEN INDEKS JII ---
DAFTAR_SAHAM_JII = {
    "AADI.JK": "AADI - Adaro Andalan Indonesia Tbk.",
    "ADMR.JK": "ADMR - Alamtri Minerals Indonesia Tbk.",
    "ADRO.JK": "ADRO - Alamtri Resources Indonesia Tbk.",
    "ANTM.JK": "ANTM - Aneka Tambang Tbk.",
    "ARCI.JK": "ARCI - Archi Indonesia Tbk.",
    "BKSL.JK": "BKSL - Sentul City Tbk.",
    "BRIS.JK": "BRIS - Bank Syariah Indonesia Tbk.",
    "BRMS.JK": "BRMS - Bumi Resources Minerals Tbk.",
    "BUMI.JK": "BUMI - Bumi Resources Tbk.",
    "CPIN.JK": "CPIN - Charoen Pokphand Indonesia Tbk.",
    "CTRA.JK": "CTRA - Ciputra Development Tbk.",
    "DEWA.JK": "DEWA - Darma Henwa Tbk.",
    "ENRG.JK": "ENRG - Energi Mega Persada Tbk.",
    "EXCL.JK": "EXCL - XLsmart Telecom Sejahtera Tbk.",
    "ICBP.JK": "ICBP - Indofood CBP Sukses Makmur Tbk.",
    "INDF.JK": "INDF - Indofood Sukses Makmur Tbk.",
    "INKP.JK": "INKP - Indah Kiat Pulp & Paper Tbk.",
    "JPFA.JK": "JPFA - Japfa Comfeed Indonesia Tbk.",
    "KLBF.JK": "KLBF - Kalbe Farma Tbk.",
    "MBMA.JK": "MBMA - Merdeka Battery Materials Tbk.",
    "MDKA.JK": "MDKA - Merdeka Copper Gold Tbk.",
    "MEDC.JK": "MEDC - Medco Energi Internasional Tbk.",
    "PGAS.JK": "PGAS - Perusahaan Gas Negara Tbk.",
    "PTBA.JK": "PTBA - Bukit Asam Tbk.",
    "RAJA.JK": "RAJA - Rukun Raharja Tbk.",
    "RATU.JK": "RATU - Raharja Energi Cepu Tbk.",
    "TLKM.JK": "TLKM - Telkom Indonesia (Persero) Tbk.",
    "TPIA.JK": "TPIA - Chandra Asri Pacific Tbk.",
    "UNTR.JK": "UNTR - United Tractors Tbk.",
    "UNVR.JK": "UNVR - Unilever Indonesia Tbk.",
    "WIFI.JK": "WIFI - Solusi Sinergi Digital Tbk."
}

# --- 2. SIDEBAR: PENGATURAN WAKTU & BOBOT ---
st.sidebar.header("⚙️ Pengaturan Portofolio JII")

saham_terpilih = st.sidebar.multiselect(
    "1. Pilih Saham Konstituen JII (Min. 2):",
    options=list(DAFTAR_SAHAM_JII.keys()),
    default=["BRIS.JK", "TLKM.JK", "CTRA.JK", "ADRO.JK"],
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

periode_hitung = st.sidebar.selectbox(
    "3. Pilih Frekuensi Perhitungan:",
    options=["Harian", "Mingguan", "Bulanan", "Tahunan"]
)

# --- 3. TARIK & FILTER DATA ---
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

with st.spinner("Mengambil data real-time saham JII..."):
    df_raw = ambil_data_saham(saham_terpilih, periode_yf)

if df_raw.empty:
    df_raw = yf.download(saham_terpilih, period="2y", progress=False)["Close"]

df_raw = df_raw[saham_terpilih]
df_raw.index = pd.to_datetime(df_raw.index)

df_filtered = df_raw[(df_raw.index >= tanggal_mulai) & (df_raw.index <= tanggal_selesai)]

if df_filtered.empty:
    df_filtered = df_raw.tail(100)

aturan_periode = {
    "Harian": {"faktor": 252},
    "Mingguan": {"rule": "W-FRI", "faktor": 52},
    "Bulanan": {"rule": "ME", "faktor": 12},
    "Tahunan": {"rule": "YE", "faktor":

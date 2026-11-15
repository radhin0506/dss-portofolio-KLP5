import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="DSS Portofolio Saham Syariah (JII)", layout="wide")

# --- TAG HTML VERIFIKASI GOOGLE SEARCH CONSOLE ---
st.markdown(
    '<meta name="google-site-verification" content="MASUKKAN_KODE_UNIK_DARI_GOOGLE_DISINI" />', 
    unsafe_allow_html=True
)

# --- 1. DAFTAR LENGKAP 30 SAHAM JII + CTRA (TOTAL 31 SAHAM) ---
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
    "EXCL.JK": "EXCL - XLSMART Telecom Sejahtera Tbk.",
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

# --- FUNGSI OPTIMASI BOBOT OTOMATIS (MONTE CARLO) ---
def cari_bobot_optimal(mean_ret, cov_mat, beta_arr, faktor, rf, rm, target="sharpe", n_simulasi=15000):
    np.random.seed(42)
    n_aset = len(mean_ret)
    w_acak = np.random.dirichlet(np.ones(n_aset), size=n_simulasi)
    port_ret = np.dot(w_acak, mean_ret) * faktor
    port_var = np.sum(np.dot(w_acak, cov_mat) * w_acak, axis=1)
    port_std = np.sqrt(port_var) * np.sqrt(faktor)
    port_beta_sim = np.dot(w_acak, beta_arr)
    
    if target == "sharpe":
        skor = np.where(port_std != 0, (port_ret - rf) / port_std, -np.inf)
    elif target == "treynor":
        skor = np.where(port_beta_sim > 0.05, (port_ret - rf) / port_beta_sim, -np.inf)
    else:
        skor = port_ret - (rf + port_beta_sim * (rm - rf))
        
    idx_terbaik = np.argmax(skor)
    return w_acak[idx_terbaik] * 100.0

# --- 2. SIDEBAR: NAVIGASI MENU ---
st.sidebar.header("🧭 Navigasi Menu")
menu_pilihan = st.sidebar.radio(
    "Pilih Halaman:",
    options=["🏠 Beranda (Home)", "📊 Analisis Lengkap (6 Sheet)"]
)

# --- KUSTOMISASI CSS KELIMA WARNA PASTEL ---
if menu_pilihan == "🏠 Beranda (Home)":
    bg_utama = "#FFC5D3"      # Pastel Pink
    bg_sidebar = "#D4EEF9"    # Pastel Biru
    bg_aksen = "#FFF0F5"      
    border_aksen = "#F8BBD0"
else:
    bg_utama =

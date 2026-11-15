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
    else:  # jensen's alpha
        skor = port_ret - (rf + port_beta_sim * (rm - rf))
        
    idx_terbaik = np.argmax(skor)
    return w_acak[idx_terbaik] * 100.0

# --- 2. SIDEBAR: NAVIGASI MENU ---
st.sidebar.header("🧭 Navigasi Menu")
menu_pilihan = st.sidebar.radio(
    "Pilih Halaman:",
    options=["🏠 Beranda (Home)", "📊 Analisis Lengkap (6 Sheet)"]
)

# --- KUSTOMISASI CSS WARNA PASTEL DINAMIS ---
# Beranda: 2 Warna (Pastel Pink + Pastel Biru)
# Analisis Sheet: 3 Warna (Pastel Peach + Pastel Hijau + Pastel Ungu)
if menu_pilihan == "🏠 Beranda (Home)":
    bg_utama = "#FFF0F5"      # Pastel Pink (Lavender Blush)
    bg_sidebar = "#E6F2FA"    # Pastel Biru (Alice/Baby Blue)
    bg_aksen = "#D9ECFA"      # Aksen Biru Lembut
    border_aksen = "#B8D8F0"
else:
    bg_utama = "#FFF3E6"      # Pastel Peach
    bg_sidebar = "#E8F6EF"    # Pastel Hijau (Mint)
    bg_aksen = "#EFE9FA"      # Pastel Ungu (Lavender)
    border_aksen = "#D5C6F0"

st.markdown(f"""
<style>
    :root {{
        --background-color: {bg_utama} !important;
        --secondary-background-color: {bg_sidebar} !important;
        --text-color: #3D354B !important;
    }}

    .stApp, 
    [data-testid="stAppViewContainer"], 
    [data-testid="stHeader"], 
    [data-testid="stToolbar"],
    section.main {{
        background-color: {bg_utama} !important;
        color: #3D354B !important;
    }}
    
    [data-testid="stSidebar"], 
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {{
        background-color: {bg_sidebar} !important;
    }}
    
    h1, h2, h3, h4, h5, h6, p, span, label, div {{
        color: #3D354B !important;
    }}

    .streamlit-expanderHeader {{
        background-color: {bg_aksen} !important;
        color: #3D354B !important;
        border: 1px solid {border_aksen} !important;
        border-radius: 8px;
    }}
    
    [data-testid="stAlert"] {{
        background-color: {bg_aksen} !important;
        border: 1px solid {border_aksen} !important;
        border-radius: 10px;
    }}
</style>
""", unsafe_allow_html=True)

# Inisialisasi variabel default
df_harga_display = None
faktor_waktu = 52
label_faktor_teks = "52 minggu"
periode_hitung = "Mingguan"
risk_free_rate = 0.06
market_return = 0.10
weights = np.array([1/3, 1/3, 1/3])
saham_terpilih_list = ["BRIS", "CTRA", "TLKM"]
mode_bobot = "Manual (Desimal spesifik)"

# --- PENGATURAN HANYA MUNCUL DI HALAMAN ANALISIS ---
if menu_pilihan == "📊 Analisis Lengkap (6 Sheet)":
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Pengaturan & Sumber Data")

    sumber_data = st.sidebar.radio(
        "Pilih Sumber Data:",
        options=["Otomatis (Yahoo Finance)", "Upload File Sendiri (Excel/CSV)"]
    )

    if sumber_data == "Upload File Sendiri (Excel/CSV)":
        uploaded_file = st.sidebar.file_uploader("Unggah file data harga Close (.xlsx / .csv):", type=["xlsx", "csv"])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_uploaded = pd.read_csv(uploaded_file)
                else:
                    df_uploaded = pd.read_excel(uploaded_file)
                
                kolom_tanggal = [c for c in df_uploaded.columns if "tanggal" in c.lower() or "date" in c.lower()]
                if kolom_tanggal:
                    df_uploaded[kolom_tanggal[0]] = pd.to_datetime(df_uploaded[kolom_tanggal[0]])
                    df_uploaded = df_uploaded.set_index(kolom_tanggal[0])
                
                df_harga_display = df_uploaded.select_dtypes(include=[np.number])
                if "No" in df_harga_display.columns:
                    df_harga_display = df_harga_display.drop(columns=["No"])
                st.sidebar.success("✅ File berhasil dimuat!")
            except Exception as e:
                st.sidebar.error(f"Gagal membaca file: {e}")
                df_harga_display = None
        else:
            st.sidebar.info("👈 Silakan unggah file Excel/CSV Anda.")

    else:
        saham_terpilih = st.sidebar.multiselect(
            "1. Pilih Saham Konstituen JII (Min. 2):",
            options=list(DAFTAR_SAHAM_JII.keys()),
            default=["BRIS.JK", "CTRA.JK", "TLKM.JK"],
            format_func=lambda x: DAFTAR_SAHAM_JII[x]
        )

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
                tanggal_mulai, tanggal_selesai = pd.to_datetime(rentang_tanggal[0]), pd.

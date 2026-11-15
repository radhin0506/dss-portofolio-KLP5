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
    bg_utama = "#F8C4B4"      # Background Utama: Pastel Peach
    bg_sidebar = "#BAED91"    # Sidebar: Pastel Hijau
    bg_aksen = "#D1C4E9"      # Aksen / Expander: Pastel Ungu
    border_aksen = "#B39DDB"

st.markdown(f"""
<style>
    :root {{
        --background-color: {bg_utama} !important;
        --secondary-background-color: {bg_sidebar} !important;
        --text-color: #2C2C2C !important;
    }}

    .stApp, 
    [data-testid="stAppViewContainer"], 
    section.main {{
        background-color: {bg_utama} !important;
        color: #2C2C2C !important;
    }}
    
    [data-testid="stSidebar"], 
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {{
        background-color: {bg_sidebar} !important;
    }}
    
    h1, h2, h3, h4, h5, h6, p, span, label, div {{
        color: #2C2C2C !important;
    }}

    span[data-baseweb="tag"], 
    div[data-baseweb="tag"],
    [data-baseweb="tag"] {{
        background-color: #D1C4E9 !important;
        background: #D1C4E9 !important;
        border-color: #B39DDB !important;
        border-radius: 6px !important;
    }}

    span[data-baseweb="tag"] span, 
    div[data-baseweb="tag"] span,
    [data-baseweb="tag"] * {{
        color: #2C2C2C !important;
        font-weight: 500 !important;
    }}

    .streamlit-expanderHeader {{
        background-color: {bg_aksen} !important;
        color: #2C2C2C !important;
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
                    df_raw = pd.read_csv(uploaded_file, header=None, dtype=str, encoding='utf-8', on_bad_lines='skip')
                else:
                    df_raw = pd.read_excel(uploaded_file, header=None, dtype=str)
                
                header_row_idx = 0
                for idx, row in df_raw.iterrows():
                    row_vals = [str(val).lower() for val in row.dropna().values]
                    if any(any(k in val for k in ["tanggal", "date", "time", "periode", "kode", "emiten", "price", "close"]) for val in row_vals):
                        header_row_idx = idx
                        break
                
                if uploaded_file.name.endswith(".csv"):
                    df_clean = pd.read_csv(uploaded_file, skiprows=header_row_idx, dtype=str, encoding='utf-8', on_bad_lines='skip')
                else:
                    df_clean = pd.read_excel(uploaded_file, skiprows=header_row_idx, dtype=str)

                df_clean.columns = [str(c).strip() for c in df_clean.columns]
                df_clean = df_clean.loc[:, ~df_clean.columns.str.contains('^Unnamed', case=False, na=False)]

                kolom_tgl = None
                for col in df_clean.columns:
                    parsed_date = pd.to_datetime(df_clean[col], errors='coerce')
                    if parsed_date.notna().sum() > max(1, len(df_clean) * 0.1):
                        kolom_tgl = col
                        break
                
                if kolom_tgl is not None:
                    df_clean[kolom_tgl] = pd.to_datetime(df_clean[kolom_tgl], errors='coerce')
                    df_clean = df_clean.dropna(subset=[kolom_tgl])
                    df_clean = df_clean.set_index(kolom_tgl)
                else:
                    df_clean.index = pd.to_datetime(df_clean.iloc[:, 0], errors='coerce')
                    df_clean = df_clean.iloc[:, 1:]

                for col in df_clean.columns:
                    ser = df_clean[col].astype(str)
                    ser = (
                        ser.str.replace('Rp', '', case=False)
                           .str.replace('IDR', '', case=False)
                           .str.replace('$', '', regex=False)
                           .str.replace('.', '', regex=False)
                           .str.replace(',', '.', regex=False)
                           .str.strip()
                    )
                    df_clean[col] = pd.to_numeric(ser, errors='coerce')

                df_harga_display = df_clean.dropna(how='all').dropna(axis=1, how='all')
                if "No" in df_harga_display.columns:
                    df_harga_display = df_harga_display.drop(columns=["No"])

                st.sidebar.success("✅ File berhasil dibersihkan dan dimuat dengan aman!")
            except Exception as e:
                st.sidebar.error(f"Gagal memproses file: {e}")
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
                tanggal_mulai = pd.to_datetime(rentang_tanggal[0])
                tanggal_selesai = pd.to_datetime(rentang_tanggal[1])
            else:
                tanggal_mulai = pd.to_datetime("2026-01-01")
                tanggal_selesai = pd.Timestamp.today()
            periode_yf = "max"

        periode_hitung = st.sidebar.selectbox(
            "3. Pilih Frekuensi Perhitungan:",
            options=["Mingguan", "Harian", "Bulanan", "Tahunan"]
        )

        aturan_periode = {
            "Harian": {"faktor": 252, "label_faktor": "252 hari bursa"},
            "Mingguan": {"faktor": 52, "label_faktor": "52 minggu"},
            "Bulanan": {"faktor": 12, "label_faktor": "12 bulan"},
            "Tahunan": {"faktor": 1, "label_faktor": "1 tahun"}
        }

        faktor_waktu = aturan_periode[periode_hitung]["faktor"]
        label_faktor_teks = aturan_periode[periode_hitung]["label_faktor"]

        if len(saham_terpilih) >= 2:
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

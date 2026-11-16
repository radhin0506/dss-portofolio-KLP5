import streamlit as st
import pandas as pd
import numpy as np
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
def cari_bobot_optimal(mean_ret, cov_mat, beta_arr, rf, rm, target="sharpe", n_simulasi=15000):
    np.random.seed(42)
    n_aset = len(mean_ret)
    w_acak = np.random.dirichlet(np.ones(n_aset), size=n_simulasi)
    port_ret = np.dot(w_acak, mean_ret)
    port_var = np.sum(np.dot(w_acak, cov_mat) * w_acak, axis=1)
    port_std = np.sqrt(port_var)
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
periode_hitung = "Mingguan"
risk_free_rate = 0.001
market_return = 0.002
weights = np.array([1/3, 1/3, 1/3])
saham_terpilih_list = ["BRIS", "CTRA", "TLKM"]
mode_bobot = "Manual (Desimal spesifik)"
sumber_data = "Otomatis (Yahoo Finance)"

# --- PENGATURAN HANYA MUNCUL DI HALAMAN ANALISIS ---
if menu_pilihan == "📊 Analisis Lengkap (6 Sheet)":
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Pengaturan & Sumber Data")

    sumber_data = st.sidebar.radio(
        "Pilih Sumber Data:",
        options=[
            "Otomatis (Yahoo Finance)",
            "Upload File Sendiri (Excel/CSV)",
            "Input Angka Manual (Tabel Interaktif)"
        ]
    )

    if sumber_data == "Input Angka Manual (Tabel Interaktif)":
        periode_hitung = "Input Manual"
        st.sidebar.markdown("**Atur Kolom Emiten Manual:**")
        jml_emiten_manual = st.sidebar.number_input("Jumlah Emiten (Min. 2):", min_value=2, max_value=15, value=3, step=1)
        default_nama = ["SAHAM_A", "SAHAM_B", "SAHAM_C", "SAHAM_D", "SAHAM_E", "SAHAM_F", "SAHAM_G", "SAHAM_H", "SAHAM_I", "SAHAM_J", "SAHAM_K", "SAHAM_L", "SAHAM_M", "SAHAM_N", "SAHAM_O"]
        nama_emiten_manual = []
        for i in range(int(jml_emiten_manual)):
            nm = st.sidebar.text_input(f"Nama/Kode Emiten {i+1}:", value=default_nama[i], key=f"nama_manual_{i}").strip()
            if not nm:
                nm = f"ASET_{i+1}"
            nama_emiten_manual.append(nm)
        
        jml_baris_awal = st.sidebar.number_input("Jumlah Baris Periode Awal:", min_value=3, max_value=100, value=6, step=1)
        
        # Bangun data template awal untuk diedit pengguna di Sheet 1
        data_template = {"Periode/Tanggal": [f"Periode {r+1}" for r in range(int(jml_baris_awal))]}
        for idx_em, nm in enumerate(nama_emiten_manual):
            base_val = 1000.0 + (idx_em * 500.0)
            data_template[nm] = [base_val + (r * 25.0) for r in range(int(jml_baris_awal))]
        
        df_template_manual = pd.DataFrame(data_template)
        
        st.info("📝 **Mode Input Manual Aktif:** Silakan ketik atau ubah angka harga pada tabel **Sheet 1** di bawah ini (Anda juga bisa menambah baris di bagian bawah tabel). Sheet 2 hingga Sheet 6 akan otomatis menyesuaikan!")
        st.header("1️⃣ Sheet 1: Harga Close (Input Manual Interaktif)")
        
        df_edited = st.data_editor(
            df_template_manual,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_harga_manual"
        )
        
        # Bersihkan hasil input pengguna agar siap dihitung ke Sheet 2 - 6
        df_clean_manual = df_edited.copy()
        if "Periode/Tanggal" in df_clean_manual.columns:
            df_clean_manual["Periode/Tanggal"] = df_clean_manual["Periode/Tanggal"].fillna("Periode Baru").astype(str)
            df_clean_manual = df_clean_manual.set_index("Periode/Tanggal")
        
        for col in df_clean_manual.columns:
            df_clean_manual[col] = pd.to_numeric(df_clean_manual[col], errors='coerce')
        
        df_harga_display = df_clean_manual.dropna(how='all')

    elif sumber_data == "Upload File Sendiri (Excel/CSV)":
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

            if periode_hitung == "Harian":
                df_harga = df_filtered.dropna()
            else:
                rule_map = {"Mingguan": "W-FRI", "Bulanan": "ME", "Tahunan": "YE"}
                df_harga = df_filtered.resample(rule_map.get(periode_hitung, "W-FRI")).last().dropna()

            df_harga_display = df_harga.copy()
            df_harga_display.columns = [c.replace(".JK", "") for c in df_harga_display.columns]

    # Validasi jika data belum siap
    if df_harga_display is None or df_harga_display.empty or len(df_harga_display) < 2:
        st.warning("⚠️ Silakan pastikan minimal terdapat **2 emiten** dan **2 baris data angka** yang terisi agar perhitungan return dan risiko dapat dijalankan.")
        st.stop()

    if sumber_data == "Upload File Sendiri (Excel/CSV)":
        periode_hitung = "Data Upload Mandiri"

    saham_terpilih_list = list(df_harga_display.columns)

    df_return_temp = df_harga_display.pct_change().dropna()
    if df_return_temp.empty:
        df_return_temp = df_harga_display.pct_change().fillna(0)
    mean_ret_temp = df_return_temp.mean().values
    cov_mat_temp = df_return_temp.cov().fillna(0).values

    market_proxy_temp = df_return_temp.mean(axis=1)
    market_var_temp = market_proxy_temp.var()
    if pd.isna(market_var_temp) or market_var_temp == 0:
        market_var_temp = 0.0020
    beta_temp = []
    for col in df_return_temp.columns:
        cov_val = pd.concat([df_return_temp[col], market_proxy_temp], axis=1).cov().iloc[0, 1]
        beta_temp.append(cov_val / market_var_temp if (not pd.isna(cov_val) and market_var_temp != 0) else 1.0)
    beta_temp = np.array(beta_temp)

    # --- SIDEBAR: PARAMETER KINERJA (BENCHMARK & RF) ---
    st.sidebar.subheader("📈 Parameter Kinerja (Benchmark & Rf)")
    risk_free_rate = st.sidebar.number_input("Bunga Bebas Risiko (Rf per Periode)", value=0.001, step=0.0001, format="%.4f")
    market_return = st.sidebar.number_input("Expected Return Pasar (Rm per Periode)", value=0.002, step=0.0001, format="%.4f")

    # --- SIDEBAR: BOBOT DESIMAL & OPTIMASI OTOMATIS ---
    st.sidebar.subheader("⚖️ Atur Bobot Investasi (%)")
    mode_bobot = st.sidebar.radio(
        "Metode Penentuan Bobot:",
        options=[
            "Manual (Desimal spesifik)",
            "Bobot Berimbang (Equal Weight)",
            "Otomatis: Maksimum Sharpe Ratio",
            "Otomatis: Maksimum Treynor Ratio",
            "Otomatis: Maksimum Jensen's Alpha"
        ]
    )

    jumlah_saham = len(saham_terpilih_list)
    default_bobot_satuan = round(100.0 / jumlah_saham, 4)

    if mode_bobot == "Otomatis: Maksimum Sharpe Ratio":
        bobot_optimal_persen = cari_bobot_optimal(mean_ret_temp, cov_mat_temp, beta_temp, risk_free_rate, market_return, target="sharpe")
        st.sidebar.success("✨ Bobot dioptimasi otomatis untuk **Sharpe Ratio tertinggi**!")
    elif mode_bobot == "Otomatis: Maksimum Treynor Ratio":
        bobot_optimal_persen = cari_bobot_optimal(mean_ret_temp, cov_mat_temp, beta_temp, risk_free_rate, market_return, target="treynor")
        st.sidebar.success("✨ Bobot dioptimasi otomatis untuk **Treynor Ratio tertinggi**!")
    elif mode_bobot == "Otomatis: Maksimum Jensen's Alpha":
        bobot_optimal_persen = cari_bobot_optimal(mean_ret_temp, cov_mat_temp, beta_temp, risk_free_rate, market_return, target="alpha")
        st.sidebar.success("✨ Bobot dioptimasi otomatis untuk **Jensen's Alpha tertinggi**!")
    elif mode_bobot == "Bobot Berimbang (Equal Weight)":
        bobot_optimal_persen = [default_bobot_satuan] * jumlah_saham
    else:
        bobot_optimal_persen = [default_bobot_satuan] * jumlah_saham

    bobot_input = []
    for idx, saham in enumerate(saham_terpilih_list):
        if mode_bobot == "Manual (Desimal spesifik)":
            nilai = st.sidebar.number_input(
                f"Bobot {saham} (%)", 
                min_value=0.0, 
                max_value=100.0, 
                value=float(bobot_optimal_persen[idx]), 
                step=0.01, 
                format="%.4f",
                key=f"manual_bobot_{saham}_{idx}"
            )
        else:
            nilai = st.sidebar.number_input(
                f"Bobot {saham} (%)", 
                min_value=0.0, 
                max_value=100.0, 
                value=round(float(bobot_optimal_persen[idx]), 4), 
                step=0.01, 
                format="%.4f",
                disabled=True,
                key=f"auto_bobot_{saham}_{mode_bobot}_{idx}"
            )
        bobot_input.append(nilai)

    total_bobot = sum(bobot_input)
    if abs(total_bobot - 100.0) > 0.01:
        st.sidebar.warning(f"⚠️ Total bobot saat ini: **{total_bobot:.4f}%**. Disarankan pas 100.00%.")

    if total_bobot == 0:
        total_bobot = 1.0
    weights = np.array(bobot_input) / total_bobot

else:
    dates = pd.date_range(start="2026-01-01", periods=10, freq="W")
    df_harga_display = pd.DataFrame({
        "BRIS": [2000, 2050, 2100, 2080, 2150, 2200, 2180, 2250, 2300, 2350],
        "CTRA": [1000, 1020, 1010, 1050, 1070, 1060, 1090, 1110, 1100, 1130],
        "TLKM": [3500, 3550, 3520, 3600, 3580, 3650, 3700, 3680, 3750, 3800]
    }, index=dates)
    saham_terpilih_list = list(df_harga_display.columns)

# Perhitungan Analisis Akhir (Murni per Periode Tanpa Skala Waktu)
jumlah_baris_data = len(df_harga_display)
df_return = df_harga_display.pct_change().fillna(0)
df_return_stats = df_harga_display.pct_change().dropna()
if df_return_stats.empty:
    df_return_stats = df_return

mean_return_stats = df_return_stats.mean()

# Matriks Kovarians Antar Emiten (Diagonal dikosongkan)
cov_matrix_stats = df_return_stats.cov()
for col in cov_matrix_stats.columns:
    cov_matrix_stats.loc[col, col] = np.nan

std_stats = df_return_stats.std().fillna(0)

# Nilai murni per periode
port_return_periode = np.sum(mean_return_stats * weights)
cov_clean_vals = df_return_stats.cov().fillna(0).values
port_var_periode = np.dot(weights.T, np.dot(cov_clean_vals, weights))
port_std_periode = np.sqrt(max(0.0, port_var_periode))

market_proxy_return = df_return_stats.mean(axis=1)
market_variance = market_proxy_return.var()
if pd.isna(market_variance) or market_variance == 0:
    market_variance = 0.0020

beta_saham = []
for col in df_return_stats.columns:
    cov_val = pd.concat([df_return_stats[col], market_proxy_return], axis=1).cov().iloc[0, 1]
    beta_i = cov_val / market_variance if (not pd.isna(cov_val) and market_variance != 0) else 1.0
    beta_saham.append(beta_i)
port_beta = np.sum(weights * np.array(beta_saham))

sharpe_ratio = (port_return_periode - risk_free_rate) / port_std_periode if port_std_periode != 0 else 0
treynor_ratio = (port_return_periode - risk_free_rate) / port_beta if port_beta != 0 else 0
jensen_alpha = port_return_periode - (risk_free_rate + port_beta * (market_return - risk_free_rate))


# =====================================================================
# TAMPILAN HALAMAN: BERANDA VS ANALISIS LENGKAP
# =====================================================================

if menu_pilihan == "🏠 Beranda (Home)":
    st.title("🕌 Selamat Datang di Sistem Pendukung Keputusan (DSS) Portofolio Saham Syariah")
    st.markdown("### Analisis Portofolio Berbasis Konstituen Jakarta Islamic Index (JII)")
    
    st.info(
        "💡 **Tentang Aplikasi:** Aplikasi web ini dirancang khusus untuk membantu pengambil keputusan "
        "dalam merancang, merumuskan risiko, menghitung return, serta mengevaluasi kinerja portofolio saham syariah "
        "secara komprehensif berdasarkan kaidah portofolio Modern Markowitz."
    )
    
    st.markdown("---")
    st.subheader("📑 Struktur Analisis 6 Sheet")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        * **1️⃣ Sheet 1: Harga Close** — Menampilkan atau menginput data harga historis emiten.
        * **2️⃣ Sheet 2: Return Realisasi & ER** — Menghitung tingkat pengembalian dan rata-rata *Expected Return*.
        * **3️⃣ Sheet 3: Varians & Standar Deviasi** — Mengukur tingkat risiko masing-masing aset.
        """)
    with c2:
        st.markdown("""
        * **4️⃣ Sheet 4: Kovarians** — Menganalisis arah pergerakan bersama antar emiten.
        * **5️⃣ Sheet 5: Koefisien Korelasi** — Mengukur keeratan hubungan untuk diversifikasi.
        * **6️⃣ Sheet 6: Return Portofolio & Kinerja** — Evaluasi akhir menggunakan Sharpe, Treynor, & Alpha.
        """)
    
    st.success("👉 Silakan buka menu navigasi di pojok kiri atas untuk mulai mengatur emiten, input data manual, bobot, dan melihat rincian perhitungannya!")

else:
    # =====================================================================
    # ANALISIS LENGKAP 6 SHEET
    # =====================================================================
    
    # --- SHEET 1: HARGA CLOSE (HANYA DITAMPILKAN JIKA BUKAN MODE INPUT MANUAL KARENA SUDAH ADA EDITOR DI ATAS) ---
    if sumber_data != "Input Angka Manual (Tabel Interaktif)":
        st.header(f"1️⃣ Sheet 1: Harga Close ({periode_hitung})")
        df_sheet1 = df_harga_display.reset_index()
        if 'Tanggal' in df_sheet1.columns:
            df_sheet1 = df_sheet1.rename(columns={'Tanggal': 'Periode/Tanggal'})
        else:
            df_sheet1.rename(columns={df_sheet1.columns[0]: 'Periode/Tanggal'}, inplace=True)

        df_sheet1.insert(0, "No", range(1, len(df_sheet1) + 1))
        st.dataframe(df_sheet1.style.format({"No": "{:.0f}", **{c: "Rp {:,.2f}" for c in saham_terpilih_list}}), use_container_width=True)

    with st.expander("📖 Panduan, Rumus & Kesimpulan - Sheet 1 (Data Harga Close)", expanded=True):
        st.markdown(
            f"* **Jumlah Data Historis:** Terdeteksi {jumlah_baris_data} baris data.\n"
            "* **Rumus / Sumber Data:** Harga Penutupan (Close Price) pada periode t\n"
            "* **Kesimpulan Sheet 1:** Data harga mentah ini berfungsi sebagai pondasi utama seluruh perhitungan."
        )

    # --- SHEET 2: RETURN REALISASI & ER ---
    st.header(f"2️⃣ Sheet 2: Return Realisasi & ER ({periode_hitung})")
    df_sheet2 = df_return.copy().reset_index(drop=True)
    df_sheet2.insert(0, "No", range(1, len(df_sheet2) + 1))
    st.dataframe(df_sheet2.style.format({"No": "{:.0f}", **{c: "{:.6f}" for c in saham_terpilih_list}}), use_container_width=True)

    st.markdown("**Expected Return (ER) Masing-masing Emiten:**")
    df_er_table = pd.DataFrame({
        "Emiten": saham_terpilih_list,
        "Expected Return (Desimal)": mean_return_stats.values,
        "Expected Return (%)": [f"{val * 100:.4f}%" for val in mean_return_stats.values]
    })
    st.dataframe(df_er_table.style.format({"Expected Return (Desimal)": "{:.6f}"}), use_container_width=True)

    with st.expander("📖 Panduan, Rumus & Kesimpulan - Sheet 2 (Return Realisasi & ER)", expanded=True):
        st.markdown(
            "* **Rumus Return:** R = (Harga_ini - Harga_lalu) / Harga_lalu\n"
            "* **Rumus Expected Return (ER):** ER = Total Return / Jumlah Periode (n)\n"
            "* **Kesimpulan Sheet 2:** Emiten dengan ER positif menunjukkan tren keuntungan yang baik."
        )

    # --- SHEET 3: VARIANS & STANDAR DEVIASI ---
    st.header("3️⃣ Sheet 3: Varians & Standar Deviasi")
    df_sheet3 = pd.DataFrame({
        "Emiten": saham_terpilih_list,
        "Expected Return Saham": mean_return_stats.values,
        "Variance": df_return_stats.var().fillna(0).values,
        "Standar Deviasi (Risiko)": std_stats.values
    })
    kolom_angka_sheet3 = ["Expected Return Saham", "Variance", "Standar Deviasi (Risiko)"]
    st.dataframe(df_sheet3.style.format({col: "{:.6f}" for col in kolom_angka_sheet3}), use_container_width=True)

    with st.expander("📖 Panduan, Rumus & Kesimpulan - Sheet 3 (Varians & Standar Deviasi)", expanded=True):
        st.markdown(
            "* **Rumus Expected Return Saham:** $E(R) = \\frac{\\sum R_t}{n}$\n"
            "* **Rumus Varians ($\\sigma^2$):** $\\sigma^2 = \\frac{\\sum (R_t - E(R))^2}{n - 1}$ (Mengukur tingkat penyebaran fluktuasi harga emiten)\n"
            "* **Rumus Standar Deviasi ($\\sigma$):** $\\sigma = \\sqrt{\\sigma^2}$ (Akar kuadrat dari varians sebagai ukuran risiko mutlak)\n"
            "* **Kesimpulan Sheet 3:** Nilai standar deviasi menunjukkan seberapa besar volatilitas atau risiko masing-masing aset."
        )

    # --- SHEET 4: COVARIANCE ---
    st.header("4️⃣ Sheet 4: Kovarians (Covariance Matrix)")
    st.dataframe(cov_matrix_stats.style.format("{:.6f}", na_rep="-"), use_container_width=True)

    with st.expander("📖 Panduan, Rumus & Kesimpulan - Sheet 4 (Covariance)", expanded=True):
        st.markdown(
            "* **Rumus Kovarians:** Mengukur arah pergerakan bersama antar dua variabel saham.\n"
            "* **Kesimpulan Sheet 4:** Kovarians negatif sangat baik untuk diversifikasi portofolio. Nilai pada saham yang sama (diagonal) dikosongkan agar tidak membingungkan."
        )

    # --- SHEET 5: KOEFISIEN KORELASI ---
    st.header("5️⃣ Sheet 5: Koefisien Korelasi")
    corr_matrix = df_return_stats.corr()
    for col in corr_matrix.columns:
        corr_matrix.loc[col, col] = np.nan
    st.dataframe(corr_matrix.style.format("{:.6f}", na_rep="-"), use_container_width=True)

    with st.expander("📖 Panduan, Rumus & Kesimpulan - Sheet 5 (Koefisien Korelasi)", expanded=True):
        st.markdown(
            "* **Rumus Koefisien Korelasi (r):** r = Cov(A,B) / (SD_A * SD_B)\n"
            "* **Kesimpulan Sheet 5:** Pilih emiten dengan korelasi rendah atau negatif untuk diversifikasi optimal."
        )

    # --- SHEET 6: RETURN PORTOFOLIO & KINERJA ---
    st.header("6️⃣ Sheet 6: Return Portofolio, Risiko, & Metrik Kinerja (Sharpe, Treynor, Alpha)")

    if "Otomatis" in mode_bobot:
        st.info(f"🤖 **Mode Optimasi Aktif:** `{mode_bobot}` — Proporsi bobot di bawah ini telah dihitung otomatis untuk memaksimalkan kinerja tersebut.")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Expected Return Portofolio", f"{port_return_periode:.4%}")
    col_m2.metric("Variance Portofolio", f"{port_var_periode:.6f}")
    col_m3.metric("Risiko Portofolio (SD)", f"{port_std_periode:.4%}")
    col_m4.metric("Beta Portofolio", f"{port_beta:.4f}")

    col_m5, col_m6, col_m7 = st.columns(3)
    col_m5.metric("Sharpe Ratio", f"{sharpe_ratio:.4f}", help="Return per unit total risiko (per periode)")
    col_m6.metric("Treynor Ratio", f"{treynor_ratio:.4f}", help="Return per unit risiko sistematis Beta (per periode)")
    col_m7.metric("Jensen's Alpha", f"{jensen_alpha:.6f}", help="Kelebihan return terhadap CAPM (per periode)")

    df_port_summary = pd.DataFrame({
        "Emiten": saham_terpilih_list,
        "Bobot (%)": [w * 100 for w in weights],
        "Expected Return": mean_return_stats.values,
        "Kontribusi Return": (mean_return_stats.values * weights)
    })
    st.dataframe(df_port_summary.style.format({"Bobot (%)": "{:.4f}%", "Expected Return": "{:.6f}", "Kontribusi Return": "{:.6f}"}), use_container_width=True)

    with st.expander("📖 Panduan, Rumus & Kesimpulan - Sheet 6 (Portofolio & Kinerja)", expanded=True):
        panduan_s6 = (
            "* **Rumus Formal Expected Return Portofolio:** E(Rp) = Sum [ w_i * E(R_i) ]\n"
            "* **Rumus Variance Portofolio ($\\sigma_p^2$):** $\\sigma_p^2 = \\sum \\sum w_i w_j \\sigma_{ij}$ = **" + f"{port_var_periode:.6f}" + "** (Murni per periode, tanpa faktor waktu)\n"
            "* **Rumus Standar Deviasi Portofolio ($\\sigma_p$):** $\\sigma_p = \\sqrt{\\sigma_p^2}$ = **" + f"{port_std_periode:.4f} ({port_std_periode:.4%})" + "**\n"
            "* **Rumus Sharpe Ratio:** Sharpe = (Return Portofolio - Rf) / Risiko Portofolio = **" + f"{sharpe_ratio:.4f}" + "**\n"
            "* **Rumus Treynor Ratio:** Treynor = (Return Portofolio - Rf) / Beta Portofolio = **" + f"{treynor_ratio:.4f}" + "**\n"
            "* **Rumus Jensen's Alpha:** Alpha = Return Portofolio - [Rf + Beta * (Rm - Rf)] = **" + f"{jensen_alpha:.6f}" + "**\n\n"
            "**Kesimpulan Keseluruhan Portofolio:**\n"
            "* Portofolio Anda menghasilkan Expected Return sebesar **" + f"{port_return_periode:.4%}" + "** dengan Variance Portofolio **" + f"{port_var_periode:.6f}" + "** dan Risiko (Standar Deviasi) sebesar **" + f"{port_std_periode:.4%}" + f"** per periode berdasarkan {jumlah_baris_data} data historis.\n"
            "* Nilai Sharpe & Treynor Ratio mencerminkan efisiensi keuntungan portofolio terhadap risiko murni.\n"
            "* Nilai Jensen's Alpha positif menunjukkan portofolio berhasil mengungguli pasar (outperform)."
        )
        st.markdown(panduan_s6)

    # --- KESIMPULAN KEPUTUSAN DSS OTOMATIS ---
    st.markdown("---")
    st.subheader("🎯 Rekomendasi & Kesimpulan Keputusan Akhir (DSS)")

    idx_dominan = np.argmax(weights)
    saham_dominan = saham_terpilih_list[idx_dominan]
    bobot_dominan = weights[idx_dominan] * 100

    if port_return_periode > risk_free_rate and sharpe_ratio > 0.1 and jensen_alpha > 0:
        status_keputusan = "SANGAT DIREKOMENDASIKAN (LAYAK & OPTIMAL)"
        saran_tindakan = "Kombinasi bobot portofolio ini mampu mengalahkan instrumen bebas risiko (Rf) sekaligus mencetak alpha positif dengan efisiensi risiko yang baik per periode."
    elif port_return_periode > risk_free_rate:
        status_keputusan = "DIREKOMENDASIKAN (LAYAK DENGAN CATATAN)"
        saran_tindakan = "Portofolio menghasilkan imbal hasil di atas bunga bebas risiko (Rf) per periode, namun efisiensi risikonya masih dapat ditingkatkan."
    else:
        status_keputusan = "TIDAK DIREKOMENDASIKAN (PERLU REBALANCING)"
        saran_tindakan = "Imbal hasil portofolio belum mampu mengimbangi tingkat risiko maupun instrumen bebas risiko (Rf). Disarankan menyesuaikan bobot investasi."

    if port_beta > 1.05:
        profil_beta = f"Agresif (Beta = {port_beta:.4f} > 1): Portofolio lebih volatil dibanding pergerakan pasar."
    elif port_beta < 0.95:
        profil_beta = f"Defensif (Beta = {port_beta:.4f} < 1): Portofolio lebih stabil terhadap fluktuasi pasar."
    else:
        profil_beta = f"Netral / Sejalan Pasar (Beta = {port_beta:.4f} ≈ 1): Pergerakan portofolio sejalan dengan pasar."

    if jensen_alpha > 0:
        status_alpha = f"Outperform (+{jensen_alpha:.6f}): Portofolio mencetak kelebihan keuntungan di atas CAPM."
    else:
        status_alpha = f"Underperform ({jensen_alpha:.6f}): Kinerja portofolio di bawah ekspektasi model pasar."

    st.success(f"**Keputusan Sistem:** **{status_keputusan}**\n\n{saran_tindakan}")

    st.markdown(
        f"**Ringkasan Dasar Pengambilan Keputusan:**\n"
        f"* **Alokasi Aset Utama:** Saham **{saham_dominan}** mendominasi portofolio sebesar **{bobot_dominan:.2f}%**.\n"
        f"* **Perbandingan Bebas Risiko ($R_f$):** Expected Return (**{port_return_periode:.4%}**) {'lebih tinggi' if port_return_periode > risk_free_rate else 'lebih rendah'} dari $R_f$ (**{risk_free_rate:.4%}**).\n"
        f"* **Evaluasi Kinerja (CAPM):** {status_alpha}\n"
        f"* **Karakteristik Risiko Sistematis:** {profil_beta}"
    )

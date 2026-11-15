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
    
    # Hasilkan kombinasi bobot acak (Dirichlet distribution memastikan jumlah bobot = 1.0)
    w_acak = np.random.dirichlet(np.ones(n_aset), size=n_simulasi)
    
    # Hitung return & risiko tahunan/skala untuk seluruh simulasi sekaligus (vektorisasi cepat)
    port_ret = np.dot(w_acak, mean_ret) * faktor
    port_var = np.sum(np.dot(w_acak, cov_mat) * w_acak, axis=1)
    port_std = np.sqrt(port_var) * np.sqrt(faktor)
    port_beta_sim = np.dot(w_acak, beta_arr)
    
    if target == "sharpe":
        skor = np.where(port_std != 0, (port_ret - rf) / port_std, -np.inf)
    elif target == "treynor":
        # Hindari pembagian beta negatif ekstrem yang bisa mendistorsi
        skor = np.where(port_beta_sim > 0.05, (port_ret - rf) / port_beta_sim, -np.inf)
    else:  # jensen's alpha
        skor = port_ret - (rf + port_beta_sim * (rm - rf))
        
    idx_terbaik = np.argmax(skor)
    return w_acak[idx_terbaik] * 100.0  # Kembalikan dalam bentuk persentase (%)

# --- 2. SIDEBAR: NAVIGASI MENU ---
st.sidebar.header("🧭 Navigasi Menu")
menu_pilihan = st.sidebar.radio(
    "Pilih Halaman:",
    options=["🏠 Beranda (Home)", "📊 Analisis Lengkap (6 Sheet)"]
)

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
                tanggal_mulai, tanggal_selesai = pd.to_datetime(rentang_tanggal[0]), pd.to_datetime(rentang_tanggal[1])
            else:
                tanggal_mulai, tanggal_selesai = pd.to_datetime("2026-01-01"), pd.Timestamp.today()
            periode_yf = "max"

        periode_hitung = st.sidebar.selectbox(
            "3. Pilih Frekuensi Perhitungan:",
            options=["Mingguan", "Harian", "Bulanan", "Semester (6 Bulan)", "Tahunan"]
        )

        aturan_periode = {
            "Harian": {"faktor": 252, "label_faktor": "252 hari bursa"},
            "Mingguan": {"faktor": 52, "label_faktor": "52 minggu"},
            "Bulanan": {"faktor": 12, "label_faktor": "12 bulan"},
            "Semester (6 Bulan)": {"faktor": 2, "label_faktor": "2 semester"},
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

            if periode_hitung == "Harian":
                df_harga = df_filtered.dropna()
            else:
                rule_map = {"Mingguan": "W-FRI", "Bulanan": "ME", "Semester (6 Bulan)": "2QE", "Tahunan": "YE"}
                df_harga = df_filtered.resample(rule_map.get(periode_hitung, "W-FRI")).last().dropna()

            df_harga_display = df_harga.copy()
            df_harga_display.columns = [c.replace(".JK", "") for c in df_harga_display.columns]

    # Validasi jika data belum siap
    if df_harga_display is None or df_harga_display.empty:
        st.warning("⚠️ Silakan pilih minimal **2 saham JII** atau unggah file data Anda terlebih dahulu di menu sebelah kiri.")
        st.stop()

    if sumber_data == "Upload File Sendiri (Excel/CSV)":
        periode_hitung = "Data Upload Mandiri"
        jumlah_baris_data = len(df_harga_display)
        
        pilihan_skala = st.sidebar.selectbox(
            "Pilih Penyesuaian Skala Waktu:",
            options=[
                f"Gunakan Nilai Per Periode Murni (Faktor = 1)",
                f"Sesuaikan dengan Jumlah Data ({jumlah_baris_data} baris setara 1 Tahun)",
                f"Setahun Penuh (Faktor Standar 52 Minggu)",
                f"Atur Faktor Manual"
            ]
        )
        if "Faktor = 1" in pilihan_skala or "Nilai Per Periode" in pilihan_skala:
            faktor_waktu = 1.0
            label_faktor_teks = f"1 (Periode murni dari {jumlah_baris_data} data)"
        elif "52 Minggu" in pilihan_skala:
            faktor_waktu = 52.0
            label_faktor_teks = "52 minggu (standar tahunan)"
        else:
            faktor_waktu = st.sidebar.number_input("Masukkan Angka Faktor Pengali Custom:", value=1.0, step=0.5)
            label_faktor_teks = f"Custom ({faktor_waktu})"

    saham_terpilih_list = list(df_harga_display.columns)

    # Hitung statistik awal sebelum penentuan bobot otomatis
    df_return_temp = df_harga_display.pct_change().dropna()
    if df_return_temp.empty:
        df_return_temp = df_harga_display.pct_change().fillna(0)
    mean_ret_temp = df_return_temp.mean().values
    cov_mat_temp = df_return_temp.cov().values

    market_proxy_temp = df_return_temp.mean(axis=1)
    market_var_temp = market_proxy_temp.var()
    if market_var_temp == 0:
        market_var_temp = 0.0020
    beta_temp = []
    for col in df_return_temp.columns:
        cov_val = pd.concat([df_return_temp[col], market_proxy_temp], axis=1).cov().iloc[0, 1]
        beta_temp.append(cov_val / market_var_temp if market_var_temp != 0 else 1.0)
    beta_temp = np.array(beta_temp)

    # --- SIDEBAR: PARAMETER KINERJA (BENCHMARK & RF) ---
    st.sidebar.subheader("📈 Parameter Kinerja (Benchmark & Rf)")
    risk_free_rate = st.sidebar.number_input("Bunga Bebas Risiko (Rf - Tahunan)", value=0.06, step=0.001, format="%.4f")
    market_return = st.sidebar.number_input("Expected Return Pasar (Rm - Tahunan)", value=0.10, step=0.001, format="%.4f")

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
        bobot_optimal_persen = cari_bobot_optimal(mean_ret_temp, cov_mat_temp, beta_temp, faktor_waktu, risk_free_rate, market_return, target="sharpe")
        st.sidebar.success("✨ Bobot dioptimasi otomatis untuk **Sharpe Ratio tertinggi**!")
    elif mode_bobot == "Otomatis: Maksimum Treynor Ratio":
        bobot_optimal_persen = cari_bobot_optimal(mean_ret_temp, cov_mat_temp, beta_temp, faktor_waktu, risk_free_rate, market_return, target="treynor")
        st.sidebar.success("✨ Bobot dioptimasi otomatis untuk **Treynor Ratio tertinggi**!")
    elif mode_bobot == "Otomatis: Maksimum Jensen's Alpha":
        bobot_optimal_persen = cari_bobot_optimal(mean_ret_temp, cov_mat_temp, beta_temp, faktor_waktu, risk_free_rate, market_return, target="alpha")
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
                key=f"manual_bobot_{saham}"
            )
        else:
            # Tampilkan hasil bobot otomatis secara langsung pada kolom presisi
            nilai = st.sidebar.number_input(
                f"Bobot {saham} (%)", 
                min_value=0.0, 
                max_value=100.0, 
                value=round(float(bobot_optimal_persen[idx]), 4), 
                step=0.01, 
                format="%.4f",
                disabled=True,
                key=f"auto_bobot_{saham}_{mode_bobot}"
            )
        bobot_input.append(nilai)

    total_bobot = sum(bobot_input)
    if abs(total_bobot - 100.0) > 0.01:
        st.sidebar.warning(f"⚠️ Total bobot saat ini: **{total_bobot:.4f}%**. Disarankan pas 100.00%.")

    if total_bobot == 0:
        total_bobot = 1.0
    weights = np.array(bobot_input) / total_bobot

else:
    # Data Dummy untuk Beranda agar halaman Home tetap bisa dimuat tanpa error
    dates = pd.date_range(start="2026-01-01", periods=10, freq="W")
    df_harga_display = pd.DataFrame({
        "BRIS": [2000, 2050, 2100, 2080, 2150, 2200, 2180, 2250, 2300, 2350],
        "CTRA": [1000, 1020, 1010, 1050, 1070, 1060, 1090, 1110, 1100, 1130],
        "TLKM": [3500, 3550, 3520, 3600, 3580, 3650, 3700, 3680, 3750, 3800]
    }, index=dates)
    saham_terpilih_list = list(df_harga_display.columns)

WARNA_PASTEL = ["#B08968", "#D4A373", "#CCD5AE", "#99582A", "#6F4E37", "#BC6C25", "#E6CCB2"]

# Perhitungan Analisis Akhir
jumlah_baris_data = len(df_harga_display)
df_return = df_harga_display.pct_change().fillna(0)
df_return_stats = df_harga_display.pct_change().dropna()
if df_return_stats.empty:
    df_return_stats = df_return

mean_return_stats = df_return_stats.mean()
cov_matrix_stats = df_return_stats.cov()
std_stats = df_return_stats.std()

port_return_periode = np.sum(mean_return_stats * weights)
port_std_periode = np.sqrt(np.dot(weights.T, np.dot(cov_matrix_stats, weights)))
port_return_skala = port_return_periode * faktor_waktu
port_std_skala = port_std_periode * np.sqrt(faktor_waktu)

market_proxy_return = df_return_stats.mean(axis=1)
market_variance = market_proxy_return.var()
if market_variance == 0:
    market_variance = 0.0020

beta_saham = []
for col in df_return_stats.columns:
    cov_val = pd.concat([df_return_stats[col], market_proxy_return], axis=1).cov().iloc[0, 1]
    beta_i = cov_val / market_variance if market_variance != 0 else 1.0
    beta_saham.append(beta_i)
port_beta = np.sum(weights * np.array(beta_saham))

sharpe_ratio = (port_return_skala - risk_free_rate) / port_std_skala if port_std_skala != 0 else 0
treynor_ratio = (port_return_skala - risk_free_rate) / port_beta if port_beta != 0 else 0
jensen_alpha = port_return_skala - (risk_free_rate + port_beta * (market_return - risk_free_rate))


# =====================================================================
# TAMPILAN HALAMAN: BERANDA VS ANALISIS LENGKAP
# =====================================================================

if menu_pilihan == "🏠 Beranda (Home)":
    st.title("🕌 Selamat Datang di Sistem Pendukung Keputusan (DSS) Portofolio Saham Syariah")
    st.markdown("### Analisis Portofolio Berbasis Konstituen Jakarta Islamic Index (JII)")
    
    st.info(
        "💡 **Tentang Aplikasi:** Aplikasi web ini dirancang khusus untuk membantu pengambil keputusan "
        "dalam merancang, mengukur risiko, menghitung return, serta mengevaluasi kinerja portofolio saham syariah "
        "secara komprehensif berdasarkan kaidah portofolio Modern Markowitz."
    )
    
    st.markdown("---")
    st.subheader("📑 Struktur Analisis 6 Sheet")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        * **1️⃣ Sheet 1: Harga Close** — Menampilkan data harga historis emiten.
        * **2️⃣ Sheet 2: Return Realisasi & ER** — Menghitung tingkat pengembalian harian/mingguan dan rata-rata *Expected Return*.
        * **3️⃣ Sheet 3: Varians & Standar Deviasi** — Mengukur tingkat risiko masing-masing aset.
        """)
    with c2:
        st.markdown("""
        * **4️⃣ Sheet 4: Kovarians** — Menganalisis arah pergerakan bersama antar emiten.
        * **5️⃣ Sheet 5: Koefisien Korelasi** — Mengukur keeratan hubungan untuk diversifikasi.
        * **6️⃣ Sheet 6: Return Portofolio & Kinerja** — Evaluasi akhir menggunakan Sharpe, Treynor, & Alpha.
        """)
    
    st.success("👉 Silakan klik menu **Analisis Lengkap (6 Sheet)** di sidebar sebelah kiri untuk mulai mengatur emiten, bobot, dan melihat rincian perhitungannya!")

else:
    # =====================================================================
    # ANALISIS LENGKAP 6 SHEET
    # =====================================================================
    
    # --- SHEET 1: HARGA CLOSE ---
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

    st.markdown("**Expected Return (ER) Masing-masing Emiten (Rata-rata Return):**")
    st.json({col: f"{val:.6f}" for col, val in mean_return_stats.items()})

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
        f"Mean Return ({periode_hitung})": mean_return_stats.values,
        "Variance": df_return_stats.var().values,
        "Standar Deviasi (Risiko)": std_stats.values,
        f"Expected Return (Skala Waktu)": mean_return_stats.values * faktor_waktu,
        f"Risiko (Skala Waktu)": std_stats.values * np.sqrt(faktor_waktu)
    })
    kolom_angka_sheet3 = [f"Mean Return ({periode_hitung})", "Variance", "Standar Deviasi (Risiko)", "Expected Return (Skala Waktu)", "Risiko (Skala Waktu)"]
    st.dataframe(df_sheet3.style.format({col: "{:.6f}" for col in kolom_angka_sheet3}), use_container_width=True)

    with st.expander("📖 Panduan, Rumus & Kesimpulan - Sheet 3 (Varians & Standar Deviasi)", expanded=True):
        st.markdown(
            f"* **Faktor Skala Waktu Aktif:** {label_faktor_teks} (Faktor = `{faktor_waktu}`)\n"
            "* **Kesimpulan Sheet 3:** Skala waktu disesuaikan agar angka hasil analisis proporsional dengan jumlah data Anda."
        )

    # --- SHEET 4: COVARIANCE ---
    st.header("4️⃣ Sheet 4: Kovarians (Covariance Matrix)")
    st.dataframe(cov_matrix_stats.style.format("{:.6f}"), use_container_width=True)

    with st.expander("📖 Panduan, Rumus & Kesimpulan - Sheet 4 (Covariance)", expanded=True):
        st.markdown(
            "* **Rumus Kovarians:** Mengukur arah pergerakan bersama antar dua variabel saham.\n"
            "* **Kesimpulan Sheet 4:** Kovarians negatif sangat baik untuk diversifikasi portofolio."
        )

    # --- SHEET 5: KOEFISIEN KORELASI ---
    st.header("5️⃣ Sheet 5: Koefisien Korelasi")
    corr_matrix = df_return_stats.corr()
    st.dataframe(corr_matrix.style.format("{:.6f}"), use_container_width=True)

    with st.expander("📖 Panduan, Rumus & Kesimpulan - Sheet 5 (Koefisien Korelasi)", expanded=True):
        st.markdown(
            "* **Rumus Koefisien Korelasi (r):** r = Cov(A,B) / (SD_A * SD_B)\n"
            "* **Kesimpulan Sheet 5:** Pilih emiten dengan korelasi rendah atau negatif untuk diversifikasi optimal."
        )

    # --- SHEET 6: RETURN PORTOFOLIO & KINERJA ---
    st.header("6️⃣ Sheet 6: Return Portofolio, Risiko, & Metrik Kinerja (Sharpe, Treynor, Alpha)")

    if "Otomatis" in mode_bobot:
        st.info(f"🤖 **Mode Optimasi Aktif:** `{mode_bobot}` — Proporsi bobot di bawah ini telah dihitung otomatis untuk memaksimalkan kinerja tersebut.")

    col_m1, col_m2, col3 = st.columns(3)
    col_m1.metric("Expected Return Portofolio", f"{port_return_skala:.2%}")
    col_m2.metric("Risiko Portofolio", f"{port_std_skala:.2%}")
    col3.metric("Beta Portofolio", f"{port_beta:.4f}")

    col_m4, col_m5, col_m6 = st.columns(3)
    col_m4.metric("Sharpe Ratio", f"{sharpe_ratio:.4f}", help="Return di atas Risk-Free per unit total risiko")
    col_m5.metric("Treynor Ratio", f"{treynor_ratio:.4f}", help="Return di atas Risk-Free per unit risiko sistematis (Beta)")
    col_m6.metric("Jensen's Alpha", f"{jensen_alpha:.4f}", help="Kelebihan return di atas model CAPM (Outperformance)")

    df_port_summary = pd.DataFrame({
        "Emiten": saham_terpilih_list,
        "Bobot (%)": [w * 100 for w in weights],
        "Expected Return": mean_return_stats.values,
        "Kontribusi Return": (mean_return_stats.values * weights)
    })
    st.dataframe(df_port_summary.style.format({"Bobot (%)": "{:.4f}%", "Expected Return": "{:.6f}", "Kontribusi Return": "{:.6f}"}), use_container_width=True)

    with st.expander("📖 Panduan, Rumus & Kesimpulan - Sheet 6 (Portofolio & Metrik Kinerja)", expanded=True):
        st.markdown(
            f"* **Rumus Formal Expected Return Portofolio:** E(Rp) = Sum [ w_i * E(R_i) ]\n"
            f"* **Skala Waktu yang Digunakan:** {label_faktor_teks}\n"
            f"* **Rumus Sharpe Ratio:** Sharpe = (Return Portofolio - Rf) / Risiko Portofolio = **{sharpe_ratio:.4f}**\n"
            f"* **Rumus Treynor Ratio:** Treynor = (Return Portofolio - Rf) / Beta Portofolio = **{treynor_ratio:.4f}**\n"
            f"* **Rumus Jensen's Alpha:** Alpha = Return Portofolio - [Rf + Beta * (Rm - Rf)] = **{jensen_alpha:.4f}**\n\n"
            f"**Kesimpulan Keseluruhan Portofolio:**\n"
            f"* Portofolio Anda menghasilkan Expected Return sebesar **{port_return_skala:.2%}** dengan tingkat risiko **{port_std_skala:.2%}** berdasarkan {jumlah_baris_data} data historis.\n"
            f"* Nilai Sharpe & Treynor Ratio mencerminkan efisiensi keuntungan portofolio terhadap risiko.\n"
            f"* Nilai Jensen's Alpha positif menunjukkan portofolio berhasil mengungguli pasar (outperform)."
        )

    # --- GRAFIK KINERJA ---
    st.subheader("📊 Visualisasi Pertumbuhan Harga Saham (Base = 100)")
    df_norm = (df_harga_display / df_harga_display.iloc[0]) * 100

    plt.clf()
    fig, ax = plt.subplots(figsize=(10, 4))

    for idx, saham in enumerate(df_norm.columns):
        warna_pilih = WARNA_PASTEL[idx % len(WARNA_PASTEL)]
        ax.plot(df_norm.index, df_norm[saham], label=saham, linewidth=2.2, color=warna_pilih)

    ax.set_ylabel("Indeks Pertumbuhan (Mulai = 100)")
    ax.set_xlabel("Tanggal")
    ax.legend(loc="upper left")
    ax.grid(True, linestyle="--", alpha=0.5)
    st.pyplot(fig)

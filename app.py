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
    "Aplikasi analisis portofolio syariah dengan struktur **6 Sheet persis seperti file Excel Anda** "
    "untuk konstituen JII (**BRIS, CTRA, TLKM** dan saham JII lainnya)."
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

# --- 2. SIDEBAR: PENGATURAN WAKTU & BOBOT ---
st.sidebar.header("⚙️ Pengaturan Portofolio JII")

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

periode_hitung = st.sidebar.selectbox(
    "3. Pilih Frekuensi Perhitungan:",
    options=["Mingguan", "Harian", "Bulanan", "Semester (6 Bulan)", "Tahunan"]
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

# Return & Statistik
df_return = df_harga_display.pct_change().fillna(0)
df_return_stats = df_harga_display.pct_change().dropna()
if df_return_stats.empty:
    df_return_stats = df_return

mean_return_stats = df_return_stats.mean()
cov_matrix_stats = df_return_stats.cov()
std_stats = df_return_stats.std()

# --- SIDEBAR: BOBOT & PARAMETER KINERJA ---
st.sidebar.subheader("4. Atur Bobot Investasi (%)")
mode_bobot = st.sidebar.radio(
    "Metode Penentuan Bobot:",
    options=["Manual (Slider)", "Bobot Berimbang (Equal Weight)"]
)

bobot_input = []
for i, saham in enumerate(saham_terpilih):
    nama_bersih = saham.replace(".JK", "")
    val_default = int(round(100 / len(saham_terpilih)))
    if mode_bobot == "Bobot Berimbang (Equal Weight)":
        val_default = int(round(100 / len(saham_terpilih)))
    nilai = st.sidebar.slider(f"Bobot {nama_bersih} (%)", min_value=0, max_value=100, value=val_default)
    bobot_input.append(nilai)

total_bobot = sum(bobot_input)
if total_bobot == 0:
    total_bobot = 1
weights = np.array(bobot_input) / total_bobot

st.sidebar.subheader("5. Parameter Kinerja (Benchmark & Rf)")
risk_free_rate = st.sidebar.number_input("Bunga Bebas Risiko (Rf - Tahunan)", value=0.06, step=0.005, format="%.3f")
market_return = st.sidebar.number_input("Expected Return Pasar (Rm - Tahunan)", value=0.10, step=0.005, format="%.3f")

WARNA_PASTEL = ["#B08968", "#D4A373", "#CCD5AE", "#99582A", "#6F4E37", "#BC6C25", "#E6CCB2"]


# =====================================================================
# STRUKTUR 6 SHEET SESUAI EXCEL ANDA
# =====================================================================

# --- SHEET 1: HARGA CLOSE MINGGUAN / PERIODE ---
st.header(f"1️⃣ Sheet 1: Harga Close {periode_hitung}")
df_sheet1 = df_harga_display.copy()
df_sheet1.insert(0, "No", range(1, len(df_sheet1) + 1))
st.dataframe(df_sheet1.style.format({"No": "{:.0f}", **{c: "Rp {:,.0f}" for c in df_harga_display.columns}}), use_container_width=True)

with st.expander("💡 Penjelasan Sederhana - Sheet 1 (Data Harga Close)", expanded=True):
    st.markdown("""
    * **Isi Sheet:** Menampilkan nomor urut, tanggal, dan harga penutupan (*Close*) murni dalam Rupiah untuk setiap emiten JII pilihan.
    * **Asal Angka:** Ditarik langsung secara *real-time* dari Bursa Efek Indonesia menggunakan API `yfinance` sesuai filter waktu yang Anda pilih di sidebar.
    """)

# --- SHEET 2: RETURN REALISASI & ER ---
st.header(f"2️⃣ Sheet 2: Return Realisasi & ER ({periode_hitung})")
df_sheet2 = df_return.copy()
df_sheet2.insert(0, "No", range(1, len(df_sheet2) + 1))
st.dataframe(df_sheet2.style.format({"No": "{:.0f}", **{c: "{:.6f}" for c in df_return.columns}}), use_container_width=True)

# Tampilkan ringkasan ER mirip baris bawah di Excel
st.markdown("**Expected Return (ER) Masing-masing Emiten (Rata-rata Return):**")
st.json({col.replace('.JK', ''): f"{val:.6f}" for col, val in mean_return_stats.items()})

with st.expander("💡 Penjelasan Sederhana - Sheet 2 (Return Realisasi & ER)", expanded=True):
    st.markdown("""
    * **Isi Sheet:** Menghitung persentase perubahan harga dari periode sebelumnya ke periode berjalan `(Harga_ini - Harga_lalu) / Harga_lalu`.
    * **ER (Expected Return):** Nilai rata-rata dari seluruh return realisasi emiten selama periode pengamatan.
    """)

# --- SHEET 3: VARIANS & STANDAR DEVIASI ---
st.header("3️⃣ Sheet 3: Varians & Standar Deviasi")
df_sheet3 = pd.DataFrame({
    "Emiten": [c.replace('.JK', '') for c in saham_terpilih],
    f"Mean Return ({periode_hitung})": mean_return_stats.values,
    "Variance": df_return_stats.var().values,
    "Standar Deviasi (Risiko)": std_stats.values,
    f"Expected Return ({periode_hitung} x {faktor_waktu})": mean_return_stats.values * faktor_waktu,
    f"Risiko Tahunan/Skala": std_stats.values * np.sqrt(faktor_waktu)
})
st.dataframe(df_sheet3.style.format("{:.6f}"), use_container_width=True)

with st.expander("💡 Penjelasan Sederhana - Sheet 3 (Varians & Standar Deviasi)", expanded=True):
    st.markdown(f"""
    * **Varians & Standar Deviasi:** Mengukur seberapa besar fluktuasi atau tingkat risiko naik-turun harga suatu emiten.
    * **Penyesuaian Waktu:** Dikalikan dengan faktor waktu (**{label_faktor_teks}** / faktor pengali `{faktor_waktu}`) untuk mendapatkan proyeksi tahunan/skala waktu yang sesuai.
    """)

# --- SHEET 4: COVARIANCE ---
st.header("4️⃣ Sheet 4: Kovarians (Covariance Matrix)")
st.dataframe(cov_matrix_stats.style.format("{:.6f}"), use_container_width=True)

with st.expander("💡 Penjelasan Sederhana - Sheet 4 (Covariance)", expanded=True):
    st.markdown("""
    * **Isi Sheet:** Matriks kovarians antar emiten.
    * **Cara Baca:** Menunjukkan arah pergerakan bersama antar saham. Jika bernilai negatif, emiten tersebut sangat baik untuk diversifikasi portofolio karena dapat saling meredam risiko.
    """)

# --- SHEET 5: KOEFISIEN KORELASI ---
st.header("5️⃣ Sheet 5: Koefisien Korelasi")
corr_matrix = df_return_stats.corr()
st.dataframe(corr_matrix.style.format("{:.6f}"), use_container_width=True)

with st.expander("💡 Penjelasan Sederhana - Sheet 5 (Koefisien Korelasi)", expanded=True):
    st.markdown("""
    * **Isi Sheet:** Nilai korelasi antar emiten (berkisar antara -1 hingga +1).
    * **Cara Baca:** Mendeskripsikan tingkat kebersamaan arah gerak harga saham. Korelasi mendekati -1 berarti pergerakannya sangat berlawanan arah.
    """)

# --- SHEET 6: RETURN PORTOFOLIO & KINERJA (SHARPE, TREYNOR, ALPHA JENSEN) ---
st.header("6️⃣ Sheet 6: Return Portofolio, Risiko, & Metrik Kinerja (Sharpe, Treynor, Alpha)")

port_return_periode = np.sum(mean_return_stats * weights)
port_std_periode = np.sqrt(np.dot(weights.T, np.dot(cov_matrix_stats, weights)))

port_return_skala = port_return_periode * faktor_waktu
port_std_skala = port_std_periode * np.sqrt(faktor_waktu)

# Estimasi Beta Portofolio sederhana
market_variance = 0.0020
beta_saham = []
for col in df_return_stats.columns:
    cov_with_market = df_return_stats[col].cov()
    beta_i = cov_with_market / market_variance if market_variance != 0 else 1.0
    beta_saham.append(beta_i)
port_beta = np.sum(weights * np.array(beta_saham))

# Perhitungan Metrik Kinerja
sharpe_ratio = (port_return_skala - risk_free_rate) / port_std_skala if port_std_skala != 0 else 0
treynor_ratio = (port_return_skala - risk_free_rate) / port_beta if port_beta != 0 else 0
jensen_alpha = port_return_skala - (risk_free_rate + port_beta * (market_return - risk_free_rate))

# Dashboard Metrik
col_m1, col_m2, col3 = st.columns(3)
col_m1.metric(f"Expected Return Portofolio ({periode_hitung})", f"{port_return_skala:.2%}")
col_m2.metric(f"Risiko Portofolio ({periode_hitung})", f"{port_std_skala:.2%}")
col3.metric("Beta Portofolio", f"{port_beta:.2f}")

col_m4, col_m5, col_m6 = st.columns(3)
col_m4.metric("Sharpe Ratio", f"{sharpe_ratio:.4f}", help="Return di atas Risk-Free per unit total risiko")
col_m5.metric("Treynor Ratio", f"{treynor_ratio:.4f}", help="Return di atas Risk-Free per unit risiko sistematis (Beta)")
col_m6.metric("Jensen's Alpha", f"{jensen_alpha:.4f}", help="Kelebihan return di atas model CAPM (Outperformance)")

# Tabel

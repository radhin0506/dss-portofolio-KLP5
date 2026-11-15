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
    options=["Harian", "Mingguan", "Bulanan", "Semester (6 Bulan)", "Tahunan"]
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
    "Harian": {"faktor": 252, "label_faktor": "252 hari bursa"},
    "Mingguan": {"faktor": 52, "label_faktor": "52 minggu"},
    "Bulanan": {"faktor": 12, "label_faktor": "12 bulan"},
    "Semester (6 Bulan)": {"faktor": 2, "label_faktor": "2 semester (faktor 2)"},
    "Tahunan": {"faktor": 1, "label_faktor": "1 tahun"}
}

faktor_waktu = aturan_periode[periode_hitung]["faktor"]
label_faktor_teks = aturan_periode[periode_hitung]["label_faktor"]

if periode_hitung == "Harian":
    df_harga = df_filtered.dropna()
elif periode_hitung == "Mingguan":
    df_harga = df_filtered.resample("W-FRI").last().dropna()
elif periode_hitung == "Bulanan":
    df_harga = df_filtered.resample("ME").last().dropna()
elif periode_hitung == "Semester (6 Bulan)":
    df_harga = df_filtered.resample("2QE").last().dropna()
else:
    df_harga = df_filtered.resample("YE").last().dropna()

df_harga_display = df_harga.copy()
df_harga_display.columns = [c.replace(".JK", "") for c in df_harga_display.columns]

df_return = df_harga_display.pct_change().fillna(0)
df_return_stats = df_harga_display.pct_change().dropna()
if df_return_stats.empty:
    df_return_stats = df_return

mean_return_stats = df_return_stats.mean()
cov_matrix_stats = df_return_stats.cov()

# --- HITUNG BOBOT OTOMATIS (OPTIMASI SHARPE) ---
np.random.seed(42)
jumlah_simulasi = 5000
bobot_terbaik = np.ones(len(saham_terpilih)) / len(saham_terpilih)
max_sharpe = -999

for _ in range(jumlah_simulasi):
    w = np.random.random(len(saham_terpilih))
    w /= np.sum(w)
    r_p = np.sum(mean_return_stats * w) * faktor_waktu
    std_p = np.sqrt(np.dot(w.T, np.dot(cov_matrix_stats, w))) * np.sqrt(faktor_waktu)
    sr = r_p / std_p if std_p != 0 else 0
    if sr > max_sharpe:
        max_sharpe = sr
        bobot_terbaik = w

st.sidebar.subheader("4. Atur Bobot Investasi (%)")
mode_bobot = st.sidebar.radio(
    "Metode Penentuan Bobot:",
    options=["Manual (Slider)", "Saran Otomatis (Optimal Sharpe)", "Bobot Berimbang (Equal Weight)"]
)

bobot_input = []
for i, saham in enumerate(saham_terpilih):
    nama_bersih = saham.replace(".JK", "")
    if mode_bobot == "Saran Otomatis (Optimal Sharpe)":
        val_default = int(round(bobot_terbaik[i] * 100))
    elif mode_bobot == "Bobot Berimbang (Equal Weight)":
        val_default = int(round(100 / len(saham_terpilih)))
    else:
        val_default = int(100 / len(saham_terpilih))
        
    nilai = st.sidebar.slider(f"Bobot {nama_bersih} (%)", min_value=0, max_value=100, value=val_default)
    bobot_input.append(nilai)

total_bobot = sum(bobot_input)
if total_bobot == 0:
    total_bobot = 1

weights = np.array(bobot_input) / total_bobot

WARNA_PASTEL = ["#B08968", "#D4A373", "#CCD5AE", "#99582A", "#6F4E37", "#BC6C25", "#E6CCB2", "#D4A373"]


# =====================================================================
# TAMPILAN SHEET LENGKAP DENGAN PENJELASAN & LANGKAH PERHITUNGAN
# =====================================================================

# --- SHEET 1: DATA HARGA ---
st.header(f"1️⃣ Sheet Data Harga Penutupan Saham JII ({periode_hitung})")
st.dataframe(df_harga_display.style.format("Rp {:,.0f}"), use_container_width=True)

with st.expander("💡 Penjelasan & Langkah Perhitungan - Sheet 1 (Data Harga)", expanded=True):
    st.markdown("""
    * **Asal Angka:** Ditarik secara *real-time* dari server Bursa Efek Indonesia (BEI) melalui API `yfinance` berupa harga penutupan murni (*Close Price*) dalam satuan Rupiah.
    * **Langkah Kerja:** Aplikasi menyaring data perdagangan secara presisi hanya pada rentang waktu yang Anda pilih (misal tahun 2026 saja) tanpa mencampur data dari tahun-tahun sebelumnya. Tabel ini berfungsi sebagai database acuan utama.
    """)

# --- SHEET 2: RETURN ---
st.header(f"2️⃣ Sheet Perhitungan Return / Imbal Hasil ({periode_hitung})")
st.dataframe(df_return.style.format("{:.2%}"), use_container_width=True)

with st.expander("💡 Penjelasan & Langkah Perhitungan - Sheet 2 (Return)", expanded=True):
    st.markdown("""
    * **Asal Angka:** Dihitung otomatis dari perbandingan harga saham pada periode saat ini dengan harga pada periode persis sebelumnya di Sheet 1.
    * **Langkah Perhitungan (Rumus):**
      1. Ambil harga periode ini ($P_t$) dan kurangi dengan harga periode sebelumnya ($P_{t-1}$).
      2. Bagi hasil selisih tersebut dengan harga periode sebelumnya ($P_{t-1}$).
      3. Rumus matematis: `(Harga Sekarang - Harga Sebelumnya) / Harga Sebelumnya`.
      * *Contoh:* Jika periode lalu harganya Rp 2.500 lalu periode ini naik menjadi Rp 2.750, maka perhitungannya adalah `(2.750 - 2.500) / 2.500 = +10%`. Nilai positif menandakan keuntungan, sedangkan nilai negatif menandakan kerugian.
    """)

# --- SHEET 3: STATISTIK INDIVIDUAL ---
st.header("3️⃣ Sheet Statistik & Risiko Individual Saham")
df_statistik = pd.DataFrame({
    f"Mean Return ({periode_hitung})": mean_return_stats,
    f"Varians ({periode_hitung})": df_return_stats.var(),
    f"Std. Deviasi / Risiko ({periode_hitung})": df_return_stats.std(),
    "Expected Return (Tahunan/Periode)": mean_return_stats * faktor_waktu,
    "Risiko / Volatilitas (Tahunan/Periode)": df_return_stats.std() * np.sqrt(faktor_waktu)
})
st.dataframe(df_statistik.style.format("{:.4f}"), use_container_width=True)

with st.expander("💡 Penjelasan & Langkah Perhitungan - Sheet 3 (Statistik & Risiko)", expanded=True):
    st.markdown(f"""
    * **Asal Angka:** Diolah dari tabel Return di Sheet 2 menggunakan metode statistik standar keuangan.
    * **Langkah Perhitungan & Penyesuaian Frekuensi:**
      1. **Mean Return (Rata-rata):** Menjumlahkan seluruh angka return di Sheet 2 lalu dibagi dengan total jumlah periode data.
      2. **Std. Deviasi (Risiko Per Periode):** Mengukur seberapa besar naik-turunnya fluktuasi harga saham dari rata-ratanya.
      3. **Expected Return Skala Waktu ({periode_hitung}):** Mean Return per periode dikalikan dengan **Faktor Penyetara ({faktor_waktu})** sesuai frekuensi pilihan Anda (**{label_faktor_teks}**). Jika Anda memilih Semester/6 Bulan (faktor 2), maka return periode dikali 2.
      4. **Risiko Skala Waktu:** Standar deviasi per periode dikalikan dengan akar kuadrat dari Faktor Penyetara ($\sqrt{{Faktor}}$).
    """)

# --- SHEET 4: MATRIKS KOVARIANS ---
st.header("4️⃣ Sheet Matriks Kovarians (Covariance Matrix)")
st.dataframe(cov_matrix_stats.style.format("{:.6f}"), use_container_width=True)

with st.expander("💡 Penjelasan & Langkah Perhitungan - Sheet 4 (Matriks Kovarians)", expanded=True):
    st.markdown("""
    * **Asal Angka:** Dihitung dengan membandingkan pola pergerakan naik-turun antar dua saham secara bersamaan (misal saham A dibandingkan dengan saham B).
    * **Langkah Perhitungan:** Menggunakan rumus statistik kovarians sampel. Jika hasil kovarians bernilai **negatif**, artinya kedua saham tersebut sering bergerak berlawanan arah, yang mana sangat efektif untuk menekan risiko gabungan portofolio melalui diversifikasi.
    """)

# --- SHEET 5: EVALUASI, GRAFIK & KEPUTUSAN ---
st.header("5️⃣ Sheet Evaluasi Portofolio & Saran Pengambilan Bobot")

port_return_periode = np.sum(mean_return_stats * weights)
port_std_periode = np.sqrt(np.dot(weights.T, np.dot(cov_matrix_stats, weights)))
port_return_tahunan = port_return_periode * faktor_waktu
port_std_tahunan = port_std_periode * np.sqrt(faktor_waktu)
sharpe_ratio = port_return_tahunan / port_std_tahunan if port_std_tahunan != 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric(f"Expected Return ({periode_hitung})", f"{port_return_tahunan:.2%}")
col2.metric(f"Risiko Portofolio ({periode_hitung})", f

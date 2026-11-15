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
    "Tahunan": {"rule": "YE", "faktor": 1}
}

faktor_waktu = aturan_periode[periode_hitung]["faktor"]

if periode_hitung == "Harian":
    df_harga = df_filtered.dropna()
else:
    rule_terpilih = aturan_periode[periode_hitung]["rule"]
    df_harga = df_filtered.resample(rule_terpilih).last().dropna()

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
# TAMPILAN SHEET LENGKAP DENGAN PENJELASAN & CARA HITUNGNYA
# =====================================================================

# --- SHEET 1: DATA HARGA ---
st.header(f"1️⃣ Sheet Data Harga Penutupan Saham JII ({periode_hitung})")
st.dataframe(df_harga_display.style.format("Rp {:,.0f}"), use_container_width=True)

with st.expander("💡 Penjelasan & Dari Mana Angka Ini Didapat - Sheet 1 (Data Harga)", expanded=True):
    st.markdown("""
    * **Sumber Angka:** Ditarik langsung secara *real-time* dari server Bursa Efek Indonesia (BEI) melalui API `yfinance` berupa harga penutupan murni (*Close Price*) dalam satuan Rupiah.
    * **Cara Kerja:** Aplikasi memfilter data secara presisi sesuai tahun atau tanggal yang Anda pilih di menu sebelah kiri tanpa mencampur data dari tahun sebelumnya.
    """)

# --- SHEET 2: RETURN ---
st.header(f"2️⃣ Sheet Perhitungan Return / Imbal Hasil ({periode_hitung})")
st.dataframe(df_return.style.format("{:.2%}"), use_container_width=True)

with st.expander("💡 Penjelasan & Dari Mana Angka Ini Didapat - Sheet 2 (Return)", expanded=True):
    st.markdown("""
    * **Sumber Angka:** Dihitung otomatis dari perbandingan harga saham pada periode saat ini dengan periode sebelumnya di Sheet 1.
    * **Cara Hitung:** 
      * Rumus: `(Harga Sekarang - Harga Sebelumnya) / Harga Sebelumnya`
      * Contoh: Jika bulan lalu harganya Rp 2.500 lalu bulan ini jadi Rp 2.750, maka hitungannya `(2.750 - 2.500) / 2.500 = +10%`. 
      * Nilai positif artinya untung, nilai negatif artinya rugi.
    """)

# --- SHEET 3: STATISTIK INDIVIDUAL ---
st.header("3️⃣ Sheet Statistik & Risiko Individual Saham")
df_statistik = pd.DataFrame({
    f"Mean Return ({periode_hitung})": mean_return_stats,
    f"Varians ({periode_hitung})": df_return_stats.var(),
    f"Std. Deviasi / Risiko ({periode_hitung})": df_return_stats.std(),
    "Expected Return (Tahunan)": mean_return_stats * faktor_waktu,
    "Risiko / Volatilitas (Tahunan)": df_return_stats.std() * np.sqrt(faktor_waktu)
})
st.dataframe(df_statistik.style.format("{:.4f}"), use_container_width=True)

with st.expander("💡 Penjelasan & Dari Mana Angka Ini Didapat - Sheet 3 (Statistik & Risiko)", expanded=True):
    st.markdown("""
    * **Sumber Angka:** Diolah dari tabel Return di Sheet 2 menggunakan rumus statistik standar keuangan.
    * **Cara Hitung:**
      * **Mean Return (Rata-rata):** Menjumlahkan seluruh return lalu dibagi jumlah periode.
      * **Std. Deviasi (Risiko per periode):** Mengukur seberapa besar naik-turunnya fluktuasi harga saham.
      * **Expected Return Tahunan:** Mean Return dikalikan dengan Faktor Waktu (misal dikali 12 jika bulanan, atau dikali 252 jika harian).
      * **Risiko Tahunan:** Standar deviasi dikalikan dengan akar kuadrat dari Faktor Waktu.
    """)

# --- SHEET 4: MATRIKS KOVARIANS ---
st.header("4️⃣ Sheet Matriks Kovarians (Covariance Matrix)")
st.dataframe(cov_matrix_stats.style.format("{:.6f}"), use_container_width=True)

with st.expander("💡 Penjelasan & Dari Mana Angka Ini Didapat - Sheet 4 (Matriks Kovarians)", expanded=True):
    st.markdown("""
    * **Sumber Angka:** Dihitung dengan membandingkan pola pergerakan naik-turun antar dua saham secara bersamaan (misal saham A terhadap saham B).
    * **Cara Hitung:** Menggunakan rumus statistik kovarians sampel. Jika hasilnya **negatif**, artinya kedua saham sering bergerak berlawanan arah, yang mana sangat bagus untuk menekan risiko gabungan portofolio (diversifikasi).
    """)

# --- SHEET 5: EVALUASI, GRAFIK & KEPUTUSAN ---
st.header("5️⃣ Sheet Evaluasi Portofolio & Saran Pengambilan Bobot")

port_return_periode = np.sum(mean_return_stats * weights)
port_std_periode = np.sqrt(np.dot(weights.T, np.dot(cov_matrix_stats, weights)))
port_return_tahunan = port_return_periode * faktor_waktu
port_std_tahunan = port_std_periode * np.sqrt(faktor_waktu)
sharpe_ratio = port_return_tahunan / port_std_tahunan if port_std_tahunan != 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Expected Return Tahunan", f"{port_return_tahunan:.2%}")
col2.metric("Risiko Portofolio Tahunan", f"{port_std_tahunan:.2%}")
col3.metric("Sharpe Ratio (Efisiensi)", f"{sharpe_ratio:.2f}")

with st.expander("💡 Penjelasan & Dari Mana Angka Ini Didapat - Sheet 5 (Evaluasi Portofolio)", expanded=True):
    saran_teks = [f"- **{s.replace('.JK', '')}**: bobot optimal **{bobot_terbaik[i]*100:.1f}%**" for i, s in enumerate(saham_terpilih)]
    st.markdown(f"""
    * **Expected Return Tahunan:** Hasil penjumlahan dari persentase bobot uang Anda dikali return tahunan masing-masing saham (**{port_return_tahunan:.2%}**).
    * **Risiko Portofolio Tahunan:** Perhitungan gabungan bobot dan matriks kovarians (Sheet 4) yang memperhitungkan efek saling menutupi risiko antar saham (**{port_std_tahunan:.2%}**).
    * **Sharpe Ratio:** Tingkat efisiensi investasi (Keuntungan dibagi Risiko). Semakin tinggi, semakin baik.
    <br><br>
    **Saran Alokasi Bobot Terbaik (Hasil Simulasi Komputer untuk Keuntungan Maksimal):**<br>
    """ + "<br>".join(saran_teks), unsafe_allow_html=True)

# --- GRAFIK KINERJA ---
st.subheader("📊 Visualisasi Pertumbuhan Harga Saham JII (Base = 100)")
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

with st.expander("💡 Penjelasan Grafik Pertumbuhan", expanded=False):
    st.markdown("Grafik ini menyamakan titik awal seluruh saham di angka **100** pada tanggal pertama yang Anda pilih. Garis yang paling tinggi di akhir grafik adalah saham dengan pertumbuhan paling kencang.")

# ---

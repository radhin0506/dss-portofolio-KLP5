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
    "Aplikasi analisis risiko, *return*, optimasi bobot, dan rekomendasi portofolio syariah berdasarkan "
    "konstituen **Jakarta Islamic Index (JII)** di Bursa Efek Indonesia (BEI) secara *real-time*."
)

# --- 1. DAFTAR RESMI 30 SAHAM KONSTITUEN INDEKS JII ---
DAFTAR_SAHAM_JII = {
    "AADI.JK": "AADI - Adaro Andalan Indonesia Tbk. (Energi)",
    "ADMR.JK": "ADMR - Alamtri Minerals Indonesia Tbk. (Pertambangan)",
    "ADRO.JK": "ADRO - Alamtri Resources Indonesia Tbk. (Energi)",
    "ANTM.JK": "ANTM - Aneka Tambang Tbk. (Pertambangan)",
    "ARCI.JK": "ARCI - Archi Indonesia Tbk. (Barang Baku)",
    "BKSL.JK": "BKSL - Sentul City Tbk. (Properti & Real Estate)",
    "BRIS.JK": "BRIS - Bank Syariah Indonesia Tbk. (Perbankan Syariah)",
    "BRMS.JK": "BRMS - Bumi Resources Minerals Tbk. (Pertambangan)",
    "BUMI.JK": "BUMI - Bumi Resources Tbk. (Energi)",
    "CPIN.JK": "CPIN - Charoen Pokphand Indonesia Tbk. (Barang Konsumen Primer)",
    "CTRA.JK": "CTRA - Ciputra Development Tbk. (Properti & Real Estate)",
    "DEWA.JK": "DEWA - Darma Henwa Tbk. (Energi)",
    "ENRG.JK": "ENRG - Energi Mega Persada Tbk. (Energi)",
    "EXCL.JK": "EXCL - XLsmart Telecom Sejahtera Tbk. (Telekomunikasi)",
    "ICBP.JK": "ICBP - Indofood CBP Sukses Makmur Tbk. (Barang Konsumen Primer)",
    "INDF.JK": "INDF - Indofood Sukses Makmur Tbk. (Barang Konsumen Primer)",
    "INKP.JK": "INKP - Indah Kiat Pulp & Paper Tbk. (Barang Baku)",
    "JPFA.JK": "JPFA - Japfa Comfeed Indonesia Tbk. (Barang Konsumen Primer)",
    "KLBF.JK": "KLBF - Kalbe Farma Tbk. (Kesehatan)",
    "MBMA.JK": "MBMA - Merdeka Battery Materials Tbk. (Barang Baku)",
    "MDKA.JK": "MDKA - Merdeka Copper Gold Tbk. (Barang Baku)",
    "MEDC.JK": "MEDC - Medco Energi Internasional Tbk. (Energi)",
    "PGAS.JK": "PGAS - Perusahaan Gas Negara Tbk. (Energi)",
    "PTBA.JK": "PTBA - Bukit Asam Tbk. (Energi)",
    "RAJA.JK": "RAJA - Rukun Raharja Tbk. (Energi)",
    "RATU.JK": "RATU - Raharja Energi Cepu Tbk. (Energi)",
    "TLKM.JK": "TLKM - Telkom Indonesia (Persero) Tbk. (Telekomunikasi)",
    "TPIA.JK": "TPIA - Chandra Asri Pacific Tbk. (Barang Baku)",
    "UNTR.JK": "UNTR - United Tractors Tbk. (Industri)",
    "UNVR.JK": "UNVR - Unilever Indonesia Tbk. (Barang Konsumen Primer)",
    "WIFI.JK": "WIFI - Solusi Sinergi Digital Tbk. (Teknologi)"
}

# --- 2. SIDEBAR: PENGATURAN DINAMIS & FILTER WAKTU SPESIFIK ---
st.sidebar.header("⚙️ Pengaturan Portofolio JII")

saham_terpilih = st.sidebar.multiselect(
    "1. Pilih Saham Konstituen JII (Min. 2):",
    options=list(DAFTAR_SAHAM_JII.keys()),
    default=["BRIS.JK", "TLKM.JK", "CTRA.JK", "ADRO.JK"],
    format_func=lambda x: DAFTAR_SAHAM_JII[x]
)

if len(saham_terpilih) < 2:
    st.warning("⚠️ Silakan pilih minimal **2 saham JII** di menu sebelah kiri untuk membentuk portofolio syariah.")
    st.stop()

# Mode Filter Waktu Kustom / Tahun Spesifik
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

# Pilihan Frekuensi Perhitungan
periode_hitung = st.sidebar.selectbox(
    "3. Pilih Frekuensi Perhitungan:",
    options=["Harian", "Mingguan", "Bulanan", "Tahunan"]
)


# --- 3. MENGAMBIL DATA & FILTER BERDASARKAN TANGGAL PILIHAN ---
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

with st.spinner("Mengambil data real-time saham JII dari Bursa Efek Indonesia..."):
    df_raw = ambil_data_saham(saham_terpilih, periode_yf)

if df_raw.empty:
    st.error("Gagal menarik data saham. Periksa koneksi internet Anda lalu muat ulang halaman.")
    st.stop()

df_raw = df_raw[saham_terpilih]
df_raw.index = pd.to_datetime(df_raw.index)

# FILTER TANGGAL PRESISI SESUAI PILIHAN USER (Tanpa mengambil tahun sebelumnya)
df_filtered = df_raw[(df_raw.index >= tanggal_mulai) & (df_raw.index <= tanggal_selesai)]

if df_filtered.empty:
    st.error(f"⚠️ Tidak ada data perdagangan pada rentang tanggal tersebut ({tanggal_mulai.strftime('%d-%m-%Y')} s.d. {tanggal_selesai.strftime('%d-%m-%Y')}). Silakan pilih rentang waktu lain.")
    st.stop()

aturan_periode = {
    "Harian": {"faktor": 252, "ket": "Hari bursa aktif"},
    "Mingguan": {"rule": "W-FRI", "faktor": 52, "ket": "Setiap akhir minggu (Jumat)"},
    "Bulanan": {"rule": "ME", "faktor": 12, "ket": "Akhir bulan"},
    "Tahunan": {"rule": "YE", "faktor": 1, "ket": "Akhir tahun"}
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
mean_return = df_return.mean()
cov_matrix = df_return.cov()

# --- HITUNG SARAN BOBOT OTOMATIS (OPTIMASI SHARPE) ---
np.random.seed(42)
jumlah_simulasi = 5000
bobot_terbaik = np.ones(len(saham_terpilih)) / len(saham_terpilih)
max_sharpe = -999

for _ in range(jumlah_simulasi):
    w = np.random.random(len(saham_terpilih))
    w /= np.sum(w)
    r_p = np.sum(mean_return * w) * faktor_waktu
    std_p = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w))) * np.sqrt(faktor_waktu)
    sr = r_p / std_p if std_p != 0 else 0
    if sr > max_sharpe:
        max_sharpe = sr
        bobot_terbaik = w

# PENGATURAN BOBOT DI SIDEBAR
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
    st.error("Total bobot investasi tidak boleh 0%!")
    st.stop()

weights = np.array(bobot_input) / total_bobot
ringkasan_bobot = ", ".join([f"{s.replace('.JK', '')}: {w*100:.1f}%" for s, w in zip(saham_terpilih, weights)])
st.sidebar.info(f"**Komposisi Bobot Aktif (Total 100%):**\n\n{ringkasan_bobot}")

WARNA_PASTEL = ["#B08968", "#D4A373", "#CCD5AE", "#99582A", "#6F4E37", "#BC6C25", "#E6CCB2", "#D4A373"]


# =====================================================================
# TAMPILAN SHEET, PENJELASAN, RUMUS & CONTOH ANGKA RIIL
# =====================================================================

# --- SHEET 1: DATA HARGA ---
st.header(f"1️⃣ Sheet Data Harga Penutupan Saham JII ({periode_hitung})")
st.dataframe(df_harga_display.style.format("Rp {:,.0f}"), use_container_width=True)

contoh_saham_satu = df_harga_display.columns[0]
harga_baris_akhir = df_harga_display[contoh_saham_satu].iloc[-1]
harga_baris_sebelumnya = df_harga_display[contoh_saham_satu].iloc[-2] if len(df_harga_display) > 1 else harga_baris_akhir

with st.expander("📘 Penjelasan Rumus & Contoh Angka Riil - Sheet 1 (Data Harga)", expanded=True):
    tgl_mulai_str = tanggal_mulai.strftime('%d %b %Y')
    tgl_selesai_str = tanggal_selesai.strftime('%d %b %Y')
    st.markdown(f"""
    * **Konsep & Rumus:** Sheet ini menampilkan data harga penutupan (*Close*) murni dalam Rupiah yang difilter spesifik mulai **{tgl_mulai_str}** s.d. **{tgl_selesai_str}**.
    * **Padanan Excel:** Menggunakan fungsi `VLOOKUP` atau filter tanggal pada rentang data bursa.
    * **Contoh Angka Riil pada Portofolio Anda:**
      * Harga penutupan saham **{contoh_saham_satu}** pada awal periode/sebelumnya adalah **Rp {harga_baris_sebelumnya:,.0f}**.
      * Harga penutupan pada periode terakhir tercatat sebesar **Rp {harga_baris_akhir:,.0f}**.
    * **📌 Kesimpulan Sheet 1:** Data tersaji murni sesuai rentang waktu yang Anda tentukan tanpa tercampur tahun sebelumnya.
    """)

# --- SHEET 2: RETURN ---
st.header(f"2️⃣ Sheet Perhitungan Return / Imbal Hasil ({periode_hitung})")
st.dataframe(df_return.style.format("{:.2%}"), use_container_width=True)

contoh_return_val = df_return[contoh_saham_satu].iloc[-1] if len(df_return) > 0 else 0
with st.expander("📘 Penjelasan Rumus & Contoh Angka Riil - Sheet 2 (Return)", expanded=True):
    st.markdown(f"""
    * **Rumus Matematika:** Return = ( Harga Sekarang - Harga Sebelumnya ) / Harga Sebelumnya
    * **Padanan Rumus Excel:** `=(B3 - B2) / B2`
    * **Contoh Angka Riil pada Portofolio Anda:**
      * Perhitungan untuk saham **{contoh_saham_satu}**: **{contoh_return_val:.4%}** pada periode terakhir.
    * **📌 Kesimpulan Sheet 2:** Menunjukkan persentase keuntungan atau kerugian per periode secara konsisten.
    """)

# --- SHEET 3: STATISTIK INDIVIDUAL ---
st.header("3️⃣ Sheet Statistik & Risiko Individual Saham")
df_return_stats = df_harga_display.pct_change().dropna()
if df_return_stats.empty:
    df_return_stats = df_return # Fallback jika titik data sedikit

std_return = df_return_stats.std()
var_return = df_return_stats.var()
mean_return_stats = df_return_stats.mean()

df_statistik = pd.DataFrame({
    f"Mean Return ({periode_hitung})": mean_return_stats,
    f"Varians ({periode_hitung})": var_return,
    f"Std. Deviasi / Risiko ({periode_hitung})": std_return,
    "Expected Return (Tahunan)": mean_return_stats * faktor_waktu,
    "Risiko / Volatilitas (Tahunan)": std_return * np.sqrt(faktor_waktu)
})

st.dataframe(df_statistik.style.format("{:.4f}"), use_container_width=True)

contoh_mean = mean_return_stats[contoh_saham_satu]
contoh_std = std_return[contoh_saham_satu]
contoh_ann_return = contoh_mean * faktor_waktu
contoh_ann_std = contoh_std * np.sqrt(faktor_waktu)

with st.expander("📘 Penjelasan Rumus & Contoh Angka Riil - Sheet 3 (Statistik & Risiko)", expanded=True):
    st.markdown(f"""
    * **Rumus Matematika:** Annualisasi Return = Mean Return x Faktor Waktu ({faktor_waktu}). Annualisasi Risiko = Standar Deviasi x akar({faktor_waktu}).
    * **Padanan Rumus Excel:** `=AVERAGE(...)`, `=STDEV.S(...)`
    * **Contoh Angka Riil pada Saham {contoh_saham_satu}:**
      * **Expected Return Tahunan:** `{contoh_ann_return:.2%}`
      * **Risiko Tahunan:** `{contoh_ann_std:.2%}`
    * **📌 Kesimpulan Sheet 3:** Menilai tingkat pengembalian dan volatilitas tahunan berdasarkan data pada rentang waktu yang Anda pilih saja.
    """)

# --- SHEET 4: MATRIKS KOVARIANS ---
st.header("4️⃣ Sheet Matriks Kovarians (Covariance Matrix)")
cov_matrix_stats = df_return_stats.cov()
st.dataframe(cov_matrix_stats.style.format("{:.6f}"), use_container_width=True)

with st.expander("📘 Penjelasan Rumus & Contoh Angka Riil - Sheet 4 (Matriks Kovarians)", expanded=True):
    st.markdown(f"""
    * **Rumus Matematika:** Mengukur variasi bersama antar saham untuk melihat korelasi pergerakan harga.
    * **Padanan Rumus Excel:** `=COVARIANCE.S(...)`
    * **📌 Kesimpulan Sheet 4:** Matriks kovarians ini dihitung secara eksklusif dari data rentang waktu terpilih untuk bahan optimasi portofolio.
    """)

# --- SHEET 5: EVALUASI & SARAN PENGAMBILAN BOBOT ---
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

with st.expander("📘 Penjelasan Rumus & Contoh Angka Riil - Sheet 5 (Evaluasi Portofolio & Sharpe)", expanded=True):
    saran_teks = [f"- **{s.replace('.JK', '')}**: bobot optimal **{bobot_terbaik[i]*100:.1f}%**" for i, s in enumerate(saham_terpilih)]
    
    st.markdown(f"""
    * **Rumus Matematika:** Return Portofolio = Sumproduct(Bobot, Return). Risiko Portofolio = Akar perkalian matriks bobot dan kovarians. Sharpe Ratio = Return / Risiko.
    * **Contoh Angka Riil Portofolio Anda:**
      * **Expected Return Tahunan:** **{port_return_tahunan:.2%}**
      * **Risiko Tahunan:** **{port_std_tahunan:.2%}**
      * **Sharpe Ratio:** **{sharpe_ratio:.2f}**
    * **Saran Alokasi Bobot Optimal (Sharpe Ratio Maksimal):**
      {'<br>'.join(saran_teks)}
    * **📌 Kesimpulan Sheet 5:** Menghasilkan rasio efisiensi portofolio terbaik pada rentang waktu yang Anda tentukan.
    """)

# --- GRAFIK KINERJA DENGAN WARNA PASTEL COKLAT ---
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

# --- 6. KESIMPULAN & REKOMENDASI KEPUTUSAN OTOMATIS ---
st.subheader("💡 Kesimpulan & Rekomendasi Keputusan Portofolio Syariah")

daftar_nama_pendek = ", ".join(df_harga_display.columns)

if port_std_tahunan < 0.15:
    kategori_risiko = "Rendah (Konservatif) 🛡️"
    deskripsi_keputusan = f"""
**Rekomendasi Keputusan:** Layak Dipertimbangkan untuk Investasi Syariah Jangka Panjang.

**Analisis Data Pasar:** Berdasarkan analisis pada rentang waktu terpilih untuk emiten JII (**{daftar_nama_pendek}**), portofolio ini memiliki volatilitas tahunan sebesar **{port_std_tahunan:.2%}** dengan potensi return tahunan **{port_return_tahunan:.2%}**. Alokasi bobot saat ini efektif menjaga keamanan modal.
"""
elif port_std_tahunan <= 0.25:
    kategori_risiko = "Sedang (Moderat) ⚖️"
    deskripsi_keputusan = f"""
**Rekomendasi Keputusan:** Seimbang & Layak Dieksekusi.

**Analisis Data Pasar:** Berdasarkan analisis pada rentang waktu terpilih untuk emiten JII (**{daftar_nama_pendek}**), portofolio berada pada titik keseimbangan optimal antara potensi keuntungan tahunan (**{port_return_tahunan:.2%}**) dan risiko (**{port_std_tahunan:.2%}**). Nilai *Sharpe Ratio* sebesar **{sharpe_ratio:.2f}** menunjukkan efisiensi yang baik.
"""
else:
    kategori_risiko = "Tinggi (Agresif) 🚀"
    deskripsi_keputusan = f"""
**Rekomendasi Keputusan:** Perlu Pengawasan Ketat / Khusus Investor Agresif.

**Analisis Data Pasar:** Berdasarkan analisis pada rentang waktu terpilih untuk emiten JII (**{daftar_nama_pendek}**), portofolio ini mencatatkan fluktuasi harga tahunan yang tinggi (**{port_std_tahunan:.2%}**). Disarankan bagi investor yang siap menghadapi volatilitas pasar jangka pendek.
"""

st.info(f"**Profil Risiko Portofolio JII:** {kategori_risiko}")
st.markdown(deskripsi_keputusan)

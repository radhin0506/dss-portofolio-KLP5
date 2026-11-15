import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="DSS Portofolio Saham Syariah (JII)", layout="wide")
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

# --- 2. SIDEBAR: PENGATURAN DINAMIS ---
st.sidebar.header("⚙️ Pengaturan Portofolio JII")

saham_terpilih = st.sidebar.multiselect(
    "1. Pilih Saham Konstituen JII (Min. 2):",
    options=list(DAFTAR_SAHAM_JII.keys()),
    default=["BRIS.JK", "TLKM.JK", "ICBP.JK", "ADRO.JK"],
    format_func=lambda x: DAFTAR_SAHAM_JII[x]
)

if len(saham_terpilih) < 2:
    st.warning("⚠️ Silakan pilih minimal **2 saham JII** di menu sebelah kiri untuk membentuk portofolio syariah.")
    st.stop()

# Rentang waktu data historis
rentang_waktu = st.sidebar.selectbox(
    "2. Rentang Data Historis:",
    options=["1 Tahun", "2 Tahun", "3 Tahun", "5 Tahun"],
    index=1
)
mapping_tahun = {"1 Tahun": 1, "2 Tahun": 2, "3 Tahun": 3, "5 Tahun": 5}
jumlah_tahun = mapping_tahun[rentang_waktu]

# Pilihan Frekuensi Perhitungan
periode_hitung = st.sidebar.selectbox(
    "3. Pilih Frekuensi Perhitungan:",
    options=["Harian", "Mingguan", "Bulanan", "Tahunan"]
)

# Selalu tarik data lebih panjang 1 tahun dari pilihan agar setelah resampling tidak terpotong
periode_yf = f"{jumlah_tahun + 1}y"


# --- 3. MENGAMBIL DATA REAL-TIME DARI WEB ---
@st.cache_data(ttl=3600)
def ambil_data_saham(tickers, period):
    data = yf.download(tickers, period=period, progress=False)["Close"]
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

aturan_periode = {
    "Harian": {"rule": "D", "faktor": 252, "ket": "252 hari perdagangan bursa dalam 1 tahun"},
    "Mingguan": {"rule": "W", "faktor": 52, "ket": "52 minggu dalam 1 tahun"},
    "Bulanan": {"rule": "ME", "faktor": 12, "ket": "12 bulan dalam 1 tahun"},
    "Tahunan": {"rule": "YE", "faktor": 1, "ket": "1 tahun penuh"}
}

rule_terpilih = aturan_periode[periode_hitung]["rule"]
faktor_waktu = aturan_periode[periode_hitung]["faktor"]
ket_faktor = aturan_periode[periode_hitung]["ket"]

if periode_hitung == "Harian":
    df_harga = df_raw.dropna()
else:
    df_harga = df_raw.resample(rule_terpilih).last().dropna()

# PERBAIKAN PENGGANTI .last(): Gunakan pd.DateOffset agar aman di semua versi Pandas
tanggal_akhir = df_harga.index.max()
tanggal_mulai = tanggal_akhir - pd.DateOffset(years=jumlah_tahun)
df_harga = df_harga[df_harga.index >= tanggal_mulai]

df_harga_display = df_harga.copy()
df_harga_display.columns = [c.replace(".JK", "") for c in df_harga_display.columns]

# Hitung Return & Statistik dasar
df_return = df_harga_display.pct_change().dropna()
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

# --- PALET WARNA DASAR PASTEL UNTUK GRAFIK ---
WARNA_PASTEL = ["#A0C4FF", "#BDB2FF", "#FFC6FF", "#FFADAD", "#CAFFBF", "#FDFFB6", "#FFD6A5", "#9BF6FF"]


# =====================================================================
# TAMPILAN SHEET, PENJELASAN & KESIMPULAN
# =====================================================================

# --- SHEET 1: DATA HARGA ---
st.header(f"1️⃣ Sheet Data Harga Penutupan Saham JII ({periode_hitung})")
st.dataframe(df_harga_display.tail(10).style.format("Rp {:,.0f}"), use_container_width=True)

with st.expander("📘 Penjelasan Detail & Kesimpulan Sheet 1 (Data Harga Historis)", expanded=True):
    tgl_awal_str = df_harga_display.index.min().strftime('%d %b %Y')
    tgl_akhir_str = df_harga_display.index.max().strftime('%d %b %Y')
    st.markdown(f"""
    * **Cakupan Emiten:** Konstituen resmi **Jakarta Islamic Index (JII)**.
    * **Rentang & Frekuensi Data:** Menampilkan data lengkap selama **{rentang_waktu}** (dari **{tgl_awal_str}** s.d. **{tgl_akhir_str}**) dengan frekuensi **{periode_hitung.lower()}** ({len(df_harga_display)} titik data valid).
    * **📌 Kesimpulan Sheet 1:** Data harga berhasil ditarik secara utuh dan konsisten dari awal hingga akhir rentang waktu yang dipilih.
    """)

# --- SHEET 2: RETURN ---
st.header(f"2️⃣ Sheet Perhitungan Return / Imbal Hasil ({periode_hitung})")
st.dataframe(df_return.tail(10).style.format("{:.2%}"), use_container_width=True)

with st.expander("📘 Penjelasan Detail & Kesimpulan Sheet 2 (Return Saham)", expanded=True):
    st.markdown("""
    * **Rumus:** $R_t = \\frac{P_t - P_{t-1}}{P_{t-1}}$ (Persentase perubahan harga antar periode).
    * **📌 Kesimpulan Sheet 2:** Nilai return positif menunjukkan adanya kenaikan harga saham pada periode tersebut, sedangkan nilai negatif menunjukkan terjadinya koreksi/penurunan harga.
    """)

# --- SHEET 3: STATISTIK INDIVIDUAL ---
st.header("3️⃣ Sheet Statistik & Risiko Individual Saham")
std_return = df_return.std()
var_return = df_return.var()

df_statistik = pd.DataFrame({
    f"Mean Return ({periode_hitung})": mean_return,
    f"Varians ({periode_hitung})": var_return,
    f"Std. Deviasi / Risiko ({periode_hitung})": std_return,
    "Expected Return (Tahunan)": mean_return * faktor_waktu,
    "Risiko / Volatilitas (Tahunan)": std_return * np.sqrt(faktor_waktu)
})

st.dataframe(df_statistik.style.format("{:.4f}"), use_container_width=True)

with st.expander("📘 Penjelasan Detail & Kesimpulan Sheet 3 (Statistik & Annualisasi)", expanded=True):
    saham_risiko_tinggi = df_statistik["Risiko / Volatilitas (Tahunan)"].idxmax()
    saham_return_tinggi = df_statistik["Expected Return (Tahunan)"].idxmax()
    st.markdown(f"""
    * **Kalkulasi:** Mengukur rata-rata return dan tingkat risiko (*Standard Deviation*) masing-masing saham JII yang disetarakan dalam skala 1 tahun (dikalikan faktor **{faktor_waktu}**).
    * **📌 Kesimpulan Sheet 3:** Emiten **{saham_return_tinggi}** mencatatkan potensi *return* tahunan tertinggi, sedangkan **{saham_risiko_tinggi}** memiliki tingkat fluktuasi risiko paling agresif.
    """)

# --- SHEET 4: MATRIKS KOVARIANS ---
st.header("4️⃣ Sheet Matriks Kovarians (Covariance Matrix)")
st.dataframe(cov_matrix.style.format("{:.6f}"), use_container_width=True)

with st.expander("📘 Penjelasan Detail & Kesimpulan Sheet 4 (Matriks Kovarians)", expanded=True):
    st.markdown("""
    * **Kalkulasi:** Mengukur arah pergerakan bersama antar saham syariah untuk memperhitungkan efek diversifikasi.
    * **📌 Kesimpulan Sheet 4:** Nilai kovarians yang negatif atau mendekati nol mengindikasikan bahwa pasangan saham tersebut bergerak tidak searah, sehingga sangat efektif untuk menekan risiko gabungan portofolio.
    """)

# --- SHEET 5: EVALUASI & SARAN PENGAMBILAN BOBOT ---
st.header("5️⃣ Sheet Evaluasi Portofolio & Saran Pengambilan Bobot")

port_return_periode = np.sum(mean_return * weights)
port_std_periode = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
port_return_tahunan = port_return_periode * faktor_waktu
port_std_tahunan = port_std_periode * np.sqrt(faktor_waktu)
sharpe_ratio = port_return_tahunan / port_std_tahunan if port_std_tahunan != 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Expected Return Tahunan", f"{port_return_tahunan:.2%}")
col2.metric("Risiko Portofolio Tahunan", f"{port_std_tahunan:.2%}")
col3.metric("Sharpe Ratio (Efisiensi)", f"{sharpe_ratio:.2f}")

with st.expander("📘 Penjelasan Detail & Kesimpulan Sheet 5 (Portofolio Gabungan)", expanded=True):
    saran_teks = [f"- **{s.replace('.JK', '')}**: disarankan bobot sekitar **{bobot_terbaik[i]*100:.1f}%**" for i, s in enumerate(saham_terpilih)]
    
    st.markdown(f"""
    1. **Evaluasi Portofolio:**
       * **Expected Return:** **{port_return_tahunan:.2%}** / tahun.
       * **Risiko Portofolio:** **{port_std_tahunan:.2%}** / tahun.
       * **Sharpe Ratio:** **{sharpe_ratio:.2f}**.
    2. **Saran Alokasi Bobot Optimal:**
       {'<br>'.join(saran_teks)}
    * **📌 Kesimpulan Sheet 5:** Kombinasi bobot aktif saat ini menghasilkan tingkat efisiensi portofolio (*Sharpe Ratio*) sebesar **{sharpe_ratio:.2f}**.
    """)

# --- GRAFIK KINERJA DENGAN WARNA PASTEL ---
st.subheader("📊 Visualisasi Pertumbuhan Harga Saham JII (Base = 100)")
df_norm = (df_harga_display / df_harga_display.iloc[0]) * 100
fig, ax = plt.subplots(figsize=(10, 4))
for idx, saham in enumerate(df_norm.columns):
    warna_ini = WARNA_PASTEL[idx % len(WARNA_PASTEL)]
    ax.plot(df_norm.index, df_norm[saham], label=saham, linewidth=2.2, color=warna_ini)
ax.set_ylabel("Indeks Pertumbuhan (Mulai = 100)")
ax.set_xlabel("Tanggal")
ax.legend()
ax.grid(True, linestyle="--", alpha=0.5)
st.pyplot(fig)

# --- 6. DESKRIPSI KEPUTUSAN OTOMATIS ---
st.subheader("💡 Kesimpulan & Rekomendasi Keputusan Portofolio Syariah")

daftar_nama_pendek = ", ".join(df_harga_display.columns)

if port_std_tahunan < 0.15:
    kategori_risiko = "Rendah (Konservatif) 🛡️"
    deskripsi_keputusan = f"""
**Rekomendasi Keputusan:** Layak Dipertimbangkan untuk Investasi Syariah Jangka Panjang.

**Analisis Data Pasar:** Berdasarkan analisis frekuensi **{periode_hitung.lower()}** pada kombinasi emiten JII (**{daftar_nama_pendek}**), portofolio ini memiliki volatilitas tahunan yang terkendali sebesar **{port_std_tahunan:.2%}** dengan potensi return tahunan **{port_return_tahunan:.2%}**. Alokasi bobot saat ini efektif menjaga keamanan modal.
"""
elif port_std_tahunan <= 0.25:
    kategori_risiko = "Sedang (Moderat) ⚖️"
    deskripsi_keputusan = f"""
**Rekomendasi Keputusan:** Seimbang & Layak Dieksekusi.

**Analisis Data Pasar:** Berdasarkan analisis frekuensi **{periode_hitung.lower()}** pada kombinasi emiten JII (**{daftar_nama_pendek}**), portofolio berada pada titik keseimbangan optimal antara potensi keuntungan tahunan (**{port_return_tahunan:.2%}**) dan risiko (**{port_std_tahunan:.2%}**). Nilai *Sharpe Ratio* sebesar **{sharpe_ratio:.2f}** menunjukkan efisiensi yang baik.
"""
else:
    kategori_risiko = "Tinggi (Agresif) 🚀"
    deskripsi_keputusan = f"""
**Rekomendasi Keputusan:** Perlu Pengawasan Ketat / Khusus Investor Agresif.

**Analisis Data Pasar:** Berdasarkan analisis frekuensi **{periode_hitung.lower()}** pada kombinasi emiten JII (**{daftar_nama_pendek}**), portofolio ini mencatatkan fluktuasi harga tahunan yang tinggi (**{port_std_tahunan:.2%}**). Disarankan bagi investor yang siap menghadapi volatilitas pasar jangka pendek.
"""

st.info(f"**Profil Risiko Portofolio JII:** {kategori_risiko}")
st.markdown(deskripsi_keputusan)

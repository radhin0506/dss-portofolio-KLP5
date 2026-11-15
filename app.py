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

# --- 2. SIDEBAR: PENGATURAN DINAMIS ---
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

rentang_waktu = st.sidebar.selectbox(
    "2. Rentang Data Historis:",
    options=["1 Tahun", "2 Tahun", "3 Tahun", "5 Tahun"],
    index=1
)
mapping_tahun = {"1 Tahun": 1, "2 Tahun": 2, "3 Tahun": 3, "5 Tahun": 5}
jumlah_tahun = mapping_tahun[rentang_waktu]

periode_hitung = st.sidebar.selectbox(
    "3. Pilih Frekuensi Perhitungan:",
    options=["Harian", "Mingguan", "Bulanan", "Tahunan"]
)

periode_yf = f"{jumlah_tahun}y"

# --- 3. MENGAMBIL DATA REAL-TIME ---
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

aturan_periode = {
    "Harian": {"faktor": 252, "ket": "Hari bursa aktif"},
    "Mingguan": {"rule": "W-FRI", "faktor": 52, "ket": "Setiap akhir minggu (Jumat)"},
    "Bulanan": {"rule": "ME", "faktor": 12, "ket": "Akhir bulan"},
    "Tahunan": {"rule": "YE", "faktor": 1, "ket": "Akhir tahun"}
}

faktor_waktu = aturan_periode[periode_hitung]["faktor"]

if periode_hitung == "Harian":
    df_harga = df_raw.dropna()
else:
    rule_terpilih = aturan_periode[periode_hitung]["rule"]
    df_harga = df_raw.resample(rule_terpilih).last().dropna()

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
harga_baris_sebelumnya = df_harga_display[contoh_saham_satu].iloc[-2]

with st.expander("📘 Penjelasan Rumus & Contoh Angka Riil - Sheet 1 (Data Harga)", expanded=True):
    st.markdown(f"""
    * **Konsep & Rumus:** Sheet ini menarik data harga penutupan (Close Price) riil dari API `yfinance` berdasarkan konstituen Jakarta Islamic Index (JII).
    * **Padanan Excel:** Menggunakan fungsi referensi data langsung dari database bursa atau `VLOOKUP` / `INDEX-MATCH`.
    * **Contoh Angka Riil pada Portofolio Anda:**
      * Harga penutupan saham **{contoh_saham_satu}** pada periode sebelumnya adalah **Rp {harga_baris_sebelumnya:,.0f}**.
      * Harga penutupan pada periode terakhir tercatat sebesar **Rp {harga_baris_akhir:,.0f}**.
    * **📌 Kesimpulan Sheet 1:** Seluruh data historis harga saham tersaji secara utuh dan akurat dalam satuan mata uang Rupiah.
    """)

# --- SHEET 2: RETURN ---
st.header(f"2️⃣ Sheet Perhitungan Return / Imbal Hasil ({periode_hitung})")
st.dataframe(df_return.style.format("{:.2%}"), use_container_width=True)

contoh_return_val = df_return[contoh_saham_satu].iloc[-1]
with st.expander("📘 Penjelasan Rumus & Contoh Angka Riil - Sheet 2 (Return)", expanded=True):
    st.markdown(f"""
    * **Rumus Matematika:** 
      Return (Rt) = ( Harga Sekarang - Harga Sebelumnya ) / Harga Sebelumnya
    * **Padanan Rumus Excel:** `=(B3 - B2) / B2`
    * **Contoh Angka Riil pada Portofolio Anda:**
      * Perhitungan untuk saham **{contoh_saham_satu}**: 
        ( {harga_baris_akhir:,.0f} - {harga_baris_sebelumnya:,.0f} ) / {harga_baris_sebelumnya:,.0f} = **{contoh_return_val:.4%}**
    * **📌 Kesimpulan Sheet 2:** Menunjukkan persentase keuntungan atau kerugian pada setiap titik waktu dengan cakupan data yang penuh.
    """)

# --- SHEET 3: STATISTIK INDIVIDUAL ---
st.header("3️⃣ Sheet Statistik & Risiko Individual Saham")
df_return_stats = df_harga_display.pct_change().dropna()
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
    * **Rumus Matematika:**
      * **Rata-rata Return (Mean):** Total seluruh return dibagi jumlah periode (n).
      * **Standar Deviasi (Risiko):** Akar kuadrat dari varians untuk mengukur tingkat fluktuasi harga.
      * **Annualisasi Return:** Mean Return dikali Faktor Waktu ({faktor_waktu}).
      * **Annualisasi Risiko:** Standar Deviasi dikali akar kuadrat dari Faktor Waktu.
    * **Padanan Rumus Excel:** `=AVERAGE( range )`, `=STDEV.S( range )`
    * **Contoh Angka Riil pada Saham {contoh_saham_satu}:**
      * Mean Return per periode = `{contoh_mean:.4f}`
      * Risiko (Standar Deviasi) per periode = `{contoh_std:.4f}`
      * **Expected Return Tahunan:** `{contoh_mean:.4f} x {faktor_waktu} = {contoh_ann_return:.2%}`
      * **Risiko Tahunan:** `{contoh_std:.4f} x akar({faktor_waktu}) = {contoh_ann_std:.2%}`
    * **📌 Kesimpulan Sheet 3:** Memberikan gambaran tingkat pengembalian tahunan serta besaran volatilitas risiko dari masing-masing emiten JII.
    """)

# --- SHEET 4: MATRIKS KOVARIANS ---
st.header("4️⃣ Sheet Matriks Kovarians (Covariance Matrix)")
cov_matrix_stats = df_return_stats.cov()
st.dataframe(cov_matrix_stats.style.format("{:.6f}"), use_container_width=True)

with st.expander("📘 Penjelasan Rumus & Contoh Angka Riil - Sheet 4 (Matriks Kovarians)", expanded=True):
    st.markdown(f"""
    * **Rumus Matematika:** 
      Mengukur variasi bersama antara dua variabel acak (saham A dan saham B) untuk melihat arah pergerakan harga bersama.
    * **Padanan Rumus Excel:** `=COVARIANCE.S( range_saham_A , range_saham_B )`
    * **Contoh Angka Riil:** Matriks di atas menghitung tingkat hubungan arah pergerakan naik/turun antar seluruh pasang emiten pilihan Anda. Nilai negatif menunjukkan korelasi berlawanan arah yang sangat baik untuk diversifikasi penekanan risiko portofolio.
    * **📌 Kesimpulan Sheet 4:** Matriks kovarians ini menjadi dasar utama dalam kalkulasi risiko gabungan portofolio pada sheet berikutnya.
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
    * **Rumus Matematika Portofolio:**
      * **Expected Return Portofolio (Rp):** Jumlah perkalian bobot setiap saham dengan return tahunannya.
      * **Risiko Portofolio (Sp):** Kalkulasi matriks perkalian bobot dengan matriks kovarians.
      * **Sharpe Ratio:** (Return Portofolio - Suku Bunga Bebas Risiko) / Risiko Portofolio.
    * **Padanan Rumus Excel:** Menggunakan `=SUMPRODUCT(...)` untuk return portofolio dan perkalian matriks `=MMULT(...)` untuk risiko.
    * **Contoh Angka Riil Portofolio Anda:**
      * **Expected Return Tahunan:** **{port_return_tahunan:.2%}**
      * **Risiko Tahunan:** **{port_std_tahunan:.2%}**
      * **Sharpe Ratio:** **{sharpe_ratio:.2f}**
    * **Saran Alokasi Bobot Optimal (Sharpe Ratio Maksimal):**
      {'<br>'.join(saran_teks)}
    * **📌 Kesimpulan Sheet 5:** Kombinasi bobot saat ini menghasilkan rasio efisiensi sebesar **{sharpe_ratio:.2f}**, yang menunjukkan tingkat keuntungan optimal yang diperoleh per unit risiko yang ditanggung.
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

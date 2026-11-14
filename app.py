import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="DSS Portofolio Saham Real-Time", layout="wide")
st.title("📈 Sistem Pendukung Keputusan (DSS) Portofolio Saham BEI")
st.markdown("Aplikasi analisis portofolio saham secara *real-time* langsung dari data pasar keuangan.")

# --- 1. SIDEBAR: PENGATURAN SAHAM & PERIODE ---
st.sidebar.header("⚙️ Pengaturan Data & Analisis")

# Daftar pilihan saham IDX (Bursa Efek Indonesia) dengan akhiran .JK
# Pengguna bisa mengetik atau memilih kode saham tambahan
saham_default = ["BRIS.JK", "CTRA.JK", "TLKM.JK", "BBCA.JK", "BBRI.JK"]
saham_terpilih = st.sidebar.multiselect(
    "1. Pilih Kode Saham (Emiten BEI):",
    options=saham_default,
    default=["BRIS.JK", "CTRA.JK", "TLKM.JK"]
)

if len(saham_terpilih) < 2:
    st.warning("⚠️ Silakan pilih minimal **2 saham** di menu sebelah kiri untuk membentuk portofolio.")
    st.stop()

# Rentang waktu data historis
rentang_waktu = st.sidebar.selectbox(
    "2. Rentang Data Historis:",
    options=["1 Tahun", "2 Tahun", "3 Tahun", "5 Tahun"],
    index=1 # Default 2 tahun
)

mapping_periode = {"1 Tahun": "1y", "2 Tahun": "2y", "3 Tahun": "3y", "5 Tahun": "5y"}
periode_yf = mapping_periode[rentang_waktu]

# Pilihan Periode Perhitungan (Harian/Mingguan/Bulanan/Tahunan)
periode_hitung = st.sidebar.selectbox(
    "3. Pilih Frekuensi Perhitungan:",
    options=["Harian", "Mingguan", "Bulanan", "Tahunan"]
)

# C. Pengaturan Bobot Portofolio
st.sidebar.subheader("4. Atur Bobot Investasi (%)")
bobot_input = []
for saham in saham_terpilih:
    # Hilangkan '.JK' untuk tampilan label slider agar bersih
    nama_bersih = saham.replace(".JK", "")
    nilai = st.sidebar.slider(f"Bobot {nama_bersih} (%)", min_value=0, max_value=100, value=int(100/len(saham_terpilih)))
    bobot_input.append(nilai)

total_bobot = sum(bobot_input)
if total_bobot == 0:
    st.error("Total bobot tidak boleh 0%!")
    st.stop()

weights = np.array(bobot_input) / total_bobot
st.sidebar.info(f"Total Bobot Ternormalisasi: **100%**")


# --- 2. MENGAMBIL DATA REAL-TIME DARI WEB (YFINANCE) ---
@st.cache_data(ttl=3600) # Cache data selama 1 jam agar aplikasi cepat
def ambil_data_saham(tickers, period):
    data = yf.download(tickers, period=period, progress=False)["Close"]
    # Jika hanya memilih 1 saham, ubah bentuk Series menjadi DataFrame
    if isinstance(data, pd.Series):
        data = data.to_frame()
    return data.dropna()

with st.spinner("Sedang mengambil data real-time dari bursa... Mohon tunggu sebentar."):
    df_raw = ambil_data_saham(saham_terpilih, periode_yf)

if df_raw.empty:
    st.error("Gagal menarik data saham. Periksa kembali koneksi internet atau kode saham yang dipilih.")
    st.stop()


# --- 3. PENYESUAIAN PERIODE (RESAMPLING) ---
aturan_periode = {
    "Harian": {"rule": "D", "faktor": 252, "ket": "252 hari bursa/tahun"},
    "Mingguan": {"rule": "W", "faktor": 52, "ket": "52 minggu/tahun"},
    "Bulanan": {"rule": "ME", "faktor": 12, "ket": "12 bulan/tahun"},
    "Tahunan": {"rule": "YE", "faktor": 1, "ket": "1 tahun penuh"}
}

rule_terpilih = aturan_periode[periode_hitung]["rule"]
faktor_waktu = aturan_periode[periode_hitung]["faktor"]
ket_faktor = aturan_periode[periode_hitung]["ket"]

if periode_hitung == "Harian":
    df_harga = df_raw.dropna()
else:
    df_harga = df_raw.resample(rule_terpilih).last().dropna()


# =====================================================================
# TAMPILAN SHEET & PENJELASAN DI WEB
# =====================================================================

# --- SHEET 1: DATA HARGA REAL ---
st.header(f"1️⃣ Sheet Data Harga Real-Time ({periode_hitung})")
st.dataframe(df_harga.tail(10), use_container_width=True)

with st.expander("📘 Penjelasan Perhitungan Sheet 1 (Data Harga Pasar)"):
    st.markdown(f"""
    * **Sumber Data:** Diambil secara otomatis langsung dari pasar keuangan (*Yahoo Finance API / Data BEI*).
    * **Periode Dipilih:** Menggunakan rentang **{rentang_waktu}** dengan frekuensi penarikan **{periode_hitung}** (mengambil harga penutupan terakhir pada setiap akhir periode).
    * **Keunggulan:** Data selalu akurat sesuai kondisi pasar terkini tanpa perlu memperbarui file Excel secara manual.
    """)

# --- SHEET 2: PERHITUNGAN RETURN ---
st.header(f"2️⃣ Sheet Perhitungan Return ({periode_hitung})")
df_return = df_harga.pct_change().dropna()
st.dataframe(df_return.tail(10).style.format("{:.2%}"), use_container_width=True)

with st.expander("📘 Penjelasan Perhitungan Sheet 2 (Return / Imbal Hasil)"):
    st.markdown(f"""
    * **Rumus Dasar:** $\\text{{Return}}_t = \\frac{{\\text{{Harga}}_t - \\text{{Harga}}_{{t-1}}}}{{\\text{{Harga}}_{{t-1}}}}$
    * Menunjukkan besarnya persentase kenaikan atau penurunan harga antar periode **{periode_hitung.lower()}**.
    """)

# --- SHEET 3: STATISTIK INDIVIDUAL ---
st.header("3️⃣ Sheet Statistik & Risiko Individual Saham")
mean_return = df_return.mean()
std_return = df_return.std()
var_return = df_return.var()

df_statistik = pd.DataFrame({
    f"Rata-rata Return ({periode_hitung})": mean_return,
    f"Standar Deviasi / Risiko ({periode_hitung})": std_return,
    f"Varians ({periode_hitung})": var_return,
    "Ekspektasi Return Tahunan (Disetahunkan)": mean_return * faktor_waktu,
    "Risiko Tahunan (Disetahunkan)": std_return * np.sqrt(faktor_waktu)
}, index=saham_terpilih)

st.dataframe(df_statistik.style.format("{:.4f}"), use_container_width=True)

with st.expander("📘 Penjelasan Perhitungan Sheet 3 (Statistik & Annualisasi)"):
    st.markdown(f"""
    * **Standar Deviasi:** Mengukur tingkat volatilitas/risiko saham secara statistik.
    * **Penyetaraan Tahunan (*Annualization*):** Risiko dan return dikalikan dengan faktor penyesuaian waktu **{faktor_waktu}** ({ket_faktor}) agar setara dalam skala 1 tahun penuh.
    """)

# --- SHEET 4: MATRIKS KOVARIANS ---
st.header("4️⃣ Sheet Matriks Kovarians (Covariance Matrix)")
cov_matrix = df_return.cov()
st.dataframe(cov_matrix.style.format("{:.6f}"), use_container_width=True)

with st.expander("📘 Penjelasan Perhitungan Sheet 4 (Matriks Kovarians)"):
    st.markdown("""
    * **Kovarians:** Menggambarkan arah pergerakan bersama antar emiten saham yang dipilih untuk mengukur efektivitas diversifikasi risiko portofolio.
    """)

# --- SHEET 5: EVALUASI & Keputusan ---
st.header("5️⃣ Sheet Evaluasi Portofolio & Rekomendasi Keputusan")

port_return_periode = np.sum(mean_return * weights)
port_std_periode = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

port_return_tahunan = port_return_periode * faktor_waktu
port_std_tahunan = port_std_periode * np.sqrt(faktor_waktu)
sharpe_ratio = port_return_tahunan / port_std_tahunan if port_std_tahunan != 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric(f"Expected Return (Tahunan)", f"{port_return_tahunan:.2%}")
col2.metric(f"Risiko Portofolio (Tahunan)", f"{port_std_tahunan:.2%}")
col3.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")

with st.expander("📘 Penjelasan Perhitungan Sheet 5 (Portofolio Gabungan)"):
    st.markdown("""
    * Menggabungkan ekspektasi return, bobot, dan risiko multiaset menggunakan aljabar matriks portofolio modern (Modern Portfolio Theory).
    """)

# Grafik Pergerakan Harga Ternormalisasi
st.subheader("📊 Grafik Kinerja Harga Saham Real-Time (Base = 100)")
df_norm = (df_harga / df_harga.iloc[0]) * 100
fig, ax = plt.subplots(figsize=(10, 4))
for saham in saham_terpilih:
    ax.plot(df_norm.index, df_norm[saham], label=saham.replace(".JK", ""))
ax.set_ylabel("Indeks Pertumbuhan")
ax.set_xlabel("Tanggal")
ax.legend()
ax.grid(True, linestyle="--", alpha=0.5)
st.pyplot(fig)

# --- DESKRIPSI KEPUTUSAN OTOMATIS ---
st.subheader("💡 Kesimpulan & Rekomendasi Keputusan")

if port_std_tahunan < 0.15:
    kategori_risiko = "Rendah (Konservatif) 🛡️"
    deskripsi_keputusan = (
        "**Rekomendasi Keputusan:** Layak Dipertimbangkan untuk Jangka Panjang.\n\n"
        f"**Analisis Data Pasar:** Berdasarkan data historis real-time dengan frekuensi **{periode_hitung.lower()}**, "
        f"kombinasi saham terpilih mencatatkan volatilitas tahunan sebesar **{port_std_tahunan:.2%}**. "
        "Portofolio ini cenderung stabil dan aman terhadap gejolak pasar ekstrem."
    )
elif port_std_tahunan <= 0.25:
    kategori_risiko = "Sedang (Moderat) ⚖️"
    deskripsi_keputusan = (
        "**Rekomendasi Keputusan:** Seimbang & Layak Dieksekusi.\n\n"
        f"**Analisis Data Pasar:** Berdasarkan data pasar terkini, portofolio menunjukkan keseimbangan yang sehat "
        f"antara potensi return tahunan **{port_return_tahunan:.2%}** dan risiko **{port_std_tahunan:.2%}**. "
        "Sangat ideal untuk investor dengan profil risiko menengah."
    )
else:
    kategori_risiko = "Tinggi (Agresif) 🚀"
    deskripsi_keputusan = (
        "**Rekomendasi Keputusan:** Perlu Pengawasan Ketat / Profil Agresif.\n\n"
        f"**Analisis Data Pasar:** Portofolio ini memiliki fluktuasi harga tahunan yang tinggi (**{port_std_tahunan:.2%}**). "
        "Cocok bagi investor agresif yang siap mengambil risiko tinggi demi memburu potensi keuntungan maksimal."
    )

st.info(f"**Profil Risiko Pasar:** {kategori_risiko}")
st.markdown(deskripsi_keputusan)

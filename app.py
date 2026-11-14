import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="DSS Portofolio Saham Syariah (JII)", layout="wide")
st.title("🕌 Sistem Pendukung Keputusan (DSS) Portofolio Saham Syariah (JII)")
st.markdown(
    "Aplikasi analisis risiko, *return*, dan optimasi portofolio saham syariah berdasarkan "
    "konstituen **Jakarta Islamic Index (JII)** di Bursa Efek Indonesia (BEI) secara *real-time*."
)

# --- 1. DAFTAR RESMI 30 SAHAM KONSTITUEN INDEKS JII (PERIODE JUNI - NOVEMBER 2026) ---
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

# Pilihan khusus saham JII
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
mapping_periode = {"1 Tahun": "1y", "2 Tahun": "2y", "3 Tahun": "3y", "5 Tahun": "5y"}
periode_yf = mapping_periode[rentang_waktu]

# Pilihan Frekuensi Perhitungan
periode_hitung = st.sidebar.selectbox(
    "3. Pilih Frekuensi Perhitungan:",
    options=["Harian", "Mingguan", "Bulanan", "Tahunan"]
)

# Pengaturan Bobot Portofolio
st.sidebar.subheader("4. Atur Bobot Investasi (%)")
bobot_input = []
for saham in saham_terpilih:
    nama_bersih = saham.replace(".JK", "")
    nilai = st.sidebar.slider(
        f"Bobot {nama_bersih} (%)",
        min_value=0,
        max_value=100,
        value=int(100 / len(saham_terpilih))
    )
    bobot_input.append(nilai)

total_bobot = sum(bobot_input)
if total_bobot == 0:
    st.error("Total bobot investasi tidak boleh 0%!")
    st.stop()

weights = np.array(bobot_input) / total_bobot
ringkasan_bobot = ", ".join([f"{s.replace('.JK', '')}: {w*100:.1f}%" for s, w in zip(saham_terpilih, weights)])
st.sidebar.info(f"**Komposisi Bobot (Total 100%):**\n\n{ringkasan_bobot}")


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

# Urutkan kolom sesuai urutan pilihan user
df_raw = df_raw[saham_terpilih]

# Pemetaan aturan resampling & faktor tahunan
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

# Bersihkan nama kolom untuk tampilan tabel agar lebih rapi (hapus .JK)
df_harga_display = df_harga.copy()
df_harga_display.columns = [c.replace(".JK", "") for c in df_harga_display.columns]


# =====================================================================
# TAMPILAN SHEET & PENJELASAN MENDALAM DI SETIAP PERHITUNGAN
# =====================================================================

# --- SHEET 1: DATA HARGA ---
st.header(f"1️⃣ Sheet Data Harga Penutupan Saham JII ({periode_hitung})")
st.dataframe(df_harga_display.tail(10).style.format("Rp {:,.0f}"), use_container_width=True)

with st.expander("📘 Penjelasan Detail Perhitungan Sheet 1 (Data Harga Historis)", expanded=True):
    st.markdown(f"""
    * **Cakupan Emiten:** Hanya mengambil saham syariah likuid yang masuk dalam daftar resmi **Jakarta Islamic Index (JII)**.
    * **Apa yang ditampilkan tabel ini?** Harga penutupan (*Adjusted Close Price*) resmi dalam mata uang Rupiah (Rp).
    * **Metode Pengambilan ({periode_hitung}):** 
      * Sistem menarik data historis selama **{rentang_waktu}** terakhir.
      * Karena frekuensi yang dipilih adalah **{periode_hitung}**, sistem mengambil **harga penutupan pada akhir setiap periode {periode_hitung.lower()}** (fungsi *resampling* akhir periode).
    * **Jumlah Titik Data:** Terdapat **{len(df_harga_display)} periode {periode_hitung.lower()}** yang valid untuk dianalisis.
    """)

# --- SHEET 2: RETURN ---
st.header(f"2️⃣ Sheet Perhitungan Return / Imbal Hasil ({periode_hitung})")
df_return = df_harga_display.pct_change().dropna()
st.dataframe(df_return.tail(10).style.format("{:.2%}"), use_container_width=True)

with st.expander("📘 Penjelasan Detail Perhitungan Sheet 2 (Return Saham)", expanded=True):
    saham_contoh = df_harga_display.columns[0]
    if len(df_harga_display) >= 2:
        h_lama = df_harga_display[saham_contoh].iloc[-2]
        h_baru = df_harga_display[saham_contoh].iloc[-1]
        ret_contoh = (h_baru - h_lama) / h_lama
        teks_contoh = (
            f"Pada saham **{saham_contoh}**, harga periode sebelumnya adalah **Rp {h_lama:,.0f}** "
            f"dan harga periode terakhir adalah **Rp {h_baru:,.0f}**, sehingga return-nya: "
            f"`({h_baru:,.0f} - {h_lama:,.0f}) / {h_lama:,.0f} = {ret_contoh:.2%}`."
        )
    else:
        teks_contoh = "-"

    st.markdown(f"""
    * **Tujuan Perhitungan:** Mengukur persentase kenaikan atau penurunan harga saham syariah dari satu periode ke periode berikutnya.
    * **Rumus Matematis:**
      $$R_t = \\frac{{P_t - P_{{t-1}}}}{{P_{{t-1}}}}$$
      *(Di mana $P_t$ adalah harga periode sekarang, dan $P_{{t-1}}$ adalah harga periode sebelumnya).*
    * **Padanan Rumus Excel:** `=(B3-B2)/B2`
    * **Contoh Perhitungan Langsung:** {teks_contoh}
    """)

# --- SHEET 3: STATISTIK INDIVIDUAL ---
st.header("3️⃣ Sheet Statistik & Risiko Individual Saham")
mean_return = df_return.mean()
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

with st.expander("📘 Penjelasan Detail Perhitungan Sheet 3 (Statistik & Annualisasi)", expanded=True):
    st.markdown(f"""
    Tabel ini merangkum performa dan tingkat risiko masing-masing emiten JII secara terpisah:
    1. **Mean Return ({periode_hitung}):** Rata-rata imbal hasil per {periode_hitung.lower()}. *(Rumus Excel: `=AVERAGE(...)`)*.
    2. **Varians ({periode_hitung}):** Mengukur kuadrat penyebaran data return dari nilai rata-ratanya. *(Rumus Excel: `=VAR.S(...)`)*.
    3. **Standar Deviasi / Risiko ({periode_hitung}):** Akar kuadrat dari varians. Menunjukkan seberapa besar fluktuasi naik-turunnya harga saham. *(Rumus Excel: `=STDEV.S(...)`)*.
    4. **Penyetaraan Tahunan (*Annualization*):** Agar hasil perhitungan {periode_hitung.lower()} bisa dibandingkan dalam skala 1 tahun penuh:
       * **Expected Return Tahunan** = $\\text{{Mean Return}} \\times {faktor_waktu}$ *(karena terdapat {ket_faktor})*.
       * **Risiko Tahunan** = $\\text{{Std. Deviasi}} \\times \\sqrt{{{faktor_waktu}}}$.
    """)

# --- SHEET 4: MATRIKS KOVARIANS ---
st.header("4️⃣ Sheet Matriks Kovarians (Covariance Matrix)")
cov_matrix = df_return.cov()
st.dataframe(cov_matrix.style.format("{:.6f}"), use_container_width=True)

with st.expander("📘 Penjelasan Detail Perhitungan Sheet 4 (Matriks Kovarians)", expanded=True):
    st.markdown("""
    * **Apa fungsi Matriks Kovarians?** Dalam teori portofolio modern (*Markowitz*), risiko gabungan tidak cukup dihitung dari rata-rata risiko masing-masing saham, melainkan harus memperhitungkan **keterkaitan arah gerak antar saham**.
    * **Cara Membaca Angka:**
      * **Diagonal Utama (kiri atas ke kanan bawah):** Menunjukkan nilai **Varians** dari masing-masing saham itu sendiri.
      * **Angka Positif (+):** Kedua saham cenderung bergerak searah (ketika saham A naik, saham B cenderung ikut naik).
      * **Angka Negatif (-):** Kedua saham bergerak berlawanan arah. Sangat ideal untuk **diversifikasi**, karena saat satu saham turun, saham lainnya menahan penurunan portofolio.
    * **Padanan Rumus Excel:** `=COVARIANCE.S(array1, array2)`
    """)

# --- SHEET 5: EVALUASI PORTOFOLIO ---
st.header("5️⃣ Sheet Evaluasi Portofolio Syariah Gabungan")

port_return_periode = np.sum(mean_return * weights)
port_std_periode = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

port_return_tahunan = port_return_periode * faktor_waktu
port_std_tahunan = port_std_periode * np.sqrt(faktor_waktu)
sharpe_ratio = port_return_tahunan / port_std_tahunan if port_std_tahunan != 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric(f"Expected Return ({periode_hitung} / Tahunan)", f"{port_return_periode:.2%} / {port_return_tahunan:.2%}")
col2.metric(f"Risiko Portofolio ({periode_hitung} / Tahunan)", f"{port_std_periode:.2%} / {port_std_tahunan:.2%}")
col3.metric("Sharpe Ratio (Efisiensi)", f"{sharpe_ratio:.2f}")

with st.expander("📘 Penjelasan Detail Perhitungan Sheet 5 (Rumus Portofolio Gabungan)", expanded=True):
    st.markdown(f"""
    1. **Expected Return Portofolio ($E(R_p)$):**
       * **Rumus:** $E(R_p) = \\sum (w_i \\times E(R_i))$
       * **Penjelasan:** Penjumlahan dari perkalian antara **Bobot Investasi ($w_i$)** dengan **Rata-rata Return ($E(R_i)$)** tiap saham.
       * **Hasil:** Diperoleh **{port_return_periode:.2%}** per {periode_hitung.lower()}, atau setara **{port_return_tahunan:.2%}** per tahun.

    2. **Risiko Portofolio ($\\sigma_p$):**
       * **Rumus Matriks:** $\\sigma_p = \\sqrt{{W^T \\times \\Sigma \\times W}}$
       * **Penjelasan:** Perkalian vektor bobot ($W$), Matriks Kovarians pada Sheet 4 ($\\Sigma$), dan transpose bobot ($W^T$), lalu ditarik akar kuadratnya. *(Padanan Excel: `=SQRT(MMULT(TRANSPOSE(Bobot), MMULT(Matriks_Kovarians, Bobot)))`)*.
       * **Hasil:** Risiko gabungan portofolio adalah **{port_std_periode:.2%}** per {periode_hitung.lower()}, atau **{port_std_tahunan:.2%}** per tahun.

    3. **Sharpe Ratio:**
       * **Rumus:** $\\text{{Sharpe Ratio}} = \\frac{{\\text{{Expected Return Tahunan}}}}{{\\text{{Risiko Tahunan}}}}$
       * **Penjelasan:** Mengukur efisiensi imbal hasil terhadap risiko. Nilai di atas **1.0** menunjukkan imbal hasil yang dihasilkan sangat sepadan dengan risiko yang ditanggung.
    """)

# --- GRAFIK KINERJA ---
st.subheader("📊 Visualisasi Pertumbuhan Harga Saham JII (Base = 100)")
df_norm = (df_harga_display / df_harga_display.iloc[0]) * 100
fig, ax = plt.subplots(figsize=(10, 4))
for saham in df_norm.columns:
    ax.plot(df_norm.index, df_norm[saham], label=saham, linewidth=1.8)
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
    deskripsi_keputusan = (
        "**Rekomendasi Keputusan:** Layak Dipertimbangkan untuk Investasi Syariah Jangka Panjang.\n\n"
        f"**Analisis Data Pasar:** Berdasarkan analisis frekuensi **{periode_hitung.lower()}** pada kombinasi emiten JII "
        f"(**{daftar_nama_pendek}**), portofolio ini memiliki tingkat volatilitas tahunan yang sangat terkendali sebesar **{port_std_tahunan:.2%}** "
        f"dengan potensi return tahunan **{port_return_tahunan:.2%}**. Komposisi bobot saat ini efektif meredam gejolak pasar dan cocok untuk menjaga keamanan modal."
    )
elif port_std_tahunan <= 0.25:
    kategori_risiko = "Sedang (Moderat) ⚖️"
    deskripsi_keputusan = (
        "**Rekomendasi Keputusan:** Seimbang & Layak Dieksekusi.\n\n"
        f"**Analisis Data Pasar:** Berdasarkan analisis frekuensi **{periode_hitung.lower()}** pada kombinasi emiten JII "
        f"(**{daftar_nama_pendek}**), portofolio berada pada titik keseimbangan optimal antara potensi keuntungan tahunan (**{port_return_tahunan:.2%}**) "
        f"dan tingkat risiko (**{port_std_tahunan:.2%}**). Nilai *Sharpe Ratio* sebesar **{sharpe_ratio:.2f}** menunjukkan efisiensi diversifikasi yang baik untuk profil investor moderat."
    )
else:
    kategori_risiko = "Tinggi (Agresif) 🚀"
    deskripsi_keputusan = (
        "**Rekomendasi Keputusan:** Perlu Pengawasan Ketat / Khusus Investor Agresif.\n\n"
        f"**Analisis Data Pasar:** Berdasarkan analisis frekuensi **{periode_hitung.lower()}** pada kombinasi emiten JII "
        f"(**{daftar_nama_pendek}**), portofolio ini mencatatkan fluktuasi harga tahunan yang tinggi (**{port_std_tahunan:.2%}**). "
        "Meskipun menawarkan peluang *return* yang besar, keputusan investasi ini hanya disarankan bagi investor yang siap menghadapi volatilitas pasar jangka pendek."
    )

st.info(f"**Profil Risiko Portofolio JII:** {kategori_risiko}")
st.markdown(deskripsi_keputusan)

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
    "Aplikasi analisis portofolio syariah lengkap dengan **rumus, angka, penjelasan rinci, dan kesimpulan** "
    "di setiap 6 Sheet dengan pengaturan bobot desimal spesifik."
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

# --- 2. SIDEBAR: SUMBER DATA & PENGATURAN ---
st.sidebar.header("⚙️ Pengaturan & Sumber Data")

sumber_data = st.sidebar.radio(
    "Pilih Sumber Data:",
    options=["Otomatis (Yahoo Finance)", "Upload File Sendiri (Excel/CSV)"]
)

df_harga_display = None

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
            st.stop()
    else:
        st.info("👈 Silakan unggah file Excel/CSV Anda melalui panel di sebelah kiri.")
        st.stop()

else:
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

    periode_hitung = st.sidebar.selectbox(
        "3. Pilih Frekuensi Perhitungan:",
        options=["Mingguan", "Harian", "Bulanan", "Semester (6 Bulan)", "Tahunan"]
    )

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

if sumber_data == "Upload File Sendiri (Excel/CSV)":
    periode_hitung = "Periode Upload"
    faktor_waktu = 52
    label_faktor_teks = "52 minggu (standar)"

saham_terpilih_list = list(df_harga_display.columns)

df_return = df_harga_display.pct_change().fillna(0)
df_return_stats = df_harga_display.pct_change().dropna()
if df_return_stats.empty:
    df_return_stats = df_return

mean_return_stats = df_return_stats.mean()
cov_matrix_stats = df_return_stats.cov()
std_stats = df_return_stats.std()

# --- SIDEBAR: BOBOT DESIMAL & PARAMETER KINERJA ---
st.sidebar.subheader("⚖️ Atur Bobot Investasi (%)")
mode_bobot = st.sidebar.radio(
    "Metode Penentuan Bobot:",
    options=["Manual (Desimal spesifik)", "Bobot Berimbang (Equal Weight)"]
)

bobot_input = []
jumlah_saham = len(saham_terpilih_list)
default_bobot_satuan = round(100.0 / jumlah_saham, 4)

for saham in saham_terpilih_list:
    if mode_bobot == "Bobot Berimbang (Equal Weight)":
        val = default_bobot_satuan
    else:
        val = default_bobot_satuan
    
    # Menggunakan number_input agar bisa spesifik sampai belakang koma (format %.4f)
    nilai = st.sidebar.number_input(
        f"Bobot {saham} (%)", 
        min_value=0.0, 
        max_value=100.0, 
        value=val, 
        step=0.01, 
        format="%.4f"
    )
    bobot_input.append(nilai)

total_bobot = sum(bobot_input)
if abs(total_bobot - 100.0) > 0.001:
    st.sidebar.warning(f"⚠️ Total bobot saat ini: **{total_bobot:.4f}%**. Disarankan total bobot pas 100.00%.")

if total_bobot == 0:
    total_bobot = 1.0
weights = np.array(bobot_input) / total_bobot

st.sidebar.subheader("📈 Parameter Kinerja (Benchmark & Rf)")
risk_free_rate = st.sidebar.number_input("Bunga Bebas Risiko (Rf - Tahunan)", value=0.06, step=0.001, format="%.4f")
market_return = st.sidebar.number_input("Expected Return Pasar (Rm - Tahunan)", value=0.10, step=0.001, format="%.4f")

WARNA_PASTEL = ["#B08968", "#D4A373", "#CCD5AE", "#99582A", "#6F4E37", "#BC6C25", "#E6CCB2"]


# =====================================================================
# 6 SHEET ANALISIS PORTOFOLIO SYARIAH
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
        "* **Rumus / Sumber Data:** Harga Penutupan (Close Price) pada periode t\n"
        "* **Penjelasan Angka:** Tabel menampilkan histori harga saham emiten pilihan dalam Rupiah.\n"
        "* **Kesimpulan Sheet 1:** Data harga mentah ini berfungsi sebagai pondasi utama seluruh perhitungan return dan risiko."
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
        "* **Penjelasan Angka:** Menunjukkan persentase keuntungan/kerugian dan nilai rata-rata return historis.\n"
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
        f"* **Rumus Varians:** Varians = Jumlah Kuadrat Selisih Return dari Mean / (n - 1)\n"
        f"* **Rumus Standar Deviasi:** Standar Deviasi = Akar Kuadrat dari Varians\n"
        f"* **Penjelasan Angka:** Mengukur tingkat volatilitas (risiko). Disesuaikan dengan faktor waktu **{label_faktor_teks}**.\n"
        f"* **Kesimpulan Sheet 3:** Semakin kecil standar deviasi, semakin stabil dan rendah risiko saham tersebut."
    )

# --- SHEET 4: COVARIANCE ---
st.header("4️⃣ Sheet 4: Kovarians (Covariance Matrix)")
st.dataframe(cov_matrix_stats.style.format("{:.6f}"), use_container_width=True)

with st.expander("📖 Panduan, Rumus & Kesimpulan - Sheet 4 (Covariance)", expanded=True):
    st.markdown(
        "* **Rumus Kovarians:** Mengukur arah pergerakan bersama antar dua variabel saham.\n"
        "* **Penjelasan Angka:** Menunjukkan keeratan arah fluktuasi antar emiten.\n"
        "* **Kesimpulan Sheet 4:** Kovarians negatif sangat baik untuk diversifikasi karena dapat meredam risiko portofolio."
    )

# --- SHEET 5: KOEFISIEN KORELASI ---
st.header("5️⃣ Sheet 5: Koefisien Korelasi")
corr_matrix = df_return_stats.corr()
st.dataframe(corr_matrix.style.format("{:.6f}"), use_container_width=True)

with st.expander("📖 Panduan, Rumus & Kesimpulan - Sheet 5 (Koefisien Korelasi)", expanded=True):
    st.markdown(
        "* **Rumus Koefisien Korelasi (r):** r = Cov(A,B) / (SD_A * SD_B)\n"
        "* **Penjelasan Angka:** Nilai berkisar dari -1 hingga +1.\n"
        "* **Kesimpulan Sheet 5:** Pilih emiten dengan korelasi rendah atau negatif untuk diversifikasi optimal."
    )

# --- SHEET 6: RETURN PORTOFOLIO & KINERJA ---
st.header("6️⃣ Sheet 6: Return Portofolio, Risiko, & Metrik Kinerja (Sharpe, Treynor, Alpha)")

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
        f"* **Rumus Expected Return Portofolio:** E(Rp) = Sum(Bobot * ER)\n"
        f"* **Rumus Sharpe Ratio:** Sharpe = (Return Portofolio - Rf) / Risiko Portofolio = **{sharpe_ratio:.4f}**\n"
        f"* **Rumus Treynor Ratio:** Treynor = (Return Portofolio - Rf) / Beta Portofolio = **{treynor_ratio:.4f}**\n"
        f"* **Rumus Jensen's Alpha:** Alpha = Return Portofolio - [Rf + Beta * (Rm - Rf)] = **{jensen_alpha:.4f}**\n\n"
        f"**Kesimpulan Keseluruhan Portofolio:**\n"
        f"* Portofolio Anda menghasilkan Expected Return sebesar **{port_return_skala:.2%}** dengan tingkat risiko **{port_std_skala:.2%}**.\n"
        f"* Nilai Sharpe & Treynor Ratio mencerminkan efisiensi keuntungan portofolio terhadap risiko yang diambil.\n"
        f"* Nilai Jensen's Alpha positif menunjukkan portofolio berhasil mengungguli return pasar (outperform)."
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

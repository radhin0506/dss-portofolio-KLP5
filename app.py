import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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
    "Aplikasi analisis portofolio syariah berdasarkan data historis **TradingView** "
    "untuk konstituen JII (**BRIS, CTRA, TLKM**)."
)

# --- MEMBACA FILE EXCEL TRADINGVIEW OTOMATIS DARI SERVER ---
@st.cache_data
def load_data_tradingview():
    file_path = "Data_Harga_Close_Mingguan_BRIS_CTRA_TLKM.xlsx"
    df_close = pd.read_excel(file_path, sheet_name="Harga Close Mingguan")
    return df_close

try:
    df_harga_raw = load_data_tradingview()
except Exception as e:
    st.error(f"⚠️ File Excel tidak ditemukan di folder project. Pastikan file 'Data_Harga_Close_Mingguan_BRIS_CTRA_TLKM.xlsx' sudah diunggah ke repository GitHub Anda. Detail: {e}")
    st.stop()

# Memastikan kolom tanggal terdeteksi dengan benar
if "Tanggal" in df_harga_raw.columns:
    df_harga_raw["Tanggal"] = pd.to_datetime(df_harga_raw["Tanggal"])
    df_harga_raw = df_harga_raw.set_index("Tanggal")

df_harga_display = df_harga_raw.copy()
df_harga_display.columns = [c.replace("Close ", "").replace(".JK", "").strip() for c in df_harga_display.columns]

saham_terpilih = list(df_harga_display.columns)

# --- SIDEBAR: PENGATURAN WAKTU & BOBOT ---
st.sidebar.header("⚙️ Pengaturan Portofolio")

periode_hitung = st.sidebar.selectbox(
    "1. Pilih Frekuensi Perhitungan:",
    options=["Mingguan", "Harian", "Bulanan", "Semester (6 Bulan)", "Tahunan"]
)

aturan_periode = {
    "Harian": {"faktor": 252, "label_faktor": "252 hari bursa"},
    "Mingguan": {"faktor": 52, "label_faktor": "52 minggu"},
    "Bulanan": {"faktor": 12, "label_faktor": "12 bulan"},
    "Semester (6 Bulan)": {"faktor": 2, "label_faktor": "2 semester (faktor 2)"},
    "Tahunan": {"faktor": 1, "label_faktor": "1 tahun"}
}

faktor_waktu = aturan_periode[periode_hitung]["faktor"]
label_faktor_teks = aturan_periode[periode_hitung]["label_faktor"]

# Return & Statistik berdasarkan data TradingView
df_return = df_harga_display.pct_change().fillna(0)
df_return_stats = df_harga_display.pct_change().dropna()
if df_return_stats.empty:
    df_return_stats = df_return

mean_return_stats = df_return_stats.mean()
cov_matrix_stats = df_return_stats.cov()
std_stats = df_return_stats.std()

st.sidebar.subheader("2. Atur Bobot Investasi (%)")
mode_bobot = st.sidebar.radio(
    "Metode Penentuan Bobot:",
    options=["Manual (Slider)", "Bobot Berimbang (Equal Weight)"]
)

bobot_input = []
for saham in saham_terpilih:
    val_default = int(round(100 / len(saham_terpilih)))
    if mode_bobot == "Bobot Berimbang (Equal Weight)":
        val_default = int(round(100 / len(saham_terpilih)))
    nilai = st.sidebar.slider(f"Bobot {saham} (%)", min_value=0, max_value=100, value=val_default)
    bobot_input.append(nilai)

total_bobot = sum(bobot_input)
if total_bobot == 0:
    total_bobot = 1
weights = np.array(bobot_input) / total_bobot

st.sidebar.subheader("3. Parameter Kinerja (Benchmark & Rf)")
risk_free_rate = st.sidebar.number_input("Bunga Bebas Risiko (Rf - Tahunan)", value=0.06, step=0.005, format="%.3f")
market_return = st.sidebar.number_input("Expected Return Pasar (Rm - Tahunan)", value=0.10, step=0.005, format="%.3f")

WARNA_PASTEL = ["#B08968", "#D4A373", "#CCD5AE", "#99582A", "#6F4E37", "#BC6C25", "#E6CCB2"]


# =====================================================================
# STRUKTUR 6 SHEET SESUAI FORMAT EXCEL ANDA
# =====================================================================

# --- SHEET 1: HARGA CLOSE ---
st.header(f"1️⃣ Sheet 1: Harga Close {periode_hitung} (TradingView)")
df_sheet1 = df_harga_display.reset_index()
df_sheet1.insert(0, "No", range(1, len(df_sheet1) + 1))
st.dataframe(df_sheet1.style.format({"No": "{:.0f}", **{c: "Rp {:,.0f}" for c in saham_terpilih}}), use_container_width=True)

with st.expander("💡 Penjelasan Sederhana - Sheet 1 (Data Harga Close)", expanded=True):
    st.markdown("""
    * **Isi Sheet:** Menampilkan data harga penutupan (*Close*) murni dari file TradingView Anda.
    """)

# --- SHEET 2: RETURN REALISASI & ER ---
st.header(f"2️⃣ Sheet 2: Return Realisasi & ER ({periode_hitung})")
df_sheet2 = df_return.copy().reset_index(drop=True)
df_sheet2.insert(0, "No", range(1, len(df_sheet2) + 1))
st.dataframe(df_sheet2.style.format({"No": "{:.0f}", **{c: "{:.6f}" for c in saham_terpilih}}), use_container_width=True)

st.markdown("**Expected Return (ER) Masing-masing Emiten (Rata-rata Return):**")
st.json({col: f"{val:.6f}" for col, val in mean_return_stats.items()})

with st.expander("💡 Penjelasan Sederhana - Sheet 2 (Return Realisasi & ER)", expanded=True):
    st.markdown("""
    * **Isi Sheet:** Menghitung persentase perubahan harga dari periode sebelumnya ke periode berjalan, ditutup dengan nilai rata-rata Expected Return (ER).
    """)

# --- SHEET 3: VARIANS & STANDAR DEVIASI ---
st.header("3️⃣ Sheet 3: Varians & Standar Deviasi")
df_sheet3 = pd.DataFrame({
    "Emiten": saham_terpilih,
    f"Mean Return ({periode_hitung})": mean_return_stats.values,
    "Variance": df_return_stats.var().values,
    "Standar Deviasi (Risiko)": std_stats.values,
    f"Expected Return (Skala Waktu)": mean_return_stats.values * faktor_waktu,
    f"Risiko (Skala Waktu)": std_stats.values * np.sqrt(faktor_waktu)
})
kolom_angka_sheet3 = [f"Mean Return ({periode_hitung})", "Variance", "Standar Deviasi (Risiko)", "Expected Return (Skala Waktu)", "Risiko (Skala Waktu)"]
st.dataframe(df_sheet3.style.format({col: "{:.6f}" for col in kolom_angka_sheet3}), use_container_width=True)

with st.expander("💡 Penjelasan Sederhana - Sheet 3 (Varians & Standar Deviasi)", expanded=True):
    st.markdown(f"""
    * **Varians & Standar Deviasi:** Mengukur tingkat risiko fluktuasi harga saham berdasarkan data TradingView, disesuaikan dengan faktor waktu (**{label_faktor_teks}**).
    """)

# --- SHEET 4: COVARIANCE ---
st.header("4️⃣ Sheet 4: Kovarians (Covariance Matrix)")
st.dataframe(cov_matrix_stats.style.format("{:.6f}"), use_container_width=True)

with st.expander("💡 Penjelasan Sederhana - Sheet 4 (Covariance)", expanded=True):
    st.markdown("""
    * **Isi Sheet:** Matriks kovarians antar emiten untuk melihat arah pergerakan bersama.
    """)

# --- SHEET 5: KOEFISIEN KORELASI ---
st.header("5️⃣ Sheet 5: Koefisien Korelasi")
corr_matrix = df_return_stats.corr()
st.dataframe(corr_matrix.style.format("{:.6f}"), use_container_width=True)

with st.expander("💡 Penjelasan Sederhana - Sheet 5 (Koefisien Korelasi)", expanded=True):
    st.markdown("""
    * **Isi Sheet:** Koefisien korelasi antar emiten (skala -1 s.d. +1) untuk analisis diversifikasi portofolio.
    """)

# --- SHEET 6: RETURN PORTOFOLIO & KINERJA (SHARPE, TREYNOR, ALPHA JENSEN) ---
st.header("6️⃣ Sheet 6: Return Portofolio, Risiko, & Metrik Kinerja (Sharpe, Treynor, Alpha)")

port_return_periode = np.sum(mean_return_stats * weights)
port_std_periode = np.sqrt(np.dot(weights.T, np.dot(cov_matrix_stats, weights)))

port_return_skala = port_return_periode * faktor_waktu
port_std_skala = port_std_periode * np.sqrt(faktor_waktu)

# Perhitungan Beta Portofolio menggunakan Market Proxy
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

# Tabel Ringkasan Bobot Portofolio
df_port_summary = pd.DataFrame({
    "Emiten": saham_terpilih,
    "Bobot (%)": [w * 100 for w in weights],
    "Expected Return": mean_return_stats.values,
    "Kontribusi Return": (mean_return_stats.values * weights)
})
st.dataframe(df_port_summary.style.format({"Bobot (%)": "{:.2f}%", "Expected Return": "{:.6f}", "Kontribusi Return": "{:.6f}"}), use_container_width=True)

with st.expander("💡 Penjelasan & Cara Hitung - Sheet 6 (Portofolio & Metrik Kinerja)", expanded=True):
    st.markdown(f"""
    * **Expected Return Portofolio:** Hasil perkalian bobot investasi dengan Expected Return masing-masing emiten.
    * **Sharpe Ratio ({sharpe_ratio:.4f}):** Efisiensi tingkat keuntungan terhadap total risiko portofolio.
    * **Treynor Ratio ({treynor_ratio:.4f}):** Keuntungan portofolio per unit risiko sistematis (**Beta**).
    * **Alpha Jensen's ({jensen_alpha:.4f}):** Indikator keunggulan portofolio di atas tingkat wajar pasar (CAPM).
    """)

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

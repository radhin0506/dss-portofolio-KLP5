import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="DSS Portofolio Saham Syariah (JII)", layout="wide")

# --- TAG HTML VERIFIKASI GOOGLE SEARCH CONSOLE ---
st.markdown(
    '<meta name="google-site-verification" content="MASUKKAN_KODE_UNIK_DARI_GOOGLE_DISINI" />', 
    unsafe_allow_html=True
)

# --- DAFTAR SAHAM JII + CTRA ---
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
    "EXCL.JK": "EXCL - XLSMART Telecom Sejahtera Tbk.",
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

# --- KUSTOMISASI CSS WARNA PASTEL ---
bg_utama = "#F8C4B4"      # Background Utama: Pastel Peach
bg_sidebar = "#BAED91"    # Sidebar: Pastel Hijau
bg_aksen = "#D1C4E9"      # Aksen / Expander: Pastel Ungu
border_aksen = "#B39DDB"

st.markdown(f"""
<style>
    :root {{
        --background-color: {bg_utama} !important;
        --secondary-background-color: {bg_sidebar} !important;
        --text-color: #2C2C2C !important;
    }}
    .stApp, [data-testid="stAppViewContainer"], section.main {{
        background-color: {bg_utama} !important;
        color: #2C2C2C !important;
    }}
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
        background-color: {bg_sidebar} !important;
    }}
    h1, h2, h3, h4, h5, h6, p, span, label, div {{
        color: #2C2C2C !important;
    }}
    .streamlit-expanderHeader {{
        background-color: {bg_aksen} !important;
        color: #2C2C2C !important;
        border: 1px solid {border_aksen} !important;
        border-radius: 8px;
    }}
    [data-testid="stAlert"] {{
        background-color: {bg_aksen} !important;
        border: 1px solid {border_aksen} !important;
        border-radius: 10px;
    }}
</style>
""", unsafe_allow_html=True)

st.title("🎯 Sistem Pendukung Keputusan (DSS) Portofolio Saham Syariah")
st.markdown("### Analisis Portofolio Berbasis Konstituen JII dengan Fitur Utama Pilihan Anda")

# --- SIDEBAR: NAVIGASI & 2 FITUR SUMBER DATA ---
st.sidebar.header("🧭 Navigasi & Sumber Data")
menu_pilihan = st.sidebar.radio(
    "Pilih Halaman:",
    options=["🏠 Beranda (Home)", "📊 Analisis & Keputusan DSS"]
)

df_harga_display = None
periode_hitung = "Mingguan"

if menu_pilihan == "📊 Analisis & Keputusan DSS":
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Pilih Fitur Sumber Data")
    
    # Menampilkan 2 Fitur Sumber Data Pilihan
    sumber_data = st.sidebar.radio(
        "Sumber Data:",
        options=[
            "1️⃣ Fitur: Data Otomatis (Yahoo Finance)", 
            "2️⃣ Fitur: Data Upload File Sendiri (Excel/CSV)"
        ]
    )

    if sumber_data == "2️⃣ Fitur: Data Upload File Sendiri (Excel/CSV)":
        uploaded_file = st.sidebar.file_uploader("Unggah file data harga Close (.xlsx / .csv):", type=["xlsx", "csv"])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_clean = pd.read_csv(uploaded_file, encoding='utf-8', on_bad_lines='skip')
                else:
                    df_clean = pd.read_excel(uploaded_file)
                
                df_clean.columns = [str(c).strip() for c in df_clean.columns]
                df_clean.index = pd.to_datetime(df_clean.iloc[:, 0], errors='coerce')
                df_harga_display = df_clean.iloc[:, 1:].dropna(how='all')
                st.sidebar.success("✅ File berhasil dimuat!")
            except Exception as e:
                st.sidebar.error(f"Gagal memproses file: {e}")
        else:
            st.sidebar.info("👈 Silakan unggah file Anda.")
    else:
        saham_terpilih = st.sidebar.multiselect(
            "Pilih Saham Konstituen JII (Min. 2):",
            options=list(DAFTAR_SAHAM_JII.keys()),
            default=["BRIS.JK", "CTRA.JK", "TLKM.JK"],
            format_func=lambda x: DAFTAR_SAHAM_JII[x]
        )
        periode_hitung = st.sidebar.selectbox("Frekuensi Perhitungan:", options=["Mingguan", "Harian", "Bulanan", "Tahunan"])
        
        if len(saham_terpilih) >= 2:
            @st.cache_data(ttl=3600)
            def ambil_data(tickers):
                df_d = yf.download(tickers, period="2y", progress=False)
                data = df_d["Close"] if isinstance(df_d.columns, pd.MultiIndex) else df_d[["Close"]]
                return data.dropna()
            
            with st.spinner("Mengambil data Yahoo Finance..."):
                df_raw = ambil_data(saham_terpilih)
            
            df_raw = df_raw[saham_terpilih]
            rule_map = {"Harian": "D", "Mingguan": "W-FRI", "Bulanan": "ME", "Tahunan": "YE"}
            df_harga_display = df_raw.resample(rule_map.get(periode_hitung, "W-FRI")).last().dropna()
            df_harga_display.columns = [c.replace(".JK", "") for c in df_harga_display.columns]

# =====================================================================
# TAMPILAN HALAMAN UTAMA
# =====================================================================

if menu_pilihan == "🏠 Beranda (Home)":
    st.title("🕌 Selamat Datang di Aplikasi DSS Portofolio Saham Syariah")
    st.info("💡 Aplikasi ini dirancang dengan 3 fitur utama: Pengambilan data Yahoo Finance, Upload file mandiri, serta Dashboard Keputusan DSS otomatis berdasarkan hasil hitung Excel.")
    st.success("👉 Silakan buka menu di sidebar kiri untuk mulai menggunakan aplikasi!")

else:
    if df_harga_display is None or df_harga_display.empty:
        st.warning("⚠️ Silakan lengkapi pemilihan saham atau unggah file di menu sidebar sebelah kiri.")
        st.stop()

    saham_terpilih_list = list(df_harga_display.columns)
    
    # --- FITUR 3: DASHBOARD INPUT HASIL AKHIR & SARAN KEPUTUSAN DSS ---
    st.sidebar.markdown("---")
    st.sidebar.header("3️⃣ Fitur: Input Hasil Excel (Sheet 1 - 6)")
    st.sidebar.markdown("Masukkan nilai akhir dari Excel Anda untuk menghasilkan saran keputusan otomatis:")
    
    input_er_porto = st.sidebar.number_input("Expected Return Portofolio:", value=0.0254, step=0.0001, format="%.6f")
    input_var_porto = st.sidebar.number_input("Variance Portofolio (Sheet 3/6):", value=0.0012, step=0.0001, format="%.6f")
    input_sd_porto = st.sidebar.number_input("Standar Deviasi / Risiko Portofolio:", value=0.0346, step=0.0001, format="%.6f")
    input_beta_porto = st.sidebar.number_input("Beta Portofolio:", value=1.0250, step=0.001, format="%.4f")
    
    input_rf = st.sidebar.number_input("Bunga Bebas Risiko (Rf):", value=0.0010, step=0.0001, format="%.4f")
    input_sharpe = st.sidebar.number_input("Sharpe Ratio:", value=0.7050, step=0.0001, format="%.4f")
    input_treynor = st.sidebar.number_input("Treynor Ratio:", value=0.0238, step=0.0001, format="%.4f")
    input_alpha = st.sidebar.number_input("Jensen's Alpha:", value=0.0045, step=0.0001, format="%.6f")
    
    nama_saham_utama = st.sidebar.text_input("Saham Unggulan / Dominan:", value=saham_terpilih_list[0])
    bobot_saham_utama = st.sidebar.number_input("Bobot Saham Utama (%):", value=50.0, step=0.1, format="%.2f")

    # Tampilan Sheet 1 (Harga Close dengan format Rupiah)
    st.header(f"1️⃣ Sheet 1: Harga Close ({periode_hitung})")
    df_sheet1 = df_harga_display.reset_index()
    df_sheet1.rename(columns={df_sheet1.columns[0]: 'Periode/Tanggal'}, inplace=True)
    df_sheet1.insert(0, "No", range(1, len(df_sheet1) + 1))
    st.dataframe(df_sheet1.style.format({"No": "{:.0f}", **{c: "Rp {:,.2f}" for c in saham_terpilih_list}}), use_container_width=True)

    # Dashboard Saran & Keputusan DSS Otomatis di Bagian Bawah
    st.markdown("---")
    st.subheader("🎯 3️⃣ Fitur: Saran & Rekomendasi Keputusan Akhir (DSS)")

    if input_er_porto > input_rf and input_sharpe > 0.1 and input_alpha > 0:
        status_keputusan = "SANGAT DIREKOMENDASIKAN (LAYAK & OPTIMAL)"
        saran_tindakan = "Berdasarkan hasil perhitungan Excel Anda, portofolio ini terbukti mampu mengalahkan instrumen bebas risiko (Rf) sekaligus mencetak alpha positif dengan efisiensi risiko yang sangat baik."
    elif input_er_porto > input_rf:
        status_keputusan = "DIREKOMENDASIKAN (LAYAK DENGAN CATATAN)"
        saran_tindakan = "Portofolio menghasilkan imbal hasil di atas bunga bebas risiko (Rf), namun efisiensi atau tingkat risikonya masih perlu dioptimalkan kembali."
    else:
        status_keputusan = "TIDAK DIREKOMENDASIKAN (PERLU REBALANCING)"
        saran_tindakan = "Imbal hasil portofolio belum mampu mengimbangi tingkat risiko maupun instrumen bebas risiko (Rf). Disarankan melakukan penyesuaian bobot aset."

    if input_beta_porto > 1.05:
        profil_beta = f"Agresif (Beta = {input_beta_porto:.4f} > 1): Portofolio lebih sensitif dan volatil dibanding pergerakan pasar."
    elif input_beta_porto < 0.95:
        profil_beta = f"Defensif (Beta = {input_beta_porto:.4f} < 1): Portofolio lebih stabil dan tahan terhadap gejolak pasar."
    else:
        profil_beta = f"Netral / Sejalan Pasar (Beta = {input_beta_porto:.4f} ≈ 1): Pergerakan portofolio sejalan dengan kondisi pasar."

    if input_alpha > 0:
        status_alpha = f"Outperform (+{input_alpha:.6f}): Portofolio berhasil mencetak kelebihan keuntungan di atas ekspektasi model pasar (CAPM)."
    else:
        status_alpha = f"Underperform ({input_alpha:.6f}): Kinerja portofolio berada di bawah ekspektasi return pasar."

    st.success(f"**Keputusan Sistem:** **{status_keputusan}**\n\n{saran_tindakan}")

    st.markdown(
        f"**Rincian Analisis Pendukung:**\n"
        f"* **Alokasi Aset Utama:** Saham **{nama_saham_utama}** menjadi penopang utama dengan porsi sebesar **{bobot_saham_utama:.2f}%**.\n"
        f"* **Uji Kelayakan Return ($R_f$):** Expected Return (**{input_er_porto:.2%}**) {'berada di atas' if input_er_porto > input_rf else 'di bawah'} suku bunga bebas risiko ($R_f$ = **{input_rf:.4f}**).\n"
        f"* **Evaluasi Kinerja (CAPM):** {status_alpha}\n"
        f"* **Karakteristik Risiko:** {profil_beta}"
    )

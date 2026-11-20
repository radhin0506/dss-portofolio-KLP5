import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="DSS Portofolio Saham - Sheet 6", layout="wide")
st.title("📐 Rumus & Perhitungan Sheet 6: RETURN PORTOFOLIO")

# --- 1. INPUT DATA / PARAMETER ---
file_path = "Data_Harga_Close_Mingguan_BRIS_CTRA_TLKM.xlsx"
df_harga = pd.read_excel(file_path, sheet_name="Harga Close Mingguan")
df_harga.columns = ["Tanggal", "BRIS", "CTRA", "TLKM"]

returns = df_harga[["BRIS", "CTRA", "TLKM"]].pct_change().dropna()
er = returns.mean()
sd = returns.std(ddof=1)
corr = returns.corr()

# --- 2. SLIDER BOBOT PORTOFOLIO (WHAT-IF) ---
st.sidebar.header("Pengaturan Bobot Portofolio")
w_a = st.sidebar.slider("Bobot BRIS (wA) %", 0, 100, 35) / 100
w_b = st.sidebar.slider("Bobot CTRA (wB) %", 0, 100, 35) / 100
w_c = st.sidebar.slider("Bobot TLKM (wC) %", 0, 100, 30) / 100

if round(w_a + w_b + w_c, 4) != 1.0:
    st.error(f"⚠️ Total bobot saat ini {(w_a + w_b + w_c)*100:.0f}%. Atur agar totalnya tepat 100%.")
    st.stop()

# --- 3. PERHITUNGAN EXPECTED RETURN, VARIANS & STANDAR DEVIASI ---
er_a, er_b, er_c = er["BRIS"], er["CTRA"], er["TLKM"]
sd_a, sd_b, sd_c = sd["BRIS"], sd["CTRA"], sd["TLKM"]
r_ab = corr.loc["BRIS", "CTRA"]
r_ac = corr.loc["BRIS", "TLKM"]
r_bc = corr.loc["CTRA", "TLKM"]

# Kontribusi Expected Return per saham
c_a = w_a * er_a
c_b = w_b * er_b
c_c = w_c * er_c
er_port = c_a + c_b + c_c

# Varians Portofolio (Rumus 3 aset yang benar)
var_port_benar = (
    (w_a**2) * (sd_a**2)
    + (w_b**2) * (sd_b**2)
    + (w_c**2) * (sd_c**2)
    + 2 * w_a * w_b * sd_a * sd_b * r_ab
    + 2 * w_a * w_c * sd_a * sd_c * r_ac
    + 2 * w_b * w_c * sd_b * sd_c * r_bc
)
sd_port_benar = np.sqrt(var_port_benar)

# Varians Portofolio (Rumus asli di sel A10 Excel Anda yang mengalikan 3 saham sekaligus)
var_port_excel_lama = (
    (w_a**2) * (sd_a**2)
    + (w_b**2) * (sd_b**2)
    + (w_c**2) * (sd_c**2)
    + 2 * (w_a * w_b * w_c * sd_a * sd_b * sd_c * r_ab * r_ac * r_bc)
)
sd_port_excel_lama = np.sqrt(var_port_excel_lama)

# --- 4. TAMPILAN RUMUS & HASIL DI WEB ---
st.subheader("A. Expected Return Portofolio")
st.latex(r"E(R_p) = (w_A \cdot E(R_A)) + (w_B \cdot E(R_B)) + (w_C \cdot E(R_C))")
st.code("Sel E7 di Excel: =SUM(A7:C7)   |   A7: =B1*D1, B7: =D2*B2, C7: =D3*B3", language="excel")

tabel_er = pd.DataFrame({
    "Saham": ["BRIS (A)", "CTRA (B)", "TLKM (C)", "Total Portofolio"],
    "Bobot (w)": [f"{w_a*100:.0f}%", f"{w_b*100:.0f}%", f"{w_c*100:.0f}%", f"{(w_a+w_b+w_c)*100:.0f}%"],
    "Expected Return E(R)": [f"{er_a:.6f}", f"{er_b:.6f}", f"{er_c:.6f}", "-"],
    "Kontribusi (w * E(R))": [f"{c_a:.6f}", f"{c_b:.6f}", f"{c_c:.6f}", f"{er_port:.6f} ({er_port*100:.2f}%)"]
})
st.dataframe(tabel_er, use_container_width=True)

st.divider()

st.subheader("B. Varians & Standar Deviasi Portofolio (3 Aset)")
st.latex(
    r"\sigma_p^2 = w_A^2\sigma_A^2 + w_B^2\sigma_B^2 + w_C^2\sigma_C^2 "
    r"+ 2w_Aw_B\sigma_A\sigma_B r_{AB} + 2w_Aw_C\sigma_A\sigma_C r_{AC} + 2w_Bw_C\sigma_B\sigma_C r_{BC}"
)
st.code(
    "Rumus Excel Koreksi (Sel A10): =((B1^2)*(F1^2))+((B2^2)*(F2^2))+((B3^2)*(F3^2))+(2*B1*B2*F1*F2*'KOEFISIEN KORELASI'!E13)+(2*B1*B3*F1*F3*'KOEFISIEN KORELASI'!J13)+(2*B2*B3*F2*F3*'KOEFISIEN KORELASI'!E24)",
    language="excel"
)
st.latex(r"\sigma_p = \sqrt{\sigma_p^2} \quad \text{(di Excel sel A13: =SQRT(A10))}")

kol1, kol2, kol3 = st.columns(3)
kol1.metric("Expected Return Portofolio", f"{er_port*100:.2f}%", f"{er_port:.6f}")
kol2.metric("Varians Portofolio (Benar)", f"{var_port_benar:.6f}", f"Lama di Excel: {var_port_excel_lama:.6f}")
kol3.metric("Standar Deviasi Portofolio (Benar)", f"{sd_port_benar*100:.2f}%", f"Lama di Excel: {sd_port_excel_lama*100:.2f}%")

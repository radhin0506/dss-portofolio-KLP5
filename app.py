import streamlit as st
import pandas as pd

st.sidebar.header("📁 Upload Data TradingView")
uploaded_file = st.sidebar.file_uploader("Unggah file Excel/CSV dari TradingView", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Membaca file yang di-upload
    if uploaded_file.name.endswith('.csv'):
        df_raw = pd.read_csv(uploaded_file)
    else:
        df_raw = pd.read_excel(uploaded_file)
    
    st.success("Data TradingView berhasil dimuat!")
    st.write(df_raw.head())
else:
    st.info("Silakan unggah file Excel/CSV dari TradingView melalui sidebar sebelah kiri.")
    st.stop()

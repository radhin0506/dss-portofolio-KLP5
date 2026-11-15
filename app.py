import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="DSS Portofolio Saham Syariah (JII)", layout="wide")

# --- KUSTOMISASI CSS WARNA PASTEL COKLAT MUTLAK (MEMAKSA BACKGROUND BERUBAH) ---
st.markdown("""
<style>
    /* 1. Paksa Background Utama Aplikasi Menjadi Krem Pastel Coklat */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #FDFBF7 !important;
        color: #4A3B32 !important;
    }
    
    /* 2. Paksa Background Sidebar Menjadi Coklat Susu Latte Pastel */
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background-color: #F4ECE1 !important;
    }
    
    /* 3. Paksa Warna Teks Seluruh Judul, Paragraf, dan Label Menjadi Coklat Tua */
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #4A3B32 !important;
    }
    
    /* 4. Paksa Kotak Expander / Penjelasan Menjadi Senada */
    .streamlit-expanderHeader {
        background-color: #EFE6D8 !important;
        color: #4A3B32 !important;
        border-radius: 8px;
    }
    
    /* 5. Paksa Tombol & Widget Input */
    .stButton>button {
        background-color: #B08968 !important;
        color: white !important;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# (Lanjutkan sisa kode aplikasi Anda di bawah sini...)

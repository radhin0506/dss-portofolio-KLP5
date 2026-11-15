# --- KUSTOMISASI CSS WARNA PASTEL COKLAT (STRUKTUR ROOT STREAMLIT) ---
st.markdown("""
<style>
    /* Mengubah variabel warna global bawaan Streamlit */
    :root {
        --background-color: #FDFBF7 !important;
        --secondary-background-color: #F4ECE1 !important;
        --text-color: #4A3B32 !important;
    }

    /* Memaksa seluruh area halaman utama dan kontainer menjadi krem pastel coklat */
    .stApp, 
    [data-testid="stAppViewContainer"], 
    [data-testid="stHeader"], 
    [data-testid="stToolbar"],
    section.main {
        background-color: #FDFBF7 !important;
        color: #4A3B32 !important;
    }
    
    /* Memaksa area sidebar menjadi coklat susu / latte pastel */
    [data-testid="stSidebar"], 
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {
        background-color: #F4ECE1 !important;
    }
    
    /* Memperjelas warna teks judul dan label */
    h1, h2, h3, h4, h5, h6, p, span, label, div, .streamlit-expanderHeader {
        color: #4A3B32 !important;
    }

    /* Warna kotak expander */
    .streamlit-expanderHeader {
        background-color: #EFE6D8 !important;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

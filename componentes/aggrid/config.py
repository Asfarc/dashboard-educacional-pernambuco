import streamlit as st
from constantes import TITULO_DASHBOARD

def configurar_pagina():
    """
    Configura a página inicial do aplicativo Streamlit.
    """
    st.set_page_config(
        page_title=TITULO_DASHBOARD,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# Controla o que é exportado pelo módulo
__all__ = ['configurar_pagina']
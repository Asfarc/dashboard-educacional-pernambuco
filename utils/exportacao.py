import pandas as pd
import io
import streamlit as st
from constantes import MENSAGEM_SEM_DADOS, MENSAGEM_ERRO_CONVERSAO, NOME_SEM_DADOS, ERRO_CONVERTER_CSV, ERRO_CONVERTER_EXCEL

def converter_df_para_csv(df):
    """Converte DataFrame para formato CSV, incluindo tratamento para DataFrame vazio."""
    if df is None or df.empty:
        return MENSAGEM_SEM_DADOS.encode('utf-8')
    try:
        return df.to_csv(index=False).encode('utf-8')
    except Exception as e:
        st.error(ERRO_CONVERTER_CSV.format(str(e)))
        return MENSAGEM_ERRO_CONVERSAO.encode('utf-8')

def converter_df_para_excel(df):
    """Converte DataFrame para formato Excel, incluindo tratamento para DataFrame vazio."""
    if df is None or df.empty:
        # Retorna um arquivo Excel válido mas com uma aba vazia
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.DataFrame({"Sem dados": []}).to_excel(writer, index=False, sheet_name=NOME_SEM_DADOS)
        return output.getvalue()
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Dados')
        return output.getvalue()
    except Exception as e:
        st.error(ERRO_CONVERTER_EXCEL.format(str(e)))
        output = io.BytesIO()
        output.write(MENSAGEM_ERRO_CONVERSAO.encode('utf-8'))
        return output.getvalue()

# Controla o que é exportado pelo módulo
__all__ = ['converter_df_para_csv', 'converter_df_para_excel']